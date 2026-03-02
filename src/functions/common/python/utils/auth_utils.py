import json

def get_user_claims(event):
    """Extract user claims from the Lambda event."""
    authorizer = event.get("requestContext", {}).get("authorizer", {})
    return authorizer.get("claims", {})

def get_user_groups(event):
    """Return a list of Cognito groups the user belongs to."""
    claims = get_user_claims(event)
    groups = claims.get("cognito:groups", "")
    
    if isinstance(groups, str):
        return groups.split(",") if groups else []
    return groups

def is_manager(event):
    """Check if the user belongs to the 'Manager' group."""
    return "Manager" in get_user_groups(event)

def require_manager(handler_func):
    def wrapper(event, context):
        if not is_manager(event):
            return {
                "statusCode": 403,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Forbidden: Manager access required"})
            }
        return handler_func(event, context)
    return wrapper

def is_tester(event):
    """Check if the user belongs to the 'Tester' group."""
    return "Tester" in get_user_groups(event)

def require_tester(handler_func):
    def wrapper(event, context):
        if not is_tester(event):
            return {
                "statusCode": 403,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Forbidden: Tester access required"})
            }
        return handler_func(event, context)
    return wrapper
