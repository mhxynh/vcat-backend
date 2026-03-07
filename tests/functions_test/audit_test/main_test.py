import json
from unittest import TestCase
from unittest.mock import MagicMock, patch

from functions.audit.main import get_audit_logs, get_daily_metrics, lambda_handler, to_positive_int

class TestAuditMain(TestCase):
    def test_lambda_handler_empty_event_returns_400(self):
        result = lambda_handler({}, None)

        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["error"], "No event data provided")

    def test_to_positive_int_bounds(self):
        self.assertEqual(to_positive_int("3", 7, minimum=1, maximum=5), 3)
        self.assertEqual(to_positive_int("0", 7, minimum=1, maximum=5), 7)
        self.assertEqual(to_positive_int("999", 7, minimum=1, maximum=5), 5)
        self.assertEqual(to_positive_int("bad", 7), 7)

    @patch("functions.audit.main.DbUtils")
    def test_get_audit_logs_builds_filters(self, mock_db):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [{"audit_id": 1}]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_db.get_db_connection.return_value = mock_conn

        params = {"entity_type": "control", "entity_id": "9", "actor_user_id": "3", "limit": "2", "offset": "1"}
        rows = get_audit_logs(params)

        self.assertEqual(rows, [{"audit_id": 1}])
        sql = mock_cur.execute.call_args[0][0]
        values = mock_cur.execute.call_args[0][1]
        self.assertIn("entity_type = %s", sql)
        self.assertIn("entity_id = %s", sql)
        self.assertIn("actor_user_id = %s", sql)
        self.assertEqual(values[0], "CONTROL")
        mock_conn.close.assert_called_once()

    @patch("functions.audit.main.DbUtils")
    def test_get_daily_metrics_with_entity_filter(self, mock_db):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [{"entity_type": "TEST", "creates": 1, "updates": 2, "deletes": 0}]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_db.get_db_connection.return_value = mock_conn

        rows = get_daily_metrics({"days": "3", "entity_type": "test"})
        self.assertEqual(len(rows), 1)
        values = mock_cur.execute.call_args[0][1]
        self.assertEqual(values, (3, "TEST"))
        mock_conn.close.assert_called_once()

    @patch("functions.audit.main.ResponseUtils")
    def test_lambda_handler_non_get_returns_405(self, mock_response):
        mock_response.get_method_and_path.return_value = ("POST", "/audit")
        mock_response.http_response.return_value = {"statusCode": 405}
        result = lambda_handler({"httpMethod": "POST"}, None)
        self.assertEqual(result["statusCode"], 405)

    @patch("functions.audit.main.get_daily_metrics")
    @patch("functions.audit.main.ResponseUtils")
    def test_lambda_handler_metrics_view(self, mock_response, mock_metrics):
        mock_response.get_method_and_path.return_value = ("GET", "/audit")
        mock_response.get_query_params.return_value = {"view": "metrics"}
        mock_metrics.return_value = [{"creates": 1}]
        mock_response.http_response.return_value = {"statusCode": 200, "body": "ok"}

        result = lambda_handler({"httpMethod": "GET"}, None)
        self.assertEqual(result["statusCode"], 200)
        mock_metrics.assert_called_once()

    @patch("functions.audit.main.get_audit_logs")
    @patch("functions.audit.main.ResponseUtils")
    def test_lambda_handler_logs_view(self, mock_response, mock_logs):
        mock_response.get_method_and_path.return_value = ("GET", "/audit")
        mock_response.get_query_params.return_value = {}
        mock_logs.return_value = [{"audit_id": 1}]
        mock_response.http_response.return_value = {"statusCode": 200, "body": "ok"}

        result = lambda_handler({"httpMethod": "GET"}, None)
        self.assertEqual(result["statusCode"], 200)
        mock_logs.assert_called_once()

    @patch("functions.audit.main.Logger")
    @patch("functions.audit.main.ResponseUtils")
    def test_lambda_handler_exception_returns_500(self, mock_response, mock_logger):
        mock_response.get_method_and_path.side_effect = Exception("boom")
        mock_response.http_response.return_value = {"statusCode": 500}

        result = lambda_handler({"httpMethod": "GET"}, None)
        self.assertEqual(result["statusCode"], 500)
        mock_logger.log.assert_any_call(
            level="ERROR", message="Error in audit handler", extra_fields={"exception": "boom"}
        )

    # Additional filter/branch coverage

    @patch("functions.audit.main.DbUtils")
    def test_get_audit_logs_no_filters(self, mock_db):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [{"audit_id": 1}, {"audit_id": 2}]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_db.get_db_connection.return_value = mock_conn

        rows = get_audit_logs({})

        self.assertEqual(len(rows), 2)
        sql = mock_cur.execute.call_args[0][0]
        self.assertNotIn("WHERE", sql.split("ORDER")[0])
        mock_conn.close.assert_called_once()

    @patch("functions.audit.main.DbUtils")
    def test_get_audit_logs_entity_type_only(self, mock_db):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = []
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_db.get_db_connection.return_value = mock_conn

        rows = get_audit_logs({"entity_type": "test"})

        sql = mock_cur.execute.call_args[0][0]
        values = mock_cur.execute.call_args[0][1]
        self.assertIn("entity_type = %s", sql)
        self.assertNotIn("entity_id = %s", sql)
        self.assertEqual(values[0], "TEST")

    @patch("functions.audit.main.DbUtils")
    def test_get_daily_metrics_no_entity_filter(self, mock_db):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [{"day": "2026-03-07", "creates": 5}]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_db.get_db_connection.return_value = mock_conn

        rows = get_daily_metrics({})

        self.assertEqual(len(rows), 1)
        values = mock_cur.execute.call_args[0][1]
        self.assertEqual(values, (7,))
        mock_conn.close.assert_called_once()

    def test_to_positive_int_none_input(self):
        self.assertEqual(to_positive_int(None, 50), 50)

    def test_to_positive_int_exact_bounds(self):
        self.assertEqual(to_positive_int("1", 7, minimum=1, maximum=5), 1)
        self.assertEqual(to_positive_int("5", 7, minimum=1, maximum=5), 5)

    @patch("functions.audit.main.get_audit_logs")
    @patch("functions.audit.main.ResponseUtils")
    def test_lambda_handler_logs_default_view(self, mock_response, mock_logs):
        mock_response.get_method_and_path.return_value = ("GET", "/audit")
        mock_response.get_query_params.return_value = {"view": "logs"}
        mock_logs.return_value = []
        mock_response.http_response.return_value = {"statusCode": 200, "body": "ok"}

        result = lambda_handler({"httpMethod": "GET"}, None)
        self.assertEqual(result["statusCode"], 200)
        mock_logs.assert_called_once()
