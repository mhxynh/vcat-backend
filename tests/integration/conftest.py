import os
import uuid
import pathlib
import pytest
import psycopg2
import subprocess
from urllib.parse import urlparse
from dotenv import load_dotenv

# Define paths to your SQL files
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")
SCHEMA_PATH = REPO_ROOT / "database" / "schema.sql"
SEED_PATH = REPO_ROOT / "database" / "seed.sql"

def _get_admin_conn_params(dsn: str) -> dict:
    """Parses a DSN to get connection params for the 'postgres' (admin) db."""
    parsed = urlparse(dsn)
    return {
        "dbname": "postgres", # Always connect to default 'postgres' to create new DBs
        "user": parsed.username or "postgres",
        "password": parsed.password or "postgres",
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
    }

def _run_psql_file(db_url: str, file_path: pathlib.Path, vars: dict = None):
    '''
    Executes a SQL file using the psql CLI tool via subprocess.
    This is REQUIRED to support "if", "set", and other psql meta-commands.
    '''
    # -v ON_ERROR_STOP=1 ensures the test fails if the SQL fails
    cmd = ["psql", db_url, "-v", "ON_ERROR_STOP=1", "-f", str(file_path)]
    
    # Inject variables (e.g., -v USERS=5)
    if vars:
        for key, val in vars.items():
            cmd.extend(["-v", f"{key}={val}"])

    # Run the command
    # We pass PGPASSWORD in the env to avoid password prompts
    env = os.environ.copy()
    parsed = urlparse(db_url)
    if parsed.password:
        env["PGPASSWORD"] = parsed.password

    result = subprocess.run(
        cmd, 
        check=False, 
        capture_output=True, 
        text=True,
        env=env
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"psql failed executing {file_path.name}:\n{result.stderr}")

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
    """
    Creates a temporary database for the test session, runs schema+seed,
    and destroys it afterwards.
    """
    # 1. Get Base Connection Info
    base_dsn = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
    admin_params = _get_admin_conn_params(base_dsn)
    
    # 2. Create Unique Temp DB Name
    temp_db_name = f"vcat_test_{uuid.uuid4().hex[:8]}"
    
    # 3. Create the Database (using psycopg2 for the simple CREATE DB command)
    conn = psycopg2.connect(**admin_params)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(f'CREATE DATABASE "{temp_db_name}"')
    finally:
        conn.close()

    # 4. Construct DSN for the new temp DB
    parsed = urlparse(base_dsn)
    # Rebuild URL with new dbname
    temp_dsn = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/{temp_db_name}"

    try:
        # 5. Apply Schema & Seed using 'psql' subprocess
        print(f"  --> Applying schema to {temp_db_name}...")
        _run_psql_file(temp_dsn, SCHEMA_PATH)
        
        print(f"  --> Applying seed to {temp_db_name}...")
        # We pass smaller limits for tests to make them run faster
        seed_vars = {"USERS": "5", "CONTROLS": "5", "REQUESTS": "2"} 
        _run_psql_file(temp_dsn, SEED_PATH, vars=seed_vars)

        yield temp_dsn

    finally:
        # 6. Cleanup: Drop the DB
        conn = psycopg2.connect(**admin_params)
        conn.autocommit = True
        try:
            with conn.cursor() as cur:
                # Force disconnect any lingering sessions (like the test runner itself)
                cur.execute(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{temp_db_name}' AND pid <> pg_backend_pid()
                """)
                cur.execute(f'DROP DATABASE IF EXISTS "{temp_db_name}"')
                print(f"  --> Dropped temp db {temp_db_name}")
        finally:
            conn.close()

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
    """
    Provides a live psycopg2 connection to the temp database for tests.
    """
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
    base_dsn = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
    admin_params = _get_admin_conn_params(base_dsn)
    temp_db_name = f"vcat_test_seed_{uuid.uuid4().hex[:12]}"
    
    # Create admin connection
    admin_conn = psycopg2.connect(**admin_params)
    admin_conn.autocommit = True
    try:
        with admin_conn.cursor() as cur:
            cur.execute(f'CREATE DATABASE "{temp_db_name}"')
    finally:
        admin_conn.close()
    
    # Construct temp DSN
    parsed = urlparse(base_dsn)
    temp_dsn = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/{temp_db_name}"
    
    # Apply schema + seed
    try:
        _run_psql_file(temp_dsn, SCHEMA_PATH)
        _run_psql_file(temp_dsn, SEED_PATH)
        
        yield temp_dsn
    finally:
        # Cleanup: drop temp db
        admin_conn = psycopg2.connect(**admin_params)
        admin_conn.autocommit = True
        try:
            with admin_conn.cursor() as cur:
                cur.execute(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{temp_db_name}' AND pid <> pg_backend_pid()
                """)
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
