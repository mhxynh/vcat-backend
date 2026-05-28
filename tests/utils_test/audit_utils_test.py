from datetime import datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch

from utils.audit import AuditUtils
from utils.test_audit import TestAuditUtils as TestAuditHelper


class TestAuditUtils(TestCase):
    def test_compact_snapshot_filters_fields(self):
        row = {"a": 1, "b": 2, "c": 3}
        result = AuditUtils.compact_snapshot(row, ["a", "c", "x"])
        self.assertEqual(result, {"a": 1, "c": 3})

    def test_build_diff_returns_changed_fields(self):
        before = {"a": 1, "b": 2}
        after = {"a": 1, "b": 3, "c": 4}
        result = AuditUtils.build_diff(before, after)
        self.assertEqual(result["b"], {"from": 2, "to": 3})
        self.assertEqual(result["c"], {"from": None, "to": 4})

    def test_build_diff_empty_when_missing_side(self):
        self.assertEqual(AuditUtils.build_diff(None, {"a": 1}), {})
        self.assertEqual(AuditUtils.build_diff({"a": 1}, None), {})

    def test_truncate_payload_marks_large_payload(self):
        payload = {"x": "a" * 500}
        truncated, was_truncated = AuditUtils.truncate_payload(payload, max_payload_bytes=32)
        self.assertTrue(was_truncated)
        self.assertTrue(truncated["truncated"])

    def test_to_json_safe_converts_datetime(self):
        payload = {"ts": datetime(2026, 1, 2, 3, 4, 5)}
        safe = AuditUtils.to_json_safe(payload)
        self.assertIsInstance(safe["ts"], str)
        self.assertIn("2026-01-02", safe["ts"])

    def test_get_table_audit_config_and_snapshot_for_table(self):
        cfg = AuditUtils.get_table_audit_config("controls")
        self.assertEqual(cfg["entity_type"], "CONTROL")

        row = {"control_id": 1, "vgcpid": "VGCP-1", "ignore": "x"}
        snap = AuditUtils.snapshot_for_table("controls", row)
        self.assertEqual(snap["control_id"], 1)
        self.assertEqual(snap["vgcpid"], "VGCP-1")
        self.assertNotIn("ignore", snap)

    def test_is_archive_update(self):
        self.assertTrue(AuditUtils.is_archive_update({"status": "ARCHIVED"}))
        self.assertFalse(AuditUtils.is_archive_update({"status": "DAT_IN_PROGRESS"}))
        self.assertFalse(AuditUtils.is_archive_update(None))

    def test_insert_audit_row_executes_insert(self):
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {"audit_id": 123}

        result = AuditUtils.insert_audit_row(
            cur=mock_cur,
            actor_user_id=1,
            entity_type="CONTROL",
            entity_id=99,
            action="CREATE",
            before_snapshot=None,
            after_snapshot={"a": "b"},
            snapshot_mode="FULL_AFTER",
            changed_fields=["*"],
        )

        self.assertEqual(result["audit_id"], 123)
        mock_cur.execute.assert_called_once()

    @patch("utils.audit.AuditUtils.insert_audit_row")
    def test_audit_create_calls_insert(self, mock_insert):
        row = {"control_id": 5, "vgcpid": "VGCP-5"}
        AuditUtils.audit_create(
            cur=MagicMock(),
            table="controls",
            created_row=row,
            context={"actor_user_id": 10},
        )
        mock_insert.assert_called_once()

    @patch("utils.audit.AuditUtils.insert_audit_row")
    def test_audit_update_diff_and_archive_paths(self, mock_insert):
        cur = MagicMock()
        before = {"request_id": 1, "status": "NOT_STARTED"}
        after = {"request_id": 1, "status": "DAT_IN_PROGRESS"}
        ctx = {"actor_user_id": 1}

        AuditUtils.audit_update(cur, "requests", before, after, {"status": "DAT_IN_PROGRESS"}, ctx)
        self.assertEqual(mock_insert.call_count, 1)

        AuditUtils.audit_update(cur, "requests", before, {"request_id": 1, "status": "ARCHIVED"}, {"status": "ARCHIVED"}, ctx)
        self.assertEqual(mock_insert.call_count, 2)

    @patch("utils.audit.AuditUtils.insert_audit_row")
    def test_audit_delete_soft_and_hard(self, mock_insert):
        cur = MagicMock()
        before = {"user_id": 1, "is_active": True}
        deleted = {"user_id": 1, "is_active": False}
        ctx = {"actor_user_id": 22}

        AuditUtils.audit_delete(cur, "users", before, deleted, ctx, is_soft_delete=True)
        AuditUtils.audit_delete(cur, "users", before, deleted, ctx, is_soft_delete=False)
        self.assertEqual(mock_insert.call_count, 2)


class TestTestAuditUtils(TestCase):
    def tearDown(self):
        TestAuditHelper.clear_context()

    def test_context_set_get_clear(self):
        TestAuditHelper.set_context(actor_user_id=7)
        self.assertEqual(TestAuditHelper.get_context()["actor_user_id"], 7)
        TestAuditHelper.clear_context()
        self.assertIsNone(TestAuditHelper.get_context())

    def test_snapshot_and_fetch_before(self):
        row = {"test_id": 1, "request_id": 2, "extra": "x"}
        snapshot = TestAuditHelper.snapshot(row)
        self.assertEqual(snapshot["test_id"], 1)
        self.assertNotIn("extra", snapshot)

        cur = MagicMock()
        cur.fetchone.return_value = {"test_id": 1}
        before = TestAuditHelper.fetch_before(cur, 1)
        cur.execute.assert_called_once_with("SELECT * FROM tests WHERE test_id = %s", (1,))
        self.assertEqual(before["test_id"], 1)

    @patch("utils.test_audit.AuditUtils.insert_audit_row")
    def test_audit_create_and_no_context_guard(self, mock_insert):
        TestAuditHelper.audit_create(MagicMock(), {"test_id": 1})
        mock_insert.assert_not_called()

        TestAuditHelper.set_context(actor_user_id=3)
        TestAuditHelper.audit_create(MagicMock(), {"test_id": 1, "status": "NOT_STARTED"})
        mock_insert.assert_called_once()

    @patch("utils.test_audit.AuditUtils.insert_audit_row")
    def test_audit_update_and_no_diff_guard(self, mock_insert):
        TestAuditHelper.set_context(actor_user_id=3)
        before = {"test_id": 1, "status": "A"}
        after = {"test_id": 1, "status": "A"}
        TestAuditHelper.audit_update(MagicMock(), before, after)
        mock_insert.assert_not_called()

        after2 = {"test_id": 1, "status": "B"}
        TestAuditHelper.audit_update(MagicMock(), before, after2)
        mock_insert.assert_called_once()

    @patch("utils.test_audit.AuditUtils.insert_audit_row")
    def test_audit_soft_and_hard_delete(self, mock_insert):
        TestAuditHelper.set_context(actor_user_id=9)
        before = {"test_id": 2, "status": "OET_IN_PROGRESS"}
        after = {"test_id": 2, "status": "ARCHIVED"}
        TestAuditHelper.audit_soft_delete(MagicMock(), before, after)
        TestAuditHelper.audit_hard_delete(MagicMock(), before, {"test_id": 2})
        self.assertEqual(mock_insert.call_count, 2)
