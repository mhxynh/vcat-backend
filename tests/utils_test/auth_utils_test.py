import base64
import json
from unittest import TestCase
from utils.auth_utils import AuthUtils, require_manager, require_tester


def _make_jwt(payload_dict):
    """Build a fake JWT (header.payload.signature) with the given payload."""
    header = base64.urlsafe_b64encode(b'{"alg":"RS256"}').rstrip(b'=').decode()
    payload = base64.urlsafe_b64encode(json.dumps(payload_dict).encode()).rstrip(b'=').decode()
    return f"{header}.{payload}.fakesig"


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

    # Get User Claims

    def test_get_user_claims_returns_claims(self):
        event = self._build_event("Manager")
        claims = AuthUtils.get_user_claims(event)
        self.assertEqual(claims["cognito:groups"], "Manager")

    def test_get_user_claims_empty_event(self):
        claims = AuthUtils.get_user_claims({})
        self.assertEqual(claims, {})

    # Get User Groups

    def test_get_user_groups_single(self):
        event = self._build_event("Manager")
        self.assertEqual(AuthUtils.get_user_groups(event), ["Manager"])

    def test_get_user_groups_multiple(self):
        event = self._build_event("Manager,Tester")
        self.assertEqual(AuthUtils.get_user_groups(event), ["Manager", "Tester"])

    def test_get_user_groups_space_separated(self):
        event = self._build_event("Managers Testers")
        self.assertEqual(AuthUtils.get_user_groups(event), ["Managers", "Testers"])

    def test_get_user_groups_empty(self):
        event = self._build_event([])
        self.assertEqual(AuthUtils.get_user_groups(event), [])

    def test_get_user_groups_list_input(self):
        event = {"requestContext": {"authorizer": {"claims": {"cognito:groups": ["Admin"]}}}}
        self.assertEqual(AuthUtils.get_user_groups(event), ["Admin"])

    # Checks for Manager and Tester groups

    def test_is_manager_true(self):
        self.assertTrue(AuthUtils.is_manager(self._build_event("Managers")))

    def test_is_manager_false(self):
        self.assertFalse(AuthUtils.is_manager(self._build_event("Testers")))

    def test_is_tester_true(self):
        self.assertTrue(AuthUtils.is_tester(self._build_event("Testers")))

    def test_is_tester_false(self):
        self.assertFalse(AuthUtils.is_tester(self._build_event("Managers")))

    # Require Manager decorator

    def test_require_manager_allows_manager(self):
        @require_manager
        def handler(event, context):
            return {"statusCode": 200}

        result = handler(self._build_event("Managers"), None)
        self.assertEqual(result["statusCode"], 200)

    def test_require_manager_blocks_non_manager(self):
        @require_manager
        def handler(event, context):
            return {"statusCode": 200}

        result = handler(self._build_event("Testers"), None)
        self.assertEqual(result["statusCode"], 403)
        self.assertIn("Manager access required", json.loads(result["body"])["error"])

    # Require Tester decorator

    def test_require_tester_allows_tester(self):
        @require_tester
        def handler(event, context):
            return {"statusCode": 200}

        result = handler(self._build_event("Testers"), None)
        self.assertEqual(result["statusCode"], 200)

    def test_require_tester_blocks_non_tester(self):
        @require_tester
        def handler(event, context):
            return {"statusCode": 200}

        result = handler(self._build_event("Managers"), None)
        self.assertEqual(result["statusCode"], 403)
        self.assertIn("Tester access required", json.loads(result["body"])["error"])

    # JWT header fallback (for sam local)

    def test_get_user_groups_jwt_fallback(self):
        token = _make_jwt({"cognito:groups": "Managers Testers"})
        event = {"headers": {"Authorization": f"Bearer {token}"}}
        self.assertEqual(AuthUtils.get_user_groups(event), ["Managers", "Testers"])

    def test_get_user_claims_jwt_fallback(self):
        token = _make_jwt({"cognito:groups": "Managers", "sub": "abc-123"})
        event = {"headers": {"Authorization": f"Bearer {token}"}}
        claims = AuthUtils.get_user_claims(event)
        self.assertEqual(claims["sub"], "abc-123")
        self.assertEqual(claims["cognito:groups"], "Managers")

    def test_jwt_fallback_no_auth_header(self):
        event = {"headers": {}}
        self.assertEqual(AuthUtils.get_user_groups(event), [])

    def test_jwt_fallback_invalid_token(self):
        event = {"headers": {"Authorization": "Bearer not-a-jwt"}}
        self.assertEqual(AuthUtils.get_user_groups(event), [])

    def test_jwt_fallback_lowercase_authorization(self):
        token = _make_jwt({"cognito:groups": "Managers"})
        event = {"headers": {"authorization": f"Bearer {token}"}}
        self.assertEqual(AuthUtils.get_user_groups(event), ["Managers"])

    def test_is_manager_via_jwt_fallback(self):
        token = _make_jwt({"cognito:groups": "Managers"})
        event = {"headers": {"Authorization": f"Bearer {token}"}}
        self.assertTrue(AuthUtils.is_manager(event))

    def test_require_manager_allows_via_jwt(self):
        @require_manager
        def handler(event, context):
            return {"statusCode": 200}

        token = _make_jwt({"cognito:groups": "Managers"})
        event = {"headers": {"Authorization": f"Bearer {token}"}}
        result = handler(event, None)
        self.assertEqual(result["statusCode"], 200)
