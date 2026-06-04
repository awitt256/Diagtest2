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
DEFAULT_SCRIPT = "HPLENDELLDEV2.ps1"
STATUS_MESSAGES = [
    "Waking up the silicon detectives",
    "Interrogating BIOS gremlins",
    "Dusting off device manager clues",
    "Cross-checking vendor secrets",
    "Building the report deck",
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
            width=320,
            height=190,
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

        width = 320
        height = 190
        pulse = frame % 6
        knight_x = 72 + ((frame % 4) * 2 if not idle else 0)
        dragon_x = 240 - ((frame % 3) * 2 if not idle else 0)
        wing_lift = [0, -8, -14, -8, 0, 6][pulse]
        fire_shift = [0, 8, 14, 8, 0, -4][pulse]

        canvas.create_rectangle(0, 0, width, height, fill="#08111d", outline="")
        canvas.create_oval(220, 18, 292, 78, fill="#f6d365", outline="", stipple="gray25")
        canvas.create_polygon(0, 124, 48, 78, 92, 124, 132, 62, 188, 124, 252, 54, 320, 124, 320, 190, 0, 190, fill="#18263a", outline="")
        canvas.create_rectangle(0, 124, width, height, fill="#223322", outline="")
        canvas.create_rectangle(0, 145, width, height, fill="#2f4a2a", outline="")

        for star_x, star_y in [(24, 22), (68, 36), (114, 24), (162, 34), (306, 28)]:
            canvas.create_oval(star_x, star_y, star_x + 3, star_y + 3, fill="#dbeafe", outline="")

        # Dragon
        canvas.create_polygon(
            dragon_x - 26, 82,
            dragon_x - 70, 56 + wing_lift,
            dragon_x - 44, 98,
            dragon_x - 10, 80,
            dragon_x + 12, 104,
            dragon_x + 44, 86,
            dragon_x + 80, 58 + wing_lift,
            dragon_x + 50, 104,
            dragon_x + 22, 90,
            fill="#5865f2",
            outline="#a5b4fc",
            width=2,
        )
        canvas.create_oval(dragon_x - 32, 88, dragon_x + 26, 128, fill="#4753d6", outline="#c7d2fe", width=2)
        canvas.create_oval(dragon_x + 10, 92, dragon_x + 56, 118, fill="#4753d6", outline="#c7d2fe", width=2)
        canvas.create_polygon(dragon_x + 54, 103, dragon_x + 86, 96, dragon_x + 74, 114, fill="#4753d6", outline="#c7d2fe", width=2)
        canvas.create_polygon(dragon_x - 6, 88, dragon_x + 2, 74, dragon_x + 12, 88, fill="#c7d2fe", outline="")
        canvas.create_polygon(dragon_x + 10, 90, dragon_x + 18, 74, dragon_x + 28, 90, fill="#c7d2fe", outline="")
        canvas.create_oval(dragon_x + 26, 98, dragon_x + 31, 103, fill="#f8fafc", outline="")
        canvas.create_oval(dragon_x + 28, 99, dragon_x + 30, 101, fill="#0f1720", outline="")
        canvas.create_line(dragon_x - 26, 118, dragon_x - 42, 142, dragon_x - 20, 138, fill="#c7d2fe", width=3)
        canvas.create_line(dragon_x - 2, 122, dragon_x - 8, 146, dragon_x + 8, 144, fill="#c7d2fe", width=3)

        if not idle:
            canvas.create_polygon(
                dragon_x + 88, 102,
                dragon_x + 116 + fire_shift, 92,
                dragon_x + 138 + fire_shift, 100,
                dragon_x + 116 + fire_shift, 108,
                fill="#fb923c",
                outline="#fdba74",
            )
            canvas.create_polygon(
                dragon_x + 92, 102,
                dragon_x + 110 + fire_shift, 96,
                dragon_x + 124 + fire_shift, 101,
                dragon_x + 110 + fire_shift, 106,
                fill="#fde047",
                outline="",
            )

        # Knight
        canvas.create_line(knight_x, 118, knight_x, 154, fill="#f8fafc", width=4)
        canvas.create_oval(knight_x - 10, 96, knight_x + 10, 116, fill="#dbeafe", outline="#f8fafc", width=2)
        canvas.create_line(knight_x, 128, knight_x - 14, 142, fill="#f8fafc", width=4)
        canvas.create_line(knight_x, 128, knight_x + 16, 132, fill="#f8fafc", width=4)
        canvas.create_line(knight_x, 154, knight_x - 12, 176, fill="#f8fafc", width=4)
        canvas.create_line(knight_x, 154, knight_x + 16, 176, fill="#f8fafc", width=4)
        canvas.create_polygon(knight_x - 18, 124, knight_x - 2, 118, knight_x - 2, 144, knight_x - 18, 148, fill="#94a3b8", outline="#e2e8f0", width=2)
        sword_tip_x = knight_x + 44 + ((frame % 5) * 3 if not idle else 0)
        canvas.create_line(knight_x + 14, 132, sword_tip_x, 106, fill="#e2e8f0", width=4)
        canvas.create_line(knight_x + 24, 128, knight_x + 18, 138, fill="#fbbf24", width=4)
        canvas.create_line(knight_x + 20, 130, knight_x + 28, 136, fill="#fbbf24", width=4)

    def _tick_status(self):
        if self.is_running:
            self.scene_tick += 1
            self.status_index = (self.status_index + 1) % len(STATUS_MESSAGES)
            self._draw_vibe_scene(self.scene_tick)
            self.fun_var.set(STATUS_MESSAGES[self.status_index])
        else:
            self._draw_vibe_scene(self.scene_tick, idle=True)
        self.root.after(700, self._tick_status)

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
