"""
Drive Scan Watcher
-------------------
Watches drive letters D: through O: for newly plugged-in drives (USB sticks,
external HDDs, etc.) and automatically runs a Windows Defender scan on each
new drive as soon as it's detected. Shows a popup window with the result:
"No threats detected" or "THREAT(S) FOUND".

Requirements:
    pip install psutil

Notes:
    - Uses the built-in Windows Defender command line scanner (MpCmdRun.exe),
      so no extra antivirus software is required.
    - Run this from a normal console window (python drive_scan_watcher.py) and
      just leave it open. Press Ctrl+C to stop.
    - Drive range watched: D: to O: (change WATCH_RANGE below if you want a
      different range).
"""

import os
import sys
import time
import string
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox

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
# Popup handling (tkinter needs a hidden root + must run on the main thread's
# mainloop, so scans run in background threads and hand results back via a
# thread-safe queue-like call using root.after).
# ---------------------------------------------------------------------------

_root = tk.Tk()
_root.withdraw()  # hide the empty root window


def show_popup(title, message, is_threat):
    """Show the result popup. Safe to call from a background thread; it
    schedules the actual popup on the Tk main thread."""

    def _do_popup():
        if is_threat:
            messagebox.showwarning(title, message)
        else:
            messagebox.showinfo(title, message)

    _root.after(0, _do_popup)


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------


def scan_drive(drive_letter):
    """Run a Windows Defender scan on drive_letter (e.g. 'D') and pop up the
    result. Runs in its own thread so the watcher keeps polling."""

    drive_path = f"{drive_letter}:\\"
    print(f"[{time.strftime('%H:%M:%S')}] New drive detected: {drive_path} -- starting scan...")

    if not MPCMDRUN_PATH:
        msg = (
            "Could not find Windows Defender's MpCmdRun.exe on this system.\n"
            "Make sure Windows Defender is installed and enabled."
        )
        print(msg)
        show_popup(f"Scan error - {drive_path}", msg, is_threat=True)
        return

    try:
        result = subprocess.run(
            [MPCMDRUN_PATH, "-Scan", "-ScanType", "3", "-File", drive_path],
            capture_output=True,
            text=True,
            timeout=60 * 30,  # 30 min safety cap for large drives
        )
    except Exception as e:
        msg = f"Scan failed to run: {e}"
        print(msg)
        show_popup(f"Scan error - {drive_path}", msg, is_threat=True)
        return

    output = (result.stdout or "") + (result.stderr or "")
    print(output.strip())
    print(f"[{time.strftime('%H:%M:%S')}] Scan of {drive_path} finished (exit code {result.returncode}).")

    # MpCmdRun.exe exit codes: 0 = no threats found, 2 = threats found and
    # (attempted to be) remediated. Fall back to checking the output text
    # too, in case the exit code isn't available for some reason.
    output_lower = output.lower()
    threat_found = (
        result.returncode == 2
        or "threat" in output_lower and "no threats" not in output_lower and "0 threat" not in output_lower
    )

    if threat_found:
        show_popup(
            f"Virus Scan - {drive_path}",
            f"THREAT(S) FOUND on drive {drive_path}\n\nSee console output for details.",
            is_threat=True,
        )
    else:
        show_popup(
            f"Virus Scan - {drive_path}",
            f"No threats detected on drive {drive_path}",
            is_threat=False,
        )


# ---------------------------------------------------------------------------
# Watcher loop
# ---------------------------------------------------------------------------


def get_current_drives():
    """Return the set of currently mounted drive letters (single uppercase
    chars, no colon) within the watched range."""
    drives = set()
    for part in psutil.disk_partitions(all=False):
        # part.device looks like 'D:\\'
        letter = part.device.rstrip("\\").rstrip(":").upper()
        if letter in WATCH_RANGE:
            drives.add(letter)
    return drives


def watch_loop():
    print("Drive Scan Watcher started.")
    print(f"Watching drives: {WATCH_RANGE[0]}: through {WATCH_RANGE[-1]}:")
    if MPCMDRUN_PATH:
        print(f"Using Defender scanner: {MPCMDRUN_PATH}")
    else:
        print("WARNING: MpCmdRun.exe not found - scans will fail until the path is corrected.")
    print("Press Ctrl+C to stop.\n")

    known_drives = get_current_drives()

    try:
        while True:
            time.sleep(POLL_INTERVAL_SECONDS)
            current_drives = get_current_drives()
            new_drives = current_drives - known_drives

            for letter in sorted(new_drives):
                threading.Thread(target=scan_drive, args=(letter,), daemon=True).start()

            known_drives = current_drives
    except KeyboardInterrupt:
        print("\nStopping Drive Scan Watcher.")


if __name__ == "__main__":
    # Run the polling loop in a background thread, and use the Tk mainloop
    # on the main thread so popups can actually display.
    watcher_thread = threading.Thread(target=watch_loop, daemon=True)
    watcher_thread.start()
    _root.mainloop()