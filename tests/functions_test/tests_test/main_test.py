import json
from unittest import TestCase
from unittest.mock import patch
import functions.tests.main as tests_main

class TestTestsMain(TestCase):
    def setUp(self):
        self.auth_patcher = patch('functions.tests.main.AuthUtils')
        self.mock_auth = self.auth_patcher.start()

    def tearDown(self):
        self.auth_patcher.stop()

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
        mock_repo.get_tests_by_id.return_value = {"test_id": "42", "status": "DAT_IN_PROGRESS"}
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
    def test_put_action_update_details_returns_200(self, mock_repo):
        # Mock the return value to match a successful update
        mock_repo.update_details.return_value = {"test_id": "42", "description": "Updated desc"}
        
        # Ensure action matches your code: "update_details"
        event = self._build_event("PUT", "/tests/42", body={
            "action": "update_details", 
            "description": "Updated desc",
            "vgcpid": "VGCP-1",
            "request_id": 1
        }, path_params={"test_id": "42"})
        
        result = tests_main.lambda_handler(event, None)
        
        # Verify the specific method and arguments are called
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["description"], "Updated desc")

    @patch('functions.tests.main.TestRepository')
    def test_put_action_assign_returns_200(self, mock_repo):
        mock_repo.update_assigned_tester.return_value = {"test_id": "42", "assigned_tester_id": "7"}
        event = self._build_event("PUT", "/tests/42", body={"action": "assign", "assigned_tester_id": "7"}, path_params={"test_id": "42"})
        
        result = tests_main.lambda_handler(event, None)
        
        mock_repo.update_assigned_tester.assert_called_once_with("42", "7")
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["assigned_tester_id"], "7")

    @patch('functions.tests.main.TestRepository')
    def test_put_action_assign_missing_tester_id_returns_400(self, mock_repo):
        event = self._build_event("PUT", "/tests/42", body={"action": "assign"}, path_params={"test_id": "42"})
        
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("assigned_tester_id is required", json.loads(result["body"])["error"])

    @patch('functions.tests.main.TestRepository')
    def test_put_action_start_returns_200(self, mock_repo):
        mock_repo.start_test.return_value = {"test_id": "42", "status": "OET_IN_PROGRESS"}
        event = self._build_event("PUT", "/tests/42", body={"action": "start"}, path_params={"test_id": "42"})
        
        result = tests_main.lambda_handler(event, None)
        
        mock_repo.start_test.assert_called_once_with("42")
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["status"], "OET_IN_PROGRESS")

    @patch('functions.tests.main.TestRepository')
    def test_put_action_update_dat_returns_200(self, mock_repo):
        mock_repo.update_dat_track.return_value = {"test_id": "42", "status": "DAT_IN_PROGRESS"}
        event = self._build_event("PUT", "/tests/42", body={"action": "update_dat", "dat_step": "Step 1", "status": "DAT_IN_PROGRESS"})
        event["pathParameters"] = {"test_id": "42", "id": "42"}
        
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 200)
        mock_repo.update_dat_track.assert_called_once()

    @patch('functions.tests.main.TestRepository')
    def test_put_action_update_oet_returns_200(self, mock_repo):
        mock_repo.update_oet_track.return_value = {"test_id": "42", "status": "OET_IN_PROGRESS"}
        event = self._build_event("PUT", "/tests/42", body={"action": "update_oet", "oet_step": "Step 1", "status": "OET_IN_PROGRESS"})
        event["pathParameters"] = {"test_id": "42", "id": "42"}
        
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 200)
        mock_repo.update_oet_track.assert_called_once()

    @patch('functions.tests.main.TestRepository')
    def test_put_action_review_returns_200(self, mock_repo):
        mock_repo.review_test.return_value = {"test_id": "42", "status": "IN_REVIEW"}
        event = self._build_event("PUT", "/tests/42", body={"action": "review"})
        event["pathParameters"] = {"test_id": "42", "id": "42"}
        
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 200)
        mock_repo.review_test.assert_called_once()

    @patch('functions.tests.main.TestRepository')
    def test_put_action_complete_returns_200(self, mock_repo):
        mock_repo.complete_test.return_value = {"test_id": "42", "status": "COMPLETED"}
        event = self._build_event("PUT", "/tests/42", body={"action": "complete"})
        event["pathParameters"] = {"test_id": "42", "id": "42"}
        
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 200)
        mock_repo.complete_test.assert_called_once()

    @patch('functions.tests.main.TestRepository')
    def test_put_action_update_evidence_links_returns_200(self, mock_repo):
        mock_repo.update_evidence_links.return_value = {
            "test_id": "42",
            "evidence_links": ["https://example.com/evidence"],
        }
        event = self._build_event(
            "PUT",
            "/tests/42",
            body={
                "action": "update_evidence_links",
                "evidence_links": ["https://example.com/evidence"],
            },
            path_params={"test_id": "42"},
        )

        result = tests_main.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        mock_repo.update_evidence_links.assert_called_once_with(
            "42", ["https://example.com/evidence"]
        )

    @patch('functions.tests.main.TestRepository')
    def test_put_action_update_evidence_links_missing_payload_returns_400(self, mock_repo):
        event = self._build_event(
            "PUT",
            "/tests/42",
            body={"action": "update_evidence_links"},
            path_params={"test_id": "42"},
        )

        result = tests_main.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 400)
        self.assertIn("evidence_links is required", json.loads(result["body"])["error"])

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
        
        mock_repo.soft_delete.assert_called_once_with("42", archive=True)
        self.assertEqual(result["statusCode"], 200)

    @patch('functions.tests.main.TestRepository')
    def test_delete_test_soft_unarchive_returns_200(self, mock_repo):
        mock_repo.soft_delete.return_value = {"test_id": "42", "status": "NOT_STARTED"}
        event = self._build_event(
            "DELETE",
            "/tests/42",
            path_params={"test_id": "42"},
            query_params={"archive": "false"},
        )

        result = tests_main.lambda_handler(event, None)

        mock_repo.soft_delete.assert_called_once_with("42", archive=False)
        self.assertEqual(result["statusCode"], 200)

    @patch('functions.tests.main.TestRepository')
    def test_delete_test_soft_delete_not_found_returns_404(self, mock_repo):
        mock_repo.soft_delete.return_value = None
        event = self._build_event("DELETE", "/tests/42", path_params={"test_id": "42"})
        
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 404)
        self.assertIn("Test not found", json.loads(result["body"])["error"])

    @patch('functions.tests.main.TestRepository')
    def test_delete_test_not_found_returns_404(self, mock_repo):
        mock_repo.soft_delete.return_value = None
        event = self._build_event("DELETE", "/tests/99", path_params={"test_id": "99"})
        
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 404)

    def test_delete_missing_test_id_returns_400(self):
        event = self._build_event("DELETE", "/tests", path_params={})
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)

    @patch('functions.tests.main.TestRepository')
    def test_delete_test_hard_delete_returns_200(self, mock_repo):
        mock_repo.hard_delete.return_value = {"test_id": "42"}
        event = self._build_event("DELETE", "/tests/42", path_params={"test_id": "42"}, query_params={"hard": "true"})
        
        result = tests_main.lambda_handler(event, None)
        
        mock_repo.hard_delete.assert_called_once_with("42")
        self.assertEqual(result["statusCode"], 200)

    @patch('functions.tests.main.TestRepository')
    def test_delete_hard_delete_not_found_returns_404(self, mock_repo):
        mock_repo.get_tests_by_id.return_value = None
        event = self._build_event("DELETE", "/tests/42", query_params={"hard": "true"})
        event["pathParameters"] = {"test_id": "42", "id": "42"}
        
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
    def test_exception_not_null_but_not_control_id(self, mock_repo, mock_logger):
        # Triggers the 'if "violates not-null constraint"' but misses the '"control_id" in error_message' side of the AND
        mock_repo.create.side_effect = Exception("violates not-null constraint on column some_other_column")
        event = self._build_event("POST", "/tests", body={
            "vgcpid": "B", "request_id": 1, "requires_dat": True, 
            "requires_oet": False, "due_date": "2026", "description": "C"
        })
        
        result = tests_main.lambda_handler(event, None)
        
        # Since it misses the first IF block, it must drop safely to the 500 error
        self.assertEqual(result["statusCode"], 500)

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

    @patch('functions.tests.main.TestRepository')
    def test_get_with_none_query_params(self, mock_repo):
        mock_repo.get_all_tests.return_value = []
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

    @patch('functions.tests.main.TestRepository')
    def test_put_action_update_evidence_links_not_list_returns_400(self, mock_repo):
        event = self._build_event(
            "PUT",
            "/tests/42",
            body={
                "action": "update_evidence_links",
                "evidence_links": "not a list",  # Invalid: string instead of list
            },
            path_params={"test_id": "42"},
        )

        result = tests_main.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 400)
        self.assertIn("evidence_links must be a list", json.loads(result["body"])["error"])

    # Authorization checks

    @patch('functions.tests.main.Logger')
    @patch('functions.tests.main.TestRepository')
    def test_post_test_non_manager_returns_403(self, mock_repo, mock_logger):
        self.mock_auth.is_manager.return_value = False
        body = {
            "vgcpid": "VGCP-001", "request_id": 100, "requires_dat": True, 
            "requires_oet": False, "due_date": "2026-03-01", "description": "Test control"
        }
        event = self._build_event("POST", "/tests", body=body)
        
        result = tests_main.lambda_handler(event, None)
        
        mock_repo.create.assert_not_called()
        mock_logger.log.assert_any_call(level="WARNING", message="Unauthorized test creation attempt")
        self.assertEqual(result["statusCode"], 403)
        self.assertIn("Forbidden", json.loads(result["body"])["error"])

    @patch('functions.tests.main.TestRepository')
    def test_put_test_non_manager_non_tester_returns_403(self, mock_repo):
        self.mock_auth.is_manager.return_value = False
        self.mock_auth.is_tester.return_value = False
        
        event = self._build_event("PUT", "/tests/42", body={"action": "start"}, path_params={"test_id": "42"})
        result = tests_main.lambda_handler(event, None)
        
        mock_repo.start_test.assert_not_called()
        self.assertEqual(result["statusCode"], 403)
        self.assertIn("Forbidden", json.loads(result["body"])["error"])

    @patch('functions.tests.main.Logger')
    @patch('functions.tests.main.TestRepository')
    def test_delete_test_non_manager_returns_403(self, mock_repo, mock_logger):
        self.mock_auth.is_manager.return_value = False
        
        event = self._build_event("DELETE", "/tests/42", path_params={"test_id": "42"})
        result = tests_main.lambda_handler(event, None)
        
        mock_repo.soft_delete.assert_not_called()
        mock_logger.log.assert_any_call(level="WARNING", message="Unauthorized test deletion attempt")
        self.assertEqual(result["statusCode"], 403)
        self.assertIn("Forbidden", json.loads(result["body"])["error"])

    # Hard delete constraints

    @patch('functions.tests.main.Logger')
    @patch('functions.tests.main.TestRepository')
    def test_hard_delete_completed_test_returns_409(self, mock_repo, mock_logger):
        completed_test = {"test_id": "42", "status": "COMPLETED"}
        mock_repo.get_tests_by_id.return_value = completed_test
        
        event = self._build_event("DELETE", "/tests/42", path_params={"test_id": "42"}, query_params={"hard": "true"})
        result = tests_main.lambda_handler(event, None)
        
        mock_repo.hard_delete.assert_not_called()
        mock_logger.log.assert_any_call(
            level="WARNING",
            message="Cannot hard delete completed test",
            extra_fields={"test_id": "42", "status": "COMPLETED"}
        )
        self.assertEqual(result["statusCode"], 409)
        self.assertIn("Cannot hard delete completed", json.loads(result["body"])["error"])

    @patch('functions.tests.main.Logger')
    @patch('functions.tests.main.TestRepository')
    def test_delete_test_not_found_returns_404(self, mock_repo, mock_logger):
        mock_repo.soft_delete.return_value = None
        event = self._build_event("DELETE", "/tests/99", path_params={"test_id": "99"})
        
        result = tests_main.lambda_handler(event, None)
        
        mock_repo.soft_delete.assert_called_once_with("99", archive=True)
        self.assertEqual(result["statusCode"], 404)
        self.assertIn("Test not found", json.loads(result["body"])["error"])

    # Update status action

    @patch('functions.tests.main.TestRepository')
    def test_put_action_update_status_returns_200(self, mock_repo):
        mock_repo.update_status.return_value = {"test_id": "42", "status": "IN_REVIEW"}
        event = self._build_event("PUT", "/tests/42", body={"action": "update_status", "status": "IN_REVIEW"}, path_params={"test_id": "42"})
        
        result = tests_main.lambda_handler(event, None)
        
        mock_repo.update_status.assert_called_once_with("42", "IN_REVIEW")
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["status"], "IN_REVIEW")

    @patch('functions.tests.main.TestRepository')
    def test_put_action_update_status_missing_status_returns_400(self, mock_repo):
        event = self._build_event("PUT", "/tests/42", body={"action": "update_status"}, path_params={"test_id": "42"})
        
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("status is required", json.loads(result["body"])["error"])

    # OPTIONS preflight

    @patch('functions.tests.main.Logger')
    def test_options_request_returns_cors_preflight(self, mock_logger):
        event = {"httpMethod": "OPTIONS", "path": "/tests"}
        result = tests_main.lambda_handler(event, None)
        
        self.assertEqual(result["statusCode"], 200)
        self.assertIn("Access-Control-Allow-Origin", result["headers"])

    def test_put_with_missing_body_key(self):
        event = self._build_event("PUT", "/tests/42", path_params={"test_id": "42"})
        event.pop("body", None)
        
        result = tests_main.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("Invalid or missing action", json.loads(result["body"])["error"])
