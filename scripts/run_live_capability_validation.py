"""Controlled runtime validation and visual report for core Zenthon capabilities."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(value: object) -> bool:
    return bool(value is True or (isinstance(value, dict) and value.get("ok") is True))


def main() -> None:
    from agents.manager import agent_manager
    from agents.unified_orchestrator import unified_orchestrator
    from brain.llm.client import get_llm_client
    from brain.self_mutate import self_mutate_engine
    from tools.registry import tool_registry

    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-mutation", action="store_true")
    args = parser.parse_args()

    results: dict[str, dict] = {}
    llm = get_llm_client(force_new=True).health_check()
    results["Lokal LLM"] = {"ok": bool(llm.get("reachable")), "detail": llm}

    react = unified_orchestrator.run("Saat neçədir?", agents=["react"])
    results["ReAct agent"] = {"ok": bool(react.get("ok")), "detail": react}

    coding_agent = agent_manager.create("coding", allow_experimental=False)
    coding = agent_manager.run(
        coding_agent.id,
        "Faktorial funksiyası yarat",
        {"filename": "capability_validation_factorial.py", "run": True},
    )
    results["Coding agent"] = {"ok": bool(coding.success), "detail": coding.output or coding.error}

    available_tools = {item["name"] for item in tool_registry.list_tools()}
    media_tools = {"image_info", "image_process", "image_generate", "image_describe", "speech_to_text", "text_to_speech"}
    results["Görüntü və səs"] = {"ok": media_tools.issubset(available_tools), "detail": {"registered": sorted(media_tools & available_tools)}}

    if args.skip_mutation:
        mutation = self_mutate_engine.status().get("last_apply") or {"ok": False, "note": "No prior mutation"}
    else:
        proposal = self_mutate_engine.propose_strategy(
            "qa_pair_append",
            goal="sual: Təhlükəsiz mutasiya nə edir? cavab: Yalnız keyfiyyət və geri alma qapılarından keçən dəyişikliyi tətbiq edir.",
        )
        mutation = self_mutate_engine.apply(proposal["proposal_id"], run_smoke=True) if proposal.get("ok") else proposal
    results["Self-mutation"] = {"ok": _ok(mutation), "detail": mutation}

    report_dir = ROOT / "data" / "leon" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_json = report_dir / "live_capability_validation.json"
    report_json.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels, values = list(results), [1 if item["ok"] else 0 for item in results.values()]
    colors = ["#22c55e" if value else "#ef4444" for value in values]
    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor="#0f172a")
    ax.set_facecolor("#0f172a")
    bars = ax.bar(labels, values, color=colors, width=0.58)
    ax.set_ylim(0, 1.18)
    ax.set_yticks([0, 1], ["Fail", "Passed"], color="#cbd5e1")
    ax.tick_params(axis="x", colors="#e2e8f0", labelrotation=12)
    for spine in ax.spines.values():
        spine.set_color("#475569")
    ax.grid(axis="y", color="#334155", alpha=0.65)
    ax.set_title("Zenthon — Live Capability Validation", color="white", weight="bold", pad=16)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.06, "PASS" if value else "CHECK", ha="center", color="white", weight="bold")
    fig.tight_layout()
    report_png = report_dir / "live_capability_validation.png"
    fig.savefig(report_png, dpi=160, facecolor=fig.get_facecolor())
    print(json.dumps({"results": results, "report_json": str(report_json), "report_png": str(report_png)}, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    if os.environ.get("LEON_ALLOW_MUTATE") != "1":
        raise SystemExit("LEON_ALLOW_MUTATE=1 tələb olunur")
    main()
