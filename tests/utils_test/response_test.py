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
