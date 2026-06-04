import ctypes
import json
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk


APP_TITLE = "Port Checker"
WINDOW_SIZE = "1180x720"
BG = "#0b1220"
CARD_BG = "#131c2e"
CARD_BORDER = "#22304b"
TEXT = "#e6edf7"
MUTED = "#9fb0c8"
ACCENT = "#5dc7ff"
GREEN = "#2ecc71"
RED = "#ff6b6b"
AMBER = "#f5b942"

VIDEO_OUTPUT_TECH = {
    5: "DVI",
    6: "HDMI",
    10: "DisplayPort",
}


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin():
    try:
        params = " ".join(f'"{arg}"' for arg in sys.argv)
        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            params,
            None,
            1,
        )
        return result > 32
    except Exception:
        return False


def normalize_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def run_powershell_json(script):
    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    if completed.returncode != 0:
        stderr = (completed.stderr or completed.stdout or "Unknown PowerShell error").strip()
        raise RuntimeError(stderr)

    raw = (completed.stdout or "").strip()
    if not raw:
        return {}
    return json.loads(raw)


def get_snapshot():
    script = r"""
$ErrorActionPreference = 'Stop'

$monitors = @()
try {
    $monitors = Get-CimInstance -Namespace root\wmi -ClassName WmiMonitorConnectionParams |
        Select-Object InstanceName, VideoOutputTechnology, Active
} catch {
    $monitors = @()
}

$adapters = @()
try {
    $adapters = Get-NetAdapter -Physical |
        Select-Object Name, Status, MediaConnectionState, InterfaceDescription
} catch {
    $adapters = @()
}

$pnp = @()
try {
    $pnp = Get-PnpDevice -PresentOnly |
        Where-Object { $_.Class -in @('USB', 'AudioEndpoint', 'MEDIA', 'Net') } |
        Select-Object Class, FriendlyName, InstanceId, Status
} catch {
    $pnp = @()
}

[pscustomobject]@{
    monitors = $monitors
    adapters = $adapters
    pnp      = $pnp
} | ConvertTo-Json -Compress -Depth 5
"""
    data = run_powershell_json(script)
    data["monitors"] = normalize_list(data.get("monitors"))
    data["adapters"] = normalize_list(data.get("adapters"))
    data["pnp"] = normalize_list(data.get("pnp"))
    return data


def format_lines(lines):
    return "\n".join(f"- {line}" for line in lines) if lines else "- No matching devices found"


def match_any(text, patterns):
    text = (text or "").lower()
    return any(pattern in text for pattern in patterns)


def detect_usb(pnp_devices):
    matches = []
    for item in pnp_devices:
        if item.get("Class") != "USB":
            continue
        name = item.get("FriendlyName") or ""
        instance_id = item.get("InstanceId") or ""
        lowered = name.lower()
        if any(skip in lowered for skip in ("hub", "host controller", "root hub")):
            continue
        if not instance_id.upper().startswith("USB\\"):
            continue
        matches.append(name or instance_id)

    if matches:
        return {
            "status": "CONNECTED",
            "color": GREEN,
            "summary": f"{len(matches)} USB device(s) detected",
            "details": format_lines(matches[:6]),
        }

    return {
        "status": "NOT DETECTED",
        "color": RED,
        "summary": "No external USB device detected",
        "details": "- Internal hubs and controllers were ignored",
    }


def detect_display(monitors, target_code, label):
    matches = []
    for item in monitors:
        if not item.get("Active"):
            continue
        if int(item.get("VideoOutputTechnology", -1)) == target_code:
            matches.append(item.get("InstanceName", "Active display"))

    if matches:
        return {
            "status": "CONNECTED",
            "color": GREEN,
            "summary": f"{label} display connection detected",
            "details": format_lines(matches),
        }

    return {
        "status": "NOT DETECTED",
        "color": RED,
        "summary": f"No active {label} display detected",
        "details": "- Based on active monitor connection data",
    }


def detect_ethernet(adapters):
    matches = []
    for item in adapters:
        name = item.get("Name") or ""
        desc = item.get("InterfaceDescription") or ""
        status = str(item.get("Status") or "")
        media_state = str(item.get("MediaConnectionState") or "")
        haystack = f"{name} {desc}".lower()
        if "ethernet" not in haystack and "802.3" not in haystack:
            continue
        if status.lower() == "up" or media_state == "1":
            matches.append(f"{name} ({desc})")

    if matches:
        return {
            "status": "CONNECTED",
            "color": GREEN,
            "summary": "Ethernet link is up",
            "details": format_lines(matches),
        }

    return {
        "status": "NOT DETECTED",
        "color": RED,
        "summary": "No active ethernet link detected",
        "details": "- Checks physical adapters that currently report link-up",
    }


