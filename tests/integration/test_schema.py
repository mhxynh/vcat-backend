import pytest


def _get_columns(db_conn, table_name):
    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name, data_type, is_nullable, udt_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY column_name
            """,
            (table_name,),
        )
        return {row[0]: (row[1], row[2], row[3]) for row in cur.fetchall()}


def _get_enum_values(db_conn, enum_name):
    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT enumlabel
            FROM pg_enum e
            JOIN pg_type t ON t.oid = e.enumtypid
            WHERE t.typname = %s
            ORDER BY e.enumsortorder
            """,
            (enum_name,),
        )
        return [row[0] for row in cur.fetchall()]


class TestSchema:
    """Test database schema structure and constraints"""

    def test_expected_tables_exist(self, db_conn):
        """Verify all expected tables exist"""
        with db_conn.cursor() as cur:
            cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            """)
            tables = {row[0] for row in cur.fetchall()}
        expected_tables = {"audit_logs", "comments", "controls", "users", "tests", "requests"}
        assert expected_tables.issubset(tables), f"Expected tables {expected_tables} not all found in database. Found tables: {tables}"

    def test_users_table_structure(self, db_conn):
        """Verify users table has expected columns with correct types"""
        columns = _get_columns(db_conn, "users")
        
        assert "user_id" in columns
        assert "email" in columns
        assert "role" in columns
        assert "display_name" in columns
        assert "is_active" in columns
        
        assert columns["email"][0] == "character varying"
        assert columns["email"][1] == "NO"  # NOT NULL
        assert columns["user_id"][1] == "NO"  # PRIMARY KEY is NOT NULL
        assert columns["role"][2] == "user_role"

    def test_controls_table_structure(self, db_conn):
        """Verify controls table has expected columns with correct types"""
        columns = _get_columns(db_conn, "controls")

        assert "control_id" in columns
        assert "vgcpid" in columns
        assert "control_owner" in columns
        assert "control_sme" in columns
        assert "escalation" in columns
        assert "is_active" in columns
        assert columns["vgcpid"][0] == "character varying"
        assert columns["control_owner"][1] == "NO"
        assert columns["control_sme"][1] == "NO"
        assert columns["escalation"][0] == "boolean"
        assert columns["is_active"][0] == "boolean"

    def test_requests_table_structure(self, db_conn):
        """Verify requests table has expected columns with correct types"""
        columns = _get_columns(db_conn, "requests")

        assert "request_id" in columns
        assert "requestor" in columns
        assert "due_date" in columns
        assert "status" in columns
        assert "created_by" in columns
        assert columns["requestor"][1] == "NO"
        assert columns["due_date"][1] == "NO"
        assert columns["status"][2] == "request_status"

    def test_tests_table_structure(self, db_conn):
        """Verify tests table has expected columns with correct types"""
        columns = _get_columns(db_conn, "tests")

        assert "test_id" in columns
        assert "request_id" in columns
        assert "control_id" in columns
        assert "test_type" in columns
        assert "status" in columns
        assert columns["request_id"][1] == "NO"
        assert columns["control_id"][1] == "NO"
        assert columns["test_type"][2] == "test_type"
        assert columns["status"][2] == "test_status"

    def test_comments_table_structure(self, db_conn):
        """Verify comments table has expected columns with correct types"""
        columns = _get_columns(db_conn, "comments")

        assert "comment_id" in columns
        assert "author_user_id" in columns
        assert "comment_text" in columns
        assert "posted_at" in columns
        assert columns["author_user_id"][1] == "NO"
        assert columns["comment_text"][1] == "NO"
        assert columns["email"][1] == "NO"
        assert columns["user_id"][1] == "NO"
        assert columns["is_active"][1] == "NO"

    def test_tests_table_structure(self, db_conn):
        """
        New Test: Verify tests table has the new DAT/OET track columns
        """
        with db_conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'tests'
            """)
            columns = {row[0]: row[1] for row in cur.fetchall()}

        # Verify the boolean flags exist
        assert "requires_dat" in columns
        assert "requires_oet" in columns
        assert columns["requires_dat"] == "boolean"
        assert columns["requires_oet"] == "boolean"
        # Verify the separate steps exist
        assert "dat_step" in columns
        assert "oet_step" in columns
        # Note: Postgres returns 'USER-DEFINED' for enums in information_schema
        assert columns["dat_step"] == "USER-DEFINED" 
        assert columns["oet_step"] == "USER-DEFINED"

        # Verify the macro status exists
        assert "status" in columns

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
        """Verify expected foreign key relationships are defined"""
        with db_conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    kcu.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                  ON ccu.constraint_name = tc.constraint_name
                 AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = 'public'
                """
            )
            fks = {tuple(row) for row in cur.fetchall()}

        expected = {
            ("requests", "created_by", "users", "user_id"),
            ("tests", "request_id", "requests", "request_id"),
            ("tests", "control_id", "controls", "control_id"),
            ("tests", "assigned_tester_id", "users", "user_id"),
            ("comments", "author_user_id", "users", "user_id"),
            ("comments", "test_id", "tests", "test_id"),
            ("comments", "request_id", "requests", "request_id"),
            ("audit_logs", "actor_user_id", "users", "user_id"),
        }

        missing = expected - fks
        assert not missing, f"Missing foreign keys: {missing}"
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
        assert any('requests' in table for table in fks.values()), "Missing foreign keys in requests table"

    def test_enums_exist(self, db_conn):
        """Verify required ENUM types are defined"""
        with db_conn.cursor() as cur:
            cur.execute("""
                SELECT typname
                FROM pg_type
                WHERE typtype = 'e'
                -- Removed 'test_type' from query as it was deleted
                AND typname IN ('user_role', 'request_status', 'test_status', 'audit_action', 'auditable_entity', 'test_progress_step')
            """)
            enums = {row[0] for row in cur.fetchall()}
        
        expected_enums = {'user_role', 'request_status', 'test_status', 'audit_action', 'auditable_entity', 'test_progress_step'}
        assert expected_enums.issubset(enums), f"Missing enums: {expected_enums - enums}"

    def test_enum_values(self, db_conn):
        """Verify enum values are correct"""
        expected = {
            "user_role": ["MANAGER", "TESTER"],
            "request_status": ["NOT_STARTED", "IN_PROGRESS", "IN_REVIEW", "COMPLETED", "BLOCKED", "ARCHIVED"],
            "test_status": ["NOT_STARTED", "IN_PROGRESS", "IN_REVIEW", "COMPLETED", "BLOCKED", "ARCHIVED"],
            "test_type": ["DAT", "OET"],
            "audit_action": ["CREATE", "UPDATE", "DELETE", "ROLLBACK"],
            "auditable_entity": ["CONTROL", "REQUEST", "TEST", "COMMENT", "USER"],
            "test_progress_step": [
                "TESTING_READY",
                "WALKTHROUGH_SCHEDULED",
                "TESTING_IN_PROGRESS",
                "TESTING_BLOCKED",
                "TESTING_CANCELED",
                "COMPLETED",
                "ADDRESSING_COMMENTS",
            ],
        }

        for enum_name, values in expected.items():
            assert _get_enum_values(db_conn, enum_name) == values

    def test_indexes_exist(self, db_conn):
        """Verify expected indexes exist"""
        with db_conn.cursor() as cur:
            cur.execute(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                """
            )
            indexes = {row[0] for row in cur.fetchall()}

        expected = {
            "idx_tests_request",
            "idx_tests_control",
            "idx_tests_type",
            "idx_tests_assigned",
            "idx_comments_test",
            "idx_comments_request",
            "idx_audit_entity",
            "idx_audit_actor",
        }

        missing = expected - indexes
        assert not missing, f"Missing indexes: {missing}"
