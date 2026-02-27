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
    """Helper function to execute psql commands cleanly."""
    cmd = ["psql", db_url, "-v", "ON_ERROR_STOP=1"] + args
    subprocess.run(cmd, check=True, capture_output=True, timeout=15)

def run_rebase():
    # Fetch config
    db_host = os.getenv("DB_HOST", "localhost")
    db_name = os.getenv("DB_NAME", "vcat_sandbox")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD")
    db_port = os.getenv("DB_PORT", "5432")

    if not db_password:
        print("❌ Error: DB_PASSWORD environment variable is not set.")
        return

    os.environ["PGPASSWORD"] = db_password
    
    target_db_url = f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}"
    admin_db_url = f"postgresql://{db_user}@{db_host}:{db_port}/postgres"

    print(f"\n⚠️  WARNING: This will completely WIPE the '{db_name}' database.")
    if input("Are you sure you want to continue? (Type 'y' to proceed): ").lower() != 'y':
        print("Rebase canceled.")
        return

    print("\nStarting database rebase...")

    try:
        print("Kicking active connections...")
        kill_connections_sql = f"""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = '{db_name}' AND pid <> pg_backend_pid();
        """
        subprocess.run(["psql", admin_db_url, "-c", kill_connections_sql], capture_output=True, timeout=10)

        print("Wiping existing tables and data...")
        run_psql(target_db_url, ["-c", "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"])

        print(f"Applying schema from {SCHEMA_PATH.name}...")
        run_psql(target_db_url, ["-f", str(SCHEMA_PATH)])

        print(f"Seeding data from {SEED_PATH.name}...")
        run_psql(target_db_url, ["-f", str(SEED_PATH)])

        print("\n✅ Database rebase complete! Your local database is fresh and ready to go.")
    except subprocess.TimeoutExpired:
        print("\n❌ Error: The rebase process timed out. Please check your database connection and try again.")
    except subprocess.CalledProcessError as e:
        print("\n❌ Error during rebase:")
        print(e.stderr.decode('utf-8') if e.stderr else "Unknown psql error.")

if __name__ == "__main__":
    run_rebase()
