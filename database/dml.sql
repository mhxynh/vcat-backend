-- Data Manipulation Language (DML) file for VCATS
-- Contains SELECT, INSERT, UPDATE, and DELETE queries for the database

---------- CONTROLS QUERIES ----------

-- Get control by vgcpid
SELECT * FROM controls WHERE vgcpid = %s;

-- Get all controls
SELECT * FROM controls WHERE is_active = TRUE;

-- Get control by control_id
SELECT * FROM controls WHERE control_id = %s;

-- Create control
INSERT INTO controls (vgcpid, description, control_owner, control_sme, escalation, is_active)
VALUES (%s, %s, %s, %s, %s, TRUE)
RETURNING *;

-- Update control by vgcpid
UPDATE controls
SET description = %s,
    control_owner = %s,
    control_sme = %s,
    escalation = %s,
    last_tested = %s
WHERE vgcpid = %s
RETURNING *;

-- Update control by control_id
UPDATE controls
SET description = %s,
    control_owner = %s,
    control_sme = %s,
    escalation = %s,
    last_tested = %s
WHERE control_id = %s
RETURNING *;

-- Deactivate control by vgcpid
UPDATE controls SET is_active = FALSE WHERE vgcpid = %s RETURNING *;

-- Delete control by vgcpid
DELETE FROM controls WHERE vgcpid = %s RETURNING *;

---------- REQUESTS QUERIES ----------

-- Get all requests
SELECT * FROM requests ORDER BY created_at DESC;

-- Get request by request_id
SELECT * FROM requests WHERE request_id = %s;

-- Create request
INSERT INTO requests (requestor, start_date, due_date, status, created_by)
VALUES (%s, %s, %s, %s, %s)
RETURNING *;

-- Update request status
UPDATE requests SET status = %s, updated_at = now() WHERE request_id = %s RETURNING *;

---------- TESTS QUERIES ----------

-- Get tests by request_id
SELECT * FROM tests WHERE request_id = %s;

-- Get tests by control_id
SELECT * FROM tests WHERE control_id = %s;

-- Get test by test_id
SELECT * FROM tests WHERE test_id = %s;

-- Create test
INSERT INTO tests (request_id, control_id, test_type, assigned_tester_id, status)
VALUES (%s, %s, %s, %s, %s)
RETURNING *;

-- Update test progress
UPDATE tests 
SET in_progress_step = %s, status = %s, updated_at = now() 
WHERE test_id = %s 
RETURNING *;

-- Update test status to IN_PROGRESS
UPDATE tests
SET testing_status = 'in_progress', start_date = current_date, updated_at = now()
WHERE test_id = %s
RETURNING *;

-- Update test status to IN_REVIEW
UPDATE tests
SET testing_status = 'in_review', complete_date = current_date, updated_at = now()
WHERE test_id = %s
RETURNING *;

-- Update test status to COMPLETED
UPDATE tests
SET testing_status = 'completed', complete_date = current_date, updated_at = now()
WHERE test_id = %s
RETURNING *;

---------- COMMENTS QUERIES ----------

-- Get comments by test_id
SELECT * FROM comments WHERE test_id = %s ORDER BY posted_at DESC;

-- Get comments by request_id
SELECT * FROM comments WHERE request_id = %s ORDER BY posted_at DESC;

-- Create comment
INSERT INTO comments (author_user_id, test_id, request_id, comment_text)
VALUES (%s, %s, %s, %s)
RETURNING *;

---------- AUDIT LOG QUERIES ----------

-- Get audit trail for entity
SELECT * FROM audit_logs 
WHERE entity_type = %s AND entity_id = %s 
ORDER BY changed_at DESC;

-- Get audit trail by actor
SELECT * FROM audit_logs 
WHERE actor_user_id = %s 
ORDER BY changed_at DESC;

-- Log audit action
INSERT INTO audit_logs (actor_user_id, entity_type, entity_id, action, before_snapshot, after_snapshot, reason)
VALUES (%s, %s, %s, %s, %s, %s, %s);

-- Get all audit logs
SELECT * FROM audit_logs ORDER BY changed_at DESC;

-- Get audit logs for specific record (by entity type and id)
SELECT * FROM audit_logs 
WHERE entity_type = %s AND entity_id = %s 
ORDER BY changed_at DESC;

---------- USERS QUERIES ----------

-- Get user by user_id
SELECT * FROM users WHERE user_id = %s;

-- Get user by email
SELECT * FROM users WHERE email = %s;

-- Get all active users
SELECT * FROM users WHERE is_active = TRUE;

-- Create user
INSERT INTO users (email, role, display_name, is_active)
VALUES (%s, %s, %s, TRUE)
RETURNING *;

-- Update user
UPDATE users SET display_name = %s, role = %s WHERE user_id = %s RETURNING *;
