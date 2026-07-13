import platform
import os
import sys
import subprocess
import tkinter as tk
import psutil

class DarkDiagnosticApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cross-Platform Hardware Diagnostics")
        self.root.geometry("540x430")
        self.root.resizable(False, False)
        
        # Define Dark Mode Color Palette
        self.bg_dark = "#1E1E1E"       
        self.bg_terminal = "#121212"   
        self.text_green = "#00FF00"    
        self.text_white = "#E0E0E0"    
        
        self.root.configure(bg=self.bg_dark)
        self.current_os = platform.system()
        
        self.create_widgets()
        self.run_diagnostics()

    def create_widgets(self):
        """Builds the layout using dark theme styling components."""
        main_frame = tk.Frame(self.root, bg=self.bg_dark, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.greeting_label = tk.Label(
            main_frame, 
            text="INITIALIZING SYSTEM DETECTION...", 
            font=("Helvetica", 14, "bold"),
            bg=self.bg_dark,
            fg=self.text_white
        )
        self.greeting_label.pack(pady=(0, 15))

        log_label = tk.Label(
            main_frame, 
            text=" HARDWARE PROGRESS MATRIX ", 
            font=("Helvetica", 10, "bold"),
            bg=self.bg_dark,
            fg="#888888"
        )
        log_label.pack(anchor=tk.W)

        self.log_box = tk.Text(
            main_frame, 
            wrap=tk.WORD, 
            font=("Courier", 10, "bold"), 
            bg=self.bg_terminal,
            fg=self.text_green,
            insertbackground=self.text_green,
            padx=10,
            pady=10,
            bd=1,
            relief=tk.SOLID,
            state=tk.DISABLED
        )
        self.log_box.pack(fill=tk.BOTH, expand=True, pady=(5, 10))

        self.status_label = tk.Label(
            main_frame, 
            text="STATUS: READY", 
            font=("Helvetica", 9, "italic"),
            bg=self.bg_dark,
            fg="#666666"
        )
        self.status_label.pack(anchor=tk.W)

    def write_to_log(self, text):
        self.log_box.config(state=tk.NORMAL)
        self.log_box.insert(tk.END, text + "\n")
        self.log_box.config(state=tk.DISABLED)

    def get_gpu_info(self):
        """Queries the system hardware layers to pull active graphics cards safely."""
        try:
            if self.current_os == "Windows":
                # Modern Win11 CIM/PowerShell call to completely replace legacy WMIC
                cmd = ["powershell", "-Command", "(Get-CimInstance Win32_VideoController).Name"]
                # CREATE_NO_WINDOW prevents the ugly command prompt box from flashing
                output = subprocess.check_output(cmd, creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
                
                gpus = [line.strip() for line in output.split('\n') if line.strip()]
                return ", ".join(gpus) if gpus else "Unknown Windows GPU"
                
            elif self.current_os == "Darwin":
                cmd = "system_profiler SPDisplaysDataType | grep 'Chipset Model'"
                output = subprocess.check_output(cmd, shell=True).decode().split(":")
                return output[1].strip() if len(output) > 1 else "Apple Integrated Graphics"
                
            elif self.current_os == "Linux":
                cmd = "lspci | grep -E 'VGA|3D'"
                output = subprocess.check_output(cmd, shell=True).decode().split(":")
                return output[-1].strip() if output else "Generic Linux GPU"
                
        except Exception:
            return "Unable to resolve GPU interface hardware"

    def run_diagnostics(self):
        """Routes logic, reads core hardware components, and fires target scripts."""
        self.status_label.config(text="STATUS: DIAGNOSTICS ACTIVE...")
        run_win_script = False
        
        if self.current_os == "Windows":
            self.greeting_label.config(text="HELLO! I AM A WINDOWS COMPUTER!", fg="#3498DB")
            self.write_to_log("[!] Executing Windows Environment Checks...")
            run_win_script = True
            
        elif self.current_os == "Darwin": 
            self.greeting_label.config(text="HELLO! I AM A MAC COMPUTER!", fg="#F1C40F")
            self.write_to_log("[!] Executing macOS Environment Checks...")
            
        elif self.current_os == "Linux":
            self.greeting_label.config(text="HELLO! I AM A LINUX COMPUTER!", fg="#E67E22")
            self.write_to_log("[!] Executing Linux Environment Checks...")
            
        else:
            self.greeting_label.config(text=f"HELLO! UNKNOWN APPARATUS ({self.current_os})", fg="#E74C3C")

        # Gather main metrics
        self.write_to_log("\n>>> GATHERING CORE SYSTEM INTERFACES...")
        
        # Memory Check
        virtual_mem = psutil.virtual_memory()
        total_ram_gb = round(virtual_mem.total / (1024 ** 3), 2)
        self.write_to_log(f"[+] MEMORY INTERFACE: {total_ram_gb} GB System RAM Mapped.")
        
        # CPU Check
        cores = psutil.cpu_count(logical=False)
        self.write_to_log(f"[+] CPU CORE INTERFACE: {cores} Discrete Hardware Cores Online.")
        
        # GPU Check
        gpu_model = self.get_gpu_info()
        self.write_to_log(f"[+] GPU INTERFACE: {gpu_model}")
        
        self.write_to_log("\n[+] HARDWARE DIAGNOSTIC SUITE RUN SUCCESSFUL.")
        
        # Final evaluation check for Windows execution handling
        if run_win_script:
            self.write_to_log("[!] WINDOWS DETECTED RUNNING WINDOWS TEST")
            
            # Subprocess launcher logic looking in the exact same folder
            base_dir = os.path.dirname(os.path.abspath(__file__))
            target_script = os.path.join(base_dir, "mywintest62.py")
            
            if os.path.exists(target_script):
                subprocess.Popen([sys.executable, target_script])
            else:
                self.write_to_log(f"[-] Subprocess Error: '{target_script}' missing from path.")
                
        self.status_label.config(text="STATUS: DIAGNOSTICS COMPLETE")

if __name__ == "__main__":
    root = tk.Tk()
    app = DarkDiagnosticApp(root)
    root.mainloop()