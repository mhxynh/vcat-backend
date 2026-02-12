-- This is a SQL schema file for a PostgreSQL database.
-- It follows:
    -- the schema-vcats.sql file,
    -- the Controls Tracker spreadsheet (DAT vs OET tracks),
    -- the OpenAPI endpoints: GET /summary, GET /requests, GET /tests

-- Run:
    --   createdb vcatdb
    --   psql -d vcatdb -f db/schema.sql
--

BEGIN;

---------- ENUMS ----------
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('MANAGER', 'TESTER');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE request_status AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'IN_REVIEW', 'COMPLETED', 'BLOCKED', 'ARCHIVED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE test_status AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'IN_REVIEW', 'COMPLETED', 'BLOCKED', 'ARCHIVED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- DAT/OET alignment with the Control Tracker Sheet
DO $$ BEGIN
    CREATE TYPE test_track AS ENUM ('DAT', 'OET');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE audit_action AS ENUM ('CREATE', 'UPDATE', 'DELETE', 'ROLLBACK');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE auditable_entity AS ENUM ('CONTROL', 'REQUEST', 'TEST', 'COMMENT', 'USER'); 
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

---------- TABLES ----------
CREATE TABLE IF NOT EXISTS users (
    user_id         BIGSERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    role            user_role NOT NULL,
    display_name    TEXT NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS controls (
    control_id      BIGSERIAL PRIMARY KEY,
    vgcpid          VARCHAR(50) UNIQUE NOT NULL,
    description     TEXT,
    control_owner   TEXT NOT NULL,
    control_sme     TEXT NOT NULL,
    escalation      BOOLEAN NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    date_created    DATE NOT NULL DEFAULT current_date,
    last_tested     DATE
);

CREATE TABLE IF NOT EXISTS requests (
    request_id      BIGSERIAL PRIMARY KEY,
    requestor       TEXT NOT NULL,
    start_date      DATE,
    due_date        DATE NOT NULL,
    complete_date   DATE,
    status          request_status NOT NULL DEFAULT 'NOT_STARTED',
    created_by      BIGINT REFERENCES users(user_id), 
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Tests are per (request, control, track)
CREATE TABLE IF NOT EXISTS tests (
    test_id             BIGSERIAL PRIMARY KEY,
    request_id          BIGINT NOT NULL REFERENCES requests(request_id) ON DELETE CASCADE,
    control_id          BIGINT NOT NULL REFERENCES controls(control_id),
    test_track          test_track NOT NULL,
    assigned_tester_id  BIGINT REFERENCES users(user_id),
    description         TEXT,
    start_date          DATE,
    estimated_date      DATE,
    complete_date       DATE,
    in_progress_step    TEXT,
    status              test_status NOT NULL DEFAULT 'NOT_STARTED',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT tests_unique_per_request_control_track UNIQUE (request_id, control_id, test_track)
);

CREATE TABLE IF NOT EXISTS comments (
    comment_id          BIGSERIAL PRIMARY KEY,
    author_user_id      BIGINT NOT NULL REFERENCES users(user_id),
    test_id             BIGINT REFERENCES tests(test_id) ON DELETE CASCADE,
    request_id          BIGINT REFERENCES requests(request_id) ON DELETE CASCADE,
    comment_text        TEXT NOT NULL,
    posted_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT  comments_target_chk CHECK (
        test_id IS NOT NULL OR request_id IS NOT NULL
    )
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id        BIGSERIAL PRIMARY KEY,
    actor_user_id   BIGINT  REFERENCES users(user_id),
    entity_type     auditable_entity NOT NULL,
    entity_id       BIGINT NOT NULL,
    action          audit_action NOT NULL,
    before_snapshot JSONB,
    after_snapshot  JSONB,
    changed_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    reason          TEXT
);

CREATE TABLE IF NOT EXISTS versions (
    version_id      BIGSERIAL PRIMARY KEY,
    entity_type     auditable_entity NOT NULL,
    entity_id       BIGINT NOT NULL,
    version_number  BIGINT NOT NULL,
    snapshot        JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by      BIGINT REFERENCES users(user_id),
    CONSTRAINT versions_unique UNIQUE (entity_type, entity_id, version_number)
);

---------- INDEXES ----------
CREATE INDEX IF NOT EXISTS idx_tests_request ON tests(request_id);
CREATE INDEX IF NOT EXISTS idx_tests_control ON tests(control_id);
CREATE INDEX IF NOT EXISTS idx_tests_track ON tests(test_track);
CREATE INDEX IF NOT EXISTS idx_tests_assigned ON tests(assigned_tester_id);
CREATE INDEX IF NOT EXISTS idx_comments_test ON comments(test_id);
CREATE INDEX IF NOT EXISTS idx_comments_request ON comments(request_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_logs(actor_user_id);
CREATE INDEX IF NOT EXISTS idx_versions_entity ON versions(entity_type, entity_id);
