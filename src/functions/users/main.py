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

    Logger.log(level=LogLevels.INFO, message="Users Function Started")

    try:
        method, path = ResponseUtils.get_method_and_path(event)
        normalized_path = (path or "").rstrip("/")
        method = (method or "").upper()

        # GET /users : list all users or filter by email/is_active via query params
        if method == Methods.GET and normalized_path == "/users":
            params = event.get("queryStringParameters") or {}
            if params and params.get("email"):
                user = CrudUtils.get_by_id(TableNames.USERS, "email", params.get("email"))
                if not user:
                    Logger.log(level=LogLevels.WARNING, message="User not found", extra_fields={"email": params.get("email")})
                    return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "User not found", "email": params.get("email")})
                Logger.log(level=LogLevels.INFO, message="Returning user by email", extra_fields={"email": params.get("email")})
                return ResponseUtils.http_response(StatusCodes.OK, user)

            if params and params.get("active"):
                active_flag = str(params.get("active")).lower()
                if active_flag == "true":
                    users = CrudUtils.get_all(TableNames.USERS)  # get_all returns all; filter client-side not ideal
                    users = [u for u in users if u.get("is_active")]
                elif active_flag == "false":
                    users = CrudUtils.get_all(TableNames.USERS)
                    users = [u for u in users if not u.get("is_active")]
                else:
                    users = CrudUtils.get_all(TableNames.USERS)
            else:
                users = CrudUtils.get_all(TableNames.USERS)

            Logger.log(level=LogLevels.INFO, message="Returning users", extra_fields={"count": len(users)})
            return ResponseUtils.http_response(StatusCodes.OK, users)

        # GET /users/{id}
        if method == Methods.GET:
            user_id = ResponseUtils.extract_id(event, normalized_path, "users")
            if user_id is None:
                Logger.log(level=LogLevels.ERROR, message="User ID not provided in path")
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "User ID not provided"})

            user = CrudUtils.get_by_id(TableNames.USERS, "user_id", user_id)
            if not user:
                Logger.log(level=LogLevels.WARNING, message="User not found", extra_fields={"user_id": user_id})
                return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "User not found", "user_id": user_id})

            Logger.log(level=LogLevels.INFO, message="Returning user", extra_fields={"user_id": user_id})
            return ResponseUtils.http_response(StatusCodes.OK, user)

        # POST /users : create a new user
        if method == Methods.POST:
            body = json.loads(event.get("body", "{}"))
            required_fields = ["email", "role", "display_name"]
            missing = [f for f in required_fields if f not in body]
            if missing:
                Logger.log(level=LogLevels.ERROR, message="Missing fields in request body", extra_fields={"missing": missing})
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "Missing required fields", "missing": missing})

            columns = ["email", "role", "display_name", "is_active"]
            values = [body.get("email"), body.get("role"), body.get("display_name"), True]
            created = CrudUtils.create(TableNames.USERS, columns, values)

            Logger.log(level=LogLevels.INFO, message="Created user", extra_fields={"user_id": created.get("user_id")})
            return ResponseUtils.http_response(StatusCodes.OK, created)

        # PUT /users/{id} : update user
        if method == Methods.PUT:
            user_id = ResponseUtils.extract_id(event, normalized_path, "users")
            if user_id is None:
                Logger.log(level=LogLevels.ERROR, message="User ID not provided in path for update")
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "User ID not provided"})

            body = json.loads(event.get("body", "{}"))
            if not body:
                Logger.log(level=LogLevels.ERROR, message="No update data provided")
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "No update data provided"})

            allowed_fields = ["display_name", "role", "is_active"]
            updates = {k: v for k, v in body.items() if k in allowed_fields}
            if not updates:
                Logger.log(level=LogLevels.ERROR, message="No valid fields to update", extra_fields={"allowed": allowed_fields})
                return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "No valid fields to update", "allowed": allowed_fields})

            updated = CrudUtils.update(TableNames.USERS, "user_id", user_id, updates)
            if not updated:
                Logger.log(level=LogLevels.WARNING, message="User not found for update", extra_fields={"user_id": user_id})
                return ResponseUtils.http_response(StatusCodes.NOT_FOUND, {"error": "User not found", "user_id": user_id})

            Logger.log(level=LogLevels.INFO, message="Updated user", extra_fields={"user_id": user_id, "updates": updates})
            return ResponseUtils.http_response(StatusCodes.OK, updated)

        # DELETE /users/{id} : deactivate user (soft)
        if method == Methods.DELETE:
            user_id = ResponseUtils.extract_id(event, normalized_path, "users")
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
