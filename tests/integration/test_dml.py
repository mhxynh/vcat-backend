import pytest
import json
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor


class TestControlsDML:
    """Test DML queries for controls table"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, db_conn):
        """Setup and teardown for each test"""
        cursor = db_conn.cursor()
        # Clear dependents before controls to satisfy FKs
        cursor.execute("DELETE FROM comments;")
        cursor.execute("DELETE FROM tests;")
        cursor.execute("DELETE FROM controls;")
        db_conn.commit()
        cursor.close()
        yield
        # Cleanup after test
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM comments;")
        cursor.execute("DELETE FROM tests;")
        cursor.execute("DELETE FROM controls;")
        db_conn.commit()
        cursor.close()

    def test_create_control(self, db_conn):
        """Test INSERT - Create a new control"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        sql = """INSERT INTO controls (vgcpid, description, control_owner, control_sme, escalation, is_active)
                 VALUES (%s, %s, %s, %s, %s, TRUE)
                 RETURNING *"""
        
        cursor.execute(sql, ('VGCP-001', 'Test Control', 'John Doe', 'Jane Smith', False))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result is not None, "Insert should return a result"
        assert result['vgcpid'] == 'VGCP-001'
        assert result['description'] == 'Test Control'
        assert result['control_owner'] == 'John Doe'
        assert result['control_sme'] == 'Jane Smith'
        assert result['escalation'] == False
        assert result['is_active'] == True
        cursor.close()

    def test_get_control_by_vgcpid(self, db_conn):
        """Test SELECT - Get control by vgcpid"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create a control first
        insert_sql = """INSERT INTO controls (vgcpid, description, control_owner, control_sme)
                        VALUES (%s, %s, %s, %s)
                        RETURNING *"""
        cursor.execute(insert_sql, ('VGCP-002', 'Another Control', 'Owner', 'SME'))
        db_conn.commit()
        
        # Now retrieve it
        select_sql = "SELECT * FROM controls WHERE vgcpid = %s"
        cursor.execute(select_sql, ('VGCP-002',))
        result = cursor.fetchone()
        
        assert result is not None, "Should retrieve the control"
        assert result['vgcpid'] == 'VGCP-002'
        assert result['description'] == 'Another Control'
        
        cursor.close()

    def test_get_all_active_controls(self, db_conn):
        """Test SELECT - Get all active controls"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Insert multiple controls
        for i in range(3):
            sql = """INSERT INTO controls (vgcpid, description, control_owner, control_sme)
                     VALUES (%s, %s, %s, %s)"""
            cursor.execute(sql, (f'VGCP-{i}', f'Control {i}', 'Owner', 'SME'))
        db_conn.commit()
        
        # Retrieve all active controls
        sql = "SELECT * FROM controls WHERE is_active = TRUE"
        cursor.execute(sql)
        results = cursor.fetchall()
        
        assert len(results) == 3, "Should retrieve all 3 controls"
        
        cursor.close()

    def test_update_control(self, db_conn):
        """Test UPDATE - Modify a control"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create a control
        insert_sql = """INSERT INTO controls (vgcpid, description, control_owner, control_sme)
                        VALUES (%s, %s, %s, %s)"""
        cursor.execute(insert_sql, ('VGCP-003', 'Original', 'Owner1', 'SME1'))
        db_conn.commit()
        
        # Update it
        update_sql = """UPDATE controls
                        SET description = %s, control_owner = %s, control_sme = %s, escalation = %s, last_tested = %s
                        WHERE vgcpid = %s
                        RETURNING *"""
        cursor.execute(update_sql, ('Updated Description', 'Owner2', 'SME2', True, '2026-01-15', 'VGCP-003'))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result['description'] == 'Updated Description'
        assert result['control_owner'] == 'Owner2'
        
        cursor.close()

    def test_deactivate_control(self, db_conn):
        """Test UPDATE - Deactivate a control"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create a control
        insert_sql = """INSERT INTO controls (vgcpid, description, control_owner, control_sme)
                        VALUES (%s, %s, %s, %s)"""
        cursor.execute(insert_sql, ('VGCP-004', 'To Deactivate', 'Owner', 'SME'))
        db_conn.commit()
        
        # Deactivate it
        deactivate_sql = "UPDATE controls SET is_active = FALSE WHERE vgcpid = %s RETURNING *"
        cursor.execute(deactivate_sql, ('VGCP-004',))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result['is_active'] == False
        
        cursor.close()

    def test_delete_control(self, db_conn):
        """Test DELETE - Delete a control by vgcpid"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create a control
        insert_sql = """INSERT INTO controls (vgcpid, description, control_owner, control_sme)
                        VALUES (%s, %s, %s, %s)"""
        cursor.execute(insert_sql, ('VGCP-DELETE', 'To Delete', 'Owner', 'SME'))
        db_conn.commit()
        
        # Delete it
        delete_sql = "DELETE FROM controls WHERE vgcpid = %s RETURNING *"
        cursor.execute(delete_sql, ('VGCP-DELETE',))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result is not None
        assert result['vgcpid'] == 'VGCP-DELETE'
        
        # Verify it's gone
        verify_sql = "SELECT * FROM controls WHERE vgcpid = %s"
        cursor.execute(verify_sql, ('VGCP-DELETE',))
        verify_result = cursor.fetchone()
        assert verify_result is None
        
        cursor.close()


