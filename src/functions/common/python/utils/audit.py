import json
from psycopg2.extras import Json


class AuditUtils:
    DEFAULT_MAX_PAYLOAD_BYTES = 65536

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

        truncated = {"truncated": True, "note": f"Payload exceeded {max_payload_bytes} bytes"}
        return truncated, True

    @staticmethod
    def to_json_safe(payload):
        if payload is None:
            return None
        # Normalize datetimes/dates and other non-JSON-native values.
        return json.loads(json.dumps(payload, default=str))

    @staticmethod
    def insert_audit_row(
        cur,
        actor_user_id,
        entity_type,
        entity_id,
        action,
        before_snapshot=None,
        after_snapshot=None,
        reason=None,
        snapshot_mode=None,
        changed_fields=None,
        max_payload_bytes=DEFAULT_MAX_PAYLOAD_BYTES,
    ):
        before_payload, before_truncated = AuditUtils.truncate_payload(before_snapshot, max_payload_bytes=max_payload_bytes)
        after_payload, after_truncated = AuditUtils.truncate_payload(after_snapshot, max_payload_bytes=max_payload_bytes)
        before_payload = AuditUtils.to_json_safe(before_payload)
        after_payload = AuditUtils.to_json_safe(after_payload)
        payload_size_bytes = AuditUtils.snapshot_size_bytes(before_payload) + AuditUtils.snapshot_size_bytes(after_payload)
        final_reason = reason
        if before_truncated or after_truncated:
            suffix = " [audit payload truncated]"
            final_reason = (final_reason or "") + suffix

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
                payload_size_bytes,
                reason
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                final_reason,
            ),
        )
        return dict(cur.fetchone())
