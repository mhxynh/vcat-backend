-- Data Manipulation Language (DML) file for VCATS
-- Contains SELECT, INSERT, UPDATE, and DELETE queries for the database
---------- CONTROLS QUERIES ----------
-- Get control by vgcpid
SELECT *
FROM controls
WHERE vgcpid = %s;
-- Get all controls
SELECT *
FROM controls
WHERE is_active = TRUE;
-- Get control by control_id
SELECT *
FROM controls
WHERE control_id = %s;
-- Create control
INSERT INTO controls (
        vgcpid,
        description,
        control_owner,
        control_sme,
        escalation,
        is_active
    )
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
UPDATE controls
SET is_active = FALSE
WHERE vgcpid = %s
RETURNING *;
-- Delete control by vgcpid
DELETE FROM controls
WHERE vgcpid = %s
RETURNING *;
---------- REQUESTS QUERIES ----------
-- Get all requests
SELECT *
FROM requests
ORDER BY created_at DESC;
-- Get request by request_id
SELECT *
FROM requests
WHERE request_id = %s;
-- Create request
INSERT INTO requests (
        requestor,
        start_date,
        due_date,
        status,
        created_by
    )
VALUES (%s, %s, %s, %s, %s)
RETURNING *;
-- Update request status
UPDATE requests
SET status = %s
WHERE request_id = %s
RETURNING *;
-- Soft delete request by request_id
UPDATE requests
SET test_status = 'ARCHIVED'
WHERE request_id = %s
RETURNING *;
-- Hard delete request by request_id
DELETE FROM requests
WHERE request_id = %s
RETURNING *;
---------- TESTS QUERIES ----------
-- Get tests by request_id
SELECT *
FROM tests
WHERE request_id = %s;
-- Get tests by request_id WITH Control Details
SELECT t.*,
    c.vgcpid,
    c.description AS control_description,
    u.display_name AS tester_name
FROM tests t
    JOIN controls c ON t.control_id = c.control_id
    LEFT JOIN users u ON t.assigned_tester_id = u.user_id
WHERE t.request_id = %s;
-- Get tests by control_id
SELECT *
FROM tests
WHERE control_id = %s;
-- Get test by test_id
SELECT *
FROM tests
WHERE test_id = %s;
-- Create test
INSERT INTO tests (
        request_id,
        control_id,
        requires_dat,
        requires_oet,
        assigned_tester_id,
        status
    )
VALUES (%s, %s, %s, %s, %s, %s)
RETURNING *;
-- Update test progress (DAT track)
UPDATE tests
SET dat_step = %s,
    status = %s
WHERE test_id = %s
RETURNING *;
-- Update test progress (OET track)
UPDATE tests
SET oet_step = %s,
    status = %s
WHERE test_id = %s
RETURNING *;
-- Update test status to IN_PROGRESS (Tester starts work / or Manager loops back)
UPDATE tests
SET status = 'IN_PROGRESS',
    start_date = COALESCE(start_date, current_date) -- Only set if it's the first time starting
WHERE test_id = %s
RETURNING *;
-- Update test status to IN_REVIEW (Tester finishes work, waits for manager)
UPDATE tests
SET status = 'IN_REVIEW'
WHERE test_id = %s
RETURNING *;
-- Update test status to COMPLETED (Manager approves)
UPDATE tests
SET status = 'COMPLETED',
    complete_date = current_date
WHERE test_id = %s
RETURNING *;
---------- COMMENTS QUERIES ----------
-- Get comments by test_id
SELECT *
FROM comments
WHERE test_id = %s
ORDER BY posted_at DESC;
-- Get comments by request_id
SELECT *
FROM comments
WHERE request_id = %s
ORDER BY posted_at DESC;
-- Create comment on test (test_id required, request_id NULL)
INSERT INTO comments (author_user_id, test_id, comment_text)
VALUES (%s, %s, %s)
RETURNING *;
-- Create comment on request (request_id required, test_id NULL)
INSERT INTO comments (author_user_id, request_id, comment_text)
VALUES (%s, %s, %s)
RETURNING *;
---------- AUDIT LOG QUERIES ----------
-- Get audit trail for entity
SELECT *
FROM audit_logs
WHERE entity_type = %s
    AND entity_id = %s
ORDER BY changed_at DESC;
-- Get audit trail by actor
SELECT *
FROM audit_logs
WHERE actor_user_id = %s
ORDER BY changed_at DESC;
-- Log audit action
INSERT INTO audit_logs (
        actor_user_id,
        entity_type,
        entity_id,
        action,
        before_snapshot,
        after_snapshot,
        reason
    )
VALUES (%s, %s, %s, %s, %s, %s, %s)
RETURNING *;
-- Get all audit logs
SELECT *
FROM audit_logs
ORDER BY changed_at DESC;
---------- USERS QUERIES ----------
-- Get user by user_id
SELECT *
FROM users
WHERE user_id = %s;
-- Get user by email
SELECT *
FROM users
WHERE email = %s;
-- Get all active users
SELECT *
FROM users
WHERE is_active = TRUE;
-- Create user
INSERT INTO users (email, role, display_name, is_active)
VALUES (%s, %s, %s, TRUE)
RETURNING *;
-- Update user
UPDATE users
SET display_name = %s,
    role = %s
WHERE user_id = %s
RETURNING *;