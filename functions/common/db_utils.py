import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_db_connection():
    try:
        connection = psycopg2.connect(
            host=os.environ.get('DB_HOST'),
            port=os.environ.get('DB_PORT', '5432'),
            database=os.environ.get('DB_NAME'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            cursor_factory=RealDictCursor
        )
        logger.info("SUCCESS: Connection to RDS established.")
        return connection
    except Exception as e:
        logger.error("ERROR: Could not connect to PostgreSQL instance.")
        logger.error(e)
        raise e
