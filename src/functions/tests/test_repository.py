import json
from unittest.mock import patch

from utils.db_utils import DbUtils
from utils.logger import Logger

class TestRepository:
    @staticmethod
    def get_all_tests():
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    query = """
                        SELECT t.*, c.vgcpid
                        FROM tests t
                        JOIN controls c ON t.control_id = c.control_id
                        ORDER BY t.test_id DESC;
                    """
                    cur.execute(query)
                    return [dict(row) for row in cur.fetchall()]
            finally:
                conn.close()
        except Exception as e:
            Logger.log(level="ERROR", message="Error fetching all tests", extra_fields={"error": str(e)})
            raise e
    
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
                        SET dat_step = %s, status = %s
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
                        SET status = 'COMPLETED', complete_date = current_date
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

    def test_get_method_and_path_v2_format(self):
        event = {
            "requestContext": {"http": {"method": "PATCH"}},
            "rawPath": "/tests/99/"
        }
        method, path = tests_main.get_method_and_path(event)
        self.assertEqual(method, "PATCH")
        self.assertEqual(path, "/tests/99")

    def test_extract_test_id_fallback_to_path_split(self):
        event = {"pathParameters": None}
        test_id = tests_main.extract_test_id(event, "/tests/123")
        self.assertEqual(test_id, "123")
        
        test_id_none = tests_main.extract_test_id(event, "/tests")
        self.assertIsNone(test_id_none)

    @patch('functions.tests.main.TestRepository')
    def test_get_with_none_query_params(self, mock_repo):
        mock_repo.get_all.return_value = []
        event = self._build_event("GET", "/tests")
        event["queryStringParameters"] = None 
        
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 200)

    def test_post_with_missing_body_key(self):
        event = self._build_event("POST", "/tests")
        event.pop("body", None) 
        
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("Missing required fields", json.loads(result["body"])["error"])

    def test_put_with_missing_body_key(self):
        event = self._build_event("PUT", "/tests/42", path_params={"test_id": "42"})
        event.pop("body", None)
        
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("Invalid or missing action", json.loads(result["body"])["error"])
