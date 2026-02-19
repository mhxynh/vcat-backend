import json
from unittest import TestCase
from functions.catalog.main import lambda_handler

class TestCatalogMain(TestCase):
    def test_lambda_handler_returns_200(self):
        result = lambda_handler({}, None)

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "Catalog API is working!")
