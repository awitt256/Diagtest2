import sys
import os
import ctypes

def force_admin():
    """Forces the script to relaunch with Administrator privileges if not already elevated."""
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False

    if not is_admin:
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join([f'"{arg}"' for arg in sys.argv]), None, 1)
        except Exception as e:
            print(f"Failed to elevate permissions: {e}")
        sys.exit(0)

# FORCE ELEVATION BEFORE EVERYTHING ELSE
force_admin()

import tkinter as tk
import customtkinter as ctk
import wmi
import threading
import time

try:
    import psutil
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

# Set window themes
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class CPUMonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DTT - CPU Monitor Module")
        self.geometry("550x400")
        self.resizable(False, False)

        self.running = True

        # --- UI LAYOUT ---
        self.header_label = ctk.CTkLabel(
            self, 
            text="CPU HARDWARE MONITOR", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.header_label.pack(pady=15)

        # Status Banner
        self.status_frame = ctk.CTkFrame(self, height=40)
        self.status_frame.pack(fill="x", padx=20, pady=5)
        self.status_frame.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame, 
            text="Initializing connection...", 
            font=ctk.CTkFont(size=12, slant="italic")
        )
        self.status_label.pack(expand=True)

        # Data Display Frame
        self.data_frame = ctk.CTkFrame(self)
        self.data_frame.pack(fill="both", expand=True, padx=20, pady=15)

        # CPU Total Load UI Elements
        self.load_label = ctk.CTkLabel(
            self.data_frame, 
            text="CPU Total Load: -- %", 
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.load_label.pack(pady=(20, 5))

        self.load_bar = ctk.CTkProgressBar(self.data_frame, width=400)
        self.load_bar.set(0)
        self.load_bar.pack(pady=5)

        # CPU Temperature UI Elements
        self.temp_label = ctk.CTkLabel(
            self.data_frame, 
            text="CPU Package Temp: -- °C", 
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.temp_label.pack(pady=(25, 5))

        # Admin Status Indicator
        self.admin_label = ctk.CTkLabel(
            self, 
            text="🛡️ Running with Administrator Privileges", 
            font=ctk.CTkFont(size=11), 
            text_color="#2ECC71"
        )
        self.admin_label.pack(pady=10)

        # Start the background data collector thread
        self.monitor_thread = threading.Thread(target=self.update_cpu_data, daemon=True)
        self.monitor_thread.start()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_cpu_data(self):
        """Background thread loop to pull CPU metrics."""
        while self.running:
            cpu_load = None
            cpu_temp = None
            using_fallback = False

            try:
                # Connect to LibreHardwareMonitor WMI namespace
                w = wmi.WMI(namespace=r"root\LibreHardwareMonitor")
                sensors = w.Sensor()
                hardware = w.Hardware()

                if not hardware or not sensors:
                    using_fallback = True
                    self.update_status_ui(
                        text="WMI Connected but paths empty. Relaunch LHM as Admin.", 
                        bg_color="#3A2222", 
                        text_color="#E74C3C"
                    )
                else:
                    self.update_status_ui(
                        text="● LibreHardwareMonitor Connected Successfully", 
                        bg_color="#1E3A24", 
                        text_color="#2ECC71"
                    )

                    backup_temp = None

                    for sensor in sensors:
                        name_lower = sensor.Name.lower()
                        sensor_type = sensor.SensorType
                        
                        # CRITICAL FIX: Look purely at the Sensor Type and explicit Name 
                        # completely ignoring parent/identifier restrictions.
                        if sensor_type == "Load" and sensor.Name == "CPU Total":
                            cpu_load = float(sensor.Value)

                        elif sensor_type == "Temperature":
                            if "cpu package" in name_lower:
                                cpu_temp = float(sensor.Value)
                            elif "core average" in name_lower and cpu_temp is None:
                                backup_temp = float(sensor.Value)
                            elif "core max" in name_lower and cpu_temp is None and backup_temp is None:
                                backup_temp = float(sensor.Value)

                    # Apply fallback temperature tracking if primary package statement didn't catch
                    if cpu_temp is None and backup_temp is not None:
                        cpu_temp = backup_temp

            except wmi.x_wmi:
                using_fallback = True
                self.update_status_ui(
                    text="LHM Not Found. Running Fallback Mode (No Temp)", 
                    bg_color="#7F8C8D", 
                    text_color="#FFFFFF"
                )

            # Apply OS level tracking if fallback was triggered
            if using_fallback:
                cpu_load = psutil.cpu_percent(interval=None)
                cpu_temp = None

            # Render directly back to the visual frame elements
            self.after(0, self.refresh_display, cpu_load, cpu_temp)
            time.sleep(1)

    def update_status_ui(self, text, bg_color, text_color):
        self.after(0, lambda: self.status_frame.configure(fg_color=bg_color))
        self.after(0, lambda: self.status_label.configure(text=text, text_color=text_color))

    def refresh_display(self, load, temp):
        if load is not None:
            self.load_label.configure(text=f"CPU Total Load: {load:.1f}%")
            self.load_bar.set(load / 100.0)
        else:
            self.load_label.configure(text="CPU Total Load: N/A")
            self.load_bar.set(0)

        if temp is not None:
            self.temp_label.configure(text=f"CPU Package Temp: {temp:.1f}°C")
        else:
            self.temp_label.configure(text="CPU Package Temp: N/A")

    def on_closing(self):
        self.running = False
        self.destroy()

if __name__ == "__main__":
    app = CPUMonitorApp()
    app.mainloop()