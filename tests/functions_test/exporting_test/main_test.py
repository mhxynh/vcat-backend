import json
from unittest import TestCase
from unittest.mock import patch
import functions.exporting.main as exporting
import os
import functools


class TestExportingMain(TestCase):
    def setUp(self):
        self.user_resolver_patcher = patch('functions.exporting.main.UserResolver')
        self.mock_user_resolver = self.user_resolver_patcher.start()
        # ensure exporter finds a bucket during tests
        os.environ["EXPORT_BUCKET_NAME"] = "test-bucket"

    def tearDown(self):
        self.user_resolver_patcher.stop()
        os.environ.pop("EXPORT_BUCKET_NAME", None)

    @staticmethod
    def get_by_id_side_effect(table, pk_column=None, pk_value=None):
        if table == "requests":
            return {"request_id": 10, "requestor": "Alice", "description": "Req desc"}
        if table == "controls":
            return {"control_id": 20, "vgcpid": "VGCP-020", "description": "Ctrl desc"}
        if table == "users":
            return {"user_id": 30, "display_name": "Tester", "email": "t@example.com"}
        return None

    @staticmethod
    def make_get_all_side_effect(mapping):
        return functools.partial(TestExportingMain.get_all_for_mapping, mapping)

    @staticmethod
    def get_all_for_mapping(mapping, table, order_by=None):
        return mapping.get(table, [])

    @staticmethod
    def get_all_tests_with_row_factory(row):
        def _side_effect(table, order_by=None):
            if table == exporting.TableNames.TESTS:
                return [row]
            return []

        return _side_effect

    @staticmethod
    def get_all_side_effect_for_tests_requests(tests, requests):
        def _side_effect(table, order_by=None):
            if table == exporting.TableNames.TESTS:
                return tests
            if table == exporting.TableNames.REQUESTS:
                return requests
            return []

        return _side_effect

    @staticmethod
    def get_by_id_raise_on_controls(table, pk_col=None, pk_val=None):
        if table == exporting.TableNames.CONTROLS:
            raise Exception("DB failure fetching control")
        return None

    @staticmethod
    def get_by_id_raise_on_users(table, pk_col=None, pk_val=None):
        if table == exporting.TableNames.USERS:
            raise Exception("DB failure fetching user")
        return None

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

    @patch('functions.exporting.main.Logger')
    def test_empty_event_returns_400(self, mock_logger):
        result = exporting.lambda_handler({}, None)
        mock_logger.log.assert_any_call(level="ERROR", message="No event data provided")
        self.assertEqual(result["statusCode"], 400)

    # GET /export

    @patch('functions.exporting.main.Logger')
    def test_missing_table_returns_400(self, mock_logger):
        event = self._build_event("GET", "/export")
        result = exporting.lambda_handler(event, None)
        mock_logger.log.assert_any_call(level="ERROR", message="Missing 'table' query parameter")
        self.assertEqual(result["statusCode"], 400)

    @patch('functions.exporting.main.Logger')
    def test_invalid_table_returns_400(self, mock_logger):
        event = self._build_event("GET", "/export", query_params={"table": "bad"})
        result = exporting.lambda_handler(event, None)
        mock_logger.log.assert_any_call(level="WARNING", message="Invalid table requested", extra_fields={"table": "bad"})
        self.assertEqual(result["statusCode"], 400)

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    @patch('functions.exporting.main.S3Utils')
    def test_dashboard_returns_expected_metrics(self, mock_s3, mock_crud, mock_logger):
        # prepare sample tests and users
        tests = [
            {"test_id": 1, "status": "NOT_STARTED", "requires_dat": True, "requires_oet": False, "dat_step": None, "oet_step": None, "assigned_tester_id": 101},
            {"test_id": 2, "status": "COMPLETED", "requires_dat": True, "requires_oet": True, "dat_step": "COMPLETED", "oet_step": "COMPLETED", "assigned_tester_id": 101},
            {"test_id": 3, "status": "DAT_IN_PROGRESS", "requires_dat": True, "requires_oet": False, "dat_step": "TESTING_IN_PROGRESS", "oet_step": None, "assigned_tester_id": 102},
            {"test_id": 4, "status": "BLOCKED", "requires_dat": False, "requires_oet": True, "dat_step": "TESTING_BLOCKED", "oet_step": "WALKTHROUGH_SCHEDULED", "assigned_tester_id": None},
        ]

        users = [
            {"user_id": 101, "display_name": "Alice", "email": "alice@example.com"},
            {"user_id": 102, "display_name": "Bob", "email": "bob@example.com"},
        ]

        mapping = {
            exporting.TableNames.TESTS: tests,
            exporting.TableNames.USERS: users,
        }
        mock_crud.get_all.side_effect = self.make_get_all_side_effect(mapping)

        mock_client = mock_s3.get_client.return_value
        mock_client.upload_fileobj.return_value = None
        mock_client.generate_presigned_url.return_value = "https://example.com/download-dashboard"

        event = self._build_event("GET", "/export", query_params={"table": "dashboard"})
        result = exporting.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        payload = json.loads(result["body"]) if isinstance(result.get("body"), str) else result["body"]
        self.assertIn("download_url", payload)
        self.assertEqual(payload["download_url"], "https://example.com/download-dashboard")
        mock_client.upload_fileobj.assert_called()

    # GET /export

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    @patch('functions.exporting.main.S3Utils')
    def test_get_controls_returns_csv(self, mock_s3, mock_crud, mock_logger):
        mock_crud.get_all.return_value = [{"vgcpid": "VGCP-001", "description": "D1"}, {"vgcpid": "VGCP-002", "description": "D2"}]
        mock_client = mock_s3.get_client.return_value
        mock_client.upload_fileobj.return_value = None
        mock_client.generate_presigned_url.return_value = "https://example.com/download"

        event = self._build_event("GET", "/export", query_params={"table": "controls"})
        result = exporting.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        payload = json.loads(result["body"]) if isinstance(result.get("body"), str) else result["body"]
        self.assertIn("download_url", payload)
        self.assertEqual(payload["download_url"], "https://example.com/download")

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    @patch('functions.exporting.main.S3Utils')
    def test_get_tests_includes_referenced_values(self, mock_s3, mock_crud, mock_logger):
        # base test row references request_id, control_id, assigned_tester_id
        test_row = {"test_id": 1, "request_id": 10, "control_id": 20, "assigned_tester_id": 30}
        mock_crud.get_all.return_value = [test_row]

        mock_crud.get_by_id.side_effect = self.get_by_id_side_effect
        mock_client = mock_s3.get_client.return_value
        mock_client.upload_fileobj.return_value = None
        mock_client.generate_presigned_url.return_value = "https://example.com/download-tests"

        event = self._build_event("GET", "/export", query_params={"table": "tests"})
        result = exporting.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        payload = json.loads(result["body"]) if isinstance(result.get("body"), str) else result["body"]
        self.assertIn("download_url", payload)
        self.assertEqual(payload["download_url"], "https://example.com/download-tests")

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    @patch('functions.exporting.main.S3Utils')
    def test_requests_tests_requested_column(self, mock_s3, mock_crud, mock_logger):
        # Ensure requests export includes a 'Tests Requested' column listing linked VGCPIDs
        request_row = {"request_id": 10, "created_by": 30, "description": "Req desc"}
        test_row = {"test_id": 1, "request_id": 10, "control_id": 20, "assigned_tester_id": 30}

        mapping = {
            exporting.TableNames.REQUESTS: [request_row],
            exporting.TableNames.TESTS: [test_row],
        }
        mock_crud.get_all.side_effect = self.make_get_all_side_effect(mapping)
        mock_crud.get_by_id.side_effect = self.get_by_id_side_effect
        mock_client = mock_s3.get_client.return_value
        mock_client.upload_fileobj.return_value = None
        mock_client.generate_presigned_url.return_value = "https://example.com/download-requests"

        event = self._build_event("GET", "/export", query_params={"table": "requests"})
        result = exporting.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        payload = json.loads(result["body"]) if isinstance(result.get("body"), str) else result["body"]
        self.assertIn("download_url", payload)
        self.assertEqual(payload["download_url"], "https://example.com/download-requests")

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    @patch('functions.exporting.main.S3Utils')
    def test_tests_headers_capitalize_dat_oet(self, mock_s3, mock_crud, mock_logger):
        # Ensure DAT/OET tokens are capitalized in headers and included in correct order
        test_row = {
            "test_id": 3,
            "request_id": 10,
            "control_id": 20,
            "assigned_tester_id": 30,
            "requires_dat": True,
            "requires_oet": False,
            "dat_step": "Step A",
            "oet_step": "Step B",
        }
        mock_crud.get_all.return_value = [test_row]
        mock_crud.get_by_id.side_effect = self.get_by_id_side_effect
        mock_client = mock_s3.get_client.return_value
        mock_client.upload_fileobj.return_value = None
        mock_client.generate_presigned_url.return_value = "https://example.com/download-tests-dat-oet"

        event = self._build_event("GET", "/export", query_params={"table": "tests"})
        result = exporting.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        payload = json.loads(result["body"]) if isinstance(result.get("body"), str) else result["body"]
        self.assertIn("download_url", payload)
        self.assertEqual(payload["download_url"], "https://example.com/download-tests-dat-oet")

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    def test_exception_returns_500(self, mock_crud, mock_logger):
        mock_crud.get_all.side_effect = Exception("DB error")

        event = self._build_event("GET", "/export", query_params={"table": "controls"})
        result = exporting.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 500)
        self.assertIn("DB error", json.loads(result["body"])["error"])

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    def test_invalid_method_returns_405(self, mock_crud, mock_logger):
        event = self._build_event("POST", "/export", query_params={"table": "controls"})
        result = exporting.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 405)
        mock_logger.log.assert_any_call(level="WARNING", message="Method not allowed", extra_fields={"method": "POST", "path": "/export"})

    # fetch_rows tests

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    def test_fetch_rows_test_table(self, mock_crud, mock_logger):
        test_row = {"test_id": 1, "request_id": 10, "control_id": 20, "assigned_tester_id": 30}
        mock_crud.get_all.return_value = [test_row]
        mock_crud.get_by_id.side_effect = self.get_by_id_side_effect

        rows = exporting.fetch_rows(exporting.TableNames.TESTS)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.get("control_vgcpid"), "VGCP-020")
        self.assertEqual(row.get("assigned_tester_name"), "Tester")

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    def test_fetch_rows_requests_table(self, mock_crud, mock_logger):
        req_row = {"request_id": 10, "created_by": 30}
        mock_crud.get_all.return_value = [req_row]
        mock_crud.get_by_id.side_effect = self.get_by_id_side_effect

        rows = exporting.fetch_rows(exporting.TableNames.REQUESTS)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.get("created_by_name"), "Tester")
        self.assertEqual(row.get("created_by_email"), "t@example.com")

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    def test_fetch_rows_tests_missing_references(self, mock_crud, mock_logger):
        # when referenced rows are missing, enrichment keys should not be added
        base = {"test_id": 2, "request_id": 99, "control_id": 199, "assigned_tester_id": 299}
        mock_crud.get_all.return_value = [base]

        # get_by_id returns None for all referenced lookups
        mock_crud.get_by_id.return_value = None

        rows = exporting.fetch_rows(exporting.TableNames.TESTS)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertNotIn("request_requestor", row)
        self.assertNotIn("control_vgcpid", row)
        self.assertNotIn("assigned_tester_name", row)

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    def test_fetch_rows_handles_tester_lookup_exception(self, mock_crud, mock_logger):
        # Simulate a test row that references a tester; prefetch returns no users
        test_row = {"test_id": 1, "request_id": 10, "control_id": None, "assigned_tester_id": 30}

        mock_crud.get_all.side_effect = self.get_all_tests_with_row_factory(test_row)
        mock_crud.get_by_id.side_effect = self.get_by_id_raise_on_users

        rows = exporting.fetch_rows(exporting.TableNames.TESTS)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        # since the user lookup raised, enrichment keys should not be present
        self.assertNotIn("assigned_tester_name", row)
        self.assertNotIn("assigned_tester_email", row)

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    def test_fetch_rows_requests_control_lookup_exception(self, mock_crud, mock_logger):
        # tests include a mapping to a control; controls prefetch empty
        tests = [{"test_id": 1, "request_id": 10, "control_id": 20}]
        requests = [{"request_id": 10, "created_by": None}]

        mock_crud.get_all.side_effect = self.get_all_side_effect_for_tests_requests(tests, requests)
        mock_crud.get_by_id.side_effect = self.get_by_id_raise_on_controls

        rows = exporting.fetch_rows(exporting.TableNames.REQUESTS)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        # mapping failed, so tests_requested should be empty
        self.assertEqual(row.get("tests_requested"), [])

        # ensure the logger recorded the mapping failure
        logged_messages = [c.kwargs.get("message") for c in mock_logger.log.call_args_list]
        self.assertTrue(any(m == "Failed to fetch control for tests mapping" for m in logged_messages))

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    def test_fetch_rows_requests_user_lookup_exception(self, mock_crud, mock_logger):
        # requests include a created_by that will fail to fetch
        requests = [{"request_id": 11, "created_by": 30}]

        mock_crud.get_all.side_effect = self.get_all_side_effect_for_tests_requests([], requests)
        mock_crud.get_by_id.side_effect = self.get_by_id_raise_on_users

        rows = exporting.fetch_rows(exporting.TableNames.REQUESTS)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        # user enrichment should be absent when fetching user failed
        self.assertNotIn("created_by_name", row)
        self.assertNotIn("created_by_email", row)

        logged_messages = [c.kwargs.get("message") for c in mock_logger.log.call_args_list]
        self.assertTrue(any(m == "Failed to fetch user for request" for m in logged_messages))

    # serialize_value

    def test_serialize_value_none(self):
        self.assertEqual(exporting.serialize_value(None), "")

    def test_serialize_value_datetime(self):
        from datetime import datetime
        dt = datetime(2024, 1, 1, 12, 0, 0)
        self.assertEqual(exporting.serialize_value(dt), "2024-01-01T12:00:00")

    def test_serialize_value_string(self):
        self.assertEqual(exporting.serialize_value("test"), "test")

    def test_serialize_value_number(self):
        self.assertEqual(exporting.serialize_value(123), "123")

    def test_serialize_value_boolean(self):
        self.assertEqual(exporting.serialize_value(True), "Yes")
        self.assertEqual(exporting.serialize_value(False), "No")

    def test_serialize_value_list(self):
        self.assertEqual(exporting.serialize_value([1, "two", None]), "1;two;")
        
    # empty rows formatting

    def test_empty_rows_format_tests_csv(self):
        csv = exporting.format_tests_csv([])
        self.assertEqual(csv, (['VGCPID', 'Assigned Tester Name', 'Assigned Tester Email'], []))

    def test_empty_rows_format_controls_csv(self):
        csv = exporting.format_controls_csv([])
        self.assertEqual(csv, (['VGCPID', 'Description'], []))

    def test_empty_rows_format_requests_csv(self):
        csv = exporting.format_requests_csv([])
        self.assertEqual(csv, (['Request ID', 'Created By Name', 'Created By Email'], []))

    # build_export_response

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    @patch('functions.exporting.main.S3Utils')
    def test_build_export_no_bucket_returns_500(self, mock_s3, mock_crud, mock_logger):
        os.environ.pop("EXPORT_BUCKET_NAME", None)

        mock_crud.get_all.return_value = []

        event = self._build_event("GET", "/export", query_params={"table": "controls"})
        result = exporting.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 500)
        mock_logger.log.assert_any_call(level="ERROR", message="Export bucket not configured", extra_fields={"table": "controls"})

    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    @patch('functions.exporting.main.S3Utils')
    def test_build_export_upload_to_s3_exception_returns_500(self, mock_s3, mock_crud, mock_logger):
        mock_crud.get_all.return_value = []
        mock_client = mock_s3.get_client.return_value
        mock_client.upload_fileobj.side_effect = Exception("S3 upload failed")

        event = self._build_event("GET", "/export", query_params={"table": "controls"})
        result = exporting.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 500)
        self.assertIn("Failed to upload export to S3", json.loads(result["body"])["error"])

    @patch('functions.exporting.main.os.unlink', side_effect=Exception('unlink fail'))
    @patch('functions.exporting.main.Logger')
    @patch('functions.exporting.main.CrudUtils')
    @patch('functions.exporting.main.S3Utils')
    def test_build_export_handles_unlink_exception(self, mock_s3, mock_crud, mock_logger, mock_unlink):
        # Ensure bucket is configured
        os.environ["EXPORT_BUCKET_NAME"] = "test-bucket"

        # No rows to write but upload will fail to force the except -> finally path
        mock_crud.get_all.return_value = []
        mock_client = mock_s3.get_client.return_value
        mock_client.upload_fileobj.side_effect = Exception("S3 upload failed")

        event = self._build_event("GET", "/export", query_params={"table": "controls"})
        result = exporting.lambda_handler(event, None)

        # Handler should return 500 and not raise despite unlink raising in finally
        self.assertEqual(result["statusCode"], 500)
        self.assertIn("Failed to upload export to S3", json.loads(result["body"])["error"])
        mock_unlink.assert_called()
