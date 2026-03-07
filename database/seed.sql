\set ON_ERROR_STOP on

-- Defaults (only applied if you don't pass -v VAR=...)
\if :{?USERS} \else \set USERS 20 \endif
\if :{?MANAGERS} \else \set MANAGERS 5 \endif
\if :{?CONTROLS} \else \set CONTROLS 20 \endif
\if :{?REQUESTS} \else \set REQUESTS 5 \endif
\if :{?COMMENTS_PER_REQUEST} \else \set COMMENTS_PER_REQUEST 3 \endif
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

-- 1. USERS: MANAGERS + TESTERS
INSERT INTO users (email, role, display_name)
SELECT
  format('manager%02s@vcat.local', i),
  'MANAGER'::user_role,
  format('Manager %02s', i)
FROM generate_series(1, :MANAGERS) AS s(i);

INSERT INTO users (email, role, display_name)
SELECT
  format('tester%02s@vcat.local', i),
  'TESTER'::user_role,
  format('Tester %02s', i)
FROM generate_series(1, GREATEST(:USERS - :MANAGERS, 1)) AS s(i);

-- 2. CONTROLS
INSERT INTO controls (vgcpid, description, control_owner, control_sme, escalation, last_tested)
SELECT
  'VGCP-' || LPAD(CAST(FLOOR(RANDOM() * 100000) AS INT)::TEXT, 5, '0') AS vgcpid,
  format('Description for control %s.', i) AS description,
  format('Owner %s', ((i - 1) % 8) + 1) AS control_owner,
  format('SME %s', ((i - 1) % 6) + 1) AS control_sme,
  (i % :ESCALATION_EVERY = 0) AS escalation,
  CASE WHEN i % 4 = 0 THEN (current_date - (i % 30)) ELSE NULL END AS last_tested
FROM generate_series(1, :CONTROLS) AS s(i);

-- 3. REQUESTS
INSERT INTO requests (requestor, description, start_date, due_date, status, priority, created_by)
SELECT
  format('Requester %s', ((i - 1) % 10) + 1),
  format('Annual audit testing requirements for Request %s.', i),
  (current_date - ((i - 1) % 14))::date,
  (current_date + ((i - 1) % 21) + 7)::date,
  'NOT_STARTED'::request_status,
  (ARRAY['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']::request_priority[])[FLOOR(RANDOM() * 4 + 1)],
  (SELECT user_id FROM users WHERE role='MANAGER'::user_role ORDER BY user_id OFFSET ((s.i - 1) % :MANAGERS) LIMIT 1)
FROM generate_series(1, :REQUESTS) AS s(i);

-- 4. TESTS
WITH raw_test_flags AS (
  SELECT
    ((s.i - 1) % :REQUESTS) + 1 AS request_id,
    s.i AS control_id,
    (SELECT user_id FROM users WHERE role='TESTER'::user_role ORDER BY user_id OFFSET ((s.i - 1) % GREATEST(:USERS - :MANAGERS, 1)) LIMIT 1) AS assigned_tester_id,
    
    -- Generate booleans first
    CASE WHEN (s.i % 10) != 1 THEN TRUE ELSE FALSE END AS requires_dat,
    CASE WHEN (s.i % 10) != 0 THEN TRUE ELSE FALSE END AS requires_oet,
    
    (ARRAY['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']::request_priority[])[(s.i % 4) + 1] AS priority,
    (s.i % 5) AS raw_status_index
  FROM generate_series(1, :CONTROLS) AS s(i)
),
test_data AS (
  SELECT
    request_id,
    control_id,
    assigned_tester_id,
    requires_dat,
    requires_oet,
    priority,
    
    -- Smart Status Assignment: Skips phases that aren't required
    CASE
      WHEN raw_status_index = 0 THEN 'NOT_STARTED'::test_status
      WHEN raw_status_index = 1 AND requires_dat THEN 'DAT_IN_PROGRESS'::test_status
      WHEN raw_status_index = 1 AND NOT requires_dat THEN 'OET_IN_PROGRESS'::test_status
      WHEN raw_status_index = 2 AND requires_oet THEN 'OET_IN_PROGRESS'::test_status
      WHEN raw_status_index = 2 AND NOT requires_oet THEN 'IN_REVIEW'::test_status
      WHEN raw_status_index = 3 THEN 'IN_REVIEW'::test_status
      ELSE 'COMPLETED'::test_status
    END AS macro_status
  FROM raw_test_flags
)
INSERT INTO tests (
  request_id, control_id, assigned_tester_id, description,
  requires_dat, requires_oet, dat_step, oet_step, status, priority,
  start_date, estimated_date, due_date, complete_date
)
SELECT
  request_id,
  control_id,
  assigned_tester_id,
  format('Testing for Control %s', control_id),
  requires_dat,
  requires_oet,
  
  -- DAT STEP LOGIC
  CASE 
    WHEN NOT requires_dat THEN NULL
    WHEN macro_status = 'NOT_STARTED' THEN NULL
    WHEN macro_status IN ('OET_IN_PROGRESS', 'IN_REVIEW', 'COMPLETED') THEN 'COMPLETED'::test_progress_step
    ELSE (ARRAY['TESTING_READY', 'WALKTHROUGH_SCHEDULED', 'TESTING_IN_PROGRESS', 'ADDRESSING_COMMENTS']::test_progress_step[])[(control_id % 4) + 1]
  END AS dat_step,
  
  -- OET STEP LOGIC
  CASE 
    WHEN NOT requires_oet THEN NULL
    WHEN macro_status IN ('NOT_STARTED', 'DAT_IN_PROGRESS') THEN NULL
    WHEN macro_status IN ('IN_REVIEW', 'COMPLETED') THEN 'COMPLETED'::test_progress_step
    ELSE (ARRAY['TESTING_READY', 'TESTING_IN_PROGRESS', 'ADDRESSING_COMMENTS']::test_progress_step[])[(control_id % 3) + 1]
  END AS oet_step,

  macro_status AS status,
  priority,

  CASE WHEN macro_status != 'NOT_STARTED' THEN current_date - 5 ELSE NULL END AS start_date,
  current_date + 5 AS estimated_date,
  current_date + 10 AS due_date,
  CASE WHEN macro_status = 'COMPLETED' THEN current_date ELSE NULL END AS complete_date

FROM test_data;

-- 4b. UPDATE REQUEST STATUSES
-- Now that tests are created, we evaluate the status of the requests 
-- based on the completion of their tests.
UPDATE requests r
SET 
  status = CASE
    WHEN (SELECT count(*) FROM tests t WHERE t.request_id = r.request_id) = 0 THEN 'NOT_STARTED'::request_status
    WHEN (SELECT count(*) FROM tests t WHERE t.request_id = r.request_id AND t.status != 'COMPLETED') = 0 THEN 'COMPLETED'::request_status
    WHEN (SELECT count(*) FROM tests t WHERE t.request_id = r.request_id AND t.status != 'NOT_STARTED') > 0 THEN 'IN_PROGRESS'::request_status
    ELSE 'NOT_STARTED'::request_status
  END,
  complete_date = CASE
    WHEN (SELECT count(*) FROM tests t WHERE t.request_id = r.request_id AND t.status != 'COMPLETED') = 0 THEN current_date
    ELSE NULL
  END;

-- 5. COMMENTS
INSERT INTO comments (author_user_id, request_id, test_id, comment_text)
SELECT
  (SELECT user_id FROM users WHERE role='MANAGER'::user_role ORDER BY user_id OFFSET ((r.request_id - 1) % :MANAGERS) LIMIT 1),
  r.request_id,
  NULL::bigint,
  format('Request %s created.  Status: %s', r.request_id, r.status)
FROM requests r;

INSERT INTO comments (author_user_id, request_id, test_id, comment_text)
SELECT
  (SELECT user_id FROM users WHERE role='TESTER'::user_role ORDER BY user_id OFFSET ((t.test_id - 1) % GREATEST(:USERS - :MANAGERS, 1)) LIMIT 1),
  NULL::bigint,
  t.test_id,
  format('Work log for Test %s. DAT Step: %s, OET Step: %s', t.test_id, COALESCE(t.dat_step::text, 'N/A'), COALESCE(t.oet_step::text, 'N/A'))
FROM tests t
WHERE t.test_id % 2 = 0
LIMIT (SELECT GREATEST((:COMMENTS_PER_REQUEST - 1) * :REQUESTS, 0));

COMMIT;
