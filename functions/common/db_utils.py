import os
import psycopg2
from psycopg2.extras import RealDictCursor

def test_connection():
    print("🔄 Attempting to connect to RDS...") # Add this!
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            password=os.getenv("DB_PASSWORD"),
            # ... other params
        )
        print("✅ Connection successful!")
    except Exception as e:
        print(f"❌ Connection failed: {e}") # This catches the "Silent" error
