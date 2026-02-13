import json
import time

class Logger:
    start_time = None

    @classmethod
    def start(cls):
        cls.start_time = time.time()

    @classmethod
    def log(cls, level, message, extra_fields=None):
        elapsed = f"{time.time() - cls.start_time:.3f}s"
        message = f"[{level} +{elapsed}]: {message}"
        if extra_fields:
            message += f" Extra fields: {extra_fields}"
        print(message)

    @staticmethod
    def http_response(status_code, payload):
        return {
            "statusCode": status_code,
            "body": json.dumps(payload),
            "headers": {"Content-Type": "application/json"},
        }
