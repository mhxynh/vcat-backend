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
    CREATE TYPE request_status AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'IN_REVIEW', 'COMPLETED', 'BLOCKED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE test_status AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'IN_REVIEW', 'COMPLETED', 'BLOCKED');
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
    display_name    TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS controls (
    control_id      BIGSERIAL PRIMARY KEY,
    vgcpid          VARCHAR(50) UNIQUE NOT NULL,
    title           TEXT NOT NULL, 
    description     TEXT,
    control_owner   TEXT,
    control_sme     TEXT,
    escalation      BOOLEAN NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    data_created    DATE NOT NULL DEFAULT current_date,
    last_tested     DATE
);

CREATE TABLE IF NOT EXISTS requests (
    request_id      BIGSERIAL PRIMARY KEY,
    requestor       TEXT,
    start_date      DATE,
    due_date        DATE,
    complete_date   DATE,
    status          request_status NOT NULL DEFAULT 'NOT_STARTED'
    created_by      BIGINT REFERENCES users(user_id), --I'm thinking of add this because would be good for audit tracker
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tests (
    test_id             BIGSERIAL PRIMARY KEY,
    request_id          BIGINT NOT NULL REFERENCES request_id(request_id) NO DELETE CASCADE,
    control_id          BIGINT NOT NULL REFERENCES controls(control_id),
    test_track          test_track NOT NULL
    assigned_tester_id  BIGINT REFERENCES users(user_id),
    description         TEXT,
    start_date          DATE,
    estimated_date      DATE,
    complete_date       DATE,
    in_progress_step    TEXT,
    status              test_status NOT NULL DEFAULT 'NO_STARTED',
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
        (test_id IS NOT NULL AND request_id IS NULL)
        OR
        (test_id IS NOT NULL and request_id IS NOT NULL)
    )
);

