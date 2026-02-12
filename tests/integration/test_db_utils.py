import pytest
import os
import sys
from pathlib import Path

# Add functions to path so we can import db_utils
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "functions" / "common"))

from db_utils import get_db_connection


class TestDBUtils:
    """Test database utility functions and connectivity"""

    def test_get_db_connection_succeeds(self):
        """Verify get_db_connection can establish a connection"""
        try:
            conn = get_db_connection()
            assert conn is not None, "Connection object should not be None"
            assert not conn.closed, "Connection should be open"
            conn.close()
        except Exception as e:
            pytest.fail(f"get_db_connection() failed: {e}")

    def test_db_connection_can_query(self):
        """Verify the connection can execute queries"""
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 as test_value")
                result = cur.fetchone()
            assert result is not None, "Query should return a result"
            assert result['test_value'] == 1, "Query result should be 1"
        finally:
            conn.close()

    def test_db_connection_tables_exist(self):
        """Verify all expected tables exist in the database"""
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = {row['table_name'] for row in cur.fetchall()}
            
            expected_tables = {'audit_logs', 'comments', 'controls', 'users', 'tests', 'requests'}
            assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"
        finally:
            conn.close()

    def test_db_has_test_data(self):
        """Verify seed data has been loaded"""
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                # Check users
                cur.execute("SELECT COUNT(*) as count FROM users")
                user_count = cur.fetchone()['count']
                assert user_count > 0, "Database should have users after seeding"
                
                # Check controls
                cur.execute("SELECT COUNT(*) as count FROM controls")
                control_count = cur.fetchone()['count']
                assert control_count > 0, "Database should have controls after seeding"
                
                # Check requests
                cur.execute("SELECT COUNT(*) as count FROM requests")
                request_count = cur.fetchone()['count']
                assert request_count > 0, "Database should have requests after seeding"
        finally:
            conn.close()

    def test_db_connection_with_realdict_cursor(self):
        """Verify RealDictCursor is working (dict-like access)"""
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users LIMIT 1")
                row = cur.fetchone()
            
            # RealDictCursor should support dict-like access
            assert row is not None, "Should have at least one user"
            assert 'user_id' in row, "Should be able to access columns as dict keys"
            assert 'email' in row, "Should be able to access email column"
            assert 'role' in row, "Should be able to access role column"
        finally:
            conn.close()

    def test_db_connection_close_works(self):
        """Verify connection closes properly"""
        conn = get_db_connection()
        assert not conn.closed, "Connection should be open after creation"
        conn.close()
        assert conn.closed, "Connection should be closed after close()"

    def test_connected_to_correct_host(self):
        """Display database connection info and table list"""
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                # Show connection info
                cur.execute("SELECT current_database() as db_name, current_user as user, inet_server_addr() as host")
                result = cur.fetchone()
            
            print(f"\n{'='*60}")
            print(f"✅ Successfully Connected!")
            print(f"{'='*60}")
            print(f"Database: {result['db_name']}")
            print(f"User: {result['user']}")
            print(f"Host: {result['host']}")
            print(f"{'='*60}\n")
            
            # List all tables like \dt command
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT table_schema, table_name
                    FROM information_schema.tables
                    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                    ORDER BY table_name
                """)
                tables = cur.fetchall()
            
            if tables:
                print("Tables in Database:")
                for row in tables:
                    print(f"  • {row['table_name']}")
            
        finally:
            conn.close()

    def test_database_content_summary(self):
        """Show row counts for each table"""
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                    ORDER BY table_name
                """)
                tables = cur.fetchall()
            
            print(f"\n{'='*60}")
            print("Row Counts by Table:")
            print(f"{'='*60}")
            
            for table_row in tables:
                table_name = table_row['table_name']
                with conn.cursor() as cur:
                    cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                    count = cur.fetchone()['count']
                print(f"  {table_name}: {count} rows")
            
            print(f"{'='*60}\n")
            
        finally:
            conn.close()
