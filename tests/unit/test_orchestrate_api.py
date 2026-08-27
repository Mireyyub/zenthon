from interfaces.api.main import native_core_status, root


def test_root_lists_orchestration_endpoint():
    assert "/orchestrate" in root()["endpoints"]


def test_root_lists_native_core_status_endpoint():
    assert "/native-core/status" in root()["endpoints"]


def test_root_lists_local_native_core_events_endpoint():
    assert "/native-core/events" in root()["endpoints"]


def test_native_core_status_discloses_python_fallback_without_binary():
    report = native_core_status()
    assert report["mode"] == "python-fallback"
    assert report["available"] is False


def test_operation_error_preserves_security_code():
    import pytest
    from fastapi import HTTPException
    from core.exceptions import SecurityError
    from interfaces.api.main import _raise_operation_error

    with pytest.raises(HTTPException) as exc:
        _raise_operation_error(SecurityError("blocked"))
    assert exc.value.status_code == 403
    assert exc.value.detail["code"] == "SECURITY_ERROR"
