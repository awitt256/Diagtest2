import ctypes
import os
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk


APP_TITLE = "System Info Console"
DEFAULT_SCRIPT = "HPLENDELLDEV3.ps1"
TYPE_INTERVAL_MS = 95
EMAIL_HOLD_STEPS = 12
STATUS_MESSAGES = [
    "Refreshing the inbox of doom",
    "Opening another suspicious dragon email",
    "Checking whether the countryside got burninated",
    "Flagging weird attachments from Trogdor",
    "Drafting a very serious reply",
]


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin():
    script = os.path.abspath(__file__)
    args = " ".join(f'"{arg}"' for arg in [script] + sys.argv[1:])
    result = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        args,
        None,
        1,
    )
    return result > 32


class HardwareQuestApp:
    def __init__(self, root):
        self.root = root
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.script_path = os.path.join(self.base_dir, DEFAULT_SCRIPT)
        self.output_queue = queue.Queue()
        self.process = None
        self.reader_thread = None
        self.is_running = False
        self.status_index = 0
        self.scene_tick = 0

        self.root.title(APP_TITLE)
        self.root.geometry("1100x760")
        self.root.minsize(980, 680)
        self.root.configure(bg="#0f1720")

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._configure_styles()
        self._build_ui()
        self._set_script_path(self.script_path)
        self._tick_queue()
        self._tick_status()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _reveal_text(self, text, count):
        if count <= 0:
            return ""
        return text[:count]

    def _get_email_message_index(self, frame):
        subject_lines = [
            "Subject: TROGDOR update",
            "Subject: countryside status",
            "Subject: burnination memo",
            "Subject: dragon support ticket",
            "Subject: keyboard + dragon issue",
        ]
        body_sets = [
            [
                "hey system info,",
                "trogdor stopped by again.",
                "three peasants yelled and one",
                "monitor blinked dramatically.",
            ],
            [
                "dear inbox,",
                "please confirm whether the",
                "burninator singed only the",
                "village or also the usb dock.",
            ],
            [
                "quick note:",
                "the big dragon says the",
                "status lights look crunchy",
                "but morale remains high.",
            ],
            [
                "follow-up:",
                "if you see smoke near bios,",
                "that is probably trogdor",
                "being extra productive.",
            ],
        ]
        frame_lengths = [
            len(subject_lines[index]) + sum(len(line) for line in body_sets[index]) + EMAIL_HOLD_STEPS
            for index in range(len(body_sets))
        ]
        total_cycle = sum(frame_lengths)
        cycle_position = frame % total_cycle

        for index, frame_length in enumerate(frame_lengths):
            if cycle_position < frame_length:
                return index
            cycle_position -= frame_length

        return 0

    def _configure_styles(self):
        self.style.configure("App.TFrame", background="#0f1720")
        self.style.configure("Card.TFrame", background="#152131")
        self.style.configure("Title.TLabel", background="#0f1720", foreground="#f8fafc", font=("Segoe UI", 24, "bold"))
        self.style.configure("Sub.TLabel", background="#0f1720", foreground="#93c5fd", font=("Segoe UI", 11, "bold"))
        self.style.configure("CardTitle.TLabel", background="#152131", foreground="#fef3c7", font=("Segoe UI", 11, "bold"))
        self.style.configure("CardValue.TLabel", background="#152131", foreground="#f8fafc", font=("Segoe UI", 12))
        self.style.configure("Hint.TLabel", background="#0f1720", foreground="#cbd5e1", font=("Segoe UI", 10))
        self.style.configure("Run.TButton", font=("Segoe UI", 11, "bold"))
        self.style.map("Run.TButton", background=[("active", "#f59e0b"), ("!disabled", "#fbbf24")], foreground=[("!disabled", "#0f1720")])

    def _build_ui(self):
        outer = ttk.Frame(self.root, style="App.TFrame", padding=18)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer, style="App.TFrame")
        header.pack(fill="x")

        ttk.Label(header, text=APP_TITLE, style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="A brighter launcher for HPLENDELLDEV2 with live output and quick tools.", style="Sub.TLabel").pack(anchor="w", pady=(4, 0))

        top_grid = ttk.Frame(outer, style="App.TFrame")
        top_grid.pack(fill="x", pady=(16, 14))
        top_grid.columnconfigure(0, weight=3)
        top_grid.columnconfigure(1, weight=2)

        control_card = ttk.Frame(top_grid, style="Card.TFrame", padding=16)
        control_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ttk.Label(control_card, text="Mission Control", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(control_card, text="Pick the PowerShell file, then launch the scan when you are ready.", style="CardValue.TLabel").pack(anchor="w", pady=(8, 12))

        path_row = ttk.Frame(control_card, style="Card.TFrame")
        path_row.pack(fill="x")
        path_row.columnconfigure(0, weight=1)

        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(path_row, textvariable=self.path_var, font=("Consolas", 10))
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        ttk.Button(path_row, text="Browse", command=self._browse_script).grid(row=0, column=1, sticky="ew")

        button_row = ttk.Frame(control_card, style="Card.TFrame")
        button_row.pack(fill="x", pady=(14, 0))

        self.run_button = ttk.Button(button_row, text="Run System Info", style="Run.TButton", command=self._start_run)
        self.run_button.pack(side="left")

        ttk.Button(button_row, text="Stop", command=self._stop_run).pack(side="left", padx=8)
        ttk.Button(button_row, text="Open Script Folder", command=self._open_script_folder).pack(side="left")
        ttk.Button(button_row, text="Open Log", command=self._open_log).pack(side="left", padx=(8, 0))
        ttk.Button(button_row, text="Clear Console", command=self._clear_console).pack(side="left", padx=(8, 0))

        ttk.Label(control_card, text="Tip: run this GUI from the same folder as the .ps1, BCU folder, and Command Configure folder.", style="Hint.TLabel").pack(anchor="w", pady=(14, 0))

        status_card = ttk.Frame(top_grid, style="Card.TFrame", padding=16)
        status_card.grid(row=0, column=1, sticky="nsew")

        ttk.Label(status_card, text="Vibe Board", style="CardTitle.TLabel").pack(anchor="w")
        self.mode_var = tk.StringVar(value="Idle")
        self.vendor_var = tk.StringVar(value="Vendor: waiting")
        self.script_name_var = tk.StringVar(value="Script: --")
        self.fun_var = tk.StringVar(value="System standing by")

        ttk.Label(status_card, textvariable=self.mode_var, style="CardValue.TLabel").pack(anchor="w", pady=(8, 4))
        ttk.Label(status_card, textvariable=self.vendor_var, style="CardValue.TLabel").pack(anchor="w", pady=4)
        ttk.Label(status_card, textvariable=self.script_name_var, style="CardValue.TLabel").pack(anchor="w", pady=4)
        self.vibe_canvas = tk.Canvas(
            status_card,
            width=390,
            height=240,
            bg="#0b1220",
            highlightthickness=0,
            relief="flat",
        )
        self.vibe_canvas.pack(fill="x", pady=(14, 10))
        ttk.Label(status_card, textvariable=self.fun_var, style="CardValue.TLabel", wraplength=300).pack(anchor="w", pady=(14, 0))
        self._draw_vibe_scene(0)

        console_card = ttk.Frame(outer, style="Card.TFrame", padding=12)
        console_card.pack(fill="both", expand=True)

        console_header = ttk.Frame(console_card, style="Card.TFrame")
        console_header.pack(fill="x")
        ttk.Label(console_header, text="Live Console", style="CardTitle.TLabel").pack(side="left")

        self.progress = ttk.Progressbar(console_header, mode="indeterminate", length=200)
        self.progress.pack(side="right")

        self.console = tk.Text(
            console_card,
            bg="#09111a",
            fg="#dbeafe",
            insertbackground="#f8fafc",
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            padx=14,
            pady=12,
        )
        self.console.pack(fill="both", expand=True, pady=(10, 0))
        self.console.tag_configure("accent", foreground="#fbbf24")
        self.console.tag_configure("error", foreground="#fca5a5")
        self.console.tag_configure("success", foreground="#86efac")
        self.console.insert("end", "System Info is ready.\nPick a script or run the one in this folder.\n", "accent")
        self.console.configure(state="disabled")

    def _set_script_path(self, path):
        self.script_path = path
        self.path_var.set(path)
        self.script_name_var.set(f"Script: {os.path.basename(path)}")

    def _append_console(self, text, tag=None):
        self.console.configure(state="normal")
        self.console.insert("end", text, tag)
        self.console.see("end")
        self.console.configure(state="disabled")

    def _clear_console(self):
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")

    def _browse_script(self):
        chosen = filedialog.askopenfilename(
            title="Choose PowerShell Script",
            initialdir=self.base_dir,
            filetypes=[("PowerShell files", "*.ps1"), ("All files", "*.*")],
        )
        if chosen:
            self._set_script_path(chosen)

    def _start_run(self):
        if self.is_running:
            return

        script_path = self.path_var.get().strip()
        if not script_path:
            messagebox.showwarning("Missing Script", "Choose a PowerShell script first.")
            return
        if not os.path.exists(script_path):
            messagebox.showwarning("Missing Script", f"Cannot find:\n{script_path}")
            return

        self._set_script_path(script_path)
        self.mode_var.set("Running")
        self.fun_var.set("System Info started. The hardware goblins are under review.")
        self.vendor_var.set("Vendor: scanning")
        self.is_running = True
        self.run_button.state(["disabled"])
        self.progress.start(12)

        self._append_console("\n=== Launching System Info ===\n", "accent")
        self._append_console(f"Script: {script_path}\n")

        command = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            script_path,
        ]

        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self.reader_thread = threading.Thread(target=self._read_output, daemon=True)
        self.reader_thread.start()

    def _read_output(self):
        try:
            for line in iter(self.process.stdout.readline, ""):
                self.output_queue.put(("line", line))
        except Exception as exc:
            self.output_queue.put(("error", f"\nReader error: {exc}\n"))
        finally:
            return_code = self.process.wait() if self.process else -1
            self.output_queue.put(("done", return_code))

    def _tick_queue(self):
        try:
            while True:
                event_type, payload = self.output_queue.get_nowait()
                if event_type == "line":
                    self._handle_output_line(payload)
                elif event_type == "error":
                    self._append_console(payload, "error")
                elif event_type == "done":
                    self._finish_run(payload)
        except queue.Empty:
            pass
        self.root.after(100, self._tick_queue)

    def _handle_output_line(self, line):
        clean = line.replace("\r", "")
        lower = clean.lower()

        if "detected manufacturer:" in lower:
            vendor = clean.split(":", 1)[1].strip() if ":" in clean else clean.strip()
            self.vendor_var.set(f"Vendor: {vendor}")
        elif "failed to run" in lower or "error" in lower:
            self._append_console(clean, "error")
            return
        elif "version match: yes" in lower:
            self._append_console(clean, "success")
            return
        elif "windows is activated" in lower or "this script currently supports" in lower:
            self._append_console(clean, "accent")
            return

        self._append_console(clean)

    def _finish_run(self, return_code):
        self.is_running = False
        self.progress.stop()
        self.run_button.state(["!disabled"])

        if return_code == 0:
            self.mode_var.set("Complete")
            self.fun_var.set("Scan Complete. The report board is ready.")
            self._append_console("\n=== Scan Complete ===\n", "success")
        else:
            self.mode_var.set("Ended")
            self.fun_var.set(f"Run finished with exit code {return_code}. Check the console and log.")
            self._append_console(f"\n=== Run finished with exit code {return_code} ===\n", "error")

        self._draw_vibe_scene(self.scene_tick, idle=True)
        self.process = None

    def _draw_vibe_scene(self, frame, idle=False):
        canvas = self.vibe_canvas
        canvas.delete("all")

        width = 390
        height = 240
        pulse = frame % 6
        cursor_blink = pulse in (1, 2, 4)
        fire_shift = [0, 8, 14, 8, 0, -4][pulse]
        subject_lines = [
            "Subject: TROGDOR update",
            "Subject: countryside status",
            "Subject: burnination memo",
            "Subject: dragon support ticket",
            "Subject: keyboard + dragon issue",
        ]
        body_sets = [
            [
                "hey system info,",
                "trogdor stopped by again.",
                "three peasants yelled and one",
                "monitor blinked dramatically.",
            ],
            [
                "dear inbox,",
                "please confirm whether the",
                "burninator singed only the",
                "village or also the usb dock.",
            ],
            [
                "quick note:",
                "the big dragon says the",
                "status lights look crunchy",
                "but morale remains high.",
            ],
            [
                "follow-up:",
                "if you see smoke near bios,",
                "that is probably trogdor",
                "being extra productive.",
            ],
        ]
        frame_lengths = [
            len(subject_lines[index]) + sum(len(line) for line in body_sets[index]) + EMAIL_HOLD_STEPS
            for index in range(len(body_sets))
        ]
        total_cycle = sum(frame_lengths)
        cycle_position = frame % total_cycle
        message_index = 0
        reveal_step = cycle_position

        for index, frame_length in enumerate(frame_lengths):
            if cycle_position < frame_length:
                message_index = index
                reveal_step = cycle_position
                break
            cycle_position -= frame_length

        current_subject = subject_lines[message_index % len(subject_lines)]
        current_body = body_sets[message_index]

        if idle:
            revealed_subject = current_subject
            revealed_body = current_body
        else:
            subject_length = len(current_subject)
            body_lengths = [len(line) for line in current_body]
            subject_chars = min(reveal_step, subject_length)
            remaining_chars = max(0, reveal_step - subject_length)
            revealed_subject = self._reveal_text(current_subject, subject_chars)
            revealed_body = []

            for line, line_length in zip(current_body, body_lengths):
                revealed_body.append(self._reveal_text(line, remaining_chars))
                remaining_chars = max(0, remaining_chars - line_length)

        canvas.create_rectangle(0, 0, width, height, fill="#08111d", outline="")
        canvas.create_rectangle(14, 16, 374, 220, fill="#d6d3d1", outline="#f8fafc", width=2)
        canvas.create_rectangle(14, 16, 374, 44, fill="#93c5fd", outline="")
        canvas.create_oval(24, 24, 32, 32, fill="#ef4444", outline="")
        canvas.create_oval(38, 24, 46, 32, fill="#f59e0b", outline="")
        canvas.create_oval(52, 24, 60, 32, fill="#22c55e", outline="")
        canvas.create_text(194, 30, text="strongly worded dragon email", fill="#0f172a", font=("Consolas", 11, "bold"))

        canvas.create_rectangle(24, 56, 132, 206, fill="#e5e7eb", outline="#cbd5e1")
        canvas.create_text(78, 70, text="Inbox", fill="#1e293b", font=("Consolas", 11, "bold"))
        mail_items = [
            ["re: trogdor"],
            ["village notes"],
            ["burnination"],
            ["dragon pics"],
            ["fw: weird", "smoke"],
        ]
        for index, item_lines in enumerate(mail_items):
            y = 96 + (index * 20)
            fill = "#fde68a" if index == message_index else "#334155"
            canvas.create_text(34, y, text=">", fill=fill, anchor="w", font=("Consolas", 10))
            for line_offset, item_line in enumerate(item_lines):
                canvas.create_text(48, y + (line_offset * 9), text=item_line, fill="#334155", anchor="w", font=("Consolas", 10))

        canvas.create_rectangle(142, 56, 364, 206, fill="#fff7ed", outline="#cbd5e1")
        canvas.create_text(154, 72, text="From: sbemail@homestar.mail", fill="#7c2d12", anchor="w", font=("Consolas", 10, "bold"))
        canvas.create_text(154, 92, text=revealed_subject, fill="#7c2d12", anchor="w", font=("Consolas", 10, "bold"))
        canvas.create_line(152, 106, 354, 106, fill="#cbd5e1", width=1)

        for index, line in enumerate(revealed_body):
            canvas.create_text(154, 124 + (index * 18), text=line, fill="#1f2937", anchor="w", font=("Consolas", 10, "bold"))

        if not idle:
            canvas.create_text(154, 184, text="typing..." + ("|" if cursor_blink else ""), fill="#2563eb", anchor="w", font=("Consolas", 10))

    def _tick_status(self):
        if self.is_running:
            self.scene_tick += 1
            self.status_index = self._get_email_message_index(self.scene_tick) % len(STATUS_MESSAGES)
            self._draw_vibe_scene(self.scene_tick)
            self.fun_var.set(STATUS_MESSAGES[self.status_index])
        else:
            self._draw_vibe_scene(self.scene_tick, idle=True)
        self.root.after(TYPE_INTERVAL_MS, self._tick_status)

    def _stop_run(self):
        if not self.process or not self.is_running:
            return
        try:
            self.process.terminate()
            self._append_console("\n=== Stop requested by user ===\n", "error")
        except Exception as exc:
            messagebox.showerror("Stop Failed", str(exc))

    def _open_script_folder(self):
        target = os.path.dirname(self.path_var.get().strip() or self.base_dir)
        if not os.path.isdir(target):
            target = self.base_dir
        os.startfile(target)

    def _open_log(self):
        script_path = self.path_var.get().strip()
        if not script_path:
            messagebox.showinfo("No Script", "Choose a script first.")
            return

        script_dir = os.path.dirname(script_path)
        script_name = os.path.splitext(os.path.basename(script_path))[0]
        log_path = os.path.join(script_dir, f"{script_name}.log")

        if not os.path.exists(log_path):
            messagebox.showinfo("Log Not Found", f"No log found yet:\n{log_path}")
            return

        os.startfile(log_path)

    def _on_close(self):
        if self.is_running and self.process:
            if not messagebox.askyesno("Exit", "A run is still active. Close anyway and stop it?"):
                return
            try:
                self.process.terminate()
            except Exception:
                pass
        self.root.destroy()


def main():
    if not is_admin():
        if relaunch_as_admin():
            return
        messagebox.showerror("Admin Required", "This GUI needs admin rights so the PowerShell tool can run cleanly.")
        return

    root = tk.Tk()
    app = HardwareQuestApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
