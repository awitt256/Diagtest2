import sys
import os
import ctypes

def force_admin():
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{os.path.abspath(sys.argv[0])}"', None, 1)
            sys.exit(0)
    except:
        sys.exit(0)

force_admin()

import tkinter as tk
import customtkinter as ctk
import threading
import time

# Verify base bridge packages are present
for package in ["clr-loader", "pythonnet", "psutil"]:
    try:
        __import__(package if package != "clr-loader" else "clr")
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

import clr
import psutil

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class NativeHardwareMonitor(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DTT - Native Hardware Monitor")
        self.geometry("550x500")  # Expanded height for GPU layout integration
        self.resizable(False, False)
        self.running = True

        # --- UI LAYOUT ---
        self.header_label = ctk.CTkLabel(self, text="HARDWARE DIAGNOSTIC MONITOR", font=ctk.CTkFont(size=20, weight="bold"))
        self.header_label.pack(pady=15)

        self.status_frame = ctk.CTkFrame(self, height=40)
        self.status_frame.pack(fill="x", padx=20, pady=5)
        self.status_frame.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Linking to native driver...", font=ctk.CTkFont(size=12, slant="italic"))
        self.status_label.pack(expand=True)

        # Main Scrollable Frame or Container for layout clean groupings
        self.data_frame = ctk.CTkFrame(self)
        self.data_frame.pack(fill="both", expand=True, padx=20, pady=15)

        # ================= CPU SECTION =================
        self.cpu_section_label = ctk.CTkLabel(self.data_frame, text="--- CENTRAL PROCESSOR (CPU) ---", font=ctk.CTkFont(size=13, weight="bold"), text_color="#3498DB")
        self.cpu_section_label.pack(pady=(10, 5))

        self.load_label = ctk.CTkLabel(self.data_frame, text="CPU Total Load: -- %", font=ctk.CTkFont(size=14, weight="bold"))
        self.load_label.pack(pady=2)
        self.load_bar = ctk.CTkProgressBar(self.data_frame, width=400)
        self.load_bar.set(0)
        self.load_bar.pack(pady=2)

        self.temp_label = ctk.CTkLabel(self.data_frame, text="CPU Package Temp: -- °C", font=ctk.CTkFont(size=14, weight="bold"))
        self.temp_label.pack(pady=(2, 15))

        # ================= GPU SECTION =================
        self.gpu_section_label = ctk.CTkLabel(self.data_frame, text="--- GRAPHICS PROCESSOR (GPU) ---", font=ctk.CTkFont(size=13, weight="bold"), text_color="#E67E22")
        self.gpu_section_label.pack(pady=(10, 5))

        self.gpu_load_label = ctk.CTkLabel(self.data_frame, text="GPU Core Load: -- %", font=ctk.CTkFont(size=14, weight="bold"))
        self.gpu_load_label.pack(pady=2)
        self.gpu_load_bar = ctk.CTkProgressBar(self.data_frame, width=400, progress_color="#E67E22")
        self.gpu_load_bar.set(0)
        self.gpu_load_bar.pack(pady=2)

        self.gpu_temp_label = ctk.CTkLabel(self.data_frame, text="GPU Core Temp: -- °C", font=ctk.CTkFont(size=14, weight="bold"))
        self.gpu_temp_label.pack(pady=2)

        self.admin_label = ctk.CTkLabel(self, text="🛡️ Running with Administrator Privileges", font=ctk.CTkFont(size=11), text_color="#2ECC71")
        self.admin_label.pack(pady=10)

        self.hardware_computer = None
        
        # Initialize native driver linkage
        self.initialize_native_dll()

        self.monitor_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.monitor_thread.start()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def initialize_native_dll(self):
        """Points directly to your verified local Downloads track folder."""
        lhm_folder = r"C:\Users\Anthony\Downloads\LibreHardwareMonitor"
        dll_path = os.path.join(lhm_folder, "LibreHardwareMonitorLib.dll")

        if os.path.exists(dll_path):
            try:
                ctypes.windll.kernel32.DeleteFileW(dll_path + ":Zone.Identifier")
                clr.AddReference(dll_path)
                from LibreHardwareMonitor.Hardware import Computer
                
                self.hardware_computer = Computer()
                self.hardware_computer.IsCpuEnabled = True
                self.hardware_computer.IsGpuEnabled = True  # CRITICAL ADD: Activate GPU driver arrays
                self.hardware_computer.Open()
                
                self.status_label.configure(text="● Native Kernel Driver Linked Successfully", text_color="#2ECC71")
                self.status_frame.configure(fg_color="#1E3A24")
            except Exception as err:
                self.status_label.configure(text=f"Initialization Error: {err}", text_color="#E74C3C")
                self.status_frame.configure(fg_color="#3A2222")
        else:
            self.status_label.configure(text="DLL not found in Downloads\\LibreHardwareMonitor", text_color="#E74C3C")
            self.status_frame.configure(fg_color="#3A2222")

    def update_loop(self):
        while self.running:
            cpu_load = None
            cpu_temp = None
            gpu_load = None
            gpu_temp = None

            if self.hardware_computer:
                try:
                    for hardware in self.hardware_computer.Hardware:
                        hardware.Update()
                        hardware_type = hardware.HardwareType.ToString()

                        for sensor in hardware.Sensors:
                            name_lower = sensor.Name.lower().strip()
                            sensor_type = sensor.SensorType.ToString()
                            
                            # ---- PROCESS CPU SENSORS ----
                            if "cpu" in hardware_type.lower():
                                if sensor_type == "Load" and name_lower == "cpu total":
                                    cpu_load = float(sensor.Value)
                                elif sensor_type == "Temperature":
                                    if name_lower == "cpu package" or name_lower == "core average":
                                        cpu_temp = float(sensor.Value)
                                    elif name_lower == "core max" and cpu_temp is None:
                                        cpu_temp = float(sensor.Value)

                            # ---- PROCESS GPU SENSORS (Nvidia, AMD, Intel Core Graphics) ----
                            elif "gpu" in hardware_type.lower():
                                if sensor_type == "Load" and "core" in name_lower:
                                    gpu_load = float(sensor.Value)
                                elif sensor_type == "Temperature" and "core" in name_lower:
                                    gpu_temp = float(sensor.Value)
                except:
                    pass

            # Local fallback matching rules for base load metrics
            if cpu_load is None:
                cpu_load = psutil.cpu_percent(interval=None)

            self.after(0, self.refresh_display, cpu_load, cpu_temp, gpu_load, gpu_temp)
            time.sleep(1)

    def refresh_display(self, cpu_load, cpu_temp, gpu_load, gpu_temp):
        # Update CPU fields
        self.load_label.configure(text=f"CPU Total Load: {cpu_load:.1f}%")
        self.load_bar.set(cpu_load / 100.0)
        
        if cpu_temp is not None:
            self.temp_label.configure(text=f"CPU Package Temp: {cpu_temp:.1f}°C")
        else:
            self.temp_label.configure(text="CPU Package Temp: N/A")

        # Update GPU fields
        if gpu_load is not None:
            self.gpu_load_label.configure(text=f"GPU Core Load: {gpu_load:.1f}%")
            self.gpu_load_bar.set(gpu_load / 100.0)
        else:
            self.gpu_load_label.configure(text="GPU Core Load: N/A")
            self.gpu_load_bar.set(0)

        if gpu_temp is not None:
            self.gpu_temp_label.configure(text=f"GPU Core Temp: {gpu_temp:.1f}°C")
        else:
            self.gpu_temp_label.configure(text="GPU Core Temp: N/A")

    def on_closing(self):
        self.running = False
        if self.hardware_computer:
            try:
                self.hardware_computer.Close()
            except:
                pass
        self.destroy()

if __name__ == "__main__":
    app = NativeHardwareMonitor()
    app.mainloop()