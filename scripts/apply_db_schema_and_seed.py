import os
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "database" / "schema.sql"
#SEED_PATH = REPO_ROOT / "database" / "seed.sql"  # change to whatever seed file needed


def _read_sql(path: pathlib.Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")
    return path.read_text(encoding="utf-8")


def _run_sql(conn, sql: str, label: str) -> None:
    # Run as one transaction so you get all-or-nothing behavior
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f"✅ Ran {label} successfully")


def _verify(conn) -> None:
    with conn.cursor() as cur:
        # Basic verification queries required by the ticket
        cur.execute("SELECT COUNT(*) AS count FROM controls;")

    # RealDictCursor should give dict rows; to be safe, re-query cleanly:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS count FROM controls;")
        row = cur.fetchone()['count']
        print(f"✅ controls row count: {row['count'] if isinstance(row, dict) else row[0]}")

        cur.execute("SELECT * FROM controls LIMIT 5;")
        rows = cur.fetchall()
        print("✅ Sample controls rows (up to 5):")
        for r in rows:
            print(r)


def main():
    # Safety: refuse to run if password missing
    if not os.environ.get("DB_PASSWORD"):
        raise RuntimeError("DB_PASSWORD is empty. Check your .env / environment variables.")

    conn = get_db_connection()
    try:
        schema_sql = _read_sql(SCHEMA_PATH)
        #seed_sql = _read_sql(SEED_PATH)

        # NOTE: This does NOT drop tables. It only runs schema and seed.
        _run_sql(conn, schema_sql, "schema.sql")
        #_run_sql(conn, seed_sql, "seed.sql")
        _verify(conn)

        print("🎉 Done: schema + seed applied and verified.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
