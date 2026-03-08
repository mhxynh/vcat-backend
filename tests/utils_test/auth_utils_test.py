import json
from unittest import TestCase
from utils.auth_utils import AuthUtils, require_manager, require_tester


class TestAuthUtils(TestCase):
    def _build_event(self, groups=""):
        return {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": groups
                    }
                }
            }
        }

    # get_user_claims
    
    def test_get_user_claims_returns_claims(self):
        event = self._build_event("Manager")
        claims = AuthUtils.get_user_claims(event)
        self.assertEqual(claims["cognito:groups"], "Manager")

    def test_get_user_claims_empty_event(self):
        claims = AuthUtils.get_user_claims({})
        self.assertEqual(claims, {})

    # get_user_groups

    def test_get_user_groups_single(self):
        event = self._build_event("Manager")
        self.assertEqual(AuthUtils.get_user_groups(event), ["Manager"])

    def test_get_user_groups_multiple(self):
        event = self._build_event("Manager,Tester")
        self.assertEqual(AuthUtils.get_user_groups(event), ["Manager", "Tester"])

    def test_get_user_groups_empty(self):
        event = self._build_event("")
        self.assertEqual(AuthUtils.get_user_groups(event), [])

    def test_get_user_groups_list_input(self):
        event = {"requestContext": {"authorizer": {"claims": {"cognito:groups": ["Admin"]}}}}
        self.assertEqual(AuthUtils.get_user_groups(event), ["Admin"])

    # is_manager / is_tester

    def test_is_manager_true(self):
        self.assertTrue(AuthUtils.is_manager(self._build_event("Manager")))

    def test_is_manager_false(self):
        self.assertFalse(AuthUtils.is_manager(self._build_event("Tester")))

    def test_is_tester_true(self):
        self.assertTrue(AuthUtils.is_tester(self._build_event("Tester")))

    def test_is_tester_false(self):
        self.assertFalse(AuthUtils.is_tester(self._build_event("Manager")))

    # require_manager decorator

    def test_require_manager_allows_manager(self):
        @require_manager
        def handler(event, context):
            return {"statusCode": 200}

        result = handler(self._build_event("Manager"), None)
        self.assertEqual(result["statusCode"], 200)

    def test_require_manager_blocks_non_manager(self):
        @require_manager
        def handler(event, context):
            return {"statusCode": 200}

        result = handler(self._build_event("Tester"), None)
        self.assertEqual(result["statusCode"], 403)
        self.assertIn("Manager access required", json.loads(result["body"])["error"])

    # require_tester decorator

    def test_require_tester_allows_tester(self):
        @require_tester
        def handler(event, context):
            return {"statusCode": 200}

        result = handler(self._build_event("Tester"), None)
        self.assertEqual(result["statusCode"], 200)

    def test_require_tester_blocks_non_tester(self):
        @require_tester
        def handler(event, context):
            return {"statusCode": 200}

        result = handler(self._build_event("Manager"), None)
        self.assertEqual(result["statusCode"], 403)
        self.assertIn("Tester access required", json.loads(result["body"])["error"])
