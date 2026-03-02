import json
from unittest import TestCase
from unittest.mock import patch
import functions.users.main as users


class TestUsersMain(TestCase):
    def _build_event(self, method, path, path_params=None, query_params=None):
        event = {
            "httpMethod": method,
            "path": path,
            "pathParameters": path_params or {},
            "queryStringParameters": query_params or {},
        }
        return event

    # Empty event

    @patch('functions.users.main.Logger')
    def test_empty_event_returns_400(self, mock_logger):
        result = users.lambda_handler({}, None)
        mock_logger.log.assert_any_call(level="ERROR", message="No event data provided")
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("No event data", json.loads(result["body"])["error"])

    # GET /users

    @patch('functions.users.main.Logger')
    @patch('functions.users.main.CrudUtils')
    def test_get_all_users_returns_200(self, mock_crud, mock_logger):
        mock_crud.get_all.return_value = [{"email": "a@x.com"}, {"email": "b@x.com"}]

        event = self._build_event("GET", "/users")
        result = users.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="INFO", message="Returning users", extra_fields={"count": 2})
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(len(json.loads(result["body"])), 2)

    @patch('functions.users.main.Logger')
    @patch('functions.users.main.CrudUtils')
    def test_get_user_by_email_returns_200(self, mock_crud, mock_logger):
        mock_crud.get_by_filter.return_value = [{"email": "andrew@example.com", "user_id": 5}]

        event = self._build_event("GET", "/users", query_params={"email": "andrew@example.com"})
        result = users.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="INFO", message="Users Function Started")
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["email"], "andrew@example.com")

    @patch('functions.users.main.Logger')
    @patch('functions.users.main.CrudUtils')
    def test_get_user_by_email_not_found_returns_404(self, mock_crud, mock_logger):
        mock_crud.get_by_filter.return_value = []

        event = self._build_event("GET", "/users", query_params={"email": "missing@example.com"})
        result = users.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="WARNING", message="User not found by email", extra_fields={"email": "missing@example.com"})
        self.assertEqual(result["statusCode"], 404)
        self.assertIn("User not found", json.loads(result["body"])["error"])

    @patch('functions.users.main.Logger')
    @patch('functions.users.main.CrudUtils')
    def test_get_active_users_query_param_returns_200(self, mock_crud, mock_logger):
        mock_crud.get_by_filter.return_value = [{"email": "a@x.com", "is_active": True}]

        event = self._build_event("GET", "/users", query_params={"is_active": "true"})
        result = users.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="INFO", message="Returning users filtered by is_active", extra_fields={"is_active": True, "count": 1})
        self.assertEqual(result["statusCode"], 200)

    # GET /users/{id}

    @patch('functions.users.main.Logger')
    @patch('functions.users.main.CrudUtils')
    def test_get_user_by_id_returns_200(self, mock_crud, mock_logger):
        mock_crud.get_by_id.return_value = {"user_id": 5, "email": "a@x.com"}

        event = self._build_event("GET", "/users/5", path_params={"id": "5"})
        result = users.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="INFO", message="Returning user", extra_fields={"user_id": "5"})
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["user_id"], 5)

    @patch('functions.users.main.Logger')
    @patch('functions.users.main.CrudUtils')
    def test_get_user_by_id_not_found_returns_404(self, mock_crud, mock_logger):
        mock_crud.get_by_id.return_value = None

        event = self._build_event("GET", "/users/999", path_params={"id": "999"})
        result = users.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="WARNING", message="User not found", extra_fields={"user_id": "999"})
        self.assertEqual(result["statusCode"], 404)
        self.assertIn("User not found", json.loads(result["body"])["error"])

    # DELETE /users/{id}

    @patch('functions.users.main.Logger')
    @patch('functions.users.main.CrudUtils')
    def test_delete_user_returns_200(self, mock_crud, mock_logger):
        mock_crud.deactivate.return_value = {"user_id": 9, "is_active": False}

        event = self._build_event("DELETE", "/users/9", path_params={"id": "9"})
        result = users.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="INFO", message="Deactivated user", extra_fields={"user_id": "9"})
        self.assertEqual(result["statusCode"], 200)
        self.assertFalse(json.loads(result["body"])["is_active"]) 

    @patch('functions.users.main.Logger')
    @patch('functions.users.main.CrudUtils')
    def test_delete_user_not_found_returns_404(self, mock_crud, mock_logger):
        mock_crud.deactivate.return_value = None

        event = self._build_event("DELETE", "/users/999", path_params={"id": "999"})
        result = users.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="WARNING", message="User not found for deactivate", extra_fields={"user_id": "999"})
        self.assertEqual(result["statusCode"], 404)

    @patch('functions.users.main.Logger')
    def test_delete_user_no_id_returns_400(self, mock_logger):
        event = self._build_event("DELETE", "/users/")
        result = users.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="ERROR", message="User ID not provided in path for delete")
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("User ID not provided", json.loads(result["body"])["error"])

    # Method not allowed

    @patch('functions.users.main.Logger')
    @patch('functions.users.main.CrudUtils')
    def test_unsupported_method_returns_405(self, mock_crud, mock_logger):
        event = self._build_event("PATCH", "/users")
        result = users.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 405)

    # Exception handling

    @patch('functions.users.main.Logger')
    @patch('functions.users.main.CrudUtils')
    def test_exception_returns_500(self, mock_crud, mock_logger):
        mock_crud.get_all.side_effect = Exception("Unexpected error")

        event = self._build_event("GET", "/users")
        result = users.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 500)
        self.assertIn("Unexpected error", json.loads(result["body"]) ["error"]) 
