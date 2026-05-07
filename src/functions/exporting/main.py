import csv
from datetime import date, datetime
import os
import tempfile
import uuid

from constants.common_variables import LogLevels, Methods, StatusCodes, TableNames
from utils.crud import CrudUtils
from utils.logger import Logger
from utils.response import ResponseUtils
from utils.user_resolver import UserResolver
from utils.s3_utils import S3Utils

ALLOWED_TABLES = {
    TableNames.CONTROLS,
    TableNames.TESTS,
    TableNames.REQUESTS,
    "dashboard",
}


def serialize_value(v):
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, (list, tuple)):
        return ";".join([serialize_value(x) for x in v])
    if v is None:
        return ""
    return str(v)


def fetch_rows(table):
    try:
        if table == TableNames.TESTS:
            rows = CrudUtils.get_all(TableNames.TESTS)
            enriched = []

            # Prefetch controls and users to avoid N+1 queries; fall back to get_by_id
            controls = CrudUtils.get_all(TableNames.CONTROLS) or []
            users = CrudUtils.get_all(TableNames.USERS) or []

            # Only map controls/users if they include the expected exported fields
            control_map = {
                c.get("control_id"): c.get("vgcpid")
                for c in controls
                if c and c.get("vgcpid")
            }
            user_map = {
                u.get("user_id"): u
                for u in users
                if u and (u.get("display_name") or u.get("email"))
            }

            for r in rows:
                row = dict(r)

                ctrl_id = row.get("control_id")
                if ctrl_id:
                    vgcp = control_map.get(ctrl_id)
                    if not vgcp:
                        try:
                            ctrl = CrudUtils.get_by_id(
                                TableNames.CONTROLS, "control_id", ctrl_id
                            )
                            vgcp = ctrl.get("vgcpid") if ctrl else None
                            ctrl_desc = ctrl.get("description") if ctrl else None
                        except Exception:
                            vgcp = None
                            ctrl_desc = None
                    else:
                        ctrl_desc = None
                    if vgcp:
                        row["control_vgcpid"] = vgcp
                        row["control_description"] = ctrl_desc

                tester_id = row.get("assigned_tester_id")
                if tester_id:
                    tester = user_map.get(tester_id)
                    if not tester:
                        try:
                            tester = CrudUtils.get_by_id(
                                TableNames.USERS, "user_id", tester_id
                            )
                        except Exception:
                            tester = None
                    if tester:
                        row["assigned_tester_name"] = tester.get("display_name")
                        row["assigned_tester_email"] = tester.get("email")

                enriched.append(row)
            return enriched

        if table == TableNames.REQUESTS:
            rows = CrudUtils.get_all(TableNames.REQUESTS)
            enriched = []

            # fetch tests and controls once to build a mapping request_id -> [vgcpid]
            tests = CrudUtils.get_all(TableNames.TESTS) or []

            controls = CrudUtils.get_all(TableNames.CONTROLS) or []

            control_map = {c.get("control_id"): c.get("vgcpid") for c in controls if c}
            request_to_vgcpids = {}
            for t in tests:
                req_id = t.get("request_id")
                ctrl_id = t.get("control_id")
                if not (req_id and ctrl_id):
                    continue

                vgcp = control_map.get(ctrl_id)
                if not vgcp:
                    try:
                        ctrl = CrudUtils.get_by_id(
                            TableNames.CONTROLS, "control_id", ctrl_id
                        )
                        vgcp = ctrl.get("vgcpid") if ctrl else None
                    except Exception as e:
                        Logger.log(
                            level=LogLevels.WARNING,
                            message="Failed to fetch control for tests mapping",
                            extra_fields={
                                "control_id": ctrl_id,
                                "request_id": req_id,
                                "error": str(e),
                            },
                        )
                        vgcp = None

                if vgcp:
                    request_to_vgcpids.setdefault(req_id, []).append(vgcp)

            # prefetch users to avoid N+1 lookups per request
            users = CrudUtils.get_all(TableNames.USERS) or []

            user_map = {
                u.get("user_id"): u
                for u in users
                if u and (u.get("display_name") or u.get("email"))
            }

            for r in rows:
                row = dict(r)
                created_by = row.get("created_by")
                user = None
                if created_by:
                    user = user_map.get(created_by)
                    if not user:
                        try:
                            user = CrudUtils.get_by_id(
                                TableNames.USERS, "user_id", created_by
                            )
                        except Exception as e:
                            Logger.log(
                                level=LogLevels.WARNING,
                                message="Failed to fetch user for request",
                                extra_fields={
                                    "user_id": created_by,
                                    "request_id": row.get("request_id"),
                                    "error": str(e),
                                },
                            )
                            user = None
                    if user:
                        row["created_by_name"] = user.get("display_name")
                        row["created_by_email"] = user.get("email")

                row["tests_requested"] = request_to_vgcpids.get(
                    row.get("request_id"), []
                )
                enriched.append(row)
            return enriched

        # default: controls
        return CrudUtils.get_all(TableNames.CONTROLS)
    except Exception as e:
        Logger.log(
            level=LogLevels.ERROR,
            message="DB fetch failed",
            extra_fields={"error": str(e), "table": table},
        )
        raise


