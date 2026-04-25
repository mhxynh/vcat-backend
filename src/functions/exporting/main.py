import io
import csv
from datetime import date, datetime

from constants.common_variables import LogLevels, Methods, StatusCodes, TableNames
from utils.crud import CrudUtils
from utils.logger import Logger
from utils.response import ResponseUtils
from utils.user_resolver import UserResolver

ALLOWED_TABLES = {TableNames.CONTROLS, TableNames.TESTS, TableNames.REQUESTS}


def serialize_value(v):
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, (list, tuple)):
        return ";".join([str(x) for x in v])
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
            control_map = {c.get("control_id"): c.get("vgcpid") for c in controls if c and c.get("vgcpid")}
            user_map = {u.get("user_id"): u for u in users if u and (u.get("display_name") or u.get("email"))}

            for r in rows:
                row = dict(r)

                ctrl_id = row.get("control_id")
                if ctrl_id:
                    vgcp = control_map.get(ctrl_id)
                    if not vgcp:
                        try:
                            ctrl = CrudUtils.get_by_id(TableNames.CONTROLS, "control_id", ctrl_id)
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
                            tester = CrudUtils.get_by_id(TableNames.USERS, "user_id", tester_id)
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
                            extra_fields={"control_id": ctrl_id, "request_id": req_id, "error": str(e)},
                        )
                        vgcp = None

                if vgcp:
                    request_to_vgcpids.setdefault(req_id, []).append(vgcp)

            for r in rows:
                row = dict(r)
                created_by = row.get("created_by")
                if created_by:
                    user = CrudUtils.get_by_id(TableNames.USERS, "user_id", created_by)
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
    headers = [
        "Requestor Name",
        "Requestor Email",
        "Tests Requested",
    ]
    data = []
    if not rows:
        return headers, data

    excluded = {"request_id", "created_by"}

    for key in rows[0].keys():
        if key in excluded or key in (
            "created_by_name",
            "created_by_email",
            "tests_requested",
        ):
            continue
        parts = key.split("_")
        label = " ".join(
            [p.upper() if p.lower() in ("dat", "oet") else p.title() for p in parts]
        )
        headers.append(label)

    for row in rows:
        row_vals = []
        row_vals.append(serialize_value(row.get("created_by_name")))
        row_vals.append(serialize_value(row.get("created_by_email")))
        row_vals.append(serialize_value(row.get("tests_requested")))
        for key in rows[0].keys():
            if key in excluded or key in (
                "created_by_name",
                "created_by_email",
                "tests_requested",
            ):
                continue
            row_vals.append(serialize_value(row.get(key)))
        data.append(row_vals)

    return headers, data


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

            # fetch rows and build CSV
            rows = fetch_rows(table)

            output = io.StringIO()
            writer = csv.writer(output)

            if table == TableNames.CONTROLS:
                headers, data_rows = format_controls_csv(rows)
                writer.writerow(headers)
                for data in data_rows:
                    writer.writerow(data)
            elif table == TableNames.TESTS:
                headers, data_rows = format_tests_csv(rows)
                writer.writerow(headers)
                for data in data_rows:
                    writer.writerow(data)
            elif table == TableNames.REQUESTS:
                headers, data_rows = format_requests_csv(rows)
                writer.writerow(headers)
                for data in data_rows:
                    writer.writerow(data)

            csv_text = output.getvalue()
            filename = f"{table}_export.csv"

            Logger.log(
                level=LogLevels.INFO,
                message="Export successful",
                extra_fields={"table": table, "count": len(rows)},
            )

            return {
                "statusCode": 200,
                "isBase64Encoded": False,
                "headers": {
                    "Content-Type": "text/csv",
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Access-Control-Allow-Origin": "*",
                },
                "body": csv_text,
            }

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
