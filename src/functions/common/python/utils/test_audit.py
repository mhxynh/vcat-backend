from utils.audit import AuditUtils


class TestAuditUtils:
    _audit_context = None

    @staticmethod
    def set_context(actor_user_id=None):
        TestAuditUtils._audit_context = {
            "actor_user_id": actor_user_id,
        }

    @staticmethod
    def clear_context():
        TestAuditUtils._audit_context = None

    @staticmethod
    def get_context():
        return TestAuditUtils._audit_context

    @staticmethod
    def snapshot(row):
        return AuditUtils.snapshot_for_table("tests", row)

    @staticmethod
    def fetch_before(cur, test_id):
        cur.execute("SELECT * FROM tests WHERE test_id = %s", (test_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    @staticmethod
    def audit_create(cur, created_row):
        context = TestAuditUtils.get_context()
        if not context or not created_row:
            return

        AuditUtils.insert_audit_row(
            cur=cur,
            actor_user_id=context.get("actor_user_id"),
            entity_type="TEST",
            entity_id=created_row.get("test_id"),
            action="CREATE",
            before_snapshot=None,
            after_snapshot=AuditUtils.snapshot_for_table("tests", created_row),
            snapshot_mode="FULL_AFTER",
            changed_fields=["*"],
        )

    @staticmethod
    def audit_update(cur, before_row, after_row):
        context = TestAuditUtils.get_context()
        if not context or not after_row:
            return

        before_snapshot = AuditUtils.snapshot_for_table("tests", before_row) if before_row else None
        after_snapshot = AuditUtils.snapshot_for_table("tests", after_row)
        diff = AuditUtils.build_diff(before_snapshot or {}, after_snapshot or {})
        if not diff:
            return

        AuditUtils.insert_audit_row(
            cur=cur,
            actor_user_id=context.get("actor_user_id"),
            entity_type="TEST",
            entity_id=after_row.get("test_id"),
            action="UPDATE",
            before_snapshot=None,
            after_snapshot={"changed": diff},
            snapshot_mode="DIFF",
            changed_fields=sorted(diff.keys()),
        )

    @staticmethod
    def audit_soft_delete(cur, before_row, after_row):
        context = TestAuditUtils.get_context()
        if not context or not after_row:
            return

        AuditUtils.insert_audit_row(
            cur=cur,
            actor_user_id=context.get("actor_user_id"),
            entity_type="TEST",
            entity_id=after_row.get("test_id"),
            action="DELETE",
            before_snapshot=AuditUtils.snapshot_for_table("tests", before_row) if before_row else None,
            after_snapshot={"status": "ARCHIVED"},
            snapshot_mode="FULL_BEFORE",
            changed_fields=["status"],
        )

    @staticmethod
    def audit_hard_delete(cur, before_row, deleted_row):
        context = TestAuditUtils.get_context()
        if not context or not deleted_row:
            return

        AuditUtils.insert_audit_row(
            cur=cur,
            actor_user_id=context.get("actor_user_id"),
            entity_type="TEST",
            entity_id=deleted_row.get("test_id"),
            action="DELETE",
            before_snapshot=AuditUtils.snapshotot_for_table("tests", before_row) if before_row else None,
            after_snapshot=None,
            snapshot_mode="FULL_BEFORE",
            changed_fields=["*"],
        )