def format_controls_csv(rows):
    headers = [
        "VGCPID",
        "Description",
        "Control Owner",
        "Control SME",
        "Escalation Required?",
        "Is Active?",
        "Date Created",
        "Last Tested",
    ]
    if not rows:
        return ["VGCPID", "Description"], []
    data = []
    for row in rows:
        data.append(
            [
                serialize_value(row.get("vgcpid")),
                serialize_value(row.get("description")),
                serialize_value(row.get("control_owner")),
                serialize_value(row.get("control_sme")),
                serialize_value(row.get("escalation")),
                serialize_value(row.get("is_active")),
                serialize_value(row.get("date_created")),
                serialize_value(row.get("last_tested")),
            ]
        )
    return headers, data


def format_tests_csv(rows):
    headers = [
        "VGCPID",
        "Assigned Tester Name",
        "Assigned Tester Email",
    ]
    data = []
    if not rows:
        return headers, data

    excluded = {
        "test_id",
        "request_id",
        "control_id",
        "assigned_tester_id",
        "request_requestor",
        "request_description",
        "control_description",
    }

    # add remaining headers in original order, map DAT/OET to uppercase labels
    for key in rows[0].keys():
        if key in excluded or key in (
            "control_vgcpid",
            "assigned_tester_name",
            "assigned_tester_email",
        ):
            continue
        parts = key.split("_")
        label = " ".join(
            [p.upper() if p.lower() in ("dat", "oet") else p.title() for p in parts]
        )
        headers.append(label)

    for row in rows:
        row_vals = []
        row_vals.append(serialize_value(row.get("control_vgcpid")))
        row_vals.append(serialize_value(row.get("assigned_tester_name")))
        row_vals.append(serialize_value(row.get("assigned_tester_email")))
        for key in rows[0].keys():
            if key in excluded or key in (
                "control_vgcpid",
                "assigned_tester_name",
                "assigned_tester_email",
            ):
                continue
            row_vals.append(serialize_value(row.get(key)))
        data.append(row_vals)

    return headers, data


def format_requests_csv(rows):
    # Keep "Tests Requested" as the first column; auto-generate the rest
    headers = ["Tests Requested"]
    data = []
    if not rows:
        return ["Request ID", "Created By Name", "Created By Email"], []

    excluded = {"request_id", "created_by"}

    for key in rows[0].keys():
        if key in excluded or key in ("tests_requested",):
            continue
        parts = key.split("_")
        label = " ".join(
            [p.upper() if p.lower() in ("dat", "oet") else p.title() for p in parts]
        )
        headers.append(label)

    for row in rows:
        row_vals = []
        # first value: Tests Requested
        row_vals.append(serialize_value(row.get("tests_requested")))
        for key in rows[0].keys():
            if key in excluded or key in ("tests_requested",):
                continue
            row_vals.append(serialize_value(row.get(key)))
        data.append(row_vals)

    return headers, data


