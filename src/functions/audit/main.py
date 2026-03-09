from constants.common_variables import LogLevels, Methods, StatusCodes
from utils.db_utils import DbUtils
from utils.logger import Logger
from utils.response import ResponseUtils


def to_positive_int(raw_value, default_value, minimum=1, maximum=1000):
    """Parse a value to int within bounds; return default on invalid input."""
    try:
        parsed = int(raw_value)
        if parsed < minimum:
            return default_value
        if parsed > maximum:
            return maximum
        return parsed
    except (TypeError, ValueError):
        return default_value


def build_audit_query(request_id=None, entity_type=None, entity_id=None, actor_user_id=None):
    """Build SQL and values for audit log fetch.
    Uses LEFT JOIN for vgcpid (single pass) instead of correlated subquery (N passes).
    Caller appends limit and offset to values.
    """
    base_sql = """
        SELECT al.*, c.vgcpid, u.display_name AS actor_display_name
        FROM audit_logs al
        LEFT JOIN users u ON al.actor_user_id = u.user_id
        LEFT JOIN tests t ON al.entity_type = 'TEST' AND al.entity_id = t.test_id
        LEFT JOIN controls c ON t.control_id = c.control_id
    """
    where = []
    values = []

    if request_id:
        where.append(
            "(al.entity_type = 'REQUEST' AND al.entity_id = %s) "
            "OR (al.entity_type = 'TEST' AND al.entity_id IN (SELECT test_id FROM tests WHERE request_id = %s))"
        )
        values.extend([request_id, request_id])
    else:
        if entity_type:
            where.append("al.entity_type = %s")
            values.append(entity_type.upper())
        if entity_id:
            where.append("al.entity_id = %s")
            values.append(entity_id)
        if actor_user_id:
            where.append("al.actor_user_id = %s")
            values.append(actor_user_id)

    sql = base_sql
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY al.changed_at DESC LIMIT %s OFFSET %s"
    return sql, values


def get_audit_logs(params):
    """Fetch audit logs with optional filters.
    - request_id: return logs for the request + all tests under that request (for request history view).
    - entity_type/entity_id: filter by single entity.
    Uses LEFT JOIN for vgcpid lookup (efficient single pass vs correlated subquery).
    """
    conn = DbUtils.get_db_connection()
    try:
        request_id = params.get("request_id")
        entity_type = params.get("entity_type")
        entity_id = params.get("entity_id")
        actor_user_id = params.get("actor_user_id")
        limit = to_positive_int(params.get("limit"), 100, minimum=1, maximum=500)
        offset = to_positive_int(params.get("offset"), 0, minimum=0, maximum=100000)

        sql, values = build_audit_query(
            request_id=request_id,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_user_id=actor_user_id,
        )
        values.extend([limit, offset])

        with conn.cursor() as cur:
            cur.execute(sql, tuple(values))
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_daily_metrics(params):
    """Fetch daily audit metrics (creates, updates, deletes per entity type)."""
    conn = DbUtils.get_db_connection()
    try:
        entity_type = params.get("entity_type")
        days = to_positive_int(params.get("days"), 7, minimum=1, maximum=365)

        where = ["changed_at >= (CURRENT_DATE - (%s::int - 1) * INTERVAL '1 day')"]
        values = [days]
        if entity_type:
            where.append("entity_type = %s")
            values.append(entity_type.upper())

        sql = f"""
            SELECT
                date_trunc('day', changed_at)::date AS day,
                entity_type::text AS entity_type,
                COUNT(*) FILTER (WHERE action = 'CREATE') AS creates,
                COUNT(*) FILTER (WHERE action = 'UPDATE') AS updates,
                COUNT(*) FILTER (WHERE action = 'DELETE') AS deletes
            FROM audit_logs
            WHERE {" AND ".join(where)}
            GROUP BY 1, 2
            ORDER BY day DESC, entity_type
        """

        with conn.cursor() as cur:
            cur.execute(sql, tuple(values))
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return ResponseUtils.cors_preflight()

    Logger.start()

    if len(event) == 0:
        Logger.log(level=LogLevels.ERROR, message="No event data provided")
        return ResponseUtils.http_response(StatusCodes.BAD_REQUEST, {"error": "No event data provided"})

    Logger.log(level=LogLevels.INFO, message="Audit Function Started")

    try:
        method, _ = ResponseUtils.get_method_and_path(event)
        method = (method or "").upper()
        if method != Methods.GET:
            return ResponseUtils.http_response(StatusCodes.METHOD_NOT_ALLOWED, {"error": "Method not allowed"})

        params = ResponseUtils.get_query_params(event)
        view = (params.get("view") or "logs").lower()

        if view == "metrics":
            metrics = get_daily_metrics(params)
            return ResponseUtils.http_response(StatusCodes.OK, {"view": "metrics", "data": metrics})

        logs = get_audit_logs(params)
        return ResponseUtils.http_response(StatusCodes.OK, {"view": "logs", "data": logs, "count": len(logs)})
    except Exception as e:
        Logger.log(level=LogLevels.ERROR, message="Error in audit handler", extra_fields={"exception": str(e)})
        return ResponseUtils.http_response(StatusCodes.INTERNAL_SERVER_ERROR, {"error": str(e)})
