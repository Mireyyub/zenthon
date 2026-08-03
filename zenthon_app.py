"""
Leon AI Platform – unified entrypoint (Faza 0).

    python zenthon_app.py
    python zenthon_app.py --bootstrap
    python zenthon_app.py --smoke
    python zenthon_app.py --status
"""

from __future__ import annotations

import argparse
import json
import sys


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Leon AI Platform")
    parser.add_argument("--bootstrap", action="store_true", help="Curriculum + genome bootstrap")
    parser.add_argument("--smoke", action="store_true", help="Faza 0 smoke test")
    parser.add_argument("--status", action="store_true", help="Status JSON")
    parser.add_argument("--volume", default="01", help="Curriculum volume for bootstrap")
    parser.add_argument("--no-llm-check", action="store_true", help="Skip Ollama/LLM probe")
    args = parser.parse_args(argv)

    from core.bootstrap import start_leon, leon_status, smoke_test
    from core.config import config
    from core.kernel import kernel

    print("=" * 64)
    print(f"  {config.ai_name} AI Platform")
    print("=" * 64)

    if args.smoke:
        report = smoke_test()
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        print("=" * 64)
        return 0 if report.get("overall_ok") else 1

    if args.status:
        print(json.dumps(leon_status(), ensure_ascii=False, indent=2, default=str))
        return 0

    report = start_leon(
        bootstrap_curriculum=args.bootstrap,
        volume_id=args.volume,
        check_llm=not args.no_llm_check,
    )

    print(f"\n[Paths] leon_dir={config.path.leon_dir}")
    for step in report.get("steps") or []:
        mark = "OK" if step.get("ok") else "FAIL"
        print(f"  [{mark}] {step.get('step')}", end="")
        if step.get("error"):
            print(f" — {step['error']}")
        else:
            print()

    if report.get("warnings"):
        print("\n[Warnings]")
        for w in report["warnings"]:
            print(f"  - {w}")

    if report.get("services"):
        print("\n[Services]")
        for k, v in report["services"].items():
            print(f"  {k}: {v}")

    llm = report.get("llm") or {}
    print(f"\n[LLM] provider={llm.get('provider')} reachable={llm.get('reachable')} model={llm.get('model')}")

    if report.get("curriculum"):
        print(f"\n[Curriculum] {report['curriculum']}")

    # Short think demo when not smoke
    try:
        brain = None
        from core.service_registry import service_registry

        try:
            brain = service_registry.get("brain")
        except Exception:
            from brain import ThinkingBrain

            brain = ThinkingBrain(name=config.ai_name)
        result = brain.think("Leon kimdir?", reasoning_mode="auto")
        print("\n--- Think ---")
        print(f"Mode       : {result.get('reasoning_mode')}")
        print(f"Confidence : {result.get('confidence')}")
        print(f"LLM used   : {result.get('llm_used')}")
        print(f"Conclusion : {str(result.get('conclusion') or '')[:240]}")
    except Exception as e:
        print(f"\n[Think] skipped: {e}")

    print("\n--- Shutdown ---")
    try:
        kernel.shutdown()
    except Exception:
        pass
    print(f"{config.ai_name} stopped.")
    print("=" * 64)
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
