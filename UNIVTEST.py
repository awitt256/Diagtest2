import platform
import tkinter as tk
from tkinter import ttk
import psutil

class DiagnosticApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cross-Platform Hardware Diagnostics")
        self.root.geometry("500x380")
        self.root.resizable(False, False)
        
        # Detect the Operating System immediately
        self.current_os = platform.system()
        
        # Initialize UI Components
        self.create_widgets()
        self.run_diagnostics()

    def create_widgets(self):
        """Builds a clean, organized layout for the test results."""
        # Main container padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. OS Greeting Banner (Your custom check)
        self.greeting_label = ttk.Label(
            main_frame, 
            text="Detecting Operating System...", 
            font=("Helvetica", 14, "bold")
        )
        self.greeting_label.pack(pady=(0, 15))

        # Divider line
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill='x', pady=5)

        # 2. Diagnostic Log Display Box
        log_frame = ttk.LabelFrame(main_frame, text=" Hardware Test Suite Progress ", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Text box to dump our live hardware status updates
        self.log_box = tk.Text(log_frame, wrap=tk.WORD, font=("Courier", 10), state=tk.DISABLED)
        self.log_box.pack(fill=tk.BOTH, expand=True)

        # 3. Status Bar/Footer
        self.status_label = ttk.Label(main_frame, text="Status: Ready", font=("Helvetica", 9, "italic"))
        self.status_label.pack(anchor=tk.W, pady=(10, 0))

    def write_to_log(self, text):
        """Helper to append lines into our read-only text suite logs."""
        self.log_box.config(state=tk.NORMAL)
        self.log_box.insert(tk.END, text + "\n")
        self.log_box.config(state=tk.DISABLED)

    def run_diagnostics(self):
        """Routes logic dynamically based on system type and prints live specs."""
        self.status_label.config(text="Status: Diagnostics Running...")
        
        # Route and print the exact greeting you requested
        if self.current_os == "Windows":
            self.greeting_label.config(text="HELLO! I AM A WINDOWS COMPUTER!", foreground="#0078D4")
            self.write_to_log("[!] Initializing Windows Diagnostic Suite...")
            
        elif self.current_os == "Darwin": # Mac OS Kernel
            self.greeting_label.config(text="HELLO! I AM A MAC COMPUTER!", foreground="#999999")
            self.write_to_log("[!] Initializing macOS Diagnostic Suite...")
            
        elif self.current_os == "Linux":
            self.greeting_label.config(text="HELLO! I AM A LINUX COMPUTER!", foreground="#E67E22")
            self.write_to_log("[!] Initializing Linux Diagnostic Suite...")
            
        else:
            self.greeting_label.config(text=f"HELLO! UNKNOWN HARDWARE UNIT ({self.current_os})", foreground="red")
            self.write_to_log("[-] Critical Error: Unknown operating system kernel route.")

        # Gather and inject the live universal hardware tests
        self.write_to_log("\n--- GATHERING SYSTEM HARDWARE SCANS ---")
        
        # Live Memory Check
        virtual_mem = psutil.virtual_memory()
        total_ram_gb = round(virtual_mem.total / (1024 ** 3), 2)
        self.write_to_log(f"[+] MEMORY SCAN: {total_ram_gb} GB total system RAM mapped.")
        
        # Live CPU Check
        cores = psutil.cpu_count(logical=False)
        self.write_to_log(f"[+] CPU SCAN: {cores} Physical core architecture active.")
        
        # Finished
        self.write_to_log("\n[+] DIAGNOSTICS RUN COMPLETE SUCCESSFULLY.")
        self.status_label.config(text="Status: Completed")

if __name__ == "__main__":
    root = tk.Tk()
    app = DiagnosticApp(root)
    root.mainloop()
    