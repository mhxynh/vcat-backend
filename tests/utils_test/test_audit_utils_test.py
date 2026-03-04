from unittest import TestCase
from unittest.mock import MagicMock, patch

from utils.test_audit import TestAuditUtils


class TestTestAuditUtils(TestCase):
    def tearDown(self):
        TestAuditUtils.clear_context()

    def test_context_set_get_clear(self):
        TestAuditUtils.set_context(actor_user_id=7, reason="r")
        self.assertEqual(TestAuditUtils.get_context()["actor_user_id"], 7)
        TestAuditUtils.clear_context()
        self.assertIsNone(TestAuditUtils.get_context())

    def test_snapshot_and_fetch_before(self):
        row = {"test_id": 1, "request_id": 2, "extra": "x"}
        snapshot = TestAuditUtils.snapshot(row)
        self.assertEqual(snapshot["test_id"], 1)
        self.assertNotIn("extra", snapshot)

        cur = MagicMock()
        cur.fetchone.return_value = {"test_id": 1}
        before = TestAuditUtils.fetch_before(cur, 1)
        cur.execute.assert_called_once_with("SELECT * FROM tests WHERE test_id = %s", (1,))
        self.assertEqual(before["test_id"], 1)

    @patch("utils.test_audit.AuditUtils.insert_audit_row")
    def test_audit_create_and_no_context_guard(self, mock_insert):
        TestAuditUtils.audit_create(MagicMock(), {"test_id": 1})
        mock_insert.assert_not_called()

        TestAuditUtils.set_context(actor_user_id=3, reason="x")
        TestAuditUtils.audit_create(MagicMock(), {"test_id": 1, "status": "NOT_STARTED"})
        mock_insert.assert_called_once()

    @patch("utils.test_audit.AuditUtils.insert_audit_row")
    def test_audit_update_and_no_diff_guard(self, mock_insert):
        TestAuditUtils.set_context(actor_user_id=3, reason="x")
        before = {"test_id": 1, "status": "A"}
        after = {"test_id": 1, "status": "A"}
        TestAuditUtils.audit_update(MagicMock(), before, after)
        mock_insert.assert_not_called()

        after2 = {"test_id": 1, "status": "B"}
        TestAuditUtils.audit_update(MagicMock(), before, after2, reason_override="override")
        mock_insert.assert_called_once()

    @patch("utils.test_audit.AuditUtils.insert_audit_row")
    def test_audit_soft_and_hard_delete(self, mock_insert):
        TestAuditUtils.set_context(actor_user_id=9, reason=None)
        before = {"test_id": 2, "status": "IN_PROGRESS"}
        after = {"test_id": 2, "status": "ARCHIVED"}
        TestAuditUtils.audit_soft_delete(MagicMock(), before, after)
        TestAuditUtils.audit_hard_delete(MagicMock(), before, {"test_id": 2})
        self.assertEqual(mock_insert.call_count, 2)
