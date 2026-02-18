import os
from unittest import TestCase
from unittest.mock import patch
from utils.db_utils import DbUtils

MOCK_ENV = {
    'DB_HOST': 'localhost',
    'DB_PORT': '5432',
    'DB_NAME': 'test_db',
    'DB_USER': 'test_user',
    'DB_PASSWORD': 'test_pass',
}

class TestDBUtils(TestCase):
    @patch('utils.db_utils.Logger')
    @patch('psycopg2.connect', return_value="Connection successful")
    @patch.dict(os.environ, MOCK_ENV)
    def test_get_db_connection_success(self, mock_connect, mock_logger):
        conn = DbUtils.get_db_connection()

        mock_connect.assert_called_once()
        mock_logger.log.assert_called_with(level="INFO", message="Successfully connected to the database", extra_fields={"host": MOCK_ENV['DB_HOST'], "database": MOCK_ENV['DB_NAME']})
        self.assertIsNotNone(conn)

    @patch('utils.db_utils.Logger')
    @patch('psycopg2.connect', side_effect=Exception("Connection failed"))
    @patch.dict(os.environ, MOCK_ENV)
    def test_get_db_connection_exception(self, mock_connect, mock_logger):
        with self.assertRaises(Exception) as context:
            DbUtils.get_db_connection()

        mock_connect.assert_called_once()
        mock_logger.log.assert_called_with(level="ERROR", message="Database connection failed", extra_fields={"error": "Connection failed"})

    @patch('utils.db_utils.Logger')
    @patch.dict(os.environ, {}, clear=True)
    def test_get_db_connection_missing_env_vars(self, mock_logger):
        with self.assertRaises(Exception) as context:
            DbUtils.get_db_connection()

        mock_logger.log.assert_any_call(level="ERROR", message="Missing required database environment variables", extra_fields={"missing": ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']})
