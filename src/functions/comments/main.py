import json
from constants.common_variables import LogLevels, Methods, StatusCodes, TableNames
from utils.crud import CrudUtils
from utils.logger import Logger
from utils.response import ResponseUtils
from utils.user_resolver import UserResolver


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return ResponseUtils.cors_preflight()

    Logger.start()

    if len(event) == 0:
        Logger.log(level=LogLevels.ERROR, message="No event data provided")
        return ResponseUtils.http_response(
            StatusCodes.BAD_REQUEST, {"error": "No event data provided"}
        )

    Logger.log(level=LogLevels.INFO, message="Comments Function Started")

    try:
        actor_user_id = UserResolver.resolve(event)
        CrudUtils.set_audit_context(
            actor_user_id=actor_user_id,
        )

        method, path = ResponseUtils.get_method_and_path(event)
        normalized_path = (path or "").rstrip("/")
        method = (method or "").upper()

        # GET /comments : list all comments
        # GET /comments?test_id=... : list comments for a test
        # GET /comments?request_id=... : list comments for a request
        if method == Methods.GET and normalized_path == "/comments":
            params = event.get("queryStringParameters", {}) or {}
            test_id = params.get("test_id")
            request_id = params.get("request_id")

            if test_id and request_id:
                Logger.log(
                    level=LogLevels.ERROR,
                    message="Both test_id and request_id provided",
                )
                return ResponseUtils.http_response(
                    StatusCodes.BAD_REQUEST,
                    {"error": "Provide only one of test_id or request_id"},
                )

            comments = CrudUtils.get_all(TableNames.COMMENTS, order_by="posted_at")

            if test_id:
                comments = [
                    comment
                    for comment in comments
                    if str(comment.get("test_id")) == str(test_id)
                ]
            elif request_id:
                comments = [
                    comment
                    for comment in comments
                    if str(comment.get("request_id")) == str(request_id)
                ]

            Logger.log(
                level=LogLevels.INFO,
                message="Returning comments",
                extra_fields={"count": len(comments)},
            )
            return ResponseUtils.http_response(StatusCodes.OK, comments)

        # POST /comments : create a comment on a test or request
        if method == Methods.POST and normalized_path == "/comments":
            body = json.loads(event.get("body", "{}"))

            required_fields = ["comment_text"]
            missing = [field for field in required_fields if field not in body]
            if missing:
                Logger.log(
                    level=LogLevels.ERROR,
                    message="Missing fields in comment body",
                    extra_fields={"missing": missing},
                )
                return ResponseUtils.http_response(
                    StatusCodes.BAD_REQUEST,
                    {"error": "Missing required fields", "missing": missing},
                )

            if actor_user_id is None:
                Logger.log(
                    level=LogLevels.ERROR,
                    message="Unable to resolve authenticated user for create",
                )
                return ResponseUtils.http_response(
                    StatusCodes.UNAUTHORIZED,
                    {"error": "Unable to resolve authenticated user"},
                )

            test_id = body.get("test_id")
            request_id = body.get("request_id")

            if bool(test_id) == bool(request_id):
                Logger.log(
                    level=LogLevels.ERROR,
                    message="Invalid comment target",
                    extra_fields={"test_id": test_id, "request_id": request_id},
                )
                return ResponseUtils.http_response(
                    StatusCodes.BAD_REQUEST,
                    {"error": "Provide exactly one of test_id or request_id"},
                )

            columns = ["author_user_id", "test_id", "request_id", "comment_text"]
            values = [
                actor_user_id,
                test_id,
                request_id,
                body.get("comment_text"),
            ]

            created = CrudUtils.create(TableNames.COMMENTS, columns, values)

            Logger.log(
                level=LogLevels.INFO,
                message="Created comment",
                extra_fields={
                    "comment_id": created.get("comment_id"),
                    "test_id": test_id,
                    "request_id": request_id,
                },
            )
            return ResponseUtils.http_response(StatusCodes.OK, created)

        # DELETE /comments?comment_id=...&test_id=...
        # DELETE /comments?comment_id=...&request_id=...
        # Authenticated user is resolved from Cognito claims.
        if method == Methods.DELETE and normalized_path == "/comments":
            params = event.get("queryStringParameters", {}) or {}
            comment_id = params.get("comment_id")
            test_id = params.get("test_id")
            request_id = params.get("request_id")

            if not comment_id or bool(test_id) == bool(request_id):
                Logger.log(
                    level=LogLevels.ERROR,
                    message="Invalid delete target",
                    extra_fields={
                        "comment_id": comment_id,
                        "test_id": test_id,
                        "request_id": request_id,
                    },
                )
                return ResponseUtils.http_response(
                    StatusCodes.BAD_REQUEST,
                    {
                        "error": (
                            "Provide comment_id and exactly one of "
                            "test_id or request_id"
                        )
                    },
                )

            if actor_user_id is None:
                Logger.log(
                    level=LogLevels.ERROR,
                    message="Unable to resolve authenticated user for delete",
                    extra_fields={"comment_id": comment_id},
                )
                return ResponseUtils.http_response(
                    StatusCodes.UNAUTHORIZED,
                    {"error": "Unable to resolve authenticated user"},
                )

            effective_author_user_id = actor_user_id

            if test_id:
                deleted = CrudUtils.hard_delete(
                    TableNames.COMMENTS,
                    ["comment_id", "author_user_id", "test_id"],
                    [comment_id, effective_author_user_id, test_id],
                )
            else:
                deleted = CrudUtils.hard_delete(
                    TableNames.COMMENTS,
                    ["comment_id", "author_user_id", "request_id"],
                    [comment_id, effective_author_user_id, request_id],
                )

            if not deleted:
                Logger.log(
                    level=LogLevels.WARNING,
                    message="Comment not found for authenticated user",
                    extra_fields={
                        "comment_id": comment_id,
                        "authenticated_user_id": actor_user_id,
                        "test_id": test_id,
                        "request_id": request_id,
                    },
                )
                return ResponseUtils.http_response(
                    StatusCodes.NOT_FOUND,
                    {"error": "Comment not found or not authorized to delete"},
                )

            Logger.log(
                level=LogLevels.INFO,
                message="Deleted comment",
                extra_fields={
                    "comment_id": comment_id,
                    "test_id": test_id,
                    "request_id": request_id,
                },
            )
            return ResponseUtils.http_response(StatusCodes.OK, deleted)

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
            message="Error in comments handler",
            extra_fields={"exception": str(e)},
        )
        return ResponseUtils.http_response(
            StatusCodes.INTERNAL_SERVER_ERROR, {"error": str(e)}
        )
    finally:
        CrudUtils.clear_audit_context()
