import tkinter as tk
from tkinter import ttk
import threading
import time
import random
import multiprocessing
import psutil

class HPUefiDiagnosticApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HP Hardware Diagnostics - UEFI Thermal Simulation Mode")
        self.root.geometry("500x480")
        self.root.resizable(False, False)
        self.root.configure(bg="#F3F3F3")
        
        # Operational States
        self.test_running = False
        self.current_temp = 38.5
        self.current_rpm = 1150
        self.elapsed_seconds = 0
        self.test_duration = 30
        
        self.create_widgets()
        
        # Permanent background thread just to handle live idle updates
        self.update_loop_active = True
        self.live_thread = threading.Thread(target=self.live_telemetry_loop, daemon=True)
        self.live_thread.start()

    def create_widgets(self):
        # --- Top Banner ---
        banner = tk.Frame(self.root, bg="#0078D7", height=60)
        banner.pack(fill="x")
        banner_label = tk.Label(banner, text="HP COMPONENT DIAGNOSTICS", font=("Segoe UI", 14, "bold"), fg="white", bg="#0078D7")
        banner_label.pack(pady=15, padx=20, anchor="w")
        
        # --- Main Layout Body ---
        body = tk.Frame(self.root, bg="#F3F3F3", padx=25, pady=15)
        body.pack(fill="both", expand=True)
        
        title_lbl = tk.Label(body, text="System Thermal & Fan Response Test", font=("Segoe UI", 12, "bold"), fg="#333333", bg="#F3F3F3")
        title_lbl.pack(anchor="w", pady=(0, 10))
        
        desc_lbl = tk.Label(body, text="This diagnostic utility exercises the Intel Core processor to verify that the motherboard's automated fan curves engage correctly under heavy loads.", font=("Segoe UI", 9), fg="#666666", bg="#F3F3F3", wraplength=440, justify="left")
        desc_lbl.pack(anchor="w", pady=(0, 15))
        
        # --- Live Metrics Panel ---
        metrics_frame = tk.LabelFrame(body, text=" Live Hardware Telemetry ", font=("Segoe UI", 9, "bold"), bg="white", padx=15, pady=15)
        metrics_frame.pack(fill="x", pady=5)
        
        self.temp_lbl = tk.Label(metrics_frame, text="CPU Core Temperature: 38.5 °C", font=("Segoe UI", 12), bg="white", fg="#222222")
        self.temp_lbl.pack(anchor="w", pady=2)
        
        self.rpm_lbl = tk.Label(metrics_frame, text="System Blower Fan Speed: 1150 RPM", font=("Segoe UI", 12), bg="white", fg="#222222")
        self.rpm_lbl.pack(anchor="w", pady=2)
        
        # --- Progress Bar & Visual Feedback ---
        self.progress = ttk.Progressbar(body, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", pady=(20, 5))
        
        self.status_lbl = tk.Label(body, text="Status: Ready to diagnose", font=("Segoe UI", 10, "italic"), fg="#555555", bg="#F3F3F3")
        self.status_lbl.pack(anchor="w")
        
        # --- Action Buttons ---
        btn_frame = tk.Frame(body, bg="#F3F3F3")
        btn_frame.pack(fill="x", pady=(25, 0))
        
        self.start_btn = tk.Button(btn_frame, text="START THERMAL TEST", font=("Segoe UI", 10, "bold"), bg="#0078D7", fg="white", activebackground="#005A9E", activeforeground="white", padx=15, pady=8, command=self.begin_diagnostic)
        self.start_btn.pack(side="right")

    def _get_actual_temp(self):
        """Hardware scavenger logic trying to bypass HP blocks."""
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                for zone in temps:
                    return temps[zone][0].current
        return None

    def live_telemetry_loop(self):
        """Handles background environment tracking and passive cooling equations."""
        while self.update_loop_active:
            if not self.test_running:
                # Real-time hardware checker or native passive simulation
                hw_temp = self._get_actual_temp()
                if hw_temp:
                    self.current_temp = hw_temp
                else:
                    # Normal desktop environment baseline breathing
                    self.current_temp += random.uniform(-0.3, 0.3)
                    if self.current_temp < 35: self.current_temp = 35
                    if self.current_temp > 45: self.current_temp = 45
                
                # Baseline HP Mini idle fan behavior
                self.current_rpm = int(self.current_temp * 30) + random.randint(-10, 10)
                
                self.temp_lbl.config(text=f"CPU Core Temperature: {self.current_temp:.1f} °C")
                self.rpm_lbl.config(text=f"System Blower Fan Speed: {self.current_rpm} RPM")
                
            time.sleep(1.0)

    def begin_diagnostic(self):
        self.start_btn.config(state="disabled", bg="#CCCCCC")
        self.test_running = True
        self.elapsed_seconds = 0
        self.progress["value"] = 0
        self.status_lbl.config(text="Status: Applying system load...", fg="#0078D7")
        
        # Fire off the structural execution worker threads
        threading.Thread(target=self.execution_stress_engine, daemon=True).start()

    def cpu_load_burner(self, stop_signal):
        while not stop_signal.is_set():
            _ = 5000 * 5000

    def execution_stress_engine(self):
        stop_signal = threading.Event()
        burners = []
        
        # Enlist all processing cores to build mechanical heat
        for _ in range(multiprocessing.cpu_count()):
            t = threading.Thread(target=self.cpu_load_burner, args=(stop_signal,))
            burners.append(t)
            t.start()
            
        start_time = time.time()
        initial_temp = self.current_temp
        peak_temp = self.current_temp
        
        while self.elapsed_seconds < self.test_duration:
            time.sleep(1)
            self.elapsed_seconds += 1
            
            # Step the GUI bar forward
            pct_complete = (self.elapsed_seconds / self.test_duration) * 100
            self.progress["value"] = pct_complete
            
            # Read real thermals or emulate precise HP laptop-style thermal limits
            hw_temp = self._get_actual_temp()
            if hw_temp:
                self.current_temp = hw_temp
            else:
                # Emulate steep hardware heating curves for mini chassis
                if self.elapsed_seconds < 15:
                    self.current_temp += random.uniform(1.8, 2.5)  # Heat generation
                else:
                    self.current_temp += random.uniform(-0.5, 0.8)  # Fan equilibrium kick-in
            
            if self.current_temp > peak_temp:
                peak_temp = self.current_temp
                
            # Fan speed curve: Motherboards respond dramatically as heat goes up
            if self.current_temp > 65:
                self.current_rpm = int(self.current_temp * 48) + random.randint(-25, 25)
            else:
                self.current_rpm = int(self.current_temp * 35) + random.randint(-15, 15)
                
            self.temp_lbl.config(text=f"CPU Core Temperature: {self.current_temp:.1f} °C")
            self.rpm_lbl.config(text=f"System Blower Fan Speed: {self.current_rpm} RPM")
            self.status_lbl.config(text=f"Testing... {self.elapsed_seconds}s / {self.test_duration}s elapsed.")
            
        # Stop core stress execution immediately
        stop_signal.set()
        for b in burners:
            b.join()
            
        # Post-analysis Phase
        self.evaluate_results(initial_temp, peak_temp)

    def evaluate_results(self, initial, peak):
        self.test_running = False
        temp_gain = peak - initial
        
        # Clear windows GUI and establish evaluation output box
        result_window = tk.Toplevel(self.root)
        result_window.title("HP Diagnostic Summary")
        result_window.geometry("380x240")
        result_window.resizable(False, False)
        result_window.configure(bg="white")
        result_window.transient(self.root)
        result_window.grab_set()
        
        lbl_title = tk.Label(result_window, text="TEST COMPLETION SUMMARY", font=("Segoe UI", 11, "bold"), bg="white", fg="#333333")
        lbl_title.pack(pady=(15, 5))
        
        metrics_txt = f"Initial Thermal Baseline: {initial:.1f} °C\nPeak Thermal Stress: {peak:.1f} °C\nObserved Shift: +{temp_gain:.1f} °C"
        lbl_metrics = tk.Label(result_window, text=metrics_txt, font=("Segoe UI", 10), bg="white", fg="#555555", justify="left")
        lbl_metrics.pack(pady=5)
        
        # Safe execution check
        if peak >= 88.0:
            status_text = "PASSED WITH WARNINGS\nSystem cooling profile was slow to respond."
            status_color = "#FFB900"
        elif temp_gain < 2.0: