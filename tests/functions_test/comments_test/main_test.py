import json
from unittest import TestCase
from unittest.mock import patch
import functions.comments.main as comments


class TestCommentsMain(TestCase):
    def _build_event(self, method, path, body=None, query_params=None):
        event = {
            "httpMethod": method,
            "path": path,
            "pathParameters": {},
            "queryStringParameters": query_params or {},
        }
        if body is not None:
            event["body"] = json.dumps(body)
        return event

    # Empty event

    @patch("functions.comments.main.Logger")
    def test_empty_event_returns_400(self, mock_logger):
        result = comments.lambda_handler({}, None)

        mock_logger.log.assert_any_call(level="ERROR", message="No event data provided")
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("No event data", json.loads(result["body"])["error"])

    # GET /comments

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_get_all_comments_returns_200(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.return_value = "user-1"
        mock_crud.get_all.return_value = [
            {"comment_id": 1, "comment_text": "A"},
            {"comment_id": 2, "comment_text": "B"},
        ]

        event = self._build_event("GET", "/comments")
        result = comments.lambda_handler(event, None)

        mock_crud.get_all.assert_called_once_with(comments.TableNames.COMMENTS, order_by="posted_at")
        mock_logger.log.assert_any_call(level="INFO", message="Returning comments", extra_fields={"count": 2})
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(len(json.loads(result["body"])), 2)

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_get_comments_by_test_id_returns_200(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.return_value = "user-1"
        mock_crud.get_all.return_value = [
            {"comment_id": 1, "test_id": 10, "comment_text": "Match"},
            {"comment_id": 2, "test_id": 11, "comment_text": "No match"},
        ]

        event = self._build_event("GET", "/comments", query_params={"test_id": "10"})
        result = comments.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["test_id"], 10)

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_get_comments_by_request_id_returns_200(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.return_value = "user-1"
        mock_crud.get_all.return_value = [
            {"comment_id": 1, "request_id": 20, "comment_text": "Match"},
            {"comment_id": 2, "request_id": 21, "comment_text": "No match"},
        ]

        event = self._build_event("GET", "/comments", query_params={"request_id": "20"})
        result = comments.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["request_id"], 20)

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_get_comments_with_both_filters_returns_400(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.return_value = "user-1"

        event = self._build_event(
            "GET",
            "/comments",
            query_params={"test_id": "10", "request_id": "20"},
        )
        result = comments.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="ERROR", message="Both test_id and request_id provided")
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("Provide only one", json.loads(result["body"])["error"])

    # POST /comments

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_post_comment_for_test_returns_200(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.return_value = 1
        mock_crud.create.return_value = {
            "comment_id": 99,
            "author_user_id": 1,
            "test_id": 10,
            "request_id": None,
            "comment_text": "New comment",
        }

        body = {
            "test_id": 10,
            "comment_text": "New comment",
        }
        event = self._build_event("POST", "/comments", body=body)
        result = comments.lambda_handler(event, None)

        mock_crud.create.assert_called_once_with(
            comments.TableNames.COMMENTS,
            ["author_user_id", "test_id", "request_id", "comment_text"],
            [1, 10, None, "New comment"],
        )
        mock_logger.log.assert_any_call(level="INFO", message="Created comment", extra_fields={"comment_id": 99, "test_id": 10, "request_id": None})
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["comment_id"], 99)

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_post_comment_for_request_returns_200(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.return_value = 1
        mock_crud.create.return_value = {
            "comment_id": 100,
            "author_user_id": 1,
            "test_id": None,
            "request_id": 20,
            "comment_text": "Request comment",
        }

        body = {
            "request_id": 20,
            "comment_text": "Request comment",
        }
        event = self._build_event("POST", "/comments", body=body)
        result = comments.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["request_id"], 20)

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_post_comment_missing_fields_returns_400(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.return_value = "user-1"

        event = self._build_event("POST", "/comments", body={})
        result = comments.lambda_handler(event, None)

        mock_crud.create.assert_not_called()
        mock_logger.log.assert_any_call(
            level="ERROR",
            message="Missing fields in comment body",
            extra_fields={"missing": ["comment_text"]},
        )
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("Missing required fields", json.loads(result["body"])["error"])

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_post_comment_without_resolved_user_returns_401(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.return_value = None

        event = self._build_event(
            "POST",
            "/comments",
            body={"request_id": 20, "comment_text": "Request comment"},
        )
        result = comments.lambda_handler(event, None)

        mock_crud.create.assert_not_called()
        self.assertEqual(result["statusCode"], 401)
        self.assertIn("Unable to resolve authenticated user", json.loads(result["body"])["error"])

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_post_comment_with_both_targets_returns_400(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.return_value = "user-1"

        body = {
            "test_id": 10,
            "request_id": 20,
            "comment_text": "Invalid",
        }
        event = self._build_event("POST", "/comments", body=body)
        result = comments.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="ERROR", message="Invalid comment target", extra_fields={"test_id": 10, "request_id": 20})
        self.assertEqual(result["statusCode"], 400)

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_post_comment_with_no_target_returns_400(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.return_value = "user-1"

        body = {
            "comment_text": "Invalid",
        }
        event = self._build_event("POST", "/comments", body=body)
        result = comments.lambda_handler(event, None)

        mock_logger.log.assert_any_call(level="ERROR", message="Invalid comment target", extra_fields={"test_id": None, "request_id": None})
        self.assertEqual(result["statusCode"], 400)

    # DELETE /comments

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_delete_comments_by_test_id_returns_200(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.return_value = "5"
        mock_crud.hard_delete.return_value = {"deleted": 2}

        event = self._build_event(
            "DELETE",
            "/comments",
            query_params={
                "comment_id": "1",
                "test_id": "10",
            },
        )
        result = comments.lambda_handler(event, None)

        mock_crud.hard_delete.assert_called_once_with(
            comments.TableNames.COMMENTS,
            ["comment_id", "author_user_id", "test_id"],
            ["1", "5", "10"],
        )
        mock_logger.log.assert_any_call(
            level="INFO",
            message="Deleted comment",
            extra_fields={"comment_id": "1", "test_id": "10", "request_id": None},
        )
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["deleted"], 2)

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_delete_comments_by_request_id_returns_200(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.return_value = "5"
        mock_crud.hard_delete.return_value = {"deleted": 1}

        event = self._build_event(
            "DELETE",
            "/comments",
            query_params={
                "comment_id": "2",
                "request_id": "20",
            },
        )
        result = comments.lambda_handler(event, None)

        mock_crud.hard_delete.assert_called_once_with(
            comments.TableNames.COMMENTS,
            ["comment_id", "author_user_id", "request_id"],
            ["2", "5", "20"],
        )
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["deleted"], 1)

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_delete_comments_without_author_user_id_uses_authenticated_user(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.return_value = "5"
        mock_crud.hard_delete.return_value = {"deleted": 1}

        event = self._build_event(
            "DELETE",
            "/comments",
            query_params={
                "comment_id": "2",
                "request_id": "20",
            },
        )
        result = comments.lambda_handler(event, None)

        mock_crud.hard_delete.assert_called_once_with(
            comments.TableNames.COMMENTS,
            ["comment_id", "author_user_id", "request_id"],
            ["2", "5", "20"],
        )
        self.assertEqual(result["statusCode"], 200)

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_delete_comments_not_owned_without_author_user_id_returns_404(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.return_value = "5"
        mock_crud.hard_delete.return_value = None

        event = self._build_event(
            "DELETE",
            "/comments",
            query_params={
                "comment_id": "16",
                "request_id": "20",
            },
        )
        result = comments.lambda_handler(event, None)

        mock_crud.hard_delete.assert_called_once_with(
            comments.TableNames.COMMENTS,
            ["comment_id", "author_user_id", "request_id"],
            ["16", "5", "20"],
        )
        self.assertEqual(result["statusCode"], 404)
        self.assertIn(
            "not authorized",
            json.loads(result["body"])["error"],
        )

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_delete_comments_ignores_query_author_user_id(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.return_value = "5"
        mock_crud.hard_delete.return_value = {"deleted": 1}

        event = self._build_event(
            "DELETE",
            "/comments",
            query_params={
                "comment_id": "2",
                "author_user_id": "7",
                "request_id": "20",
            },
        )
        result = comments.lambda_handler(event, None)

        mock_crud.hard_delete.assert_called_once_with(
            comments.TableNames.COMMENTS,
            ["comment_id", "author_user_id", "request_id"],
            ["2", "5", "20"],
        )
        self.assertEqual(result["statusCode"], 200)

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_delete_comments_without_resolved_user_returns_401(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.return_value = None

        event = self._build_event(
            "DELETE",
            "/comments",
            query_params={
                "comment_id": "2",
                "request_id": "20",
            },
        )
        result = comments.lambda_handler(event, None)

        mock_crud.hard_delete.assert_not_called()
        self.assertEqual(result["statusCode"], 401)
        self.assertIn("Unable to resolve authenticated user", json.loads(result["body"])["error"])

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_delete_comments_with_both_targets_returns_400(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.return_value = "user-1"

        event = self._build_event(
            "DELETE",
            "/comments",
            query_params={
                "comment_id": "1",
                "author_user_id": "5",
                "test_id": "10",
                "request_id": "20",
            },
        )
        result = comments.lambda_handler(event, None)

        mock_logger.log.assert_any_call(
            level="ERROR",
            message="Invalid delete target",
            extra_fields={
                "comment_id": "1",
                "test_id": "10",
                "request_id": "20",
            },
        )
        self.assertEqual(result["statusCode"], 400)

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_delete_comments_with_no_target_returns_400(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.return_value = "5"

        event = self._build_event(
            "DELETE",
            "/comments",
            query_params={
                "comment_id": "1",
            },
        )
        result = comments.lambda_handler(event, None)

        mock_logger.log.assert_any_call(
            level="ERROR",
            message="Invalid delete target",
            extra_fields={
                "comment_id": "1",
                "test_id": None,
                "request_id": None,
            },
        )
        self.assertEqual(result["statusCode"], 400)

    # Method not allowed

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_unsupported_method_returns_405(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.return_value = "user-1"

        event = self._build_event("PATCH", "/comments")
        result = comments.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 405)

    # Exception handling

    @patch("functions.comments.main.Logger")
    @patch("functions.comments.main.CrudUtils")
    @patch("functions.comments.main.UserResolver")
    def test_exception_returns_500(self, mock_user_resolver, mock_crud, mock_logger):
        mock_user_resolver.resolve.side_effect = Exception("Unexpected error")

        event = self._build_event("GET", "/comments")
        result = comments.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 500)
        self.assertIn("Unexpected error", json.loads(result["body"])["error"])
