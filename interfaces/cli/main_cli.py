"""Leon CLI – cognitive + omniverse + image + improve + mutate."""

import argparse
import sys
import json

from core.logger import logger
from core.kernel import kernel
from core.config import config


def parse_args():
    parser = argparse.ArgumentParser(description="Leon AI Platform CLI")
    sub = parser.add_subparsers(dest="command")

    start_p = sub.add_parser("start")
    start_p.add_argument("--bootstrap", action="store_true")
    start_p.add_argument("--volume", default="01")
    start_p.add_argument("--no-llm-check", action="store_true")
    start_p.add_argument("--json", action="store_true")

    sub.add_parser("smoke")
    sub.add_parser("health")
    save_p = sub.add_parser("save")
    save_p.add_argument("--name", default="leon")
    sub.add_parser("load")

    eval_p = sub.add_parser("eval")
    eval_p.add_argument("volume_id", nargs="?", default="01")
    eval_p.add_argument("--no-teach", action="store_true")
    eval_p.add_argument("--json", action="store_true")

    reason_p = sub.add_parser("reason")
    reason_p.add_argument("query", type=str)
    reason_p.add_argument("--strategy", default="auto")
    reason_p.add_argument("--goal", default=None)
    reason_p.add_argument("--no-brain", action="store_true")
    reason_p.add_argument("--json", action="store_true")

    think_p = sub.add_parser("think")
    think_p.add_argument("query", type=str)
    think_p.add_argument("--mode", default="auto", choices=["auto", "cot", "tot", "sot"])
    think_p.add_argument("--goal", default=None)
    think_p.add_argument("--agent", default=None)
    think_p.add_argument("--experimental", action="store_true")
    think_p.add_argument("--json", action="store_true")

    ret_p = sub.add_parser("retrieve")
    ret_p.add_argument("query", type=str)
    ret_p.add_argument("--top-k", type=int, default=8)
    ret_p.add_argument("--json", action="store_true")

    q_p = sub.add_parser("quarantine")
    q_p.add_argument("--accept", default=None)
    q_p.add_argument("--reject", default=None)

    agent_p = sub.add_parser("agent")
    agent_p.add_argument("type", nargs="?", default=None)
    agent_p.add_argument("task", nargs="?", default=None)
    agent_p.add_argument("--list", action="store_true")
    agent_p.add_argument("--experimental", action="store_true")
    agent_p.add_argument("--json", action="store_true")

    plan_p = sub.add_parser("plan")
    plan_sub = plan_p.add_subparsers(dest="plan_cmd")
    pc = plan_sub.add_parser("create")
    pc.add_argument("--goal", required=True)
    pc.add_argument("--curriculum", default=None)
    pc.add_argument("--json", action="store_true")
    plan_sub.add_parser("list")
    ps = plan_sub.add_parser("show")
    ps.add_argument("plan_id")
    ps.add_argument("--json", action="store_true")
    pr = plan_sub.add_parser("run")
    pr.add_argument("plan_id")
    pr.add_argument("--max-tasks", type=int, default=None)
    pr.add_argument("--json", action="store_true")
    pre = plan_sub.add_parser("replan")
    pre.add_argument("plan_id")
    pre.add_argument("--reason", default="user")
    pre.add_argument("--json", action="store_true")

    ov = sub.add_parser("omniverse", help="Leon ↔ Omniverse bridge")
    ov_sub = ov.add_subparsers(dest="ov_cmd")
    ov_sub.add_parser("status")
    ov_sub.add_parser("demo")
    ov_sub.add_parser("sync")
    ova = ov_sub.add_parser("ask")
    ova.add_argument("question", type=str)
    ova.add_argument("--json", action="store_true")
    ov_sub.add_parser("inject")

    img = sub.add_parser("image", help="Multimodal image ops")
    img_sub = img.add_subparsers(dest="img_cmd")
    img_sub.add_parser("status")
    ii = img_sub.add_parser("info")
    ii.add_argument("path")
    ii.add_argument("--json", action="store_true")
    ip = img_sub.add_parser("process")
    ip.add_argument("path")
    ip.add_argument("--op", default="thumbnail")
    ip.add_argument("--width", type=int, default=256)
    ip.add_argument("--height", type=int, default=256)
    ip.add_argument("--json", action="store_true")
    idesc = img_sub.add_parser("describe")
    idesc.add_argument("path")
    idesc.add_argument("--prompt", default="Bu şəkli qısa və dəqiq təsvir et.")
    idesc.add_argument("--json", action="store_true")
    iund = img_sub.add_parser("understand")
    iund.add_argument("path")
    iund.add_argument("--question", default=None)
    iund.add_argument("--no-vlm", action="store_true")
    iund.add_argument("--inject", action="store_true")
    iund.add_argument("--json", action="store_true")
    igen = img_sub.add_parser("generate")
    igen.add_argument("--prompt", default="leon abstract")
    igen.add_argument(
        "--style",
        default="auto",
        choices=["auto", "gradient", "noise", "shapes", "grid", "waves", "scene"],
    )
    igen.add_argument("--width", type=int, default=512)
    igen.add_argument("--height", type=int, default=512)
    igen.add_argument("--seed", type=int, default=None)
    igen.add_argument("--json", action="store_true")

    imp = sub.add_parser("improve", help="Self-improvement cycle")
    imp_sub = imp.add_subparsers(dest="imp_cmd")
    idg = imp_sub.add_parser("diagnose")
    idg.add_argument("--volumes", default="01,02")
    irun = imp_sub.add_parser("run")
    irun.add_argument("--volumes", default="01,02")
    irun.add_argument("--dry-run", action="store_true")
    irun.add_argument("--with-mutate", action="store_true")
    iauto = imp_sub.add_parser("auto")
    iauto.add_argument("--volumes", default="01,02")
    iauto.add_argument("--rounds", type=int, default=3)
    iauto.add_argument("--target", type=float, default=0.95)
    iauto.add_argument("--with-mutate", action="store_true")
    iauto.add_argument("--dry-run", action="store_true")
    imp_sub.add_parser("status")

    mut = sub.add_parser("mutate", help="Controlled source self-mutation")
    mut_sub = mut.add_subparsers(dest="mut_cmd")
    mut_sub.add_parser("status")
    mp = mut_sub.add_parser("propose")
    mp.add_argument("--path", default=None)
    mp.add_argument("--mode", default="replace", choices=["replace", "append", "write"])
    mp.add_argument("--old", default=None)
    mp.add_argument("--new", default=None)
    mp.add_argument("--content", default=None)
    mp.add_argument("--reason", default="")
    mp.add_argument("--goal", default=None)
    mp.add_argument("--candidates", type=int, default=3)
    mp.add_argument("--strategy", default=None, help="train_enrich|docstring_boost|...")
    ms = mut_sub.add_parser("smart")
    ms.add_argument("--goal", default=None)
    ms.add_argument("--apply", action="store_true")
    ms.add_argument("--no-diagnose", action="store_true")
    me = mut_sub.add_parser("evolve")
    me.add_argument("--rounds", type=int, default=2)
    me.add_argument("--apply", action="store_true")
    me.add_argument("--goal", default=None)
    me.add_argument("--min-quality", type=float, default=40.0)
    mut_sub.add_parser("diagnose")
    mroute = mut_sub.add_parser("route")
    mroute.add_argument("--goal", required=True)
    ml = mut_sub.add_parser("list")
    ml.add_argument("--limit", type=int, default=20)
    mut_sub.add_parser("strategies")
    ma = mut_sub.add_parser("apply")
    ma.add_argument("proposal_id", nargs="?", default=None)
    ma.add_argument("--no-smoke", action="store_true")
    mr = mut_sub.add_parser("rollback")
    mr.add_argument("mutation_id")

    teach_p = sub.add_parser("teach")
    teach_p.add_argument("lesson_id", nargs="?", default="000001")
    teach_p.add_argument("--volume", default=None)
    teach_p.add_argument("--json", action="store_true")

    tv = sub.add_parser("teach-volume")
    tv.add_argument("volume_id", nargs="?", default="01")
    tv.add_argument("--json", action="store_true")

    sub.add_parser("volumes")
    sub.add_parser("lessons")
    sub.add_parser("status")
    sub.add_parser("info")
    sub.add_parser("llm-check")

    return parser.parse_args()