class TestRequestsDML:
    """Test DML queries for requests table"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, db_conn):
        """Setup and teardown for each test"""
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM tests;")
        cursor.execute("DELETE FROM requests;")
        cursor.execute("DELETE FROM users;")
        db_conn.commit()
        cursor.close()
        yield
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM tests;")
        cursor.execute("DELETE FROM requests;")
        cursor.execute("DELETE FROM users;")
        db_conn.commit()
        cursor.close()

    def test_create_request(self, db_conn):
        """Test INSERT - Create a new request"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create a user first for created_by
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('user@test.com', 'MANAGER', 'Test User'))
        user_id = cursor.fetchone()['user_id']
        db_conn.commit()
        
        sql = """INSERT INTO requests (requestor, start_date, due_date, status, created_by)
                 VALUES (%s, %s, %s, %s, %s)
                 RETURNING *"""
        
        start_date = datetime.now().date()
        due_date = start_date + timedelta(days=350)
        cursor.execute(sql, ('John Requestor', start_date, due_date, 'NOT_STARTED', user_id))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result is not None
        assert result['requestor'] == 'John Requestor'
        assert result['status'] == 'NOT_STARTED'
        assert result['start_date'] == start_date
        
        cursor.close()

    def test_get_all_requests(self, db_conn):
        """Test SELECT - Get all requests"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create a user first for created_by
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('user@test.com', 'MANAGER', 'Test User'))
        user_id = cursor.fetchone()['user_id']
        db_conn.commit()
        
        # Insert requests
        for i in range(2):
            sql = "INSERT INTO requests (requestor, start_date, due_date, status, created_by) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (f'Requestor {i}', '2026-01-15', '2026-12-31', 'NOT_STARTED', user_id))
        db_conn.commit()
        
        # Retrieve all
        sql = "SELECT * FROM requests ORDER BY created_at DESC"
        cursor.execute(sql)
        results = cursor.fetchall()
        
        assert len(results) == 2
        
        cursor.close()

    def test_update_request_status(self, db_conn):
        """Test UPDATE - Change request status"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create a user first for created_by
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('user@test.com', 'MANAGER', 'Test User'))
        user_id = cursor.fetchone()['user_id']
        db_conn.commit()
        
        # Create a request
        insert_sql = "INSERT INTO requests (requestor, start_date, due_date, status, created_by) VALUES (%s, %s, %s, %s, %s) RETURNING request_id"
        cursor.execute(insert_sql, ('Requestor', '2026-01-15', '2026-12-31', 'NOT_STARTED', user_id))
        request_id = cursor.fetchone()['request_id']
        db_conn.commit()
        
        # Update status
        update_sql = "UPDATE requests SET status = %s WHERE request_id = %s RETURNING *"
        cursor.execute(update_sql, ('IN_PROGRESS', request_id))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result['status'] == 'IN_PROGRESS'
        
        cursor.close()

    def test_get_request_by_id(self, db_conn):
        """Test SELECT - Get request by request_id"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create a user first for created_by
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('user@test.com', 'MANAGER', 'Test User'))
        user_id = cursor.fetchone()['user_id']
        db_conn.commit()
        
        # Create a request
        insert_sql = "INSERT INTO requests (requestor, start_date, due_date, status, created_by) VALUES (%s, %s, %s, %s, %s) RETURNING request_id"
        cursor.execute(insert_sql, ('Get Request', '2026-01-15', '2026-12-31', 'NOT_STARTED', user_id))
        request_id = cursor.fetchone()['request_id']
        db_conn.commit()
        
        # Retrieve it
        select_sql = "SELECT * FROM requests WHERE request_id = %s"
        cursor.execute(select_sql, (request_id,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result['requestor'] == 'Get Request'
        assert result['request_id'] == request_id
        
        cursor.close()


class TestTestsDML:
    """Test DML queries for tests table"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, db_conn):
        """Setup and teardown for each test"""
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM comments;")
        cursor.execute("DELETE FROM tests;")
        cursor.execute("DELETE FROM requests;")
        cursor.execute("DELETE FROM controls;")
        cursor.execute("DELETE FROM users;")
        db_conn.commit()
        cursor.close()
        yield
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM comments;")
        cursor.execute("DELETE FROM tests;")
        cursor.execute("DELETE FROM requests;")
        cursor.execute("DELETE FROM controls;")
        cursor.execute("DELETE FROM users;")
        db_conn.commit()
        cursor.close()

    def test_create_test(self, db_conn):
        """Test INSERT - Create a new test"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create a user for assigned_tester_id
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('tester@test.com', 'TESTER', 'Test Tester'))
        tester_id = cursor.fetchone()['user_id']
        
        # Create control and request first
        cursor.execute("INSERT INTO controls (vgcpid, control_owner, control_sme) VALUES (%s, %s, %s) RETURNING control_id", ('VGCP-T1', 'Owner', 'SME'))
        control_id = cursor.fetchone()['control_id']
        
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('user@test.com', 'MANAGER', 'User'))
        user_id = cursor.fetchone()['user_id']
        
        cursor.execute("INSERT INTO requests (requestor, start_date, due_date, status, created_by) VALUES (%s, %s, %s, %s, %s) RETURNING request_id", ('Req', '2026-01-15', '2026-12-31', 'NOT_STARTED', user_id))
        request_id = cursor.fetchone()['request_id']
        db_conn.commit()
        
        # Create test
        sql = """INSERT INTO tests (request_id, control_id, requires_dat, requires_oet, assigned_tester_id, status)
                 VALUES (%s, %s, %s, %s, %s, %s)
                 RETURNING *"""
        cursor.execute(sql, (request_id, control_id, True, False, tester_id, 'NOT_STARTED'))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result is not None
        assert result['requires_dat'] == True
        assert result['requires_oet'] == False
        
        cursor.close()

    def test_update_test_status(self, db_conn):
        """Test UPDATE - Change test status"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create test prerequisites
        cursor.execute("INSERT INTO controls (vgcpid, control_owner, control_sme) VALUES (%s, %s, %s) RETURNING control_id", ('VGCP-T2', 'Owner', 'SME'))
        control_id = cursor.fetchone()['control_id']
        
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('user2@test.com', 'MANAGER', 'User2'))
        user_id = cursor.fetchone()['user_id']
        
        cursor.execute("INSERT INTO requests (requestor, start_date, due_date, status, created_by) VALUES (%s, %s, %s, %s, %s) RETURNING request_id", ('Req', '2026-01-15', '2026-12-31', 'NOT_STARTED', user_id))
        request_id = cursor.fetchone()['request_id']
        
        cursor.execute("INSERT INTO tests (request_id, control_id, requires_dat, requires_oet, status) VALUES (%s, %s, %s, %s, %s) RETURNING test_id", (request_id, control_id, True, False, 'NOT_STARTED'))
        test_id = cursor.fetchone()['test_id']
        db_conn.commit()
        
        # Update status - test IN_PROGRESS
        sql = "UPDATE tests SET dat_step = %s, status = %s, updated_at = now() WHERE test_id = %s RETURNING *"
        cursor.execute(sql, ('TESTING_IN_PROGRESS', 'IN_PROGRESS', test_id))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result['status'] == 'IN_PROGRESS'
        
        cursor.close()

    def test_get_tests_by_request_id(self, db_conn):
        """Test SELECT - Get tests by request_id"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Setup
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('user@test.com', 'MANAGER', 'User'))
        user_id = cursor.fetchone()['user_id']
        
        cursor.execute("INSERT INTO requests (requestor, start_date, due_date, status, created_by) VALUES (%s, %s, %s, %s, %s) RETURNING request_id", ('Req', '2026-01-15', '2026-12-31', 'NOT_STARTED', user_id))
        request_id = cursor.fetchone()['request_id']
        
        # Create multiple controls for multiple tests
        for i in range(2):
            cursor.execute("INSERT INTO controls (vgcpid, control_owner) VALUES (%s, %s) RETURNING control_id", (f'VGCP-GR{i}', 'Owner'))
            control_id = cursor.fetchone()['control_id']
            # Create test with same request but different control
            cursor.execute("INSERT INTO tests (request_id, control_id, requires_dat, requires_oet, status) VALUES (%s, %s, %s, %s, %s)", (request_id, control_id, True, False, 'NOT_STARTED'))
        db_conn.commit()
        
        # Retrieve tests
        cursor.execute("SELECT * FROM tests WHERE request_id = %s", (request_id,))
        results = cursor.fetchall()
        
        assert len(results) == 2
        assert all(r['request_id'] == request_id for r in results)
        
        cursor.close()

    def test_get_tests_by_control_id(self, db_conn):
        """Test SELECT - Get tests by control_id"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Setup
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('user@test.com', 'MANAGER', 'User'))
        user_id = cursor.fetchone()['user_id']
        
        cursor.execute("INSERT INTO controls (vgcpid, control_owner) VALUES (%s, %s) RETURNING control_id", ('VGCP-GC1', 'Owner'))
        control_id = cursor.fetchone()['control_id']
        
        # Create multiple requests for multiple tests
        for i in range(2):
            cursor.execute("INSERT INTO requests (requestor, start_date, due_date, status, created_by) VALUES (%s, %s, %s, %s, %s) RETURNING request_id", (f'Req{i}', '2026-01-15', '2026-12-31', 'NOT_STARTED', user_id))
            request_id = cursor.fetchone()['request_id']
            # Create test with same control but different request
            cursor.execute("INSERT INTO tests (request_id, control_id, requires_dat, requires_oet, status) VALUES (%s, %s, %s, %s, %s)", (request_id, control_id, True, False, 'NOT_STARTED'))
        db_conn.commit()
        
        # Retrieve tests
        cursor.execute("SELECT * FROM tests WHERE control_id = %s", (control_id,))
        results = cursor.fetchall()
        
        assert len(results) == 2
        assert all(r['control_id'] == control_id for r in results)
        
        cursor.close()

    def test_get_test_by_id(self, db_conn):
        """Test SELECT - Get test by test_id"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Setup
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('user@test.com', 'MANAGER', 'User'))
        user_id = cursor.fetchone()['user_id']
        
        cursor.execute("INSERT INTO controls (vgcpid, control_owner) VALUES (%s, %s) RETURNING control_id", ('VGCP-GT1', 'Owner'))
        control_id = cursor.fetchone()['control_id']
        
        cursor.execute("INSERT INTO requests (requestor, start_date, due_date, status, created_by) VALUES (%s, %s, %s, %s, %s) RETURNING request_id", ('Req', '2026-01-15', '2026-12-31', 'NOT_STARTED', user_id))
        request_id = cursor.fetchone()['request_id']
        
        cursor.execute("INSERT INTO tests (request_id, control_id, requires_dat, requires_oet, status) VALUES (%s, %s, %s, %s, %s) RETURNING test_id", (request_id, control_id, True, False, 'NOT_STARTED'))
        test_id = cursor.fetchone()['test_id']
        db_conn.commit()
        
        # Retrieve it
        cursor.execute("SELECT * FROM tests WHERE test_id = %s", (test_id,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result['test_id'] == test_id
        
        cursor.close()

    def test_update_test_status_in_progress(self, db_conn):
        """Test UPDATE - Set test status to IN_PROGRESS"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Setup
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('user@test.com', 'MANAGER', 'User'))
        user_id = cursor.fetchone()['user_id']
        
        cursor.execute("INSERT INTO controls (vgcpid, control_owner) VALUES (%s, %s) RETURNING control_id", ('VGCP-IP1', 'Owner'))
        control_id = cursor.fetchone()['control_id']
        
        cursor.execute("INSERT INTO requests (requestor, start_date, due_date, status, created_by) VALUES (%s, %s, %s, %s, %s) RETURNING request_id", ('Req', '2026-01-15', '2026-12-31', 'NOT_STARTED', user_id))
        request_id = cursor.fetchone()['request_id']
        
        cursor.execute("INSERT INTO tests (request_id, control_id, requires_dat, requires_oet, status) VALUES (%s, %s, %s, %s, %s) RETURNING test_id", (request_id, control_id, True, False, 'NOT_STARTED'))
        test_id = cursor.fetchone()['test_id']
        db_conn.commit()
        
        # Update to IN_PROGRESS
        cursor.execute("UPDATE tests SET status = %s, start_date = current_date, updated_at = now() WHERE test_id = %s RETURNING *", ('IN_PROGRESS', test_id))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result['status'] == 'IN_PROGRESS'
        assert result['start_date'] is not None
        
        cursor.close()

    def test_update_test_status_in_review(self, db_conn):
        """Test UPDATE - Set test status to IN_REVIEW"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Setup
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('user@test.com', 'MANAGER', 'User'))
        user_id = cursor.fetchone()['user_id']
        
        cursor.execute("INSERT INTO controls (vgcpid, control_owner) VALUES (%s, %s) RETURNING control_id", ('VGCP-IR1', 'Owner'))
        control_id = cursor.fetchone()['control_id']
        
        cursor.execute("INSERT INTO requests (requestor, start_date, due_date, status, created_by) VALUES (%s, %s, %s, %s, %s) RETURNING request_id", ('Req', '2026-01-15', '2026-12-31', 'NOT_STARTED', user_id))
        request_id = cursor.fetchone()['request_id']
        
        cursor.execute("INSERT INTO tests (request_id, control_id, requires_dat, requires_oet, status) VALUES (%s, %s, %s, %s, %s) RETURNING test_id", (request_id, control_id, True, False, 'NOT_STARTED'))
        test_id = cursor.fetchone()['test_id']
        db_conn.commit()
        
        # Update to IN_REVIEW
        cursor.execute("UPDATE tests SET status = %s, complete_date = current_date, updated_at = now() WHERE test_id = %s RETURNING *", ('IN_REVIEW', test_id))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result['status'] == 'IN_REVIEW'
        assert result['complete_date'] is not None
        
        cursor.close()

    def test_update_test_status_completed(self, db_conn):
        """Test UPDATE - Set test status to COMPLETED"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Setup
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('user@test.com', 'MANAGER', 'User'))
        user_id = cursor.fetchone()['user_id']
        
        cursor.execute("INSERT INTO controls (vgcpid, control_owner) VALUES (%s, %s) RETURNING control_id", ('VGCP-COM1', 'Owner'))
        control_id = cursor.fetchone()['control_id']
        
        cursor.execute("INSERT INTO requests (requestor, start_date, due_date, status, created_by) VALUES (%s, %s, %s, %s, %s) RETURNING request_id", ('Req', '2026-01-15', '2026-12-31', 'NOT_STARTED', user_id))
        request_id = cursor.fetchone()['request_id']
        
        cursor.execute("INSERT INTO tests (request_id, control_id, requires_dat, requires_oet, status) VALUES (%s, %s, %s, %s, %s) RETURNING test_id", (request_id, control_id, True, False, 'NOT_STARTED'))
        test_id = cursor.fetchone()['test_id']
        db_conn.commit()
        
        # Update to COMPLETED
        cursor.execute("UPDATE tests SET status = %s, complete_date = current_date, updated_at = now() WHERE test_id = %s RETURNING *", ('COMPLETED', test_id))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result['status'] == 'COMPLETED'
        assert result['complete_date'] is not None
        
        cursor.close()


