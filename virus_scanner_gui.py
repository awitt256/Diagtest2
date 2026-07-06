"""
Virus Scanner GUI
-----------------
A GUI version of the Drive Scan Watcher that watches drive letters D: through O:
for newly plugged-in drives and automatically runs Windows Defender scans.
Features live scan progress and scan history.

Requirements:
    pip install psutil customtkinter
"""

import os
import sys
import time
import string
import subprocess
import threading
import ctypes
import customtkinter as ctk
from tkinter import ttk
from datetime import datetime

# Hide console window on Windows
if sys.platform == "win32":
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass

try:
    import psutil
except ImportError:
    print("This script requires the 'psutil' package.")
    print("Install it with:  pip install psutil")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Drive letters to watch (inclusive). Default: D through O.
WATCH_RANGE = [d for d in string.ascii_uppercase if 'D' <= d <= 'O']

# How often to check for newly plugged-in drives (seconds).
POLL_INTERVAL_SECONDS = 2

# Path to the Windows Defender command-line scanner.
MPCMDRUN_CANDIDATES = [
    r"C:\Program Files\Windows Defender\MpCmdRun.exe",
    os.path.expandvars(
        r"%ProgramData%\Microsoft\Windows Defender\Platform"
    ),  # base dir; real exe lives in a versioned subfolder, handled below
]


def find_mpcmdrun():
    """Locate MpCmdRun.exe, checking the fixed path first, then the
    versioned Platform folder that Defender updates create."""
    fixed = r"C:\Program Files\Windows Defender\MpCmdRun.exe"
    if os.path.isfile(fixed):
        return fixed

    platform_dir = os.path.expandvars(
        r"%ProgramData%\Microsoft\Windows Defender\Platform"
    )
    if os.path.isdir(platform_dir):
        # Versioned subfolders look like 4.18.24070.5; pick the newest.
        versions = [
            os.path.join(platform_dir, d)
            for d in os.listdir(platform_dir)
            if os.path.isdir(os.path.join(platform_dir, d))
        ]
        versions.sort(reverse=True)
        for v in versions:
            candidate = os.path.join(v, "MpCmdRun.exe")
            if os.path.isfile(candidate):
                return candidate

    return None


MPCMDRUN_PATH = find_mpcmdrun()