def build_export_response(table, rows):
    tmp = None
    try:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", newline="", delete=False, encoding="utf-8"
        )
        writer = csv.writer(tmp)

        data_rows = []
        if table == TableNames.CONTROLS:
            headers, data_rows = format_controls_csv(rows)
        elif table == TableNames.TESTS:
            headers, data_rows = format_tests_csv(rows)
        elif table == TableNames.REQUESTS:
            headers, data_rows = format_requests_csv(rows)
        elif table == "dashboard":
            headers, data_rows = format_dashboard_csv()

        # write CSV
        writer.writerow(headers)
        for data in data_rows:
            writer.writerow(data)

        tmp.flush()
        tmp.close()

        bucket = os.environ.get("EXPORT_BUCKET_NAME")
        presign_ttl = int(os.environ.get("PRESIGNED_URL_TTL_SECONDS", "900"))

        FILENAME_MAP = {
            TableNames.CONTROLS: "control_export.csv",
            TableNames.TESTS: "test_export.csv",
            TableNames.REQUESTS: "request_export.csv",
            "dashboard": "dashboard_export.csv",
        }
        filename = FILENAME_MAP.get(table, f"{table}_export.csv")
        if not bucket:
            Logger.log(
                level=LogLevels.ERROR,
                message="Export bucket not configured",
                extra_fields={"table": table},
            )
            return ResponseUtils.http_response(
                StatusCodes.INTERNAL_SERVER_ERROR,
                {"error": "EXPORT_BUCKET_NAME not configured"},
            )

        prefix = os.environ.get("EXPORT_KEY_PREFIX", "exports/")
        normalized_prefix = (prefix or "").strip("/")
        if normalized_prefix:
            normalized_prefix = f"{normalized_prefix}/"

        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        unique = uuid.uuid4().hex
        object_key = f"{normalized_prefix}{timestamp}-{unique}-{filename}"

        try:
            with open(tmp.name, "rb") as fh:
                S3Utils.get_client().upload_fileobj(
                    fh,
                    bucket,
                    object_key,
                    ExtraArgs={"ContentType": "text/csv"},
                )

            # generate presigned GET URL
            download_url = S3Utils.get_client().generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": bucket,
                    "Key": object_key,
                    "ResponseContentDisposition": f'attachment; filename="{filename}"',
                },
                ExpiresIn=presign_ttl,
            )

            # log actual number of CSV data rows written for accuracy
            Logger.log(
                level=LogLevels.INFO,
                message="Export uploaded to S3",
                extra_fields={
                    "table": table,
                    "count": len(data_rows),
                    "bucket": bucket,
                    "key": object_key,
                },
            )

            return ResponseUtils.http_response(
                StatusCodes.OK,
                {
                    "download_url": download_url,
                    "bucket": bucket,
                    "key": object_key,
                    "filename": filename,
                },
            )
        except Exception as e:
            Logger.log(
                level=LogLevels.ERROR,
                message="Failed to upload export to S3",
                extra_fields={"error": str(e), "table": table},
            )
            return ResponseUtils.http_response(
                StatusCodes.INTERNAL_SERVER_ERROR,
                {"error": "Failed to upload export to S3", "details": str(e)},
            )
    finally:
        try:
            if tmp is not None:
                os.unlink(tmp.name)
        except Exception:
            pass


