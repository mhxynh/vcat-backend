from db_utils import DbUtils
from utils.logger import Logger

class CrudUtils:
    @staticmethod
    def get_all(table, condition="TRUE"):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT * FROM {table} WHERE {condition}")
                    return [dict(row) for row in cur.fetchall()]
            finally:
                conn.close()
        except Exception as e:
            Logger.log(level="ERROR", message="Error fetching all records", extra_fields={"error": str(e), "table": table, "condition": condition})
            raise e

    @staticmethod
    def get_by_id(table, pk_column, pk_value):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT * FROM {table} WHERE {pk_column} = %s", (pk_value,))
                    row = cur.fetchone()
                    return dict(row) if row else None
            finally:
                conn.close()
        except Exception as e:
            Logger.log(level="ERROR", message="Error fetching record by ID", extra_fields={"error": str(e), "table": table, "pk_column": pk_column, "pk_value": pk_value})
            raise e

    @staticmethod
    def create(table, columns, values):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    cols = ", ".join(columns)
                    placeholders = ", ".join(["%s"] * len(values))
                    cur.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders}) RETURNING *", values)
                    conn.commit()
                    return dict(cur.fetchone())
            finally:
                conn.close()
        except Exception as e:
            Logger.log(level="ERROR", message="Error creating record", extra_fields={"error": str(e), "table": table, "columns": columns})
            raise e

    @staticmethod
    def update(table, pk_column, pk_value, updates):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    set_clause = ", ".join([f"{col} = %s" for col in updates.keys()])
                    values = list(updates.values()) + [pk_value]
                    cur.execute(f"UPDATE {table} SET {set_clause} WHERE {pk_column} = %s RETURNING *", values)
                    conn.commit()
                    row = cur.fetchone()
                    return dict(row) if row else None
            finally:
                conn.close()
        except Exception as e:
            Logger.log(level="ERROR", message="Error updating record", extra_fields={"error": str(e), "table": table, "pk_column": pk_column, "pk_value": pk_value, "updates": updates})
            raise e
