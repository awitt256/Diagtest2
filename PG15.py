import customtkinter as ctk
import subprocess
import os
import threading
import sys
import ctypes
import difflib
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


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin():
    try:
        script = os.path.abspath(__file__)
        args = " ".join([f'"{script}"'] + [f'"{arg}"' for arg in sys.argv[1:]])
        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            args,
            None,
            1,
        )
        return result > 32
    except Exception:
        return False


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


def generate_drive_health_report():
    command = r'''
try {
    $physicalDisks = Get-PhysicalDisk -ErrorAction Stop

    if (-not $physicalDisks) {
        "No physical disks found."
        return
    }

    $lines = foreach ($disk in $physicalDisks) {
        $sizeGB = if ($disk.Size) { [math]::Round($disk.Size / 1GB, 0) } else { "Unknown" }
        @(
            "Drive: $($disk.FriendlyName)"
            "Health Level: $($disk.HealthStatus)"
            "Operational Status: $($disk.OperationalStatus)"
            "Media Type: $($disk.MediaType)"
            "Size: $sizeGB GB"
            ""
        ) -join "`n"
    }

    $lines -join "`n"
}
catch {
    try {
        Get-CimInstance Win32_DiskDrive | ForEach-Object {
            $sizeGB = if ($_.Size) { [math]::Round($_.Size / 1GB, 0) } else { "Unknown" }
            @(
                "Drive: $($_.Model)"
                "Serial Number: $($_.SerialNumber)"
                "Health Level: $($_.Status)"
                "Size: $sizeGB GB"
                ""
            ) -join "`n"
        }
    }
    catch {
        "Error retrieving drive health information."
    }
}
'''
    return run_powershell(command)


def open_system_info():
    global active_screen
    clear_main_frame()
    try:
        main_frame.pack_forget()
    except Exception:
        pass
    active_screen = ctk.CTkFrame(app, fg_color="#101723")
    active_screen.pack(fill="both", expand=True, padx=10, pady=10)
    ctk.CTkLabel(
        active_screen,
        text="System Information Report",
        font=ctk.CTkFont(size=20, weight="bold")
    ).pack(pady=(14, 8))
    status_label = ctk.CTkLabel(
        active_screen,
        text="Collecting system information... This may take up to a minute.",
        font=ctk.CTkFont(size=13),
        text_color="#d4af37"
    )
    status_label.pack(pady=(0, 6))
    textbox = ctk.CTkTextbox(active_screen, wrap="word")
    textbox.pack(fill="both", expand=True, padx=14, pady=(0, 8))
    textbox.insert(
        "1.0",
        "Collecting system information...\n"
        "This may take up to a minute.\n\n"
        "Administrator privileges may be requested."
    )
    textbox.configure(state="disabled")
    return_button = ctk.CTkButton(
        active_screen,
        text="Back To Main Menu",
        command=render_main_menu,
        state="disabled"
    )
    return_button.pack(pady=(0, 14))
    def finish_screen():
        status_label.configure(text="Done. Press Enter to go back to the main menu.")
        return_button.configure(state="normal")
        app.bind("<Return>", lambda event=None: render_main_menu())
        app.focus_force()
    def load_report():
        report = generate_system_info_report()
        def update():
            if active_screen is None or not active_screen.winfo_exists():
                return
            textbox.configure(state="normal")
            textbox.delete("1.0", "end")
            textbox.insert("1.0", report)
            textbox.configure(state="disabled")
            finish_screen()
        app.after(0, update)
    threading.Thread(target=load_report, daemon=True).start()


