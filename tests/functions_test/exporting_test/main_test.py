import json
from unittest import TestCase
from unittest.mock import patch
import functions.exporting.main as exporting


class TestExportingMain(TestCase):
    def setUp(self):
        self.user_resolver_patcher = patch('functions.exporting.main.UserResolver')
        self.mock_user_resolver = self.user_resolver_patcher.start()

    def tearDown(self):
        self.user_resolver_patcher.stop()

    @staticmethod
    def get_by_id_side_effect(table, pk_column=None, pk_value=None):
        if table == "requests":
            return {"request_id": 10, "requestor": "Alice", "description": "Req desc"}
        if table == "controls":
            return {"control_id": 20, "vgcpid": "VGCP-020", "description": "Ctrl desc"}
        if table == "users":
            return {"user_id": 30, "display_name": "Tester", "email": "t@example.com"}
        return None

    def _build_event(self, method, path, body=None, path_params=None, query_params=None):
        event = {
            "httpMethod": method,
            "path": path,
            "pathParameters": path_params or {},
            "queryStringParameters": query_params or {},
        }
        if body is not None:
            event["body"] = json.dumps(body)
        return event

    @patch('functions.exporting.main.Logger')
    def test_empty_event_returns_400(self, mock_logger):
        result = exporting.lambda_handler({}, None)
        mock_logger.log.assert_any_call(level="ERROR", message="No event data provided")
        self.assertEqual(result["statusCode"], 400)

    @patch('functions.exporting.main.Logger')
    def test_missing_table_returns_400(self, mock_logger):
        event = self._build_event("GET", "/export")
        result = exporting.lambda_handler(event, None)
        mock_logger.log.assert_any_call(level="ERROR", message="Missing 'table' query parameter")
        self.assertEqual(result["statusCode"], 400)

    @patch('functions.exporting.main.Logger')
    def test_invalid_table_returns_400(self, mock_logger):
        event = self._build_event("GET", "/export", query_params={"table": "bad"})
        result = exporting.lambda_handler(event, None)
        mock_logger.log.assert_any_call(level="WARNING", message="Invalid table requested", extra_fields={"table": "bad"})
        self.assertEqual(result["statusCode"], 400)

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    def test_get_controls_returns_csv(self, mock_crud, mock_logger):
        mock_crud.get_all.return_value = [{"vgcpid": "VGCP-001", "description": "D1"}, {"vgcpid": "VGCP-002", "description": "D2"}]

        event = self._build_event("GET", "/export", query_params={"table": "controls"})
        result = exporting.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["headers"]["Content-Type"], "text/csv")
        body = result["body"]
        self.assertIn("vgcpid", body)
        self.assertIn("VGCP-001", body)

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    def test_get_tests_includes_referenced_values(self, mock_crud, mock_logger):
        # base test row references request_id, control_id, assigned_tester_id
        test_row = {"test_id": 1, "request_id": 10, "control_id": 20, "assigned_tester_id": 30}
        mock_crud.get_all.return_value = [test_row]

        mock_crud.get_by_id.side_effect = self.get_by_id_side_effect

        event = self._build_event("GET", "/export", query_params={"table": "tests"})
        result = exporting.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        body = result["body"]
        self.assertIn("request_requestor", body)
        self.assertIn("Alice", body)
        self.assertIn("control_vgcpid", body)
        self.assertIn("VGCP-020", body)

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    def test_exception_returns_500(self, mock_crud, mock_logger):
        mock_crud.get_all.side_effect = Exception("DB error")

        event = self._build_event("GET", "/export", query_params={"table": "controls"})
        result = exporting.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 500)
        self.assertIn("DB error", json.loads(result["body"])["error"])

    # fetch_rows tests

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    def test_fetch_rows_test_table(self, mock_crud, mock_logger):
        test_row = {"test_id": 1, "request_id": 10, "control_id": 20, "assigned_tester_id": 30}
        mock_crud.get_all.return_value = [test_row]
        mock_crud.get_by_id.side_effect = self.get_by_id_side_effect

        rows = exporting.fetch_rows(exporting.TableNames.TESTS)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.get("request_requestor"), "Alice")
        self.assertEqual(row.get("control_vgcpid"), "VGCP-020")
        self.assertEqual(row.get("assigned_tester_name"), "Tester")

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    def test_fetch_rows_requests_table(self, mock_crud, mock_logger):
        req_row = {"request_id": 10, "created_by": 30}
        mock_crud.get_all.return_value = [req_row]
        mock_crud.get_by_id.side_effect = self.get_by_id_side_effect

        rows = exporting.fetch_rows(exporting.TableNames.REQUESTS)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.get("created_by_name"), "Tester")
        self.assertEqual(row.get("created_by_email"), "t@example.com")

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    def test_fetch_rows_tests_missing_references(self, mock_crud, mock_logger):
        # when referenced rows are missing, enrichment keys should not be added
        base = {"test_id": 2, "request_id": 99, "control_id": 199, "assigned_tester_id": 299}
        mock_crud.get_all.return_value = [base]

        # get_by_id returns None for all referenced lookups
        mock_crud.get_by_id.return_value = None

        rows = exporting.fetch_rows(exporting.TableNames.TESTS)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertNotIn("request_requestor", row)
        self.assertNotIn("control_vgcpid", row)
        self.assertNotIn("assigned_tester_name", row)
