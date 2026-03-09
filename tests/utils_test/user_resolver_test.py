from unittest import TestCase
from unittest.mock import patch, MagicMock
from utils.user_resolver import UserResolver


class TestUserResolver(TestCase):
    def _build_event(self, sub="test-sub-123", email="alice@example.com", groups=""):
        return {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": sub,
                        "email": email,
                        "cognito:groups": groups,
                        "name": "Alice Test",
                    }
                }
            }
        }

    def _mock_connection(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        return mock_conn, mock_cursor

    # resolve — no claims

    @patch('utils.user_resolver.DbUtils')
    def test_resolve_returns_none_when_no_claims(self, mock_db):
        event = {"requestContext": {"authorizer": {"claims": {}}}}
        result = UserResolver.resolve(event)
        self.assertIsNone(result)
        mock_db.get_db_connection.assert_not_called()

    # resolve — found by cognito_sub

    @patch('utils.user_resolver.DbUtils')
    def test_resolve_finds_user_by_cognito_sub(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection()
        mock_db.get_db_connection.return_value = mock_conn
        mock_cursor.fetchone.return_value = {"user_id": 42}

        result = UserResolver.resolve(self._build_event())

        self.assertEqual(result, 42)
        mock_cursor.execute.assert_called_once_with(
            "SELECT user_id FROM users WHERE cognito_sub = %s",
            ("test-sub-123",),
        )
        mock_conn.close.assert_called_once()

    # resolve — not found by sub, found by email, links sub

    @patch('utils.user_resolver.DbUtils')
    def test_resolve_finds_by_email_and_links_sub(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection()
        mock_db.get_db_connection.return_value = mock_conn
        # First call (cognito_sub lookup) returns None, second (email lookup) returns user
        mock_cursor.fetchone.side_effect = [
            None,
            {"user_id": 7, "cognito_sub": None},
        ]

        result = UserResolver.resolve(self._build_event())

        self.assertEqual(result, 7)
        # Should have issued UPDATE to link cognito_sub
        calls = mock_cursor.execute.call_args_list
        self.assertEqual(len(calls), 3)
        self.assertIn("UPDATE users SET cognito_sub", calls[2][0][0])
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    # resolve — found by email, sub already linked (no update)

    @patch('utils.user_resolver.DbUtils')
    def test_resolve_finds_by_email_sub_already_linked(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection()
        mock_db.get_db_connection.return_value = mock_conn
        mock_cursor.fetchone.side_effect = [
            None,
            {"user_id": 7, "cognito_sub": "existing-sub"},
        ]

        result = UserResolver.resolve(self._build_event())

        self.assertEqual(result, 7)
        # Should NOT have issued UPDATE
        calls = mock_cursor.execute.call_args_list
        self.assertEqual(len(calls), 2)  # only the two SELECTs
        mock_conn.commit.assert_not_called()
        mock_conn.close.assert_called_once()

    # resolve — auto-provision new user

    @patch('utils.user_resolver.Logger')
    @patch('utils.user_resolver.DbUtils')
    def test_resolve_auto_provisions_new_user(self, mock_db, mock_logger):
        mock_conn, mock_cursor = self._mock_connection()
        mock_db.get_db_connection.return_value = mock_conn
        mock_cursor.fetchone.side_effect = [
            None,  # cognito_sub lookup
            None,  # email lookup
            {"user_id": 99},  # INSERT RETURNING
        ]

        event = self._build_event(groups="Managers")
        result = UserResolver.resolve(event)

        self.assertEqual(result, 99)
        insert_call = mock_cursor.execute.call_args_list[2]
        self.assertIn("INSERT INTO users", insert_call[0][0])
        self.assertEqual(insert_call[0][1], ("test-sub-123", "alice@example.com", "MANAGER", "Alice Test"))
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('utils.user_resolver.Logger')
    @patch('utils.user_resolver.DbUtils')
    def test_resolve_auto_provisions_tester_by_default(self, mock_db, mock_logger):
        mock_conn, mock_cursor = self._mock_connection()
        mock_db.get_db_connection.return_value = mock_conn
        mock_cursor.fetchone.side_effect = [None, None, {"user_id": 100}]

        event = self._build_event(groups="Testers")
        result = UserResolver.resolve(event)

        self.assertEqual(result, 100)
        insert_call = mock_cursor.execute.call_args_list[2]
        self.assertEqual(insert_call[0][1][2], "TESTER")

    # resolve — sub only, no email, not found → None

    @patch('utils.user_resolver.DbUtils')
    def test_resolve_sub_only_not_found_returns_none(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection()
        mock_db.get_db_connection.return_value = mock_conn
        mock_cursor.fetchone.return_value = None

        event = self._build_event(email="")
        # email is empty string → falsy, so only cognito_sub path runs
        result = UserResolver.resolve(event)

        self.assertIsNone(result)
        mock_conn.close.assert_called_once()

    # resolve — DB error returns None

    @patch('utils.user_resolver.Logger')
    @patch('utils.user_resolver.DbUtils')
    def test_resolve_returns_none_on_db_error(self, mock_db, mock_logger):
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = Exception("connection failed")
        mock_db.get_db_connection.return_value = mock_conn

        result = UserResolver.resolve(self._build_event())

        self.assertIsNone(result)
        mock_conn.close.assert_called_once()

    # _resolve_role

    def test_resolve_role_manager(self):
        event = self._build_event(groups="Managers")
        self.assertEqual(UserResolver._resolve_role(event), "MANAGER")

    def test_resolve_role_tester(self):
        event = self._build_event(groups="Testers")
        self.assertEqual(UserResolver._resolve_role(event), "TESTER")

    def test_resolve_role_default_tester(self):
        event = self._build_event(groups="")
        self.assertEqual(UserResolver._resolve_role(event), "TESTER")

    # _resolve_display_name

    def test_display_name_from_name_claim(self):
        claims = {"name": "Alice Smith", "email": "alice@example.com"}
        self.assertEqual(UserResolver._resolve_display_name(claims, "alice@example.com"), "Alice Smith")

    def test_display_name_from_cognito_username(self):
        claims = {"cognito:username": "alice_s"}
        self.assertEqual(UserResolver._resolve_display_name(claims, "alice@example.com"), "alice_s")

    def test_display_name_from_preferred_username(self):
        claims = {"preferred_username": "alice_preferred"}
        self.assertEqual(UserResolver._resolve_display_name(claims, "alice@example.com"), "alice_preferred")

    def test_display_name_falls_back_to_email_prefix(self):
        claims = {}
        self.assertEqual(UserResolver._resolve_display_name(claims, "alice@example.com"), "alice")
