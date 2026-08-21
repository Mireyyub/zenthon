from interfaces.api.main import root


def test_root_lists_orchestration_endpoint():
    assert "/orchestrate" in root()["endpoints"]
