import json
import subprocess
import sys


BATTERY_STATUS_MAP = {
    1: "Discharging",
    2: "Plugged in, not charging",
    3: "Fully Charged",
    4: "Low",
    5: "Critical",
    6: "Charging",
    7: "Charging (High)",
    8: "Charging (Low)",
    9: "Charging (Critical)",
    10: "Undefined",
    11: "Partially Charged",
}


def run_powershell_json(command):
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True,
        text=True,
        timeout=20,
    )
    if result.returncode != 0:
        error_text = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(error_text or "PowerShell command failed.")

    output = (result.stdout or "").strip()
    if not output:
        return None
    return json.loads(output)


def get_battery_data():
    battery_command = r"""
$battery = Get-CimInstance -ClassName Win32_Battery -ErrorAction SilentlyContinue
if (-not $battery) { $null | ConvertTo-Json -Compress; return }

[pscustomobject]@{
    Name = $battery.Name
    BatteryStatus = $battery.BatteryStatus
    EstimatedChargeRemaining = $battery.EstimatedChargeRemaining
} | ConvertTo-Json -Compress
"""

    health_command = r"""
$reportPath = Join-Path $env:TEMP 'battery-report.xml'
powercfg /batteryreport /XML /OUTPUT $reportPath | Out-Null
if (-not (Test-Path $reportPath)) { $null | ConvertTo-Json -Compress; return }

try {
    [xml]$xml = Get-Content -LiteralPath $reportPath
    $batteryNode = $xml.BatteryReport.Batteries.Battery | Select-Object -First 1

    if (-not $batteryNode) { $null | ConvertTo-Json -Compress; return }

    [pscustomobject]@{
        DesignCapacity = $batteryNode.DesignCapacity
        FullChargeCapacity = $batteryNode.FullChargeCapacity
        CycleCount = $batteryNode.CycleCount
    } | ConvertTo-Json -Compress
}
catch {
    $null | ConvertTo-Json -Compress
}
"""

    battery_info = run_powershell_json(battery_command)
    if not battery_info:
        return None

    health_info = run_powershell_json(health_command) or {}

    name = battery_info.get("Name") or "Battery"
    level = battery_info.get("EstimatedChargeRemaining")
    status_code = battery_info.get("BatteryStatus")
    status_text = BATTERY_STATUS_MAP.get(status_code, f"Unknown ({status_code})")

    design_capacity = health_info.get("DesignCapacity")
    full_charge_capacity = health_info.get("FullChargeCapacity")
    cycle_count = health_info.get("CycleCount")

    health_percent = None
    if design_capacity and full_charge_capacity:
        try:
            design_value = int(str(design_capacity).replace(",", "").strip())
            full_value = int(str(full_charge_capacity).replace(",", "").strip())
            health_percent = min(round((full_value * 100) / design_value, 1), 100.0) if design_value else None
            health_text = f"{health_percent:.1f}%"
            capacity_text = f"{full_value} / {design_value} mWh"
        except Exception:
            health_text = "Unavailable"
            capacity_text = f"{full_charge_capacity} / {design_capacity} mWh"
    else:
        health_text = "Unavailable"
        capacity_text = "Unavailable"

    return {
        "name": name,
        "level": level,
        "level_text": f"{level}%" if level not in (None, "") else "Unknown",
        "status_text": status_text,
        "health_percent": health_percent,
        "health_text": health_text,
        "capacity_text": capacity_text,
        "cycle_text": str(cycle_count) if cycle_count not in (None, "") else "Unavailable",
    }


