import json
from constants.common_variables import LogLevels, Methods, StatusCodes, TableNames
from utils.crud import CrudUtils
from utils.logger import Logger
from utils.response import ResponseUtils


def lambda_handler(event, context):
    Logger.start()

    if len(event) == 0:
        Logger.log(level=LogLevels.ERROR, message="No event data provided")
        return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "No event data provided"})

    Logger.log(level=LogLevels.INFO, message="Controls Function Started")

    try:
        body_for_context = ResponseUtils.get_json_body(event)
        CrudUtils.set_audit_context(
            actor_user_id=ResponseUtils.get_actor_user_id(event, body=body_for_context),
            reason=body_for_context.get("reason") or body_for_context.get("audit_reason"),
        )

        method, path = ResponseUtils.get_method_and_path(event)
        normalized_path = (path or "").rstrip("/")
        method = (method or "").upper()

        # GET /controls : List all controls (active and inactive)
        if method == Methods.GET and normalized_path == "/controls":
            controls = CrudUtils.get_all(TableNames.CONTROLS, order_by="control_id")
            Logger.log(level=LogLevels.INFO, message="Returning controls", extra_fields={"count": len(controls)})
            return ResponseUtils.http_response(StatusCodes.OK, controls)

        # GET /controls/{vgcpid} : Get a single control by vgcpid
        if method == Methods.GET:
            vgcpid = ResponseUtils.extract_id(event, normalized_path, TableNames.CONTROLS)
            
            control = CrudUtils.get_by_id(TableNames.CONTROLS, "vgcpid", vgcpid)
            if not control:
                Logger.log(level=LogLevels.WARNING, message="Control not found", extra_fields={"vgcpid": vgcpid})
                return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "Control not found", "vgcpid": vgcpid})

            Logger.log(level=LogLevels.INFO, message="Returning control", extra_fields={"vgcpid": vgcpid})
            return ResponseUtils.http_response(StatusCodes.OK, control)

        # POST /controls : Create a new control
        if method == Methods.POST:
            body = json.loads(event.get("body", "{}"))

            required_fields = ["vgcpid", "description", "control_owner", "escalation"]
            missing = [field for field in required_fields if field not in body]
            if missing:
                Logger.log(level=LogLevels.ERROR, message="Missing fields in request body", extra_fields={"missing_fields": missing})
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "Missing required fields", "missing": missing})

            columns = ["vgcpid", "description", "control_owner", "control_sme", "escalation", "is_active"]
            values = [
                body.get("vgcpid"),
                body.get("description"),
                body.get("control_owner"),
                None if body.get("control_sme") == "" else body.get("control_sme"),
                body.get("escalation"),
                True
            ]

            created = CrudUtils.create(TableNames.CONTROLS, columns, values)
            Logger.log(level=LogLevels.INFO, message="Created control", extra_fields={"vgcpid": body["vgcpid"]})
            return ResponseUtils.http_response(StatusCodes.OK, created)

        # PUT /controls/{vgcpid} : Update an existing control by vgcpid
        if method == Methods.PUT:
            vgcpid = ResponseUtils.extract_id(event, normalized_path, TableNames.CONTROLS)
            if vgcpid is None:
                Logger.log(level=LogLevels.ERROR, message="VGCPID not provided in path")
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "VGCPID not provided"})

            body = json.loads(event.get("body", "{}"))
            if not body:
                Logger.log(level=LogLevels.ERROR, message="No update data provided")
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "No update data provided"})

            allowed_fields = ["vgcpid", "description", "control_owner", "control_sme", "escalation", "last_tested"]
            updates = {field: value for field, value in body.items() if field in allowed_fields}

            if not updates:
                Logger.log(level=LogLevels.ERROR, message="No valid fields to update")
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "No valid fields", "allowed": allowed_fields})

            updated = CrudUtils.update(TableNames.CONTROLS, "vgcpid", vgcpid, updates)
            if not updated:
                Logger.log(level=LogLevels.WARNING, message="Control not found", extra_fields={"vgcpid": vgcpid})
                return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "Control not found", "vgcpid": vgcpid})

            Logger.log(level=LogLevels.INFO, message="Updated control", extra_fields={"vgcpid": vgcpid})
            return ResponseUtils.http_response(StatusCodes.OK, updated)
        
        # DELETE /controls/{vgcpid} : Retire or Hard Delete a control by vgcpid
        if method == Methods.DELETE:
            vgcpid = ResponseUtils.extract_id(event, normalized_path, TableNames.CONTROLS)
            if vgcpid is None:
                Logger.log(level=LogLevels.ERROR, message="VGCPID not provided in path for delete")
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "VGCPID not provided"})

            params = event.get("queryStringParameters", {})
            hard_flag = str(params.get("hard", "false")).lower() if params else "false"
            hard = hard_flag == "true"

            if hard:
                deleted = CrudUtils.hard_delete(TableNames.CONTROLS, "vgcpid", vgcpid)
                if not deleted:
                    Logger.log(level=LogLevels.WARNING, message="Control not found for hard delete", extra_fields={"vgcpid": vgcpid})
                    return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "Control not found", "vgcpid": vgcpid})

                Logger.log(level=LogLevels.INFO, message="Hard deleted control", extra_fields={"vgcpid": vgcpid})
                return ResponseUtils.http_response(StatusCodes.OK, deleted)
            else:
                deactivated = CrudUtils.deactivate(TableNames.CONTROLS, "vgcpid", vgcpid)
                if not deactivated:
                    Logger.log(level=LogLevels.WARNING, message="Control not found for deactivate", extra_fields={"vgcpid": vgcpid})
                    return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "Control not found", "vgcpid": vgcpid})

                Logger.log(level=LogLevels.INFO, message="Deactivated control", extra_fields={"vgcpid": vgcpid})
                return ResponseUtils.http_response(StatusCodes.OK, deactivated)

        Logger.log(level=LogLevels.WARNING, message="Method not allowed", extra_fields={"method": method, "path": normalized_path})
        return ResponseUtils.http_response(StatusCodes.METHOD_NOT_ALLOWED, {"error": f"Method {method} not allowed on path {normalized_path}"})
    except Exception as e:
        Logger.log(level=LogLevels.ERROR, message="Error in controls handler", extra_fields={"exception": str(e)})
        return ResponseUtils.http_response(StatusCodes.INTERNAL_SERVER_ERROR, {"error": str(e)})
    finally:
        CrudUtils.clear_audit_context()
