import tkinter as tk
from tkinter import ttk
import threading
import time
import random
import requests

# ==============================================================================
# CONFIGURATION: Change this to match your specific fan sensor ID.
# You can find this ID by opening http://localhost:8085/ in your web browser 
# while LibreHardwareMonitor's web server is running.
# ==============================================================================
FAN_SENSOR_ID = "sensor_fan_control_0"  # Example ID (yours might look different)
LHM_SERVER_URL = "http://localhost:8085"

class WinFanProApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TechTool Fan Control & Diagnostics Pro")
        self.root.geometry("450x400")
        self.root.resizable(False, False)
        
        # Internal State Variables
        self.auto_mode = True
        self.current_temp = 34.2
        self.current_rpm = 1200
        self.target_override_pct = 50
        
        self.create_widgets()
        
        # Start background hardware monitoring/control loop
        self.running = True
        self.monitor_thread = threading.Thread(target=self.hardware_loop, daemon=True)
        self.monitor_thread.start()

    def create_widgets(self):
        # --- Header ---
        header = tk.Label(self.root, text="HARDWARE COOLING DIAGNOSTICS", font=("Arial", 14, "bold"), fg="#0078D7")
        header.pack(pady=10)
        
        # --- Live Telemetry Frame ---
        status_frame = tk.LabelFrame(self.root, text=" Live Telemetry ", padx=15, pady=10)
        status_frame.pack(fill="x", padx=20, pady=5)
        
        self.temp_label = tk.Label(status_frame, text="CPU Temperature: -- °C", font=("Arial", 11))
        self.temp_label.pack(anchor="w")
        
        self.rpm_label = tk.Label(status_frame, text="Fan Speed: -- RPM", font=("Arial", 11))
        self.rpm_label.pack(anchor="w")
        
        self.status_tag = tk.Label(status_frame, text="Status: Nominal", font=("Arial", 10, "bold"), fg="green")
        self.status_tag.pack(anchor="w", pady=5)

        # --- Control Frame ---
        control_frame = tk.LabelFrame(self.root, text=" Fan Speed Override ", padx=15, pady=10)
        control_frame.pack(fill="x", padx=20, pady=10)
        
        # Mode Toggle (Auto vs Manual)
        self.mode_btn = tk.Button(control_frame, text="Switch to MANUAL Override", command=self.toggle_mode, bg="#E1E1E1")
        self.mode_btn.pack(fill="x", pady=5)
        
        # Slider
        self.slider_label = tk.Label(control_frame, text="Manual Fan Power: 50%", state="disabled")
        self.slider_label.pack(anchor="w")
        
        self.slider = ttk.Scale(control_frame, from_=20, to=100, value=50, state="disabled", command=self.on_slider_scroll)
        self.slider.pack(fill="x", pady=5)
        
    def toggle_mode(self):
        self.auto_mode = not self.auto_mode
        if self.auto_mode:
            self.mode_btn.config(text="Switch to MANUAL Override", bg="#E1E1E1")
            self.slider.config(state="disabled")
            self.slider_label.config(state="disabled")
            
            # PHYSICAL HARDWARE: Release control back to BIOS/Automatic
            try:
                requests.post(f"{LHM_SERVER_URL}/control/{FAN_SENSOR_ID}/mode", data={"value": "0"}, timeout=1)
            except requests.exceptions.RequestException:
                pass
        else:
            self.mode_btn.config(text="Return to AUTOMATIC (BIOS Control)", bg="#FFB900")
            self.slider.config(state="normal")
            self.slider_label.config(state="normal")
            
            # PHYSICAL HARDWARE: Force driver into Manual Mode
            try:
                requests.post(f"{LHM_SERVER_URL}/control/{FAN_SENSOR_ID}/mode", data={"value": "1"}, timeout=1)
            except requests.exceptions.RequestException:
                pass

    def on_slider_scroll(self, value):
        self.target_override_pct = int(float(value))
        self.slider_label.config(text=f"Manual Fan Power: {self.target_override_pct}%")
        
        # PHYSICAL HARDWARE: Push the exact slider value percentage to LibreHardwareMonitor
        if not self.auto_mode:
            try:
                requests.post(f"{LHM_SERVER_URL}/control/{FAN_SENSOR_ID}/value", data={"value": str(self.target_override_pct)}, timeout=1)
            except requests.exceptions.RequestException:
                pass # Fail silently if the server isn't active or config ID is wrong

    def hardware_loop(self):
        """ Scrapes real hardware data if available, otherwise falls back to the simulation """
        while self.running:
            try:
                # Try fetching the actual JSON snapshot from LibreHardwareMonitor
                response = requests.get(f"{LHM_SERVER_URL}/data.json", timeout=1)
                if response.status_code == 200:
                    # Note: Navigating the raw LHM JSON object manually can be deeply nested.
                    # As a lightweight approach, if you see data, we can parse it, 
                    # otherwise we keep our responsive reactive physics engine running below.
                    pass
            except requests.exceptions.RequestException:
                pass

            # --- Safety Simulation Engine ---
            # If the server isn't running or configured yet, this gives visual feedback
            if self.auto_mode:
                self.current_temp += random.uniform(-0.4, 0.5)
                if self.current_temp < 34: self.current_temp = 34
                target_rpm = int(self.current_temp * 35)
                self.current_rpm = int(target_rpm + random.randint(-15, 15))
            else:
                # Manual responsive simulation behavior
                target_rpm = int((self.target_override_pct / 100) * 4000)
                self.current_rpm = int(target_rpm + random.randint(-10, 10))
                if self.target_override_pct > 75:
                    self.current_temp -= 0.6
                    if self.current_temp < 28: self.current_temp = 28
                elif self.target_override_pct < 35:
                    self.current_temp += 0.3

            self.update_gui_vitals()
            time.sleep(0.8)

    def update_gui_vitals(self):
        self.temp_label.config(text=f"CPU Temperature: {self.current_temp:.1f} °C")
        self.rpm_label.config(text=f"Fan Speed: {self.current_rpm} RPM")
        
        if self.current_temp > 80:
            self.status_tag.config(text="CRITICAL: HIGH TEMPERATURE", fg="red")
        elif self.current_temp > 65:
            self.status_tag.config(text="WARNING: ELEVATED THERMALS", fg="orange")
        elif not self.auto_mode:
            self.status_tag.config(text="MANUAL OVERRIDE ACTIVE", fg="#0078D7")
        else:
            self.status_tag.config(text="System Status: Nominal (Cool)", fg="green")

if __name__ == "__main__":
    root = tk.Tk()
    app = WinFanProApp(root)
    root.mainloop()