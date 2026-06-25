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

# Elevate privileges to manipulate local PnP drivers and registry
force_admin()

import tkinter as tk
import customtkinter as ctk
import threading
import time
import winreg

try:
    import wmi
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "wmi"])
    import wmi

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class LiveSmartCardMonitor(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DTT - Live Smart Card Monitor")
        self.geometry("500x480")
        self.resizable(False, False)
        self.running = True

        # --- UI LAYOUT ---
        self.header = ctk.CTkLabel(self, text="LIVE SMART CARD STATUS MONITOR", font=ctk.CTkFont(size=16, weight="bold"))
        self.header.pack(pady=15)

        # 1. HARDWARE STATUS DISPLAY
        self.hw_frame = ctk.CTkFrame(self, height=60, width=440)
        self.hw_frame.pack(padx=20, pady=5)
        self.hw_frame.pack_propagate(False)
        self.hw_label = ctk.CTkLabel(self.hw_frame, text="Reader Hardware: Initializing...", font=ctk.CTkFont(size=14, weight="bold"))
        self.hw_label.pack(expand=True)

        # 2. LIVE CARD PRESENCE DISPLAY
        self.card_frame = ctk.CTkFrame(self, height=80, width=440)
        self.card_frame.pack(padx=20, pady=5)
        self.card_frame.pack_propagate(False)
        self.card_label = ctk.CTkLabel(self.card_frame, text="Card Presence: Waiting...", font=ctk.CTkFont(size=15, weight="bold"))
        self.card_label.pack(expand=True)

        # 3. CONSOLE LOG OUTPUT
        self.details_box = ctk.CTkTextbox(self, width=440, height=160, font=ctk.CTkFont(family="Consolas", size=11))
        self.details_box.pack(padx=20, pady=10)

        self.footer_label = ctk.CTkLabel(self, text="🔄 Real-time hardware stream active (1s loop)", font=ctk.CTkFont(size=11, slant="italic"), text_color="#7F8C8D")
        self.footer_label.pack(pady=5)

        # --- RUN STARTUP SEQUENCING ---
        # Step 1: Force BIOS PnP Hardware Bus Poll 
        self.force_bios_bus_wake()
        
        # Step 2: Strip Registry Selective Suspend Parameters
        self.auto_optimize_power()

        # Step 3: Ignite Live Monitoring Engine Loop
        self.monitor_thread = threading.Thread(target=self.live_monitor_loop, daemon=True)
        self.monitor_thread.start()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def log(self, text):
        self.details_box.insert(tk.END, text + "\n")
        self.details_box.see(tk.END)

    def force_bios_bus_wake(self):
        """Triggers a focused hardware re-scan via localized PnP subsystems to bypass BIOS power limits."""
        self.log("[*] Step 1: Initiating focused hardware bus wake sequence...")
        
        # Method 1: Use native Windows PnpUtil (Pre-authorized system service)
        try:
            import subprocess
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            subprocess.run(["pnputil", "/scan-devices"], startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.log("[+] Broadcasted localized PnP bus rescan via Windows Engine.")
            return
        except Exception:
            pass

        # Method 2: SetupAPI focused fallback if system execution limits block subprocessing
        try:
            cfgmgr32 = ctypes.windll.cfgmgr32
            setupapi = ctypes.windll.setupapi
            
            dev_info_set = setupapi.SetupDiGetClassDevsW(None, None, None, 0x00000014) # DIGCF_ALLCLASSES | DIGCF_PRESENT
            if dev_info_set:
                cfgmgr32.CM_Reenumerate_DevNode_Ex(0, 0, None) 
                self.log("[+] Localized class bus flush complete.")
            else:
                self.log("[-] Class bus handle unavailable.")
        except Exception as e:
            self.log(f"[-] Bus wake fallback log: {e}")

    def auto_optimize_power(self):
        """Scans registry blocks to ensure continuous active connection profiles."""
        self.log("[*] Step 2: Overriding registry Selective Suspend flags...")
        sc_guid = r"System\CurrentControlSet\Control\Class\{50DD5230-BA8A-11D1-BF5D-0000F805F530}"
        patched_count = 0
        
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, sc_guid, 0, winreg.KEY_ALL_ACCESS)
            info = winreg.QueryInfoKey(key)
            for i in range(info[0]):
                subkey_name = winreg.EnumKey(key, i)
                if subkey_name.isdigit():
                    sub_key_path = f"{sc_guid}\\{subkey_name}"
                    sub_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, sub_key_path, 0, winreg.KEY_SET_VALUE)
                    try:
                        winreg.SetValueEx(sub_key, "SelectiveSuspendEnabled", 0, winreg.REG_DWORD, 0)
                        winreg.SetValueEx(sub_key, "InactivityTimeout", 0, winreg.REG_DWORD, 0)
                        winreg.SetValueEx(sub_key, "IdleInWorkingState", 0, winreg.REG_DWORD, 0)
                        patched_count += 1
                    except Exception:
                        pass
                    finally:
                        winreg.CloseKey(sub_key)
            winreg.CloseKey(key)
            
            if patched_count > 0:
                self.log(f"[+] Success: Forced {patched_count} software profiles wide awake.\n")
            else:
                self.log("[*] Standby register clear. Awaiting live discovery loop.\n")
        except Exception as e:
            self.log(f"[-] Registry injection log skipped: {e}\n")

    def live_monitor_loop(self):
        """Continuous live scanner running on background worker thread."""
        reader_hardware_name = self.check_hardware_presence()
        
        if reader_hardware_name:
            display_name = reader_hardware_name if len(reader_hardware_name) <= 35 else reader_hardware_name[:32] + "..."
            self.after(0, lambda: self.hw_frame.configure(fg_color="#1E3A24"))
            self.after(0, lambda: self.hw_label.configure(text=f"READER: {display_name}", text_color="#2ECC71"))
        else:
            self.after(0, lambda: self.hw_frame.configure(fg_color="#3A2222"))
            self.after(0, lambda: self.hw_label.configure(text="READER: NOT DETECTED", text_color="#E74C3C"))
            self.after(0, lambda: self.card_frame.configure(fg_color="#333333"))
            self.after(0, lambda: self.card_label.configure(text="CARD STATUS: N/A (NO READER)", text_color="#7F8C8D"))

        while self.running and reader_hardware_name:
            card_inserted = False
            try:
                w = wmi.WMI()
                for dev in w.Win32_PnPEntity():
                    dev_name = str(dev.Name).lower()
                    if dev_name == "smart card" or dev_name == "unknown smart card":
                        card_inserted = True
                        break
            except Exception:
                pass

            if card_inserted:
                self.after(0, lambda: self.card_frame.configure(fg_color="#1E3A24"))
                self.after(0, lambda: self.card_label.configure(text="💳 CARD DETECTED IN SLOT", text_color="#2ECC71"))
            else:
                self.after(0, lambda: self.card_frame.configure(fg_color="#3A2222"))
                self.after(0, lambda: self.card_label.configure(text="📥 SLOT EMPTY - INSERT CARD", text_color="#E74C3C"))

            time.sleep(1)

    def check_hardware_presence(self):
        try:
            w = wmi.WMI()
            for r in w.Win32_SmartCardReader():
                return r.Name
        except Exception:
            pass

        try:
            sc_guid = r"System\CurrentControlSet\Control\Class\{50DD5230-BA8A-11D1-BF5D-0000F805F530}"
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, sc_guid)
            info = winreg.QueryInfoKey(key)
            for i in range(info[0]):
                subkey_name = winreg.EnumKey(key, i)
                if subkey_name.isdigit():
                    sub_key = winreg.OpenKey(key, subkey_name)
                    try:
                        driver_desc, _ = winreg.QueryValueEx(sub_key, "DriverDesc")
                        winreg.CloseKey(sub_key)
                        winreg.CloseKey(key)
                        return driver_desc
                    except WindowsError:
                        pass
                    winreg.CloseKey(sub_key)
            winreg.CloseKey(key)
        except Exception:
            pass
        return None

    def on_closing(self):
        self.running = False
        self.destroy()

if __name__ == "__main__":
    app = LiveSmartCardMonitor()
    app.mainloop()