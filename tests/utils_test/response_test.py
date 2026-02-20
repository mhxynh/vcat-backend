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
        self.assertEqual(json.loads(response["body"]), payload)
