import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor

from utils.logger import Logger

class DbUtils:
    @staticmethod
    def get_db_connection():
        try:
            required = {
                'DB_HOST': os.environ.get('DB_HOST'),
                'DB_NAME': os.environ.get('DB_NAME'),
                'DB_USER': os.environ.get('DB_USER'),
                'DB_PASSWORD': os.environ.get('DB_PASSWORD'),
            }
            missing = [key for key, value in required.items() if not value]
            if missing:
                Logger.log(level="ERROR", message="Missing required database environment variables", extra_fields={"missing": missing})
                raise Exception()

            connection = psycopg2.connect(
                host=required['DB_HOST'],
                port=os.environ.get('DB_PORT', '5432'),
                database=required['DB_NAME'],
                user=required['DB_USER'],
                password=required['DB_PASSWORD'],
                cursor_factory=RealDictCursor
            )
            Logger.log(level="INFO", message="Successfully connected to the database", extra_fields={"host": required['DB_HOST'], "database": required['DB_NAME']})
            return connection
        except Exception as e:
            Logger.log(level="ERROR", message=f"Database connection failed", extra_fields={"error": str(e)})
            raise e
