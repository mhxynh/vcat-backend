import json
import io
import csv
from datetime import date, datetime

from constants.common_variables import LogLevels, Methods, StatusCodes, TableNames
from utils.crud import CrudUtils
from utils.logger import Logger
from utils.response import ResponseUtils
from utils.user_resolver import UserResolver
from utils.db_utils import DbUtils


ALLOWED_TABLES = {TableNames.CONTROLS, TableNames.TESTS, TableNames.REQUESTS}


def serialize_value(v):
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, (list, tuple)):
        return ";".join([str(x) for x in v])
    if v is None:
        return ""
    return str(v)


def fetch_rows(table):
    try:
        # Use CrudUtils to fetch base rows, then enrich with referenced values
        if table == TableNames.TESTS:
            rows = CrudUtils.get_all(TableNames.TESTS)
            enriched = []
            for r in rows:
                row = dict(r)
                req_id = row.get("request_id")
                if req_id:
                    req = CrudUtils.get_by_id(TableNames.REQUESTS, "request_id", req_id)
                    if req:
                        row["request_requestor"] = req.get("requestor")
                        row["request_description"] = req.get("description")

                ctrl_id = row.get("control_id")
                if ctrl_id:
                    ctrl = CrudUtils.get_by_id(TableNames.CONTROLS, "control_id", ctrl_id)
                    if ctrl:
                        row["control_vgcpid"] = ctrl.get("vgcpid")
                        row["control_description"] = ctrl.get("description")

                tester_id = row.get("assigned_tester_id")
                if tester_id:
                    tester = CrudUtils.get_by_id(TableNames.USERS, "user_id", tester_id)
                    if tester:
                        row["assigned_tester_name"] = tester.get("display_name")
                        row["assigned_tester_email"] = tester.get("email")

                enriched.append(row)
            return enriched

        if table == TableNames.REQUESTS:
            rows = CrudUtils.get_all(TableNames.REQUESTS)
            enriched = []
            for r in rows:
                row = dict(r)
                created_by = row.get("created_by")
                if created_by:
                    user = CrudUtils.get_by_id(TableNames.USERS, "user_id", created_by)
                    if user:
                        row["created_by_name"] = user.get("display_name")
                        row["created_by_email"] = user.get("email")
                enriched.append(row)
            return enriched

        # default: controls
        return CrudUtils.get_all(TableNames.CONTROLS)
    except Exception as e:
        Logger.log(level=LogLevels.ERROR, message="DB fetch failed", extra_fields={"error": str(e), "table": table})
        raise


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
                Logger.log(level=LogLevels.ERROR, message="Missing 'table' query parameter")
                return ResponseUtils.http_response(
                    StatusCodes.BAD_REQUEST, {"error": "Missing 'table' query parameter"}
                )

            if table not in ALLOWED_TABLES:
                Logger.log(level=LogLevels.WARNING, message="Invalid table requested", extra_fields={"table": table})
                allowed = ", ".join(sorted(ALLOWED_TABLES))
                return ResponseUtils.http_response(
                    StatusCodes.BAD_REQUEST, {"error": f"Invalid table. Allowed: {allowed}"}
                )

            # fetch rows and build CSV
            rows = fetch_rows(table)

            output = io.StringIO()
            writer = csv.writer(output)

            if rows:
                headers = list(rows[0].keys())
                writer.writerow(headers)
                for row in rows:
                    writer.writerow([serialize_value(row.get(h)) for h in headers])

            csv_text = output.getvalue()
            filename = f"{table}_export.csv"

            Logger.log(level=LogLevels.INFO, message="Export successful", extra_fields={"table": table, "count": len(rows)})

            return {
                "statusCode": 200,
                "isBase64Encoded": False,
                "headers": {
                    "Content-Type": "text/csv",
                    "Content-Disposition": f"attachment; filename=\"{filename}\"",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": csv_text,
            }

        Logger.log(level=LogLevels.WARNING, message="Method not allowed", extra_fields={"method": method, "path": normalized_path})
        return ResponseUtils.http_response(
            StatusCodes.METHOD_NOT_ALLOWED, {"error": f"Method {method} not allowed on path {normalized_path}"}
        )
    except Exception as e:
        Logger.log(level=LogLevels.ERROR, message="Error in export handler", extra_fields={"exception": str(e)})
        return ResponseUtils.http_response(StatusCodes.INTERNAL_SERVER_ERROR, {"error": str(e)})
    finally:
        CrudUtils.clear_audit_context()
