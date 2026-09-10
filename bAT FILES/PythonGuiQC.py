
import tkinter as tk
from tkinter import messagebox
import subprocess
import os

BASE = os.path.dirname(os.path.abspath(__file__))

# -----------------------------------------------------
# Helper functions
# -----------------------------------------------------

def run_cmd(command):
    try:
        subprocess.Popen(command, shell=True)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def run_tool(path):
    full = os.path.join(BASE, path)
    if not os.path.exists(full):
        messagebox.showerror("Missing File", f"Cannot find:\n{full}")
        return
    run_cmd(f'"{full}"')


# -----------------------------------------------------
# Main Window
# -----------------------------------------------------

root = tk.Tk()
root.title("Diagnostics Test Tool v.66")
root.geometry("750x650")
root.config(bg="#1e1e1e")


# -----------------------------------------------------
# TRUE INVISIBLE SCROLLING
# -----------------------------------------------------

container = tk.Frame(root, bg="#1e1e1e")
container.pack(fill="both", expand=True)

canvas = tk.Canvas(container, bg="#1e1e1e", highlightthickness=0, borderwidth=0)
canvas.pack(side="left", fill="both", expand=True)

scroll_frame = tk.Frame(canvas, bg="#1e1e1e")
canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

def update_scroll_region(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

scroll_frame.bind("<Configure>", update_scroll_region)

# Invisibility: we ADD scrolling ability without showing scrollbar
def _on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)


# -----------------------------------------------------
# UI helper functions
# -----------------------------------------------------

def section(title):
    tk.Label(
        scroll_frame,
        text=title,
        fg="cyan",
        bg="#1e1e1e",
        font=("Segoe UI", 13, "bold")
    ).pack(pady=(20, 5))

def add_button(label, command):
    tk.Button(
        scroll_frame,
        text=label,
        width=45,
        bg="#333333",
        fg="white",
        activebackground="#555555",
        font=("Segoe UI", 10),
        command=command
    ).pack(pady=4)


# -----------------------------------------------------
#   MENU CONTENT
# -----------------------------------------------------

section("SYSTEM / HARDWARE")

add_button("System Info", lambda: run_tool("Tools/sysinfo3.bat"))
add_button("Bitlocker Check", lambda: run_tool("Tools/bitlockercheck1.bat"))
add_button("Hotkeys Test", lambda: run_tool("Tools/hk1.bat"))
add_button("Device Manager", lambda: run_cmd("devmgmt.msc"))
add_button("Battery Test", lambda: run_tool("Apps/bat"))
add_button("Speaker Test", lambda: run_tool("Media/st.mp3"))
add_button("Mic Test", lambda: run_tool("Apps/soundcheck.exe"))
add_button("Camera Test", lambda: run_cmd("start microsoft.windows.camera:"))
add_button("Windows Activation", lambda: run_tool("Tools/ACT.bat"))
add_button("Keyboard Test", lambda: run_tool("Tools/Kbtest.bat"))

section("SYSTEM DIAGNOSTICS & HEALTH")

add_button("System File Checker", lambda: run_cmd("sfc /scannow"))
add_button("SMART Drive Health", lambda: run_cmd('powershell "Get-CimInstance Win32_DiskDrive | ft Model,SerialNumber,Status"'))
add_button("Memory Diagnostic", lambda: run_cmd("mdsched.exe"))
add_button("Disk Cleanup", lambda: run_cmd("cleanmgr"))

section("ADVANCED HARDWARE TESTING")

add_button("Stress Test Suite", lambda: run_tool("Tools/stresstestmenu.bat"))
add_button("Performance Tests", lambda: run_tool("Tools/Install-PerfTest-WithWinget.bat"))
add_button("USB Port Test", lambda: run_tool("Apps/USBTreeView.exe"))
add_button("SSD Test", lambda: run_tool("Apps/CrystalDiskInfo.exe"))

section("NETWORK")

add_button("Network Settings", lambda: run_cmd("start ms-settings:network"))
add_button("WiFi Info", lambda: run_cmd("netsh wlan show interfaces"))

section("UTILITIES / POWER")

add_button("Clear Temp Files", lambda: run_cmd('powershell "Remove-Item $env:TEMP\\* -Recurse -Force"'))
add_button("Restart PC", lambda: run_cmd("shutdown /r /t 0"))
add_button("Shutdown PC", lambda: run_cmd("shutdown /s /t 0"))
add_button("Exit Program", root.quit)


# -----------------------------------------------------
# Run Program
# -----------------------------------------------------
root.mainloop()