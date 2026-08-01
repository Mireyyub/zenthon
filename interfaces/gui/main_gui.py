"""
Main GUI Module
Graphical User Interface for AI System using Tkinter.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import json
from typing import Optional, Dict, Any, List

from core.logger import logger
from core.config import config


class AIApp:
    """
    Main GUI application for AI System.
    """

    def __init__(self, root: tk.Tk):
        """
        Initialize the AI application GUI.

        Args:
            root: Tkinter root window.
        """
        self.root = root
        self.root.title("AI System - Machine Learning Platform")
        self.root.geometry("1024x768")

        # Configure styles
        self._configure_styles()

        # Create main containers
        self._create_main_containers()

        # Create menu
        self._create_menu()

        # Create notebook tabs
        self._create_notebook()

        # Create status bar
        self._create_status_bar()

        # Message queue for thread-safe logging
        self.log_queue = queue.Queue()
        self.root.after(100, self._process_log_queue)

        logger.info("AI System GUI initialized")

    def _configure_styles(self) -> None:
        """Configure ttk styles."""
        style = ttk.Style()
        style.theme_use("clam")

        # Configure main frame style
        style.configure("TFrame", background="#f0f0f0")

        # Configure notebook style
        style.configure("TNotebook", background="#f0f0f0")
        style.configure("TNotebook.Tab", background="#e0e0e0", foreground="black")
        style.map("TNotebook.Tab", background=[("selected", "#4a90d9")])

        # Configure button style
        style.configure("TButton", padding=6, background="#4a90d9", foreground="white")
        style.map("TButton", background=[("active", "#3a7bc8")])

        # Configure label style
        style.configure("TLabel", background="#f0f0f0", padding=6)

        # Configure entry style
        style.configure("TEntry", padding=6)

        # Configure combobox style
        style.configure("TCombobox", padding=6)

    def _create_main_containers(self) -> None:
        """Create main containers."""
        # Main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _create_menu(self) -> None:
        """Create application menu."""
        menubar = tk.Menu(self.root)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self._on_file_open)
        file_menu.add_command(label="Save", command=self._on_file_save)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Model menu
        model_menu = tk.Menu(menubar, tearoff=0)
        model_menu.add_command(label="Train Model", command=self._on_train_model)
        model_menu.add_command(label="Load Model", command=self._on_load_model)
        model_menu.add_command(label="Save Model", command=self._on_save_model)
        menubar.add_cascade(label="Model", menu=model_menu)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Data Preprocessing", command=self._on_data_preprocessing)
        tools_menu.add_command(label="Model Evaluation", command=self._on_model_evaluation)
        tools_menu.add_command(label="Explain Prediction", command=self._on_explain_prediction)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._on_about)
        help_menu.add_command(label="Documentation", command=self._on_documentation)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def _create_notebook(self) -> None:
        """Create notebook with tabs."""
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self._create_data_tab()
        self._create_train_tab()
        self._create_predict_tab()
        self._create_explain_tab()
        self._create_logs_tab()

    def _create_data_tab(self) -> None:
        """Create data tab."""
        data_frame = ttk.Frame(self.notebook)
        self.notebook.add(data_frame, text="Data")

        # Data preview frame
        preview_frame = ttk.LabelFrame(data_frame, text="Data Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Treeview for data display
        self.data_tree = ttk.Treeview(preview_frame)
        self.data_tree.pack(fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.data_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.data_tree.configure(yscrollcommand=scrollbar.set)

        # Data controls frame
        controls_frame = ttk.Frame(data_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)

        # Load data button
        load_btn = ttk.Button(controls_frame, text="Load Data", command=self._on_load_data)
        load_btn.pack(side=tk.LEFT, padx=5)

        # Clear data button
        clear_btn = ttk.Button(controls_frame, text="Clear Data", command=self._on_clear_data)
        clear_btn.pack(side=tk.LEFT, padx=5)

        # Data info label
        self.data_info_label = ttk.Label(controls_frame, text="No data loaded")
        self.data_info_label.pack(side=tk.RIGHT, padx=10)

    def _create_train_tab(self) -> None:
        """Create training tab."""
        train_frame = ttk.Frame(self.notebook)
        self.notebook.add(train_frame, text="Train")

        # Training form frame
        form_frame = ttk.LabelFrame(train_frame, text="Training Configuration")
        form_frame.pack(fill=tk.X, padx=10, pady=10)

        # Model selection
        ttk.Label(form_frame, text="Model Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.model_type_combo = ttk.Combobox(
            form_frame,
            values=["Linear Regression", "Random Forest", "K-Means", "Neural Network"],
        )
        self.model_type_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.model_type_combo.set("Random Forest")

        # Target column
        ttk.Label(form_frame, text="Target Column:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.target_column_entry = ttk.Entry(form_frame)
        self.target_column_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)

        # Training parameters frame
        params_frame = ttk.LabelFrame(train_frame, text="Training Parameters")
        params_frame.pack(fill=tk.X, padx=10, pady=10)

        # Epochs
        ttk.Label(params_frame, text="Epochs:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.epochs_entry = ttk.Entry(params_frame)
        self.epochs_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.epochs_entry.insert(0, "10")

        # Batch size
        ttk.Label(params_frame, text="Batch Size:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.batch_size_entry = ttk.Entry(params_frame)
        self.batch_size_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        self.batch_size_entry.insert(0, "32")

        # Learning rate
        ttk.Label(params_frame, text="Learning Rate:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.learning_rate_entry = ttk.Entry(params_frame)
        self.learning_rate_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        self.learning_rate_entry.insert(0, "0.001")

        # Train button
        train_btn = ttk.Button(train_frame, text="Start Training", command=self._on_start_training)
        train_btn.pack(pady=10)

        # Training progress
        self.train_progress = ttk.Progressbar(train_frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.train_progress.pack(pady=10)

        # Training log
        self.train_log = scrolledtext.ScrolledText(train_frame, height=10)
        self.train_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _create_predict_tab(self) -> None:
        """Create prediction tab."""
        predict_frame = ttk.Frame(self.notebook)
        self.notebook.add(predict_frame, text="Predict")

        # Prediction form
        form_frame = ttk.LabelFrame(predict_frame, text="Prediction Configuration")
        form_frame.pack(fill=tk.X, padx=10, pady=10)

        # Model selection
        ttk.Label(form_frame, text="Model:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.predict_model_combo = ttk.Combobox(form_frame)
        self.predict_model_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

        # Input data
        ttk.Label(form_frame, text="Input Data:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.input_data_text = scrolledtext.ScrolledText(form_frame, height=5)
        self.input_data_text.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)

        # Predict button
        predict_btn = ttk.Button(predict_frame, text="Make Prediction", command=self._on_make_prediction)
        predict_btn.pack(pady=10)

        # Prediction results
        results_frame = ttk.LabelFrame(predict_frame, text="Prediction Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.prediction_results = scrolledtext.ScrolledText(results_frame)
        self.prediction_results.pack(fill=tk.BOTH, expand=True)

    def _create_explain_tab(self) -> None:
        """Create explanation tab."""
        explain_frame = ttk.Frame(self.notebook)
        self.notebook.add(explain_frame, text="Explain")

        # Explanation form
        form_frame = ttk.LabelFrame(explain_frame, text="Explanation Configuration")
        form_frame.pack(fill=tk.X, padx=10, pady=10)

        # Model selection
        ttk.Label(form_frame, text="Model:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.explain_model_combo = ttk.Combobox(form_frame)
        self.explain_model_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

        # Method selection
        ttk.Label(form_frame, text="Method:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.explain_method_combo = ttk.Combobox(
            form_frame,
            values=["LIME", "SHAP"],
        )
        self.explain_method_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        self.explain_method_combo.set("LIME")

        # Input data
        ttk.Label(form_frame, text="Input Data:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.explain_input_text = scrolledtext.ScrolledText(form_frame, height=5)
        self.explain_input_text.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)

        # Explain button
        explain_btn = ttk.Button(explain_frame, text="Generate Explanation", command=self._on_generate_explanation)
        explain_btn.pack(pady=10)

        # Explanation results
        results_frame = ttk.LabelFrame(explain_frame, text="Explanation Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.explanation_results = scrolledtext.ScrolledText(results_frame)
        self.explanation_results.pack(fill=tk.BOTH, expand=True)

    def _create_logs_tab(self) -> None:
        """Create logs tab."""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Logs")

        # Log display
        self.log_display = scrolledtext.ScrolledText(logs_frame)
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Log level controls
        controls_frame = ttk.Frame(logs_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)

        # Clear logs button
        clear_btn = ttk.Button(controls_frame, text="Clear Logs", command=self._on_clear_logs)
        clear_btn.pack(side=tk.LEFT, padx=5)

    def _create_status_bar(self) -> None:
        """Create status bar."""
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _process_log_queue(self) -> None:
        """Process log messages from the queue."""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self._log_message(message)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._process_log_queue)

    def _log_message(self, message: str) -> None:
        """Log a message to the GUI."""
        self.log_display.insert(tk.END, message + "\n")
        self.log_display.see(tk.END)
        self.status_bar.config(text=message)

    def _on_file_open(self) -> None:
        """Handle file open action."""
        file_path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[("CSV Files", "*.csv"), ("JSON Files", "*.json"), ("All Files", "*.*")],
        )
        if file_path:
            self._log_message(f"File opened: {file_path}")

    def _on_file_save(self) -> None:
        """Handle file save action."""
        file_path = filedialog.asksaveasfilename(
            title="Save File",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("CSV Files", "*.csv"), ("All Files", "*.*")],
        )
        if file_path:
            self._log_message(f"File saved: {file_path}")

    def _on_load_data(self) -> None:
        """Handle load data action."""
        file_path = filedialog.askopenfilename(
            title="Load Data",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        )
        if file_path:
            try:
                import pandas as pd
                data = pd.read_csv(file_path)

                # Clear existing data
                for item in self.data_tree.get_children():
                    self.data_tree.delete(item)

                # Set up treeview columns
                self.data_tree["columns"] = list(data.columns)
                self.data_tree["show"] = "headings"

                for col in data.columns:
                    self.data_tree.heading(col, text=col)
                    self.data_tree.column(col, width=100)

                # Insert data
                for i, row in data.head(100).iterrows():
                    self.data_tree.insert("", "end", values=list(row))

                # Update info label
                self.data_info_label.config(text=f"Loaded {len(data)} rows, {len(data.columns)} columns")
                self._log_message(f"Data loaded: {file_path}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load data: {e}")
                self._log_message(f"Error loading data: {e}")

    def _on_clear_data(self) -> None:
        """Handle clear data action."""
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        self.data_info_label.config(text="No data loaded")
        self._log_message("Data cleared")

    def _on_train_model(self) -> None:
        """Handle train model action."""
        self.notebook.select(1)  # Switch to train tab
        self._log_message("Navigate to Train tab to configure and start training")

    def _on_load_model(self) -> None:
        """Handle load model action."""
        file_path = filedialog.askopenfilename(
            title="Load Model",
            filetypes=[("PyTorch Models", "*.pt;*.pth"), ("Joblib Models", "*.joblib"), ("All Files", "*.*")],
        )
        if file_path:
            self._log_message(f"Model loaded: {file_path}")

    def _on_save_model(self) -> None:
        """Handle save model action."""
        file_path = filedialog.asksaveasfilename(
            title="Save Model",
            defaultextension=".pt",
            filetypes=[("PyTorch Models", "*.pt"), ("Joblib Models", "*.joblib"), ("All Files", "*.*")],
        )
        if file_path:
            self._log_message(f"Model saved: {file_path}")

    def _on_data_preprocessing(self) -> None:
        """Handle data preprocessing action."""
        self._log_message("Data preprocessing functionality coming soon")

    def _on_model_evaluation(self) -> None:
        """Handle model evaluation action."""
        self._log_message("Model evaluation functionality coming soon")

    def _on_explain_prediction(self) -> None:
        """Handle explain prediction action."""
        self.notebook.select(3)  # Switch to explain tab
        self._log_message("Navigate to Explain tab to generate explanations")

    def _on_start_training(self) -> None:
        """Handle start training action."""
        # Get training parameters
        model_type = self.model_type_combo.get()
        target_column = self.target_column_entry.get()
        epochs = int(self.epochs_entry.get() or 10)
        batch_size = int(self.batch_size_entry.get() or 32)
        learning_rate = float(self.learning_rate_entry.get() or 0.001)

        self._log_message(f"Starting training: {model_type}")
        self._log_message(f"Target: {target_column}, Epochs: {epochs}, Batch Size: {batch_size}")

        # Start training in a separate thread
        training_thread = threading.Thread(
            target=self._run_training,
            args=(model_type, target_column, epochs, batch_size, learning_rate),
            daemon=True,
        )
        training_thread.start()

    def _run_training(
        self,
        model_type: str,
        target_column: str,
        epochs: int,
        batch_size: int,
        learning_rate: float,
    ) -> None:
        """Run training in a separate thread."""
        try:
            # Simulate training
            for i in range(epochs):
                time.sleep(0.5)  # Simulate training time
                progress = (i + 1) / epochs * 100
                self.root.after(0, lambda: self.train_progress.config(value=progress))
                self.root.after(0, lambda: self.train_log.insert(tk.END, f"Epoch {i+1}/{epochs} - Loss: {np.random.random():.4f}\n"))
                self.root.after(0, lambda: self.train_log.see(tk.END))

            self.root.after(0, lambda: self._log_message(f"Training completed for {model_type}"))

        except Exception as e:
            self.root.after(0, lambda: self._log_message(f"Training failed: {e}"))

    def _on_make_prediction(self) -> None:
        """Handle make prediction action."""
        model_name = self.predict_model_combo.get()
        input_data = self.input_data_text.get("1.0", tk.END).strip()

        if not model_name:
            messagebox.showwarning("Warning", "Please select a model")
            return

        if not input_data:
            messagebox.showwarning("Warning", "Please enter input data")
            return

        self._log_message(f"Making prediction with model: {model_name}")
        self._log_message(f"Input data: {input_data}")

        # Simulate prediction
        self.prediction_results.delete("1.0", tk.END)
        self.prediction_results.insert(tk.END, "Prediction Results:\n\n")
        self.prediction_results.insert(tk.END, f"Model: {model_name}\n")
        self.prediction_results.insert(tk.END, f"Input: {input_data}\n\n")
        self.prediction_results.insert(tk.END, "Predicted Class: Class 1 (Probability: 0.85)\n")
        self.prediction_results.insert(tk.END, "Predicted Class: Class 2 (Probability: 0.10)\n")
        self.prediction_results.insert(tk.END, "Predicted Class: Class 3 (Probability: 0.05)\n")

    def _on_generate_explanation(self) -> None:
        """Handle generate explanation action."""
        model_name = self.explain_model_combo.get()
        method = self.explain_method_combo.get()
        input_data = self.explain_input_text.get("1.0", tk.END).strip()

        if not model_name:
            messagebox.showwarning("Warning", "Please select a model")
            return

        if not input_data:
            messagebox.showwarning("Warning", "Please enter input data")
            return

        self._log_message(f"Generating explanation for model: {model_name} using {method}")
        self._log_message(f"Input data: {input_data}")

        # Simulate explanation
        self.explanation_results.delete("1.0", tk.END)
        self.explanation_results.insert(tk.END, f"Explanation for {model_name} using {method}:\n\n")
        self.explanation_results.insert(tk.END, "Top Features:\n")
        self.explanation_results.insert(tk.END, "  Feature 1: Coefficient = 0.45, Importance = 0.92\n")
        self.explanation_results.insert(tk.END, "  Feature 2: Coefficient = -0.32, Importance = 0.78\n")
        self.explanation_results.insert(tk.END, "  Feature 3: Coefficient = 0.18, Importance = 0.65\n")
        self.explanation_results.insert(tk.END, "\nIntercept: 0.12\n")
        self.explanation_results.insert(tk.END, "\nPrediction: Class 1")

    def _on_clear_logs(self) -> None:
        """Handle clear logs action."""
        self.log_display.delete("1.0", tk.END)
        self._log_message("Logs cleared")

    def _on_about(self) -> None:
        """Handle about action."""
        messagebox.showinfo(
            "About AI System",
            "AI System - Machine Learning Platform\n\n"
            "Version: 1.0.0\n"
            "A comprehensive platform for training, evaluating, and deploying machine learning models.\n\n"
            "Features:\n"
            "- Support for multiple model types (ML and DL)\n"
            "- Data preprocessing and augmentation\n"
            "- Model training and evaluation\n"
            "- Prediction and explanation\n"
            "- REST API for model serving\n"
            "- CLI and GUI interfaces\n",
        )

    def _on_documentation(self) -> None:
        """Handle documentation action."""
        self._log_message("Documentation: Check the docs/ directory in the project")


def run_gui():
    """Run the GUI application."""
    root = tk.Tk()
    app = AIApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