def open_drive_health():
    win = ctk.CTkToplevel(app)
    win.title("SMART Drive Health")
    win.geometry("800x500")

    header = ctk.CTkFrame(win)
    header.pack(fill="x", padx=10, pady=(10, 0))

    ctk.CTkLabel(
        header,
        text="SMART Drive Health",
        font=ctk.CTkFont(size=20, weight="bold")
    ).pack(side="left", padx=12, pady=10)

    textbox = ctk.CTkTextbox(win, wrap="word")
    textbox.pack(fill="both", expand=True, padx=10, pady=10)
    textbox.insert("1.0", "Loading drive health information...")
    textbox.configure(state="disabled")

    def load_report():
        report = generate_drive_health_report()

        def update_ui():
            textbox.configure(state="normal")
            textbox.delete("1.0", "end")
            textbox.insert("1.0", report)
            textbox.configure(state="disabled")

        win.after(0, update_ui)

    threading.Thread(target=load_report, daemon=True).start()

# ----------------------------------------
# Main Window
# ----------------------------------------

if not is_admin():
    if relaunch_as_admin():
        sys.exit()
    messagebox.showwarning("Administrator Required", "This tool works best when started with administrator privileges.")

app = ctk.CTk()

# Set window icon (must be .ico)
icon_path = os.path.join(BASE, "DTT.ico")
if os.path.exists(icon_path):
    try:
        app.iconbitmap(icon_path)
    except Exception:
        pass
app.title("Diagnostics Test Tool V.73 (Modern UI)")
app.geometry("850x700")

# Scrollable Frame
main_frame = ctk.CTkScrollableFrame(app, width=800, height=650)
main_frame.pack(pady=10, padx=10, fill="both", expand=True)
content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
content_frame.pack(fill="both", expand=True)

# Helper functions for layout
def section(title):
    ctk.CTkLabel(
        content_frame, text=title,
        font=ctk.CTkFont(size=16, weight="bold")
    ).pack(pady=(20, 8))


def add_button(text, command):
    ctk.CTkButton(
        content_frame,
        text=text,
        width=300,
        height=32,
        command=command
    ).pack(pady=5)


def clear_main_frame():
    for widget in content_frame.winfo_children():
        widget.destroy()


def open_text_report(title, loader, geometry="760x480"):
    win = ctk.CTkToplevel(app)
    win.title(title)
    win.geometry(geometry)

    textbox = ctk.CTkTextbox(win, wrap="word")
    textbox.pack(fill="both", expand=True, padx=10, pady=10)
    textbox.insert("1.0", "Loading...")
    textbox.configure(state="disabled")

    def load_content():
        report = loader()

        def update_ui():
            textbox.configure(state="normal")
            textbox.delete("1.0", "end")
            textbox.insert("1.0", report)
            textbox.configure(state="disabled")

        win.after(0, update_ui)

    threading.Thread(target=load_content, daemon=True).start()


def show_serial_and_sku():
    def loader():
        return "\n".join([
            "SYSTEM IDENTIFICATION",
            "=" * 48,
            "",
            run_powershell(
                "Get-CimInstance Win32_ComputerSystem | "
                "ForEach-Object { \"Manufacturer : $($_.Manufacturer)`nModel        : $($_.Model)`nSystem SKU   : $($_.SystemSKUNumber)\" }"
            ),
            "",
            run_powershell(
                "Get-CimInstance Win32_BIOS | "
                "ForEach-Object { \"Serial Number: $($_.SerialNumber)\" }"
            ),
        ])

    open_text_report("Serial Number / SKU", loader, geometry="700x320")


def normalize_search_text(text):
    return " ".join(str(text).lower().split())


def matches_search(label, keywords, query):
    normalized_query = normalize_search_text(query)
    if not normalized_query:
        return True

    search_parts = [
        normalize_search_text(part)
        for part in [label, *keywords]
        if part
    ]
    haystack = " ".join(search_parts)
    haystack_words = set(haystack.split())

    def term_matches(term):
        if term in haystack:
            return True

        if any(term in word or word in term for word in haystack_words):
            return True

        close_words = difflib.get_close_matches(term, list(haystack_words), n=3, cutoff=0.68)
        if close_words:
            return True

        condensed_term = term.replace(" ", "")
        for part in search_parts:
            condensed_part = part.replace(" ", "")
            if condensed_term and condensed_term in condensed_part:
                return True
            if difflib.SequenceMatcher(None, condensed_term, condensed_part).ratio() >= 0.72:
                return True

        return False

    return all(term_matches(term) for term in normalized_query.split())


