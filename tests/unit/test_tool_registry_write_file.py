from tools.registry import ToolRegistry


def test_write_file_dispatch_splits_path_and_content_before_path_routing():
    captured = {}
    registry = ToolRegistry()
    registry.register(
        "write_file",
        lambda path, content: captured.update({"path": path, "content": content}) or captured,
        parameters={"path": "str", "content": "str"},
    )
    result = registry.dispatch("write_file", "sandbox/demo.py||result = 120")
    assert result == {"path": "sandbox/demo.py", "content": "result = 120"}