def _print_reason(result: dict):
    print(f"Answer     : {result.get('answer') or result.get('conclusion')}")
    print(f"Confidence : {result.get('confidence')} ({result.get('confidence_label')})")
    print(f"Source     : {result.get('source')}")
    print(f"Trace ID   : {result.get('trace_id')}")


def _vols(s: str):
    return [v.strip() for v in (s or "01").split(",") if v.strip()]


class CLIController:
    def cmd_start(self, args):
        from core.bootstrap import start_leon

        report = start_leon(
            bootstrap_curriculum=args.bootstrap,
            volume_id=args.volume,
            check_llm=not args.no_llm_check,
            load_persisted=True,
        )
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
            return
        for step in report.get("steps") or []:
            print(f"[{'OK' if step.get('ok') else 'FAIL'}] {step.get('step')}")

    def cmd_smoke(self):
        from core.bootstrap import smoke_test

        print(json.dumps(smoke_test(), ensure_ascii=False, indent=2, default=str))

    def cmd_health(self):
        from interfaces.api.health import health_report

        print(json.dumps(health_report(), ensure_ascii=False, indent=2, default=str))

    def cmd_save(self, args):
        from core.bootstrap import save_state

        print(save_state(name=args.name))

    def cmd_load(self):
        from core.bootstrap import load_state

        print(json.dumps(load_state(), ensure_ascii=False, indent=2, default=str))

    def cmd_eval(self, args):
        from evaluation.runner import evaluate_curriculum

        report = evaluate_curriculum(args.volume_id, teach_first=not args.no_teach)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
            return
        print(f"Pass rate : {report.get('pass_rate')}")

    def cmd_reason(self, args):
        from brain.reasoning.engine import reasoning_engine

        result = reasoning_engine.reason(
            args.query, strategy=args.strategy, goal=args.goal, use_brain=not args.no_brain
        )
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            return
        _print_reason(result)

    def cmd_think(self, args):
        from brain.orchestrator import BrainOrchestrator

        orch = BrainOrchestrator(brain_name=config.ai_name)
        result = orch.run(
            args.query,
            goal=args.goal,
            reasoning_mode=args.mode,
            agent_type=args.agent,
            allow_experimental_agent=args.experimental,
        )
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            return
        _print_reason(result)

    def cmd_retrieve(self, args):
        from memory.retrieve import retrieve

        report = retrieve(args.query, top_k=args.top_k)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
            return
        for c in report.get("candidates") or []:
            print(f"  [{c.get('source')}|{c.get('score')}] {c.get('content')[:100]}")

    def cmd_quarantine(self, args):
        from learning.engine import LearningEngine

        eng = LearningEngine()
        if args.accept:
            rec = eng.validate_record(args.accept, accept=True)
            print(rec.to_dict() if rec else {"error": "not found"})
            return
        if args.reject:
            rec = eng.validate_record(args.reject, accept=False)
            print(rec.to_dict() if rec else {"error": "not found"})
            return
        print(
            json.dumps(
                {"quarantine": eng.quarantine_list(), "pending": eng.pending_list()},
                ensure_ascii=False,
                indent=2,
            )
        )

    def cmd_agent(self, args):
        from agents.manager import agent_manager

        if args.list or not args.type:
            for d in agent_manager.list_types_detailed():
                flag = "PROD" if d.get("production") else "EXP"
                print(f"  [{flag}] {d.get('type')}")
            return
        if not args.task:
            print("agent <type> <task>")
            sys.exit(1)
        agent = agent_manager.create(
            args.type, allow_experimental=args.experimental or args.type in ("react", "coding")
        )
        res = agent_manager.run(agent.id, args.task)
        if args.json:
            print(
                json.dumps(
                    {"success": res.success, "output": res.output, "error": res.error},
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
            )
            return
        print(f"Success: {res.success}\nOutput: {res.output}")

    def cmd_plan(self, args):
        from brain.planning import Planner, curriculum_learn_plan

        p = Planner()
        cmd = args.plan_cmd
        if cmd == "create":
            plan = (
                curriculum_learn_plan(args.curriculum)
                if args.curriculum
                else p.create(goal=args.goal)
            )
            if args.json:
                print(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2, default=str))
            else:
                print(f"Created {plan.id} tasks={len(plan.tasks)}")
            return
        if cmd == "list":
            for row in p.list_plans():
                print(f"{row.get('id')} [{row.get('status')}] | {row.get('goal')}")
            return
        if cmd == "show":
            plan = p.get(args.plan_id)
            if not plan:
                print("not found")
                sys.exit(1)
            if args.json:
                print(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2, default=str))
                return
            print(f"{plan.id} [{plan.status}]")
            for t in p.ordered_tasks(plan):
                print(f"  {t.id} [{t.status}] {t.action} | {t.title}")
            return
        if cmd == "run":
            report = p.run(args.plan_id, max_tasks=args.max_tasks)
            if args.json:
                print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
                return
            print(f"Plan {report.get('plan_id')} → {report.get('status')}")
            return
        if cmd == "replan":
            plan = p.replan(args.plan_id, reason=args.reason)
            print(f"Replanned {plan.id if plan else '?'}")
            return
        print("plan create|list|show|run|replan")

    def cmd_omniverse(self, args):
        from integrations.omniverse import OmniverseBridge

        ov = OmniverseBridge()
        cmd = args.ov_cmd
        if cmd == "status" or cmd is None:
            print(json.dumps(ov.status(), ensure_ascii=False, indent=2))
            return
        if cmd == "demo":
            print(json.dumps(ov.load_stub_demo_scene(), ensure_ascii=False, indent=2))
            print(json.dumps(ov.describe_scene(), ensure_ascii=False, indent=2))
            return
        if cmd == "sync":
            print(json.dumps(ov.sync_from_stage(), ensure_ascii=False, indent=2))
            return
        if cmd == "inject":
            n = ov.inject_scene_facts()
            print(json.dumps({"injected": n, "status": ov.status()}, ensure_ascii=False, indent=2))
            return
        if cmd == "ask":
            if not ov.list_objects():
                ov.load_stub_demo_scene()
            result = ov.ask_leon(args.question)
            if getattr(args, "json", False):
                print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
                return
            _print_reason(result)
            print(f"OV mode   : {(result.get('omniverse') or {}).get('mode')}")
            print(f"Objects   : {result.get('scene_object_count')}")
            return
        print("omniverse status|demo|sync|inject|ask")

    def cmd_image(self, args):
        cmd = args.img_cmd
        if cmd == "status" or cmd is None:
            from multimodal.image_ops import list_supported
            from multimodal.vision import vision_available

            print(
                json.dumps(
                    {"pillow": list_supported(), "vision": vision_available()},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return
        if cmd == "info":
            from multimodal.image_ops import image_info

            out = image_info(args.path)
            print(json.dumps(out, ensure_ascii=False, indent=2) if args.json else out)
            return
        if cmd == "process":
            from multimodal.image_ops import process_image

            out = process_image(args.path, op=args.op, width=args.width, height=args.height)
            print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
            return
        if cmd == "describe":
            from multimodal.vision import describe_image

            out = describe_image(args.path, prompt=args.prompt)
            print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
            return
        if cmd == "understand":
            from multimodal.understand import understand_image

            out = understand_image(
                args.path,
                question=args.question,
                use_vlm=not args.no_vlm,
                inject_facts=args.inject,
            )
            print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
            return
        if cmd == "generate":
            from multimodal.generate import generate_image

            out = generate_image(
                prompt=args.prompt,
                style=args.style,
                width=args.width,
                height=args.height,
                seed=args.seed,
            )
            print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
            return
        print("image status|info|process|describe|understand|generate")

    def cmd_improve(self, args):
        from brain.self_improve import SelfImproveEngine, improve, improve_auto

        eng = SelfImproveEngine()
        cmd = args.imp_cmd
        if cmd == "status" or cmd is None:
            print(json.dumps(eng.status(), ensure_ascii=False, indent=2, default=str))
            return
        if cmd == "diagnose":
            out = eng.diagnose(volumes=_vols(args.volumes))
            print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
            return
        if cmd == "run":
            out = improve(
                volumes=_vols(args.volumes),
                dry_run=args.dry_run,
                with_mutate=bool(getattr(args, "with_mutate", False)),
            )
            print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
            return
        if cmd == "auto":
            out = improve_auto(
                volumes=_vols(args.volumes),
                rounds=args.rounds,
                target=args.target,
                with_mutate=bool(getattr(args, "with_mutate", False)),
                dry_run=args.dry_run,
            )
            print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
            return
        print("improve diagnose|run|auto|status")

    def cmd_mutate(self, args):
        from interfaces.cli.mutate_cli import run_mutate

        run_mutate(args)

    def cmd_teach(self, args):
        from curriculum import CurriculumEngine
        from core.bootstrap import save_state

        eng = CurriculumEngine()
        report = eng.teach(args.lesson_id, volume_id=getattr(args, "volume", None))
        try:
            save_state("after_teach")
        except Exception:
            pass
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
            return
        st = report.get("self_test") or {}
        print(f"{report.get('name')}: {st.get('passed')}/{st.get('total')}")

    def cmd_teach_volume(self, args):
        from curriculum import CurriculumEngine
        from core.bootstrap import save_state

        eng = CurriculumEngine()
        report = eng.teach_volume(args.volume_id)
        try:
            save_state("after_teach_volume")
        except Exception:
            pass
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
            return
        print(f"Lessons {report.get('lessons_passed')}/{report.get('lessons_total')}")

    def cmd_volumes(self):
        from curriculum import CurriculumEngine, load_volume

        eng = CurriculumEngine()
        for vid in eng.list_volumes():
            try:
                m = load_volume(vid)
                print(f"{m.get('volume')} | {m.get('name')}")
            except Exception as e:
                print(vid, e)

    def cmd_lessons(self):
        from curriculum import CurriculumEngine

        print(CurriculumEngine().list_available())

    def cmd_status(self):
        from core.bootstrap import leon_status

        print(json.dumps(leon_status(), ensure_ascii=False, indent=2, default=str))

    def cmd_info(self):
        kernel.initialize()
        print(f"{config.ai_name} | {config.path.leon_dir}")

    def cmd_llm_check(self):
        from brain.llm.client import get_llm_client

        print(json.dumps(get_llm_client(force_new=True).health_check(), ensure_ascii=False, indent=2))


def main():
    args = parse_args()
    ctrl = CLIController()
    try:
        cmd = args.command
        if cmd == "plan":
            ctrl.cmd_plan(args)
            return
        if cmd == "omniverse":
            ctrl.cmd_omniverse(args)
            return
        if cmd == "image":
            ctrl.cmd_image(args)
            return
        if cmd == "improve":
            ctrl.cmd_improve(args)
            return
        if cmd == "mutate":
            ctrl.cmd_mutate(args)
            return
        mapping = {
            "start": lambda: ctrl.cmd_start(args),
            "smoke": ctrl.cmd_smoke,
            "health": ctrl.cmd_health,
            "save": lambda: ctrl.cmd_save(args),
            "load": ctrl.cmd_load,
            "eval": lambda: ctrl.cmd_eval(args),
            "reason": lambda: ctrl.cmd_reason(args),
            "think": lambda: ctrl.cmd_think(args),
            "retrieve": lambda: ctrl.cmd_retrieve(args),
            "quarantine": lambda: ctrl.cmd_quarantine(args),
            "agent": lambda: ctrl.cmd_agent(args),
            "teach": lambda: ctrl.cmd_teach(args),
            "teach-volume": lambda: ctrl.cmd_teach_volume(args),
            "volumes": ctrl.cmd_volumes,
            "lessons": ctrl.cmd_lessons,
            "status": ctrl.cmd_status,
            "info": ctrl.cmd_info,
            "llm-check": ctrl.cmd_llm_check,
        }
        if cmd not in mapping:
            print("Leon CLI – --help")
            sys.exit(1)
        mapping[cmd]()
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
