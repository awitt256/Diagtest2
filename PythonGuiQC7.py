import customtkinter as ctk
import subprocess
import os
import threading
from tkinter import messagebox

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
        messagebox.showerror("Error", str(e))


def run_tool(path):
    full = os.path.join(BASE, path)
    if not os.path.exists(full):
        messagebox.showwarning("Missing File", f"Cannot find:\n{full}")
        return
    run_cmd(f'"{full}"')


def run_powershell(command):
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            shell=False,
            timeout=20,
        )
    except Exception as e:
        return f"Error: {e}"

    output = (result.stdout or "").strip()
    error = (result.stderr or "").strip()

    if result.returncode != 0 and error:
        return f"Error: {error}"
    if output:
        return output
    if error:
        return error
    return "Not Available"


def generate_system_info_report():
    sections = [
        ("SYSTEM IDENTIFICATION", [
            ("[System]", "Get-CimInstance Win32_ComputerSystem | ForEach-Object { \"Manufacturer : $($_.Manufacturer)`nModel        : $($_.Model)`nSystem SKU   : $($_.SystemSKUNumber)\" }"),
            ("[BIOS]", "Get-CimInstance Win32_BIOS | ForEach-Object { \"Serial Number: $($_.SerialNumber)\" }"),
        ]),
        ("STORAGE INFORMATION", [
            ("Logical Drive Information:", "try { Get-CimInstance Win32_LogicalDisk | Where-Object { $_.DriveType -eq 3 } | ForEach-Object { $totalGB = [math]::Round($_.Size / 1GB, 1); $freeGB = [math]::Round($_.FreeSpace / 1GB, 1); $usedGB = [math]::Round(($_.Size - $_.FreeSpace) / 1GB, 1); \"Drive $($_.Caption) Total: $totalGB GB, Free: $freeGB GB, Used: $usedGB GB\" } } catch { \"Error retrieving drive information\" }"),
            ("Physical Disk Information:", "try { Get-CimInstance Win32_DiskDrive | ForEach-Object { $sizeGB = [math]::Round($_.Size / 1GB, 0); \"$($_.Model) - $sizeGB GB\" } } catch { \"Error retrieving disk information\" }"),
        ]),
        ("MEMORY INFORMATION", [
            ("Total System Memory:", "try { $cs = Get-CimInstance Win32_ComputerSystem; \"Total RAM: $([math]::Round($cs.TotalPhysicalMemory / 1GB, 1)) GB\" } catch { \"Not Available\" }"),
            ("Memory Modules:", "try { Get-CimInstance Win32_PhysicalMemory | ForEach-Object { $capGB = [math]::Round($_.Capacity / 1GB, 0); $speed = if ($_.Speed) { \"$($_.Speed) MHz\" } else { \"Unknown Speed\" }; $mfg = if ($_.Manufacturer) { $_.Manufacturer.Trim() } else { \"Unknown\" }; \"Module: $capGB GB, $speed, $mfg\" } } catch { \"Error retrieving memory information\" }"),
        ]),
        ("GRAPHICS INFORMATION", [
            ("Graphics Cards:", "try { Get-CimInstance Win32_VideoController | ForEach-Object { if ($_.AdapterRAM -and $_.AdapterRAM -gt 0) { $vramGB = [math]::Round($_.AdapterRAM / 1GB, 1); if ($vramGB -lt 1) { $vramMB = [math]::Round($_.AdapterRAM / 1MB, 0); \"$($_.Name) - $vramMB MB\" } else { \"$($_.Name) - $vramGB GB\" } } else { \"$($_.Name) - VRAM: Not Available\" } } } catch { \"Error retrieving graphics information\" }"),
        ]),
        ("PROCESSOR INFORMATION", [
            ("Processor:", "try { $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1; $cpu.Name } catch { \"Not Available\" }"),
            ("Processor Details:", "try { $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1; \"Cores: $($cpu.NumberOfCores), Logical Processors: $($cpu.NumberOfLogicalProcessors), Max Speed: $($cpu.MaxClockSpeed) MHz\" } catch { \"Details not available\" }"),
        ]),
        ("OPERATING SYSTEM INFORMATION", [
            ("Operating System:", "try { $os = Get-CimInstance Win32_OperatingSystem; $os.Caption } catch { \"Not Available\" }"),
            ("OS Details:", "try { $os = Get-CimInstance Win32_OperatingSystem; \"Version: $($os.Version)`nArchitecture: $($os.OSArchitecture)\" } catch { \"Details not available\" }"),
        ]),
    ]

    lines = [
        "=" * 64,
        "                   SYSTEM INFORMATION REPORT",
        "=" * 64,
        "",
        f"Generated: {run_powershell('Get-Date -Format \"yyyy-MM-dd HH:mm:ss\"')}",
        "",
    ]

    for header, items in sections:
        lines.extend([
            "=" * 64,
            header.center(64),
            "=" * 64,
            "",
        ])
        for title, command in items:
            lines.append(title)
            lines.append(run_powershell(command))
            lines.append("")

    lines.extend([
        f"System Name: {os.environ.get('COMPUTERNAME', 'Unknown')}",
        f"Current User: {os.environ.get('USERNAME', 'Unknown')}",
        "",
        "=" * 64,
        "                            SUMMARY",
        "=" * 64,
        "",
        "QUICK SYSTEM OVERVIEW:",
        "=======================",
        run_powershell("try { $cs = Get-CimInstance Win32_ComputerSystem; $bios = Get-CimInstance Win32_BIOS; $ramGB = [math]::Round($cs.TotalPhysicalMemory / 1GB, 0); \"Model: $($cs.Model)`nSerial: $($bios.SerialNumber)`nRAM: $ramGB GB\" } catch { \"Summary information not available\" }"),
        f"Computer: {os.environ.get('COMPUTERNAME', 'Unknown')}",
        f"User: {os.environ.get('USERNAME', 'Unknown')}",
        f"Date: {run_powershell('Get-Date -Format \"yyyy-MM-dd HH:mm:ss\"')}",
        "",
        "=" * 64,
    ])

    return "\n".join(lines)


def open_system_info():
    win = ctk.CTkToplevel(app)
    win.title("System Information")
    win.geometry("900x700")

    header = ctk.CTkFrame(win)
    header.pack(fill="x", padx=10, pady=(10, 0))

    ctk.CTkLabel(
        header,
        text="System Information Report",
        font=ctk.CTkFont(size=20, weight="bold")
    ).pack(side="left", padx=12, pady=10)

    textbox = ctk.CTkTextbox(win, wrap="word")
    textbox.pack(fill="both", expand=True, padx=10, pady=10)
    textbox.insert("1.0", "Loading system information...\nThis may take a few seconds.")
    textbox.configure(state="disabled")

    def load_report():
        report = generate_system_info_report()

        def update_ui():
            textbox.configure(state="normal")
            textbox.delete("1.0", "end")
            textbox.insert("1.0", report)
            textbox.configure(state="disabled")

        win.after(0, update_ui)

    threading.Thread(target=load_report, daemon=True).start()

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
app.title("Diagnostics Test Tool V.73 (Modern UI)")
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
add_button("System Info", open_system_info)
add_button("Bitlocker Check", lambda: run_tool("Tools/bitlockercheck1.bat"))
add_button("Hotkeys Test", lambda: run_tool("Tools/hk1.bat"))
add_button("Device Manager", lambda: run_cmd("devmgmt.msc"))
add_button("Battery Test", lambda: run_tool("Tools/Battery TEST/bat.exe"))
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
