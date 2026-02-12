\set ON_ERROR_STOP on

-- Defaults (only applied if you don't pass -v VAR=...)
\if :{?USERS} \else \set USERS 20 \endif
\if :{?MANAGERS} \else \set MANAGERS 5 \endif
\if :{?CONTROLS} \else \set CONTROLS 10 \endif
\if :{?REQUESTS} \else \set REQUESTS :CONTROLS \endif
\if :{?COMMENTS_PER_REQUEST} \else \set COMMENTS_PER_REQUEST 2 \endif
\if :{?ESCALATION_EVERY} \else \set ESCALATION_EVERY 10 \endif

BEGIN;

TRUNCATE TABLE
  audit_logs,
  comments,
  tests,
  requests,
  controls,
  users
RESTART IDENTITY CASCADE;

-- ----------------------------
-- USERS
-- ----------------------------
-- Managers (default 5)
INSERT INTO users (email, role, display_name)
SELECT
  format('manager%02s@vcat.local', i),
  'MANAGER'::user_role,
  format('Manager %02s', i)
FROM generate_series(1, :MANAGERS) AS s(i);

-- Testers (USERS - MANAGERS)
INSERT INTO users (email, role, display_name)
SELECT
  format('tester%02s@vcat.local', i),
  'TESTER'::user_role,
  format('Tester %02s', i)
FROM generate_series(1, GREATEST(:USERS - :MANAGERS, 1)) AS s(i);

-- ----------------------------
-- CONTROLS
-- ----------------------------
INSERT INTO controls (vgcpid, description, control_owner, control_sme, escalation, last_tested)
SELECT
  format('VGCP-%05s', i) AS vgcpid,
  format('Description for control %s.', i) AS description,
  format('Owner %s', ((i - 1) % 8) + 1) AS control_owner,
  format('SME %s', ((i - 1) % 6) + 1) AS control_sme,
  (i % :ESCALATION_EVERY = 0) AS escalation,
  CASE WHEN i % 4 = 0 THEN (current_date - (i % 30)) ELSE NULL END AS last_tested
FROM generate_series(1, :CONTROLS) AS s(i);

-- ----------------------------
-- REQUESTS (default = CONTROLS)
-- ----------------------------
INSERT INTO requests (requestor, start_date, due_date, complete_date, status, created_by)
SELECT
  format('Requester %s', ((i - 1) % 10) + 1),
  (current_date - ((i - 1) % 14))::date,
  (current_date + ((i - 1) % 21) + 7)::date,
  CASE WHEN i % 5 = 0 THEN current_date::date ELSE NULL END,
  CASE
    WHEN i % 5 = 0 THEN 'COMPLETED'::request_status
    WHEN i % 3 = 0 THEN 'IN_REVIEW'::request_status
    WHEN i % 2 = 0 THEN 'IN_PROGRESS'::request_status
    ELSE 'NOT_STARTED'::request_status
  END,
  (SELECT user_id FROM users WHERE role='MANAGER'::user_role ORDER BY user_id LIMIT 1)
FROM generate_series(1, :REQUESTS) AS s(i);

-- ----------------------------
-- TESTS: DAT + OET per request/control pair
-- We map request N -> control N by row_number() (deterministic).
-- ----------------------------
WITH
  c AS (
    SELECT control_id, vgcpid, row_number() OVER (ORDER BY control_id) AS rn
    FROM controls
  ),
  r AS (
    SELECT request_id, status, start_date, due_date, complete_date,
           row_number() OVER (ORDER BY request_id) AS rn
    FROM requests
  ),
  pairs AS (
    SELECT r.request_id, r.status AS request_status, r.start_date, r.due_date, r.complete_date,
           c.control_id, c.vgcpid
    FROM r
    JOIN c USING (rn)
  )
INSERT INTO tests (
  request_id, control_id, test_type, assigned_tester_id,
  description, start_date, estimated_date, complete_date,
  in_progress_step, status
)
SELECT
  p.request_id,
  p.control_id,
  tt.track::test_type,
  (SELECT user_id
   FROM users
   WHERE role='TESTER'::user_role
   ORDER BY user_id
   OFFSET ((p.control_id - 1) % GREATEST(:USERS - :MANAGERS, 1))
   LIMIT 1),
  format('%s testing for %s', tt.track, p.vgcpid),
  CASE WHEN p.request_status IN ('IN_PROGRESS','IN_REVIEW','COMPLETED') THEN p.start_date ELSE NULL END,
  (p.due_date - 2),
  CASE WHEN p.request_status = 'COMPLETED' THEN p.complete_date ELSE NULL END,
  CASE
    WHEN p.request_status = 'NOT_STARTED' THEN NULL
    WHEN p.request_status = 'IN_PROGRESS' THEN 'TESTING_IN_PROGRESS'::test_progress_step
    WHEN p.request_status = 'IN_REVIEW' THEN 'ADDRESSING_COMMENTS'::test_progress_step
    WHEN p.request_status = 'COMPLETED' THEN 'COMPLETED'::test_progress_step
    ELSE 'TESTING_BLOCKED'::test_progress_step
  END,
  CASE
    WHEN p.request_status = 'NOT_STARTED' THEN 'NOT_STARTED'::test_status
    WHEN p.request_status = 'IN_PROGRESS' THEN 'IN_PROGRESS'::test_status
    WHEN p.request_status = 'IN_REVIEW' THEN 'IN_REVIEW'::test_status
    WHEN p.request_status = 'COMPLETED' THEN 'COMPLETED'::test_status
    ELSE 'BLOCKED'::test_status
  END
FROM pairs p
CROSS JOIN (VALUES ('DAT'), ('OET')) AS tt(track);

-- ----------------------------
-- COMMENTS (lightweight + adjustable)
-- ----------------------------
-- 1 request-level comment per request
INSERT INTO comments (author_user_id, request_id, test_id, comment_text)
SELECT
  (SELECT user_id FROM users WHERE role='MANAGER'::user_role ORDER BY user_id OFFSET ((r.request_id - 1) % :MANAGERS) LIMIT 1),
  r.request_id,
  NULL::bigint,
  format('Request %s created (%s).', r.request_id, r.status)
FROM requests r;

-- (COMMENTS_PER_REQUEST - 1) test-level comments per request (spread across tests)
-- Example: if COMMENTS_PER_REQUEST=2 => adds 1 extra comment per request.
INSERT INTO comments (author_user_id, request_id, test_id, comment_text)
SELECT
  (SELECT user_id FROM users WHERE role='TESTER'::user_role ORDER BY user_id OFFSET ((t.test_id - 1) % GREATEST(:USERS - :MANAGERS, 1)) LIMIT 1),
  NULL::bigint,
  t.test_id,
  format('Update on %s: %s', t.test_type, COALESCE(t.in_progress_step::text, 'Not started'))
FROM tests t
WHERE t.test_id % 2 = 0
LIMIT (SELECT GREATEST((:COMMENTS_PER_REQUEST - 1) * :REQUESTS, 0));

COMMIT;
