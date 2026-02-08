#!/usr/bin/env bash
set -euo pipefail

# NOTE: This is for local postgres DBs only! Don't run this against production or staging databases, or else we gonna rewrite the data!
# Before running, create a local postgres DB called "vcatdb" and update the DB_URL if needed.

# FIRST: bash cmd you put in your CLI: createdb -U postgres vcatdb
# THEN: you can run this script. 

# Usage examples:
#   DB_URL="postgres://postgres:postgres@localhost:5432/vcatdb" ./scripts/db_reset.sh
#   ./scripts/db_reset.sh --users 12 --managers 3 --controls 50 --requests 50 --comments-per-request 1
#
# Defaults (can be overridden by flags)
DB_URL="${DB_URL:-postgres://postgres:postgres@localhost:5432/vcatdb}"

USERS="${USERS:-1}"
MANAGERS="${MANAGERS:-1}"
CONTROLS="${CONTROLS:-11}"
REQUESTS="${REQUESTS:-$CONTROLS}"
COMMENTS_PER_REQUEST="${COMMENTS_PER_REQUEST:-2}"
ESCALATION_EVERY="${ESCALATION_EVERY:-10}"

print_help() {
  cat <<EOF
Reset and seed the VCAT database.

Env:
  DB_URL=postgres://user:pass@host:5432/dbname

Flags:
  --users N                 (default: $USERS)
  --managers N              (default: $MANAGERS)
  --controls N              (default: $CONTROLS)
  --requests N              (default: $REQUESTS)
  --comments-per-request N  (default: $COMMENTS_PER_REQUEST)
  --escalation-every N      (default: $ESCALATION_EVERY)
  -h, --help                Show help

Examples:
  ./scripts/db_reset.sh
  ./scripts/db_reset.sh --users 12 --controls 50 --comments-per-request 1
EOF
}

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --users) USERS="$2"; shift 2 ;;
    --managers) MANAGERS="$2"; shift 2 ;;
    --controls) CONTROLS="$2"; shift 2 ;;
    --requests) REQUESTS="$2"; shift 2 ;;
    --comments-per-request) COMMENTS_PER_REQUEST="$2"; shift 2 ;;
    --escalation-every) ESCALATION_EVERY="$2"; shift 2 ;;
    -h|--help) print_help; exit 0 ;;
    *)
      echo "Unknown option: $1" >&2
      print_help
      exit 1
      ;;
  esac
done

# Basic validation
if [[ "$MANAGERS" -gt "$USERS" ]]; then
  echo "Error: --managers ($MANAGERS) cannot be greater than --users ($USERS)" >&2
  exit 1
fi

echo "Resetting and seeding DB: $DB_URL"
echo "Seed config: USERS=$USERS MANAGERS=$MANAGERS CONTROLS=$CONTROLS REQUESTS=$REQUESTS COMMENTS_PER_REQUEST=$COMMENTS_PER_REQUEST ESCALATION_EVERY=$ESCALATION_EVERY"

# Drop everything (tables + enums) in public schema
psql "$DB_URL" -v ON_ERROR_STOP=1 <<'SQL'
DO $$
DECLARE r RECORD;
BEGIN
  -- drop tables in public
  FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname='public') LOOP
    EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
  END LOOP;

  -- drop enums in public
  FOR r IN (
    SELECT t.typname
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname='public' AND t.typtype='e'
  ) LOOP
    EXECUTE 'DROP TYPE IF EXISTS public.' || quote_ident(r.typname) || ' CASCADE';
  END LOOP;
END $$;
SQL

# Recreate schema
psql "$DB_URL" -v ON_ERROR_STOP=1 -f db/schema.sql

# Seed with adjustable knobs (requires your refactored seed.sql using psql vars)
psql "$DB_URL" \
  -v ON_ERROR_STOP=1 \
  -v USERS="$USERS" \
  -v MANAGERS="$MANAGERS" \
  -v CONTROLS="$CONTROLS" \
  -v REQUESTS="$REQUESTS" \
  -v COMMENTS_PER_REQUEST="$COMMENTS_PER_REQUEST" \
  -v ESCALATION_EVERY="$ESCALATION_EVERY" \
  -f db/seed.sql

echo "Done."
