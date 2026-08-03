"""Faza 9 security tests."""

from __future__ import annotations

import pytest


def test_allowlist_default():
    from security.allowlist import tool_allowlist

    assert tool_allowlist.is_allowed("echo")
    assert not tool_allowlist.is_allowed("shell")


def test_path_sandbox_blocks_escape(tmp_path):
    from security.sandbox import PathSandbox
    from core.exceptions import SecurityError

    root = tmp_path / "sandbox"
    root.mkdir()
    sb = PathSandbox(roots=[root])
    ok = sb.resolve("note.txt")
    assert str(ok).startswith(str(root.resolve()))
    with pytest.raises(SecurityError):
        sb.resolve("/etc/passwd")


def test_permissions_guest():
    from security.permissions import PermissionManager

    pm = PermissionManager()
    assert pm.check("nobody", "brain.think")
    assert not pm.check("nobody", "tools.write_file")


def test_audit_log():
    from security.audit import AuditLog

    log = AuditLog(persist=False)
    eid = log.log("test.action", user="t", details={"x": 1})
    assert eid
    rows = log.query(action="test")
    assert rows
