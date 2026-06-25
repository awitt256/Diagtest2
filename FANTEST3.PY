"""
Real Fan / Thermal Stress Test
-------------------------------
Goal: actually load every CPU core (for real, bypassing the GIL) and show
REAL temperature/fan data when it's available -- and say "not available"
instead of inventing numbers when it isn't.

Notes on what this can and can't do:

1. STRESS LOAD: uses multiprocessing.Process (not threading.Thread), so the
   work genuinely runs in parallel across physical cores. A thread-based
   "burner" in pure Python cannot do this because of the GIL -- only one
   thread runs Python bytecode at a time, so a thread-based version mostly
   loads a single core no matter how many threads you spawn.

2. TEMPERATURE: there is no cross-platform Python API for CPU temp on
   Windows. psutil.sensors_temperatures() only works on Linux/*BSD. The
   most reliable real-data path on Windows is LibreHardwareMonitor (free,
   open source) running with its WMI provider enabled, queried here via
   the `wmi` package. If that's not present, this tool tells you so --
   it does NOT fabricate a temperature curve.

3. FAN RPM: most consumer laptops/mini-PCs simply do not expose fan RPM to
   any software at all -- it's locked inside the embedded controller. If
   LibreHardwareMonitor's sensor list includes a Fan sensor for your board,
   you'll see a real number. If not, this tool says so honestly. For
   judging actual fan failure/noise, your ears (or a sound meter app) are
   the real instrument here -- software can't reliably tell you that on
   most hardware.

Setup for real sensor data (optional but recommended):
  1. Download & run LibreHardwareMonitor (https://github.com/LibreHardwareMonitor/LibreHardwareMonitor)
     -- run it as Administrator, and in Options enable "Remote Web Server"
     OR just leave it running (it registers a WMI provider automatically).
  2. pip install wmi   (Windows only, --break-system-packages may be needed
     in some environments)
  3. Run this script while LibreHardwareMonitor is running.

If you skip that setup, the test still genuinely stresses your CPU --
you'll just see "Not available" for temp/fan instead of fake numbers.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import multiprocessing
import psutil

try:
    import wmi  # Windows-only, optional
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False


# ----------------------------------------------------------------------
# Real CPU load. Runs in a separate OS process so it actually occupies a
# physical core instead of being serialized behind the GIL.
# ----------------------------------------------------------------------
def cpu_burner_process(stop_event):
    x = 1.0001
    while not stop_event.is_set():
        for _ in range(200_000):
            x = (x * 1.0000001) % 999_999
            if stop_event.is_set():
                break


# ----------------------------------------------------------------------
# Honest hardware monitor: real data if available, explicit "unavailable"
# state if not. Never invents a number.
# ----------------------------------------------------------------------
class HardwareMonitor:
    def __init__(self):
        self.wmi_conn = None
        self.source = None
        self.error = None

        if not WMI_AVAILABLE:
            self.error = "Python 'wmi' package not installed"
            return

        for namespace in ("root\\LibreHardwareMonitor", "root\\OpenHardwareMonitor"):
            try:
                conn = wmi.WMI(namespace=namespace)
                sensors = conn.Sensor()
                if sensors:
                    self.wmi_conn = conn
                    self.source = namespace.split("\\")[-1]
                    return
            except Exception:
                continue

        self.error = "LibreHardwareMonitor/OpenHardwareMonitor not running"

    def read(self):
        """Returns (temp_c_or_None, rpm_or_None)."""
        if self.wmi_conn is None:
            return None, None
        temp = None
        rpm = None
        try:
            for sensor in self.wmi_conn.Sensor():
                if sensor.SensorType == "Temperature" and temp is None:
                    name = sensor.Name or ""
                    if "CPU" in name or "Core" in name or "Package" in name:
                        temp = float(sensor.Value)
                if sensor.SensorType == "Fan" and rpm is None:
                    rpm = float(sensor.Value)
        except Exception:
            return None, None
        return temp, rpm


class FanStressTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Real CPU/Fan Stress Test")
        self.root.geometry("520x520")
        self.root.resizable(False, False)
        self.root.configure(bg="#F3F3F3")

        self.monitor = HardwareMonitor()
        self.test_running = False
        self.test_duration = 60
        self.elapsed_seconds = 0
        self.stop_event = None
        self.burners = []
        self.peak_temp = None
        self.start_temp = None

        self.create_widgets()

        self.poll_active = True
        threading.Thread(target=self.poll_loop, daemon=True).start()

    # ------------------------------------------------------------------
    def create_widgets(self):
        banner = tk.Frame(self.root, bg="#0078D7", height=60)
        banner.pack(fill="x")
        tk.Label(banner, text="REAL CPU / FAN STRESS TEST", font=("Segoe UI", 14, "bold"),
                 fg="white", bg="#0078D7").pack(pady=15, padx=20, anchor="w")

        body = tk.Frame(self.root, bg="#F3F3F3", padx=25, pady=15)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Multi-process CPU Load Test", font=("Segoe UI", 12, "bold"),
                 fg="#333333", bg="#F3F3F3").pack(anchor="w", pady=(0, 5))

        desc = ("Loads every physical core using separate processes (so the GIL can't "
                "limit it). Listen for fan noise/rattle yourself -- most consumer "
                "hardware doesn't expose real fan RPM to software.")
        tk.Label(body, text=desc, font=("Segoe UI", 9), fg="#555555", bg="#F3F3F3",
                 wraplength=460, justify="left").pack(anchor="w", pady=(0, 10))

        # Sensor source status line -- always honest about what we have.
        if self.monitor.wmi_conn is not None:
            src_text = f"Sensor source: {self.monitor.source} (live data)"
            src_color = "green"
        else:
            src_text = f"Sensor source: NONE -- {self.monitor.error}. Showing CPU usage % only."
            src_color = "#A80000"
        self.src_lbl = tk.Label(body, text=src_text, font=("Segoe UI", 8, "italic"),
                                 fg=src_color, bg="#F3F3F3", wraplength=460, justify="left")
        self.src_lbl.pack(anchor="w", pady=(0, 10))

        metrics_frame = tk.LabelFrame(body, text=" Live Readings ", font=("Segoe UI", 9, "bold"),
                                      bg="white", padx=15, pady=15)
        metrics_frame.pack(fill="x", pady=5)

        self.cpu_lbl = tk.Label(metrics_frame, text="CPU Usage: -- %",
                                 font=("Segoe UI", 12), bg="white", fg="#222222")
        self.cpu_lbl.pack(anchor="w", pady=2)

        self.temp_lbl = tk.Label(metrics_frame, text="CPU Temperature: --",
                                  font=("Segoe UI", 12), bg="white", fg="#222222")
        self.temp_lbl.pack(anchor="w", pady=2)

        self.rpm_lbl = tk.Label(metrics_frame, text="Fan RPM: --",
                                 font=("Segoe UI", 12), bg="white", fg="#222222")
        self.rpm_lbl.pack(anchor="w", pady=2)

        self.cores_lbl = tk.Label(metrics_frame, text=f"Logical cores detected: {multiprocessing.cpu_count()}",
                                   font=("Segoe UI", 10), bg="white", fg="#666666")
        self.cores_lbl.pack(anchor="w", pady=(5, 0))

        self.progress = ttk.Progressbar(body, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", pady=(20, 5))

        self.status_lbl = tk.Label(body, text="Status: Ready", font=("Segoe UI", 10, "italic"),
                                    fg="#555555", bg="#F3F3F3")
        self.status_lbl.pack(anchor="w")

        btn_frame = tk.Frame(body, bg="#F3F3F3")
        btn_frame.pack(fill="x", pady=(20, 0))

        self.start_btn = tk.Button(btn_frame, text="RUN STRESS TEST (60s)", font=("Segoe UI", 10, "bold"),
                                    bg="#A80000", fg="white", activebackground="#820000",
                                    activeforeground="white", padx=15, pady=8, command=self.begin_test)
        self.start_btn.pack(side="right")

    # ------------------------------------------------------------------
    def poll_loop(self):
        """Updates readings once per second, whether or not a test is running."""
        while self.poll_active:
            cpu_pct = psutil.cpu_percent(interval=None)
            temp, rpm = self.monitor.read()

            self.cpu_lbl.config(text=f"CPU Usage: {cpu_pct:.0f} %")

            if temp is not None:
                self.temp_lbl.config(text=f"CPU Temperature: {temp:.1f} °C")
                if self.test_running:
                    if self.start_temp is None:
                        self.start_temp = temp
                    if self.peak_temp is None or temp > self.peak_temp:
                        self.peak_temp = temp
            else:
                self.temp_lbl.config(text="CPU Temperature: Not available (no sensor source)")

            if rpm is not None:
                self.rpm_lbl.config(text=f"Fan RPM: {rpm:.0f}")
            else:
                self.rpm_lbl.config(text="Fan RPM: Not exposed by this hardware/BIOS")

            time.sleep(1.0)

    # ------------------------------------------------------------------
    def begin_test(self):
        self.start_btn.config(state="disabled", bg="#CCCCCC")
        self.test_running = True
        self.elapsed_seconds = 0
        self.peak_temp = None
        self.start_temp = None
        self.progress["value"] = 0
        self.status_lbl.config(text="Status: Spinning up worker processes...", fg="#A80000")
        threading.Thread(target=self.run_test, daemon=True).start()

    def run_test(self):
        self.stop_event = multiprocessing.Event()
        self.burners = []
        core_count = multiprocessing.cpu_count()

        for _ in range(core_count):
            p = multiprocessing.Process(target=cpu_burner_process, args=(self.stop_event,))
            p.daemon = True
            p.start()
            self.burners.append(p)

        while self.elapsed_seconds < self.test_duration:
            time.sleep(1)
            self.elapsed_seconds += 1
            self.progress["value"] = (self.elapsed_seconds / self.test_duration) * 100
            self.status_lbl.config(text=f"Status: Stressing {core_count} cores... "
                                         f"{self.elapsed_seconds}s / {self.test_duration}s")

        self.stop_event.set()
        for p in self.burners:
            p.join(timeout=3)
            if p.is_alive():
                p.terminate()

        self.finish_test()

    def finish_test(self):
        self.test_running = False
        self.root.after(0, self._show_results)

    def _show_results(self):
        win = tk.Toplevel(self.root)
        win.title("Test Results")
        win.geometry("400x280")
        win.resizable(False, False)
        win.configure(bg="white")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="STRESS TEST RESULTS", font=("Segoe UI", 11, "bold"),
                 bg="white", fg="#333333").pack(pady=(15, 5))

        lines = [f"Duration: {self.test_duration}s", f"Cores loaded: {multiprocessing.cpu_count()}"]

        if self.start_temp is not None and self.peak_temp is not None:
            lines.append(f"Starting temp: {self.start_temp:.1f} °C")
            lines.append(f"Peak temp: {self.peak_temp:.1f} °C")
            lines.append(f"Rise: +{self.peak_temp - self.start_temp:.1f} °C")
        else:
            lines.append("Temp data: not available during this run")

        tk.Label(win, text="\n".join(lines), font=("Segoe UI", 10), bg="white",
                 fg="#555555", justify="left").pack(pady=5)

        note = ("This tool can't judge fan health for you -- listen for rattling, "
                "grinding, or a fan that doesn't speed up at all under this load. "
                "That's the real test.")
        tk.Label(win, text=note, font=("Segoe UI", 9, "italic"), bg="white", fg="#A80000",
                 wraplength=360, justify="left").pack(pady=(5, 10))

        def close():
            win.destroy()
            self.start_btn.config(state="normal", bg="#A80000")
            self.status_lbl.config(text="Status: Ready", fg="#555555")

        tk.Button(win, text="Close", font=("Segoe UI", 10), width=15, command=close).pack(pady=(0, 10))


if __name__ == "__main__":
    multiprocessing.freeze_support()
    root = tk.Tk()
    app = FanStressTestApp(root)
    root.mainloop()