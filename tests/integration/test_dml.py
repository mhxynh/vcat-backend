import pytest
import json
from psycopg2.extras import RealDictCursor


class TestControlsDML:
    """Test DML queries for controls table"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, db_conn):
        """Setup and teardown for each test"""
        cursor = db_conn.cursor()
        # Clear dependents before controls to satisfy FKs
        cursor.execute("DELETE FROM comments CASCADE;")
        cursor.execute("DELETE FROM tests CASCADE;")
        cursor.execute("DELETE FROM controls;")
        db_conn.commit()
        cursor.close()
        yield
        # Cleanup after test
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM comments CASCADE;")
        cursor.execute("DELETE FROM tests CASCADE;")
        cursor.execute("DELETE FROM controls;")
        db_conn.commit()
        cursor.close()

    def test_create_control(self, db_conn):
        """Test INSERT - Create a new control"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        sql = """INSERT INTO controls (vgcpid, description, control_owner, control_sme, escalation)
                 VALUES (%s, %s, %s, %s, %s)
                 RETURNING *"""
        
        cursor.execute(sql, ('VGCP-001', 'Test Control', 'John Doe', 'Jane Smith', False))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result is not None, "Insert should return a result"
        assert result['vgcpid'] == 'VGCP-001'
        assert result['description'] == 'Test Control'
        assert result['control_owner'] == 'John Doe'
        
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
                        SET description = %s, control_owner = %s 
                        WHERE vgcpid = %s
                        RETURNING *"""
        cursor.execute(update_sql, ('Updated Description', 'Owner2', 'VGCP-003'))
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


class TestRequestsDML:
    """Test DML queries for requests table"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, db_conn):
        """Setup and teardown for each test"""
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM tests CASCADE;")
        cursor.execute("DELETE FROM requests CASCADE;")
        db_conn.commit()
        cursor.close()
        yield
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM tests CASCADE;")
        cursor.execute("DELETE FROM requests CASCADE;")
        db_conn.commit()
        cursor.close()

    def test_create_request(self, db_conn):
        """Test INSERT - Create a new request"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        sql = """INSERT INTO requests (requestor, due_date, status)
                 VALUES (%s, %s, %s)
                 RETURNING *"""
        
        cursor.execute(sql, ('John Requestor', '2026-12-31', 'NOT_STARTED'))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result is not None
        assert result['requestor'] == 'John Requestor'
        assert result['status'] == 'NOT_STARTED'
        
        cursor.close()

    def test_get_all_requests(self, db_conn):
        """Test SELECT - Get all requests"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Insert requests
        for i in range(2):
            sql = "INSERT INTO requests (requestor, due_date, status) VALUES (%s, %s, %s)"
            cursor.execute(sql, (f'Requestor {i}', '2026-12-31', 'NOT_STARTED'))
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
        
        # Create a request
        insert_sql = "INSERT INTO requests (requestor, due_date, status) VALUES (%s, %s, %s) RETURNING request_id"
        cursor.execute(insert_sql, ('Requestor', '2026-12-31', 'NOT_STARTED'))
        request_id = cursor.fetchone()['request_id']
        db_conn.commit()
        
        # Update status
        update_sql = "UPDATE requests SET status = %s WHERE request_id = %s RETURNING *"
        cursor.execute(update_sql, ('IN_PROGRESS', request_id))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result['status'] == 'IN_PROGRESS'
        
        cursor.close()


