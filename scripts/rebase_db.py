import os
import subprocess
import pathlib
from dotenv import load_dotenv

# Setup Paths
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=REPO_ROOT / ".env")

SCHEMA_PATH = REPO_ROOT / "database" / "schema.sql"
SEED_PATH = REPO_ROOT / "database" / "seed.sql"

def run_psql(db_url: str, args: list):
    cmd = ["psql", "-d", db_url, "-v", "ON_ERROR_STOP=1"] + args
    subprocess.run(cmd, check=True, timeout=15)

def run_rebase():
    # Fetch config
    db_host = os.getenv("DB_HOST", "localhost")
    db_name = os.getenv("DB_NAME", "vcat_sandbox")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD")
    db_port = os.getenv("DB_PORT", "5432")

    if not db_password:
        print("Error: DB_PASSWORD environment variable is not set.")
        return

    target_db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    admin_db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/postgres"

    print(f"WARNING: This will completely WIPE the '{db_name}' database.")
    if input("Are you sure you want to continue? (type 'y' to proceed): ").lower() != 'y':
        print("Rebase canceled.")
        return

    print("\nStarting database rebase...")

    try:
        print("Kicking active connections...")
        kill_connections_sql = f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{db_name}' AND pid <> pg_backend_pid();"
        subprocess.run(["psql", "-d", admin_db_url, "-c", kill_connections_sql], timeout=10)

        print("Wiping existing tables and data...")
        run_psql(target_db_url, ["-c", "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"])

        print(f"Applying schema from {SCHEMA_PATH.name}...")
        run_psql(target_db_url, ["-f", str(SCHEMA_PATH)])

        print(f"Seeding data from {SEED_PATH.name}...")
        run_psql(target_db_url, ["-f", str(SEED_PATH)])

        print("\nDatabase rebase complete! Your local database is fresh and ready to go.")
    except subprocess.TimeoutExpired:
        print("\nError: The database connection timed out. Look at the text directly above this line to see what psql was waiting for.")
    except subprocess.CalledProcessError as e:
        print(f"\nError during rebase. Process exited with code {e.returncode}")

if __name__ == "__main__":
    run_rebase()