def detect_audio_jack(pnp_devices):
    matches = []
    for item in pnp_devices:
        if item.get("Class") != "AudioEndpoint":
            continue
        name = item.get("FriendlyName") or ""
        lowered = name.lower()
        if any(skip in lowered for skip in ("display audio", "intel(", "nvidia", "amd hd audio", "usb")):
            continue
        if match_any(lowered, ("headphone", "headset", "line in", "line-in", "line out", "line-out", "mic in", "front mic")):
            matches.append(name)

    if matches:
        return {
            "status": "LIKELY CONNECTED",
            "color": AMBER,
            "summary": "Wired audio endpoint likely detected",
            "details": format_lines(matches) + "\n- Windows jack sensing is hardware-dependent",
        }

    return {
        "status": "NOT DETECTED",
        "color": RED,
        "summary": "No wired audio-jack endpoint detected",
        "details": "- Some PCs do not expose 3.5mm plug-state to Windows",
    }


def detect_usb_c(pnp_devices):
    strong_matches = []
    for item in pnp_devices:
        name = item.get("FriendlyName") or ""
        lowered = name.lower()
        if match_any(lowered, ("usb-c", "type-c", "usb4", "thunderbolt", "billboard", "dock")):
            strong_matches.append(name)

    if strong_matches:
        return {
            "status": "LIKELY CONNECTED",
            "color": AMBER,
            "summary": "USB-C or dock-related device likely detected",
            "details": format_lines(strong_matches[:6]) + "\n- USB-C plug-state is often not exposed directly",
        }

    return {
        "status": "UNKNOWN",
        "color": AMBER,
        "summary": "No clear USB-C-specific device evidence",
        "details": "- Many systems cannot reliably report whether a USB-C port is occupied",
    }


def build_results(snapshot):
    monitors = snapshot.get("monitors", [])
    adapters = snapshot.get("adapters", [])
    pnp_devices = snapshot.get("pnp", [])
    return {
        "USB": detect_usb(pnp_devices),
        "HDMI": detect_display(monitors, 6, "HDMI"),
        "DisplayPort": detect_display(monitors, 10, "DisplayPort"),
        "Audio Jack": detect_audio_jack(pnp_devices),
        "Ethernet": detect_ethernet(adapters),
        "USB-C": detect_usb_c(pnp_devices),
    }


class PortCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.configure(bg=BG)
        self.root.minsize(980, 620)

        self.auto_refresh = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Ready")
        self.updated_var = tk.StringVar(value="Last updated: never")
        self.cards = {}
        self.refresh_in_progress = False

        self._build_ui()
        self.refresh()
        self._schedule_refresh()

    def _build_ui(self):
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill="x", padx=20, pady=(18, 12))

        title = tk.Label(
            top,
            text="Port Checker",
            font=("Segoe UI Semibold", 24),
            fg=TEXT,
            bg=BG,
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            top,
            text="Live best-effort detection for USB, HDMI, DisplayPort, audio jack, ethernet, and USB-C on Windows.",
            font=("Segoe UI", 11),
            fg=MUTED,
            bg=BG,
        )
        subtitle.pack(anchor="w", pady=(4, 10))

        toolbar = tk.Frame(top, bg=BG)
        toolbar.pack(fill="x")

        refresh_btn = tk.Button(
            toolbar,
            text="Refresh Now",
            command=self.refresh,
            bg=ACCENT,
            fg="#04111d",
            activebackground="#82d9ff",
            activeforeground="#04111d",
            relief="flat",
            padx=16,
            pady=8,
            font=("Segoe UI Semibold", 10),
            cursor="hand2",
        )
        refresh_btn.pack(side="left")

        auto_check = tk.Checkbutton(
            toolbar,
            text="Auto refresh every 5 seconds",
            variable=self.auto_refresh,
            bg=BG,
            fg=TEXT,
            activebackground=BG,
            activeforeground=TEXT,
            selectcolor=CARD_BG,
            font=("Segoe UI", 10),
        )
        auto_check.pack(side="left", padx=(14, 0))

        if not is_admin():
            elevate_btn = tk.Button(
                toolbar,
                text="Relaunch as Admin",
                command=self._elevate,
                bg="#243145",
                fg=TEXT,
                activebackground="#30425d",
                activeforeground=TEXT,
                relief="flat",
                padx=14,
                pady=8,
                font=("Segoe UI Semibold", 10),
                cursor="hand2",
            )
            elevate_btn.pack(side="left", padx=(14, 0))

        info = tk.Label(
            toolbar,
            textvariable=self.updated_var,
            font=("Segoe UI", 10),
            fg=MUTED,
            bg=BG,
        )
        info.pack(side="right")

        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            font=("Segoe UI", 10),
            fg=MUTED,
            bg=BG,
        )
        status_bar.pack(fill="x", padx=20, pady=(0, 10))

        grid = tk.Frame(self.root, bg=BG)
        grid.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_columnconfigure(2, weight=1)

        ports = ["USB", "HDMI", "DisplayPort", "Audio Jack", "Ethernet", "USB-C"]
        for index, name in enumerate(ports):
            row, col = divmod(index, 3)
            card = self._build_card(grid, name)
            card["frame"].grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
            grid.grid_rowconfigure(row, weight=1)
            self.cards[name] = card

        note = tk.Label(
            self.root,
            text="Note: HDMI and DisplayPort are usually reliable. Audio-jack and USB-C status can be limited by the chipset and driver stack.",
            font=("Segoe UI", 10),
            fg=MUTED,
            bg=BG,
            wraplength=1080,
            justify="left",
        )
        note.pack(fill="x", padx=20, pady=(0, 16))

    def _build_card(self, parent, name):
        frame = tk.Frame(parent, bg=CARD_BG, highlightthickness=1, highlightbackground=CARD_BORDER)
        header = tk.Label(
            frame,
            text=name,
            font=("Segoe UI Semibold", 18),
            fg=TEXT,
            bg=CARD_BG,
        )
        header.pack(anchor="w", padx=18, pady=(16, 8))

        status = tk.Label(
            frame,
            text="Waiting",
            font=("Segoe UI Semibold", 15),
            fg=AMBER,
            bg=CARD_BG,
        )
        status.pack(anchor="w", padx=18)

        summary = tk.Label(
            frame,
            text="No data yet",
            font=("Segoe UI", 11),
            fg=TEXT,
            bg=CARD_BG,
            wraplength=320,
            justify="left",
        )
        summary.pack(anchor="w", padx=18, pady=(10, 8))

        details = tk.Label(
            frame,
            text="",
            font=("Consolas", 10),
            fg=MUTED,
            bg=CARD_BG,
            wraplength=320,
            justify="left",
            anchor="nw",
        )
        details.pack(fill="both", expand=True, anchor="nw", padx=18, pady=(0, 18))

        return {
            "frame": frame,
            "status": status,
            "summary": summary,
            "details": details,
        }

    def _elevate(self):
        self.status_var.set("Requesting administrator privileges...")
        if relaunch_as_admin():
            self.root.after(250, self.root.destroy)
        else:
            self.status_var.set("Unable to relaunch as admin.")

    def _schedule_refresh(self):
        if self.auto_refresh.get() and not self.refresh_in_progress:
            self.refresh()
        self.root.after(5000, self._schedule_refresh)

    def refresh(self):
        if self.refresh_in_progress:
            return
        self.refresh_in_progress = True
        self.status_var.set("Refreshing hardware status...")
        thread = threading.Thread(target=self._refresh_worker, daemon=True)
        thread.start()

    def _refresh_worker(self):
        try:
            snapshot = get_snapshot()
            results = build_results(snapshot)
            self.root.after(0, lambda: self._apply_results(results))
        except Exception as exc:
            self.root.after(0, lambda: self._show_error(str(exc)))

    def _apply_results(self, results):
        for port_name, result in results.items():
            card = self.cards[port_name]
            card["status"].configure(text=result["status"], fg=result["color"])
            card["summary"].configure(text=result["summary"])
            card["details"].configure(text=result["details"])

        now = time.strftime("%Y-%m-%d %I:%M:%S %p")
        self.updated_var.set(f"Last updated: {now}")
        self.status_var.set("Refresh complete")
        self.refresh_in_progress = False

    def _show_error(self, message):
        for card in self.cards.values():
            card["status"].configure(text="ERROR", fg=RED)
            card["summary"].configure(text="Hardware query failed")
            card["details"].configure(text=f"- {message}")
        self.status_var.set("Refresh failed")
        self.refresh_in_progress = False


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass
    app = PortCheckerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
