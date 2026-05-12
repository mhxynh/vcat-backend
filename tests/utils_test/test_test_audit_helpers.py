from unittest.mock import MagicMock, patch

from utils.test_audit import TestAuditUtils
from utils.audit import AuditUtils


def test_context_set_and_clear():
    TestAuditUtils.clear_context()
    assert TestAuditUtils.get_context() is None

    TestAuditUtils.set_context(actor_user_id=42)
    ctx = TestAuditUtils.get_context()
    assert ctx["actor_user_id"] == 42

    TestAuditUtils.clear_context()
    assert TestAuditUtils.get_context() is None


def test_snapshot_uses_audit_config():
    row = {"test_id": "t1", "request_id": 5, "control_id": 3}
    snap = TestAuditUtils.snapshot(row)
    assert isinstance(snap, dict)
    assert snap.get("test_id") == "t1"


def test_audit_create_no_context_does_not_call_insert():
    TestAuditUtils.clear_context()
    mock_cur = MagicMock()
    with patch.object(AuditUtils, "insert_audit_row") as mock_insert:
        TestAuditUtils.audit_create(mock_cur, {"test_id": "t1"})
        mock_insert.assert_not_called()


def test_audit_create_calls_insert_when_context_present():
    TestAuditUtils.set_context(actor_user_id=99)
    mock_cur = MagicMock()
    with patch.object(AuditUtils, "insert_audit_row") as mock_insert:
        TestAuditUtils.audit_create(mock_cur, {"test_id": "t1"})
        mock_insert.assert_called_once()
    TestAuditUtils.clear_context()


def test_audit_update_behaviour_calls_insert_on_diff():
    TestAuditUtils.set_context(actor_user_id=7)
    mock_cur = MagicMock()
    before = {"test_id": "t1", "status": "OPEN"}
    after = {"test_id": "t1", "status": "CLOSED"}
    with patch.object(AuditUtils, "insert_audit_row") as mock_insert:
        TestAuditUtils.audit_update(mock_cur, before, after)
        mock_insert.assert_called_once()
    TestAuditUtils.clear_context()


def test_audit_soft_and_hard_delete_call_insert_when_context_present():
    TestAuditUtils.set_context(actor_user_id=5)
    mock_cur = MagicMock()
    before = {"test_id": "t1", "is_active": True}
    after = {"test_id": "t1", "is_active": False}

    with patch.object(AuditUtils, "insert_audit_row") as mock_insert:
        TestAuditUtils.audit_soft_delete(mock_cur, before, after)
        mock_insert.assert_called_once()
        mock_insert.reset_mock()

        TestAuditUtils.audit_hard_delete(mock_cur, before, after)
        mock_insert.assert_called_once()

    TestAuditUtils.clear_context()
