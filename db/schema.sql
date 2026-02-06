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
    
)