class TestTestsDML:
    """Test DML queries for tests table"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, db_conn):
        """Setup and teardown for each test"""
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM comments CASCADE;")
        cursor.execute("DELETE FROM tests CASCADE;")
        cursor.execute("DELETE FROM requests CASCADE;")
        cursor.execute("DELETE FROM controls CASCADE;")
        db_conn.commit()
        cursor.close()
        yield
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM comments CASCADE;")
        cursor.execute("DELETE FROM tests CASCADE;")
        cursor.execute("DELETE FROM requests CASCADE;")
        cursor.execute("DELETE FROM controls CASCADE;")
        db_conn.commit()
        cursor.close()

    def test_create_test(self, db_conn):
        """Test INSERT - Create a new test"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create control and request first
        cursor.execute("INSERT INTO controls (vgcpid, control_owner, control_sme) VALUES (%s, %s, %s) RETURNING control_id", ('VGCP-T1', 'Owner', 'SME'))
        control_id = cursor.fetchone()['control_id']
        
        cursor.execute("INSERT INTO requests (requestor, due_date, status) VALUES (%s, %s, %s) RETURNING request_id", ('Req', '2026-12-31', 'NOT_STARTED'))
        request_id = cursor.fetchone()['request_id']
        
        # Create test
        sql = """INSERT INTO tests (request_id, control_id, test_type, status)
                 VALUES (%s, %s, %s, %s)
                 RETURNING *"""
        cursor.execute(sql, (request_id, control_id, 'DAT', 'NOT_STARTED'))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result is not None
        assert result['test_type'] == 'DAT'
        
        cursor.close()

    def test_update_test_status(self, db_conn):
        """Test UPDATE - Change test status"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create test prerequisites
        cursor.execute("INSERT INTO controls (vgcpid, control_owner, control_sme) VALUES (%s, %s, %s) RETURNING control_id", ('VGCP-T2', 'Owner', 'SME'))
        control_id = cursor.fetchone()['control_id']
        
        cursor.execute("INSERT INTO requests (requestor, due_date, status) VALUES (%s, %s, %s) RETURNING request_id", ('Req', '2026-12-31', 'NOT_STARTED'))
        request_id = cursor.fetchone()['request_id']
        
        cursor.execute("INSERT INTO tests (request_id, control_id, test_type, status) VALUES (%s, %s, %s, %s) RETURNING test_id", (request_id, control_id, 'DAT', 'NOT_STARTED'))
        test_id = cursor.fetchone()['test_id']
        db_conn.commit()
        
        # Update status
        sql = "UPDATE tests SET status = %s WHERE test_id = %s RETURNING *"
        cursor.execute(sql, ('IN_PROGRESS', test_id))
        result = cursor.fetchone()
        db_conn.commit()
        
        assert result['status'] == 'IN_PROGRESS'
        
        cursor.close()


class TestCommentsDML:
    """Test DML queries for comments table"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, db_conn):
        """Setup and teardown for each test"""
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM comments CASCADE;")
        cursor.execute("DELETE FROM tests CASCADE;")
        cursor.execute("DELETE FROM requests CASCADE;")
        cursor.execute("DELETE FROM controls CASCADE;")
        cursor.execute("DELETE FROM users CASCADE;")
        db_conn.commit()
        cursor.close()
        yield
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM comments CASCADE;")
        cursor.execute("DELETE FROM tests CASCADE;")
        cursor.execute("DELETE FROM requests CASCADE;")
        cursor.execute("DELETE FROM controls CASCADE;")
        cursor.execute("DELETE FROM users CASCADE;")
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
        
        cursor.execute("INSERT INTO requests (requestor, due_date, status) VALUES (%s, %s, %s) RETURNING request_id", ('Req', '2026-12-31', 'NOT_STARTED'))
        request_id = cursor.fetchone()['request_id']
        
        cursor.execute("INSERT INTO tests (request_id, control_id, test_type, status) VALUES (%s, %s, %s, %s) RETURNING test_id", (request_id, control_id, 'DAT', 'NOT_STARTED'))
        test_id = cursor.fetchone()['test_id']
        
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
        
        cursor.execute("INSERT INTO requests (requestor, due_date, status) VALUES (%s, %s, %s) RETURNING request_id", ('Req', '2026-12-31', 'NOT_STARTED'))
        request_id = cursor.fetchone()['request_id']
        
        cursor.execute("INSERT INTO tests (request_id, control_id, test_type, status) VALUES (%s, %s, %s, %s) RETURNING test_id", (request_id, control_id, 'DAT', 'NOT_STARTED'))
        test_id = cursor.fetchone()['test_id']
        
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


class TestAuditLogsDML:
    """Test DML queries for audit_logs table"""

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

    def test_log_audit_action(self, db_conn):
        """Test INSERT - Log an audit action"""
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Create a user to act as the auditor
        cursor.execute("INSERT INTO users (email, role, display_name) VALUES (%s, %s, %s) RETURNING user_id", ('auditor@test.com', 'MANAGER', 'Auditor'))
        user_id = cursor.fetchone()['user_id']
        db_conn.commit()
        
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
