from utils.db_utils import DbUtils
from utils.logger import Logger
from utils.audit import AuditUtils


class CrudUtils:
    _audit_context = None

    @staticmethod
    def set_audit_context(actor_user_id=None):
        CrudUtils._audit_context = {
            "actor_user_id": actor_user_id,
        }

    @staticmethod
    def clear_audit_context():
        CrudUtils._audit_context = None

    @staticmethod
    def get_all(table, order_by=None):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    if order_by:
                        cur.execute(f"SELECT * FROM {table} ORDER BY {order_by} DESC")
                    else:
                        cur.execute(f"SELECT * FROM {table}")
                    return [dict(row) for row in cur.fetchall()]
            finally:
                conn.close()
        except Exception as e:
            Logger.log(
                level="ERROR",
                message="Error fetching all records",
                extra_fields={"error": str(e), "table": table},
            )
            raise e

    @staticmethod
    def get_by_id(table, pk_column, pk_value):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT * FROM {table} WHERE {pk_column} = %s", (pk_value,)
                    )
                    row = cur.fetchone()
                    return dict(row) if row else None
            finally:
                conn.close()
        except Exception as e:
            Logger.log(
                level="ERROR",
                message="Error fetching record by ID",
                extra_fields={
                    "error": str(e),
                    "table": table,
                    "pk_column": pk_column,
                    "pk_value": pk_value,
                },
            )
            raise e

    @staticmethod
    def get_by_filter(table, column, value):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT * FROM {table} WHERE {column} = %s", (value,))
                    return [dict(row) for row in cur.fetchall()]
            finally:
                conn.close()
        except Exception as e:
            Logger.log(
                level="ERROR",
                message="Error fetching records by filter",
                extra_fields={
                    "error": str(e),
                    "table": table,
                    "column": column,
                    "value": value,
                },
            )
            raise e

    @staticmethod
    def create(table, columns, values):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    cols = ", ".join(columns)
                    placeholders = ", ".join(["%s"] * len(values))
                    cur.execute(
                        f"INSERT INTO {table} ({cols}) "
                        f"VALUES ({placeholders}) RETURNING *",
                        values,
                    )
                    created_row = dict(cur.fetchone())
                    AuditUtils.audit_create(
                        cur, table, created_row, CrudUtils._audit_context
                    )
                    conn.commit()
                    return created_row
            finally:
                conn.close()
        except Exception as e:
            Logger.log(
                level="ERROR",
                message="Error creating record",
                extra_fields={"error": str(e), "table": table, "columns": columns},
            )
            raise e

    @staticmethod
    def update(table, pk_column, pk_value, updates):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    before_row = None
                    if CrudUtils._audit_context and AuditUtils.get_table_audit_config(
                        table
                    ):
                        cur.execute(
                            f"SELECT * FROM {table} WHERE {pk_column} = %s", (pk_value,)
                        )
                        before_row = cur.fetchone()

                    set_clause = ", ".join([f"{col} = %s" for col in updates.keys()])
                    values = list(updates.values()) + [pk_value]
                    cur.execute(
                        f"UPDATE {table} SET {set_clause} "
                        f"WHERE {pk_column} = %s RETURNING *",
                        values,
                    )
                    row = cur.fetchone()
                    updated_row = dict(row) if row else None
                    AuditUtils.audit_update(
                        cur=cur,
                        table=table,
                        before_row=dict(before_row) if before_row else None,
                        after_row=updated_row,
                        updates=updates,
                        context=CrudUtils._audit_context,
                    )
                    conn.commit()
                    return updated_row
            finally:
                conn.close()
        except Exception as e:
            Logger.log(
                level="ERROR",
                message="Error updating record",
                extra_fields={
                    "error": str(e),
                    "table": table,
                    "pk_column": pk_column,
                    "pk_value": pk_value,
                    "updates": updates,
                },
            )
            raise e

    @staticmethod
    def deactivate(table, pk_column, pk_value):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    before_row = None
                    if CrudUtils._audit_context and AuditUtils.get_table_audit_config(
                        table
                    ):
                        cur.execute(
                            f"SELECT * FROM {table} WHERE {pk_column} = %s", (pk_value,)
                        )
                        before_row = cur.fetchone()

                    cur.execute(
                        f"UPDATE {table} SET is_active = FALSE "
                        f"WHERE {pk_column} = %s RETURNING *",
                        (pk_value,),
                    )
                    row = cur.fetchone()
                    deactivated_row = dict(row) if row else None
                    AuditUtils.audit_delete(
                        cur=cur,
                        table=table,
                        before_row=dict(before_row) if before_row else None,
                        deleted_row=deactivated_row,
                        context=CrudUtils._audit_context,
                        is_soft_delete=True,
                    )
                    conn.commit()
                    return deactivated_row
            finally:
                conn.close()
        except Exception as e:
            Logger.log(
                level="ERROR",
                message="Error deactivating record",
                extra_fields={
                    "error": str(e),
                    "table": table,
                    "pk_column": pk_column,
                    "pk_value": pk_value,
                },
            )
            raise e

    @staticmethod
    def hard_delete(table, pk_column, pk_value):
        try:
            conn = DbUtils.get_db_connection()
            try:
                with conn.cursor() as cur:
                    before_row = None
                    if CrudUtils._audit_context and AuditUtils.get_table_audit_config(
                        table
                    ):
                        cur.execute(
                            f"SELECT * FROM {table} WHERE {pk_column} = %s", (pk_value,)
                        )
                        before_row = cur.fetchone()

                    cur.execute(
                        f"DELETE FROM {table} WHERE {pk_column} = %s RETURNING *",
                        (pk_value,),
                    )
                    row = cur.fetchone()
                    deleted_row = dict(row) if row else None
                    AuditUtils.audit_delete(
                        cur=cur,
                        table=table,
                        before_row=dict(before_row) if before_row else None,
                        deleted_row=deleted_row,
                        context=CrudUtils._audit_context,
                        is_soft_delete=False,
                    )
                    conn.commit()
                    return deleted_row
            finally:
                conn.close()
        except Exception as e:
            Logger.log(
                level="ERROR",
                message="Error hard deleting record",
                extra_fields={
                    "error": str(e),
                    "table": table,
                    "pk_column": pk_column,
                    "pk_value": pk_value,
                },
            )
            raise e
