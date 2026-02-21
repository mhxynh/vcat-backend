from unittest import TestCase
from unittest.mock import patch, MagicMock
from utils.crud import CrudUtils

class TestCrudUtils(TestCase):
    def _mock_connection(self, rows, fetchone=False):
        # Helper to create a mock connection with a cursor that returns rows.
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        if fetchone:
            mock_cursor.fetchone.return_value = rows
        else:
            mock_cursor.fetchall.return_value = rows
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        return mock_conn, mock_cursor

    # Get All
    @patch('utils.crud.DbUtils')
    def test_get_all_returns_list(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection([
            {"control_id": 1, "vgcpid": "VGCP-001"},
            {"control_id": 2, "vgcpid": "VGCP-002"},
        ])
        mock_db.get_db_connection.return_value = mock_conn

        result = CrudUtils.get_all("controls")

        mock_cursor.execute.assert_called_once_with("SELECT * FROM controls")
        mock_conn.close.assert_called_once()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["vgcpid"], "VGCP-001")

    @patch('utils.crud.DbUtils')
    def test_get_all_returns_empty_list(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection([])
        mock_db.get_db_connection.return_value = mock_conn

        result = CrudUtils.get_all("controls")

        mock_conn.close.assert_called_once()
        self.assertEqual(result, [])

    @patch('utils.crud.Logger')
    @patch('utils.crud.DbUtils')
    def test_get_all_raises_and_logs_on_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")

        with self.assertRaises(Exception):
            CrudUtils.get_all("controls")

        mock_logger.log.assert_called_with(level="ERROR", message="Error fetching all records", extra_fields={"error": "DB down", "table": "controls"})

    # Get by ID
    @patch('utils.crud.Logger')
    @patch('utils.crud.DbUtils')
    def test_get_by_id_returns_record(self, mock_db, mock_logger):
        mock_conn, mock_cursor = self._mock_connection(
            {"control_id": 1, "vgcpid": "VGCP-001"}, fetchone=True
        )
        mock_db.get_db_connection.return_value = mock_conn

        result = CrudUtils.get_by_id("controls", "vgcpid", "VGCP-001")

        self.assertEqual(result["vgcpid"], "VGCP-001")
        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM controls WHERE vgcpid = %s", ("VGCP-001",)
        )
        mock_conn.close.assert_called_once()

    @patch('utils.crud.DbUtils')
    def test_get_by_id_returns_none_when_not_found(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(None, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = CrudUtils.get_by_id("controls", "vgcpid", "VGCP-999")

        self.assertIsNone(result)
        mock_conn.close.assert_called_once()

    @patch('utils.crud.Logger')
    @patch('utils.crud.DbUtils')
    def test_get_by_id_raises_and_logs_on_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")

        with self.assertRaises(Exception):
            CrudUtils.get_by_id("controls", "vgcpid", "VGCP-001")

        mock_logger.log.assert_called_once_with(level="ERROR", message="Error fetching record by ID", extra_fields={'error': 'DB down', 'table': 'controls', 'pk_column': 'vgcpid', 'pk_value': 'VGCP-001'})

    # Create
    @patch('utils.crud.Logger')
    @patch('utils.crud.DbUtils')
    def test_create_returns_created_record(self, mock_db, mock_logger):
        created_row = {"control_id": 10, "vgcpid": "VGCP-999", "description": "New"}
        mock_conn, mock_cursor = self._mock_connection(created_row, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        columns = ["vgcpid", "description"]
        values = ["VGCP-999", "New"]
        result = CrudUtils.create("controls", columns, values)

        self.assertEqual(result["vgcpid"], "VGCP-999")
        mock_cursor.execute.assert_called_once_with(
            "INSERT INTO controls (vgcpid, description) VALUES (%s, %s) RETURNING *",
            ["VGCP-999", "New"]
        )
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('utils.crud.Logger')
    @patch('utils.crud.DbUtils')
    def test_create_raises_and_logs_on_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")

        with self.assertRaises(Exception):
            CrudUtils.create("controls", ["vgcpid"], ["VGCP-999"])

        mock_logger.log.assert_called_with(level="ERROR", message="Error creating record", extra_fields={"error": "DB down", "table": "controls", "columns": ["vgcpid"]})

    # Update
    @patch('utils.crud.DbUtils')
    def test_update_returns_updated_record(self, mock_db):
        updated_row = {"control_id": 1, "vgcpid": "VGCP-001", "description": "Updated"}
        mock_conn, mock_cursor = self._mock_connection(updated_row, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        updates = {"description": "Updated"}
        result = CrudUtils.update("controls", "vgcpid", "VGCP-001", updates)

        mock_cursor.execute.assert_called_once_with(
            "UPDATE controls SET description = %s WHERE vgcpid = %s RETURNING *",
            ["Updated", "VGCP-001"]
        )
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
        self.assertEqual(result["description"], "Updated")

    @patch('utils.crud.DbUtils')
    def test_update_returns_none_when_not_found(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(None, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = CrudUtils.update("controls", "vgcpid", "VGCP-999", {"description": "X"})

        self.assertIsNone(result)
        mock_conn.close.assert_called_once()

    @patch('utils.crud.Logger')
    @patch('utils.crud.DbUtils')
    def test_update_raises_and_logs_on_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")

        with self.assertRaises(Exception):
            CrudUtils.update("controls", "vgcpid", "VGCP-001", {"description": "X"})

        mock_logger.log.assert_called_once_with(level="ERROR", message="Error updating record", extra_fields={"error": "DB down", "table": "controls", "pk_column": "vgcpid", "pk_value": "VGCP-001", "updates": {"description": "X"}})

    # Deactivate (soft delete)
    @patch('utils.crud.DbUtils')
    def test_deactivate_returns_updated_record(self, mock_db):
        updated_row = {"control_id": 1, "vgcpid": "VGCP-001", "is_active": False}
        mock_conn, mock_cursor = self._mock_connection(updated_row, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = CrudUtils.deactivate("controls", "vgcpid", "VGCP-001")

        mock_cursor.execute.assert_called_once_with("UPDATE controls SET is_active = FALSE WHERE vgcpid = %s RETURNING *", "VGCP-001")
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
        self.assertEqual(result["is_active"], False)

    @patch('utils.crud.Logger')
    @patch('utils.crud.DbUtils')
    def test_deactivate_raises_and_logs_on_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")

        with self.assertRaises(Exception):
            CrudUtils.deactivate("controls", "vgcpid", "VGCP-001")

        mock_logger.log.assert_called_once_with(level="ERROR", message="Error deactivating record", extra_fields={"error": "DB down", "table": "controls", "pk_column": "vgcpid", "pk_value": "VGCP-001"})

    # Hard Delete
    @patch('utils.crud.DbUtils')
    def test_hard_delete_returns_deleted_record(self, mock_db):
        deleted_row = {"control_id": 1, "vgcpid": "VGCP-001"}
        mock_conn, mock_cursor = self._mock_connection(deleted_row, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = CrudUtils.hard_delete("controls", "vgcpid", "VGCP-001")

        mock_cursor.execute.assert_called_once_with("DELETE FROM controls WHERE vgcpid = %s RETURNING *", ("VGCP-001",))
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
        self.assertEqual(result["vgcpid"], "VGCP-001")

    @patch('utils.crud.DbUtils')
    def test_hard_delete_returns_none_when_not_found(self, mock_db):
        mock_conn, mock_cursor = self._mock_connection(None, fetchone=True)
        mock_db.get_db_connection.return_value = mock_conn

        result = CrudUtils.hard_delete("controls", "vgcpid", "VGCP-999")

        self.assertIsNone(result)
        mock_conn.close.assert_called_once()

    @patch('utils.crud.Logger')
    @patch('utils.crud.DbUtils')
    def test_hard_delete_raises_and_logs_on_error(self, mock_db, mock_logger):
        mock_db.get_db_connection.side_effect = Exception("DB down")

        with self.assertRaises(Exception):
            CrudUtils.hard_delete("controls", "vgcpid", "VGCP-001")

        mock_logger.log.assert_called_once_with(level="ERROR", message="Error hard deleting record", extra_fields={"error": "DB down", "table": "controls", "pk_column": "vgcpid", "pk_value": "VGCP-001"})
