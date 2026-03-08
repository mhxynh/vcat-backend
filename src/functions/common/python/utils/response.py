import json
from datetime import date, datetime

class ResponseUtils:
    @staticmethod
    def default_serializer(obj):
        # Handles types that json.dumps cannot serialize natively. (i.e. "date_created" and "last_tested")
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    @staticmethod
    def http_response(status_code, payload):
        return {
            "statusCode": status_code,
            "body": json.dumps(payload, default=ResponseUtils.default_serializer),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET,PUT,DELETE",
            },
        }
    
    @staticmethod
    def get_method_and_path(event):
        method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method")
        path = event.get("path") or event.get("rawPath")

        return method or "", path or ""

    @staticmethod
    def extract_id(event, path, resource):
        path_params = event.get("pathParameters", {}) or {}
        if "id" in path_params and path_params["id"] is not None:
            return str(path_params["id"])

        parts = (path or "").strip("/").split("/")
        if len(parts) >= 2 and parts[0] == resource:
            return parts[1]
        return None

    @staticmethod
    def get_query_params(event):
        return event.get("queryStringParameters") or {}

    @staticmethod
    def get_json_body(event):
        raw_body = event.get("body") if event else None
        if not raw_body:
            return {}
        if isinstance(raw_body, dict):
            return raw_body
        try:
            return json.loads(raw_body)
        except Exception:
            return {}

    @staticmethod
    def get_actor_user_id(event, body=None):
        request_context = event.get("requestContext", {}) if event else {}
        authorizer = request_context.get("authorizer", {}) if request_context else {}
        headers = event.get("headers", {}) or {}
        params = event.get("queryStringParameters", {}) or {}
        payload = body or {}

        candidates = [
            authorizer.get("user_id"),
            authorizer.get("principalId"),
            (authorizer.get("claims", {}) or {}).get("sub"),
            (authorizer.get("claims", {}) or {}).get("custom:user_id"),
            headers.get("x-user-id"),
            headers.get("X-User-Id"),
            headers.get("x-actor-user-id"),
            headers.get("X-Actor-User-Id"),
            params.get("actor_user_id"),
            payload.get("actor_user_id"),
            payload.get("created_by"),
        ]

        for candidate in candidates:
            if candidate is None or candidate == "":
                continue
            try:
                return int(candidate)
            except (ValueError, TypeError):
                continue
        return None
