import json
from constants.common_variables import TableNames, Methods, StatusCodes, LogLevels
from utils.crud import CrudUtils
from utils.logger import Logger
from utils.response import ResponseUtils

def lambda_handler(event, context):
    Logger.start()

    if len(event) == 0:
        Logger.log(level=LogLevels.ERROR, message="No event data provided")
        return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "No event data provided"})

    Logger.log(level=LogLevels.INFO, message="Requests Function Started")

    try:
        method, path = ResponseUtils.get_method_and_path(event)
        normalized_path = (path or "").rstrip("/")
        method = (method or "").upper()

        # GET /requests : list all requests
        if method == Methods.GET and normalized_path == "/requests":
            requests = CrudUtils.get_all(TableNames.REQUESTS)
            Logger.log(level=LogLevels.INFO, message="Returning requests", extra_fields={"count": len(requests)})
            return ResponseUtils.http_response(StatusCodes.OK, requests)

        # GET /requests/{id} : get single request
        if method == Methods.GET:
            req_id = ResponseUtils.extract_id(event, normalized_path, TableNames.REQUESTS)

            request_record = CrudUtils.get_by_id(TableNames.REQUESTS, "request_id", req_id)
            if not request_record:
                Logger.log(level=LogLevels.WARNING, message="Request not found", extra_fields={"request_id": req_id})
                return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "Request not found", "request_id": req_id})

            Logger.log(level=LogLevels.INFO, message="Returning request", extra_fields={"request_id": req_id})
            return ResponseUtils.http_response(StatusCodes.OK, request_record)

        # POST /requests : create a new request
        if method == Methods.POST:
            body = json.loads(event.get("body", "{}"))
            required_fields = ["requestor", "created_by"]
            missing = [field for field in required_fields if field not in body]
            if missing:
                Logger.log(level=LogLevels.ERROR, message="Missing fields in request body", extra_fields={"missing": missing})
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "Missing required fields", "missing": missing})

            columns = ["requestor", "start_date", "due_date", "status", "created_by"]
            values = [
                body.get("requestor"),
                body.get("start_date"),
                body.get("due_date"),
                body.get("status", "Not Started"),
                body.get("created_by"),
            ]
            created = CrudUtils.create(TableNames.REQUESTS, columns, values)

            Logger.log(level=LogLevels.INFO, message="Created request", extra_fields={"request_id": created.get("request_id")})
            return ResponseUtils.http_response(StatusCodes.OK, created)

        # PUT /requests/{id} : update request (status transitions)
        if method == Methods.PUT:
            req_id = ResponseUtils.extract_id(event, normalized_path, TableNames.REQUESTS)
            if req_id is None:
                Logger.log(level=LogLevels.ERROR, message="Request ID not provided in path for update")
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "Request ID not provided"})

            body = json.loads(event.get("body", "{}"))
            if not body:
                Logger.log(level=LogLevels.ERROR, message="No update data provided")
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "No update data provided"})

            allowed_fields = ["status"]
            updates = {k: v for k, v in body.items() if k in allowed_fields}
            if not updates:
                Logger.log(level=LogLevels.ERROR, message="No valid fields to update; only 'status' allowed")
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "No valid fields to update; only 'status' allowed", "allowed": allowed_fields})

            updated = CrudUtils.update(TableNames.REQUESTS, "request_id", req_id, updates)
            if not updated:
                Logger.log(level=LogLevels.WARNING, message="Request not found for update", extra_fields={"request_id": req_id})
                return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "Request not found", "request_id": req_id})

            Logger.log(level=LogLevels.INFO, message="Updated request", extra_fields={"request_id": req_id, "updates": updates})
            return ResponseUtils.http_response(StatusCodes.OK, updated)

        # DELETE /requests/{id} : Archive or Hard Delete a request
        if method == Methods.DELETE:
            req_id = ResponseUtils.extract_id(event, normalized_path, TableNames.REQUESTS)
            if req_id is None:
                Logger.log(level=LogLevels.ERROR, message="Request ID not provided in path for delete")
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "Request ID not provided"})

            params = event.get("queryStringParameters", {})
            hard_flag = str(params.get("hard", "false")).lower() if params else "false"
            hard = hard_flag == "true"

            if hard:
                deleted = CrudUtils.hard_delete(TableNames.REQUESTS, "request_id", req_id)
                if not deleted:
                    Logger.log(level=LogLevels.WARNING, message="Request not found for hard delete", extra_fields={"request_id": req_id})
                    return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "Request not found", "request_id": req_id})

                Logger.log(level=LogLevels.INFO, message="Hard deleted request", extra_fields={"request_id": req_id})
                return ResponseUtils.http_response(StatusCodes.OK, deleted)
            else:
                archived = CrudUtils.update(TableNames.REQUESTS, "request_id", req_id, {"status": "ARCHIVED"})
                if not archived:
                    Logger.log(level=LogLevels.WARNING, message="Request not found for archive", extra_fields={"request_id": req_id})
                    return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "Request not found", "request_id": req_id})

                Logger.log(level=LogLevels.INFO, message="Archived request", extra_fields={"request_id": req_id})
                return ResponseUtils.http_response(StatusCodes.OK, archived)

        Logger.log(level=LogLevels.WARNING, message="Method not allowed", extra_fields={"method": method, "path": normalized_path})
        return ResponseUtils.http_response(StatusCodes.METHOD_NOT_ALLOWED, {"error": f"Method {method} not allowed on path {normalized_path}"})
    except Exception as e:
        Logger.log(level=LogLevels.ERROR, message="Error in requests handler", extra_fields={"exception": str(e)})
        return ResponseUtils.http_response(StatusCodes.INTERNAL_SERVER_ERROR, {"error": str(e)})
