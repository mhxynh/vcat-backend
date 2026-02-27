import json
from unittest import TestCase
from unittest.mock import patch
import functions.tests.main as tests_main

class TestTestsMain(TestCase):
    def _build_event(self, method, path, body=None, path_params=None, query_params=None):
        event = {
            "httpMethod": method,
            "path": path,
            "pathParameters": path_params,
            "queryStringParameters": query_params or {},
        }
        if body is not None:
            event["body"] = json.dumps(body)
        return event

    # Empty event

    @patch('functions.tests.main.Logger')
    def test_empty_event_returns_400(self, mock_logger):
        result = tests_main.lambda_handler({}, None)
        mock_logger.log.assert_any_call(level="ERROR", message="No event data provided")
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("No event data", json.loads(result["body"])["error"])

    # GET /tests

    @patch('functions.tests.main.TestRepository')
    def test_get_tests_by_id_returns_200(self, mock_repo):
        mock_repo.get_tests_by_id.return_value = {"test_id": "42", "status": "IN_PROGRESS"}
        event = self._build_event("GET", "/tests/42", path_params={"test_id": "42"})
        
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["test_id"], "42")

    @patch('functions.tests.main.TestRepository')
    def test_get_tests_by_id_not_found_returns_404(self, mock_repo):
        mock_repo.get_tests_by_id.return_value = None
        event = self._build_event("GET", "/tests/99", path_params={"test_id": "99"})
        
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 404)

    @patch('functions.tests.main.TestRepository')
    def test_get_tests_by_request_with_details_returns_200(self, mock_repo):
        mock_repo.get_tests_by_request_with_details.return_value = [{"test_id": "1", "tester_name": "Bob"}]
        event = self._build_event("GET", "/tests", query_params={"request_id": "100", "details": "true"})
        
        result = tests_main.lambda_handler(event, None)
        
        mock_repo.get_tests_by_request_with_details.assert_called_once_with("100")
        self.assertEqual(result["statusCode"], 200)

    @patch('functions.tests.main.TestRepository')
    def test_get_tests_by_request_id_only_returns_200(self, mock_repo):
        mock_repo.get_tests_by_request_id.return_value = [{"test_id": "1", "request_id": "100"}]
        
        event = self._build_event("GET", "/tests", query_params={"request_id": "100"})
        result = tests_main.lambda_handler(event, None)
        
        mock_repo.get_tests_by_request_id.assert_called_once_with("100")
        self.assertEqual(result["statusCode"], 200)

    @patch('functions.tests.main.TestRepository')
    def test_get_tests_by_control_id_returns_200(self, mock_repo):
        mock_repo.get_tests_by_control_id.return_value = [{"test_id": "1", "control_id": "20"}]
        event = self._build_event("GET", "/tests", query_params={"control_id": "20"})
        
        result = tests_main.lambda_handler(event, None)
        
        mock_repo.get_tests_by_control_id.assert_called_once_with("20")
        self.assertEqual(result["statusCode"], 200)

    @patch('functions.tests.main.TestRepository')
    def test_get_all_tests_returns_200(self, mock_repo):
        mock_repo.get_all_tests.return_value = [{"test_id": "1"}]
        event = self._build_event("GET", "/tests") # No query params
        result = tests_main.lambda_handler(event, None)
        
        mock_repo.get_all_tests.assert_called_once()
        self.assertEqual(result["statusCode"], 200)

    # POST /tests

    @patch('functions.tests.main.TestRepository')
    def test_post_test_returns_200(self, mock_repo):
        body = {
            "vgcpid": "VGCP-001", "request_id": 100, "requires_dat": True, 
            "requires_oet": False, "due_date": "2026-03-01", "description": "Test control"
        }
        mock_repo.create.return_value = {**body, "test_id": 1}
        event = self._build_event("POST", "/tests", body=body)
        
        result = tests_main.lambda_handler(event, None)
        
        mock_repo.create.assert_called_once()
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["test_id"], 1)

    @patch('functions.tests.main.TestRepository')
    def test_post_test_bad_vgcpid_returns_400(self, mock_repo):
        body = {
            "vgcpid": "BAD-VGCPID", "request_id": 100, "requires_dat": True, 
            "requires_oet": False, "due_date": "2026-03-01", "description": "Test control"
        }
        mock_repo.create.return_value = None # Simulating the subquery failing to find an ID
        event = self._build_event("POST", "/tests", body=body)
        
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("Failed to create test. Verify that VGCPID exists.", json.loads(result["body"])["error"])

    def test_post_test_missing_required_returns_400(self):
        body = {"vgcpid": "VGCP-001"} # Missing request_id, description, etc.
        event = self._build_event("POST", "/tests", body=body)
        
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("Missing required fields", json.loads(result["body"])["error"])

    # PUT /tests/{test_id}

    @patch('functions.tests.main.TestRepository')
    def test_put_action_start_returns_200(self, mock_repo):
        mock_repo.start_test.return_value = {"test_id": "42", "status": "IN_PROGRESS"}
        event = self._build_event("PUT", "/tests/42", body={"action": "start"}, path_params={"test_id": "42"})
        
        result = tests_main.lambda_handler(event, None)
        
        mock_repo.start_test.assert_called_once_with("42")
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["status"], "IN_PROGRESS")

    def test_put_test_invalid_action_returns_400(self):
        event = self._build_event("PUT", "/tests/42", body={"action": "garbage_action"}, path_params={"test_id": "42"})
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("Invalid or missing action", json.loads(result["body"])["error"])

    def test_put_missing_test_id_returns_400(self):
        event = self._build_event("PUT", "/tests", body={"action": "start"}, path_params={})
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)

    @patch('functions.tests.main.TestRepository')
    def test_put_test_not_found_returns_404(self, mock_repo):
        mock_repo.start_test.return_value = None 
        event = self._build_event("PUT", "/tests/99", body={"action": "start"}, path_params={"test_id": "99"})
        
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 404)
        self.assertIn("Test not found", json.loads(result["body"])["error"])

    # DELETE /tests/{test_id}

    @patch('functions.tests.main.TestRepository')
    def test_delete_test_soft_delete_returns_200(self, mock_repo):
        mock_repo.soft_delete.return_value = {"test_id": "42", "status": "ARCHIVED"}
        event = self._build_event("DELETE", "/tests/42", path_params={"test_id": "42"})
        
        result = tests_main.lambda_handler(event, None)
        
        mock_repo.soft_delete.assert_called_once_with("42")
        self.assertEqual(result["statusCode"], 200)

    @patch('functions.tests.main.TestRepository')
    def test_delete_test_hard_delete_returns_200(self, mock_repo):
        mock_repo.hard_delete.return_value = {"test_id": "42"}
        event = self._build_event("DELETE", "/tests/42", path_params={"test_id": "42"}, query_params={"hard": "true"})
        
        result = tests_main.lambda_handler(event, None)
        
        mock_repo.hard_delete.assert_called_once_with("42")
        self.assertEqual(result["statusCode"], 200)

    def test_delete_missing_test_id_returns_400(self):
        event = self._build_event("DELETE", "/tests", path_params={})
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)

    @patch('functions.tests.main.TestRepository')
    def test_delete_test_not_found_returns_404(self, mock_repo):
        mock_repo.soft_delete.return_value = None
        event = self._build_event("DELETE", "/tests/99", path_params={"test_id": "99"})
        
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 404)

    def test_unsupported_method_returns_405(self):
        event = self._build_event("PATCH", "/tests")
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 405)
        self.assertIn("Method not allowed", json.loads(result["body"])["error"])
    
    # Exception Handling

    @patch('functions.tests.main.Logger')
    @patch('functions.tests.main.TestRepository')
    def test_exception_returns_500(self, mock_repo, mock_logger):
        mock_repo.get_tests_by_id.side_effect = Exception("Unexpected database crash")
        event = self._build_event("GET", "/tests/42", path_params={"test_id": "42"})
        
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 500)
        self.assertIn("Unexpected database crash", json.loads(result["body"])["error"])

    @patch('functions.tests.main.Logger')
    @patch('functions.tests.main.TestRepository')
    def test_exception_not_null_returns_400(self, mock_repo, mock_logger):
        mock_repo.create.side_effect = Exception("violates not-null constraint on column control_id")
        event = self._build_event("POST", "/tests", body={"vgcpid": "B", "request_id": 1, "requires_dat": True, "requires_oet": False, "due_date": "2026", "description": "C"})
        
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("provided vgcpid does not exist", json.loads(result["body"])["error"])

    @patch('functions.tests.main.Logger')
    @patch('functions.tests.main.TestRepository')
    def test_exception_foreign_key_returns_400(self, mock_repo, mock_logger):
        mock_repo.create.side_effect = Exception("violates foreign key constraint tests_request_id_fkey")
        event = self._build_event("POST", "/tests", body={"vgcpid": "B", "request_id": 1, "requires_dat": True, "requires_oet": False, "due_date": "2026", "description": "C"})
        
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("Invalid referenced ID", json.loads(result["body"])["error"])
