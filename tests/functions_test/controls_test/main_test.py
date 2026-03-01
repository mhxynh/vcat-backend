import json
from unittest import TestCase
from unittest.mock import patch
import functions.controls.main as controls
from functions.common.python.utils.response import ResponseUtils

class TestControlsMain(TestCase):
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

    # Empty event

    @patch('functions.controls.main.Logger')
    def test_empty_event_returns_400(self, mock_logger):
        result = controls.lambda_handler({}, None)
        mock_logger.log.assert_any_call(level="ERROR", message="No event data provided")
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("No event data", json.loads(result["body"])["error"])

    # GET /controls

    @patch('functions.controls.main.Logger')
    @patch('functions.controls.main.CrudUtils')
    def test_get_all_controls_returns_200(self, mock_crud, mock_logger):
        mock_crud.get_all.return_value = [{"vgcpid": "VGCP-001"}, {"vgcpid": "VGCP-002"}]

        event = self._build_event("GET", "/controls")
        result = controls.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="INFO", message="Returning controls", extra_fields={"count": 2})
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(len(json.loads(result["body"])), 2)

    # GET /controls/{vgcpid}

    @patch('functions.controls.main.Logger')
    @patch('functions.controls.main.CrudUtils')
    def test_get_control_by_id_returns_200(self, mock_crud, mock_logger):
        mock_crud.get_by_id.return_value = {"vgcpid": "VGCP-001", "description": "Test"}

        event = self._build_event("GET", "/controls/VGCP-001", path_params={"vgcpid": "VGCP-001"})
        result = controls.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="INFO", message="Returning control", extra_fields={"vgcpid": "VGCP-001"})
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["vgcpid"], "VGCP-001")

    @patch('functions.controls.main.Logger')
    @patch('functions.controls.main.CrudUtils')
    def test_get_control_not_found_returns_404(self, mock_crud, mock_logger):
        mock_crud.get_by_id.return_value = None

        event = self._build_event("GET", "/controls/VGCP-999", path_params={"vgcpid": "VGCP-999"})
        result = controls.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="WARNING", message="Control not found", extra_fields={"vgcpid": "VGCP-999"})
        self.assertEqual(result["statusCode"], 404)
        self.assertIn("Control not found", json.loads(result["body"])["error"])

    # POST /controls
    
    @patch('functions.controls.main.Logger')
    @patch('functions.controls.main.CrudUtils')
    def test_post_control_returns_200(self, mock_crud, mock_logger):
        new_control = {"vgcpid": "VGCP-999", "description": "New", "control_owner": "Owner", "escalation": True}
        mock_crud.create.return_value = {**new_control, "control_id": 10}

        event = self._build_event("POST", "/controls", body=new_control)
        result = controls.lambda_handler(event, None)

        mock_crud.create.assert_called_once()
        mock_logger.log.assert_any_call(level="INFO", message="Created control", extra_fields={"vgcpid": "VGCP-999"})
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["vgcpid"], "VGCP-999")

    @patch('functions.controls.main.Logger')
    @patch('functions.controls.main.CrudUtils')
    def test_post_control_missing_fields_returns_400(self, mock_crud, mock_logger):
        event = self._build_event("POST", "/controls", body={"vgcpid": "VGCP-999"})
        result = controls.lambda_handler(event, None)

        mock_crud.create.assert_not_called()
        mock_logger.log.assert_any_call(level="ERROR", message="Missing fields in request body", extra_fields={"missing_fields": ["description", "control_owner", "escalation"]})
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("missing", json.loads(result["body"]))

    # PUT /controls/{vgcpid}

    @patch('functions.controls.main.Logger')
    @patch('functions.controls.main.CrudUtils')
    def test_put_control_returns_200(self, mock_crud, mock_logger):
        mock_crud.update.return_value = {"vgcpid": "VGCP-001", "description": "Updated"}

        event = self._build_event("PUT", "/controls/VGCP-001", body={"description": "Updated"}, path_params={"vgcpid": "VGCP-001"})
        result = controls.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="INFO", message="Updated control", extra_fields={"vgcpid": "VGCP-001"})
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["description"], "Updated")

    @patch('functions.controls.main.Logger')
    @patch('functions.controls.main.CrudUtils')
    def test_put_control_not_found_returns_404(self, mock_crud, mock_logger):
        mock_crud.update.return_value = None

        event = self._build_event("PUT", "/controls/VGCP-999", body={"description": "X"}, path_params={"vgcpid": "VGCP-999"})
        result = controls.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="WARNING", message="Control not found", extra_fields={"vgcpid": "VGCP-999"})
        self.assertEqual(result["statusCode"], 404)

    @patch('functions.controls.main.Logger')
    @patch('functions.controls.main.CrudUtils')
    def test_put_control_no_body_returns_400(self, mock_crud, mock_logger):
        event = self._build_event("PUT", "/controls/VGCP-001", body={}, path_params={"vgcpid": "VGCP-001"})
        result = controls.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="ERROR", message="No update data provided")
        self.assertEqual(result["statusCode"], 400)

    @patch('functions.controls.main.Logger')
    @patch('functions.controls.main.CrudUtils')
    def test_put_control_invalid_fields_returns_400(self, mock_crud, mock_logger):
        event = self._build_event("PUT", "/controls/VGCP-001", body={"bad_field": "X"}, path_params={"vgcpid": "VGCP-001"})
        result = controls.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="ERROR", message="No valid fields to update")
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("allowed", json.loads(result["body"]))

    @patch('functions.controls.main.Logger')
    @patch('functions.controls.main.CrudUtils')
    def test_put_control_missing_vgcpid_returns_400(self, mock_crud, mock_logger):
        event = self._build_event("PUT", "/controls/", body={"description": "X"}, path_params={})
        result = controls.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="ERROR", message="VGCPID not provided in path")
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("VGCPID not provided", json.loads(result["body"])["error"])

    # DELETE /controls/{vgcpid}

    @patch('functions.controls.main.Logger')
    @patch('functions.controls.main.CrudUtils')
    def test_delete_control_returns_200(self, mock_crud, mock_logger):
        mock_crud.deactivate.return_value = {"vgcpid": "VGCP-001", "is_active": False}

        event = self._build_event("DELETE", "/controls/VGCP-001", path_params={"vgcpid": "VGCP-001"})
        result = controls.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="INFO", message="Deactivated control", extra_fields={"vgcpid": "VGCP-001"})
        self.assertEqual(result["statusCode"], 200)
        self.assertFalse(json.loads(result["body"])["is_active"])

    @patch('functions.controls.main.Logger')
    @patch('functions.controls.main.CrudUtils')
    def test_delete_control_hard_delete_returns_200(self, mock_crud, mock_logger):
        mock_crud.hard_delete.return_value = {"vgcpid": "VGCP-001"}

        event = self._build_event("DELETE", "/controls/VGCP-001", path_params={"vgcpid": "VGCP-001"}, query_params={"hard": "true"})
        result = controls.lambda_handler(event, None)

        mock_crud.hard_delete.assert_called_once_with("controls", "vgcpid", "VGCP-001")
        mock_logger.log.assert_any_call(level="INFO", message="Hard deleted control", extra_fields={"vgcpid": "VGCP-001"})
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["vgcpid"], "VGCP-001")

    @patch('functions.controls.main.Logger')
    @patch('functions.controls.main.CrudUtils')
    def test_delete_control_not_found_returns_404(self, mock_crud, mock_logger):
        mock_crud.deactivate.return_value = None

        event = self._build_event("DELETE", "/controls/VGCP-999", path_params={"vgcpid": "VGCP-999"})
        result = controls.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="WARNING", message="Control not found for deactivate", extra_fields={"vgcpid": "VGCP-999"})
        self.assertEqual(result["statusCode"], 404)
        self.assertIn("Control not found", json.loads(result["body"])["error"])

    @patch('functions.controls.main.Logger')
    @patch('functions.controls.main.CrudUtils')
    def test_delete_control_hard_delete_not_found_returns_404(self, mock_crud, mock_logger):
        mock_crud.hard_delete.return_value = None

        event = self._build_event("DELETE", "/controls/VGCP-999", path_params={"vgcpid": "VGCP-999"}, query_params={"hard": "true"})
        result = controls.lambda_handler(event, None)

        mock_crud.hard_delete.assert_called_once_with("controls", "vgcpid", "VGCP-999")
        mock_logger.log.assert_any_call(level="WARNING", message="Control not found for hard delete", extra_fields={"vgcpid": "VGCP-999"})
        self.assertEqual(result["statusCode"], 404)
        self.assertIn("Control not found", json.loads(result["body"])["error"])

    @patch('functions.controls.main.Logger')
    @patch('functions.controls.main.CrudUtils')
    def test_delete_control_missing_vgcpid_returns_400(self, mock_crud, mock_logger):
        event = self._build_event("DELETE", "/controls/", path_params={})
        result = controls.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="ERROR", message="VGCPID not provided in path for delete")
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("VGCPID not provided", json.loads(result["body"])["error"])

    # Method not allowed

    @patch('functions.controls.main.Logger')
    @patch('functions.controls.main.CrudUtils')
    def test_unsupported_method_returns_405(self, mock_crud, mock_logger):
        event = self._build_event("PATCH", "/controls")
        result = controls.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 405)

    # Exception handling

    @patch('functions.controls.main.Logger')
    @patch('functions.controls.main.CrudUtils')
    def test_exception_returns_500(self, mock_crud, mock_logger):
        mock_crud.get_all.side_effect = Exception("Unexpected error")

        event = self._build_event("GET", "/controls")
        result = controls.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 500)
        self.assertIn("Unexpected error", json.loads(result["body"])["error"])
