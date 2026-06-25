import sys
import os
import ctypes
import tkinter as tk
import customtkinter as ctk
import threading
import time

def force_admin():
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{os.path.abspath(sys.argv[0])}"', None, 1)
            sys.exit(0)
    except:
        sys.exit(0)

# Force elevation to query hardware details smoothly
force_admin()

try:
    import wmi
    import pythoncom  # Required for background thread COM initialization
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "wmi pywin32"])
    import wmi
    import pythoncom

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class RAMAuditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DTT - Memory Sub-Bus Auditor")
        self.geometry("600x520")
        self.resizable(False, False)

        # --- UI LAYOUT ---
        self.header = ctk.CTkLabel(
            self, 
            text="🧠 MEMORY SUB-BUS AUDITOR", 
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#58a6ff"
        )
        self.header.pack(pady=(20, 10))

        # Total RAM Capacity Summary Frame
        self.total_frame = ctk.CTkFrame(self, height=50, width=540, fg_color="#1f1f24")
        self.total_frame.pack(padx=20, pady=5)
        self.total_frame.pack_propagate(False)
        self.total_label = ctk.CTkLabel(
            self.total_frame, 
            text="Total System Memory: Fetching...", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.total_label.pack(expand=True)

        # Mismatch Status Banners
        self.speed_banner = ctk.CTkFrame(self, height=40, width=540, fg_color="#2c3e50")
        self.speed_banner.pack(padx=20, pady=5)
        self.speed_banner.pack_propagate(False)
        self.speed_text = ctk.CTkLabel(self.speed_banner, text="Speed Sync: Auditing...", font=ctk.CTkFont(size=12, weight="bold"))
        self.speed_text.pack(expand=True)

        self.timing_banner = ctk.CTkFrame(self, height=40, width=540, fg_color="#2c3e50")
        self.timing_banner.pack(padx=20, pady=5)
        self.timing_banner.pack_propagate(False)
        self.timing_text = ctk.CTkLabel(self.timing_banner, text="Timing / Voltage Layout: Auditing...", font=ctk.CTkFont(size=12, weight="bold"))
        self.timing_text.pack(expand=True)

        # Slots Breakdown List Box
        self.lbl_slots = ctk.CTkLabel(self, text="Detected Physical Modules Mapping:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#8b949e")
        self.lbl_slots.pack(anchor="w", padx=30, pady=(10, 2))

        self.details_box = ctk.CTkTextbox(
            self, 
            width=540, 
            height=160, 
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#0d1117", 
            border_color="#21262d",
            border_width=1
        )
        self.details_box.pack(padx=20, pady=(0, 15))

        # Scan Trigger
        self.btn_scan = ctk.CTkButton(
            self, 
            text="RE-AUDIT MEMORY BUS", 
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.start_audit
        )
        self.btn_scan.pack(pady=(0, 15))

        # Run initial scan automatically on launch
        self.start_audit()

    def start_audit(self):
        self.btn_scan.configure(state="disabled")
        self.details_box.configure(state="normal")
        self.details_box.delete("1.0", tk.END)
        self.details_box.insert("1.0", "[*] Querying WMI memory configuration table nodes...\n")
        self.details_box.configure(state="disabled")
        
        self.speed_banner.configure(fg_color="#2c3e50")
        self.speed_text.configure(text="Scanning clock alignments...", text_color="#ffffff")
        self.timing_banner.configure(fg_color="#2c3e50")
        self.timing_text.configure(text="Evaluating CAS/Voltage stability...", text_color="#ffffff")

        threading.Thread(target=self.run_ram_audit, daemon=True).start()

    def run_ram_audit(self):
        # FIXED: Initialize the COM interface on this thread before initializing WMI
        try:
            pythoncom.CoInitialize()
        except Exception:
            pass

        try:
            w = wmi.WMI()
            memory_modules = w.Win32_PhysicalMemory()
        except Exception as e:
            self.update_ui_error(f"WMI Query Failure: {e}")
            try: pythoncom.CoUninitialize()
            except: pass
            return

        if not memory_modules:
            self.update_ui_error("No physical memory modules reported by motherboard context.")
            try: pythoncom.CoUninitialize()
            except: pass
            return

        # Alternative backup method via PowerShell CIM Instance query for frequency extraction
        backup_speed = 0
        try:
            import subprocess
            ps_cmd = "Get-CimInstance Win32_PhysicalMemory | Select-Object -ExpandProperty ConfiguredClockSpeed"
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            res = subprocess.run(["powershell", "-Command", ps_cmd], startupinfo=startupinfo, capture_output=True, text=True, timeout=3)
            if res.returncode == 0 and res.stdout.strip().isdigit():
                backup_speed = int(res.stdout.strip().split()[0])
        except Exception:
            pass

        speeds = []
        manufacturers = []
        part_numbers = []
        slot_logs = []
        total_bytes = 0

        for index, module in enumerate(memory_modules):
            speed = 0
            if hasattr(module, 'Speed') and module.Speed is not None:
                try: speed = int(module.Speed)
                except ValueError: pass

            if speed == 0 and backup_speed > 0:
                speed = backup_speed

            capacity_bytes = 0
            if hasattr(module, 'Capacity') and module.Capacity is not None:
                try: capacity_bytes = int(module.Capacity)
                except ValueError: pass
                    
            cap_gb = int(capacity_bytes / (1024 ** 3))
            mfg = module.Manufacturer.strip() if (hasattr(module, 'Manufacturer') and module.Manufacturer) else "Unknown Vendor"
            part = module.PartNumber.strip() if (hasattr(module, 'PartNumber') and module.PartNumber) else "Unknown Part"
            locator = module.DeviceLocator.strip() if (hasattr(module, 'DeviceLocator') and module.DeviceLocator) else f"Slot {index}"
            
            total_bytes += capacity_bytes
            if speed > 0: 
                speeds.append(speed)
                
            manufacturers.append(mfg.lower())
            part_numbers.append(part.lower())
            
            speed_display = f"{speed}MHz" if speed > 0 else "Unknown Speed"
            slot_logs.append(f"[{locator}] {cap_gb}GB {mfg}\n    -> Speed: {speed_display} | Part: {part}\n")

        total_gb = round(total_bytes / (1024 ** 3))
        log_text = "".join(slot_logs)

        # Process Rules Outcomes
        if len(set(speeds)) > 1:
            lowest_speed = min(speeds)
            highest_speed = max(speeds)
            speed_status = f"⚠️ SPEED MISMATCH: Bus throttled to {lowest_speed}MHz (Max chip: {highest_speed}MHz)"
            speed_color = "#7e3d11"
            speed_text_color = "#ff944d"
        elif len(speeds) == 1 or (len(set(speeds)) == 1 and speeds):
            speed_status = f"✔️ Perfect Speed Match ({speeds[0]}MHz)"
            speed_color = "#14341c"
            speed_text_color = "#52c41a"
        else:
            speed_status = "✔️ Frequencies Synchronized"
            speed_color = "#14341c"
            speed_text_color = "#52c41a"

        if len(set(manufacturers)) > 1 or len(set(part_numbers)) > 1:
            timing_status = "⚠️ TIMING RISK: Mixed parts/vendors. Potential CAS Latency/Voltage drift."
            timing_color = "#7e3d11"
            timing_text_color = "#ff944d"
        else:
            timing_status = "✔️ Symmetrical Timing & Voltage Configuration"
            timing_color = "#14341c"
            timing_text_color = "#52c41a"

        # Update GUI safely
        self.after(0, lambda: self.total_label.configure(text=f"Total System Memory: {total_gb} GB"))
        self.after(0, lambda: self.speed_banner.configure(fg_color=speed_color))
        self.after(0, lambda: self.speed_text.configure(text=speed_status, text_color=speed_text_color))
        self.after(0, lambda: self.timing_banner.configure(fg_color=timing_color))
        self.after(0, lambda: self.timing_text.configure(text=timing_status, text_color=timing_text_color))
        
        self.after(0, lambda: self.refresh_textbox(log_text))
        self.after(0, lambda: self.btn_scan.configure(state="normal"))

        # Clean up the COM thread context allocation
        try:
            pythoncom.CoUninitialize()
        except:
            pass

    def refresh_textbox(self, text):
        self.details_box.configure(state="normal")
        self.details_box.delete("1.0", tk.END)
        self.details_box.insert("1.0", text)
        self.details_box.configure(state="disabled")

    def update_ui_error(self, message):
        self.after(0, lambda: self.total_label.configure(text="Total System Memory: Error"))
        self.after(0, lambda: self.refresh_textbox(f"[-] Error: {message}"))
        self.after(0, lambda: self.btn_scan.configure(state="normal"))

if __name__ == "__main__":
    app = RAMAuditorApp()
    app.mainloop()