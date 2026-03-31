#!/usr/bin/env python3
"""Simple desktop GUI for the photo progress report generator."""

from __future__ import annotations

import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


class ReportGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Flare CCECC Monthly Report Generator")
        self.geometry("760x560")
        self.minsize(700, 520)

        self.log_queue: queue.Queue[str] = queue.Queue()
        self.worker: threading.Thread | None = None

        self.input_var = tk.StringVar(value=str(Path("Input") / "Jan 2026"))
        self.output_var = tk.StringVar(value="Output")
        self.month_var = tk.StringVar(value="Jan 2026")
        self.strict_var = tk.BooleanVar(value=True)

        self._build_ui()
        self.after(150, self._drain_log_queue)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=16)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(5, weight=1)

        title = ttk.Label(
            outer,
            text="Monthly Photo Report Generator",
            font=("Arial", 16, "bold"),
        )
        title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 14))

        ttk.Label(outer, text="Input month folder").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(outer, textvariable=self.input_var).grid(row=1, column=1, sticky="ew", padx=8)
        ttk.Button(outer, text="Browse...", command=self._browse_input).grid(row=1, column=2, sticky="ew")

        ttk.Label(outer, text="Month label").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Entry(outer, textvariable=self.month_var).grid(row=2, column=1, sticky="ew", padx=8)
        ttk.Label(outer, text='Example: Jan 2026').grid(row=2, column=2, sticky="w")

        ttk.Label(outer, text="Output folder").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Entry(outer, textvariable=self.output_var).grid(row=3, column=1, sticky="ew", padx=8)
        ttk.Button(outer, text="Browse...", command=self._browse_output).grid(row=3, column=2, sticky="ew")

        ttk.Checkbutton(
            outer,
            text="Strict mode (stop if any photo is missing a timestamp)",
            variable=self.strict_var,
        ).grid(row=4, column=0, columnspan=3, sticky="w", pady=(8, 12))

        log_frame = ttk.LabelFrame(outer, text="Run log", padding=8)
        log_frame.grid(row=5, column=0, columnspan=3, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, wrap="word", height=18)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scroll.set)

        actions = ttk.Frame(outer)
        actions.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        actions.columnconfigure(0, weight=1)

        ttk.Button(actions, text="Open Input Folder", command=self._open_input_folder).pack(side="left")
        ttk.Button(actions, text="Open Output Folder", command=self._open_output_folder).pack(side="left", padx=(8, 0))
        self.run_button = ttk.Button(actions, text="Generate PDFs", command=self._run_generator)
        self.run_button.pack(side="right")

    def _browse_input(self) -> None:
        path = filedialog.askdirectory(title="Choose the input month folder")
        if path:
            self.input_var.set(path)
            month_name = Path(path).name.strip()
            if month_name:
                self.month_var.set(month_name)

    def _browse_output(self) -> None:
        path = filedialog.askdirectory(title="Choose the output folder")
        if path:
            self.output_var.set(path)

    def _open_folder(self, folder: str) -> None:
        path = Path(folder)
        path.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                subprocess.Popen(["explorer", str(path)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            messagebox.showerror("Open folder failed", str(exc))

    def _open_input_folder(self) -> None:
        self._open_folder(self.input_var.get())

    def _open_output_folder(self) -> None:
        self._open_folder(self.output_var.get())

    def _append_log(self, text: str) -> None:
        self.log_text.insert("end", text)
        self.log_text.see("end")

    def _drain_log_queue(self) -> None:
        while True:
            try:
                msg = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self._append_log(msg)
        self.after(150, self._drain_log_queue)

    def _run_generator(self) -> None:
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("Already running", "A generation job is already in progress.")
            return

        input_folder = self.input_var.get().strip()
        output_folder = self.output_var.get().strip()
        month_label = self.month_var.get().strip()

        if not input_folder:
            messagebox.showerror("Missing input", "Please choose an input month folder.")
            return
        if not month_label:
            messagebox.showerror("Missing month", "Please enter a month label like Jan 2026.")
            return
        if not Path(input_folder).exists():
            messagebox.showerror("Input not found", f"Input folder not found:\n{input_folder}")
            return

        cmd = [
            sys.executable,
            str(Path(__file__).with_name("make_reports.py")),
            "--input",
            input_folder,
            "--month",
            month_label,
            "--output",
            output_folder or "Output",
        ]
        if self.strict_var.get():
            cmd.append("--strict")

        self.log_text.delete("1.0", "end")
        self._append_log("Running command:\n" + " ".join(f'"{x}"' if " " in x else x for x in cmd) + "\n\n")
        self.run_button.configure(state="disabled")

        def worker() -> None:
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                assert proc.stdout is not None
                for line in proc.stdout:
                    self.log_queue.put(line)
                return_code = proc.wait()
                if return_code == 0:
                    self.log_queue.put("\nDone. PDFs generated successfully.\n")
                else:
                    self.log_queue.put(f"\nProcess exited with code {return_code}.\n")
            except Exception as exc:
                self.log_queue.put(f"\nFailed to run generator: {exc}\n")
            finally:
                self.after(0, lambda: self.run_button.configure(state="normal"))

        self.worker = threading.Thread(target=worker, daemon=True)
        self.worker.start()


if __name__ == "__main__":
    app = ReportGui()
    app.mainloop()
