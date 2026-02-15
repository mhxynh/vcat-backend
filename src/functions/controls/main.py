import json
from constants.common_variables import LogLevels, Methods, StatusCodes
from utils.crud import CrudUtils
from utils.logger import Logger
from utils.response import ResponseUtils

def get_method_and_path(event):
    method = event.get("httpMethod")
    path = event.get("path")

    if not method:
        method = event.get("requestContext", {}).get("http", {}).get("method")
    if not path:
        path = event.get("rawPath")

    return method or "", path or ""

def extract_vgcpid(event, path):
    path_params = event.get("pathParameters", {})
    if "vgcpid" in path_params and path_params["vgcpid"] is not None:
        return str(path_params["vgcpid"])

    parts = path.strip("/").split("/")
    if len(parts) == 2 and parts[0] == "controls":
        return parts[1]
    return None

def lambda_handler(event, context):
    Logger.start()

    if len(event) == 0:
        Logger.log(level=LogLevels.ERROR, message="No event data provided")
        return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "No event data provided"})

    Logger.log(level=LogLevels.INFO, message="Controls Function Started")

    try:
        method, path = get_method_and_path(event)
        normalized_path = path.rstrip("/")
        method = method.upper()

        # GET /controls : List all active controls
        if method == Methods.GET and normalized_path == "/controls":
            controls = CrudUtils.get_all("controls", condition="is_active = TRUE")
            Logger.log(level=LogLevels.INFO, message="Returning controls", extra_fields={"count": len(controls)})
            return ResponseUtils.http_response(StatusCodes.OK, controls)

        # GET /controls/{vgcpid} : Get a single control by vgcpid
        if method == Methods.GET:
            vgcpid = extract_vgcpid(event, normalized_path)
            if vgcpid is None:
                Logger.log(level=LogLevels.ERROR, message="VGCPID not provided in path")
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "VGCPID not provided"})

            control = CrudUtils.get_by_id("controls", "vgcpid", vgcpid)
            if not control:
                Logger.log(level=LogLevels.WARNING, message="Control not found", extra_fields={"vgcpid": vgcpid})
                return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "Control not found", "vgcpid": vgcpid})

            Logger.log(level=LogLevels.INFO, message="Returning control", extra_fields={"vgcpid": vgcpid})
            return ResponseUtils.http_response(StatusCodes.OK, control)

        # POST /controls : Create a new control
        if method == Methods.POST and normalized_path == "/controls":
            body = json.loads(event.get("body", "{}"))

            required_fields = ["vgcpid", "description", "control_owner", "control_sme"]
            missing = [field for field in required_fields if field not in body]
            if missing:
                Logger.log(level=LogLevels.ERROR, message="Missing fields in request body", extra_fields={"missing_fields": missing})
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "Missing required fields", "missing": missing})

            columns = ["vgcpid", "description", "control_owner", "control_sme", "escalation", "is_active"]
            values = [
                body["vgcpid"],
                body["description"],
                body["control_owner"],
                body["control_sme"],
                body.get("escalation", False),
                True,
            ]

            created = CrudUtils.create("controls", columns, values)
            Logger.log(level=LogLevels.INFO, message="Created control", extra_fields={"vgcpid": body["vgcpid"]})
            return ResponseUtils.http_response(StatusCodes.OK, created)

        # PUT /controls/{vgcpid} : Update an existing control by vgcpid
        if method == Methods.PUT:
            vgcpid = extract_vgcpid(event, normalized_path)
            if vgcpid is None:
                Logger.log(level=LogLevels.ERROR, message="VGCPID not provided in path")
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "VGCPID not provided"})

            body = json.loads(event.get("body", "{}"))
            if not body:
                Logger.log(level=LogLevels.ERROR, message="No update data provided")
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "No update data provided"})

            allowed_fields = ["description", "control_owner", "control_sme", "escalation", "last_tested"]
            updates = {field: value for field, value in body.items() if field in allowed_fields}

            if not updates:
                Logger.log(level=LogLevels.ERROR, message="No valid fields to update")
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "No valid fields", "allowed": allowed_fields})

            updated = CrudUtils.update("controls", "vgcpid", vgcpid, updates)
            if not updated:
                Logger.log(level=LogLevels.WARNING, message="Control not found", extra_fields={"vgcpid": vgcpid})
                return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "Control not found", "vgcpid": vgcpid})

            Logger.log(level=LogLevels.INFO, message="Updated control", extra_fields={"vgcpid": vgcpid})
            return ResponseUtils.http_response(StatusCodes.OK, updated)

        Logger.log(level=LogLevels.WARNING, message="Method not allowed", extra_fields={"method": method, "path": normalized_path})
        return ResponseUtils.http_response(StatusCodes.METHOD_NOT_ALLOWED, {"error": f"Method {method} not allowed on path {normalized_path}"})
    except Exception as e:
        Logger.log(level=LogLevels.ERROR, message="Error in controls handler", extra_fields={"exception": str(e)})
        return ResponseUtils.http_response(StatusCodes.INTERNAL_SERVER_ERROR, {"error": str(e)})
