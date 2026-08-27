from __future__ import annotations

import pytest


def test_tool_registry_exposes_contract_metadata():
    from tools.registry import tool_registry

    rows = {row["name"]: row for row in tool_registry.list_tools()}
    assert rows["write_file"]["policy"]["risk_level"] == "sandbox-write"
    assert rows["run_python"]["policy"]["timeout_seconds"] == 2.0
    assert rows["write_file"]["policy"]["redact_argument"] is True


def test_agent_execution_requires_explicit_approval():
    from core.exceptions import ToolApprovalRequiredError
    from security.gate import gate_tool

    with pytest.raises(ToolApprovalRequiredError):
        gate_tool("crew_run", user="agent", arg="private task")


def test_tool_gate_redacts_argument_in_audit_log():
    from security.audit import AuditLog, audit_log
    from security.gate import gate_tool

    previous_entries = audit_log._entries
    audit_log._entries = []
    try:
        gate_tool("write_file", user="agent", arg="secret.txt||do-not-log-this")
        entry = audit_log.query(action="tool.gate")[-1]
        assert entry["details"]["argument"] == "[redacted]"
        assert "do-not-log-this" not in str(entry["details"])
    finally:
        audit_log._entries = previous_entries
