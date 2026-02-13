import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor

from utils.logger import Logger

class DbUtils:
    @staticmethod
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
            Logger.log(level="INFO", message="Successfully connected to the database", extra_fields={"host": os.environ.get('DB_HOST'), "database": os.environ.get('DB_NAME')})
            return connection
        except Exception as e:
            Logger.log(level="ERROR", message=f"Database connection failed", extra_fields={"error": str(e)})
            raise e
