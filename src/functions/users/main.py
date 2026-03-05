from constants.common_variables import TableNames, Methods, StatusCodes, LogLevels
from utils.crud import CrudUtils
from utils.logger import Logger
from utils.response import ResponseUtils


def lambda_handler(event, context):
    Logger.start()

    if len(event) == 0:
        Logger.log(level=LogLevels.ERROR, message="No event data provided")
        return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "No event data provided"})

    Logger.log(level=LogLevels.INFO, message="Users Function Started")

    try:
        body_for_context = ResponseUtils.get_json_body(event)
        CrudUtils.set_audit_context(
            actor_user_id=ResponseUtils.get_actor_user_id(event, body=body_for_context),
        )

        method, path = ResponseUtils.get_method_and_path(event)
        normalized_path = (path or "").rstrip("/")
        method = (method or "").upper()

        # GET /users : List all users or filter by query params (?email=, ?is_active=)
        if method == Methods.GET and normalized_path == "/users":
            params = event.get("queryStringParameters") or {}

            # Filter by email
            if params and params.get("email"):
                email = params.get("email")
                results = CrudUtils.get_by_filter(TableNames.USERS, "email", email)
                if not results:
                    Logger.log(level=LogLevels.WARNING, message="User not found by email", extra_fields={"email": email})
                    return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "User not found", "email": email})
                return ResponseUtils.http_response(StatusCodes.OK, results[0])

            # Filter by active status
            if params and params.get("is_active"):
                raw = params.get("is_active")
                is_active = str(raw).lower() == "true"
                results = CrudUtils.get_by_filter(TableNames.USERS, "is_active", is_active)
                Logger.log(level=LogLevels.INFO, message="Returning users filtered by is_active", extra_fields={"is_active": is_active, "count": len(results)})
                return ResponseUtils.http_response(StatusCodes.OK, results)

            # No filters: return all
            users = CrudUtils.get_all(TableNames.USERS)
            Logger.log(level=LogLevels.INFO, message="Returning users", extra_fields={"count": len(users)})
            return ResponseUtils.http_response(StatusCodes.OK, users)

        # GET /users/{id}
        if method == Methods.GET:
            user_id = ResponseUtils.extract_id(event, normalized_path, TableNames.USERS)
            
            user = CrudUtils.get_by_id(TableNames.USERS, "user_id", user_id)
            if not user:
                Logger.log(level=LogLevels.WARNING, message="User not found", extra_fields={"user_id": user_id})
                return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "User not found", "user_id": user_id})
            
            Logger.log(level=LogLevels.INFO, message="Returning user", extra_fields={"user_id": user_id})
            return ResponseUtils.http_response(StatusCodes.OK, user)

        # DELETE /users/{id} : Deactivate user
        if method == Methods.DELETE:
            user_id = ResponseUtils.extract_id(event, normalized_path, TableNames.USERS)
            if user_id is None:
                Logger.log(level=LogLevels.ERROR, message="User ID not provided in path for delete")
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "User ID not provided"})

            deactivated = CrudUtils.deactivate(TableNames.USERS, "user_id", user_id)
            if not deactivated:
                Logger.log(level=LogLevels.WARNING, message="User not found for deactivate", extra_fields={"user_id": user_id})
                return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "User not found", "user_id": user_id})

            Logger.log(level=LogLevels.INFO, message="Deactivated user", extra_fields={"user_id": user_id})
            return ResponseUtils.http_response(StatusCodes.OK, deactivated)

        Logger.log(level=LogLevels.WARNING, message="Method not allowed", extra_fields={"method": method, "path": normalized_path})
        return ResponseUtils.http_response(StatusCodes.METHOD_NOT_ALLOWED, {"error": f"Method {method} not allowed on path {normalized_path}"})
    except Exception as e:
        Logger.log(level=LogLevels.ERROR, message="Error in users handler", extra_fields={"exception": str(e)})
        return ResponseUtils.http_response(StatusCodes.INTERNAL_SERVER_ERROR, {"error": str(e)})
    finally:
        CrudUtils.clear_audit_context()
