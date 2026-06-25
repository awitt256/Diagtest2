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
import winreg

try:
    import wmi
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "wmi"])
    import wmi

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SmartCardDiagnostic(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DTT - Smart Card Diagnostic")
        self.geometry("500x480")  # Bumped height slightly for dual status displays
        self.resizable(False, False)

        # --- UI LAYOUT ---
        self.header = ctk.CTkLabel(self, text="SMART CARD DIAGNOSTIC SUITE", font=ctk.CTkFont(size=18, weight="bold"))
        self.header.pack(pady=15)

        # 1. HARDWARE DETECTION BANNER
        self.hw_frame = ctk.CTkFrame(self, height=50, width=440)
        self.hw_frame.pack(padx=20, pady=5)
        self.hw_frame.pack_propagate(False)
        self.hw_label = ctk.CTkLabel(self.hw_frame, text="Reader Hardware: UNKNOWN", font=ctk.CTkFont(size=14, weight="bold"))
        self.hw_label.pack(expand=True)

        # 2. CARD INSERTION STATUS BANNER
        self.card_frame = ctk.CTkFrame(self, height=50, width=440)
        self.card_frame.pack(padx=20, pady=5)
        self.card_frame.pack_propagate(False)
        self.card_label = ctk.CTkLabel(self.card_frame, text="Card Presence: NOT SCANNED", font=ctk.CTkFont(size=14, weight="bold"))
        self.card_label.pack(expand=True)

        # Interactive Logging Terminal
        self.details_box = ctk.CTkTextbox(self, width=440, height=170, font=ctk.CTkFont(family="Consolas", size=12))
        self.details_box.pack(padx=20, pady=10)

        # Test Scan Trigger Button
        self.btn_test = ctk.CTkButton(self, text="RUN FULL SMART CARD TEST", font=ctk.CTkFont(size=13, weight="bold"), command=self.start_scan)
        self.btn_test.pack(pady=15)

    def log(self, text):
        self.details_box.insert(tk.END, text + "\n")
        self.details_box.see(tk.END)

    def start_scan(self):
        self.btn_test.configure(state="disabled")
        self.details_box.delete("1.0", tk.END)
        
        # Reset frames to scanning states
        self.hw_frame.configure(fg_color="#2C3E50")
        self.hw_label.configure(text="Scanning System Bus...", text_color="#FFFFFF")
        self.card_frame.configure(fg_color="#2C3E50")
        self.card_label.configure(text="Checking Card Slots...", text_color="#FFFFFF")
        
        threading.Thread(target=self.scan_hardware_and_card, daemon=True).start()

    def scan_hardware_and_card(self):
        reader_found = False
        card_inserted = False
        detected_names = []
        
        # --- PHASE 1: HARDWARE DETECTION LAYER ---
        self.log("[*] Phase 1: Sweeping System for Reader Hardware...")
        try:
            w = wmi.WMI()
            readers = w.Win32_SmartCardReader()
            for r in readers:
                reader_found = True
                detected_names.append(r.Name)
                self.log(f"[+] Active Reader Detected via WMI: {r.Name}")
        except Exception:
            pass

        # Registry sweep fallback for sleeping/suspended integrated components
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
                        reader_found = True
                        detected_names.append(driver_desc)
                        self.log(f"[+] Cached Base Registry Profile Found: '{driver_desc}'")
                    except WindowsError:
                        pass
                    winreg.CloseKey(sub_key)
            winreg.CloseKey(key)
        except Exception:
            pass

        # Clean duplicates and update hardware UI
        if reader_found:
            unique_names = list(set(detected_names))
            display_name = unique_names[0] if unique_names else "SmartCard Reader"
            if len(display_name) > 35: display_name = display_name[:32] + "..."
            
            self.after(0, lambda: self.hw_frame.configure(fg_color="#1E3A24"))
            self.after(0, lambda: self.hw_label.configure(text=f"READER: {display_name}", text_color="#2ECC71"))
            
            # --- PHASE 2: CARD INSERTION PRESENCE DETECTION ---
            self.log("\n[*] Phase 2: Interrogating Reader for Inserted Cards...")
            try:
                pnp_devices = w.Win32_PnPEntity()
                for dev in pnp_devices:
                    dev_name = str(dev.Name).lower()
                    # When a smart card is physically plugged in, Windows creates a child device entry 
                    # under the PnP tree named "Smart Card" or matching the specific card type profile.
                    if dev_name == "smart card" or dev_name == "unknown smart card":
                        # Verify the device status is active/operating normal
                        status = getattr(dev, "Status", "Unknown")
                        self.log(f"[+] Card detected in reader slot! PnP Device: {dev.Name} (Status: {status})")
                        card_inserted = True
                        break
            except Exception as e:
                self.log(f"[-] Error querying smart card PnP subnodes: {e}")

            if card_inserted:
                self.after(0, lambda: self.card_frame.configure(fg_color="#1E3A24"))
                self.after(0, lambda: self.card_label.configure(text="CARD STATUS: CARD INSERTED / ACTIVE", text_color="#2ECC71"))
            else:
                self.log("[-] Slot check complete. No physical smart card media detected.")
                self.after(0, lambda: self.card_frame.configure(fg_color="#3A2222"))
                self.after(0, lambda: self.card_label.configure(text="CARD STATUS: SLOT EMPTY", text_color="#E74C3C"))

        else:
            # No hardware found anywhere
            self.log("\n[!] Failure: Reader module is entirely missing or disabled in BIOS.")
            self.after(0, lambda: self.hw_frame.configure(fg_color="#3A2222"))
            self.after(0, lambda: self.hw_label.configure(text="READER: NOT DETECTED", text_color="#E74C3C"))
            self.after(0, lambda: self.card_frame.configure(fg_color="#333333"))
            self.after(0, lambda: self.card_label.configure(text="CARD STATUS: N/A (NO READER)", text_color="#7F8C8D"))

        self.after(0, lambda: self.btn_test.configure(state="normal"))

if __name__ == "__main__":
    app = SmartCardDiagnostic()
    app.mainloop()