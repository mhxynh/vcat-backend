import pytest


class TestSchema:
    """Test database schema structure and constraints"""

    def test_expected_tables_exist(self, db_conn):
        """Verify all expected tables exist"""
        with db_conn.cursor() as cur:
            cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            """        )
            tables = {row[0] for row in cur.fetchall()}
        expected_tables = {"audit_logs", "comments", "controls", "users", "tests", "requests", "versions" }
        assert expected_tables.issubset(tables), f"Expected tables {expected_tables} not all found in database. Found tables: {tables}"

    def test_users_table_structure(self, db_conn):
        """Verify users table has expected columns with correct types"""
        with db_conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY column_name
            """)
            columns = {row[0]: (row[1], row[2]) for row in cur.fetchall()}
        
        assert "user_id" in columns
        assert "email" in columns
        assert "role" in columns
        assert "display_name" in columns
        assert columns["email"][0] == "character varying"
        assert columns["email"][1] == "NO"  # NOT NULL
        assert columns["user_id"][1] == "NO"  # PRIMARY KEY is NOT NULL

    def test_primary_keys_exist(self, db_conn):
        """Verify all tables have primary keys"""
        with db_conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name NOT IN ('pg_stat_statements')
                EXCEPT
                SELECT t.table_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.tables t ON tc.table_name = t.table_name
                WHERE tc.constraint_type = 'PRIMARY KEY'
                AND t.table_schema = 'public'
            """)
            tables_without_pk = [row[0] for row in cur.fetchall()]
        
        assert not tables_without_pk, f"Tables missing primary keys: {tables_without_pk}"

    def test_foreign_keys_exist(self, db_conn):
        """Verify key foreign keys are defined"""
        with db_conn.cursor() as cur:
            cur.execute("""
                SELECT constraint_name, table_name
                FROM information_schema.table_constraints
                WHERE constraint_type = 'FOREIGN KEY'
                AND table_schema = 'public'
            """)
            fks = {row[0]: row[1] for row in cur.fetchall()}
        
        # Verify some key foreign keys exist
        assert any('tests' in table for table in fks.values()), "Missing foreign keys in tests table"
        assert any('comments' in table for table in fks.values()), "Missing foreign keys in comments table"

    def test_enums_exist(self, db_conn):
        """Verify required ENUM types are defined"""
        with db_conn.cursor() as cur:
            cur.execute("""
                SELECT typname
                FROM pg_type
                WHERE typtype = 'e'
                AND typname IN ('user_role', 'request_status', 'test_status', 'test_track', 'audit_action', 'auditable_entity')
            """)
            enums = {row[0] for row in cur.fetchall()}
        
        expected_enums = {'user_role', 'request_status', 'test_status', 'test_track', 'audit_action', 'auditable_entity'}
        assert expected_enums.issubset(enums), f"Missing enums: {expected_enums - enums}"
