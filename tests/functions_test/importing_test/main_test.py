import json
import os
from datetime import date
from unittest import TestCase
from unittest.mock import MagicMock, patch

import functions.importing.main as importing
from functions.importing.main import ImportValidationError


class TestImportingMain(TestCase):
    def _build_http_event(self, method="POST", body=None):
        event = {
            "httpMethod": method,
            "path": "/import",
            "pathParameters": {},
            "queryStringParameters": {},
            "headers": {},
        }
        if body is not None:
            event["body"] = json.dumps(body)
        return event

    def _build_s3_event(self, bucket="imports-bucket", key="control-metadata/file.csv"):
        return {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": bucket},
                        "object": {"key": key},
                    },
                }
            ]
        }

    # POST /import

    @patch("functions.importing.main.S3Utils.generate_presigned_put_url")
    @patch("functions.importing.main.AuthUtils")
    def test_post_returns_presigned_upload_details(
        self, mock_auth, mock_generate_presigned_put_url
    ):
        mock_auth.is_manager.return_value = True
        mock_generate_presigned_put_url.return_value = "https://example.com/upload"

        with patch.dict(
            os.environ,
            {
                "UPLOAD_BUCKET_NAME": "imports-bucket",
                "UPLOAD_KEY_PREFIX": "control-metadata/",
                "PRESIGNED_URL_TTL_SECONDS": "600",
            },
            clear=True,
        ):
            result = importing.lambda_handler(
                self._build_http_event(body={"filename": "controls.csv"}), None
            )

        self.assertEqual(result["statusCode"], 200)
        payload = json.loads(result["body"])
        self.assertEqual(payload["bucket"], "imports-bucket")
        self.assertEqual(payload["method"], "PUT")
        self.assertEqual(payload["content_type"], "text/csv")
        self.assertEqual(payload["expires_in"], 600)
        self.assertTrue(payload["key"].startswith("control-metadata/"))
        mock_generate_presigned_put_url.assert_called_once()

    @patch("functions.importing.main.AuthUtils")
    def test_post_requires_manager(self, mock_auth):
        mock_auth.is_manager.return_value = False

        result = importing.lambda_handler(
            self._build_http_event(body={"filename": "controls.csv"}), None
        )

        self.assertEqual(result["statusCode"], 403)
        self.assertIn("Manager access required", json.loads(result["body"])["error"])

    def test_non_post_method_returns_405(self):
        result = importing.lambda_handler(self._build_http_event(method="GET"), None)

        self.assertEqual(result["statusCode"], 405)

    @patch("functions.importing.main.AuthUtils")
    def test_post_invalid_file_type_returns_400(self, mock_auth):
        mock_auth.is_manager.return_value = True

        with patch.dict(
            os.environ,
            {"UPLOAD_BUCKET_NAME": "imports-bucket"},
            clear=True,
        ):
            result = importing.lambda_handler(
                self._build_http_event(body={"filename": "controls.xlsx"}), None
            )

        self.assertEqual(result["statusCode"], 400)
        self.assertIn("Unsupported file type", json.loads(result["body"])["error"])

    @patch("functions.importing.main.AuthUtils")
    def test_post_missing_upload_bucket_returns_500(self, mock_auth):
        mock_auth.is_manager.return_value = True

        with patch.dict(os.environ, {}, clear=True):
            result = importing.lambda_handler(
                self._build_http_event(body={"filename": "controls.csv"}), None
            )

        self.assertEqual(result["statusCode"], 500)
        self.assertIn("UPLOAD_BUCKET_NAME", json.loads(result["body"])["error"])

    # S3 event processing

    @patch("functions.importing.main.bulk_upsert_controls")
    @patch("functions.importing.main.S3Utils.get_file_from_s3")
    def test_s3_event_processes_csv_and_upserts(self, mock_get_file, mock_upsert):
        csv_payload = (
            "vgcpid,description,control_owner,control_sme,escalation,is_active,date_created,last_tested\n"
            "VGCP-101,Control 101,Owner 1,SME 1,true,true,2026-04-01,2026-04-02\n"
            "VGCP-102,Control 102,Owner 2,,false,true,2026-04-03,\n"
        ).encode("utf-8")
        mock_get_file.return_value = (csv_payload, "text/csv")
        mock_upsert.return_value = (2, [])

        result = importing.lambda_handler(
            self._build_s3_event(key="control-metadata/controls.csv"), None
        )

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["processed_count"], 1)
        self.assertEqual(body["skipped_count"], 0)

        processed_file = body["processed_files"][0]
        self.assertEqual(processed_file["total_rows"], 2)
        self.assertEqual(processed_file["valid_rows"], 2)
        self.assertEqual(processed_file["invalid_rows"], 0)
        self.assertEqual(processed_file["inserted_rows"], 2)
        self.assertNotIn("upserted_rows", processed_file)

        inserted_rows = mock_upsert.call_args[0][0]
        self.assertEqual(inserted_rows[0][0], "VGCP-101")
        self.assertEqual(inserted_rows[0][4], True)
        self.assertEqual(inserted_rows[0][6], date(2026, 4, 1))

    @patch("functions.importing.main.bulk_upsert_controls")
    @patch("functions.importing.main.S3Utils.get_file_from_s3")
    def test_s3_event_processes_tracker_style_csv(self, mock_get_file, mock_upsert):
        csv_payload = (
            ",,Controls,,,,,,Testing Details\n"
            "Ref,VGCP ID,Procedure Name,Control Owner,Control SME,Escalation Needed? (Yes / No),Tester,Column1,DAT Status,Date Started,Date Completed\n"
            "1,VGCP-01054,Procedure A,Jason,,,Jason,notes,Completed,1/31/2025,2/7/2025\n"
            "2,VGCP-05245,Procedure B,,SME B,No,Alan/Clara,notes,Completed,1/22/2025,2/10/2025\n"
        ).encode("utf-8")
        mock_get_file.return_value = (csv_payload, "text/csv")
        mock_upsert.return_value = (2, [])

        result = importing.lambda_handler(
            self._build_s3_event(key="control-metadata/Controls Tracker - Example.csv"),
            None,
        )

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["processed_count"], 1)

        inserted_rows = mock_upsert.call_args[0][0]
        self.assertEqual(len(inserted_rows), 2)

        first_row = inserted_rows[0]
        self.assertEqual(first_row[0], "VGCP-01054")
        self.assertEqual(first_row[1], "Procedure A")
        self.assertEqual(first_row[2], "Jason")
        self.assertEqual(first_row[3], None)
        self.assertEqual(first_row[4], False)
        self.assertEqual(first_row[6], date(2025, 1, 31))
        self.assertEqual(first_row[7], date(2025, 2, 7))

        second_row = inserted_rows[1]
        self.assertEqual(second_row[0], "VGCP-05245")
        self.assertEqual(second_row[2], "Alan/Clara")
        self.assertEqual(second_row[3], "SME B")
        self.assertEqual(second_row[4], False)

    @patch("functions.importing.main.bulk_upsert_controls")
    @patch("functions.importing.main.S3Utils.get_file_from_s3")
    def test_s3_event_tracks_invalid_rows_and_keeps_valid_rows(
        self, mock_get_file, mock_upsert
    ):
        csv_payload = (
            "vgcpid,description,control_owner,escalation\n"
            "VGCP-201,,Owner 1,true\n"
            "VGCP-202,Control 202,Owner 2,false\n"
        ).encode("utf-8")
        mock_get_file.return_value = (csv_payload, "text/csv")
        mock_upsert.return_value = (1, [])

        result = importing.lambda_handler(
            self._build_s3_event(key="control-metadata/controls.csv"), None
        )

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        processed_file = body["processed_files"][0]
        self.assertEqual(processed_file["valid_rows"], 1)
        self.assertEqual(processed_file["invalid_rows"], 1)
        self.assertEqual(len(processed_file["invalid_row_samples"]), 1)

    @patch("functions.importing.main.bulk_upsert_controls")
    @patch("functions.importing.main.S3Utils.get_file_from_s3")
    def test_s3_event_deduplicates_duplicate_vgcpid_rows(
        self, mock_get_file, mock_upsert
    ):
        csv_payload = (
            "vgcpid,description,control_owner,escalation\n"
            "VGCP-101,Control 101,Owner 1,true\n"
            "VGCP-101,Control 101 Updated,Owner 2,false\n"
        ).encode("utf-8")
        mock_get_file.return_value = (csv_payload, "text/csv")
        mock_upsert.return_value = (1, [])

        result = importing.lambda_handler(
            self._build_s3_event(key="control-metadata/controls.csv"), None
        )

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        processed_file = body["processed_files"][0]
        self.assertEqual(processed_file["valid_rows"], 2)
        self.assertEqual(processed_file["deduped_valid_rows"], 1)
        self.assertEqual(processed_file["duplicate_vgcpid_count"], 1)

        inserted_rows = mock_upsert.call_args[0][0]
        self.assertEqual(len(inserted_rows), 1)
        self.assertEqual(inserted_rows[0][0], "VGCP-101")
        self.assertEqual(inserted_rows[0][1], "Control 101 Updated")
        self.assertEqual(inserted_rows[0][2], "Owner 2")

    @patch("functions.importing.main.bulk_upsert_controls")
    @patch("functions.importing.main.S3Utils.get_file_from_s3")
    def test_s3_event_skips_existing_database_vgcpids(self, mock_get_file, mock_upsert):
        csv_payload = (
            "vgcpid,description,control_owner,escalation\n"
            "VGCP-201,Control 201,Owner 1,true\n"
            "VGCP-202,Control 202,Owner 2,false\n"
        ).encode("utf-8")
        mock_get_file.return_value = (csv_payload, "text/csv")
        mock_upsert.return_value = (0, ["VGCP-201", "VGCP-202"])

        result = importing.lambda_handler(
            self._build_s3_event(key="control-metadata/controls.csv"), None
        )

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        processed_file = body["processed_files"][0]
        self.assertEqual(processed_file["valid_rows"], 2)
        self.assertEqual(processed_file["deduped_valid_rows"], 2)
        self.assertEqual(processed_file["existing_vgcpid_count"], 2)
        self.assertEqual(processed_file["inserted_rows"], 0)
        self.assertNotIn("upserted_rows", processed_file)

    @patch("functions.importing.main.bulk_upsert_controls")
    @patch("functions.importing.main.S3Utils.get_file_from_s3")
    def test_s3_event_skips_json_payload_as_invalid(self, mock_get_file, mock_upsert):
        json_payload = json.dumps(
            {
                "controls": [
                    {
                        "vgcpid": "VGCP-301",
                        "description": "Control 301",
                        "control_owner": "Owner 301",
                        "escalation": "yes",
                    }
                ]
            }
        ).encode("utf-8")
        mock_get_file.return_value = (json_payload, "application/json")
        mock_upsert.return_value = (1, [])

        result = importing.lambda_handler(
            self._build_s3_event(key="control-metadata/controls.json"), None
        )

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["processed_count"], 0)
        self.assertEqual(body["skipped_count"], 1)
        self.assertEqual(len(body["skipped_files"]), 1)
        self.assertIn("Unsupported file type", body["skipped_files"][0]["error"])
        mock_upsert.assert_not_called()

    # S3 event error handling

    @patch("functions.importing.main.process_import_file")
    def test_s3_event_skips_non_retryable_failures(self, mock_process_file):
        mock_process_file.side_effect = ImportValidationError("bad file")

        result = importing.lambda_handler(self._build_s3_event(), None)

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["processed_count"], 0)
        self.assertEqual(body["skipped_count"], 1)

    @patch("functions.importing.main.process_import_file")
    def test_s3_event_raises_for_retryable_failures(self, mock_process_file):
        mock_process_file.side_effect = Exception("database unavailable")

        with self.assertRaises(RuntimeError):
            importing.lambda_handler(self._build_s3_event(), None)

    # Helper function tests

    def _build_control_row(
        self,
        vgcpid,
        description="Control",
        owner="Owner",
        escalation=False,
        is_active=True,
        date_created=date(2026, 1, 1),
        last_tested=None,
    ):
        return (
            vgcpid,
            description,
            owner,
            None,
            escalation,
            is_active,
            date_created,
            last_tested,
        )
    
    # Get Environment

    def test_get_int_env_returns_default_value(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                importing.get_int_env("IMPORT_MAX_FILE_SIZE_MB", 20),
                20,
            )

    def test_get_int_env_var_exception(self):
        with patch.dict(
            os.environ,
            {"IMPORT_MAX_FILE_SIZE_MB": "not-an-int"},
            clear=True,
        ):
            self.assertEqual(
                importing.get_int_env("IMPORT_MAX_FILE_SIZE_MB", 20),
                20,
            )

    def test_get_int_env_returns_default_when_value_below_minimum(self):
        with patch.dict(
            os.environ,
            {"IMPORT_MAX_FILE_SIZE_MB": "0"},
            clear=True,
        ):
            self.assertEqual(
                importing.get_int_env("IMPORT_MAX_FILE_SIZE_MB", 20, minimum=1),
                20,
            )
    
    # File format resolution

    def test_resolve_file_format_uses_extension_or_content_type(self):
        self.assertEqual(importing.resolve_file_format("controls.csv"), "csv")
        self.assertEqual(
            importing.resolve_file_format("controls", "TEXT/CSV; charset=utf-8"),
            "csv",
        )

    def test_resolve_file_format_rejects_unsupported_type(self):
        with self.assertRaises(ImportValidationError):
            importing.resolve_file_format("controls.xlsx", "application/octet-stream")

    # Upload key generation

    def test_build_upload_key_contains_prefix_timestamp_uuid_and_filename(self):
        with patch.dict(
            os.environ,
            {
                "UPLOAD_KEY_PREFIX": "control-metadata/",
            },
            clear=True,
        ):
            key = importing.build_upload_key("Controls Tracker.csv", "csv")

        self.assertTrue(key.startswith("control-metadata/"))
        self.assertTrue(key.endswith("-Controls_Tracker.csv"))
        self.assertRegex(
            key,
            r"^control-metadata/\d{8}T\d{6}Z-[0-9a-f]{32}-Controls_Tracker\.csv$",
        )

    def test_build_upload_key_missing_safe_filename(self):
        with patch.dict(
            os.environ,
            {
                "UPLOAD_KEY_PREFIX": "control-metadata/",
            },
            clear=True,
        ):
            key = importing.build_upload_key("..\\..\\secret.txt", "txt")

        self.assertTrue(key.startswith("control-metadata/"))
        self.assertTrue(key.endswith("-secret.txt"))
        self.assertNotIn("..", key)

    def test_build_upload_key_uses_fallback_filename_without_prefix(self):
        with patch.dict(
            os.environ,
            {
                "UPLOAD_KEY_PREFIX": "",
            },
            clear=True,
        ):
            key = importing.build_upload_key("   ", "csv")

        self.assertRegex(
            key,
            r"^\d{8}T\d{6}Z-[0-9a-f]{32}-controls-metadata\.csv$",
        )

    # Boolean parsing

    def test_parse_boolean_accepts_true_and_false_strings(self):
        self.assertTrue(importing.parse_boolean("true", False, "escalation"))
        self.assertFalse(importing.parse_boolean("false", True, "escalation"))

    def test_parse_boolean_accepts_int_values(self):
        self.assertTrue(importing.parse_boolean(1, False, "escalation"))
        self.assertFalse(importing.parse_boolean(0, True, "escalation"))

    def test_parse_boolean_accepts_bool_values(self):
        self.assertTrue(importing.parse_boolean(True, False, "escalation"))
        self.assertFalse(importing.parse_boolean(False, True, "escalation"))

    def test_parse_boolean_accepts_case_insensitive_values(self):
        self.assertTrue(importing.parse_boolean("TRUE", False, "escalation"))
        self.assertFalse(importing.parse_boolean("No", True, "escalation"))
        self.assertTrue(importing.parse_boolean("  y  ", False, "escalation"))

    def test_parse_boolean_rejects_unknown_values(self):
        with self.assertRaises(ImportValidationError):
            importing.parse_boolean("maybe", False, "escalation")

    # Date parsing

    def test_parse_optional_date_supports_multiple_formats(self):
        self.assertEqual(
            importing.parse_optional_date("2026-04-10", "last_tested"),
            date(2026, 4, 10),
        )
        self.assertEqual(
            importing.parse_optional_date("4/10/2026", "last_tested"),
            date(2026, 4, 10),
        )
        self.assertEqual(
            importing.parse_optional_date("10-Apr-2026", "last_tested"),
            date(2026, 4, 10),
        )

    def test_parse_optional_date_accepts_date_instance(self):
        value = date(2026, 4, 10)
        self.assertEqual(importing.parse_optional_date(value, "last_tested"), value)

    def test_parse_optional_date_handles_iso_datetime_value(self):
        self.assertEqual(
            importing.parse_optional_date("2026-04-10T14:30:00Z", "last_tested"),
            date(2026, 4, 10),
        )

    def test_parse_optional_date_day_month_uses_current_year(self):
        parsed = importing.parse_optional_date("10-Apr", "last_tested")
        self.assertEqual(parsed.month, 4)
        self.assertEqual(parsed.day, 10)

    @patch("functions.importing.main.Logger.log")
    def test_parse_optional_date_returns_none_for_unparseable_values(self, mock_log):
        self.assertIsNone(importing.parse_optional_date("not-a-date", "last_tested"))
        mock_log.assert_called_once()

    # CSV and row normalization helpers

    def test_normalize_row_keys_maps_aliases(self):
        normalized = importing.normalize_row_keys(
            {
                "VGCP ID": "VGCP-01054",
                "Procedure Name": "Procedure A",
                "Control Owner": "Jason",
                "Escalation Needed? (Yes / No)": "Yes",
            }
        )

        self.assertEqual(normalized["vgcpid"], "VGCP-01054")
        self.assertEqual(normalized["description"], "Procedure A")
        self.assertEqual(normalized["control_owner"], "Jason")
        self.assertEqual(normalized["escalation"], "Yes")

    def test_normalize_row_keys_ignores_none_keys(self):
        normalized = importing.normalize_row_keys(
            {
                None: "ignore-me",
                "VGCP ID": "VGCP-01054",
            }
        )

        self.assertEqual(normalized["vgcpid"], "VGCP-01054")
        self.assertEqual(len(normalized), 1)

    def test_find_header_row_index_detects_tracker_header(self):
        rows = [
            ["", "", "Controls"],
            ["Ref", "VGCP ID", "Procedure Name", "Control Owner"],
        ]
        self.assertEqual(importing.find_header_row_index(rows), 1)

    def test_parse_csv_rows_extracts_rows_after_detected_header(self):
        csv_payload = (
            ",,Controls\n"
            "Ref,VGCP ID,Procedure Name,Control Owner\n"
            "1,VGCP-01054,Procedure A,Jason\n"
        ).encode("utf-8")

        rows = importing.parse_csv_rows(csv_payload)
        self.assertEqual(len(rows), 1)
        row_number, row = rows[0]
        self.assertEqual(row_number, 3)
        self.assertEqual(row["VGCP ID"], "VGCP-01054")
        self.assertEqual(row["Procedure Name"], "Procedure A")

    def test_parse_csv_rows_unicode_decoding_error(self):
        invalid_csv_payload = b"\xff\xfe\x00\x00"  # Invalid UTF-8 bytes
        with self.assertRaises(ImportValidationError):
            importing.parse_csv_rows(invalid_csv_payload)

    def test_parse_csv_rows_missing_csv_rows(self):
        csv_payload = "This is not a valid CSV file".encode("utf-8")
        with self.assertRaises(ImportValidationError):
            importing.parse_csv_rows(csv_payload)

    def test_parse_csv_rows_missing_header(self):
        csv_payload = (
            "This is not a valid CSV file without headers".encode("utf-8")
        )
        with self.assertRaises(ImportValidationError):
            importing.parse_csv_rows(csv_payload)

    def test_parse_csv_rows_empty_file_raises_validation_error(self):
        with self.assertRaises(ImportValidationError):
            importing.parse_csv_rows(b"")

    def test_parse_csv_rows_ignores_blank_header_cells(self):
        csv_payload = (
            ",VGCP ID,Procedure Name,Control Owner\n"
            ",VGCP-01054,Procedure A,Jason\n"
        ).encode("utf-8")

        rows = importing.parse_csv_rows(csv_payload)
        self.assertEqual(len(rows), 1)
        _, row = rows[0]
        self.assertNotIn("", row)

    def test_parse_csv_rows_skips_empty_data_rows(self):
        csv_payload = (
            "VGCP ID,Procedure Name,Control Owner\n"
            ",,\n"
            "VGCP-01054,Procedure A,Jason\n"
        ).encode("utf-8")

        rows = importing.parse_csv_rows(csv_payload)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], 3)

    def test_parse_metadata_rows_rejects_unsupported_format(self):
        with self.assertRaises(ImportValidationError):
            importing.parse_metadata_rows(b"{}", "json")

    def test_validate_and_transform_rows_separates_valid_and_invalid(self):
        rows = [
            (
                2,
                {
                    "vgcpid": "VGCP-101",
                    "description": "Control 101",
                    "control_owner": "Owner 1",
                    "escalation": "true",
                },
            ),
            (
                3,
                {
                    "vgcpid": "VGCP-102",
                    "description": "",
                    "control_owner": "Owner 2",
                },
            ),
        ]

        valid_rows, invalid_rows = importing.validate_and_transform_rows(rows)
        self.assertEqual(len(valid_rows), 1)
        self.assertEqual(valid_rows[0][0], "VGCP-101")
        self.assertEqual(len(invalid_rows), 1)
        self.assertEqual(invalid_rows[0]["row"], 3)

    # Duplicate VGCP handling

    def test_dedupe_control_rows_by_vgcpid_keeps_latest_row(self):
        control_rows = [
            self._build_control_row("VGCP-101", description="Old", owner="Owner 1"),
            self._build_control_row("VGCP-102", description="Middle", owner="Owner 2"),
            self._build_control_row("VGCP-101", description="New", owner="Owner 3"),
        ]

        deduped_rows, duplicate_vgcpids = importing.dedupe_control_rows_by_vgcpid(
            control_rows
        )

        self.assertEqual(duplicate_vgcpids, ["VGCP-101"])
        by_vgcpid = {row[0]: row for row in deduped_rows}
        self.assertEqual(by_vgcpid["VGCP-101"][1], "New")
        self.assertEqual(by_vgcpid["VGCP-101"][2], "Owner 3")
        self.assertEqual(len(deduped_rows), 2)

    @patch("functions.importing.main.execute_values")
    @patch("functions.importing.main.DbUtils.get_db_connection")
    def test_bulk_upsert_controls_inserts_only_new_ids(
        self, mock_get_db_connection, mock_execute_values
    ):
        connection = MagicMock()
        cursor = MagicMock()
        mock_get_db_connection.return_value = connection
        connection.cursor.return_value.__enter__.return_value = cursor

        cursor.fetchall.return_value = [{"vgcpid": "VGCP-102"}]

        inserted_rows, existing_vgcpids = importing.bulk_upsert_controls(
            [
                self._build_control_row("VGCP-101"),
                self._build_control_row("VGCP-102"),
            ]
        )

        self.assertEqual(inserted_rows, 1)
        self.assertEqual(existing_vgcpids, ["VGCP-101"])

        execute_values_rows = mock_execute_values.call_args[0][2]
        self.assertEqual(len(execute_values_rows), 2)
        self.assertEqual(execute_values_rows[0][0], "VGCP-101")
        self.assertEqual(execute_values_rows[1][0], "VGCP-102")

    # DB insert helper behavior

    @patch("functions.importing.main.execute_values")
    @patch("functions.importing.main.DbUtils.get_db_connection")
    def test_bulk_upsert_controls_skips_when_all_ids_exist(
        self, mock_get_db_connection, mock_execute_values
    ):
        connection = MagicMock()
        cursor = MagicMock()
        mock_get_db_connection.return_value = connection
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchall.return_value = []

        inserted_rows, existing_vgcpids = importing.bulk_upsert_controls(
            [self._build_control_row("VGCP-101")]
        )

        self.assertEqual(inserted_rows, 0)
        self.assertEqual(existing_vgcpids, ["VGCP-101"])
        mock_execute_values.assert_called_once()

    def test_get_vgcpid_from_db_row_supports_tuple_rows(self):
        self.assertEqual(importing.get_vgcpid_from_db_row(("VGCP-101",)), "VGCP-101")

    def test_bulk_upsert_controls_returns_zero_for_empty_input(self):
        self.assertEqual(importing.bulk_upsert_controls([]), (0, []))

    @patch("functions.importing.main.execute_values")
    @patch("functions.importing.main.DbUtils.get_db_connection")
    def test_bulk_upsert_controls_rolls_back_on_exception(
        self, mock_get_db_connection, mock_execute_values
    ):
        connection = MagicMock()
        cursor = MagicMock()
        mock_get_db_connection.return_value = connection
        connection.cursor.return_value.__enter__.return_value = cursor

        cursor.fetchall.return_value = []
        mock_execute_values.side_effect = Exception("insert failed")

        with self.assertRaises(Exception):
            importing.bulk_upsert_controls([self._build_control_row("VGCP-101")])

        connection.rollback.assert_called_once()

    # To Control Tuple conversion

    def test_to_control_tuple_exception(self):
        with self.assertRaises(ImportValidationError) as ctx:
            importing.to_control_tuple(
                {
                    "vgcpid": "VGCP-101",
                    "description": "Control 101",
                    "control_owner": "Owner 1",
                    "escalation": "notaboolean",
                },
                2,
            )

        self.assertIn("Row 2:", str(ctx.exception))

    def test_to_control_tuple_requires_vgcpid(self):
        with self.assertRaises(ImportValidationError) as ctx:
            importing.to_control_tuple(
                {
                    "description": "Control 101",
                    "control_owner": "Owner 1",
                },
                2,
            )

        self.assertIn("vgcpid is required", str(ctx.exception))

    def test_to_control_tuple_requires_control_owner(self):
        with self.assertRaises(ImportValidationError) as ctx:
            importing.to_control_tuple(
                {
                    "vgcpid": "VGCP-101",
                    "description": "Control 101",
                    "control_owner": "",
                    "tester": "",
                },
                2,
            )

        self.assertIn("control_owner is required", str(ctx.exception))

    # Process helper behavior

    @patch("functions.importing.main.S3Utils.get_file_from_s3")
    def test_process_import_file_wraps_s3_value_error(self, mock_get_file):
        mock_get_file.side_effect = ValueError("too large")

        with self.assertRaises(ImportValidationError) as ctx:
            importing.process_import_file("imports-bucket", "control-metadata/file.csv")

        self.assertIn("too large", str(ctx.exception))

    @patch("functions.importing.main.S3Utils.get_file_from_s3")
    def test_process_import_file_raises_when_no_valid_rows(self, mock_get_file):
        csv_payload = (
            "vgcpid,description,control_owner\n"
            "VGCP-101,,Owner 1\n"
        ).encode("utf-8")
        mock_get_file.return_value = (csv_payload, "text/csv")

        with self.assertRaises(ImportValidationError) as ctx:
            importing.process_import_file("imports-bucket", "control-metadata/file.csv")

        self.assertIn("No valid rows", str(ctx.exception))

    # process_s3_event helper behavior

    def test_process_s3_event_ignores_non_s3_records(self):
        event = {"Records": [{"eventSource": "aws:sns"}]}
        result = importing.process_s3_event(event)

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["processed_count"], 0)
        self.assertEqual(body["skipped_count"], 0)

    def test_process_s3_event_skips_missing_bucket_or_key(self):
        event = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {},
                        "object": {},
                    },
                }
            ]
        }
        result = importing.process_s3_event(event)

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["processed_count"], 0)
        self.assertEqual(body["skipped_count"], 1)
        self.assertIn("Missing S3 bucket", body["skipped_files"][0]["error"])

    # API edge behavior

    def test_lambda_handler_none_event_returns_400(self):
        result = importing.lambda_handler(None, None)
        self.assertEqual(result["statusCode"], 400)

    @patch("functions.importing.main.ResponseUtils.cors_preflight")
    def test_lambda_handler_options_returns_cors_preflight(self, mock_cors_preflight):
        mock_cors_preflight.return_value = {"statusCode": 200}

        result = importing.lambda_handler({"httpMethod": "OPTIONS"}, None)

        self.assertEqual(result["statusCode"], 200)
        mock_cors_preflight.assert_called_once()

    def test_lambda_handler_truthy_empty_event_returns_400(self):
        class TruthyEmptyDict(dict):
            def __bool__(self):
                return True

        result = importing.lambda_handler(TruthyEmptyDict(), None)

        self.assertEqual(result["statusCode"], 400)
