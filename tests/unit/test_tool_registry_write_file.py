from tools.registry import ToolRegistry, tool_registry


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


def test_native_core_tools_are_registered_with_fallback_support():
    names = {item["name"] for item in tool_registry.list_tools()}
    assert {"native_core_status", "normalize_text", "text_fingerprint", "text_metrics"} <= names