def format_dashboard_csv():
    tests = CrudUtils.get_all(TableNames.TESTS) or []
    users = CrudUtils.get_all(TableNames.USERS) or []

    total_tests = len(tests)

    not_started = sum(
        1 for r in tests if (r.get("status") or "").upper() == "NOT_STARTED"
    )
    completed = sum(1 for r in tests if (r.get("status") or "").upper() == "COMPLETED")
    open_count = sum(
        1
        for r in tests
        if (r.get("status") or "").upper() not in ("NOT_STARTED", "COMPLETED")
    )
    blocked = sum(
        1
        for r in tests
        if (r.get("status") or "").upper() == "BLOCKED"
        or (r.get("dat_step") or "").upper() == "TESTING_BLOCKED"
        or (r.get("oet_step") or "").upper() == "TESTING_BLOCKED"
    )

    dat_only = sum(
        1 for r in tests if r.get("requires_dat") and not r.get("requires_oet")
    )
    oet_only = sum(
        1 for r in tests if r.get("requires_oet") and not r.get("requires_dat")
    )
    dat_and_oet = sum(
        1 for r in tests if r.get("requires_oet") and r.get("requires_dat")
    )

    walkthrough_scheduled = sum(
        1
        for r in tests
        if (r.get("dat_step") or "").upper() == "WALKTHROUGH_SCHEDULED"
        or (r.get("oet_step") or "").upper() == "WALKTHROUGH_SCHEDULED"
    )
    walkthrough_completed = sum(
        1
        for r in tests
        if (r.get("dat_step") or "").upper() == "WALKTHROUGH_COMPLETED"
        or (r.get("oet_step") or "").upper() == "WALKTHROUGH_COMPLETED"
    )

    dat_in_progress = sum(
        1
        for r in tests
        if (r.get("dat_step") or "").upper() == "TESTING_IN_PROGRESS"
        or (r.get("status") or "").upper() == "DAT_IN_PROGRESS"
    )
    dat_completed = sum(
        1 for r in tests if (r.get("dat_step") or "").upper() == "COMPLETED"
    )

    oet_in_progress = sum(
        1
        for r in tests
        if (r.get("oet_step") or "").upper() == "TESTING_IN_PROGRESS"
        or (r.get("status") or "").upper() == "OET_IN_PROGRESS"
    )
    oet_completed = sum(
        1 for r in tests if (r.get("oet_step") or "").upper() == "COMPLETED"
    )

    rows = []
    rows.append(["Total Controls", total_tests])
    rows.append(["Not Started", not_started])
    rows.append(["Open", open_count])
    rows.append(["Completed", completed])
    rows.append(["Blocked", blocked])
    rows.append(["", ""])

    rows.append(["DAT Only", dat_only])
    rows.append(["OET Only", oet_only])
    rows.append(["DAT & OET", dat_and_oet])
    rows.append(["", ""])

    rows.append(["Walkthrough Scheduled", walkthrough_scheduled])
    rows.append(["Walkthrough Completed", walkthrough_completed])
    rows.append(["DAT In Progress", dat_in_progress])
    rows.append(["DAT Completed", dat_completed])
    rows.append(["", ""])

    rows.append(["OET In Progress", oet_in_progress])
    rows.append(["OET Completed", oet_completed])
    rows.append(["", ""])

    # testers: NotCompleted/TotalAssigned
    tests_by_tester = {}
    for t in tests:
        tester_id = t.get("assigned_tester_id")
        tests_by_tester.setdefault(tester_id, []).append(t)

    for u in users:
        uid = u.get("user_id")
        name = u.get("display_name") or u.get("email")
        assigned = tests_by_tester.get(uid, [])
        not_done = sum(
            1 for t in assigned if (t.get("status") or "").upper() != "COMPLETED"
        )
        total_assigned = len(assigned)
        rows.append([name, f"{not_done} | {total_assigned}"])

    headers = ["Metric", "Value"]
    return headers, rows


def lambda_handler(event, context):
    method = event.get("httpMethod")

    if method == "OPTIONS":
        return ResponseUtils.cors_preflight()

    Logger.start()

    if len(event) == 0:
        Logger.log(level=LogLevels.ERROR, message="No event data provided")
        return ResponseUtils.http_response(
            StatusCodes.BAD_REQUEST, {"error": "No event data provided"}
        )

    Logger.log(level=LogLevels.INFO, message="Export Function Started")

    try:
        CrudUtils.set_audit_context(actor_user_id=UserResolver.resolve(event))

        method, path = ResponseUtils.get_method_and_path(event)
        normalized_path = (path or "").rstrip("/")
        method = (method or "").upper()

        # GET /export?table={controls|tests|requests}
        if method == Methods.GET:
            params = ResponseUtils.get_query_params(event)
            table = (params.get("table") or params.get("export") or "").lower()

            if not table:
                Logger.log(
                    level=LogLevels.ERROR, message="Missing 'table' query parameter"
                )
                return ResponseUtils.http_response(
                    StatusCodes.BAD_REQUEST,
                    {"error": "Missing 'table' query parameter"},
                )

            if table not in ALLOWED_TABLES:
                Logger.log(
                    level=LogLevels.WARNING,
                    message="Invalid table requested",
                    extra_fields={"table": table},
                )
                allowed = ", ".join(sorted(ALLOWED_TABLES))
                return ResponseUtils.http_response(
                    StatusCodes.BAD_REQUEST,
                    {"error": f"Invalid table. Allowed: {allowed}"},
                )

            # fetch rows and build CSV (uploads to S3 when configured)
            rows = fetch_rows(table)
            return build_export_response(table, rows)

        Logger.log(
            level=LogLevels.WARNING,
            message="Method not allowed",
            extra_fields={"method": method, "path": normalized_path},
        )
        return ResponseUtils.http_response(
            StatusCodes.METHOD_NOT_ALLOWED,
            {"error": f"Method {method} not allowed on path {normalized_path}"},
        )
    except Exception as e:
        Logger.log(
            level=LogLevels.ERROR,
            message="Error in export handler",
            extra_fields={"exception": str(e)},
        )
        return ResponseUtils.http_response(
            StatusCodes.INTERNAL_SERVER_ERROR, {"error": str(e)}
        )
    finally:
        CrudUtils.clear_audit_context()
