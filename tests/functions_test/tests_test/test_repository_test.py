import pytest
from unittest import TestCase
from unittest.mock import patch, MagicMock
from functions.tests.test_repository import TestRepository

class TestTestRepository(TestCase):
    def _mock_connection(self, rows, fetchone=False):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        if fetchone:
            mock_cursor.fetchone.return_value = rows
        else:
            mock_cursor.fetchall.return_value = rows
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        return mock_conn, mock_cursor

    # GET Methods

    @patch('functions.tests.test_repository.DbUtils')
    def test_get_all_tests_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection([{
            "test_id": 1, 
            "vgcpid": "VGCP-001", 
            "assigned_tester_name": "Bob Vance"
        }])
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.get_all_tests()

        args, _ = mock_cursor.execute.call_args
        self.assertIn("LEFT JOIN users u", args[0])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["assigned_tester_name"], "Bob Vance")

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_get_all_tests_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.get_all_tests()
        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.DbUtils')
    def test_get_tests_by_id_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "vgcpid": "VGCP-001", "assigned_tester_name": "Alice"}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.get_tests_by_id(42)

        args, kwargs = mock_cursor.execute.call_args
        self.assertIn("WHERE t.test_id = %s", args[0])
        self.assertEqual(args[1], (42,))
        self.assertEqual(result["test_id"], 42)
        self.assertEqual(result["assigned_tester_name"], "Alice")

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_get_tests_by_id_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.get_tests_by_id(42)
        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.DbUtils')
    def test_get_tests_by_request_id_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection([{"test_id": 1, "request_id": 100, "vgcpid": "VGCP-001", "assigned_tester_name": "Alice"}])
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.get_tests_by_request_id(100)

        args, kwargs = mock_cursor.execute.call_args
        self.assertEqual(args[1], (100,))
        self.assertEqual(len(result), 1)

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_get_tests_by_request_id_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.get_tests_by_request_id(100)
        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.DbUtils')
    def test_get_tests_by_request_with_details_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection([
            {"test_id": 1, "request_id": 100, "vgcpid": "VGCP-001", "assigned_tester_name": "Alice"}
        ])
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.get_tests_by_request_with_details(100)

        self.assertEqual(result[0]["assigned_tester_name"], "Alice")

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_get_tests_by_request_with_details_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.get_tests_by_request_with_details(100)
        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.DbUtils')
    def test_get_tests_by_control_id_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection([{"test_id": 1, "control_id": 20, "vgcpid": "VGCP-001", "assigned_tester_name": "Alice"}])
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.get_tests_by_control_id(20)

        args, kwargs = mock_cursor.execute.call_args
        self.assertEqual(args[1], (20,))
        self.assertEqual(len(result), 1)

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_get_tests_by_control_id_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.get_tests_by_control_id(20)
        mock_logger.log.assert_called_once()

    # Create & Mutate Methods

    @patch('functions.tests.test_repository.DbUtils')
    def test_create_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 1, "description": "Desc", "vgcpid": "VGCP-001", "assigned_tester_name": "Alice"}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.create(
            vgcpid="VGCP-001", request_id=1, description="Desc", 
            requires_dat=True, requires_oet=False, due_date="2026-03-01"
        )

        args, kwargs = mock_cursor.execute.call_args
        sql_query, sql_params = args[0], args[1]
        
        self.assertIn("(SELECT control_id FROM controls WHERE vgcpid = %s)", sql_query)
        self.assertEqual(sql_params[0], "VGCP-001")
        mock_conn.commit.assert_called_once()
        self.assertEqual(result["test_id"], 1)
        self.assertEqual(result["assigned_tester_name"], "Alice")   

    @patch('functions.tests.test_repository.DbUtils')
    def test_create_allows_null_request_id(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 1, "request_id": None}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.create(
            vgcpid="VGCP-001", request_id=None, description="Desc",
            requires_dat=True, requires_oet=False, due_date="2026-03-01"
        )

        args, kwargs = mock_cursor.execute.call_args
        sql_params = args[1]

        self.assertIsNone(sql_params[1])
        mock_conn.commit.assert_called_once()
        self.assertIsNone(result["request_id"])

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_create_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.create("VGCP", 1, "Desc", True, False, "2026")
        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.DbUtils')
    def test_update_details_success(self, mock_db):
        """Test a full update of all test details."""
        mock_row = {
            "test_id": 42, "control_id": 10, "request_id": 2, 
            "vgcpid": "VGCP-101010", "assigned_tester_id": 505
        }
        mock_conn, mock_cursor = self._mock_connection(mock_row, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.update_details(
            42, "VGCP-101010", 2, 505, False, True, "2026-04-01", "2026-03-25", "Updated Desc"
        )

        args, _ = mock_cursor.execute.call_args
        sql_query, sql_params = args[0], args[1]

        normalized_query = ' '.join(sql_query.split())

        self.assertIn("SET control_id = ( SELECT control_id FROM controls WHERE vgcpid = %s", normalized_query)
        self.assertIn("request_id = %s", normalized_query)
        self.assertIn("description = %s", normalized_query)
        
        self.assertEqual(sql_params[0], "VGCP-101010")
        self.assertEqual(sql_params[-1], 42) # test_id should be last for the WHERE clause
        
        mock_conn.commit.assert_called_once()
        self.assertEqual(result["test_id"], 42)

    @patch('functions.tests.test_repository.DbUtils')
    def test_update_details_not_found(self, mock_db):
        """Test returning None when details update fails to find the test_id."""
        mock_conn, mock_cursor = self._mock_connection(None, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.update_details(
            999, "VGCP-FAIL", 1, 1, True, True, "2026-01-01", "2026-01-01", "None"
        )

        self.assertIsNone(result)

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_update_details_error(self, mock_db, mock_logger):
        """Test that errors are logged and exceptions are raised during details update."""
        mock_db.get_db_connection.side_effect = Exception("DB connection failed")

        with self.assertRaises(Exception):
            TestRepository.update_details(42, "VGCP-1", 1, 1, True, True, "2026", "2026", "Err")

        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.DbUtils')
    def test_update_evidence_links_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(
            {"test_id": 42, "evidence_links": ["https://example.com/evidence"]},
            fetchone=True,
        )
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.update_evidence_links(
            42, ["https://example.com/evidence", "https://example.com/evidence"]
        )

        args, _ = mock_cursor.execute.call_args
        self.assertIn("SET evidence_links = %s", args[0])
        self.assertEqual(args[1], (["https://example.com/evidence"], 42))
        mock_conn.commit.assert_called_once()
        self.assertEqual(result["test_id"], 42)

    @patch('functions.tests.test_repository.DbUtils')
    def test_update_evidence_links_not_found(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(None, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.update_evidence_links(9999, ["https://example.com/evidence"])

        self.assertIsNone(result)

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_update_evidence_links_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.update_evidence_links(42, ["https://example.com/evidence"])
        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_update_evidence_links_invalid_payload_raises(self, mock_db, mock_logger):
        mock_conn, mock_cursor = self._mock_connection(None, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        with self.assertRaises(ValueError):
            TestRepository.update_evidence_links(42, "https://example.com/evidence")

    @patch('functions.tests.test_repository.DbUtils')
    def test_update_assigned_tester_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "assigned_tester_id": 500}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.update_assigned_tester(42, 500)

        args, _ = mock_cursor.execute.call_args
        self.assertIn("SET assigned_tester_id = %s", args[0])
        self.assertEqual(args[1], (500, 42))
        mock_conn.commit.assert_called_once()
        self.assertEqual(result["assigned_tester_id"], 500)

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_update_assigned_tester_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB error")
        with self.assertRaises(Exception):
            TestRepository.update_assigned_tester(42, 500)
        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.DbUtils')
    def test_update_dat_track_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(
            {"test_id": 42, "dat_step": "Phase 2", "status": "DAT_IN_PROGRESS"}, fetchone=True
        )
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.update_dat_track(42, "Phase 2", "DAT_IN_PROGRESS")

        args, _ = mock_cursor.execute.call_args
        self.assertIn("SET dat_step = %s, status = %s", args[0])
        self.assertEqual(args[1], ("Phase 2", "DAT_IN_PROGRESS", 42))
        mock_conn.commit.assert_called_once()

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_update_dat_track_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.update_dat_track(42, "Phase 2", "DAT_IN_PROGRESS")
        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.DbUtils')
    def test_update_oet_track_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(
            {"test_id": 42, "oet_step": "Step 1", "status": "OET_IN_PROGRESS", "assigned_tester_name": "Alice"}, fetchone=True
        )
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.update_oet_track(42, "Step 1", "OET_IN_PROGRESS")

        args, _ = mock_cursor.execute.call_args
        self.assertIn("SET oet_step = %s, status = %s", args[0]) 
        self.assertEqual(args[1], ("Step 1", "OET_IN_PROGRESS", 42))
        mock_conn.commit.assert_called_once()

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_update_oet_track_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.update_oet_track(42, "Step 1", "OET_IN_PROGRESS")
        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.DbUtils')
    def test_start_test_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "status": "DAT_IN_PROGRESS", "assigned_tester_name": "Alice"}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.start_test(42)

        args, _ = mock_cursor.execute.call_args
        self.assertIn("WHEN requires_dat THEN 'DAT_IN_PROGRESS'", args[0])
        self.assertIn("ELSE 'OET_IN_PROGRESS'", args[0])
        self.assertEqual(args[1], (42,))
        mock_conn.commit.assert_called_once()
        self.assertEqual(result["status"], "DAT_IN_PROGRESS")

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_start_test_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.start_test(42)
        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.DbUtils')
    def test_review_test_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "status": "IN_REVIEW", "assigned_tester_name": "Alice"}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.review_test(42)

        args, _ = mock_cursor.execute.call_args
        self.assertIn("SET status = 'IN_REVIEW'", args[0])
        self.assertEqual(args[1], (42,))
        mock_conn.commit.assert_called_once()
        self.assertEqual(result["status"], "IN_REVIEW")

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_review_test_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.review_test(42)
        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.DbUtils')
    def test_complete_test_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "status": "COMPLETED", "assigned_tester_name": "Alice"}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.complete_test(42)

        args, _ = mock_cursor.execute.call_args
        self.assertIn("SET status = 'COMPLETED'", args[0])
        self.assertEqual(args[1], (42,))
        mock_conn.commit.assert_called_once()
        self.assertEqual(result["status"], "COMPLETED")

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_complete_test_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.complete_test(42)
        mock_logger.log.assert_called_once()

    # Delete Methods

    @patch('functions.tests.test_repository.DbUtils')
    def test_soft_delete_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "status": "ARCHIVED", "assigned_tester_name": "Alice"}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.soft_delete(42)

        args, _ = mock_cursor.execute.call_args
        self.assertIn("SET status = %s", args[0])
        self.assertEqual(args[1], ("ARCHIVED", 42))
        mock_conn.commit.assert_called_once()
        self.assertEqual(result["status"], "ARCHIVED")
        self.assertEqual(result["assigned_tester_name"], "Alice")

    @patch('functions.tests.test_repository.DbUtils')
    def test_soft_delete_unarchive_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(
            {"test_id": 42, "status": "NOT_STARTED", "assigned_tester_name": "Alice"},
            fetchone=True,
        )
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.soft_delete(42, archive=False)

        args, _ = mock_cursor.execute.call_args
        self.assertIn("SET status = %s", args[0])
        self.assertEqual(args[1], ("NOT_STARTED", 42))
        mock_conn.commit.assert_called_once()
        self.assertEqual(result["status"], "NOT_STARTED")

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_soft_delete_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.soft_delete(42)
        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.DbUtils')
    def test_hard_delete_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "assigned_tester_name": "Alice"}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.hard_delete(42)

        args, _ = mock_cursor.execute.call_args
        self.assertIn("DELETE FROM tests", args[0])
        mock_conn.commit.assert_called_once()
        self.assertEqual(result["test_id"], 42)
        self.assertEqual(result["assigned_tester_name"], "Alice")
    
    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_hard_delete_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.hard_delete(42)
        mock_logger.log.assert_called_once()

    # Not-found (None) return cases

    @patch('functions.tests.test_repository.DbUtils')
    def test_get_tests_by_id_not_found(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(None, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.get_tests_by_id(9999)

        self.assertIsNone(result)

    @patch('functions.tests.test_repository.DbUtils')
    def test_update_assigned_tester_not_found(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(None, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.update_assigned_tester(9999, 1)

        self.assertIsNone(result)

    @patch('functions.tests.test_repository.DbUtils')
    def test_update_dat_track_not_found(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(None, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.update_dat_track(9999, "TESTING_READY", "DAT_IN_PROGRESS")

        self.assertIsNone(result)

    @patch('functions.tests.test_repository.DbUtils')
    def test_update_oet_track_not_found(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(None, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.update_oet_track(9999, "TESTING_READY", "OET_IN_PROGRESS")

        self.assertIsNone(result)

    @patch('functions.tests.test_repository.DbUtils')
    def test_start_test_not_found(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(None, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.start_test(9999)

        self.assertIsNone(result)

    @patch('functions.tests.test_repository.DbUtils')
    def test_review_test_not_found(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(None, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.review_test(9999)

        self.assertIsNone(result)

    @patch('functions.tests.test_repository.DbUtils')
    def test_complete_test_not_found(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(None, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.complete_test(9999)

        self.assertIsNone(result)

    @patch('functions.tests.test_repository.DbUtils')
    def test_soft_delete_not_found(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(None, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.soft_delete(9999)

        self.assertIsNone(result)

    @patch('functions.tests.test_repository.DbUtils')
    def test_hard_delete_not_found(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(None, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.hard_delete(9999)

        self.assertIsNone(result)

    @patch('functions.tests.test_repository.DbUtils')
    def test_create_not_found(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(None, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.create("VGCP-NONE", 1, "Desc", True, False, "2026-03-01")

        self.assertIsNone(result)

    # Audit context branch coverage

    @patch('functions.tests.test_repository.TestAuditUtils')
    @patch('functions.tests.test_repository.DbUtils')
    def test_update_assigned_tester_with_audit_context(self, mock_db, mock_audit):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "assigned_tester_id": 500}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn
        mock_audit.get_context.return_value = {"actor_user_id": 1}
        mock_audit.fetch_before.return_value = {"test_id": 42, "assigned_tester_id": 100}

        result = TestRepository.update_assigned_tester(42, 500)

        mock_audit.fetch_before.assert_called_once()
        mock_audit.audit_update.assert_called_once()
        self.assertEqual(result["assigned_tester_id"], 500)

    @patch('functions.tests.test_repository.TestAuditUtils')
    @patch('functions.tests.test_repository.DbUtils')
    def test_start_test_with_audit_context(self, mock_db, mock_audit):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "status": "DAT_IN_PROGRESS"}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn
        mock_audit.get_context.return_value = {"actor_user_id": 1}
        mock_audit.fetch_before.return_value = {"test_id": 42, "status": "NOT_STARTED"}

        result = TestRepository.start_test(42)

        mock_audit.fetch_before.assert_called_once()
        mock_audit.audit_update.assert_called_once()

    @patch('functions.tests.test_repository.TestAuditUtils')
    @patch('functions.tests.test_repository.DbUtils')
    def test_complete_test_with_audit_context(self, mock_db, mock_audit):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "status": "COMPLETED"}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn
        mock_audit.get_context.return_value = {"actor_user_id": 1}
        mock_audit.fetch_before.return_value = {"test_id": 42, "status": "IN_REVIEW"}

        result = TestRepository.complete_test(42)

        mock_audit.fetch_before.assert_called_once()
        mock_audit.audit_update.assert_called_once()

    @patch('functions.tests.test_repository.TestAuditUtils')
    @patch('functions.tests.test_repository.DbUtils')
    def test_soft_delete_with_audit_context(self, mock_db, mock_audit):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "status": "ARCHIVED"}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn
        mock_audit.get_context.return_value = {"actor_user_id": 1}
        mock_audit.fetch_before.return_value = {"test_id": 42, "status": "COMPLETED"}

        result = TestRepository.soft_delete(42)

        mock_audit.fetch_before.assert_called_once()
        mock_audit.audit_soft_delete.assert_called_once()

    @patch('functions.tests.test_repository.TestAuditUtils')
    @patch('functions.tests.test_repository.DbUtils')
    def test_soft_unarchive_with_audit_context(self, mock_db, mock_audit):
        mock_conn, mock_cursor = self._mock_connection(
            {"test_id": 42, "status": "NOT_STARTED"},
            fetchone=True,
        )
        mock_db.get_db_connection.return_value = mock_conn
        mock_audit.get_context.return_value = {"actor_user_id": 1}
        mock_audit.fetch_before.return_value = {"test_id": 42, "status": "ARCHIVED"}

        TestRepository.soft_delete(42, archive=False)

        mock_audit.fetch_before.assert_called_once()
        mock_audit.audit_update.assert_called_once()
        mock_audit.audit_soft_delete.assert_not_called()

    @patch('functions.tests.test_repository.TestAuditUtils')
    @patch('functions.tests.test_repository.DbUtils')
    def test_hard_delete_with_audit_context(self, mock_db, mock_audit):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn
        mock_audit.get_context.return_value = {"actor_user_id": 1}
        mock_audit.fetch_before.return_value = {"test_id": 42}

        result = TestRepository.hard_delete(42)

        mock_audit.fetch_before.assert_called_once()
        mock_audit.audit_hard_delete.assert_called_once()

    @patch('functions.tests.test_repository.TestAuditUtils')
    @patch('functions.tests.test_repository.DbUtils')
    def test_update_details_with_audit_context(self, mock_db, mock_audit):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "control_id": 10}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn
        mock_audit.get_context.return_value = {"actor_user_id": 1}
        mock_audit.fetch_before.return_value = {"test_id": 42, "description": "Before"}

        result = TestRepository.update_details(
            42,
            "VGCP-101010",
            2,
            505,
            False,
            True,
            "2026-04-01",
            "2026-03-25",
            "Updated Desc",
            ["https://example.com/evidence"],
        )

        mock_audit.fetch_before.assert_called_once()
        mock_audit.audit_update.assert_called_once()
        self.assertEqual(result["test_id"], 42)

    @patch('functions.tests.test_repository.TestAuditUtils')
    @patch('functions.tests.test_repository.DbUtils')
    def test_update_evidence_links_with_audit_context(self, mock_db, mock_audit):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "evidence_links": []}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn
        mock_audit.get_context.return_value = {"actor_user_id": 1}
        mock_audit.fetch_before.return_value = {"test_id": 42, "evidence_links": ["old"]}

        result = TestRepository.update_evidence_links(42, ["https://example.com/evidence"])

        mock_audit.fetch_before.assert_called_once()
        mock_audit.audit_update.assert_called_once()
        self.assertEqual(result["test_id"], 42)

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.TestAuditUtils')
    @patch('functions.tests.test_repository.DbUtils')
    def test_update_evidence_links_none_payload_raises(self, mock_db, mock_audit, mock_logger):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn
        mock_audit.get_context.return_value = None

        with self.assertRaises(ValueError):
            TestRepository.update_evidence_links(42, None)

    @patch('functions.tests.test_repository.TestAuditUtils')
    @patch('functions.tests.test_repository.DbUtils')
    def test_update_dat_track_with_audit_context(self, mock_db, mock_audit):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "dat_step": "Phase 2", "status": "DAT_IN_PROGRESS"}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn
        mock_audit.get_context.return_value = {"actor_user_id": 1}
        mock_audit.fetch_before.return_value = {"test_id": 42, "dat_step": "Phase 1", "status": "NOT_STARTED"}

        result = TestRepository.update_dat_track(42, "Phase 2", "DAT_IN_PROGRESS")

        mock_audit.fetch_before.assert_called_once()
        mock_audit.audit_update.assert_called_once()
        self.assertEqual(result["status"], "DAT_IN_PROGRESS")

    @patch('functions.tests.test_repository.TestAuditUtils')
    @patch('functions.tests.test_repository.DbUtils')
    def test_update_oet_track_with_audit_context(self, mock_db, mock_audit):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "oet_step": "Step 1", "status": "OET_IN_PROGRESS"}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn
        mock_audit.get_context.return_value = {"actor_user_id": 1}
        mock_audit.fetch_before.return_value = {"test_id": 42, "oet_step": "Step 0", "status": "NOT_STARTED"}

        result = TestRepository.update_oet_track(42, "Step 1", "OET_IN_PROGRESS")

        mock_audit.fetch_before.assert_called_once()
        mock_audit.audit_update.assert_called_once()
        self.assertEqual(result["status"], "OET_IN_PROGRESS")

    @patch('functions.tests.test_repository.TestAuditUtils')
    @patch('functions.tests.test_repository.DbUtils')
    def test_review_test_with_audit_context(self, mock_db, mock_audit):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "status": "IN_REVIEW"}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn
        mock_audit.get_context.return_value = {"actor_user_id": 1}
        mock_audit.fetch_before.return_value = {"test_id": 42, "status": "DAT_IN_PROGRESS"}

        result = TestRepository.review_test(42)

        mock_audit.fetch_before.assert_called_once()
        mock_audit.audit_update.assert_called_once()
        self.assertEqual(result["status"], "IN_REVIEW")

    def test_normalize_evidence_links_none_returns_none(self):
        self.assertIsNone(TestRepository._normalize_evidence_links(None))

    def test_normalize_evidence_links_non_list_raises(self):
        with self.assertRaises(ValueError):
            TestRepository._normalize_evidence_links("not-a-list")

    def test_normalize_evidence_links_filters_none_and_empty_and_dedups(self):
        links = [None, "  http://a.com  ", "", "http://a.com", "http://b.com"]
        cleaned = TestRepository._normalize_evidence_links(links)
        self.assertEqual(cleaned, ["http://a.com", "http://b.com"])

    def test_normalize_evidence_links_preserves_order_first_occurrence(self):
        links = ["b", "a", "b", "c"]
        self.assertEqual(TestRepository._normalize_evidence_links(links), ["b", "a", "c"]) 
