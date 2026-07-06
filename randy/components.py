"""
Graphical UI for HPLENDELLDEV8.ps1 system and component reporting.
"""

import ctypes
import os
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk


APP_TITLE = "Components"
WINDOW_SIZE = "1180x820"
DEFAULT_SCRIPT = "HPLENDELLDEV8.ps1"
REPORT_FILENAME = "components-report.txt"
SCAN_TIMEOUT = 180

BG = "#0b1220"
CARD_BG = "#131c2e"
CARD_BORDER = "#22304b"
TEXT = "#e6edf7"
MUTED = "#9fb0c8"
ACCENT = "#5dc7ff"
GREEN = "#2ecc71"
RED = "#ff6b6b"
AMBER = "#f5b942"

COMPONENT_ORDER = [
    ("Fingerprint", "fingerprint"),
    ("WWAN", "wwan"),
    ("WLAN", "wlan"),
    ("Privacy", "privacy"),
    ("RGB", "rgb"),
    ("Backlight", "backlight"),
    ("NFC", "nfc"),
    ("Smartcard", "smartcard"),
]

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
SW_HIDE = 0


def _hidden_startupinfo():
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = SW_HIDE
    return startupinfo


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin():
    try:
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
    except Exception:
        return False


def _report_is_complete(text):
    return bool(text) and ("System Serial:" in text or "System Model:" in text)


def _read_transcript_log(log_path):
    if not os.path.isfile(log_path):
        return ""

    with open(log_path, encoding="utf-8", errors="replace") as handle:
        content = handle.read()

    marker = "Windows PowerShell transcript start"
    start = content.rfind(marker)
    if start < 0:
        return content

    body = content[start:]
    end = body.find("Windows PowerShell transcript end")
    if end >= 0:
        body = body[:end]

    for needle in ("Detected manufacturer:", "Device Manager Component Check", "System Info"):
        idx = body.find(needle)
        if idx >= 0:
            return body[idx:]
    return body


def _ps_single_quoted(path):
    return path.replace("'", "''")


def _read_text_file(path):
    if not os.path.isfile(path):
        return ""

    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            with open(path, encoding=encoding, errors="replace") as handle:
                return handle.read()
        except (UnicodeError, UnicodeDecodeError):
            continue

    with open(path, errors="replace") as handle:
        return handle.read()


def _resolve_report_text(script_path):
    base_dir = os.path.dirname(os.path.abspath(script_path))
    candidates = [
        os.path.join(base_dir, REPORT_FILENAME),
        f"{os.path.splitext(script_path)[0]}.log",
    ]

    for path in candidates:
        if path.endswith(".log"):
            text = _read_transcript_log(path)
        else:
            text = _read_text_file(path)

        if _report_is_complete(text):
            return text

    for path in candidates:
        text = _read_text_file(path) if not path.endswith(".log") else _read_transcript_log(path)
        if text.strip():
            return text

    return ""


def run_hardware_script(script_path):
    if not os.path.isfile(script_path):
        raise FileNotFoundError(f"Script not found: {script_path}")

    script_path = os.path.abspath(script_path)
    base_dir = os.path.dirname(script_path)
    report_path = os.path.join(base_dir, REPORT_FILENAME)

    try:
        if os.path.isfile(report_path):
            os.remove(report_path)
    except OSError:
        pass

    ps_command = (
        f"$report = '{_ps_single_quoted(report_path)}'; "
        f"$script = '{_ps_single_quoted(script_path)}'; "
        f"& $script -Silent *>&1 | ForEach-Object {{ Out-String -InputObject $_ }} | "
        f"Out-File -LiteralPath $report -Encoding utf8; "
        f"exit $LASTEXITCODE"
    )

    proc = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-WindowStyle",
            "Hidden",
            "-Command",
            ps_command,
        ],
        capture_output=True,
        text=True,
        timeout=SCAN_TIMEOUT,
        creationflags=CREATE_NO_WINDOW,
        startupinfo=_hidden_startupinfo(),
    )

    # Give the filesystem a moment on slower disks.
    for _ in range(20):
        output = _resolve_report_text(script_path)
        if _report_is_complete(output):
            return output
        time.sleep(0.25)

    if proc.returncode not in (0, None) and not _report_is_complete(output):
        detail = (proc.stderr or proc.stdout or "").strip()
        if not detail:
            detail = f"PowerShell exited with code {proc.returncode}."
        raise RuntimeError(detail)

    if not _report_is_complete(output):
        raise RuntimeError(
            "Hardware scan returned no system data. Run Components as Administrator and try Refresh Scan."
        )

    return output


