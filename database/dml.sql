-- Data Manipulation Language (DML) file for VCATS
-- Contains SELECT, INSERT, UPDATE, and DELETE queries for the database

---------- USERS QUERIES ----------
-- Get all users
SELECT *
FROM users
ORDER BY email;

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

-- Get all inactive users
SELECT *
FROM users
WHERE is_active = FALSE;

-- Deactivate user
UPDATE users
SET is_active = FALSE
WHERE user_id = %s
RETURNING *;

---------- CONTROLS QUERIES ----------
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

-- Get all controls
SELECT *
FROM controls
ORDER BY vgcpid DESC;

-- Get control by control_id
SELECT *
FROM controls
WHERE control_id = %s;

-- Get control by vgcpid
SELECT *
FROM controls
WHERE vgcpid = %s;

-- Update control by control_id
UPDATE controls
SET description = %s,
    control_owner = %s,
    control_sme = %s,
    escalation = %s,
    is_active = %s
WHERE control_id = %s
RETURNING *;

-- Update control by vgcpid
UPDATE controls
SET description = %s,
    control_owner = %s,
    control_sme = %s,
    escalation = %s,
    is_active = %s
WHERE vgcpid = %s
RETURNING *;

-- Update last_tested date to most recently completed test date for control
UPDATE controls
SET last_tested = (
    SELECT MAX(complete_date)
    FROM tests
    WHERE control_id = %s AND status = 'COMPLETED'
)
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
-- Create request
INSERT INTO requests (
    priority,
    requestor,
    due_date,
    description,
    created_by
)
VALUES (%s, %s, %s, %s, %s)
RETURNING *;

-- Get all requests (Includes generated display_id and request_date for the UI)
SELECT 
    *,
    'REQ-' || to_char(created_at, 'YYYY') || '-' || LPAD(request_id::TEXT, 3, '0') AS display_id,
    created_at::DATE AS request_date
FROM requests
ORDER BY created_at DESC;

-- Get request by request_id
SELECT 
    *,
    'REQ-' || to_char(created_at, 'YYYY') || '-' || LPAD(request_id::TEXT, 3, '0') AS display_id,
    created_at::DATE AS request_date
FROM requests
WHERE request_id = %s;

-- Update request by request_id
UPDATE requests
SET 
    priority = %s,
    requestor = %s,
    due_date = %s,
    description = %s
WHERE request_id = %s
RETURNING *;

-- Auto-Start Request
-- Executes safely: Only updates if the request is currently NOT_STARTED.
UPDATE requests
SET status = 'IN_PROGRESS',
    start_date = current_date
WHERE request_id = %s
  AND status = 'NOT_STARTED'
RETURNING *;

-- Auto-Complete Request
-- Executes safely: Only updates if ALL tests for the request are COMPLETED.
UPDATE requests
SET status = 'COMPLETED',
    complete_date = current_date
WHERE request_id = %s
  AND status != 'COMPLETED'
  AND NOT EXISTS (
      -- This subquery checks if ANY test for this request is NOT completed.
      -- If it finds even one, the NOT EXISTS evaluates to FALSE, and the update aborts.
      SELECT 1 
      FROM tests 
      WHERE request_id = %s 
        AND status != 'COMPLETED'
  )
RETURNING *;

-- Soft delete request by request_id
UPDATE requests
SET status = 'ARCHIVED'
WHERE request_id = %s
RETURNING *;

-- Hard delete request by request_id
DELETE FROM requests
WHERE request_id = %s
RETURNING *;

---------- TESTS QUERIES ----------
-- Create test  
INSERT INTO tests (
        control_id,
        request_id,
        assigned_tester_id,
        requires_dat,
        requires_oet,
        due_date,
        estimated_date,
        description
    )
VALUES (
    (SELECT control_id FROM controls WHERE vgcpid = %s),
    %s, 
    %s, 
    %s, 
    %s, 
    %s, 
    %s, 
    %s
)
RETURNING *;

-- Get all tests (Joined to get vgcpid for the UI)
SELECT 
    t.*,
    c.vgcpid
FROM tests t
JOIN controls c ON t.control_id = c.control_id
ORDER BY t.test_id DESC;

-- Get test by test_id (Joined to get vgcpid)
SELECT 
    t.*,
    c.vgcpid
FROM tests t
JOIN controls c ON t.control_id = c.control_id
WHERE t.test_id = %s;

-- Get tests by request_id (Joined to get vgcpid)
SELECT 
    t.*,
    c.vgcpid
FROM tests t
JOIN controls c ON t.control_id = c.control_id
WHERE t.request_id = %s
ORDER BY t.test_id DESC;

-- Get tests by request_id WITH control details
SELECT 
    t.*,
    c.vgcpid,
    u.display_name AS tester_name
FROM tests t
JOIN controls c ON t.control_id = c.control_id
LEFT JOIN users u ON t.assigned_tester_id = u.user_id
WHERE t.request_id = %s
ORDER BY t.test_id DESC;

-- Get tests by control_id 
SELECT 
    t.*,
    c.vgcpid
FROM tests t
JOIN controls c ON t.control_id = c.control_id
WHERE t.control_id = %s
ORDER BY t.test_id DESC;

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

-- Update test status to IN_PROGRESS 
UPDATE tests
SET status = 'IN_PROGRESS',
    start_date = COALESCE(start_date, current_date) 
WHERE test_id = %s
RETURNING *;

-- Update test status to IN_REVIEW 
UPDATE tests
SET status = 'IN_REVIEW'
WHERE test_id = %s
RETURNING *;

-- Update test status to COMPLETED 
UPDATE tests
SET status = 'COMPLETED',
    complete_date = current_date
WHERE test_id = %s
RETURNING *;

-- Soft delete test by test_id
UPDATE tests
SET status = 'ARCHIVED'
WHERE test_id = %s
RETURNING *;

-- Hard delete test by test_id
DELETE FROM tests
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
