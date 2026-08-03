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


class LeonApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Leon AI Platform")
        self.root.geometry("1000x720")
        self._orch = None
        self.log_queue: queue.Queue = queue.Queue()

        self._configure_styles()
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
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
        style.configure("TButton", padding=6)

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
        self._create_think_tab()
        self._create_teach_tab()
        self._create_status_tab()

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

    def _create_status_bar(self) -> None:
        self.status_bar = ttk.Label(self.root, text="Leon Ready", relief=tk.SUNKEN, anchor=tk.W)
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
