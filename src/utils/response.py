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
            "headers": {"Content-Type": "application/json"},
        }
