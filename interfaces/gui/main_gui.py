"""
Leon GUI – yalnız işlək tablar: Think | Teach | Status (Faza 7).
"""

from __future__ import annotations

import json
import queue
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Any, Dict, Optional

from core.logger import logger
from interfaces.gui.command_center import infer_operation_mode


class LeonApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Zenthon AI Command Center")
        self.root.geometry("1180x760")
        self.root.minsize(920, 620)
        self._orch = None
        self.log_queue: queue.Queue = queue.Queue()
        self.mission_events: list[dict[str, str]] = [
            {"label": "Command center ready", "detail": "Local-first operator surface initialized", "tone": "core"}
        ]

        self._configure_styles()
        self._create_command_header()
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 12))
        self._create_menu()
        self._create_notebook()
        self._create_status_bar()
        self.root.after(100, self._process_log_queue)
        logger.info("Leon GUI initialized (Faza 7)")

    def _orch_lazy(self):
        if self._orch is None:
            from brain.orchestrator import BrainOrchestrator
            from core.config import config

            self._orch = BrainOrchestrator(brain_name=getattr(config, "ai_name", "Leon") or "Leon")
        return self._orch

    def _configure_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(".", background="#06101D", foreground="#E8F4FF")
        style.configure("TFrame", background="#06101D")
        style.configure("Panel.TFrame", background="#0A1D30")
        style.configure("TLabel", background="#06101D", foreground="#D7E8FA")
        style.configure("Hud.TLabel", background="#071625", foreground="#74E7B6", font=("Segoe UI", 9, "bold"))
        style.configure("Title.TLabel", background="#071625", foreground="#F2F7FF", font=("Segoe UI", 18, "bold"))
        style.configure("Subtitle.TLabel", background="#071625", foreground="#8FA9C4", font=("Segoe UI", 9))
        style.configure("TButton", padding=7, background="#0C2237", foreground="#DDF0FF", bordercolor="#23506F")
        style.map("TButton", background=[("active", "#143954")], foreground=[("active", "#FFFFFF")])
        style.configure("Accent.TButton", background="#70E6B1", foreground="#06201A", font=("Segoe UI", 9, "bold"))
        style.map("Accent.TButton", background=[("active", "#8AF4C7")])
        style.configure("TNotebook", background="#06101D", borderwidth=0)
        style.configure("TNotebook.Tab", background="#0C2237", foreground="#91A9C4", padding=(13, 8), font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#123E46")], foreground=[("selected", "#70E6B1")])
        style.configure("TLabelframe", background="#06101D", bordercolor="#204967", relief="solid")
        style.configure("TLabelframe.Label", background="#06101D", foreground="#79A2C8", font=("Segoe UI", 9, "bold"))

    def _create_command_header(self) -> None:
        header = ttk.Frame(self.root, style="Panel.TFrame")
        header.pack(fill=tk.X, padx=14, pady=(12, 10))
        identity = ttk.Frame(header, style="Panel.TFrame")
        identity.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=14, pady=11)
        ttk.Label(identity, text="ZENTHON / AI COMMAND CENTER", style="Hud.TLabel").pack(anchor=tk.W)
        ttk.Label(identity, text="Local AI operator surface", style="Title.TLabel").pack(anchor=tk.W, pady=(2, 1))
        ttk.Label(identity, text="Mission plan · agent execution · safe improvement observability", style="Subtitle.TLabel").pack(anchor=tk.W)
        status = ttk.Frame(header, style="Panel.TFrame")
        status.pack(side=tk.RIGHT, padx=14, pady=14)
        self.header_status = ttk.Label(status, text="● LOCAL CORE READY", style="Hud.TLabel")
        self.header_status.pack(anchor=tk.E)
        self.native_status = ttk.Label(status, text=self._native_core_status_text(), style="Subtitle.TLabel")
        self.native_status.pack(anchor=tk.E, pady=(3, 0))

    @staticmethod
    def _native_core_status_text() -> str:
        try:
            from native_core import health_report

            report = health_report()
            source = "native binary" if report.get("available") else "Python fallback"
            return f"Native Core · {source}"
        except Exception:
            return "Native Core · unavailable"

    def _create_menu(self) -> None:
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._on_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)

    def _create_notebook(self) -> None:
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self._create_command_center_tab()
        self._create_think_tab()
        self._create_teach_tab()
        self._create_improve_tab()
        self._create_status_tab()

    def _create_command_center_tab(self) -> None:
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Command Center")

        mission = ttk.LabelFrame(frame, text="Live Mission")
        mission.pack(fill=tk.X, padx=8, pady=(8, 6))
        mission.columnconfigure(0, weight=1)
        self.command_mode = ttk.Label(mission, text="Reasoning Operation", foreground="#70E6B1", font=("Segoe UI", 12, "bold"))
        self.command_mode.grid(row=0, column=0, sticky=tk.W, padx=12, pady=(10, 2))
        self.command_objective = ttk.Label(mission, text="Write an objective to begin a controlled mission.", foreground="#9EB6CF")
        self.command_objective.grid(row=1, column=0, sticky=tk.W, padx=12, pady=(0, 10))
        self.command_state = ttk.Label(mission, text="● STANDBY", foreground="#56D8FF", font=("Segoe UI", 8, "bold"))
        self.command_state.grid(row=0, column=1, rowspan=2, sticky=tk.E, padx=12)

        stages = ttk.LabelFrame(frame, text="Execution Trace")
        stages.pack(fill=tk.X, padx=8, pady=6)
        self.command_canvas = tk.Canvas(stages, height=104, bg="#0A1D30", highlightthickness=0)
        self.command_canvas.pack(fill=tk.X, padx=8, pady=8)
        self._draw_command_stages(active_index=-1, complete=False)

        work = ttk.Frame(frame)
        work.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        work.columnconfigure(0, weight=5)
        work.columnconfigure(1, weight=4)
        work.rowconfigure(0, weight=1)

        prompt_box = ttk.LabelFrame(work, text="Mission Input")
        prompt_box.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 5))
        self.command_query = scrolledtext.ScrolledText(
            prompt_box, height=10, wrap=tk.WORD, bg="#0A1D30", fg="#E8F4FF", insertbackground="#70E6B1",
            relief=tk.FLAT, padx=10, pady=10,
        )
        self.command_query.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        command_controls = ttk.Frame(prompt_box)
        command_controls.pack(fill=tk.X, padx=8, pady=(0, 8))
        ttk.Button(command_controls, text="Run Mission", style="Accent.TButton", command=self._on_command_run).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(command_controls, text="Use Think Tab", command=lambda: self.notebook.select(1)).pack(side=tk.LEFT, padx=6)
        ttk.Button(command_controls, text="Clear", command=self._on_command_clear).pack(side=tk.RIGHT)

        event_box = ttk.LabelFrame(work, text="Mission Events")
        event_box.grid(row=0, column=1, sticky=tk.NSEW, padx=(5, 0))
        self.command_events = scrolledtext.ScrolledText(
            event_box, height=10, wrap=tk.WORD, state=tk.DISABLED, bg="#0A1D30", fg="#BFD5EA", relief=tk.FLAT, padx=10, pady=10,
        )
        self.command_events.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._refresh_command_events()

        result = ttk.LabelFrame(frame, text="Result & Confidence")
        result.pack(fill=tk.BOTH, expand=True, padx=8, pady=(6, 8))
        self.command_output = scrolledtext.ScrolledText(
            result, wrap=tk.WORD, bg="#071625", fg="#DCEBFA", insertbackground="#70E6B1", relief=tk.FLAT, padx=10, pady=10,
        )
        self.command_output.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._set_text(self.command_output, "Zenthon is standing by. Each mission exposes its operation mode, stages, result source, and confidence.\n")

    def _draw_command_stages(self, active_index: int, complete: bool) -> None:
        canvas = self.command_canvas
        canvas.delete("all")
        stages = [
            ("Intake", "objective accepted"),
            ("Intent", "skill selected"),
            ("Reason", "agent executes"),
            ("Deliver", "result verified"),
        ]
        width = max(canvas.winfo_width(), 820)
        step = (width - 36) / len(stages)
        for index, (label, detail) in enumerate(stages):
            x1, x2 = 18 + index * step, 18 + (index + 1) * step - 12
            if complete or index < active_index:
                color, text_color = "#174D4C", "#86F1C3"
            elif index == active_index:
                color, text_color = "#173E5C", "#75D9FF"
            else:
                color, text_color = "#16283B", "#7892AE"
            canvas.create_rectangle(x1, 18, x2, 75, fill=color, outline="#2B6680", width=1)
            canvas.create_text((x1 + x2) / 2, 39, text=label, fill=text_color, font=("Segoe UI", 10, "bold"))
            canvas.create_text((x1 + x2) / 2, 58, text=detail, fill="#B2C5D9", font=("Segoe UI", 8))
            if index < len(stages) - 1:
                canvas.create_line(x2 + 2, 46, x2 + 10, 46, fill="#587692", width=2, arrow=tk.LAST)
        status = "MISSION COMPLETE" if complete else ("STANDBY" if active_index < 0 else f"ACTIVE: {stages[active_index][0].upper()}")
        canvas.create_text(18, 92, text=status, anchor=tk.W, fill="#7FA8C9", font=("Segoe UI", 8, "bold"))

    def _append_mission_event(self, label: str, detail: str) -> None:
        self.mission_events.insert(0, {"label": label, "detail": detail, "tone": "core"})
        self.mission_events = self.mission_events[:8]
        self._refresh_command_events()

    def _refresh_command_events(self) -> None:
        if not hasattr(self, "command_events"):
            return
        self.command_events.config(state=tk.NORMAL)
        self.command_events.delete("1.0", tk.END)
        for event in self.mission_events:
            self.command_events.insert(tk.END, f"● {event['label']}\n", ("label",))
            self.command_events.insert(tk.END, f"  {event['detail']}\n\n")
        self.command_events.tag_configure("label", foreground="#70E6B1", font=("Segoe UI", 9, "bold"))
        self.command_events.config(state=tk.DISABLED)

    def _on_command_clear(self) -> None:
        self.command_query.delete("1.0", tk.END)
        self._set_text(self.command_output, "Mission input cleared. Zenthon is standing by.\n")
        self.command_mode.config(text="Reasoning Operation")
        self.command_objective.config(text="Write an objective to begin a controlled mission.")
        self.command_state.config(text="● STANDBY", foreground="#56D8FF")
        self._draw_command_stages(active_index=-1, complete=False)
        self._append_mission_event("Mission reset", "Context cleared from the operator surface")

    def _on_command_run(self) -> None:
        query = self.command_query.get("1.0", tk.END).strip()
        if not query:
            messagebox.showwarning("Zenthon", "Write a mission objective first.")
            return
        mode = infer_operation_mode(query)
        self.command_mode.config(text=mode)
        self.command_objective.config(text=query[:150] + ("…" if len(query) > 150 else ""))
        self.command_state.config(text="● EXECUTING", foreground="#56D8FF")
        self._draw_command_stages(active_index=1, complete=False)
        self._set_text(self.command_output, "Mission accepted. Intent mapping and agent routing are in progress…\n")
        self._append_mission_event("Mission accepted", mode)
        self._log(f"Command mission started: {mode}")

        def worker():
            try:
                self.root.after(0, lambda: self._draw_command_stages(active_index=2, complete=False))
                result = self._orch_lazy().run(query, reasoning_mode="auto", use_session=True)
                text = (
                    f"Operation : {mode}\n"
                    f"Answer    : {result.get('answer') or result.get('conclusion')}\n"
                    f"Confidence: {result.get('confidence')} ({result.get('confidence_label')})\n"
                    f"Source    : {result.get('source')}\n"
                    f"Trace ID  : {result.get('trace_id')}\n"
                    f"LLM used  : {result.get('llm_used')}\n"
                )
                if result.get("agent"):
                    text += f"\nAgent trace:\n{json.dumps(result['agent'], ensure_ascii=False, indent=2, default=str)}\n"
                self.root.after(0, lambda: self._set_text(self.command_output, text))
                self.root.after(0, lambda: self.command_state.config(text="● RESULT READY", foreground="#70E6B1"))
                self.root.after(0, lambda: self._draw_command_stages(active_index=3, complete=True))
                self.root.after(0, lambda: self._append_mission_event("Result ready", f"Source: {result.get('source')} · Confidence: {result.get('confidence')}"))
                self.root.after(0, lambda: self._log("Command mission complete"))
            except Exception as e:
                self.root.after(0, lambda: self._set_text(self.command_output, f"Mission error: {e}"))
                self.root.after(0, lambda: self.command_state.config(text="● ATTENTION REQUIRED", foreground="#F6C760"))
                self.root.after(0, lambda: self._draw_command_stages(active_index=1, complete=False))
                self.root.after(0, lambda: self._append_mission_event("Mission paused", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _create_think_tab(self) -> None:
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Think")

        top = ttk.LabelFrame(frame, text="Leon · Reasoning")
        top.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(top, text="Sual:").grid(row=0, column=0, sticky=tk.W, padx=4, pady=4)
        self.think_query = scrolledtext.ScrolledText(top, height=4, wrap=tk.WORD)
        self.think_query.grid(row=0, column=1, columnspan=3, sticky=tk.EW, padx=4, pady=4)

        ttk.Label(top, text="Mode:").grid(row=1, column=0, sticky=tk.W, padx=4)
        self.think_mode = ttk.Combobox(top, values=["auto", "cot", "tot", "sot"], width=12)
        self.think_mode.set("auto")
        self.think_mode.grid(row=1, column=1, sticky=tk.W, padx=4)

        ttk.Label(top, text="Agent:").grid(row=1, column=2, sticky=tk.W, padx=4)
        self.think_agent = ttk.Combobox(top, values=["", "react", "coding"], width=12)
        self.think_agent.set("")
        self.think_agent.grid(row=1, column=3, sticky=tk.W, padx=4)

        btn = ttk.Frame(top)
        btn.grid(row=2, column=0, columnspan=4, pady=8)
        ttk.Button(btn, text="Think", command=self._on_think).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn, text="Clear", command=self._on_think_clear).pack(side=tk.LEFT, padx=4)
        top.columnconfigure(1, weight=1)
        top.columnconfigure(3, weight=1)

        out = ttk.LabelFrame(frame, text="Nəticə")
        out.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.think_output = scrolledtext.ScrolledText(out, wrap=tk.WORD)
        self.think_output.pack(fill=tk.BOTH, expand=True)

    def _create_teach_tab(self) -> None:
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Teach")

        form = ttk.LabelFrame(frame, text="Curriculum")
        form.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(form, text="Volume:").grid(row=0, column=0, padx=4, pady=4)
        self.teach_volume = ttk.Combobox(form, values=["01", "02"], width=8)
        self.teach_volume.set("01")
        self.teach_volume.grid(row=0, column=1, padx=4)

        ttk.Label(form, text="Lesson ID:").grid(row=0, column=2, padx=4)
        self.teach_lesson = ttk.Entry(form, width=12)
        self.teach_lesson.insert(0, "000001")
        self.teach_lesson.grid(row=0, column=3, padx=4)

        btn = ttk.Frame(form)
        btn.grid(row=1, column=0, columnspan=4, pady=8)
        ttk.Button(btn, text="Teach Lesson", command=self._on_teach_lesson).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn, text="Teach Volume", command=self._on_teach_volume).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn, text="Eval Volume", command=self._on_eval_volume).pack(side=tk.LEFT, padx=4)

        out = ttk.LabelFrame(frame, text="Hesabat")
        out.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.teach_output = scrolledtext.ScrolledText(out, wrap=tk.WORD)
        self.teach_output.pack(fill=tk.BOTH, expand=True)

    def _create_status_tab(self) -> None:
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Status")

        btn = ttk.Frame(frame)
        btn.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(btn, text="Refresh Status", command=self._on_status).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn, text="Health", command=self._on_health).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn, text="LLM Check", command=self._on_llm).pack(side=tk.LEFT, padx=4)

        self.status_output = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
        self.status_output.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _create_improve_tab(self) -> None:
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Improve")

        controls = ttk.Frame(frame)
        controls.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(controls, text="Refresh Cycle", command=self._on_improve_refresh).pack(side=tk.LEFT, padx=4)
        ttk.Button(controls, text="Run Safe Simulation", command=self._on_improve_simulate).pack(side=tk.LEFT, padx=4)
        self.improve_summary = ttk.Label(controls, text="Cycle status yüklənir…")
        self.improve_summary.pack(side=tk.LEFT, padx=12)

        graph_box = ttk.LabelFrame(frame, text="Self-Improvement Cycle")
        graph_box.pack(fill=tk.X, padx=8, pady=8)
        self.improve_canvas = tk.Canvas(graph_box, height=150, bg="#17212b", highlightthickness=0)
        self.improve_canvas.pack(fill=tk.X, padx=8, pady=8)

        detail = ttk.LabelFrame(frame, text="Audit & Decision Details")
        detail.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.improve_output = scrolledtext.ScrolledText(detail, wrap=tk.WORD)
        self.improve_output.pack(fill=tk.BOTH, expand=True)
        self._draw_improve_cycle({})
        self._on_improve_refresh()

    def _draw_improve_cycle(self, data: Dict[str, Any]) -> None:
        canvas = self.improve_canvas
        canvas.delete("all")
        stages = [
            ("Diagnose", bool(data.get("diagnosis")), "Zəif hallar"),
            ("Propose", bool(data.get("proposal")), "Namizədlər"),
            ("Quality Gate", data.get("quality_ok") is True, "≥ 55 skor"),
            ("Apply", bool(data.get("applied")), "İcazəli yazma"),
            ("Verify", data.get("verified") is True, "Smoke / test"),
            ("Rollback", bool(data.get("rolled_back")), "Yalnız xəta"),
        ]
        width = max(canvas.winfo_width(), 880)
        step = (width - 40) / len(stages)
        for index, (name, state, note) in enumerate(stages):
            x1, x2 = 20 + index * step, 20 + (index + 1) * step - 14
            color = "#22c55e" if state else "#475569"
            if name == "Rollback" and state:
                color = "#f59e0b"
            canvas.create_rectangle(x1, 30, x2, 105, fill=color, outline="#dbeafe", width=1)
            canvas.create_text((x1 + x2) / 2, 57, text=name, fill="white", font=("TkDefaultFont", 10, "bold"))
            canvas.create_text((x1 + x2) / 2, 81, text=note, fill="#e2e8f0", font=("TkDefaultFont", 8))
            if index < len(stages) - 1:
                canvas.create_line(x2 + 2, 67, x2 + 12, 67, fill="#94a3b8", width=2, arrow=tk.LAST)
        canvas.create_text(20, 128, anchor=tk.W, text="Yaşıl: təsdiqli mərhələ · Boz: gözləyir / tətbiq edilməyib · Sarı: rollback", fill="#cbd5e1")

    def _on_improve_refresh(self) -> None:
        def worker():
            try:
                from brain.self_improve import self_improve_engine
                from brain.self_mutate import self_mutate_engine

                improve = self_improve_engine.status()
                mutate = self_mutate_engine.status()
                last_apply = mutate.get("last_apply") or {}
                proposal = mutate.get("last_proposal") or {}
                diagnosis = improve.get("last_diagnose") or {}
                quality = (proposal.get("quality") or {}).get("score")
                data = {
                    "diagnosis": diagnosis,
                    "proposal": proposal,
                    "quality_ok": isinstance(quality, (int, float)) and quality >= 55,
                    "applied": last_apply.get("ok"),
                    "verified": last_apply.get("smoke", {}).get("ok") if isinstance(last_apply.get("smoke"), dict) else bool(last_apply.get("ok")),
                    "rolled_back": last_apply.get("rolled_back", False),
                }
                text = json.dumps({"diagnosis": diagnosis, "proposal": proposal, "last_apply": last_apply, "mutation_enabled": mutate.get("enabled")}, ensure_ascii=False, indent=2, default=str)
                self.root.after(0, lambda: self._draw_improve_cycle(data))
                self.root.after(0, lambda: self._set_text(self.improve_output, text))
                self.root.after(0, lambda: self.improve_summary.config(text=f"Quality: {quality if quality is not None else '—'} | Mutasiya: {'aktiv' if mutate.get('enabled') else 'qapalı'}"))
            except Exception as e:
                self.root.after(0, lambda: self._set_text(self.improve_output, f"Xəta: {e}"))
        threading.Thread(target=worker, daemon=True).start()

    def _on_improve_simulate(self) -> None:
        self._set_text(self.improve_output, "Təhlükəsiz simulyasiya işləyir…\n")
        def worker():
            try:
                from brain.self_improve import self_improve_engine
                from brain.self_mutate import self_mutate_engine

                result = {"self_improve": self_improve_engine.auto(rounds=1, dry_run=True), "mutation": self_mutate_engine.auto_cycle(apply_best=False)}
                self.root.after(0, lambda: self._set_text(self.improve_output, json.dumps(result, ensure_ascii=False, indent=2, default=str)))
                self.root.after(0, self._on_improve_refresh)
            except Exception as e:
                self.root.after(0, lambda: self._set_text(self.improve_output, f"Xəta: {e}"))
        threading.Thread(target=worker, daemon=True).start()

    def _create_status_bar(self) -> None:
        self.status_bar = ttk.Label(self.root, text="Zenthon Command Center · Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _process_log_queue(self) -> None:
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.status_bar.config(text=msg[:120])
        except queue.Empty:
            pass
        self.root.after(150, self._process_log_queue)

    def _log(self, msg: str) -> None:
        self.log_queue.put(msg)

    def _set_text(self, widget: scrolledtext.ScrolledText, text: str) -> None:
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)

    def _on_think(self) -> None:
        query = self.think_query.get("1.0", tk.END).strip()
        if not query:
            messagebox.showwarning("Leon", "Sual yazın")
            return
        mode = self.think_mode.get() or "auto"
        agent = self.think_agent.get().strip() or None
        self._set_text(self.think_output, "Leon düşünür...\n")
        self._log(f"Think mode={mode}")

        def worker():
            try:
                result = self._orch_lazy().run(
                    query,
                    reasoning_mode=mode,
                    agent_type=agent,
                    use_session=True,
                )
                text = (
                    f"Answer     : {result.get('answer') or result.get('conclusion')}\n"
                    f"Confidence : {result.get('confidence')} ({result.get('confidence_label')})\n"
                    f"Source     : {result.get('source')}\n"
                    f"Trace ID   : {result.get('trace_id')}\n"
                    f"LLM used   : {result.get('llm_used')}\n"
                    f"Decision   : {(result.get('decision') or {}).get('action')}\n"
                )
                if result.get("evidence"):
                    text += "\nEvidence:\n"
                    for e in result["evidence"][:8]:
                        text += f"  [{e.get('kind')}] {str(e.get('content'))[:120]}\n"
                if result.get("agent"):
                    text += f"\nAgent:\n{json.dumps(result['agent'], ensure_ascii=False, indent=2, default=str)}\n"
                self.root.after(0, lambda: self._set_text(self.think_output, text))
                self.root.after(0, lambda: self._log("Think OK"))
            except Exception as e:
                self.root.after(0, lambda: self._set_text(self.think_output, f"Xəta: {e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_think_clear(self) -> None:
        self.think_query.delete("1.0", tk.END)
        self.think_output.delete("1.0", tk.END)

    def _on_teach_lesson(self) -> None:
        lid = self.teach_lesson.get().strip() or "000001"
        vid = self.teach_volume.get().strip() or "01"
        self._set_text(self.teach_output, f"Teaching {lid}...\n")

        def worker():
            try:
                from curriculum import CurriculumEngine
                from core.bootstrap import save_state

                eng = CurriculumEngine()
                report = eng.teach(lid, volume_id=vid)
                try:
                    save_state("gui_teach")
                except Exception:
                    pass
                text = json.dumps(report, ensure_ascii=False, indent=2, default=str)
                self.root.after(0, lambda: self._set_text(self.teach_output, text))
                self.root.after(0, lambda: self._log(f"Taught {lid}"))
            except Exception as e:
                self.root.after(0, lambda: self._set_text(self.teach_output, str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_teach_volume(self) -> None:
        vid = self.teach_volume.get().strip() or "01"
        self._set_text(self.teach_output, f"Teaching volume {vid}...\n")

        def worker():
            try:
                from curriculum import CurriculumEngine
                from core.bootstrap import save_state

                report = CurriculumEngine().teach_volume(vid)
                try:
                    save_state("gui_teach_volume")
                except Exception:
                    pass
                text = json.dumps(report, ensure_ascii=False, indent=2, default=str)
                self.root.after(0, lambda: self._set_text(self.teach_output, text))
            except Exception as e:
                self.root.after(0, lambda: self._set_text(self.teach_output, str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_eval_volume(self) -> None:
        vid = self.teach_volume.get().strip() or "01"

        def worker():
            try:
                from evaluation.runner import evaluate_curriculum

                report = evaluate_curriculum(vid, teach_first=False)
                text = json.dumps(report, ensure_ascii=False, indent=2, default=str)
                self.root.after(0, lambda: self._set_text(self.teach_output, text))
            except Exception as e:
                self.root.after(0, lambda: self._set_text(self.teach_output, str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_status(self) -> None:
        def worker():
            try:
                from core.bootstrap import leon_status

                text = json.dumps(leon_status(), ensure_ascii=False, indent=2, default=str)
                self.root.after(0, lambda: self._set_text(self.status_output, text))
            except Exception as e:
                self.root.after(0, lambda: self._set_text(self.status_output, str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_health(self) -> None:
        def worker():
            try:
                from interfaces.api.health import health_report

                text = json.dumps(health_report(), ensure_ascii=False, indent=2, default=str)
                self.root.after(0, lambda: self._set_text(self.status_output, text))
            except Exception as e:
                self.root.after(0, lambda: self._set_text(self.status_output, str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_llm(self) -> None:
        def worker():
            try:
                from brain.llm.client import get_llm_client

                text = json.dumps(
                    get_llm_client(force_new=True).health_check(),
                    ensure_ascii=False,
                    indent=2,
                )
                self.root.after(0, lambda: self._set_text(self.status_output, text))
            except Exception as e:
                self.root.after(0, lambda: self._set_text(self.status_output, str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_about(self) -> None:
        messagebox.showinfo(
            "Leon",
            "Leon AI Platform\n\n"
            "Think · Teach · Status\n"
            "CLI · FastAPI · GUI\n\n"
            "https://github.com/Mireyyub/zenthon",
        )


def run_gui():
    root = tk.Tk()
    LeonApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
