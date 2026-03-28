import base64
import json


class AuthUtils:
    @staticmethod
    def get_user_claims(event):
        """Extract user claims from the Lambda event"""
        authorizer = event.get("requestContext", {}).get("authorizer", {})
        claims = authorizer.get("claims", {})
        if claims:
            return claims
        # Fallback: decode JWT from Authorization header (for sam local)
        return AuthUtils._decode_jwt_claims(event)

    @staticmethod
    def _decode_jwt_claims(event):
        """Decode claims from JWT in the Authorization header
        Used as fallback when running locally where Cognito authorizer is not available
        """
        auth_header = event.get("headers", {}).get("Authorization", "") or event.get(
            "headers", {}
        ).get("authorization", "")
        if not auth_header:
            return {}
        token = auth_header.removeprefix("Bearer ").removeprefix("bearer ")
        parts = token.split(".")
        if len(parts) != 3:
            return {}
        try:
            payload = parts[1]
            # Add padding for base64url decoding
            payload += "=" * (4 - len(payload) % 4)
            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded)
        except Exception:
            return {}

    @staticmethod
    def get_user_groups(event):
        """Safely extracts Cognito groups as a list"""
        # Navigate the event structure for SAM/API Gateway
        claims = event.get("requestContext", {}).get("authorizer", {}).get("claims", {})

        # Fallback: decode JWT from Authorization header (for sam local)
        if not claims:
            claims = AuthUtils._decode_jwt_claims(event)

        groups = claims.get("cognito:groups", [])

        # If it's a string, split it; if it's already a list, return it
        if isinstance(groups, str):
            return [g for g in groups.replace(",", " ").split() if g]
        return groups

    @staticmethod
    def is_tester(event):
        """Returns True if the user has the 'Testers' role"""
        return "Testers" in AuthUtils.get_user_groups(event)

    @staticmethod
    def is_manager(event):
        """Returns True if the user has the 'Managers' role"""
        return "Managers" in AuthUtils.get_user_groups(event)


def require_manager(handler_func):
    def wrapper(event, context):
        if not AuthUtils.is_manager(event):
            return {
                "statusCode": 403,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Forbidden: Manager access required"}),
            }
        return handler_func(event, context)

    return wrapper


def is_tester(event):
    """Check if the user belongs to the 'Tester' group"""
    return "Tester" in AuthUtils.get_user_groups(event)


def require_tester(handler_func):
    def wrapper(event, context):
        if not AuthUtils.is_tester(event):
            return {
                "statusCode": 403,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Forbidden: Tester access required"}),
            }
        return handler_func(event, context)

    return wrapper
