import os
import uuid
import pathlib
import psycopg2
import pytest
import re
from urllib.parse import urlparse
from dotenv import load_dotenv

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")
SCHEMA_PATH = REPO_ROOT / "database" / "schema.sql"
SEED_PATH = REPO_ROOT / "database" / "seed.sql"

def _get_admin_dsn() -> str:
    """
    DSN to connect to Postgres *admin database* (e.g. "postgres"),
    used only to create/drop a tep test database.
    
    Set the TEST_DATABASE_URL in ev to something like:
    postgres://postgres:postgres@localhost:5432/postgres

    :return: DSN string for admin database connection
    :rtype: str
    """
    dsn = os.getenv("TEST_DATABASE_URL")
    if not dsn:
        raise RuntimeError("TEST_DATABASE_URL. Example:\n"
                           "postgres://postgres:postgres@localhost:5432/postgres"            
        )
    return dsn

def _with_db_name(dsn: str, dbname: str) -> str:
    # simple + safe for typical Postgres URLs.
    # Assumes URL ends with /<dbname> o rhas dbname as last path segment.
    # Need to adjust if URL more complex
    if dsn.rstrip("/").endswith("/postgres"):
        return dsn.rstrip("/")[:-len("postgres")] + dbname
    # fallback: replace last path segment
    parts = dsn.rstrip("/").split("/")
    parts[-1] = dbname
    return "/".join(parts)

def _exec_sql_file(conn, path: pathlib.Path):
    
    sql = path.read_text(encoding="utf-8")
    
    # Extract psql variables from \set statements
    variables = {}
    for match in re.finditer(r'\\set\s+(\w+)\s+(.+?)(?=\s|$)', sql):
        var_name = match.group(1)
        var_value = match.group(2).strip("'\"")
        variables[var_name] = var_value
    
    # Remove psql meta-commands (lines starting with \)
    lines = [line for line in sql.split('\n') if not line.strip().startswith('\\')]
    sql = '\n'.join(lines)
    
    # Replace psql variables with their values (multiple passes to handle variable references)
    for _ in range(len(variables)):
        for var_name, var_value in variables.items():
            sql = sql.replace(f':{var_name}', var_value)
    
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()

def _set_db_env_from_dsn(dsn: str) -> None:
    parsed = urlparse(dsn)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError("Unsupported database URL scheme")

    db_name = parsed.path.lstrip("/")
    os.environ["DB_HOST"] = parsed.hostname or ""
    os.environ["DB_PORT"] = str(parsed.port or 5432)
    os.environ["DB_NAME"] = db_name
    os.environ["DB_USER"] = parsed.username or ""
    os.environ["DB_PASSWORD"] = parsed.password or ""
    os.environ.pop("DB_PASSWORD_SECRET_NAME", None)

@pytest.fixture(scope="session")
def test_db_url():
    admin_dsn = _get_admin_dsn()
    temp_db_name = f"vcat_test_{uuid.uuid4().hex[:12]}"
    temp_dsn = _with_db_name(admin_dsn, temp_db_name)

    # connect to admin db and create temp db
    admin_conn = psycopg2.connect(admin_dsn)
    admin_conn.autocommit = True
    try:
        with admin_conn.cursor() as cur:
            cur.execute(f'CREATE DATABASE "{temp_db_name}"')
    finally:
        admin_conn.close()

    # apply schema + seed
    conn = psycopg2.connect(temp_dsn)
    try:
        _exec_sql_file(conn, SCHEMA_PATH)
        _exec_sql_file(conn, SEED_PATH)
    finally:
        conn.close()
        
    yield temp_dsn

    # cleanup: drop temp db
    admin_conn = psycopg2.connect(admin_dsn)
    admin_conn.autocommit = True
    try:
        with admin_conn.cursor() as cur:
            # terminate any connection just in case
            cur.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s AND pid <> pg_backend_pid() 
                """,
                (temp_db_name,),
            )
            cur.execute(f'DROP DATABASE IF EXISTS "{temp_db_name}"')
    finally:
        admin_conn.close()

@pytest.fixture(scope="session", autouse=True)
def _use_temp_db_env(test_db_url):
    keys = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "DB_PASSWORD_SECRET_NAME",
    ]
    old_env = {key: os.environ.get(key) for key in keys}
    _set_db_env_from_dsn(test_db_url)
    try:
        yield
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

@pytest.fixture
def db_conn(test_db_url):
    conn = psycopg2.connect(test_db_url)
    try:
        yield conn
    finally:
        conn.close()

@pytest.fixture(scope="function")
def seed_db_url():
    """
    Separate fixture for seed tests - creates its own isolated database
    so it's not affected by other tests deleting data
    """
    admin_dsn = _get_admin_dsn()
    temp_db_name = f"vcat_test_seed_{uuid.uuid4().hex[:12]}"
    temp_dsn = _with_db_name(admin_dsn, temp_db_name)

    # connect to admin db and create temp db
    admin_conn = psycopg2.connect(admin_dsn)
    admin_conn.autocommit = True
    try:
        with admin_conn.cursor() as cur:
            cur.execute(f'CREATE DATABASE "{temp_db_name}"')
    finally:
        admin_conn.close()

    # apply schema + seed
    conn = psycopg2.connect(temp_dsn)
    try:
        _exec_sql_file(conn, SCHEMA_PATH)
        _exec_sql_file(conn, SEED_PATH)
    finally:
        conn.close()
        
    yield temp_dsn

    # cleanup: drop temp db
    admin_conn = psycopg2.connect(admin_dsn)
    admin_conn.autocommit = True
    try:
        with admin_conn.cursor() as cur:
            # terminate any connection just in case
            cur.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s AND pid <> pg_backend_pid() 
                """,
                (temp_db_name,),
            )
            cur.execute(f'DROP DATABASE IF EXISTS "{temp_db_name}"')
    finally:
        admin_conn.close()

@pytest.fixture
def seed_db_conn(seed_db_url):
    """Connection to the isolated seed test database"""
    conn = psycopg2.connect(seed_db_url)
    try:
        yield conn
    finally:
        conn.close()