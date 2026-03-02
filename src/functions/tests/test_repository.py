import json

from utils.db_utils import DbUtils
from utils.logger import Logger

class TestRepository:
    @staticmethod
    def get_all_tests():
        conn = None
        try:
            conn = DbUtils.get_db_connection()
            with conn.cursor() as cur:
                query = """
                    SELECT
                        t.*,
                        c.vgcpid,
                        u.display_name AS assigned_tester_name
                    FROM tests t
                    JOIN controls c ON t.control_id = c.control_id
                    LEFT JOIN users u ON t.assigned_tester_id = u.user_id
                    ORDER BY t.test_id DESC;
                """
                cur.execute(query)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            Logger.log(level="ERROR", message="Error fetching all tests", extra_fields={"error": str(e)})
            raise e
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_tests_by_id(test_id):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    query = """
                        SELECT t.*, c.vgcpid
                        FROM tests t
                        JOIN controls c ON t.control_id = c.control_id
                        WHERE t.test_id = %s;
                    """
                    cur.execute(query, (test_id,))
                    row = cur.fetchone()
                    return dict(row) if row else None
            finally:
                conn.close()
        except Exception as e:
            Logger.log(level="ERROR", message="Error fetching test by ID", extra_fields={"error": str(e), "test_id": test_id})
            raise e

    @staticmethod
    def get_tests_by_request_id(request_id):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    query = """
                        SELECT t.*, c.vgcpid
                        FROM tests t
                        JOIN controls c ON t.control_id = c.control_id
                        WHERE t.request_id = %s
                        ORDER BY t.test_id DESC;
                    """
                    cur.execute(query, (request_id,))
                    return [dict(row) for row in cur.fetchall()]
            finally:
                conn.close()
        except Exception as e:
            Logger.log(level="ERROR", message="Error fetching tests by request ID", extra_fields={"error": str(e), "request_id": request_id})
            raise e

    @staticmethod
    def get_tests_by_request_with_details(request_id):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    query = """
                        SELECT t.*, c.vgcpid, u.display_name AS assigned_tester_name
                        FROM tests t
                        JOIN controls c ON t.control_id = c.control_id
                        LEFT JOIN users u ON t.assigned_tester_id = u.user_id
                        WHERE t.request_id = %s
                        ORDER BY t.test_id DESC;
                    """
                    cur.execute(query, (request_id,))
                    return [dict(row) for row in cur.fetchall()]
            finally:
                conn.close()
        except Exception as e:
            Logger.log(level="ERROR", message="Error fetching detailled tests by request", extra_fields={"error": str(e), "request_id": request_id})
            raise e

    @staticmethod
    def get_tests_by_control_id(control_id):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    query = """
                        SELECT t.*, c.vgcpid
                        FROM tests t
                        JOIN controls c ON t.control_id = c.control_id
                        WHERE t.control_id = %s
                        ORDER BY t.test_id DESC;
                    """
                    cur.execute(query, (control_id,))
                    return [dict(row) for row in cur.fetchall()]
            finally:
                conn.close()
        except Exception as e:
            Logger.log(level="ERROR", message="Error fetching tests by control ID", extra_fields={"error": str(e), "control_id": control_id})
            raise e

    @staticmethod
    def create(vgcpid, request_id, description, requires_dat, requires_oet, due_date, assigned_tester_id=None, estimated_date=None):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    query = """
                        INSERT INTO tests (
                            control_id,
                            request_id,
                            assigned_tester_id,
                            requires_dat,
                            requires_oet,
                            due_date,
                            estimated_date,
                            description
                        ) VALUES (
                            (SELECT control_id FROM controls WHERE vgcpid = %s),
                            %s, 
                            %s, 
                            %s, 
                            %s, 
                            %s, 
                            %s, 
                            %s
                        )
                        RETURNING *;
                    """
                    cur.execute(query, (vgcpid, request_id, assigned_tester_id, requires_dat, requires_oet, due_date, estimated_date, description))
                    conn.commit()
                    row = cur.fetchone()
                    return dict(row) if row else None
            finally:
                conn.close()
        except Exception as e:
            Logger.log(level="ERROR", message="Error creating test", extra_fields={"error": str(e), "vgcpid": vgcpid})
            raise e


    @staticmethod
    def update_dat_track(test_id, dat_step, status):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    query = """
                        UPDATE tests
                        SET dat_step = %s, status = %s,
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
                        SET oet_step = %s, status = %s
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
                        SET status = 'IN_PROGRESS', start_date = COALESCE(start_date, current_date)
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
                        SET status = 'COMPLETED', complete_date = COALESCE(complete_date, current_date)
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
    
    @staticmethod
    def soft_delete(test_id):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    query = """
                        UPDATE tests
                        SET status = 'ARCHIVED'
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
            Logger.log(level="ERROR", message="Error soft deleting test", extra_fields={"error": str(e), "test_id": test_id})
            raise e
    
    @staticmethod
    def hard_delete(test_id):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    query = """
                        DELETE FROM tests
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
            Logger.log(level="ERROR", message="Error hard deleting test", extra_fields={"error": str(e), "test_id": test_id})
            raise e
