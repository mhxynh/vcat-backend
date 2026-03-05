BEGIN;

---------- ENUMS ----------
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('MANAGER', 'TESTER');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE request_status AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'BLOCKED', 'ARCHIVED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE test_status AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'IN_REVIEW', 'COMPLETED', 'BLOCKED', 'ARCHIVED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE test_progress_step AS ENUM (
        'TESTING_READY',
        'WALKTHROUGH_SCHEDULED',
        'WALKTHROUGH_COMPLETED',
        'TESTING_IN_PROGRESS',
        'TESTING_BLOCKED',
        'TESTING_CANCELED',
        'COMPLETED',
        'ADDRESSING_COMMENTS'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE request_priority AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE audit_action AS ENUM ('CREATE', 'UPDATE', 'DELETE', 'ROLLBACK');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE auditable_entity AS ENUM ('CONTROL', 'REQUEST', 'TEST', 'COMMENT', 'USER');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE snapshot_mode AS ENUM ('FULL_AFTER', 'FULL_BEFORE', 'DIFF');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

---------- FUNCTIONS ----------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = now();
   RETURN NEW;
END;
$$ language 'plpgsql';

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
    description     TEXT NOT NULL,
    control_owner   TEXT NOT NULL,
    control_sme     TEXT,
    escalation      BOOLEAN NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    date_created    DATE NOT NULL DEFAULT current_date,
    last_tested     DATE
);

CREATE TABLE IF NOT EXISTS requests (
    request_id      BIGSERIAL PRIMARY KEY,
    requestor       TEXT NOT NULL,
    description     TEXT NOT NULL,
    start_date      DATE,
    due_date        DATE NOT NULL,
    complete_date   DATE,
    status          request_status NOT NULL DEFAULT 'NOT_STARTED',
    priority        request_priority NOT NULL DEFAULT 'MEDIUM',
    created_by      BIGINT REFERENCES users(user_id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tests (
    test_id             BIGSERIAL PRIMARY KEY,
    request_id          BIGINT NOT NULL REFERENCES requests(request_id) ON DELETE CASCADE,
    control_id          BIGINT NOT NULL REFERENCES controls(control_id),
    requires_dat        BOOLEAN NOT NULL DEFAULT TRUE,
    requires_oet        BOOLEAN NOT NULL DEFAULT TRUE,
    dat_step            test_progress_step,
    oet_step            test_progress_step,
    assigned_tester_id  BIGINT REFERENCES users(user_id),
    description         TEXT,
    start_date          DATE,
    estimated_date      DATE,
    due_date            DATE,
    complete_date       DATE,
    status              test_status NOT NULL DEFAULT 'NOT_STARTED',
    priority            request_priority NOT NULL DEFAULT 'MEDIUM',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT tests_unique_per_request_control_track UNIQUE (request_id, control_id),
    CONSTRAINT test_must_have_track CHECK (requires_dat OR requires_oet)
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
        (test_id IS NULL AND request_id IS NOT NULL)
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
    snapshot_mode   snapshot_mode NOT NULL DEFAULT 'FULL_AFTER',
    changed_fields  TEXT[],
    payload_size_bytes INTEGER,
    changed_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    reason          TEXT
);

---------- TRIGGERS ----------
CREATE TRIGGER update_tests_modtime BEFORE UPDATE ON tests FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

---------- INDEXES ----------
CREATE INDEX IF NOT EXISTS idx_tests_request ON tests(request_id);
CREATE INDEX IF NOT EXISTS idx_tests_control ON tests(control_id);
CREATE INDEX IF NOT EXISTS idx_tests_dat_step ON tests(dat_step);
CREATE INDEX IF NOT EXISTS idx_tests_oet_step ON tests(oet_step);
CREATE INDEX IF NOT EXISTS idx_tests_assigned ON tests(assigned_tester_id);
CREATE INDEX IF NOT EXISTS idx_comments_test ON comments(test_id);
CREATE INDEX IF NOT EXISTS idx_comments_request ON comments(request_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_logs(actor_user_id);
CREATE INDEX IF NOT EXISTS idx_audit_changed_at ON audit_logs(changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action_changed_at ON audit_logs(action, changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_entity_changed_at ON audit_logs(entity_type, changed_at DESC);

COMMIT;
