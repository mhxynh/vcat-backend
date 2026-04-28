class TableNames:
    CONTROLS = "controls"
    REQUESTS = "requests"
    TESTS = "tests"
    COMMENTS = "comments"
    AUDIT_LOGS = "audit_logs"
    USERS = "users"


class StatusCodes:
    OK = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    INTERNAL_SERVER_ERROR = 500


class Methods:
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class LogLevels:
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