KNOWN_SECTIONS = {
    "system info",
    "display",
    "cpu info",
    "hard drives",
    "memory",
    "gpu info",
    "computrace check",
    "detected components",
}


def _normalize_section(line):
    stripped = line.strip()
    if not stripped or stripped.startswith("="):
        return None

    lower = stripped.lower()
    if lower.startswith("device manager component check"):
        return None

    for section in KNOWN_SECTIONS:
        if lower == section or lower.startswith(section):
            return section

    return None


def parse_report(text):
    data = {
        "manufacturer": "",
        "system": {},
        "displays": [],
        "cpus": [],
        "disks": [],
        "memory": [],
        "gpus": [],
        "computrace": {"summary": "", "findings": []},
        "components": {},
        "bios_comparison": [],
        "raw_sections": {},
    }

    for label, _key in COMPONENT_ORDER:
        data["components"][label] = {"present": False, "detail": ""}

    mfg = re.search(r"Detected manufacturer:\s*(.+)", text, re.I)
    if mfg:
        data["manufacturer"] = mfg.group(1).strip()

    current_section = None
    current_display = None
    current_disk = None

    component_line = re.compile(r"^\[(X| )\]\s+(.+?)\s+:\s+(Yes|No)\s*$", re.I)
    detail_line = re.compile(r"^\s+Detail:\s*(.+)$", re.I)
    kv_line = re.compile(r"^([^:]+):\s*(.+)$")

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("="):
            continue

        section_name = _normalize_section(stripped)
        if section_name:
            current_section = section_name
            data["raw_sections"].setdefault(section_name, [])
            continue

        if current_section:
            data["raw_sections"].setdefault(current_section, []).append(line)

        comp_match = component_line.match(line)
        if comp_match:
            checked, label, status = comp_match.groups()
            label = label.strip()
            data["components"][label] = {
                "present": checked.upper() == "X" or status.lower() == "yes",
                "detail": "",
            }
            continue

        det_match = detail_line.match(line)
        if det_match and data["components"]:
            for label in reversed(list(data["components"].keys())):
                entry = data["components"][label]
                if entry["present"] and not entry["detail"]:
                    entry["detail"] = det_match.group(1).strip()
                    break
            continue

        if (
            current_section == "computrace check"
            and stripped
            and not stripped.startswith("PS>")
            and ":" not in stripped
            and not data["computrace"]["summary"]
        ):
            data["computrace"]["summary"] = stripped
            continue

        kv = kv_line.match(stripped)
        if not kv or not current_section:
            continue

        key, value = kv.group(1).strip(), kv.group(2).strip()
        section = current_section or ""

        if section == "system info":
            data["system"][key] = value
        elif section == "display":
            if key == "Manufacturer":
                if current_display:
                    data["displays"].append(current_display)
                current_display = {}
            if current_display is None:
                current_display = {}
            current_display[key] = value
        elif section == "cpu info":
            if key == "Name":
                data["cpus"].append({})
            if data["cpus"]:
                data["cpus"][-1][key] = value
        elif section == "hard drives":
            if key == "Model":
                current_disk = {"Model": value}
                data["disks"].append(current_disk)
            elif key == "Size" and current_disk is not None:
                current_disk["Size"] = value
            elif key == "Total":
                data["disk_total"] = value
        elif section == "memory":
            if key == "Name":
                data["memory"].append({"Name": value})
            elif key == "Size" and data["memory"]:
                data["memory"][-1]["Size"] = value
        elif section == "gpu info":
            if key == "Name":
                data["gpus"].append({"Name": value})
            elif key == "Video Memory" and data["gpus"]:
                data["gpus"][-1]["Video Memory"] = value
        elif section == "computrace check":
            if key == "Details":
                if data["computrace"]["findings"]:
                    data["computrace"]["findings"][-1]["details"] = value
            elif key in ("Process", "Service", "Driver", "Registry", "BIOS", "ScheduledTask", "File"):
                data["computrace"]["findings"].append(
                    {"category": key, "name": value, "details": ""}
                )
            elif not data["computrace"]["summary"] and stripped and not stripped.startswith("PS>"):
                data["computrace"]["summary"] = stripped

    if current_display:
        data["displays"].append(current_display)

    table_section = False
    headers = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if "bios vs device manager comparison" in stripped.lower():
            table_section = True
            headers = []
            continue
        if table_section:
            if not stripped or stripped.startswith("-"):
                continue
            if not headers and "Feature" in stripped and "BIOS" in stripped:
                headers = stripped.split()
                continue
            if headers and not stripped.startswith("="):
                parts = re.split(r"\s{2,}", stripped)
                if len(parts) >= 2:
                    row = {"Feature": parts[0]}
                    for idx, header in enumerate(headers[1:], start=1):
                        if idx < len(parts):
                            row[header] = parts[idx]
                    data["bios_comparison"].append(row)
            if stripped.startswith("="):
                table_section = False

    return data


