"""
Leon GUI – ThinkingBrain inteqrasiyalı interfeys.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import json
from typing import Optional, Dict, Any

from core.logger import logger


class LeonApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Leon AI Platform")
        self.root.geometry("1100x780")
        self._orch = None
        self.log_queue: queue.Queue = queue.Queue()

        self._configure_styles()
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self._create_menu()
        self._create_notebook()
        self._create_status_bar()
        self.root.after(100, self._process_log_queue)
        logger.info("Leon GUI initialized")

    def _orch_lazy(self):
        if self._orch is None:
            from brain.orchestrator import BrainOrchestrator
            self._orch = BrainOrchestrator(brain_name="Leon")
        return self._orch

    def _configure_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TButton", padding=6)
        style.configure("TLabel", padding=4)

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
        self._create_brain_tab()
        self._create_data_tab()
        self._create_train_tab()
        self._create_logs_tab()

    def _create_brain_tab(self) -> None:
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Leon")

        top = ttk.LabelFrame(frame, text="Leon · ThinkingBrain")
        top.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(top, text="Sual / tapşırıq:").grid(row=0, column=0, sticky=tk.W, padx=4, pady=4)
        self.brain_query = scrolledtext.ScrolledText(top, height=4, wrap=tk.WORD)
        self.brain_query.grid(row=0, column=1, columnspan=3, sticky=tk.EW, padx=4, pady=4)

        ttk.Label(top, text="Mode:").grid(row=1, column=0, sticky=tk.W, padx=4)
        self.brain_mode = ttk.Combobox(top, values=["auto", "cot", "tot", "sot"], width=12)
        self.brain_mode.set("auto")
        self.brain_mode.grid(row=1, column=1, sticky=tk.W, padx=4)

        ttk.Label(top, text="Goal:").grid(row=1, column=2, sticky=tk.W, padx=4)
        self.brain_goal = ttk.Entry(top, width=40)
        self.brain_goal.grid(row=1, column=3, sticky=tk.EW, padx=4)

        ttk.Label(top, text="Agent:").grid(row=2, column=0, sticky=tk.W, padx=4)
        self.brain_agent = ttk.Combobox(
            top,
            values=["", "coding", "research", "executor", "react", "pev", "reflexion"],
            width=12,
        )
        self.brain_agent.set("")
        self.brain_agent.grid(row=2, column=1, sticky=tk.W, padx=4)

        btn_row = ttk.Frame(top)
        btn_row.grid(row=3, column=0, columnspan=4, pady=8)
        ttk.Button(btn_row, text="Think", command=self._on_brain_think).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="Clear", command=self._on_brain_clear).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="Status", command=self._on_brain_status).pack(side=tk.LEFT, padx=4)

        top.columnconfigure(1, weight=1)
        top.columnconfigure(3, weight=1)

        out = ttk.LabelFrame(frame, text="Nəticə")
        out.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.brain_output = scrolledtext.ScrolledText(out, wrap=tk.WORD)
        self.brain_output.pack(fill=tk.BOTH, expand=True)

    def _create_data_tab(self) -> None:
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Data")
        preview = ttk.LabelFrame(frame, text="Data Preview")
        preview.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.data_tree = ttk.Treeview(preview)
        self.data_tree.pack(fill=tk.BOTH, expand=True)
        ctrl = ttk.Frame(frame)
        ctrl.pack(fill=tk.X, padx=8, pady=4)
        ttk.Button(ctrl, text="Load CSV", command=self._on_load_data).pack(side=tk.LEFT, padx=4)
        self.data_info_label = ttk.Label(ctrl, text="No data")
        self.data_info_label.pack(side=tk.RIGHT)

    def _create_train_tab(self) -> None:
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Train")
        form = ttk.LabelFrame(frame, text="ML Training (CLI tövsiyə olunur)")
        form.pack(fill=tk.X, padx=8, pady=8)
        ttk.Label(
            form,
            text="Tam train üçün: python -m interfaces.cli.main_cli train --model linear_regression --data f.csv --target y",
        ).pack(padx=8, pady=8)

    def _create_logs_tab(self) -> None:
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Logs")
        self.log_display = scrolledtext.ScrolledText(frame)
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        ttk.Button(frame, text="Clear", command=lambda: self.log_display.delete("1.0", tk.END)).pack(pady=4)

    def _create_status_bar(self) -> None:
        self.status_bar = ttk.Label(self.root, text="Leon Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _process_log_queue(self) -> None:
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_display.insert(tk.END, msg + "\n")
                self.log_display.see(tk.END)
                self.status_bar.config(text=msg[:120])
        except queue.Empty:
            pass
        self.root.after(100, self._process_log_queue)

    def _log(self, msg: str) -> None:
        self.log_queue.put(msg)

    def _on_brain_think(self) -> None:
        query = self.brain_query.get("1.0", tk.END).strip()
        if not query:
            messagebox.showwarning("Xəbərdarlıq", "Sual yazın")
            return
        mode = self.brain_mode.get() or "auto"
        goal = self.brain_goal.get().strip() or None
        agent = self.brain_agent.get().strip() or None
        self._log(f"Leon think | mode={mode} agent={agent or '-'}")
        self.brain_output.delete("1.0", tk.END)
        self.brain_output.insert(tk.END, "Leon düşünür...\n")

        def worker():
            try:
                orch = self._orch_lazy()
                result = orch.run(
                    query,
                    goal=goal,
                    reasoning_mode=mode,
                    agent_type=agent,
                    use_session=True,
                    archive_result=True,
                )
                text = (
                    f"Mode       : {result.get('reasoning_mode')}\n"
                    f"Confidence : {result.get('confidence')}\n"
                    f"LLM used   : {result.get('llm_used')}\n"
                    f"Decision   : {result.get('decision')}\n"
                    f"Reflection : {result.get('reflection')}\n"
                    f"\n--- Conclusion ---\n{result.get('conclusion')}\n"
                )
                if result.get("agent"):
                    text += f"\n--- Agent ---\n{json.dumps(result['agent'], ensure_ascii=False, indent=2, default=str)}\n"
                self.root.after(0, lambda: self._show_brain_result(text))
                self.root.after(0, lambda: self._log("Leon think completed"))
            except Exception as e:
                self.root.after(0, lambda: self._show_brain_result(f"Xəta: {e}"))
                self.root.after(0, lambda: self._log(f"Leon error: {e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _show_brain_result(self, text: str) -> None:
        self.brain_output.delete("1.0", tk.END)
        self.brain_output.insert(tk.END, text)

    def _on_brain_clear(self) -> None:
        self.brain_query.delete("1.0", tk.END)
        self.brain_output.delete("1.0", tk.END)
        self.brain_goal.delete(0, tk.END)

    def _on_brain_status(self) -> None:
        def worker():
            try:
                st = self._orch_lazy().status()
                text = json.dumps(st, ensure_ascii=False, indent=2, default=str)
                self.root.after(0, lambda: self._show_brain_result(text))
            except Exception as e:
                self.root.after(0, lambda: self._show_brain_result(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_load_data(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if not path:
            return
        try:
            import pandas as pd

            data = pd.read_csv(path)
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)
            self.data_tree["columns"] = list(data.columns)
            self.data_tree["show"] = "headings"
            for col in data.columns:
                self.data_tree.heading(col, text=col)
                self.data_tree.column(col, width=100)
            for _, row in data.head(100).iterrows():
                self.data_tree.insert("", "end", values=list(row))
            self.data_info_label.config(text=f"{len(data)} rows")
            self._log(f"Loaded {path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_about(self) -> None:
        messagebox.showinfo(
            "About Leon",
            "Leon AI Platform\n\n"
            "ThinkingBrain + Agents + Memory + GraphRAG\n"
            "Ollama lokal LLM · CLI · API · GUI\n\n"
            "https://github.com/Mireyyub/zenthon",
        )


def run_gui():
    root = tk.Tk()
    LeonApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