def get_main_menu_sections():
    return [
        ("SYSTEM / HARDWARE", [
            ("System Info", open_system_info, ["system", "hardware", "info"]),
            ("Bitlocker Check", lambda: run_tool("BITLOCKERCHECK1.BAT"), ["bitlocker", "encryption"]),
            ("Hotkeys Test", lambda: run_tool("HK1.BAT"), ["hotkeys", "keyboard"]),
            ("Device Manager", lambda: run_cmd("devmgmt.msc"), ["device", "manager", "drivers"]),
            ("Battery Test", lambda: run_tool("Tools/Battery TEST/bat.exe"), ["battery", "power"]),
            ("Speaker Test", lambda: run_tool("st.mp3"), ["speaker", "audio", "sound"]),
            ("Mic Test", lambda: run_tool("soundcheck.exe"), ["mic", "microphone", "audio", "sound"]),
            ("Camera Test", lambda: run_cmd("start microsoft.windows.camera:"), ["camera", "webcam"]),
            ("Windows Activation", lambda: run_tool("ACT.bat"), ["activation", "windows key"]),
            ("Keyboard Test", render_keyboard_menu, ["keyboard", "kb", "double typing", "notepad"]),
            ("Notepad", lambda: run_cmd("notepad"), ["notepad", "notes", "kb"]),
            ("Windows Update", render_windows_update_menu, ["windows", "update", "drivers"]),
            ("Windows Test", lambda: run_tool("launch-tool.bat"), ["windows", "test"]),
            ("Show Serial / SKU", show_serial_and_sku, ["serial", "sku", "model"]),
            ("Change Audio Output", lambda: run_tool("AUDIOrun.bat"), ["audio", "sound", "speaker"]),
        ]),
        ("SYSTEM HEALTH", [
            ("SFC Scan", lambda: run_cmd("sfc /scannow"), ["sfc", "scan", "system file checker"]),
            ("SMART Drive Health", open_drive_health, ["smart", "drive", "disk", "health", "ssd"]),
            ("Memory Diagnostic", lambda: run_cmd("mdsched.exe"), ["memory", "ram", "diagnostic"]),
            ("Disk Cleanup", lambda: run_cmd("cleanmgr"), ["disk", "cleanup", "storage"]),
        ]),
        ("ADVANCED HARDWARE TESTING", [
            ("Stress Test Suite", render_stress_test_menu, ["stress", "test", "cpu", "gpu", "memory"]),
            ("Performance Tests", render_performance_menu, ["performance", "benchmark"]),
            ("USB Port Test", lambda: run_tool("UsbTreeView.exe"), ["usb", "port"]),
            ("SSD Test", lambda: run_tool("CrystalDiskInfo.exe"), ["ssd", "disk", "drive", "health", "smart"]),
        ]),
        ("NETWORK", [
            ("Network Settings", lambda: run_cmd("start ms-settings:network"), ["network", "wifi", "internet"]),
            ("WiFi Info", lambda: run_cmd("netsh wlan show interfaces"), ["wifi", "wireless", "network"]),
        ]),
        ("SETTINGS / SECURITY", [
            ("Camera Settings", lambda: run_cmd("start ms-settings:privacy-webcam"), ["camera", "settings", "webcam"]),
            ("Activation Settings", lambda: run_cmd("start ms-settings:activation"), ["activation", "settings", "windows key"]),
            ("Sound Settings", lambda: run_cmd("start ms-settings:sound"), ["sound", "audio", "settings"]),
            ("Account Settings", open_account_menu, ["account", "users", "login"]),
            ("Date / Time Settings", lambda: run_cmd("start ms-settings:dateandtime"), ["date", "time", "clock"]),
            ("Language / Region", lambda: run_cmd("start ms-settings:regionlanguage"), ["language", "region", "locale"]),
            ("Windows Defender", lambda: run_tool("wd.BAT"), ["defender", "security", "virus"]),
            ("Check Windows Key", lambda: run_tool("WK.BAT"), ["windows key", "activation", "license"]),
            ("Windows Version", lambda: run_cmd("winver"), ["windows", "version", "build"]),
            ("Computrace Check", lambda: run_tool("Computrace.bat"), ["computrace", "security"]),
            ("More Settings Tools", render_settings_menu, ["settings", "security", "tools"]),
        ]),
        ("DEPLOYMENT / TESTS", [
            ("Sysprep Options", render_sysprep_menu, ["sysprep", "deployment", "image"]),
        ]),
        ("UTILITIES", [
            ("Task Manager", lambda: run_cmd("taskmgr"), ["task manager", "processes"]),
            ("Event Viewer", lambda: run_cmd("eventvwr.msc"), ["event", "viewer", "logs"]),
            ("Clear Temp Files", lambda: run_cmd('powershell "Remove-Item $env:TEMP\\* -Recurse -Force"'), ["temp", "cleanup", "files"]),
            ("Restart PC", lambda: run_cmd("shutdown /r /t 0"), ["restart", "reboot"]),
            ("Shutdown PC", lambda: run_cmd("shutdown /s /t 0"), ["shutdown", "power off"]),
            ("Exit Program", app.destroy, ["exit", "close", "quit"]),
        ]),
    ]