class ComponentsApp:
    def __init__(self, root):
        self.root = root
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.script_path = os.path.join(self.base_dir, DEFAULT_SCRIPT)
        self.component_vars = {}
        self.component_labels = {}
        self.component_detected = {}
        self.scan_thread = None
        self.is_scanning = False

        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(960, 680)
        self.root.configure(bg=BG)

        self._configure_styles()
        self._build_ui()
        self.root.after(300, self.refresh)

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("App.TFrame", background=BG)
        style.configure("Card.TFrame", background=CARD_BG)
        style.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 20, "bold"))
        style.configure("Sub.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 10))
        style.configure("Section.TLabel", background=CARD_BG, foreground=ACCENT, font=("Segoe UI", 11, "bold"))
        style.configure("Body.TLabel", background=CARD_BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=CARD_BG, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Status.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 10))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
        style.map(
            "Accent.TButton",
            background=[("active", "#3aa9e0"), ("!disabled", ACCENT)],
            foreground=[("!disabled", BG)],
        )

    def _build_ui(self):
        outer = ttk.Frame(self.root, style="App.TFrame", padding=16)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer, style="App.TFrame")
        header.pack(fill="x", pady=(0, 12))

        ttk.Label(header, text=APP_TITLE, style="Title.TLabel").pack(side="left")
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(header, textvariable=self.status_var, style="Status.TLabel").pack(side="right", padx=(12, 0))

        sub = ttk.Frame(outer, style="App.TFrame")
        sub.pack(fill="x", pady=(0, 10))
        self.manufacturer_var = tk.StringVar(value="Manufacturer: —")
        ttk.Label(sub, textvariable=self.manufacturer_var, style="Sub.TLabel").pack(side="left")
        ttk.Button(sub, text="Refresh Scan", style="Accent.TButton", command=self.refresh).pack(side="right")

        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self.body = ttk.Frame(canvas, style="App.TFrame")

        self.body.bind(
            "<Configure>",
            lambda _e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self.body, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.sections = {}
        self.section_cards = {}
        self._add_section("system", "System Info")
        self._add_section("display", "Display")
        self._add_section("cpu", "CPU")
        self._add_section("drives", "Hard Drives")
        self._add_section("memory", "Memory")
        self._add_section("gpu", "GPU")
        self._add_section("computrace", "Computrace Check")
        self._build_components_section()
        self._add_section("bios", "BIOS vs Device Manager")

    def _add_section(self, key, title):
        card = tk.Frame(self.body, bg=CARD_BORDER, padx=1, pady=1)
        card.pack(fill="x", pady=(0, 10))

        inner = ttk.Frame(card, style="Card.TFrame", padding=12)
        inner.pack(fill="both", expand=True)

        ttk.Label(inner, text=title, style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        content = ttk.Frame(inner, style="Card.TFrame")
        content.pack(fill="x")
        self.sections[key] = content
        self.section_cards[key] = card

    def _build_components_section(self):
        card = tk.Frame(self.body, bg=CARD_BORDER, padx=1, pady=1)
        card.pack(fill="x", pady=(0, 10))

        inner = ttk.Frame(card, style="Card.TFrame", padding=12)
        inner.pack(fill="both", expand=True)

        ttk.Label(inner, text="Detected Components", style="Section.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Label(
            inner,
            text="Auto-filled from scan — check or uncheck manually as needed.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(0, 8))

        grid = tk.Frame(inner, bg=CARD_BG)
        grid.pack(fill="x")

        for idx, (label, _key) in enumerate(COMPONENT_ORDER):
            var = tk.BooleanVar(value=False)
            row = idx // 4
            col = idx % 4

            cell = tk.Frame(grid, bg=CARD_BG)
            cell.grid(row=row, column=col, sticky="w", padx=10, pady=6)

            cb = tk.Checkbutton(
                cell,
                text=label,
                variable=var,
                bg=CARD_BG,
                fg=TEXT,
                selectcolor="#1f6fbf",
                activebackground=CARD_BG,
                activeforeground=TEXT,
                font=("Segoe UI", 10, "bold"),
                command=lambda lbl=label: self._on_component_toggle(lbl),
            )
            cb.pack(anchor="w")

            detail = ttk.Label(cell, text="", style="Muted.TLabel", wraplength=240)
            detail.pack(anchor="w", pady=(2, 0))

            self.component_vars[label] = var
            self.component_labels[label] = detail

        self.sections["components"] = grid

    def _on_component_toggle(self, label):
        detected = self.component_detected.get(label, False)
        manual = self.component_vars[label].get()
        if manual == detected:
            detail = self.component_detected.get(f"{label}__detail", "")
            if manual:
                self.component_labels[label].configure(
                    text=detail if detail else "Detected"
                )
            else:
                self.component_labels[label].configure(text="Not detected")
        else:
            self.component_labels[label].configure(text="Manual override")

    def _clear_frame(self, frame):
        for child in frame.winfo_children():
            child.destroy()

    def _add_lines(self, frame, lines):
        if not lines:
            ttk.Label(frame, text="No information found.", style="Muted.TLabel").pack(anchor="w")
            return
        for line in lines:
            ttk.Label(frame, text=line, style="Body.TLabel", wraplength=1050).pack(anchor="w", pady=1)

    def refresh(self):
        if self.is_scanning:
            return
        if not os.path.isfile(self.script_path):
            messagebox.showerror(APP_TITLE, f"Could not find {DEFAULT_SCRIPT} in:\n{self.base_dir}")
            return

        self.is_scanning = True
        self.status_var.set("Scanning hardware…")

        def worker():
            error = None
            parsed = None
            try:
                output = run_hardware_script(self.script_path)
                parsed = parse_report(output)
            except Exception as exc:
                error = str(exc)

            self.root.after(0, lambda p=parsed, e=error: self._apply_results(p, e))

        self.scan_thread = threading.Thread(target=worker, daemon=True)
        self.scan_thread.start()

    def _apply_results(self, data, error):
        self.is_scanning = False

        if error:
            self.status_var.set("Scan failed")
            messagebox.showerror(APP_TITLE, error)
            return

        assert data is not None
        self.status_var.set("Scan complete")
        mfg = data.get("manufacturer") or "Unknown"
        self.manufacturer_var.set(f"Manufacturer: {mfg}")

        system_lines = [f"{k}: {v}" for k, v in data.get("system", {}).items()]
        self._clear_frame(self.sections["system"])
        self._add_lines(self.sections["system"], system_lines)

        display_lines = []
        for display in data.get("displays", []):
            display_lines.append(
                " | ".join(f"{k}: {v}" for k, v in display.items() if v and v != "Unknown")
            )
        self._clear_frame(self.sections["display"])
        self._add_lines(self.sections["display"], display_lines or ["No display information found."])

        cpu_lines = []
        for cpu in data.get("cpus", []):
            cpu_lines.append(" | ".join(f"{k}: {v}" for k, v in cpu.items()))
        self._clear_frame(self.sections["cpu"])
        self._add_lines(self.sections["cpu"], cpu_lines)

        drive_lines = []
        for disk in data.get("disks", []):
            model = disk.get("Model", "Unknown")
            size = disk.get("Size", "—")
            drive_lines.append(f"{model} — {size}")
        total = data.get("disk_total")
        if total:
            drive_lines.append(f"Total: {total}")
        self._clear_frame(self.sections["drives"])
        self._add_lines(self.sections["drives"], drive_lines or ["No internal HDDs or SSDs detected."])

        mem_lines = [f"{m.get('Name', 'Module')} — {m.get('Size', '—')}" for m in data.get("memory", [])]
        self._clear_frame(self.sections["memory"])
        self._add_lines(self.sections["memory"], mem_lines)

        gpu_lines = []
        for gpu in data.get("gpus", []):
            gpu_lines.append(f"{gpu.get('Name', 'GPU')} — {gpu.get('Video Memory', '—')} GB VRAM")
        self._clear_frame(self.sections["gpu"])
        self._add_lines(self.sections["gpu"], gpu_lines)

        computrace = data.get("computrace", {})
        comp_lines = []
        summary = computrace.get("summary", "")
        if summary:
            comp_lines.append(summary)
        for finding in computrace.get("findings", []):
            line = f"{finding.get('category', 'Finding')}: {finding.get('name', '')}"
            if finding.get("details"):
                line += f" — {finding['details']}"
            comp_lines.append(line)
        if not comp_lines:
            comp_lines = ["No Computrace findings reported."]
        self._clear_frame(self.sections["computrace"])
        self._add_lines(self.sections["computrace"], comp_lines)

        components = data.get("components", {})
        for label, _key in COMPONENT_ORDER:
            entry = components.get(label, {})
            present = bool(entry.get("present"))
            detail = entry.get("detail") or ""
            self.component_detected[label] = present
            self.component_detected[f"{label}__detail"] = detail
            self.component_vars[label].set(present)
            self.component_labels[label].configure(
                text=detail if present and detail else ("Detected" if present else "Not detected")
            )

        bios_lines = []
        for row in data.get("bios_comparison", []):
            feature = row.get("Feature", "")
            extras = " | ".join(f"{k}: {v}" for k, v in row.items() if k != "Feature")
            bios_lines.append(f"{feature} — {extras}")
        self._clear_frame(self.sections["bios"])
        bios_card = self.section_cards.get("bios")
        if bios_lines and bios_card is not None:
            bios_card.pack(fill="x", pady=(0, 10))
            self._add_lines(self.sections["bios"], bios_lines)
        elif bios_card is not None:
            bios_card.pack_forget()


def main():
    if not is_admin():
        if relaunch_as_admin():
            sys.exit(0)
        messagebox.showerror(
            APP_TITLE,
            "Administrator access is required to run the hardware scan silently.",
        )
        sys.exit(1)

    root = tk.Tk()
    ComponentsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