# ---------------------------------------------------------------------------
# GUI Application
# ---------------------------------------------------------------------------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class VirusScannerApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Virus Scanner - Drive Watcher")
        self.root.geometry("700x600")
        
        self.watcher_running = False
        self.watcher_thread = None
        self.scan_history = []
        self.active_scans = {}  # {drive_letter: {"thread": thread, "progress": float}}
        
        self._setup_ui()
        
    def _setup_ui(self):
        # Main container
        main_frame = ctk.CTkFrame(self.root, fg_color="#1a1a2e")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header = ctk.CTkFrame(main_frame, fg_color="#16213e", corner_radius=8)
        header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            header,
            text="🦠 Virus Scanner - Drive Watcher",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#e94560"
        ).pack(side="left", padx=15, pady=12)
        
        # Status indicator
        self.status_label = ctk.CTkLabel(
            header,
            text="● Stopped",
            font=ctk.CTkFont(size=12),
            text_color="#666666"
        )
        self.status_label.pack(side="right", padx=15)
        
        # Control panel
        control_frame = ctk.CTkFrame(main_frame, fg_color="#16213e", corner_radius=8)
        control_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            control_frame,
            text=f"Watching drives: {WATCH_RANGE[0]}: through {WATCH_RANGE[-1]}:",
            font=ctk.CTkFont(size=11),
            text_color="#a0a0a0"
        ).pack(side="left", padx=15, pady=12)
        
        if MPCMDRUN_PATH:
            ctk.CTkLabel(
                control_frame,
                text="✓ Defender found",
                font=ctk.CTkFont(size=11),
                text_color="#2ecc71"
            ).pack(side="left", padx=(10, 15), pady=12)
        else:
            ctk.CTkLabel(
                control_frame,
                text="✗ Defender not found",
                font=ctk.CTkFont(size=11),
                text_color="#e94560"
            ).pack(side="left", padx=(10, 15), pady=12)
        
        self.start_btn = ctk.CTkButton(
            control_frame,
            text="Start Watching",
            width=120,
            height=32,
            fg_color="#2ecc71",
            hover_color="#3ae083",
            command=self.toggle_watcher
        )
        self.start_btn.pack(side="right", padx=15, pady=12)
        
        # Active scans section
        active_frame = ctk.CTkFrame(main_frame, fg_color="#16213e", corner_radius=8)
        active_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            active_frame,
            text="Active Scans",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#e94560"
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.active_scans_frame = ctk.CTkScrollableFrame(
            active_frame,
            fg_color="#0f0f1a",
            corner_radius=6,
            height=100
        )
        self.active_scans_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        # Scan history section
        history_frame = ctk.CTkFrame(main_frame, fg_color="#16213e", corner_radius=8)
        history_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            history_frame,
            text="Scan History",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#e94560"
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        # History list with columns
        self.history_tree = ttk.Treeview(
            history_frame,
            columns=("time", "drive", "result"),
            show="headings",
            height=10
        )
        self.history_tree.heading("time", text="Time")
        self.history_tree.heading("drive", text="Drive")
        self.history_tree.heading("result", text="Result")
        
        self.history_tree.column("time", width=150)
        self.history_tree.column("drive", width=80)
        self.history_tree.column("result", width=400)
        
        self.history_tree.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # Style the treeview for dark theme
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#0f0f1a", foreground="#e0e0e0", fieldbackground="#0f0f1a")
        style.configure("Treeview.Heading", background="#1a1a2e", foreground="#e94560")
        style.map("Treeview", background=[("selected", "#e94560")], foreground=[("selected", "white")])
        
    def toggle_watcher(self):
        if self.watcher_running:
            self.stop_watcher()
        else:
            self.start_watcher()
    
    def start_watcher(self):
        if not MPCMDRUN_PATH:
            self.show_error("MpCmdRun.exe not found. Windows Defender must be installed.")
            return
        
        self.watcher_running = True
        self.start_btn.configure(text="Stop Watching", fg_color="#e94560", hover_color="#ff6b6b")
        self.status_label.configure(text="● Running", text_color="#2ecc71")
        
        self.watcher_thread = threading.Thread(target=self.watch_loop, daemon=True)
        self.watcher_thread.start()
    
    def stop_watcher(self):
        self.watcher_running = False
        self.start_btn.configure(text="Start Watching", fg_color="#2ecc71", hover_color="#3ae083")
        self.status_label.configure(text="● Stopped", text_color="#666666")
    
    def show_error(self, message):
        from tkinter import messagebox
        messagebox.showerror("Error", message)
    
    def add_to_history(self, drive, result, is_threat):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Insert into treeview
        item_id = self.history_tree.insert("", "end", values=(timestamp, drive, result))
        
        # Color code based on result
        if is_threat:
            self.history_tree.tag_configure(item_id, foreground="#e94560")
        else:
            self.history_tree.tag_configure(item_id, foreground="#2ecc71")
        
        # Keep only last 50 entries
        if len(self.history_tree.get_children()) > 50:
            self.history_tree.delete(self.history_tree.get_children()[0])
    
    def add_active_scan(self, drive_letter):
        """Add an active scan to the UI"""
        frame = ctk.CTkFrame(self.active_scans_frame, fg_color="#0f0f1a", corner_radius=4)
        frame.pack(fill="x", pady=2)
        
        label = ctk.CTkLabel(
            frame,
            text=f"{drive_letter}: - Scanning...",
            font=ctk.CTkFont(size=10),
            text_color="#5dc7ff"
        )
        label.pack(side="left", padx=10, pady=5)
        
        progress = ctk.CTkProgressBar(frame, width=200, height=8)
        progress.pack(side="right", padx=10, pady=5)
        progress.set(0)
        
        self.active_scans[drive_letter] = {
            "frame": frame,
            "label": label,
            "progress": progress,
            "start_time": time.time()
        }
    
    def update_scan_progress(self, drive_letter, progress_value):
        """Update scan progress"""
        if drive_letter in self.active_scans:
            scan = self.active_scans[drive_letter]
            scan["progress"].set(progress_value)
            
            elapsed = time.time() - scan["start_time"]
            scan["label"].configure(text=f"{drive_letter}: - Scanning... ({elapsed:.0f}s)")
    
    def remove_active_scan(self, drive_letter):
        """Remove an active scan from the UI"""
        if drive_letter in self.active_scans:
            scan = self.active_scans[drive_letter]
            scan["frame"].destroy()
            del self.active_scans[drive_letter]
    
    def get_current_drives(self):
        """Return the set of currently mounted drive letters (single uppercase
        chars, no colon) within the watched range."""
        drives = set()
        for part in psutil.disk_partitions(all=False):
            # part.device looks like 'D:\\'
            letter = part.device.rstrip("\\").rstrip(":").upper()
            if letter in WATCH_RANGE:
                drives.add(letter)
        return drives
    
    def watch_loop(self):
        """Main watcher loop"""
        print("Drive Scan Watcher started.")
        known_drives = self.get_current_drives()
        
        try:
            while self.watcher_running:
                time.sleep(POLL_INTERVAL_SECONDS)
                current_drives = self.get_current_drives()
                new_drives = current_drives - known_drives
                
                for letter in sorted(new_drives):
                    if self.watcher_running:
                        threading.Thread(target=self.scan_drive, args=(letter,), daemon=True).start()
                
                known_drives = current_drives
        except Exception as e:
            print(f"Watcher error: {e}")
            self.root.after(0, lambda: self.show_error(f"Watcher error: {e}"))
            self.root.after(0, self.stop_watcher)
    
    def scan_drive(self, drive_letter):
        """Run a Windows Defender scan on drive_letter (e.g. 'D')"""
        drive_path = f"{drive_letter}:\\"
        print(f"[{time.strftime('%H:%M:%S')}] New drive detected: {drive_path} -- starting scan...")
        
        # Add to active scans
        self.root.after(0, lambda: self.add_active_scan(drive_letter))
        
        if not MPCMDRUN_PATH:
            msg = (
                "Could not find Windows Defender's MpCmdRun.exe on this system.\n"
                "Make sure Windows Defender is installed and enabled."
            )
            print(msg)
            self.root.after(0, lambda: self.add_to_history(drive_path, "Error: MpCmdRun.exe not found", True))
            self.root.after(0, lambda: self.remove_active_scan(drive_letter))
            return
        
        try:
            # Start the scan process
            process = subprocess.Popen(
                [MPCMDRUN_PATH, "-Scan", "-ScanType", "3", "-File", drive_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Simulate progress updates (since MpCmdRun doesn't provide progress)
            start_time = time.time()
            while process.poll() is None:
                elapsed = time.time() - start_time
                progress = min(0.9, elapsed / 300)  # Cap at 90% over 5 minutes
                self.root.after(0, lambda d=drive_letter, p=progress: self.update_scan_progress(d, p))
                time.sleep(1)
            
            stdout, stderr = process.communicate()
            output = (stdout or "") + (stderr or "")
            returncode = process.returncode
            
        except Exception as e:
            msg = f"Scan failed to run: {e}"
            print(msg)
            self.root.after(0, lambda: self.add_to_history(drive_path, f"Error: {e}", True))
            self.root.after(0, lambda: self.remove_active_scan(drive_letter))
            return
        
        # Complete progress
        self.root.after(0, lambda d=drive_letter: self.update_scan_progress(d, 1.0))
        
        print(output.strip())
        print(f"[{time.strftime('%H:%M:%S')}] Scan of {drive_path} finished (exit code {returncode}).")
        
        # Determine result
        output_lower = output.lower()
        threat_found = (
            returncode == 2
            or ("threat" in output_lower and "no threats" not in output_lower and "0 threat" not in output_lower)
        )
        
        if threat_found:
            result_text = f"THREAT(S) FOUND - See console for details"
            self.root.after(0, lambda: self.add_to_history(drive_path, result_text, True))
        else:
            result_text = "No threats detected"
            self.root.after(0, lambda: self.add_to_history(drive_path, result_text, False))
        
        # Remove from active scans after a short delay
        self.root.after(0, lambda d=drive_letter: self.remove_active_scan(d))
    
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = VirusScannerApp()
    app.run()
