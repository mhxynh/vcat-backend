import json
from unittest import TestCase
from unittest.mock import patch
import functions.requests.main as requests


class TestRequestsMain(TestCase):
	def setUp(self):
		self.auth_patcher = patch('functions.requests.main.AuthUtils')
		self.mock_auth = self.auth_patcher.start()

	def tearDown(self):
		self.auth_patcher.stop()

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

	@patch('functions.requests.main.Logger')
	def test_empty_event_returns_400(self, mock_logger):
		result = requests.lambda_handler({}, None)
		mock_logger.log.assert_any_call(level="ERROR", message="No event data provided")
		self.assertEqual(result["statusCode"], 400)
		self.assertIn("No event data", json.loads(result["body"])['error'])

	# GET /requests

	@patch('functions.requests.main.Logger')
	@patch('functions.requests.main.CrudUtils')
	def test_get_all_requests_returns_200(self, mock_crud, mock_logger):
		mock_crud.get_all.return_value = [{"request_id": 1}, {"request_id": 2}]

		event = self._build_event("GET", "/requests")
		result = requests.lambda_handler(event, None)

		mock_logger.log.assert_any_call(level="INFO", message="Returning requests", extra_fields={"count": 2})
		self.assertEqual(result["statusCode"], 200)
		self.assertEqual(len(json.loads(result["body"])), 2)

	# GET /requests/{id}

	@patch('functions.requests.main.Logger')
	@patch('functions.requests.main.CrudUtils')
	def test_get_request_by_id_returns_200(self, mock_crud, mock_logger):
		mock_crud.get_by_id.return_value = {"request_id": 42, "requestor": "a"}

		event = self._build_event("GET", "/requests/42", path_params={"id": "42"})
		result = requests.lambda_handler(event, None)

		mock_logger.log.assert_any_call(level="INFO", message="Returning request", extra_fields={"request_id": '42'})
		self.assertEqual(result["statusCode"], 200)
		self.assertEqual(json.loads(result["body"])["request_id"], 42)

	@patch('functions.requests.main.Logger')
	@patch('functions.requests.main.CrudUtils')
	def test_get_request_not_found_returns_404(self, mock_crud, mock_logger):
		mock_crud.get_by_id.return_value = None

		event = self._build_event("GET", "/requests/999", path_params={"id": "999"})
		result = requests.lambda_handler(event, None)

		mock_logger.log.assert_any_call(level="WARNING", message="Request not found", extra_fields={"request_id": '999'})
		self.assertEqual(result["statusCode"], 404)
		self.assertIn("Request not found", json.loads(result["body"])['error'])

	# POST /requests

	@patch('functions.requests.main.Logger')
	@patch('functions.requests.main.CrudUtils')
	def test_post_request_returns_200(self, mock_crud, mock_logger):
		new_req = {"requestor": "random", "created_by": 1, "due_date": "2026-03-01", "priority": "HIGH"}
		mock_crud.create.return_value = {**new_req, "request_id": 10}

		event = self._build_event("POST", "/requests", body=new_req)
		result = requests.lambda_handler(event, None)

		mock_crud.create.assert_called_once()
		mock_logger.log.assert_any_call(level="INFO", message="Created request", extra_fields={"request_id": 10})
		self.assertEqual(result["statusCode"], 200)
		self.assertEqual(json.loads(result["body"])["request_id"], 10)

	@patch('functions.requests.main.Logger')
	@patch('functions.requests.main.CrudUtils')
	def test_post_request_missing_fields_returns_400(self, mock_crud, mock_logger):
		event = self._build_event("POST", "/requests", body={"requestor": "x"})
		result = requests.lambda_handler(event, None)

		mock_crud.create.assert_not_called()
		mock_logger.log.assert_any_call(level="ERROR", message="Missing fields in request body", extra_fields={"missing": ['due_date', 'priority', 'created_by']})
		self.assertEqual(result["statusCode"], 400)
		self.assertIn("missing", json.loads(result["body"]))

	# PUT /requests/{id}

	@patch('functions.requests.main.Logger')
	@patch('functions.requests.main.CrudUtils')
	def test_put_request_updates_status_returns_200(self, mock_crud, mock_logger):
		mock_crud.update.return_value = {"request_id": 42, "priority": "HIGH"}

		event = self._build_event("PUT", "/requests/42", body={"priority": "HIGH"}, path_params={"id": "42"})
		result = requests.lambda_handler(event, None)

		mock_logger.log.assert_any_call(level="INFO", message="Updated request", extra_fields={"request_id": '42', "updates": {'priority': 'HIGH'}})
		self.assertEqual(result["statusCode"], 200)
		self.assertEqual(json.loads(result["body"])["priority"], "HIGH")

	@patch('functions.requests.main.Logger')
	@patch('functions.requests.main.CrudUtils')
	def test_put_request_not_found_returns_404(self, mock_crud, mock_logger):
		mock_crud.update.return_value = None

		event = self._build_event("PUT", "/requests/999", body={"priority": "HIGH"}, path_params={"id": "999"})
		result = requests.lambda_handler(event, None)

		mock_logger.log.assert_any_call(level="WARNING", message="Request not found for update", extra_fields={"request_id": '999'})
		self.assertEqual(result["statusCode"], 404)

	@patch('functions.requests.main.Logger')
	@patch('functions.requests.main.CrudUtils')
	def test_put_request_no_body_returns_400(self, mock_crud, mock_logger):
		event = self._build_event("PUT", "/requests/42", body={}, path_params={"id": "42"})
		result = requests.lambda_handler(event, None)

		mock_logger.log.assert_any_call(level="ERROR", message="No update data provided")
		self.assertEqual(result["statusCode"], 400)

	@patch('functions.requests.main.Logger')
	@patch('functions.requests.main.CrudUtils')
	def test_put_request_invalid_fields_returns_400(self, mock_crud, mock_logger):
		event = self._build_event("PUT", "/requests/42", body={"bad": "x"}, path_params={"id": "42"})
		result = requests.lambda_handler(event, None)

		mock_logger.log.assert_any_call(level="ERROR", message="No valid fields to update")
		self.assertEqual(result["statusCode"], 400)
		self.assertIn("allowed", json.loads(result["body"]))

	@patch('functions.requests.main.Logger')
	@patch('functions.requests.main.CrudUtils')
	def test_put_request_missing_id_returns_400(self, mock_crud, mock_logger):
		event = self._build_event("PUT", "/requests/", body={"status": "IN_PROGRESS"}, path_params={})
		result = requests.lambda_handler(event, None)

		mock_logger.log.assert_any_call(level="ERROR", message="Request ID not provided in path for update")
		self.assertEqual(result["statusCode"], 400)
		self.assertIn("Request ID not provided", json.loads(result["body"])["error"])

	# DELETE /requests/{id}

	@patch('functions.requests.main.Logger')
	@patch('functions.requests.main.CrudUtils')
	def test_delete_request_soft_archive_returns_200(self, mock_crud, mock_logger):
		mock_crud.update.return_value = {"request_id": 42, "status": "ARCHIVED"}

		event = self._build_event("DELETE", "/requests/42", path_params={"id": "42"})
		result = requests.lambda_handler(event, None)

		mock_logger.log.assert_any_call(level="INFO", message="Archived request", extra_fields={"request_id": '42'})
		self.assertEqual(result["statusCode"], 200)
		self.assertEqual(json.loads(result["body"])["status"], "ARCHIVED")

	@patch('functions.requests.main.Logger')
	@patch('functions.requests.main.CrudUtils')
	def test_delete_request_hard_delete_returns_200(self, mock_crud, mock_logger):
		mock_crud.hard_delete.return_value = {"request_id": 42}

		event = self._build_event("DELETE", "/requests/42", path_params={"id": "42"}, query_params={"hard": "true"})
		result = requests.lambda_handler(event, None)

		mock_crud.hard_delete.assert_called_once_with("requests", "request_id", '42')
		mock_logger.log.assert_any_call(level="INFO", message="Hard deleted request", extra_fields={"request_id": '42'})
		self.assertEqual(result["statusCode"], 200)
		self.assertEqual(json.loads(result["body"])["request_id"], 42)

	@patch('functions.requests.main.Logger')
	@patch('functions.requests.main.CrudUtils')
	def test_delete_request_not_found_returns_404(self, mock_crud, mock_logger):
		mock_crud.update.return_value = None

		event = self._build_event("DELETE", "/requests/999", path_params={"id": "999"})
		result = requests.lambda_handler(event, None)

		mock_logger.log.assert_any_call(level="WARNING", message="Request not found for archive", extra_fields={"request_id": '999'})
		self.assertEqual(result["statusCode"], 404)
		self.assertIn("Request not found", json.loads(result["body"])['error'])

	@patch('functions.requests.main.Logger')
	@patch('functions.requests.main.CrudUtils')
	def test_delete_request_hard_delete_not_found_returns_404(self, mock_crud, mock_logger):
		mock_crud.hard_delete.return_value = None

		event = self._build_event("DELETE", "/requests/999", path_params={"id": "999"}, query_params={"hard": "true"})
		result = requests.lambda_handler(event, None)

		mock_crud.hard_delete.assert_called_once_with("requests", "request_id", '999')
		mock_logger.log.assert_any_call(level="WARNING", message="Request not found for hard delete", extra_fields={"request_id": '999'})
		self.assertEqual(result["statusCode"], 404)
		self.assertIn("Request not found", json.loads(result["body"])['error'])

	@patch('functions.requests.main.Logger')
	@patch('functions.requests.main.CrudUtils')
	def test_delete_request_missing_id_returns_400(self, mock_crud, mock_logger):
		event = self._build_event("DELETE", "/requests/", path_params={})
		result = requests.lambda_handler(event, None)

		mock_logger.log.assert_any_call(level="ERROR", message="Request ID not provided in path for delete")
		self.assertEqual(result["statusCode"], 400)
		self.assertIn("Request ID not provided", json.loads(result["body"])["error"])

	# Method not allowed

	@patch('functions.requests.main.Logger')
	@patch('functions.requests.main.CrudUtils')
	def test_unsupported_method_returns_405(self, mock_crud, mock_logger):
		event = self._build_event("PATCH", "/requests")
		result = requests.lambda_handler(event, None)

		self.assertEqual(result["statusCode"], 405)

	# Exception handling

	@patch('functions.requests.main.Logger')
	@patch('functions.requests.main.CrudUtils')
	def test_exception_returns_500(self, mock_crud, mock_logger):
		mock_crud.get_all.side_effect = Exception("Unexpected error")

		event = self._build_event("GET", "/requests")
		result = requests.lambda_handler(event, None)

		self.assertEqual(result["statusCode"], 500)
		self.assertIn("Unexpected error", json.loads(result["body"])["error"])
