import customtkinter as ctk
import tkinter as tk
import os
import sys
import ctypes
import difflib
from tkinter import messagebox
from PIL import Image

banner_img = None


# ✅ Catch crashes so the window doesn't close silently
import traceback
def excepthook(exc_type, exc_value, exc_tb):
    traceback.print_exception(exc_type, exc_value, exc_tb)
    input("Press ENTER to exit...")
sys.excepthook = excepthook

# ✅ Import embedded keyboard tester (full-featured)
import importlib.util as _importlib_util
import os as _os
_kb2_path = _os.path.join(_os.path.dirname(__file__), 'KeyboardTesterGUI2.py')
_spec = _importlib_util.spec_from_file_location("KeyboardTesterGUI2", _kb2_path)
KeyboardTesterGUI2 = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(KeyboardTesterGUI2)


# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BASE = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------------
# Admin helpers (unchanged logic)
# ------------------------------------------------------------------
def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


# ------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------
app = ctk.CTk()
app.title("Diagnostics Test Tool V 0.82 (Modern UI)")
app.geometry("850x700")

# Set window icon
icon_path = os.path.join(BASE, "media", "dtt.ico")
if os.path.exists(icon_path):
    try:
        app.iconbitmap(icon_path)
    except Exception:
        pass

active_screen = None


# ------------------------------------------------------------------
# Main frame (menu container)
# ------------------------------------------------------------------
main_frame = ctk.CTkScrollableFrame(app, width=800, height=650)
main_frame.pack(pady=10, padx=10, fill="both", expand=True)

content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
content_frame.pack(fill="both", expand=True)


# ------------------------------------------------------------------
# UI helpers
# ------------------------------------------------------------------
def clear_main_frame():
    for widget in content_frame.winfo_children():
        widget.destroy()


def section(title):
    ctk.CTkLabel(
        content_frame,
        text=title,
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


# ------------------------------------------------------------------
# Screen switch helpers
# ------------------------------------------------------------------
def clear_screen():
    global active_screen
    if active_screen is not None:
        active_screen.destroy()
        active_screen = None


def show_keyboard_tester():
    """Load KeyboardTesterGUI in the same window"""
    global active_screen
    clear_screen()

    # Hide menu
    try:
        main_frame.pack_forget()
    except Exception:
        pass

    global active_screen
    clear_screen()
    # Hide menu
    try:
        main_frame.pack_forget()
    except Exception:
        pass
    # Embed KeyboardTesterGUI2 in a Frame as a screen
    active_screen = tk.Frame(app, bg="#101723")
    active_screen.pack(fill="both", expand=True)
    # Place the full-featured tester inside this frame
    tester = KeyboardTesterGUI2.KeyboardTesterApp(active_screen)
    # Provide a callback to return to main menu when Menu button is clicked
    def menu_callback():
        return_to_main_menu()
    tester.set_menu_callback(menu_callback)


def return_to_main_menu(event=None):
    """Return to main menu"""
    global active_screen
    clear_screen()
    main_frame.pack(pady=10, padx=10, fill="both", expand=True)
    render_main_menu()


# ------------------------------------------------------------------
# Menus
# ------------------------------------------------------------------

# --- BEGIN: Stubs and helpers for missing PG15 features ---
import subprocess
import threading

def run_powershell_script(script_name):
    script_path = os.path.join(BASE, script_name)

    if not os.path.exists(script_path):
        return f"Missing PowerShell script:\n{script_name}"

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", script_path
            ],
            capture_output=True,
            text=True,
            timeout=300
        )
    except Exception as e:
        return f"Error launching PowerShell:\n{str(e)}"

    output = (result.stdout or "").strip()
    error = (result.stderr or "").strip()

    if result.returncode != 0:
        if error:
            return f"PowerShell Error:\n{error}"

    if output:
        return output

    return "No output returned from PowerShell script."


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
        result = subprocess.run([
            "powershell", "-NoProfile", "-Command", command
        ], capture_output=True, text=True, shell=False, timeout=20)
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

def open_system_info():
    win = ctk.CTkToplevel(app)
    win.title("System Information (Advanced)")
    win.geometry("950x750")

    ctk.CTkLabel(
        win,
        text="System Information Report",
        font=ctk.CTkFont(size=20, weight="bold")
    ).pack(pady=10)

    textbox = ctk.CTkTextbox(win, wrap="word")
    textbox.pack(fill="both", expand=True, padx=10, pady=10)

    textbox.insert(
        "1.0",
        "Collecting system information...\n"
        "This may take up to a minute.\n\n"
        "Administrator privileges may be requested."
    )
    textbox.configure(state="disabled")

    def load_report():
        report = run_powershell_script("HPLENDELLDEV5.ps1")

        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", report)
        textbox.configure(state="disabled")

    threading.Thread(target=load_report, daemon=True).start()

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

