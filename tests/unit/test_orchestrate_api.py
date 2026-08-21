from interfaces.api.main import native_core_status, root


def test_root_lists_orchestration_endpoint():
    assert "/orchestrate" in root()["endpoints"]


def test_root_lists_native_core_status_endpoint():
    assert "/native-core/status" in root()["endpoints"]


def test_native_core_status_discloses_python_fallback_without_binary():
    report = native_core_status()
    assert report["mode"] == "python-fallback"
    assert report["available"] is False
