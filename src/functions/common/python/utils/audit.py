import json
from psycopg2.extras import Json


class AuditUtils:
    DEFAULT_MAX_PAYLOAD_BYTES = 65536
    TABLE_AUDIT_CONFIG = {
        "controls": {
            "entity_type": "CONTROL",
            "id_column": "control_id",
            "fields": [
                "control_id",
                "vgcpid",
                "description",
                "control_owner",
                "control_sme",
                "escalation",
                "is_active",
                "date_created",
                "last_tested",
            ],
        },
        "requests": {
            "entity_type": "REQUEST",
            "id_column": "request_id",
            "fields": [
                "request_id",
                "requestor",
                "description",
                "start_date",
                "due_date",
                "complete_date",
                "status",
                "priority",
                "created_by",
                "created_at",
            ],
        },
        "users": {
            "entity_type": "USER",
            "id_column": "user_id",
            "fields": [
                "user_id",
                "cognito_sub",
                "email",
                "role",
                "display_name",
                "is_active",
                "created_at",
            ],
        },
        "tests": {
            "entity_type": "TEST",
            "id_column": "test_id",
            "fields": [
                "test_id",
                "request_id",
                "control_id",
                "requires_dat",
                "requires_oet",
                "dat_step",
                "oet_step",
                "assigned_tester_id",
                "description",
                "start_date",
                "estimated_date",
                "due_date",
                "complete_date",
                "status",
                "priority",
                "created_at",
                "updated_at",
            ],
        },
        "comments": {
            "entity_type": "COMMENT",
            "id_column": "comment_id",
            "fields": [
                "comment_id",
                "author_user_id",
                "test_id",
                "request_id",
                "comment_text",
                "posted_at",
            ],
        },
    }

    @staticmethod
    def compact_snapshot(row, fields):
        if not row:
            return None
        return {field: row.get(field) for field in fields if field in row}

    @staticmethod
    def build_diff(before_snapshot, after_snapshot):
        if not before_snapshot or not after_snapshot:
            return {}

        changed = {}
        keys = set(before_snapshot.keys()) | set(after_snapshot.keys())
        for key in keys:
            before_value = before_snapshot.get(key)
            after_value = after_snapshot.get(key)
            if before_value != after_value:
                changed[key] = {"from": before_value, "to": after_value}
        return changed

    @staticmethod
    def snapshot_size_bytes(payload):
        if payload is None:
            return 0
        return len(json.dumps(payload, default=str).encode("utf-8"))

    @staticmethod
    def truncate_payload(payload, max_payload_bytes=DEFAULT_MAX_PAYLOAD_BYTES):
        if payload is None:
            return None, False

        if AuditUtils.snapshot_size_bytes(payload) <= max_payload_bytes:
            return payload, False

        truncated = {
            "truncated": True,
            "note": f"Payload exceeded {max_payload_bytes} bytes",
        }
        return truncated, True

    @staticmethod
    def to_json_safe(payload):
        if payload is None:
            return None
        # Normalize datetimes/dates and other non-JSON-native values.
        return json.loads(json.dumps(payload, default=str))

    @staticmethod
    def get_table_audit_config(table):
        return AuditUtils.TABLE_AUDIT_CONFIG.get(table)

    @staticmethod
    def snapshot_for_table(table, row):
        config = AuditUtils.get_table_audit_config(table)
        if not config or not row:
            return None
        return AuditUtils.compact_snapshot(row, config["fields"])

    @staticmethod
    def is_archive_update(updates):
        if not isinstance(updates, dict):
            return False
        return updates.get("status") == "ARCHIVED"

    @staticmethod
    def insert_audit_row(
        cur,
        actor_user_id,
        entity_type,
        entity_id,
        action,
        before_snapshot=None,
        after_snapshot=None,
        snapshot_mode=None,
        changed_fields=None,
        max_payload_bytes=DEFAULT_MAX_PAYLOAD_BYTES,
    ):
        before_payload, _ = AuditUtils.truncate_payload(
            before_snapshot, max_payload_bytes=max_payload_bytes
        )
        after_payload, _ = AuditUtils.truncate_payload(
            after_snapshot, max_payload_bytes=max_payload_bytes
        )
        before_payload = AuditUtils.to_json_safe(before_payload)
        after_payload = AuditUtils.to_json_safe(after_payload)
        payload_size_bytes = AuditUtils.snapshot_size_bytes(
            before_payload
        ) + AuditUtils.snapshot_size_bytes(after_payload)

        cur.execute(
            """
            INSERT INTO audit_logs (
                actor_user_id,
                entity_type,
                entity_id,
                action,
                before_snapshot,
                after_snapshot,
                snapshot_mode,
                changed_fields,
                payload_size_bytes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                actor_user_id,
                entity_type,
                entity_id,
                action,
                Json(before_payload) if before_payload is not None else None,
                Json(after_payload) if after_payload is not None else None,
                snapshot_mode,
                changed_fields,
                payload_size_bytes,
            ),
        )
        return dict(cur.fetchone())

    @staticmethod
    def audit_create(cur, table, created_row, context):
        config = AuditUtils.get_table_audit_config(table)
        if not config or not context or not created_row:
            return
        AuditUtils.insert_audit_row(
            cur=cur,
            actor_user_id=context.get("actor_user_id"),
            entity_type=config["entity_type"],
            entity_id=created_row.get(config["id_column"]),
            action="CREATE",
            before_snapshot=None,
            after_snapshot=AuditUtils.snapshot_for_table(table, created_row),
            snapshot_mode="FULL_AFTER",
            changed_fields=["*"],
        )

    @staticmethod
    def audit_update(cur, table, before_row, after_row, updates, context):
        config = AuditUtils.get_table_audit_config(table)
        if not config or not context or not after_row:
            return

        before_snapshot = (
            AuditUtils.snapshot_for_table(table, before_row) if before_row else None
        )
        after_snapshot = AuditUtils.snapshot_for_table(table, after_row)
        diff = AuditUtils.build_diff(before_snapshot or {}, after_snapshot or {})
        if not diff and not AuditUtils.is_archive_update(updates):
            return

        if AuditUtils.is_archive_update(updates):
            action = "DELETE"
            snapshot_mode = "FULL_BEFORE"
            payload = {"status": "ARCHIVED"}
            changed_fields = ["status"]
        else:
            action = "UPDATE"
            snapshot_mode = "DIFF"
            payload = {"changed": diff}
            changed_fields = sorted(diff.keys())

        AuditUtils.insert_audit_row(
            cur=cur,
            actor_user_id=context.get("actor_user_id"),
            entity_type=config["entity_type"],
            entity_id=after_row.get(config["id_column"]),
            action=action,
            before_snapshot=None if action == "UPDATE" else before_snapshot,
            after_snapshot=payload,
            snapshot_mode=snapshot_mode,
            changed_fields=changed_fields,
        )

    @staticmethod
    def audit_delete(
        cur, table, before_row, deleted_row, context, is_soft_delete=False
    ):
        config = AuditUtils.get_table_audit_config(table)
        if not config or not context or not deleted_row:
            return

        before_snapshot = (
            AuditUtils.snapshot_for_table(table, before_row) if before_row else None
        )
        if is_soft_delete:
            after_snapshot = {"is_active": False}
            changed_fields = ["is_active"]
        else:
            after_snapshot = None
            changed_fields = ["*"]

        AuditUtils.insert_audit_row(
            cur=cur,
            actor_user_id=context.get("actor_user_id"),
            entity_type=config["entity_type"],
            entity_id=deleted_row.get(config["id_column"]),
            action="DELETE",
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
            snapshot_mode="FULL_BEFORE",
            changed_fields=changed_fields,
        )