if __name__ == "__main__":
    if "--json" in sys.argv:
        # JSON mode for web server
        try:
            data = get_battery_data()
            if not data:
                result = {
                    "ok": False,
                    "status": "fail",
                    "output": "No battery detected",
                    "data": None
                }
            else:
                result = {
                    "ok": True,
                    "status": "pass",
                    "output": "Battery data retrieved successfully",
                    "data": data
                }
            print(json.dumps(result, indent=2))
        except Exception as exc:
            error_result = {
                "ok": False,
                "status": "fail",
                "output": str(exc),
                "data": None
            }
            print(json.dumps(error_result, indent=2))
    else:
        # GUI mode (original Tkinter version)
        import tkinter as tk
        from tkinter import ttk

        class BatteryApp:
            def __init__(self, root):
                self.root = root
                self.root.title("Battery Status")
                self.root.geometry("430x320")
                self.root.configure(bg="#101820")
                self.root.resizable(False, False)

                style = ttk.Style()
                style.theme_use("clam")
                style.configure("TProgressbar", thickness=18)

                frame = tk.Frame(root, bg="#101820", padx=20, pady=20)
                frame.pack(fill="both", expand=True)

                self.title_label = tk.Label(
                    frame,
                    text="Battery Status",
                    font=("Segoe UI", 18, "bold"),
                    fg="white",
                    bg="#101820",
                )
                self.title_label.pack(anchor="w")

                self.device_label = tk.Label(
                    frame,
                    text="",
                    font=("Segoe UI", 10),
                    fg="#9fb3c8",
                    bg="#101820",
                )
                self.device_label.pack(anchor="w", pady=(2, 18))

                self.level_value = tk.Label(
                    frame,
                    text="--%",
                    font=("Segoe UI", 28, "bold"),
                    fg="#7ee787",
                    bg="#101820",
                )
                self.level_value.pack(anchor="w")

                self.level_bar = ttk.Progressbar(frame, orient="horizontal", length=360, mode="determinate", maximum=100)
                self.level_bar.pack(anchor="w", pady=(10, 18))

                self.health_label = tk.Label(
                    frame,
                    text="Battery health: --",
                    font=("Segoe UI", 12, "bold"),
                    fg="white",
                    bg="#101820",
                )
                self.health_label.pack(anchor="w", pady=(0, 8))

                self.status_label = tk.Label(
                    frame,
                    text="Status: --",
                    font=("Segoe UI", 11),
                    fg="white",
                    bg="#101820",
                )
                self.status_label.pack(anchor="w", pady=(0, 6))

                self.capacity_label = tk.Label(
                    frame,
                    text="Capacity: --",
                    font=("Segoe UI", 11),
                    fg="white",
                    bg="#101820",
                )
                self.capacity_label.pack(anchor="w", pady=(0, 6))

                self.cycle_label = tk.Label(
                    frame,
                    text="Cycle count: --",
                    font=("Segoe UI", 11),
                    fg="white",
                    bg="#101820",
                )
                self.cycle_label.pack(anchor="w", pady=(0, 14))

                self.message_label = tk.Label(
                    frame,
                    text="",
                    font=("Segoe UI", 10),
                    fg="#ffb86c",
                    bg="#101820",
                )
                self.message_label.pack(anchor="w", pady=(0, 14))

                button_row = tk.Frame(frame, bg="#101820")
                button_row.pack(fill="x")

                tk.Button(
                    button_row,
                    text="Refresh",
                    command=self.refresh,
                    font=("Segoe UI", 10, "bold"),
                    bg="#1f6feb",
                    fg="white",
                    activebackground="#388bfd",
                    activeforeground="white",
                    relief="flat",
                    padx=16,
                    pady=8,
                ).pack(side="left")

                tk.Button(
                    button_row,
                    text="Close",
                    command=self.root.destroy,
                    font=("Segoe UI", 10, "bold"),
                    bg="#30363d",
                    fg="white",
                    activebackground="#484f58",
                    activeforeground="white",
                    relief="flat",
                    padx=16,
                    pady=8,
                ).pack(side="left", padx=(10, 0))

                self.refresh()

            def refresh(self):
                try:
                    data = get_battery_data()
                    if not data:
                        self.device_label.config(text="No battery detected")
                        self.level_value.config(text="--%", fg="#ff7b72")
                        self.level_bar["value"] = 0
                        self.health_label.config(text="Battery health: Unavailable")
                        self.status_label.config(text="Status: Unavailable")
                        self.capacity_label.config(text="Capacity: Unavailable")
                        self.cycle_label.config(text="Cycle count: Unavailable")
                        self.message_label.config(text="This system may be a desktop or may not expose battery data.")
                        return

                    level = data["level"] if isinstance(data["level"], int) else 0
                    self.device_label.config(text=data["name"])
                    self.level_value.config(text=data["level_text"], fg=self._level_color(level))
                    self.level_bar["value"] = level
                    self.health_label.config(text=f"Battery health: {data['health_text']}")
                    self.status_label.config(text=f"Status: {data['status_text']}")
                    self.capacity_label.config(text=f"Capacity: {data['capacity_text']}")
                    self.cycle_label.config(text=f"Cycle count: {data['cycle_text']}")
                    self.message_label.config(text="")
                except Exception as exc:
                    self.device_label.config(text="Battery read error")
                    self.level_value.config(text="--%", fg="#ff7b72")
                    self.level_bar["value"] = 0
                    self.health_label.config(text="Battery health: Unavailable")
                    self.status_label.config(text="Status: Unavailable")
                    self.capacity_label.config(text="Capacity: Unavailable")
                    self.cycle_label.config(text="Cycle count: Unavailable")
                    self.message_label.config(text=str(exc))

            @staticmethod
            def _level_color(level):
                if level >= 60:
                    return "#7ee787"
                if level >= 25:
                    return "#e3b341"
                return "#ff7b72"

        root = tk.Tk()
        app = BatteryApp(root)
        root.mainloop()
