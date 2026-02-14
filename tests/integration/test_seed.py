import pytest

class TestSeedData:
    """Test seed.sql generates expected data"""

    def test_seed_runs_and_has_data(self, seed_db_conn):
        """Verify seed created users"""
        with seed_db_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users")
            user_count = cur.fetchone()[0]
        assert user_count > 0, "No users created from seed"

    def test_seed_creates_managers_and_testers(self, seed_db_conn):
        """Verify seed creates both manager and tester roles"""
        with seed_db_conn.cursor() as cur:
            cur.execute("""
                SELECT role, COUNT(*) as count
                FROM users
                GROUP BY role
            """)
            roles = {row[0]: row[1] for row in cur.fetchall()}
        
        assert "MANAGER" in roles, "No MANAGER roles created"
        assert "TESTER" in roles, "No TESTER roles created"
        assert roles["MANAGER"] >= 1, "Should have at least 1 manager"
        assert roles["TESTER"] >= 1, "Should have at least 1 tester"

    def test_seed_creates_controls(self, seed_db_conn):
        """Verify seed creates controls"""
        with seed_db_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM controls")
            control_count = cur.fetchone()[0]
        assert control_count > 0, "No controls created from seed"

    def test_seed_creates_requests(self, seed_db_conn):
        """Verify seed creates requests"""
        with seed_db_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM requests")
            request_count = cur.fetchone()[0]
        assert request_count > 0, "No requests created from seed"

    def test_seed_creates_tests_with_tracks(self, db_conn):
        """
        Verify seed creates tests and assigns DAT/OET requirements correctly.
        Checks that boolean flags are working and we have a mix of types.
        """
        with db_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM tests")
            test_count = cur.fetchone()[0]
            
            # Check for presence of DAT requirements
            cur.execute("SELECT COUNT(*) FROM tests WHERE requires_dat = TRUE")
            dat_count = cur.fetchone()[0]

            # Check for presence of OET requirements
            cur.execute("SELECT COUNT(*) FROM tests WHERE requires_oet = TRUE")
            oet_count = cur.fetchone()[0]
            
            # Check for "Both" (Intersection)
            cur.execute("SELECT COUNT(*) FROM tests WHERE requires_dat = TRUE AND requires_oet = TRUE")
            both_count = cur.fetchone()[0]

        assert test_count > 0, "No tests created from seed"
        assert dat_count > 0, "No tests with DAT requirements created"
        assert oet_count > 0, "No tests with OET requirements created"
        # Based on your seed logic (80% both), this should be true
        assert both_count > 0, "No tests requiring BOTH tracks created"

    def test_seed_test_steps_alignment(self, db_conn):
        """
        Verify that if a track is required, it has a valid step, 
        and if not required, the step is NULL.
        """
        with db_conn.cursor() as cur:
            # 1. Verify Integrity: requires_dat=TRUE implies dat_step is NOT NULL
            cur.execute("""
                SELECT COUNT(*) FROM tests 
                WHERE requires_dat = TRUE AND dat_step IS NULL
            """)
            invalid_dat = cur.fetchone()[0]

            # 2. Verify Cleanup: requires_dat=FALSE implies dat_step IS NULL
            cur.execute("""
                SELECT COUNT(*) FROM tests 
                WHERE requires_dat = FALSE AND dat_step IS NOT NULL
            """)
            dirty_dat = cur.fetchone()[0]

        assert invalid_dat == 0, "Found tests requiring DAT but having NULL dat_step"
        assert dirty_dat == 0, "Found tests NOT requiring DAT but having a dat_step value"

    def test_seed_creates_comments(self, seed_db_conn):
        """Verify seed creates comments on requests and tests"""
        with seed_db_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM comments")
            comment_count = cur.fetchone()[0]
            
            cur.execute("""
                SELECT COUNT(*) FROM comments WHERE request_id IS NOT NULL
            """)
            request_comments = cur.fetchone()[0]
            
            cur.execute("""
                SELECT COUNT(*) FROM comments WHERE test_id IS NOT NULL
            """)
            test_comments = cur.fetchone()[0]
        
        assert comment_count > 0, "No comments created from seed"
        assert request_comments > 0, "No request-level comments created"
        assert test_comments > 0, "No test-level comments created"

    def test_seed_foreign_keys_valid(self, seed_db_conn):
        """Verify seed data respects foreign key constraints"""
        with seed_db_conn.cursor() as cur:
            # Check that all test assignments reference valid users
            cur.execute("""
                SELECT COUNT(*)
                FROM tests t
                LEFT JOIN users u ON t.assigned_tester_id = u.user_id
                WHERE t.assigned_tester_id IS NOT NULL
                AND u.user_id IS NULL
            """)
            invalid_tester_refs = cur.fetchone()[0]
            
            # Check that all request creators reference valid users
            cur.execute("""
                SELECT COUNT(*)
                FROM requests r
                LEFT JOIN users u ON r.created_by = u.user_id
                WHERE r.created_by IS NOT NULL
                AND u.user_id IS NULL
            """)
            invalid_creator_refs = cur.fetchone()[0]
            
            # Check that all comment authors reference valid users
            cur.execute("""
                SELECT COUNT(*)
                FROM comments c
                LEFT JOIN users u ON c.author_user_id = u.user_id
                WHERE u.user_id IS NULL
            """)
            invalid_author_refs = cur.fetchone()[0]
        
        assert invalid_tester_refs == 0, "Tests reference non-existent users"
        assert invalid_creator_refs == 0, "Requests reference non-existent creator users"
        assert invalid_author_refs == 0, "Comments reference non-existent author users"

    def test_seed_request_status_values_valid(self, seed_db_conn):
        """Verify all request statuses are valid enum values"""
        with seed_db_conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT status
                FROM requests
            """)
            statuses = {row[0] for row in cur.fetchall()}
            valid_statuses = {'NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'BLOCKED', 'ARCHIVED'}
            
        assert statuses.issubset(valid_statuses), f"Invalid request statuses: {statuses - valid_statuses}"

    def test_seed_test_status_values_valid(self, seed_db_conn):
        """Verify all test statuses are valid enum values"""
        with seed_db_conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT status
                FROM tests
            """)
            statuses = {row[0] for row in cur.fetchall()}
            valid_statuses = {'NOT_STARTED', 'IN_PROGRESS', 'IN_REVIEW', 'COMPLETED', 'BLOCKED', 'ARCHIVED'}
            
        assert statuses.issubset(valid_statuses), f"Invalid test statuses: {statuses - valid_statuses}"