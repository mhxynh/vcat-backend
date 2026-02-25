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

    # get_tests_by_request_with_details

    @patch('functions.tests.test_repository.DbUtils')
    def test_get_tests_by_request_with_details_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection([
            {"test_id": 1, "request_id": 100, "vgcpid": "VGCP-001", "tester_name": "Alice"}
        ])
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.get_tests_by_request_with_details(100)

        args, kwargs = mock_cursor.execute.call_args
        sql_query, sql_params = args[0], args[1]
        
        self.assertIn("JOIN controls c", sql_query)
        self.assertIn("LEFT JOIN users u", sql_query)
        self.assertEqual(sql_params, (100,))
        
        mock_conn.close.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["tester_name"], "Alice")

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_get_tests_by_request_with_details_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")

        with self.assertRaises(Exception):
            TestRepository.get_tests_by_request_with_details(100)

        mock_logger.log.assert_called_once_with(
            level="ERROR", 
            message="Error fetching test details by request", 
            extra_fields={'error': 'DB down', 'request_id': 100}
        )

    # update_dat_track

    @patch('functions.tests.test_repository.DbUtils')
    def test_update_dat_track_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(
        {"test_id": 42, "dat_step": "Original Step", "status": "IN_PROGRESS"}, 
        fetchone=True
    )
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.update_dat_track(42, None, "IN_PROGRESS")

        args, _ = mock_cursor.execute.call_args
        self.assertIn("COALESCE(%s, dat_step)", args[0])
        self.assertEqual(args[1], (None, "IN_PROGRESS", 42))
        self.assertEqual(result["dat_step"], "Original Step")

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_update_dat_track_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")

        with self.assertRaises(Exception):
            TestRepository.update_dat_track(42, "Phase 2", "IN_PROGRESS")

        mock_logger.log.assert_called_once_with(
            level="ERROR", 
            message="Error updating DAT track", 
            extra_fields={'error': 'DB down', 'test_id': 42}
        )

    # update_oet_track

    @patch('functions.tests.test_repository.DbUtils')
    def test_update_oet_track_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(
            {"test_id": 42, "oet_step": "Step 1", "status": "IN_PROGRESS"}, fetchone=True
        )
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.update_oet_track(42, "Step 1", "IN_PROGRESS")

        args, kwargs = mock_cursor.execute.call_args
        sql_query = args[0]
        
        self.assertIn("UPDATE tests", sql_query)
        self.assertIn("oet_step = COALESCE(%s, oet_step)", sql_query)
        self.assertIn("status = COALESCE(%s, status)", sql_query)
        self.assertEqual(args[1], ("Step 1", "IN_PROGRESS", 42))
        
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
        self.assertEqual(result["oet_step"], "Step 1")

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_update_oet_track_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")

        with self.assertRaises(Exception):
            TestRepository.update_oet_track(42, "Step 1", "IN_PROGRESS")

        mock_logger.log.assert_called_once_with(
            level="ERROR", 
            message="Error updating OET track", 
            extra_fields={'error': 'DB down', 'test_id': 42}
        )

    # start_test

    @patch('functions.tests.test_repository.DbUtils')
    def test_start_test_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(
            {"test_id": 42, "status": "IN_PROGRESS"}, fetchone=True
        )
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.start_test(42)

        args, kwargs = mock_cursor.execute.call_args
        self.assertIn("SET status = 'IN_PROGRESS'", args[0])
        self.assertIn("COALESCE(start_date, current_date)", args[0])
        self.assertEqual(args[1], (42,))
        
        mock_conn.commit.assert_called_once()
        self.assertEqual(result["status"], "IN_PROGRESS")

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_start_test_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")

        with self.assertRaises(Exception):
            TestRepository.start_test(42)

        mock_logger.log.assert_called_once_with(
            level="ERROR", 
            message="Error starting test", 
            extra_fields={'error': 'DB down', 'test_id': 42}
        )

    # complete_test

    @patch('functions.tests.test_repository.DbUtils')
    def test_complete_test_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(
            {"test_id": 42, "status": "COMPLETED"}, fetchone=True
        )
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.complete_test(42)

        args, kwargs = mock_cursor.execute.call_args
        self.assertIn("SET status = 'COMPLETED'", args[0])
        self.assertIn("complete_date = current_date", args[0])
        self.assertEqual(args[1], (42,))
        
        mock_conn.commit.assert_called_once()
        self.assertEqual(result["status"], "COMPLETED")

    @patch('functions.tests.test_repository.Logger')
    @patch('functions.tests.test_repository.DbUtils')
    def test_complete_test_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")

        with self.assertRaises(Exception):
            TestRepository.complete_test(42)

        mock_logger.log.assert_called_once_with(
            level="ERROR", 
            message="Error completing test", 
            extra_fields={'error': 'DB down', 'test_id': 42}
        )

    # review_test

    @patch('functions.tests.test_repository.DbUtils')
    def test_review_test_success(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(
            {"test_id": 42, "status": "IN_REVIEW"}, fetchone=True
        )
        mock_db.get_db_connection.return_value = mock_conn

        result = TestRepository.review_test(42)

        args, kwargs = mock_cursor.execute.call_args
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

        mock_logger.log.assert_called_once_with(
            level="ERROR", 
            message="Error reviewing test", 
            extra_fields={'error': 'DB down', 'test_id': 42}
        )