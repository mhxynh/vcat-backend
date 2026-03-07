import json
from unittest import TestCase
from utils.response import ResponseUtils
from datetime import date, datetime

class TestResponseUtils(TestCase):
    def test_default_serializer_with_date(self):
        test_date = date(2024, 6, 1)
        result = ResponseUtils.default_serializer(test_date)
        self.assertEqual(result, "2024-06-01")

    def test_default_serializer_with_datetime(self):
        test_datetime = datetime(2024, 6, 1, 12, 30, 45)
        result = ResponseUtils.default_serializer(test_datetime)
        self.assertEqual(result, "2024-06-01T12:30:45")

    def test_default_serializer_with_unsupported_type(self):
        with self.assertRaises(TypeError):
            ResponseUtils.default_serializer(set([1, 2, 3]))

    def test_http_response_structure(self):
        payload = {"message": "Hello, World!"}
        response = ResponseUtils.http_response(200, payload)

        self.assertIn("statusCode", response)
        self.assertIn("body", response)
        self.assertIn("headers", response)

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["headers"]["Content-Type"], "application/json")
        self.assertEqual(response["headers"]["Access-Control-Allow-Origin"], "*")
        self.assertEqual(response["headers"]["Access-Control-Allow-Headers"], "Content-Type")
        self.assertEqual(response["headers"]["Access-Control-Allow-Methods"], "OPTIONS,POST,GET,PUT,DELETE")
        self.assertEqual(json.loads(response["body"]), payload)

    # Get method and path

    def test_get_method_and_path(self):
        event = {"httpMethod": "GET", "path": "/controls/VGCP-001"}
        method, path = ResponseUtils.get_method_and_path(event)

        self.assertEqual(method, "GET")
        self.assertEqual(path, "/controls/VGCP-001")

    def test_get_method_and_path_v2_fallback(self):
        event = {"requestContext": {"http": {"method": "PUT"}}, "rawPath": "/controls/VGCP-001"}
        method, path = ResponseUtils.get_method_and_path(event)

        self.assertEqual(method, "PUT")
        self.assertEqual(path, "/controls/VGCP-001")

    def test_get_method_and_path_empty_event(self):
        method, path = ResponseUtils.get_method_and_path({})

        self.assertEqual(method, "")
        self.assertEqual(path, "")

    def test_get_method_and_path_v1_priority_over_v2(self):
        event = {
            "httpMethod": "DELETE",
            "path": "/controls/VGCP-001",
            "requestContext": {"http": {"method": "GET"}},
            "rawPath": "/other",
        }
        method, path = ResponseUtils.get_method_and_path(event)

        self.assertEqual(method, "DELETE")
        self.assertEqual(path, "/controls/VGCP-001")

    # Extract ID

    def test_extract_id_from_path_params(self):
        event = {"pathParameters": {"vgcpid": "VGCP-001"}}
        result = ResponseUtils.extract_id(event, "/controls/VGCP-001", "controls")

        self.assertEqual(result, "VGCP-001")

    def test_extract_id_converts_to_string(self):
        event = {"pathParameters": {"vgcpid": 12345}}
        result = ResponseUtils.extract_id(event, "/controls/12345", "controls")

        self.assertEqual(result, "12345")

    def test_extract_id_ignores_none_path_param(self):
        event = {"pathParameters": {"vgcpid": None}}
        result = ResponseUtils.extract_id(event, "/controls/VGCP-001", "controls")

        self.assertEqual(result, "VGCP-001")

    def test_extract_id_from_url_path(self):
        event = {"pathParameters": {}}
        result = ResponseUtils.extract_id(event, "/controls/VGCP-002", "controls")

        self.assertEqual(result, "VGCP-002")

    def test_extract_id_strips_trailing_slash(self):
        event = {"pathParameters": {}}
        result = ResponseUtils.extract_id(event, "/controls/VGCP-003/", "controls")

        self.assertEqual(result, "VGCP-003")

    def test_extract_id_returns_none_for_base_path(self):
        event = {"pathParameters": {}}
        result = ResponseUtils.extract_id(event, "/controls", "controls")

        self.assertIsNone(result)

    def test_extract_id_returns_none_for_empty_path(self):
        event = {}
        result = ResponseUtils.extract_id(event, "", "controls")

        self.assertIsNone(result)

    def test_extract_id_returns_none_for_wrong_resource(self):
        event = {"pathParameters": {}}
        result = ResponseUtils.extract_id(event, "/requests/123", "controls")

        self.assertIsNone(result)

    def test_extract_id_from_generic_id_param(self):
        event = {"pathParameters": {"id": "99"}}
        result = ResponseUtils.extract_id(event, "/tests/99", "tests")

        self.assertEqual(result, "99")

    def test_extract_id_generic_id_converts_int_to_string(self):
        event = {"pathParameters": {"id": 42}}
        result = ResponseUtils.extract_id(event, "/tests/42", "tests")

        self.assertEqual(result, "42")

    def test_extract_id_none_path(self):
        event = {"pathParameters": {}}
        result = ResponseUtils.extract_id(event, None, "tests")

        self.assertIsNone(result)

    # get_query_params

    def test_get_query_params_returns_params(self):
        event = {"queryStringParameters": {"status": "active", "page": "2"}}
        result = ResponseUtils.get_query_params(event)

        self.assertEqual(result, {"status": "active", "page": "2"})

    def test_get_query_params_returns_empty_dict_when_none(self):
        event = {"queryStringParameters": None}
        result = ResponseUtils.get_query_params(event)

        self.assertEqual(result, {})

    def test_get_query_params_returns_empty_dict_when_missing(self):
        result = ResponseUtils.get_query_params({})

        self.assertEqual(result, {})

    # get_json_body

    def test_get_json_body_with_string_body(self):
        event = {"body": json.dumps({"key": "value"})}
        result = ResponseUtils.get_json_body(event)

        self.assertEqual(result, {"key": "value"})

    def test_get_json_body_with_dict_body(self):
        event = {"body": {"key": "value"}}
        result = ResponseUtils.get_json_body(event)

        self.assertEqual(result, {"key": "value"})

    def test_get_json_body_with_empty_body(self):
        result = ResponseUtils.get_json_body({"body": ""})

        self.assertEqual(result, {})

    def test_get_json_body_with_none_body(self):
        result = ResponseUtils.get_json_body({"body": None})

        self.assertEqual(result, {})

    def test_get_json_body_with_no_body_key(self):
        result = ResponseUtils.get_json_body({})

        self.assertEqual(result, {})

    def test_get_json_body_with_none_event(self):
        result = ResponseUtils.get_json_body(None)

        self.assertEqual(result, {})

    def test_get_json_body_with_invalid_json(self):
        result = ResponseUtils.get_json_body({"body": "not-json"})

        self.assertEqual(result, {})

    # get_actor_user_id

    def test_get_actor_user_id_from_authorizer_user_id(self):
        event = {"requestContext": {"authorizer": {"user_id": "7"}}, "headers": {}, "queryStringParameters": {}}
        result = ResponseUtils.get_actor_user_id(event)

        self.assertEqual(result, 7)

    def test_get_actor_user_id_from_authorizer_principal_id(self):
        event = {"requestContext": {"authorizer": {"principalId": "12"}}, "headers": {}, "queryStringParameters": {}}
        result = ResponseUtils.get_actor_user_id(event)

        self.assertEqual(result, 12)

    def test_get_actor_user_id_from_claims_sub(self):
        event = {"requestContext": {"authorizer": {"claims": {"sub": "5"}}}, "headers": {}, "queryStringParameters": {}}
        result = ResponseUtils.get_actor_user_id(event)

        self.assertEqual(result, 5)

    def test_get_actor_user_id_from_claims_custom(self):
        event = {"requestContext": {"authorizer": {"claims": {"custom:user_id": "8"}}}, "headers": {}, "queryStringParameters": {}}
        result = ResponseUtils.get_actor_user_id(event)

        self.assertEqual(result, 8)

    def test_get_actor_user_id_from_header_lowercase(self):
        event = {"requestContext": {}, "headers": {"x-user-id": "3"}, "queryStringParameters": {}}
        result = ResponseUtils.get_actor_user_id(event)

        self.assertEqual(result, 3)

    def test_get_actor_user_id_from_header_mixed_case(self):
        event = {"requestContext": {}, "headers": {"X-User-Id": "4"}, "queryStringParameters": {}}
        result = ResponseUtils.get_actor_user_id(event)

        self.assertEqual(result, 4)

    def test_get_actor_user_id_from_query_param(self):
        event = {"requestContext": {}, "headers": {}, "queryStringParameters": {"actor_user_id": "15"}}
        result = ResponseUtils.get_actor_user_id(event)

        self.assertEqual(result, 15)

    def test_get_actor_user_id_from_body_actor(self):
        result = ResponseUtils.get_actor_user_id(
            {"requestContext": {}, "headers": {}, "queryStringParameters": {}},
            body={"actor_user_id": "20"}
        )

        self.assertEqual(result, 20)

    def test_get_actor_user_id_from_body_created_by(self):
        result = ResponseUtils.get_actor_user_id(
            {"requestContext": {}, "headers": {}, "queryStringParameters": {}},
            body={"created_by": "25"}
        )

        self.assertEqual(result, 25)

    def test_get_actor_user_id_returns_none_when_not_found(self):
        event = {"requestContext": {}, "headers": {}, "queryStringParameters": {}}
        result = ResponseUtils.get_actor_user_id(event)

        self.assertIsNone(result)

    def test_get_actor_user_id_skips_empty_string(self):
        event = {"requestContext": {"authorizer": {"user_id": ""}}, "headers": {"x-user-id": "9"}, "queryStringParameters": {}}
        result = ResponseUtils.get_actor_user_id(event)

        self.assertEqual(result, 9)

    def test_get_actor_user_id_skips_non_numeric(self):
        event = {"requestContext": {"authorizer": {"user_id": "not-a-number"}}, "headers": {"x-user-id": "11"}, "queryStringParameters": {}}
        result = ResponseUtils.get_actor_user_id(event)

        self.assertEqual(result, 11)

    def test_get_actor_user_id_with_none_headers_and_params(self):
        event = {"requestContext": {}, "headers": None, "queryStringParameters": None}
        result = ResponseUtils.get_actor_user_id(event, body={"created_by": "30"})

        self.assertEqual(result, 30)

    def test_get_actor_user_id_with_none_claims(self):
        event = {"requestContext": {"authorizer": {"claims": None}}, "headers": {"x-user-id": "6"}, "queryStringParameters": {}}
        result = ResponseUtils.get_actor_user_id(event)

        self.assertEqual(result, 6)