search_var = ctk.StringVar(value="")
search_entry = None


def refresh_main_menu_filter(*_args):
    if app.winfo_exists():
        render_main_menu()


def render_simple_menu(title, buttons):
    clear_main_frame()

    frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    frame.pack(fill="x", expand=True, pady=20)

    ctk.CTkLabel(
        frame,
        text=title,
        font=ctk.CTkFont(size=18, weight="bold")
    ).pack(pady=15)

    for label, command in buttons:
        ctk.CTkButton(
            frame,
            text=label,
            width=320,
            height=32,
            command=command
        ).pack(pady=6)

    ctk.CTkButton(
        frame,
        text="Back",
        width=320,
        height=32,
        fg_color="#444444",
        command=render_main_menu
    ).pack(pady=15)

    main_frame._parent_canvas.yview_moveto(0)


def render_account_menu():
    render_simple_menu("ACCOUNT SETTINGS", [
        ("Manage Users", lambda: run_cmd("start ms-settings:otherusers")),
        ("Delete User Account", lambda: run_tool("DELETEACCOUNT.BAT")),
        ("Create Local Account", lambda: run_tool("ACCOUNT.BAT")),
    ])


def render_keyboard_menu():
    render_simple_menu("KEYBOARD TEST", [
        ("Keyboard Test", lambda: run_tool("KB.exe")),
        ("Double Typing Check", lambda: run_tool("KBTEST.exe")),
        ("Open Notepad", lambda: run_cmd("notepad")),
    ])


def render_settings_menu():
    render_simple_menu("SETTINGS / SECURITY", [
        ("Camera Settings", lambda: run_cmd("start ms-settings:privacy-webcam")),
        ("Activation Settings", lambda: run_cmd("start ms-settings:activation")),
        ("Sound Settings", lambda: run_cmd("start ms-settings:sound")),
        ("Account Settings", open_account_menu),
        ("Date / Time Settings", lambda: run_cmd("start ms-settings:dateandtime")),
        ("Language / Region", lambda: run_cmd("start ms-settings:regionlanguage")),
        ("Windows Defender", lambda: run_tool("wd.BAT")),
        ("Check Windows Key", lambda: run_tool("WK.BAT")),
        ("Windows Version", lambda: run_cmd("winver")),
        ("Computrace Check", lambda: run_tool("Computrace.bat")),
    ])


def render_windows_update_menu():
    render_simple_menu("WINDOWS UPDATE", [
        ("Install All Windows Updates", lambda: run_tool("Windowsupdate.bat")),
        ("Install Missing Drivers", lambda: run_tool("MissDrivers.bat")),
    ])


