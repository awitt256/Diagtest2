import customtkinter as ctk
import subprocess
import os

ctk.set_appearance_mode("dark")       # "light", "dark", or "system"
ctk.set_default_color_theme("blue")   # themes: "blue", "green", "dark-blue"

BASE = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------
# Helper functions
# ----------------------------------------

def run_cmd(command):
    try:
        subprocess.Popen(command, shell=True)
    except Exception as e:
        ctk.CTkMessagebox(title="Error", message=str(e), icon="cancel")

def run_tool(path):
    full = os.path.join(BASE, path)
    if not os.path.exists(full):
        ctk.CTkMessagebox(
            title="Missing File",
            message=f"Cannot find:\n{full}",
            icon="warning"
        )
        return
    run_cmd(f'"{full}"')

# ----------------------------------------
# Account menu
# ----------------------------------------

def open_account_menu():
    acc = ctk.CTkToplevel()
    acc.title("Account Settings")
    acc.geometry("400x300")

    ctk.CTkLabel(acc, text="ACCOUNT SETTINGS", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

    ctk.CTkButton(
        acc, text="Manage Users",
        command=lambda: (run_cmd("start ms-settings:otherusers"), acc.destroy())
    ).pack(pady=6)

    ctk.CTkButton(
        acc, text="Delete User Account",
        command=lambda: (run_tool("deleteaccount.bat"), acc.destroy())
    ).pack(pady=6)

    ctk.CTkButton(
        acc, text="Create Local Account",
        command=lambda: (run_tool("account.bat"), acc.destroy())
    ).pack(pady=6)

    ctk.CTkButton(
        acc, text="Back", fg_color="#444444",
        command=acc.destroy
    ).pack(pady=15)

# ----------------------------------------
# Main Window
# ----------------------------------------

app = ctk.CTk()

# Set window icon (must be .ico)
app.iconbitmap("DTT.ico")
app.title("Diagnostics Test Tool V.72 (Modern UI)")
app.geometry("850x700")

# Scrollable Frame
main_frame = ctk.CTkScrollableFrame(app, width=800, height=650)
main_frame.pack(pady=10, padx=10, fill="both", expand=True)

# Helper functions for layout
def section(title):
    ctk.CTkLabel(
        main_frame, text=title,
        font=ctk.CTkFont(size=16, weight="bold")
    ).pack(pady=(20, 8))

def add_button(text, command):
    ctk.CTkButton(
        main_frame,
        text=text,
        width=300,
        height=32,
        command=command
    ).pack(pady=5)

# -------------------------
# Menu Contents
# -------------------------

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

section("SYSTEM HEALTH")
add_button("SFC Scan", lambda: run_cmd("sfc /scannow"))
add_button("SMART Drive Health", lambda: run_cmd(
    'powershell "Get-CimInstance Win32_DiskDrive | ft Model,SerialNumber,Status"'
))
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

section("ACCOUNT / USER SETTINGS")
add_button("Account Settings", open_account_menu)

section("UTILITIES")
add_button("Clear Temp Files", lambda: run_cmd('powershell "Remove-Item $env:TEMP\\* -Recurse -Force"'))
add_button("Restart PC", lambda: run_cmd("shutdown /r /t 0"))
add_button("Shutdown PC", lambda: run_cmd("shutdown /s /t 0"))
add_button("Exit Program", app.destroy)

app.mainloop()