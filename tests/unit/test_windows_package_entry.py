from __future__ import annotations


def test_packaged_entry_routes_explicit_smoke_modes(monkeypatch):
    import zenthon_desktop
    import interfaces.desktop.package_smoke as package_smoke

    calls = []
    monkeypatch.setattr(package_smoke, "run_and_exit", lambda kind: calls.append(kind) or 0)
    assert zenthon_desktop.main(["--smoke"]) == 0
    assert zenthon_desktop.main(["--bridge-smoke"]) == 0
    assert calls == ["core", "bridge"]


def test_packaged_entry_rejects_unknown_argument():
    import zenthon_desktop

    assert zenthon_desktop.main(["--unknown"]) == 2


def test_package_bridge_smoke_uses_real_loopback_server():
    from interfaces.desktop.package_smoke import bridge_smoke

    report = bridge_smoke()
    assert report["ok"] is True
    assert report["root"]["name"] == "Leon"