def render_stress_test_menu():
    render_simple_menu("STRESS TEST SUITE", [
        ("CPU / Burn-In Test", lambda: run_tool("BURNIN.exe")),
        ("GPU Stress Test (FurMark)", lambda: run_tool("FURMARK.lnk")),
        ("Memory Diagnostic", lambda: run_cmd("mdsched.exe")),
        ("Heaven Benchmark", lambda: run_tool("Heaven.lnk")),
        ("OCCT Stress Test", lambda: run_tool("OCCT.exe")),
    ])


def render_performance_menu():
    render_simple_menu("PERFORMANCE TESTS", [
        ("Burn-In Test", lambda: run_tool("BURNIN.exe")),
        ("Run FurMark", lambda: run_tool("FURMARK.lnk")),
        ("Run Performance Test", lambda: run_tool("Install-PerfTest-WithWinget.bat")),
    ])


def render_sysprep_menu():
    render_simple_menu("SYSPREP OPTIONS", [
        ("Sysprep Restart", lambda: run_cmd('start "" "%SystemRoot%\\System32\\Sysprep\\sysprep.exe" /reboot')),
        ("Sysprep Shutdown", lambda: run_cmd('start "" "%SystemRoot%\\System32\\Sysprep\\sysprep.exe" /shutdown')),
    ])


def open_account_menu():
    render_account_menu()


def render_main_menu():
    global search_entry
    clear_main_frame()

# -------------------------
# Menu Contents
# -------------------------

    title_frame = ctk.CTkFrame(
        content_frame,
        fg_color="#1f2a44",
        corner_radius=14,
        border_width=2,
        border_color="#d4af37"
    )
    title_frame.pack(fill="x", padx=18, pady=(10, 18))

    ctk.CTkLabel(
        title_frame,
        text="===o===[ DTT EXPRESS ]===o===",
        font=ctk.CTkFont(size=18, weight="bold"),
        text_color="#f5d76e"
    ).pack(pady=(12, 4))

    ctk.CTkLabel(
        title_frame,
        text="DTT v 78 Created By Anthony Witt 2026",
        font=ctk.CTkFont(size=24, weight="bold"),
        text_color="#f8f8f8"
    ).pack(pady=2)

    ctk.CTkLabel(
        title_frame,
        text="Revision V79 - Added search feature and fuzzy typing",
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color="#d4af37"
    ).pack(pady=2)

    ctk.CTkLabel(
        title_frame,
        text="Full Steam Diagnostics and Testing Toolkit",
        font=ctk.CTkFont(size=13, weight="bold"),
        text_color="#b8c7e0"
    ).pack(pady=(4, 12))

    search_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    search_frame.pack(fill="x", padx=18, pady=(0, 10))

    ctk.CTkLabel(
        search_frame,
        text="Search Tools",
        font=ctk.CTkFont(size=14, weight="bold")
    ).pack(anchor="w", pady=(0, 6))

    search_entry = ctk.CTkEntry(
        search_frame,
        textvariable=search_var,
        placeholder_text="Type to filter tools, like ssd, kb, disk health, notepad...",
        height=36
    )
    search_entry.pack(fill="x")

    filtered_any = False
    search_text = search_var.get()

    for section_title, items in get_main_menu_sections():
        visible_items = [
            (label, command)
            for label, command, keywords in items
            if matches_search(label, keywords, search_text)
        ]
        if visible_items:
            filtered_any = True
            section(section_title)
            for label, command in visible_items:
                add_button(label, command)

    if not filtered_any:
        ctk.CTkLabel(
            content_frame,
            text="No matching tools found.",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#d4af37"
        ).pack(pady=24)

    main_frame._parent_canvas.yview_moveto(0)

    if search_var.get():
        search_entry.focus_set()
        search_entry.icursor("end")


search_var.trace_add("write", refresh_main_menu_filter)
render_main_menu()

app.mainloop()