def open_drive_health():
    win = ctk.CTkToplevel(app)
    win.title("SMART Drive Health")
    win.geometry("800x500")
    ctk.CTkLabel(win, text="SMART Drive Health", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
    textbox = ctk.CTkTextbox(win, wrap="word")
    textbox.pack(fill="both", expand=True, padx=10, pady=10)
    textbox.insert("1.0", "Loading drive health information...")
    textbox.configure(state="disabled")
    def load_report():
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", generate_drive_health_report())
        textbox.configure(state="disabled")
    threading.Thread(target=load_report, daemon=True).start()

def show_serial_and_sku():
    win = ctk.CTkToplevel(app)
    win.title("Serial Number / SKU")
    win.geometry("700x320")
    textbox = ctk.CTkTextbox(win, wrap="word")
    textbox.pack(fill="both", expand=True, padx=10, pady=10)
    textbox.insert("1.0", "Serial and SKU info would be here.")
    textbox.configure(state="disabled")

def render_simple_menu(title, buttons):
    clear_main_frame()
    frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    frame.pack(fill="x", expand=True, pady=20)
    ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
    for label, command in buttons:
        ctk.CTkButton(frame, text=label, width=320, height=32, command=command).pack(pady=6)
    ctk.CTkButton(frame, text="Back", width=320, height=32, fg_color="#444444", command=render_main_menu).pack(pady=15)
    main_frame._parent_canvas.yview_moveto(0)

def render_account_menu():
    render_simple_menu("ACCOUNT SETTINGS", [
        ("Manage Users", lambda: run_cmd("start ms-settings:otherusers")),
        ("Delete User Account", lambda: run_tool("DELETEACCOUNT.BAT")),
        ("Create Local Account", lambda: run_tool("ACCOUNT.BAT")),
    ])

def render_settings_menu():
    render_simple_menu("SETTINGS / SECURITY", [
        ("Camera Settings", lambda: run_cmd("start ms-settings:privacy-webcam")),
        ("Activation Settings", lambda: run_cmd("start ms-settings:activation")),
        ("Sound Settings", lambda: run_cmd("start ms-settings:sound")),
        ("Account Settings", render_account_menu),
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
# --- END: Stubs and helpers ---


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
            ("Keyboard Test", show_keyboard_tester, ["keyboard", "kb", "double typing", "notepad"]),
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
            ("Account Settings", render_account_menu, ["account", "users", "login"]),
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
_search_trace_id = None


def refresh_main_menu_filter(*_args):
    if app.winfo_exists():
        render_main_menu()


def render_main_menu():
    global search_entry, _search_trace_id, banner_img

    # Remove trace BEFORE destroying widgets to avoid dead-widget callbacks
    if _search_trace_id is not None:
        try:
            search_var.trace_remove("write", _search_trace_id)
        except Exception:
            pass
        _search_trace_id = None

    clear_main_frame()

    # -------------------------
    # Banner / Title Header
    # -------------------------
    title_frame = ctk.CTkFrame(
        content_frame,
        fg_color="#1f2a44",
        corner_radius=14,
        border_width=2,
        border_color="#d4af37"
    )
    title_frame.pack(fill="x", padx=18, pady=(10, 18))

    banner_path = os.path.join(BASE, "media", "dtt_express_banner.png")
    if os.path.exists(banner_path):
        banner_img = ctk.CTkImage(
            light_image=Image.open(banner_path),
            dark_image=Image.open(banner_path),
            size=(860, 240)
        )
        ctk.CTkLabel(
            title_frame,
            image=banner_img,
            text=""
        ).pack(pady=(12, 6))
    else:
        ctk.CTkLabel(
            title_frame,
            text="===o===[ DTT EXPRESS ]===o===",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#f5d76e"
        ).pack(pady=(12, 4))

        ctk.CTkLabel(
            title_frame,
            text="DTT v 0.84 Created By Anthony Witt 2026",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#f8f8f8"
        ).pack(pady=2)

        ctk.CTkLabel(
            title_frame,
            text="Revision V0.84 - Search works, banner image support added",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#d4af37"
        ).pack(pady=2)

    ctk.CTkLabel(
        title_frame,
        text="Full Steam Diagnostics and Testing Toolkit",
        font=ctk.CTkFont(size=13, weight="bold"),
        text_color="#b8c7e0"
    ).pack(pady=(4, 12))

    # -------------------------
    # Search Tools
    # -------------------------
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

    # Re-register trace now that the new entry widget exists
    _search_trace_id = search_var.trace_add("write", refresh_main_menu_filter)

    # -------------------------
    # Menu Contents (filtered)
    # -------------------------
    search_text = search_var.get()
    filtered_any = False

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


# ------------------------------------------------------------------
# Start app
# ------------------------------------------------------------------
render_main_menu()
app.mainloop()