from utils.db_utils import DbUtils
from utils.logger import Logger

class TestRepository:
    @staticmethod
    def get_tests_by_request_with_details(request_id):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    query = """
                        SELECT t.*,
                            c.vgcpid,
                            c.description AS control_description,
                            u.display_name AS tester_name
                        FROM tests t
                        JOIN controls c ON t.control_id = c.control_id
                        LEFT JOIN users u ON t.assigned_tester_id = u.user_id
                        WHERE t.request_id = %s;
                    """
                    cur.execute(query, (request_id,))
                    return [dict(row) for row in cur.fetchall()]
            finally:
                conn.close()
        except Exception as e:
            Logger.log(level="ERROR", message="Error fetching test details by request", extra_fields={"error": str(e), "request_id": request_id})
            raise e

    @staticmethod
    def update_dat_track(test_id, dat_step, status):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    query = """
                        UPDATE tests
                        SET dat_step = COALESCE(%s, dat_step), status = COALESCE(%s, status)
                        WHERE test_id = %s
                        RETURNING *;
                    """
                    cur.execute(query, (dat_step, status, test_id))
                    conn.commit()
                    row = cur.fetchone()
                    return dict(row) if row else None
            finally:
                conn.close()
        except Exception as e:
            Logger.log(level="ERROR", message="Error updating DAT track", extra_fields={"error": str(e), "test_id": test_id})
            raise e

    @staticmethod
    def update_oet_track(test_id, oet_step, status):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    query = """
                        UPDATE tests
                        SET oet_step = COALESCE(%s, oet_step), status = COALESCE(%s, status)
                        WHERE test_id = %s
                        RETURNING *;
                    """
                    cur.execute(query, (oet_step, status, test_id))
                    conn.commit()
                    row = cur.fetchone()
                    return dict(row) if row else None
            finally:
                conn.close()
        except Exception as e:
            Logger.log(level="ERROR", message="Error updating OET track", extra_fields={"error": str(e), "test_id": test_id})
            raise e

    @staticmethod
    def start_test(test_id):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    query = """
                        UPDATE tests
                        SET status = 'IN_PROGRESS',
                            start_date = COALESCE(start_date, current_date)
                        WHERE test_id = %s
                        RETURNING *;
                    """
                    cur.execute(query, (test_id,))
                    conn.commit()
                    row = cur.fetchone()
                    return dict(row) if row else None
            finally:
                conn.close()
        except Exception as e:
            Logger.log(level="ERROR", message="Error starting test", extra_fields={"error": str(e), "test_id": test_id})
            raise e

    @staticmethod
    def review_test(test_id):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    query = """
                        UPDATE tests
                        SET status = 'IN_REVIEW'
                        WHERE test_id = %s
                        RETURNING *;
                    """
                    cur.execute(query, (test_id,))
                    conn.commit()
                    row = cur.fetchone()
                    return dict(row) if row else None
            finally:
                conn.close()
        except Exception as e:
            Logger.log(level="ERROR", message="Error reviewing test", extra_fields={"error": str(e), "test_id": test_id})
            raise e

    @staticmethod
    def complete_test(test_id):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    query = """
                        UPDATE tests
                        SET status = 'COMPLETED',
                            complete_date = current_date
                        WHERE test_id = %s
                        RETURNING *;
                    """
                    cur.execute(query, (test_id,))
                    conn.commit()
                    row = cur.fetchone()
                    return dict(row) if row else None
            finally:
                conn.close()
        except Exception as e:
            Logger.log(level="ERROR", message="Error completing test", extra_fields={"error": str(e), "test_id": test_id})
            raise e