class TestCommentsDML:
    """Test DML queries for comments table"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, db_conn):
        """Setup and teardown for each test"""
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM audit_logs;")
        cursor.execute("DELETE FROM comments;")
        cursor.execute("DELETE FROM tests;")
        cursor.execute("DELETE FROM requests;")
        cursor.execute("DELETE FROM controls;")
        cursor.execute("DELETE FROM users;")
        db_conn.commit()
        cursor.close()
        yield
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM audit_logs;")
        cursor.execute("DELETE FROM comments;")
        cursor.execute("DELETE FROM tests;")
        cursor.execute("DELETE FROM requests;")
        cursor.execute("DELETE FROM controls;")
        cursor.execute("DELETE FROM users;")
        db_conn.commit()
        cursor.close()

    def test_add_comment_to_test(self, db_conn):
        """Test INSERT - Add comment to test"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Setup prerequisites
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('user1@test.com', 'MANAGER', 'User One'))
        user_id = cursor.fetchone()['user_id']
        
        cursor.execute("INSERT INTO controls (vgcpid, control_owner, control_sme) VALUES (%s, %s, %s) RETURNING control_id", ('VGCP-C1', 'Owner', 'SME'))
        control_id = cursor.fetchone()['control_id']
        
        cursor.execute("INSERT INTO requests (requestor, start_date, due_date, status, created_by) VALUES (%s, %s, %s, %s, %s) RETURNING request_id", ('Req', '2026-01-15', '2026-12-31', 'NOT_STARTED', user_id))
        request_id = cursor.fetchone()['request_id']
        
        cursor.execute("INSERT INTO tests (request_id, control_id, requires_dat, requires_oet, status) VALUES (%s, %s, %s, %s, %s) RETURNING test_id", (request_id, control_id, True, False, 'NOT_STARTED'))
        test_id = cursor.fetchone()['test_id']
        db_conn.commit()
        
        # Add comment
        sql = """INSERT INTO comments (author_user_id, test_id, comment_text)
                 VALUES (%s, %s, %s)
                 RETURNING *"""
        cursor.execute(sql, (user_id, test_id, 'This is a test comment'))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result['comment_text'] == 'This is a test comment'
        assert result['test_id'] == test_id
        
        cursor.close()

    def test_get_comments_for_test(self, db_conn):
        """Test SELECT - Get all comments for a test"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Setup
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('user2@test.com', 'TESTER', 'User Two'))
        user_id = cursor.fetchone()['user_id']
        
        cursor.execute("INSERT INTO controls (vgcpid, control_owner, control_sme) VALUES (%s, %s, %s) RETURNING control_id", ('VGCP-C2', 'Owner', 'SME'))
        control_id = cursor.fetchone()['control_id']
        
        cursor.execute("INSERT INTO requests (requestor, start_date, due_date, status, created_by) VALUES (%s, %s, %s, %s, %s) RETURNING request_id", ('Req', '2026-01-15', '2026-12-31', 'NOT_STARTED', user_id))
        request_id = cursor.fetchone()['request_id']
        
        cursor.execute("INSERT INTO tests (request_id, control_id, requires_dat, requires_oet, status) VALUES (%s, %s, %s, %s, %s) RETURNING test_id", (request_id, control_id, True, False, 'NOT_STARTED'))
        test_id = cursor.fetchone()['test_id']
        db_conn.commit()
        
        # Add multiple comments
        for i in range(3):
            cursor.execute("INSERT INTO comments (author_user_id, test_id, comment_text) VALUES (%s, %s, %s)", (user_id, test_id, f'Comment {i}'))
        db_conn.commit()
        
        # Retrieve comments
        sql = "SELECT * FROM comments WHERE test_id = %s ORDER BY posted_at DESC"
        cursor.execute(sql, (test_id,))
        results = cursor.fetchall()
        
        assert len(results) == 3
        
        cursor.close()

    def test_get_audit_trail_by_actor(self, db_conn):
        """Test SELECT - Get audit trail by actor"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create user
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('auditor@test.com', 'MANAGER', 'Auditor'))
        user_id = cursor.fetchone()['user_id']
        db_conn.commit()
        
        # Log multiple actions by this actor
        for action in ['CREATE', 'UPDATE', 'DELETE']:
            cursor.execute("""INSERT INTO audit_logs (actor_user_id, entity_type, entity_id, action)
                              VALUES (%s, %s, %s, %s)""", (user_id, 'CONTROL', 10, action))
        db_conn.commit()
        
        # Retrieve audit trail by actor
        cursor.execute("SELECT * FROM audit_logs WHERE actor_user_id = %s ORDER BY changed_at DESC", (user_id,))
        results = cursor.fetchall()
        
        assert len(results) == 3
        assert all(r['actor_user_id'] == user_id for r in results)
        
        cursor.close()

    def test_get_all_audit_logs(self, db_conn):
        """Test SELECT - Get all audit logs"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create user
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('auditor2@test.com', 'MANAGER', 'Auditor2'))
        user_id = cursor.fetchone()['user_id']
        db_conn.commit()
        
        # Log some actions
        for i in range(2):
            cursor.execute("""INSERT INTO audit_logs (actor_user_id, entity_type, entity_id, action)
                              VALUES (%s, %s, %s, %s)""", (user_id, 'TEST', i, 'CREATE'))
        db_conn.commit()
        
        # Retrieve all audit logs
        cursor.execute("SELECT * FROM audit_logs ORDER BY changed_at DESC")
        results = cursor.fetchall()
        
        assert len(results) >= 2
        
        cursor.close()


class TestUsersDML:
    """Test DML queries for users table"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, db_conn):
        """Setup and teardown for each test"""
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM audit_logs;")
        cursor.execute("DELETE FROM users;")
        db_conn.commit()
        cursor.close()
        yield
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM audit_logs;")
        cursor.execute("DELETE FROM users;")
        db_conn.commit()
        cursor.close()

    def test_get_user_by_id(self, db_conn):
        """Test SELECT - Get user by user_id"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create a user
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('test@example.com', 'MANAGER', 'Test User'))
        user_id = cursor.fetchone()['user_id']
        db_conn.commit()
        
        # Retrieve it
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result['email'] == 'test@example.com'
        assert result['role'] == 'MANAGER'
        
        cursor.close()

    def test_get_user_by_email(self, db_conn):
        """Test SELECT - Get user by email"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create a user
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s)", ('user@test.com', 'TESTER', 'User'))
        db_conn.commit()
        
        # Retrieve by email
        cursor.execute("SELECT * FROM users WHERE email = %s", ('user@test.com',))
        result = cursor.fetchone()
        
        assert result is not None
        assert result['email'] == 'user@test.com'
        assert result['role'] == 'TESTER'
        
        cursor.close()

    def test_get_all_active_users(self, db_conn):
        """Test SELECT - Get all active users"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create multiple active users
        for i in range(3):
            cursor.execute("INSERT INTO users (email, role, display_name, is_active) VALUES (%s, %s, %s, %s)", (f'user{i}@test.com', 'MANAGER', f'User {i}', True))
        
        # Create one inactive user
        cursor.execute("INSERT INTO users (email, role, display_name, is_active) VALUES (%s, %s, %s, %s)", ('inactive@test.com', 'TESTER', 'Inactive User', False))
        db_conn.commit()
        
        # Retrieve active users
        cursor.execute("SELECT * FROM users WHERE is_active = TRUE")
        results = cursor.fetchall()
        
        assert len(results) == 3
        assert all(r['is_active'] == True for r in results)
        
        cursor.close()

    def test_create_user(self, db_conn):
        """Test INSERT - Create a user"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        sql = """INSERT INTO users (email, role, display_name, is_active)
                 VALUES (%s, %s, %s, TRUE)
                 RETURNING *"""
        
        cursor.execute(sql, ('newuser@test.com', 'MANAGER', 'New User'))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result is not None
        assert result['email'] == 'newuser@test.com'
        assert result['role'] == 'MANAGER'
        assert result['is_active'] == True
        
        cursor.close()

    def test_update_user(self, db_conn):
        """Test UPDATE - Update user"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create a user
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('update@test.com', 'TESTER', 'Original'))
        user_id = cursor.fetchone()['user_id']
        db_conn.commit()
        
        # Update the user
        cursor.execute("UPDATE users SET display_name = %s, role = %s WHERE user_id = %s RETURNING *", ('Updated User', 'MANAGER', user_id))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result['display_name'] == 'Updated User'
        assert result['role'] == 'MANAGER'
        
        # Log an audit action
        sql = """INSERT INTO audit_logs (actor_user_id, entity_type, entity_id, action, before_snapshot, after_snapshot, reason)
                 VALUES (%s, %s, %s, %s, %s, %s, %s)
                 RETURNING *"""
        
        before = json.dumps({'status': 'ACTIVE'})
        after = json.dumps({'status': 'INACTIVE'})
        
        cursor.execute(sql, (user_id, 'CONTROL', 1, 'UPDATE', before, after, 'Control deactivated'))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result is not None
        assert result['entity_type'] == 'CONTROL'
        assert result['action'] == 'UPDATE'
        
        cursor.close()

    def test_get_audit_trail_for_entity(self, db_conn):
        """Test SELECT - Get audit trail for an entity"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create user
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('auditor2@test.com', 'MANAGER', 'Auditor2'))
        user_id = cursor.fetchone()['user_id']
        db_conn.commit()
        
        # Log multiple actions
        for action in ['CREATE', 'UPDATE', 'UPDATE']:
            cursor.execute("""INSERT INTO audit_logs (actor_user_id, entity_type, entity_id, action)
                              VALUES (%s, %s, %s, %s)""", (user_id, 'REQUEST', 5, action))
        db_conn.commit()
        
        # Retrieve audit trail
        sql = "SELECT * FROM audit_logs WHERE entity_type = %s AND entity_id = %s ORDER BY changed_at DESC"
        cursor.execute(sql, ('REQUEST', 5))
        results = cursor.fetchall()
        
        assert len(results) == 3
        
        cursor.close()
