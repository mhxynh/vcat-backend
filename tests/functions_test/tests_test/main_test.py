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

    @patch('functions.tests.main.CrudUtils')
    def test_get_test_by_id_returns_200(self, mock_crud):
        mock_crud.get_by_id.return_value = {"test_id": "42", "status": "IN_PROGRESS"}
        event = self._build_event("GET", "/tests/42", path_params={"test_id": "42"})
        
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["test_id"], "42")

    @patch('functions.tests.main.CrudUtils')
    def test_get_test_by_id_not_found_returns_404(self, mock_crud):
        mock_crud.get_by_id.return_value = None
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

    @patch('functions.tests.main.CrudUtils')
    def test_get_tests_by_request_id_only_returns_200(self, mock_crud):
        mock_crud.get_by_filter.return_value = [{"test_id": "1", "request_id": "100"}]
        
        event = self._build_event("GET", "/tests", query_params={"request_id": "100"})
        result = tests_main.lambda_handler(event, None)
        
        mock_crud.get_by_filter.assert_called_once_with("tests", "request_id", "100")
        self.assertEqual(result["statusCode"], 200)

    @patch('functions.tests.main.CrudUtils')
    def test_get_tests_by_control_id_returns_200(self, mock_crud):
        mock_crud.get_by_filter.return_value = [{"test_id": "1", "control_id": "20"}]
        event = self._build_event("GET", "/tests", query_params={"control_id": "20"})
        
        result = tests_main.lambda_handler(event, None)
        
        mock_crud.get_by_filter.assert_called_once_with("tests", "control_id", "20")
        self.assertEqual(result["statusCode"], 200)

    def test_get_tests_missing_params_returns_400(self):
        event = self._build_event("GET", "/tests") # No query params
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("Must provide request_id or control_id", json.loads(result["body"])["error"])

    # POST /tests

    @patch('functions.tests.main.CrudUtils')
    def test_post_test_returns_200(self, mock_crud):
        body = {
            "control_id": 20, "request_id": 100, "requires_dat": True, 
            "requires_oet": False, "due_date": "2026-03-01", "assigned_tester_id": 5
        }
        mock_crud.create.return_value = {**body, "test_id": 1}
        event = self._build_event("POST", "/tests", body=body)
        
        result = tests_main.lambda_handler(event, None)
        
        mock_crud.create.assert_called_once()
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["test_id"], 1)

    @patch('functions.tests.main.CrudUtils')
    def test_post_test_with_only_required_fields(self, mock_crud):
        body = {
            "control_id": 20, "request_id": 100, "requires_dat": True, 
            "requires_oet": False, "due_date": "2026-03-01"
            # Explicitly leaving out assigned_tester_id, estimated_date, and description
        }
        mock_crud.create.return_value = {"test_id": 1}
        event = self._build_event("POST", "/tests", body=body)
        
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 200)

    @patch('functions.tests.main.CrudUtils')
    def test_post_test_with_all_optional_fields_returns_200(self, mock_crud):
        body = {
            "control_id": 20, "request_id": 100, "requires_dat": True, 
            "requires_oet": False, "due_date": "2026-03-01",
            "assigned_tester_id": 5, "estimated_date": "2026-03-05", "description": "Test details"
        }
        mock_crud.create.return_value = {"test_id": 1}
        event = self._build_event("POST", "/tests", body=body)
        
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 200)
        # Verify that CrudUtils.create was called with the optional columns
        called_columns = mock_crud.create.call_args[0][1]
        self.assertIn("estimated_date", called_columns)
        self.assertIn("description", called_columns)

    def test_post_test_missing_required_returns_400(self):
        body = {"control_id": 20} # Missing request_id, requires_dat, etc.
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

    @patch('functions.tests.main.TestRepository')
    def test_put_action_update_dat_returns_200(self, mock_repo):
        mock_repo.update_dat_track.return_value = {"test_id": "42", "dat_step": "Phase 2"}
        event = self._build_event("PUT", "/tests/42", body={"action": "update_dat", "dat_step": "Phase 2", "status": "IN_PROGRESS"}, path_params={"test_id": "42"})
        
        result = tests_main.lambda_handler(event, None)
        
        mock_repo.update_dat_track.assert_called_once_with("42", "Phase 2", "IN_PROGRESS")
        self.assertEqual(result["statusCode"], 200)

    @patch('functions.tests.main.TestRepository')
    def test_put_action_update_oet_returns_200(self, mock_repo):
        mock_repo.update_oet_track.return_value = {"test_id": "42"}
        event = self._build_event("PUT", "/tests/42", body={"action": "update_oet", "oet_step": "Step 1", "status": "IN_PROGRESS"}, path_params={"test_id": "42"})
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 200)

    @patch('functions.tests.main.TestRepository')
    def test_put_action_review_returns_200(self, mock_repo):
        mock_repo.review_test.return_value = {"test_id": "42"}
        event = self._build_event("PUT", "/tests/42", body={"action": "review"}, path_params={"test_id": "42"})
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 200)

    @patch('functions.tests.main.TestRepository')
    def test_put_action_complete_returns_200(self, mock_repo):
        mock_repo.complete_test.return_value = {"test_id": "42"}
        event = self._build_event("PUT", "/tests/42", body={"action": "complete"}, path_params={"test_id": "42"})
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 200)

    @patch('functions.tests.main.CrudUtils')
    def test_put_fallback_generic_update_returns_200(self, mock_crud):
        mock_crud.update.return_value = {"test_id": "42", "assigned_tester_id": 99}
        event = self._build_event("PUT", "/tests/42", body={"assigned_tester_id": 99}, path_params={"test_id": "42"})
        
        result = tests_main.lambda_handler(event, None)
        
        mock_crud.update.assert_called_once_with("tests", "test_id", "42", {"assigned_tester_id": 99})
        self.assertEqual(result["statusCode"], 200)

    def test_put_test_invalid_fallback_fields_returns_404(self):
        event = self._build_event("PUT", "/tests/42", body={"garbage_field": "123"}, path_params={"test_id": "42"})
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 404)
        self.assertIn("invalid action provided", json.loads(result["body"])["error"])

    def test_put_missing_test_id_returns_400(self):
        event = self._build_event("PUT", "/tests", body={"action": "start"}, path_params={})
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)

    @patch('functions.tests.main.TestRepository')
    def test_put_test_not_found_returns_404(self, mock_repo):
        # Simulate the DB returning nothing
        mock_repo.start_test.return_value = None 
        event = self._build_event("PUT", "/tests/99", body={"action": "start"}, path_params={"test_id": "99"})
        
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 404)
        self.assertIn("Test not found", json.loads(result["body"])["error"])

    # DELETE /tests/{test_id}

    @patch('functions.tests.main.CrudUtils')
    def test_delete_test_returns_200(self, mock_crud):
        mock_crud.hard_delete.return_value = {"test_id": "42"}
        event = self._build_event("DELETE", "/tests/42", path_params={"test_id": "42"})
        
        result = tests_main.lambda_handler(event, None)
        
        mock_crud.hard_delete.assert_called_once_with("tests", "test_id", "42")
        self.assertEqual(result["statusCode"], 200)

    def test_delete_missing_test_id_returns_400(self):
        event = self._build_event("DELETE", "/tests", path_params={})
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)

    @patch('functions.tests.main.CrudUtils')
    def test_delete_test_not_found_returns_404(self, mock_crud):
        mock_crud.hard_delete.return_value = None
        event = self._build_event("DELETE", "/tests/99", path_params={"test_id": "99"})
        
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 404)

    def test_unsupported_method_returns_405(self):
        event = self._build_event("PATCH", "/tests")
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 405)
        self.assertIn("Method not allowed", json.loads(result["body"])["error"])

    # Helper Methods

    def test_extract_test_id_from_path_params(self):
        event = {"pathParameters": {"test_id": "42"}}
        result = tests_main.extract_test_id(event, "/tests/42")
        self.assertEqual(result, "42")

    def test_extract_test_id_from_raw_path(self):
        event = {"pathParameters": {}}
        result = tests_main.extract_test_id(event, "/tests/42")
        self.assertEqual(result, "42")

    def test_extract_test_id_handles_null_path_params(self):
        event = {"pathParameters": None}
        result = tests_main.extract_test_id(event, "/tests/42")
        self.assertEqual(result, "42")

    def test_extract_test_id_returns_none_for_base_path(self):
        event = {"pathParameters": None}
        result = tests_main.extract_test_id(event, "/tests")
        self.assertIsNone(result)
    
    # Exception Handling

    @patch('functions.tests.main.Logger')
    @patch('functions.tests.main.CrudUtils')
    def test_exception_returns_500(self, mock_crud, mock_logger):
        mock_crud.get_by_id.side_effect = Exception("Unexpected database crash")
        event = self._build_event("GET", "/tests/42", path_params={"test_id": "42"})
        
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 500)
        self.assertIn("Unexpected database crash", json.loads(result["body"])["error"])
