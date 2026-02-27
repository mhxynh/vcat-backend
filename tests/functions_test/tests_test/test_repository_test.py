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
        mock_conn, mock_cursor = self._mock_connection([{"test_id": 1, "vgcpid": "VGCP-001"}])
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.get_all_tests()

        args, _ = mock_cursor.execute.call_args
        self.assertIn("SELECT t.*, c.vgcpid", args[0])
        self.assertEqual(len(result), 1)

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_get_all_tests_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.get_all_tests()
        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.DbUtils')
    def test_get_tests_by_id_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "vgcpid": "VGCP-001"}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.get_tests_by_id(42)

        args, kwargs = mock_cursor.execute.call_args
        self.assertIn("WHERE t.test_id = %s", args[0])
        self.assertEqual(args[1], (42,))
        self.assertEqual(result["test_id"], 42)

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_get_tests_by_id_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.get_tests_by_id(42)
        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.DbUtils')
    def test_get_tests_by_request_id_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection([{"test_id": 1, "request_id": 100}])
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

        args, kwargs = mock_cursor.execute.call_args
        sql_query, sql_params = args[0], args[1]
        
        self.assertIn("JOIN controls c", sql_query)
        self.assertIn("LEFT JOIN users u", sql_query)
        self.assertEqual(sql_params, (100,))
        self.assertEqual(len(result), 1)
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
        mock_conn, mock_cursor = self._mock_connection([{"test_id": 1, "control_id": 20}])
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
        mock_conn, mock_cursor = self._mock_connection({"test_id": 1, "description": "Desc"}, fetchone=True)
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

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_create_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.create("VGCP", 1, "Desc", True, False, "2026")
        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.DbUtils')
    def test_update_dat_track_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(
            {"test_id": 42, "dat_step": "Phase 2", "status": "IN_PROGRESS"}, fetchone=True
        )
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.update_dat_track(42, "Phase 2", "IN_PROGRESS")

        args, _ = mock_cursor.execute.call_args
        self.assertIn("SET dat_step = %s, status = %s", args[0])
        self.assertEqual(args[1], ("Phase 2", "IN_PROGRESS", 42))
        mock_conn.commit.assert_called_once()
        self.assertEqual(result["dat_step"], "Phase 2")

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_update_dat_track_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.update_dat_track(42, "Phase 2", "IN_PROGRESS")
        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.DbUtils')
    def test_update_oet_track_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(
            {"test_id": 42, "oet_step": "Step 1", "status": "IN_PROGRESS"}, fetchone=True
        )
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.update_oet_track(42, "Step 1", "IN_PROGRESS")

        args, _ = mock_cursor.execute.call_args
        self.assertIn("SET oet_step = %s, status = %s", args[0])
        self.assertEqual(args[1], ("Step 1", "IN_PROGRESS", 42))
        mock_conn.commit.assert_called_once()
        self.assertEqual(result["oet_step"], "Step 1")

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_update_oet_track_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.update_oet_track(42, "Step 1", "IN_PROGRESS")
        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.DbUtils')
    def test_start_test_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "status": "IN_PROGRESS"}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.start_test(42)

        args, _ = mock_cursor.execute.call_args
        self.assertIn("SET status = 'IN_PROGRESS'", args[0])
        self.assertEqual(args[1], (42,))
        mock_conn.commit.assert_called_once()
        self.assertEqual(result["status"], "IN_PROGRESS")

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_start_test_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.start_test(42)
        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.DbUtils')
    def test_review_test_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "status": "IN_REVIEW"}, fetchone=True)
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
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "status": "COMPLETED"}, fetchone=True)
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
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42, "status": "ARCHIVED"}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.soft_delete(42)

        args, _ = mock_cursor.execute.call_args
        self.assertIn("SET status = 'ARCHIVED'", args[0])
        mock_conn.commit.assert_called_once()
        self.assertEqual(result["status"], "ARCHIVED")

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_soft_delete_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.soft_delete(42)
        mock_logger.log.assert_called_once()

    @patch('functions.tests.test_repository.DbUtils')
    def test_hard_delete_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection({"test_id": 42}, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.hard_delete(42)

        args, _ = mock_cursor.execute.call_args
        self.assertIn("DELETE FROM tests", args[0])
        mock_conn.commit.assert_called_once()
        self.assertEqual(result["test_id"], 42)

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_hard_delete_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")
        with self.assertRaises(Exception):
            TestRepository.hard_delete(42)
        mock_logger.log.assert_called_once()
