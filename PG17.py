import customtkinter as ctk
import tkinter as tk
import os
import sys
import ctypes
from tkinter import messagebox

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
app.title("Diagnostics Test Tool V 0.81 (Modern UI)")
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
    win.title("System Information")
    win.geometry("900x700")
    ctk.CTkLabel(win, text="System Information Report", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
    textbox = ctk.CTkTextbox(win, wrap="word")
    textbox.pack(fill="both", expand=True, padx=10, pady=10)
    textbox.insert("1.0", "Loading system information...\nThis may take a few seconds.")
    textbox.configure(state="disabled")
    def load_report():
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", "System info would be here.")
        textbox.configure(state="disabled")
    threading.Thread(target=load_report, daemon=True).start()

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
        textbox.insert("1.0", "Drive health info would be here.")
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

def render_main_menu():
    clear_main_frame()

    # -------------------------
    # Menu Title Header
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
        text="Revision V 0.81 - Added live keyboard tester module with key log",
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color="#d4af37"
    ).pack(pady=2)

    ctk.CTkLabel(
        title_frame,
        text="Full Steam Diagnostics and Testing Toolkit",
        font=ctk.CTkFont(size=13, weight="bold"),
        text_color="#b8c7e0"
    ).pack(pady=(4, 12))

    # SYSTEM / HARDWARE
    section("SYSTEM / HARDWARE")
    add_button("System Info", open_system_info)
    add_button("Bitlocker Check", lambda: run_tool("BITLOCKERCHECK1.BAT"))
    add_button("Hotkeys Test", lambda: run_tool("HK1.BAT"))
    add_button("Device Manager", lambda: run_cmd("devmgmt.msc"))
    add_button("Battery Test", lambda: run_tool("Tools/Battery TEST/bat.exe"))
    add_button("Speaker Test", lambda: run_tool("st.mp3"))
    add_button("Mic Test", lambda: run_tool("soundcheck.exe"))
    add_button("Camera Test", lambda: run_cmd("start microsoft.windows.camera:"))
    add_button("Windows Activation", lambda: run_tool("ACT.bat"))
    # Keyboard Test: keep PG16's version
    add_button("Keyboard Test", show_keyboard_tester)
    add_button("Notepad", lambda: os.system("notepad"))
    add_button("Windows Update", render_windows_update_menu)
    add_button("Windows Test", lambda: run_tool("launch-tool.bat"))
    add_button("Show Serial / SKU", show_serial_and_sku)
    add_button("Change Audio Output", lambda: run_tool("AUDIOrun.bat"))

    # SYSTEM HEALTH
    section("SYSTEM HEALTH")
    add_button("SFC Scan", lambda: run_cmd("sfc /scannow"))
    add_button("SMART Drive Health", open_drive_health)
    add_button("Memory Diagnostic", lambda: run_cmd("mdsched.exe"))
    add_button("Disk Cleanup", lambda: run_cmd("cleanmgr"))

    # ADVANCED HARDWARE TESTING
    section("ADVANCED HARDWARE TESTING")
    add_button("Stress Test Suite", render_stress_test_menu)
    add_button("Performance Tests", render_performance_menu)
    add_button("USB Port Test", lambda: run_tool("UsbTreeView.exe"))
    add_button("SSD Test", lambda: run_tool("CrystalDiskInfo.exe"))

    # NETWORK
    section("NETWORK")
    add_button("Network Settings", lambda: run_cmd("start ms-settings:network"))
    add_button("WiFi Info", lambda: run_cmd("netsh wlan show interfaces"))

    # SETTINGS / SECURITY
    section("SETTINGS / SECURITY")
    add_button("Camera Settings", lambda: run_cmd("start ms-settings:privacy-webcam"))
    add_button("Activation Settings", lambda: run_cmd("start ms-settings:activation"))
    add_button("Sound Settings", lambda: run_cmd("start ms-settings:sound"))
    add_button("Account Settings", render_account_menu)
    add_button("Date / Time Settings", lambda: run_cmd("start ms-settings:dateandtime"))
    add_button("Language / Region", lambda: run_cmd("start ms-settings:regionlanguage"))
    add_button("Windows Defender", lambda: run_tool("wd.BAT"))
    add_button("Check Windows Key", lambda: run_tool("WK.BAT"))
    add_button("Windows Version", lambda: run_cmd("winver"))
    add_button("Computrace Check", lambda: run_tool("Computrace.bat"))
    add_button("More Settings Tools", render_settings_menu)

    # DEPLOYMENT / TESTS
    section("DEPLOYMENT / TESTS")
    add_button("Sysprep Options", render_sysprep_menu)

    # UTILITIES
    section("UTILITIES")
    add_button("Task Manager", lambda: run_cmd("taskmgr"))
    add_button("Event Viewer", lambda: run_cmd("eventvwr.msc"))
    add_button("Clear Temp Files", lambda: run_cmd('powershell "Remove-Item $env:TEMP\\* -Recurse -Force"'))
    add_button("Restart PC", lambda: run_cmd("shutdown /r /t 0"))
    add_button("Shutdown PC", lambda: run_cmd("shutdown /s /t 0"))
    add_button("Exit Program", app.destroy)


# ------------------------------------------------------------------
# Start app
# ------------------------------------------------------------------
render_main_menu()
app.mainloop()