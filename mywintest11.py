import customtkinter as ctk
import tkinter as tk
import os
import sys
import ctypes
import difflib
import json
import re
import subprocess
import threading
import time
from tkinter import messagebox, ttk
from PIL import Image
import winsound

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
_kb2_path = _os.path.join(_os.path.dirname(__file__), "KeyboardTesterGUI2.py")
_spec = _importlib_util.spec_from_file_location("KeyboardTesterGUI2", _kb2_path)
KeyboardTesterGUI2 = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(KeyboardTesterGUI2)

# Ensure venv site-packages is in sys.path for MICTEST1 module loading
_venv_site_packages = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), ".venv", "Lib", "site-packages")
if _venv_site_packages not in sys.path:
    sys.path.insert(0, _venv_site_packages)

_mic_path = _os.path.join(_os.path.dirname(__file__), "MICTEST1.py")
_mic_spec = _importlib_util.spec_from_file_location("MICTEST1", _mic_path)
MICTEST1 = _importlib_util.module_from_spec(_mic_spec)
_mic_spec.loader.exec_module(MICTEST1)


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

def ensure_admin():
    if is_admin():
        return

    if getattr(sys, "frozen", False):
        executable = sys.executable
        params = " ".join(f'"{arg}"' for arg in sys.argv[1:])
    else:
        executable = sys.executable
        script_path = os.path.abspath(sys.argv[0])
        extra_args = " ".join(f'"{arg}"' for arg in sys.argv[1:])
        params = f'"{script_path}"'
        if extra_args:
            params = f"{params} {extra_args}"

    result = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        executable,
        params,
        None,
        1
    )
    if result <= 32:
        raise RuntimeError("Administrator privileges are required to run this app.")
    sys.exit(0)


# ------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------
ensure_admin()

app = ctk.CTk()
app.title("Diagnostics Test Tool V 0.88 (Modern UI)")
app.geometry("850x700")

# Set window icon
icon_path = os.path.join(BASE, "media", "dtt.ico")
if os.path.exists(icon_path):
    try:
        app.iconbitmap(icon_path)
    except Exception:
        pass

active_screen = None
_speaker_after_id = None
_speaker_process = None
_speaker_backend = None
_speaker_pygame = None
_camera_captures = []
_camera_after_id = None
_camera_index = 0


# ------------------------------------------------------------------
# Main frame (menu container)
# ------------------------------------------------------------------
main_frame = ctk.CTkScrollableFrame(app, width=800, height=650)
# Main menu removed: do not pack the main menu frame so it never appears
# main_frame.pack(pady=10, padx=10, fill="both", expand=True)

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
    stop_speaker_test()
    stop_camera_preview()
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
    # Embed keyboard tester variant in a Frame as a screen
    active_screen = tk.Frame(app, bg="#101723")
    active_screen.pack(fill="both", expand=True)
    # Place the full-featured tester inside this frame
    tester = KeyboardTesterGUI2.KeyboardTesterApp(active_screen)
    # Provide a callback to return to main menu when Menu button is clicked
    def menu_callback():
        return_to_main_menu()
    tester.set_menu_callback(menu_callback)


def show_mic_tester():
    """Load MICTEST1 in the same window"""
    global active_screen
    clear_screen()

    try:
        main_frame.pack_forget()
    except Exception:
        pass

    active_screen = tk.Frame(app, bg="#101723")
    active_screen.pack(fill="both", expand=True)

    try:
        mic_tester = MICTEST1.AudioDiagnosticApp(active_screen)
    except Exception as exc:
        messagebox.showerror("Mic Test", f"Could not start embedded Mic Test.\n\n{exc}")
        return_to_main_menu()
        return

    mic_tester.set_menu_callback(return_to_main_menu)


def stop_camera_preview():
    global _camera_captures, _camera_after_id
    if _camera_after_id:
        try:
            app.after_cancel(_camera_after_id)
        except Exception:
            pass
        _camera_after_id = None
    for cap in _camera_captures:
        try:
            cap.release()
        except Exception:
            pass
    _camera_captures = []


def show_camera_test_screen():
    """Load Camera Test in the same window."""
    global active_screen, _camera_captures, _camera_after_id, _camera_index
    clear_screen()

    try:
        main_frame.pack_forget()
    except Exception:
        pass

    active_screen = tk.Frame(app, bg="#101723")
    active_screen.pack(fill="both", expand=True)

    ctk.CTkLabel(
        active_screen,
        text="Camera Test",
        font=ctk.CTkFont(size=24, weight="bold"),
        text_color="#f8f8f8",
    ).pack(pady=(14, 6))

    status_label = ctk.CTkLabel(
        active_screen,
        text="Starting camera...",
        font=ctk.CTkFont(size=13),
        text_color="#d4af37",
    )
    status_label.pack(pady=(0, 8))

    previews_row = ctk.CTkFrame(active_screen, fg_color="transparent")
    previews_row.pack(fill="both", expand=True, padx=14, pady=(0, 10))

    button_row = ctk.CTkFrame(active_screen, fg_color="transparent")
    button_row.pack(pady=(0, 14))

    ctk.CTkButton(
        button_row,
        text="Back to Main Menu",
        width=190,
        height=34,
        fg_color="#444444",
        hover_color="#555555",
        command=return_to_main_menu,
    ).pack(side="left", padx=6)

    try:
        import cv2
        from PIL import ImageTk
    except Exception:
        status_label.configure(
            text="OpenCV is not installed. Run: pip install opencv-python",
            text_color="#ff7b72",
        )
        return

    def discover_camera_indexes(max_to_scan=6, max_found=2):
        found = []
        for idx in range(max_to_scan):
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if cap.isOpened():
                found.append(idx)
            try:
                cap.release()
            except Exception:
                pass
            if len(found) >= max_found:
                break
        return found

    camera_indexes = discover_camera_indexes()
    if not camera_indexes:
        status_label.configure(
            text="Could not open camera. Check webcam permissions/device.",
            text_color="#ff7b72",
        )
        return

    _camera_captures = []
    preview_labels = []
    for idx in camera_indexes:
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if not cap.isOpened():
            try:
                cap.release()
            except Exception:
                pass
            continue
        _camera_captures.append(cap)

        cam_panel = ctk.CTkFrame(previews_row, fg_color="transparent")
        cam_panel.pack(side="left", fill="both", expand=True, padx=8)

        live_label = tk.Label(cam_panel, bg="#000000")
        live_label.pack(fill="both", expand=True)
        preview_labels.append(live_label)

        ctk.CTkLabel(
            cam_panel,
            text=f"Camera {idx}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#d4af37",
        ).pack(pady=(6, 0))

    if not _camera_captures:
        status_label.configure(
            text="Cameras detected but could not start preview.",
            text_color="#ff7b72",
        )
        return

    _camera_index = camera_indexes[0]
    if len(_camera_captures) == 1:
        status_label.configure(text=f"Live preview running (Camera {_camera_index})", text_color="#7ee787")
    else:
        status_label.configure(
            text=f"Live preview running: Camera {camera_indexes[0]} and Camera {camera_indexes[1]}",
            text_color="#7ee787",
        )

    def update_frame():
        global _camera_after_id
        if not _camera_captures or not active_screen or not active_screen.winfo_exists():
            return
        for idx, cap in enumerate(_camera_captures):
            if idx >= len(preview_labels):
                continue
            ok, frame = cap.read()
            if not ok:
                continue
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame)
            image.thumbnail((430, 360))
            tk_image = ImageTk.PhotoImage(image=image)
            preview_labels[idx].configure(image=tk_image)
            preview_labels[idx].image = tk_image
        _camera_after_id = app.after(30, update_frame)
    update_frame()


def return_to_main_menu(event=None):
    """Return to main menu"""
    global active_screen
    try:
        app.unbind("<Return>")
    except Exception:
        pass
    # Menus removed — return to the hardware-only screen instead
    clear_screen()
    try:
        show_hardware_test_screen()
    except Exception:
        # fallback: recreate hardware screen directly
        try:
            clear_screen()
            show_hardware_test_screen()
        except Exception:
            pass


def stop_speaker_test():
    global _speaker_after_id, _speaker_process, _speaker_backend
    if _speaker_after_id:
        try:
            app.after_cancel(_speaker_after_id)
        except Exception:
            pass
        _speaker_after_id = None
    if _speaker_process is not None:
        try:
            if _speaker_process.poll() is None:
                _speaker_process.terminate()
        except Exception:
            pass
        _speaker_process = None
    _speaker_backend = None


def start_speaker_playback(on_finished):
    global _speaker_after_id, _speaker_process, _speaker_backend
    stop_speaker_test()
    mp3_path = os.path.join(BASE, "st.wav")
    if not os.path.exists(mp3_path):
        messagebox.showwarning("Missing File", f"Cannot find:\n{mp3_path}")
        return False
    try:
        winsound.PlaySound(mp3_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        _speaker_backend = "winsound"
    except Exception as winsound_exc:
        try:
            escaped_path = mp3_path.replace("'", "''")
            ps_script = (
                "Add-Type -AssemblyName PresentationCore; "
                f"$uri = [System.Uri]::new('{escaped_path}'); "
                "$player = New-Object System.Windows.Media.MediaPlayer; "
                "$done = $false; "
                "$player.add_MediaEnded({ $script:done = $true }); "
                "$player.add_MediaFailed({ $script:done = $true }); "
                "$player.Open($uri); "
                "$player.Play(); "
                "while (-not $done) { Start-Sleep -Milliseconds 200 }; "
                "$player.Close();"
            )
            _speaker_process = subprocess.Popen(
                ["powershell", "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            _speaker_backend = "powershell"
        except Exception as ps_exc:
            messagebox.showerror(
                "Speaker Test",
                "Could not play ST.WAV.\n\n"
                f"Winsound error: {winsound_exc}\n\n"
                f"PowerShell error: {ps_exc}"
            )
            stop_speaker_test()
            return False

    def poll_playback():
        global _speaker_after_id, _speaker_process, _speaker_backend
        if active_screen is None or not active_screen.winfo_exists():
            stop_speaker_test()
            return

        if _speaker_backend == "winsound":
            # Winsound plays asynchronously with SND_ASYNC, so we wait a bit and assume it's done
            # This is approximate; the audio file length determines actual duration
            if hasattr(poll_playback, 'winsound_count'):
                poll_playback.winsound_count += 1
                if poll_playback.winsound_count < 20:  # Wait ~7 seconds (350ms * 20)
                    _speaker_after_id = app.after(350, poll_playback)
                    return
            else:
                poll_playback.winsound_count = 1
                _speaker_after_id = app.after(350, poll_playback)
                return
            poll_playback.winsound_count = 0
        elif _speaker_backend == "powershell":
            if _speaker_process is not None and _speaker_process.poll() is None:
                _speaker_after_id = app.after(350, poll_playback)
                return
            if _speaker_process is not None:
                return_code = _speaker_process.poll()
                if return_code not in (None, 0):
                    stderr_text = (_speaker_process.stderr.read() or "").strip()
                    messagebox.showerror(
                        "Speaker Test",
                        "Could not play ST.WAV with PowerShell backend.\n\n"
                        + (stderr_text or f"PowerShell exited with code {return_code}.")
                    )
        _speaker_process = None
        stop_speaker_test()
        on_finished()

    _speaker_after_id = app.after(350, poll_playback)
    return True


def show_speaker_test_screen():
    global active_screen
    clear_screen()

    try:
        main_frame.pack_forget()
    except Exception:
        pass

    active_screen = ctk.CTkFrame(app, fg_color="#101820")
    active_screen.pack(fill="both", expand=True, padx=10, pady=10)

    ctk.CTkLabel(
        active_screen,
        text="Speaker Test",
        font=ctk.CTkFont(size=24, weight="bold"),
        text_color="white"
    ).pack(pady=(25, 10))

    status_label = ctk.CTkLabel(
        active_screen,
        text="Playing ST.WAV now...",
        font=ctk.CTkFont(size=14),
        text_color="#b8c7e0"
    )
    status_label.pack(pady=(0, 20))

    buttons_frame = ctk.CTkFrame(active_screen, fg_color="transparent")
    buttons_frame.pack(pady=(6, 10))

    restart_button = ctk.CTkButton(
        buttons_frame,
        text="Restart",
        width=140,
        state="disabled"
    )
    restart_button.pack(side="left", padx=8)

    menu_button = ctk.CTkButton(
        buttons_frame,
        text="Main Menu",
        width=140,
        fg_color="#444444",
        hover_color="#555555",
        command=return_to_main_menu,
        state="disabled"
    )
    menu_button.pack(side="left", padx=8)

    def on_finished():
        if active_screen is None or not active_screen.winfo_exists():
            return
        status_label.configure(text="Playback finished. Choose an option below.")
        restart_button.configure(state="normal")
        menu_button.configure(state="normal")

    def restart_test():
        if active_screen is None or not active_screen.winfo_exists():
            return
        status_label.configure(text="Playing ST.WAV now...")
        restart_button.configure(state="disabled")
        menu_button.configure(state="disabled")
        started = start_speaker_playback(on_finished)
        if not started:
            status_label.configure(text="Could not start ST.WAV. Check file location.")
            menu_button.configure(state="normal")

    restart_button.configure(command=restart_test)
    restart_test()


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

def run_powershell(command, timeout=60):
    try:
        result = subprocess.run([
            "powershell", "-NoProfile", "-Command", command
        ], capture_output=True, text=True, shell=False, timeout=timeout)
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

def append_console_text(textbox, text):
    textbox.configure(state="normal")
    textbox.insert("end", text)
    textbox.see("end")
    textbox.configure(state="disabled")


def ui_call(callback, *args, **kwargs):
    """Run Tk UI updates on the main thread."""
    try:
        if app.winfo_exists():
            app.after(0, lambda: callback(*args, **kwargs))
    except Exception:
        pass


def widget_exists(widget):
    try:
        return widget is not None and widget.winfo_exists()
    except Exception:
        return False

def run_process_capture(args, shell=False):
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        shell=shell
    )
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode, output

def show_bitlocker_screen():
    global active_screen
    clear_screen()

    try:
        main_frame.pack_forget()
    except Exception:
        pass

    active_screen = ctk.CTkFrame(app, fg_color="#101723")
    active_screen.pack(fill="both", expand=True, padx=10, pady=10)

    ctk.CTkLabel(
        active_screen,
        text="BitLocker Check",
        font=ctk.CTkFont(size=20, weight="bold")
    ).pack(pady=(14, 8))

    status_label = ctk.CTkLabel(
        active_screen,
        text="Running BitLocker check...",
        font=ctk.CTkFont(size=14)
    )
    status_label.pack(pady=(0, 8))

    textbox = ctk.CTkTextbox(active_screen, wrap="none")
    textbox.pack(fill="both", expand=True, padx=14, pady=(0, 12))
    textbox.insert("1.0", "Preparing BitLocker check...\n\n")
    textbox.configure(state="disabled")

    return_button = ctk.CTkButton(
        active_screen,
        text="Back To Main Menu",
        command=return_to_main_menu,
        state="disabled"
    )
    return_button.pack(pady=(0, 14))

    def finish_screen():
        status_label.configure(text="Finished. Press Enter to go back to the main menu.")
        return_button.configure(state="normal")
        app.bind("<Return>", return_to_main_menu)
        app.focus_force()

    def write(text):
        app.after(0, lambda: append_console_text(textbox, text))

    def worker():
        try:
            write("Running BitLocker check with administrator rights...\n\n")

            write("==========================================\n")
            write("    BitLocker Status for All Drives\n")
            write("==========================================\n\n")

            rc_all, output_all = run_process_capture(["manage-bde", "-status"])
            write(output_all if output_all else "No output returned.\n")
            if output_all and not output_all.endswith("\n"):
                write("\n")

            write("\n==========================================\n")
            write("Current Status For C:\n")
            write("==========================================\n")

            rc_c, output_c = run_process_capture(["manage-bde", "-status", "C:"])
            write(output_c if output_c else "No output returned for C:.\n")
            if output_c and not output_c.endswith("\n"):
                write("\n")

            if "fully decrypted" in output_c.lower():
                write("\nBitLocker is already fully decrypted.\n")
            else:
                write("\nBitLocker is not fully decrypted.\n")
                write("Disabling BitLocker on C: ...\n\n")
                rc_disable, output_disable = run_process_capture([
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy", "Bypass",
                    "-Command",
                    "Disable-BitLocker -MountPoint 'C:'"
                ])
                write(output_disable if output_disable else "Disable-BitLocker command sent.\n")
                if output_disable and not output_disable.endswith("\n"):
                    write("\n")
                if rc_disable != 0:
                    write(f"\nDisable-BitLocker returned exit code {rc_disable}.\n")

            write("\nFinal BitLocker Status for C:\n")
            rc_final, output_final = run_process_capture(["manage-bde", "-status", "C:"])
            write(output_final if output_final else "No final status output returned.\n")
            if output_final and not output_final.endswith("\n"):
                write("\n")

            if rc_all != 0 or rc_c != 0 or rc_final != 0:
                write("\nOne or more BitLocker commands returned a non-zero exit code.\n")
        except Exception as exc:
            write(f"\nError while running BitLocker check:\n{exc}\n")
        finally:
            write("\n==========================================\n")
            write("Press Enter to go back to the main menu.\n")
            app.after(0, finish_screen)

    threading.Thread(target=worker, daemon=True).start()

# ------------------------------------------------------------------
# Battery Screen (embedded from BAT.py)
# ------------------------------------------------------------------

BATTERY_STATUS_MAP = {
    1: "Discharging",
    2: "Plugged in, not charging",
    3: "Fully Charged",
    4: "Low",
    5: "Critical",
    6: "Charging",
    7: "Charging (High)",
    8: "Charging (Low)",
    9: "Charging (Critical)",
    10: "Undefined",
    11: "Partially Charged",
}


def _run_powershell_json(command):
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        error_text = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(error_text or "PowerShell command failed.")
    output = (result.stdout or "").strip()
    if not output:
        return None
    return json.loads(output)


def _get_battery_data():
    battery_command = r"""
$wmi   = Get-CimInstance -ClassName BatteryStatus -Namespace root\wmi -ErrorAction SilentlyContinue | Select-Object -First 1
$win32 = Get-CimInstance -ClassName Win32_Battery -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $wmi -and -not $win32) { $null | ConvertTo-Json -Compress; return }

$level = if ($win32) { $win32.EstimatedChargeRemaining } else { $null }
$name  = if ($win32 -and $win32.Name) { $win32.Name } else { "Battery" }

$statusCode = 10
if ($wmi) {
    if     ($wmi.Charging    -eq $true) { $statusCode = 6 }
    elseif ($wmi.Discharging -eq $true) { $statusCode = 1 }
    elseif ($wmi.PowerOnline -eq $true) {
        if ($level -ge 100) { $statusCode = 3 } else { $statusCode = 2 }
    }
}

[pscustomobject]@{
    Name                     = $name
    BatteryStatus            = $statusCode
    EstimatedChargeRemaining = $level
} | ConvertTo-Json -Compress
"""

    health_command = r"""
$reportPath = Join-Path $env:TEMP 'battery-report.xml'
powercfg /batteryreport /XML /OUTPUT $reportPath | Out-Null
if (-not (Test-Path $reportPath)) { $null | ConvertTo-Json -Compress; return }
try {
    [xml]$xml = Get-Content -LiteralPath $reportPath
    $batteryNode = $xml.BatteryReport.Batteries.Battery | Select-Object -First 1
    if (-not $batteryNode) { $null | ConvertTo-Json -Compress; return }
    [pscustomobject]@{
        DesignCapacity    = $batteryNode.DesignCapacity
        FullChargeCapacity = $batteryNode.FullChargeCapacity
        CycleCount        = $batteryNode.CycleCount
    } | ConvertTo-Json -Compress
} catch { $null | ConvertTo-Json -Compress }
"""

    battery_info = _run_powershell_json(battery_command)
    if not battery_info:
        return None

    health_info = _run_powershell_json(health_command) or {}

    name        = battery_info.get("Name") or "Battery"
    level       = battery_info.get("EstimatedChargeRemaining")
    status_code = battery_info.get("BatteryStatus")
    status_text = BATTERY_STATUS_MAP.get(status_code, f"Unknown ({status_code})")

    design_capacity    = health_info.get("DesignCapacity")
    full_charge_capacity = health_info.get("FullChargeCapacity")
    cycle_count        = health_info.get("CycleCount")

    health_percent = None
    if design_capacity and full_charge_capacity:
        try:
            design_value = int(str(design_capacity).replace(",", "").strip())
            full_value   = int(str(full_charge_capacity).replace(",", "").strip())
            health_percent = min(round((full_value * 100) / design_value, 1), 100.0) if design_value else None
            health_text    = f"{health_percent:.1f}%"
            capacity_text  = f"{full_value} / {design_value} mWh"
        except Exception:
            health_text   = "Unavailable"
            capacity_text = f"{full_charge_capacity} / {design_capacity} mWh"
    else:
        health_text   = "Unavailable"
        capacity_text = "Unavailable"

    return {
        "name":          name,
        "level":         level,
        "level_text":    f"{level}%" if level not in (None, "") else "Unknown",
        "status_text":   status_text,
        "health_percent": health_percent,
        "health_text":   health_text,
        "capacity_text": capacity_text,
        "cycle_text":    str(cycle_count) if cycle_count not in (None, "") else "Unavailable",
    }


def _level_color(level):
    if level >= 60:
        return "#7ee787"
    if level >= 25:
        return "#e3b341"
    return "#ff7b72"


def show_battery_screen():
    global active_screen
    clear_screen()
    try:
        main_frame.pack_forget()
    except Exception:
        pass

    active_screen = ctk.CTkFrame(app, fg_color="#101820")
    active_screen.pack(fill="both", expand=True, padx=10, pady=10)

    # --- Title ---
    ctk.CTkLabel(
        active_screen,
        text="Battery Status",
        font=ctk.CTkFont(size=22, weight="bold"),
        text_color="white"
    ).pack(anchor="w", padx=24, pady=(18, 2))

    device_label = ctk.CTkLabel(
        active_screen, text="",
        font=ctk.CTkFont(size=11), text_color="#9fb3c8"
    )
    device_label.pack(anchor="w", padx=24, pady=(0, 10))

    # --- Charge level ---
    level_value = ctk.CTkLabel(
        active_screen, text="--%",
        font=ctk.CTkFont(size=36, weight="bold"), text_color="#7ee787"
    )
    level_value.pack(anchor="w", padx=24)

    # Progress bar using tkinter ttk inside a tk.Frame
    bar_frame = tk.Frame(active_screen, bg="#101820")
    bar_frame.pack(anchor="w", padx=24, pady=(8, 16))
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Battery.Horizontal.TProgressbar", thickness=20, troughcolor="#1e2a3a", background="#7ee787")
    level_bar = ttk.Progressbar(bar_frame, orient="horizontal", length=420,
                                 mode="determinate", maximum=100,
                                 style="Battery.Horizontal.TProgressbar")
    level_bar.pack()

    # --- Info labels ---
    health_label   = ctk.CTkLabel(active_screen, text="Battery health: --",
                                   font=ctk.CTkFont(size=14, weight="bold"), text_color="white")
    health_label.pack(anchor="w", padx=24, pady=(0, 6))

    status_label   = ctk.CTkLabel(active_screen, text="Status: --",
                                   font=ctk.CTkFont(size=13), text_color="white")
    status_label.pack(anchor="w", padx=24, pady=(0, 4))

    capacity_label = ctk.CTkLabel(active_screen, text="Capacity: --",
                                   font=ctk.CTkFont(size=13), text_color="white")
    capacity_label.pack(anchor="w", padx=24, pady=(0, 4))

    cycle_label    = ctk.CTkLabel(active_screen, text="Cycle count: --",
                                   font=ctk.CTkFont(size=13), text_color="white")
    cycle_label.pack(anchor="w", padx=24, pady=(0, 4))

    message_label  = ctk.CTkLabel(active_screen, text="",
                                   font=ctk.CTkFont(size=11), text_color="#ffb86c")
    message_label.pack(anchor="w", padx=24, pady=(0, 14))

    # --- Buttons ---
    btn_row = ctk.CTkFrame(active_screen, fg_color="transparent")
    btn_row.pack(anchor="w", padx=20, pady=(4, 16))

    _battery_after_id = [None]

    def do_refresh():
        try:
            data = _get_battery_data()
            if not data:
                def _apply_no_battery():
                    if not widget_exists(active_screen):
                        return
                    device_label.configure(text="No battery detected")
                    level_value.configure(text="--%", text_color="#ff7b72")
                    level_bar["value"] = 0
                    health_label.configure(text="Battery health: Unavailable")
                    status_label.configure(text="Status: Unavailable")
                    capacity_label.configure(text="Capacity: Unavailable")
                    cycle_label.configure(text="Cycle count: Unavailable")
                    message_label.configure(text="This system may be a desktop or may not expose battery data.")
                ui_call(_apply_no_battery)
                return
            lv = data["level"] if isinstance(data["level"], int) else 0
            color = _level_color(lv)
            def _apply_data():
                if not widget_exists(active_screen):
                    return
                device_label.configure(text=data["name"])
                level_value.configure(text=data["level_text"], text_color=color)
                level_bar["value"] = lv
                style.configure("Battery.Horizontal.TProgressbar", background=color)
                health_label.configure(text=f"Battery health: {data['health_text']}")
                status_label.configure(text=f"Status: {data['status_text']}")
                capacity_label.configure(text=f"Capacity: {data['capacity_text']}")
                cycle_label.configure(text=f"Cycle count: {data['cycle_text']}")
                message_label.configure(text="")
            ui_call(_apply_data)
        except Exception as exc:
            ui_call(lambda: widget_exists(message_label) and message_label.configure(text=str(exc)))

    def auto_refresh():
        if active_screen is None or not active_screen.winfo_exists():
            return
        threading.Thread(target=do_refresh, daemon=True).start()
        _battery_after_id[0] = app.after(5000, auto_refresh)

    def go_back():
        if _battery_after_id[0]:
            try:
                app.after_cancel(_battery_after_id[0])
            except Exception:
                pass
        return_to_main_menu()

    ctk.CTkButton(
        btn_row, text="Refresh", width=120, height=34,
        command=lambda: threading.Thread(target=do_refresh, daemon=True).start()
    ).pack(side="left", padx=(0, 10))

    ctk.CTkButton(
        btn_row, text="Back to Main Menu", width=180, height=34,
        fg_color="#444444", hover_color="#555555",
        command=go_back
    ).pack(side="left")

    # Kick off first load + auto-refresh
    threading.Thread(target=do_refresh, daemon=True).start()
    _battery_after_id[0] = app.after(5000, auto_refresh)


# ------------------------------------------------------------------
# Combined Hardware Test Screen
# ------------------------------------------------------------------
def show_hardware_test_screen():
    global active_screen, _camera_captures, _camera_after_id
    clear_screen()
    # Hide and clear the main menu so its widgets don't remain visible
    try:
        # Destroy any existing menu widgets and remove the menu frame from view
        clear_main_frame()
        main_frame.pack_forget()
    except Exception:
        pass
    try:
        # Give the embedded keyboard tester enough room to avoid clipping.
        app.geometry("1460x900")
    except Exception:
        pass

    _bat_after_id = [None]
    _cam_after_local = [None]
    _cam_caps_local = []
    _kb_bind_id = [None]

    active_screen = ctk.CTkFrame(app, fg_color="#0d1117")
    active_screen.pack(fill="both", expand=True)
    try:
        # Ensure hardware screen is on top of the main menu
        active_screen.lift()
    except Exception:
        pass

    # ── Top bar ──────────────────────────────────────────────────────
    top_bar = ctk.CTkFrame(active_screen, fg_color="#1f2a44", corner_radius=0, height=46)
    top_bar.pack(fill="x", side="top")
    top_bar.pack_propagate(False)
    ctk.CTkLabel(top_bar, text="Hardware Test Suite — Revision 0.09: Added Windows Defender Virus Scan ",
                 font=ctk.CTkFont(size=18, weight="bold"),
                 text_color="#f5d76e").pack(side="left", padx=18, pady=8)

    def _go_back():
        # Cancel all timers and release cameras
        if _bat_after_id[0]:
            try: app.after_cancel(_bat_after_id[0])
            except Exception: pass
        if _cam_after_local[0]:
            try: app.after_cancel(_cam_after_local[0])
            except Exception: pass
        for cap in _cam_caps_local:
            try: cap.release()
            except Exception: pass
        _cam_caps_local.clear()
        if _kb_bind_id[0]:
            try:
                app.unbind("<KeyPress>", _kb_bind_id[0])
            except Exception:
                pass
            _kb_bind_id[0] = None
        stop_speaker_test()
        return_to_main_menu()

    # ── Scrollable body ───────────────────────────────────────────────
    body = ctk.CTkScrollableFrame(active_screen, fg_color="#0d1117")
    body.pack(fill="both", expand=True, padx=0, pady=0)

    def card(parent, title):
        f = ctk.CTkFrame(parent, fg_color="#161b22", corner_radius=10,
                         border_width=1, border_color="#30363d")
        # default: card fills horizontally only; callers may override to expand
        f.pack(fill="x", padx=14, pady=8)
        ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#58a6ff").pack(anchor="w", padx=14, pady=(10, 6))
        # Status boxes at bottom of every card: PASS (green) and FAIL (red)
        try:
            status_frame = tk.Frame(f, bg="#161b22")
            status_frame.pack(side="bottom", fill="x", padx=14, pady=(6, 10))

            fail_box = tk.Label(status_frame, text=" FAIL ", bg="#ff7b72", fg="#3b0000",
                                font=(None, 10, 'bold'), bd=1, relief="solid")
            fail_box.pack(side="right", padx=(6, 4))

            pass_box = tk.Label(status_frame, text=" PASS ", bg="#7ee787", fg="#063500",
                                font=(None, 10, 'bold'), bd=1, relief="solid")
            pass_box.pack(side="right", padx=(6, 4))
        except Exception:
            # If something goes wrong creating status boxes, ignore and continue
            pass
        return f

    # ══════════════════════════════════════════════════════════════════
    # 1. AUDIOG RUNNER CARD (runs audiog.ps1 with result display)
    # ══════════════════════════════════════════════════════════════════
    ag_card = card(body, "🔈  Audio Changer")
    
    ag_status_label = ctk.CTkLabel(ag_card, text="Running audio configuration...", font=ctk.CTkFont(size=12), text_color="#9fb3c8")
    ag_status_label.pack(anchor="w", padx=14, pady=(0, 10))
    
    # Results labels frame
    ag_results_frame = ctk.CTkFrame(ag_card, fg_color="transparent")
    ag_results_frame.pack(fill="both", expand=False, padx=14, pady=(0, 10))
    # Buffer for dynamic output lines
    ag_output_labels = []

    def _add_ag_line(line):
        try:
            lbl = ctk.CTkLabel(ag_results_frame, text=line.strip(), font=ctk.CTkFont(size=10), text_color="#d4af37", justify="left", wraplength=600)
            lbl.pack(anchor="w", pady=2)
            ag_output_labels.append(lbl)
            if len(ag_output_labels) > 15:
                old = ag_output_labels.pop(0)
                old.destroy()
        except Exception:
            pass
    
    # Result labels
    ag_current_label = ctk.CTkLabel(ag_results_frame, text="Current Device: —", font=ctk.CTkFont(size=11), text_color="#d4af37", justify="left", wraplength=500)
    ag_current_label.pack(anchor="w", pady=4)
    
    ag_switched_label = ctk.CTkLabel(ag_results_frame, text="Switched To: —", font=ctk.CTkFont(size=11), text_color="#d4af37", justify="left", wraplength=500)
    ag_switched_label.pack(anchor="w", pady=4)
    
    ag_input_label = ctk.CTkLabel(ag_results_frame, text="Input Device: —", font=ctk.CTkFont(size=11), text_color="#d4af37", justify="left", wraplength=500)
    ag_input_label.pack(anchor="w", pady=4)

    def _start_audiog():
        script_path = os.path.join(BASE, "audiog.ps1")
        if not os.path.exists(script_path):
            ui_call(lambda: ag_status_label.configure(text="audiog.ps1 not found", text_color="#ff7b72"))
            return

        # Use pwsh (PowerShell 7) when available — falls back to powershell (5.1)
        import shutil as _shutil
        _ps_exe = "pwsh" if _shutil.which("pwsh") else "powershell"
        cmd = [_ps_exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path]
        creation = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            # Redirect stderr into stdout so we don't miss messages
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                creationflags=creation,
            )
            
            ui_call(lambda: ag_status_label.configure(text=f"Running Audio Changer...", text_color="#7ee787"))
            
            def _reader():
                current_dev = None
                switched_dev = None
                input_dev = None
                
                try:
                    # Read combined stdout+stderr
                    while True:
                        if proc.stdout is None:
                            break
                        line = proc.stdout.readline()
                        if not line:
                            if proc.poll() is not None:
                                break
                            time.sleep(0.1)
                            continue

                        # Display output line in the Audio Changer results frame
                        ui_call(_add_ag_line, line)

                        # Parse key information from output
                        line_stripped = line.strip()
                        if "Current default audio device:" in line_stripped:
                            current_dev = line_stripped.split("Current default audio device:")[-1].strip()
                        elif "Switched audio output (speakers) to:" in line_stripped:
                            switched_dev = line_stripped.split("Switched audio output (speakers) to:")[-1].strip()
                        elif "Switched audio input (microphone) to:" in line_stripped:
                            input_dev = line_stripped.split("Switched audio input (microphone) to:")[-1].strip()
                        elif "No preferred 'Microphone Array' input device was found" in line_stripped:
                            input_dev = "No preferred Microphone Array found"
                    
                finally:
                    rc = proc.poll() or 0

                    # Update labels (final values)
                    ui_call(lambda: ag_current_label.configure(text=f"Current Device: {current_dev or '—'}"))
                    ui_call(lambda: ag_switched_label.configure(text=f"Switched To: {switched_dev or '—'}"))
                    ui_call(lambda: ag_input_label.configure(text=f"Input Device: {input_dev or '—'}"))

                    if rc == 0:
                        status_text = "✓ Completed successfully"
                        color = "#7ee787"
                    else:
                        status_text = f"✗ Failed (exit code {rc})"
                        color = "#ff7b72"
                    ui_call(lambda: ag_status_label.configure(text=status_text, text_color=color))

            threading.Thread(target=_reader, daemon=True).start()
            
        except Exception as e:
            ui_call(lambda: ag_status_label.configure(text=f"Error: {str(e)}", text_color="#ff7b72"))

    # Start audiog.ps1 after the Tk event loop begins
    try:
        app.after(0, lambda: threading.Thread(target=_start_audiog, daemon=True).start())
    except Exception:
        threading.Thread(target=_start_audiog, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════
    # 2. SYSTEM INFO CARD (embedded module)
    # ══════════════════════════════════════════════════════════════════
    # Create a System Info card that expands vertically and is scrollable
    sys_card = card(body, "🖥️  System Info")
    # Repack the card to allow vertical expansion
    try:
        sys_card.pack_forget()
    except Exception:
        pass
    sys_card.pack(fill="both", expand=True, padx=14, pady=8)

    # Host frame to manage textbox + scrollbar layout
    _sys_host = ctk.CTkFrame(sys_card, fg_color="transparent")
    _sys_host.pack(fill="both", expand=True, padx=12, pady=(6, 12))

    sys_text = ctk.CTkTextbox(_sys_host, wrap="word")
    sys_text.pack(side="left", fill="both", expand=True)
    sys_text.insert("1.0", "Collecting system information...\nThis may take up to a minute.\n")
    sys_text.configure(state="disabled")

    # Vertical scrollbar for long reports
    try:
        vscroll = ctk.CTkScrollbar(_sys_host, orientation="vertical", command=sys_text.yview)
        vscroll.pack(side="right", fill="y")
        sys_text.configure(yscrollcommand=vscroll.set)
    except Exception:
        # Older CTK versions may not provide CTkScrollbar; ignore gracefully
        pass

    # Components checklist (English labels)
    _comp_vars = {}
    try:
        comp_frame = ctk.CTkFrame(sys_card, fg_color="transparent")
        comp_frame.pack(fill="x", padx=14, pady=(6, 6))
        ctk.CTkLabel(
            comp_frame,
            text="Components",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#58a6ff"
        ).pack(anchor="w", padx=2, pady=(0, 6))

        # Use a simple tk.Frame for grid layout of checkboxes
        _comp_grid = tk.Frame(comp_frame, bg="#0d1117")
        _comp_grid.pack(fill="x")

        comp_labels = [
            ("WWAN", "wwan"),
            ("WLAN", "wlan"),
            ("Privacy", "privacy"),
            ("NFC", "nfc"),
            ("Smart Card", "smartcard"),
            ("Backlight", "backlight"),
            ("RGB Keyboard", "rgb_keyboard"),
            ("Fingerprint", "fingerprint"),
        ]

        _comp_vars = {}
        for i, (label_text, key) in enumerate(comp_labels):
            var = tk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(_comp_grid, text=label_text, variable=var)
            cb.grid(row=i // 4, column=i % 4, sticky="w", padx=8, pady=4)
            _comp_vars[key] = var
    except Exception:
        # Fail gracefully if CTk widgets are unavailable
        pass

    def _load_system_info():
        script_path = os.path.join(BASE, "HPLENDELLDEV7.ps1")
        if not os.path.exists(script_path):
            report = f"Error: Script not found at {script_path}"
        else:
            # Stream PowerShell output into the GUI textbox without creating
            # a separate console window. Send a newline to stdin to satisfy
            # any Read-Host calls in the script.
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path]
            creation = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    creationflags=creation,
                )

                # Give the script an initial newline in case it immediately waits
                try:
                    proc.stdin.write("\n")
                    proc.stdin.flush()
                except Exception:
                    pass

                start_time = time.time()
                timeout = 120
                report_lines = []

                def adjust_textbox_rows(tb, min_rows=6, max_rows=80):
                    try:
                        # Get number of lines in the textbox (index like '12.0')
                        line_count = int(str(tb.index('end-1c')).split('.')[0])
                        rows = max(min_rows, min(line_count, max_rows))
                        # CTkTextbox accepts `height` as number of text lines in many versions
                        try:
                            tb.configure(height=rows)
                        except Exception:
                            # fallback: set pixel height approximately
                            tb.configure(height=rows * 18)
                    except Exception:
                        pass

                def filter_line_for_bcu(line):
                    try:
                        if not line:
                            return False
                        low = line.strip().lower()
                        # Common markers to skip
                        if "bcu output" in low or "bcu stdout" in low or "bcu stderr" in low:
                            return True
                        # skip lines that reference bcu output files
                        if "bcu-output" in low or "bcu_stdout" in low or "bcu-stdout" in low:
                            return True
                        # path references ending with bcu-output.txt etc.
                        if "bcu-output.txt" in low or "bcu-stdout.txt" in low or "bcu-stderr.txt" in low:
                            return True
                        return False
                    except Exception:
                        return False

                def _append_line(line):
                    if not line:
                        return
                    # filter BCU-related noise
                    try:
                        if filter_line_for_bcu(line):
                            return
                    except Exception:
                        pass
                    try:
                        sys_text.configure(state="normal")
                        sys_text.insert("end", line)
                        sys_text.see("end")
                        adjust_textbox_rows(sys_text)
                        sys_text.configure(state="disabled")
                    except Exception:
                        pass

                # Read stdout line-by-line and append to textbox
                try:
                    # Skip blocks we don't want to display (e.g., BCU output file lists)
                    skip_bcu_block = False
                    while True:
                        if proc.stdout is None:
                            break
                        line = proc.stdout.readline()
                        if not line:
                            if proc.poll() is not None:
                                break
                            if time.time() - start_time > timeout:
                                try:
                                    proc.kill()
                                except Exception:
                                    pass
                                report_lines.append(f"\nPowerShell timed out after {timeout}s.\n")
                                app.after(0, lambda: _append_line(f"\nPowerShell timed out after {timeout}s.\n"))
                                break
                            time.sleep(0.1)
                            continue

                        # Normalize for matching
                        lstrip = line.strip()
                        low = lstrip.lower()

                        # Start skipping when we encounter the BCU header
                        if "bcu output files" in low:
                            skip_bcu_block = True
                            continue

                        # Skip known BCU lines while in the block
                        if skip_bcu_block:
                            # End block on an empty line or when unrelated section starts
                            if low == "" or low.endswith(":"):
                                skip_bcu_block = False
                                continue
                            # also skip lines that mention bcu output
                            if "bcu output" in low or "bcu stdout" in low or "bcu stderr" in low:
                                continue
                            # otherwise continue skipping
                            continue

                        # Parse the line for component flags and then append it
                        report_lines.append(line)

                        # Update component checkboxes based on known markers
                        try:
                            low_line = lstrip.lower()
                            if _comp_vars:
                                def set_comp(key, value):
                                    try:
                                        var = _comp_vars.get(key)
                                        if var is not None:
                                            app.after(0, lambda v=var, val=value: v.set(val))
                                    except Exception:
                                        pass

                                # mapping of keywords to comp keys
                                keyword_map = {
                                    'wlan': ['wlan', 'wifi', 'wireless'],
                                    'wwan': ['wwan'],
                                    'privacy': ['sureview', 'privacy'],
                                    'nfc': ['nfc'],
                                    'smartcard': ['smart card', 'smartcard', 'smart-card'],
                                    'backlight': ['backlight', 'keyboard backlight'],
                                    'rgb_keyboard': ['rgb keyboard', 'rgb'],
                                    'fingerprint': ['fingerprint', 'finger print']
                                }

                                for comp_key, keys in keyword_map.items():
                                    for k in keys:
                                        if k in low_line:
                                            # decide true/false from nearby tokens
                                            if any(tok in low_line for tok in (' yes', ': yes', 'enabled', 'present', 'true', 'available')):
                                                set_comp(comp_key, True)
                                            elif any(tok in low_line for tok in (' no', ': no', 'disabled', 'not present', 'false', 'unavailable')):
                                                set_comp(comp_key, False)
                                            # once matched one keyword, stop checking variants for this comp
                                            break
                        except Exception:
                            pass

                        app.after(0, lambda ln=line: _append_line(ln))
                        
                except Exception as read_exc:
                    report_lines.append(f"\nException while reading output: {read_exc}\n")
                    app.after(0, lambda: _append_line(f"\nException while reading output: {read_exc}\n"))

                # Capture any remaining stderr
                try:
                    stderr = (proc.stderr.read() if proc.stderr is not None else "") or ""
                    if stderr.strip():
                        # Append stderr lines through the normal append path so filtering applies
                        for ln in stderr.splitlines(True):
                            app.after(0, lambda ln=ln: _append_line(ln))
                except Exception:
                    pass

                # Prepare a final report string for fallback (not used when streaming)
                report = "".join(report_lines) if report_lines else "No output returned from PowerShell script."
            except Exception as e:
                report = f"Error launching PowerShell:\n{e}"

        def _update():
            if active_screen is None or not active_screen.winfo_exists():
                return
            sys_text.configure(state="normal")
            sys_text.delete("1.0", "end")
            sys_text.insert("1.0", report)
            sys_text.configure(state="disabled")

        app.after(0, _update)

    threading.Thread(target=_load_system_info, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════
    # 2. BATTERY CARD
    # ══════════════════════════════════════════════════════════════════
    bat_card = card(body, "🔋  Battery")

    bat_device  = ctk.CTkLabel(bat_card, text="Loading...", font=ctk.CTkFont(size=11), text_color="#9fb3c8")
    bat_device.pack(anchor="w", padx=14)

    bat_level_lbl = ctk.CTkLabel(bat_card, text="--%", font=ctk.CTkFont(size=28, weight="bold"), text_color="#7ee787")
    bat_level_lbl.pack(anchor="w", padx=14, pady=(4,0))

    bat_bar_frame = tk.Frame(bat_card, bg="#161b22")
    bat_bar_frame.pack(anchor="w", padx=14, pady=(4, 8))
    bat_style = ttk.Style()
    bat_style.theme_use("clam")
    bat_style.configure("HW.Horizontal.TProgressbar", thickness=14, troughcolor="#1e2a3a", background="#7ee787")
    bat_bar = ttk.Progressbar(bat_bar_frame, orient="horizontal", length=500,
                               mode="determinate", maximum=100, style="HW.Horizontal.TProgressbar")
    bat_bar.pack()

    bat_row2 = ctk.CTkFrame(bat_card, fg_color="transparent")
    bat_row2.pack(fill="x", padx=14, pady=(0,4))
    bat_health_lbl   = ctk.CTkLabel(bat_row2, text="Health: --",   font=ctk.CTkFont(size=12), text_color="white")
    bat_health_lbl.pack(side="left", padx=(0,20))
    bat_status_lbl   = ctk.CTkLabel(bat_row2, text="Status: --",   font=ctk.CTkFont(size=12), text_color="white")
    bat_status_lbl.pack(side="left", padx=(0,20))
    bat_cycle_lbl    = ctk.CTkLabel(bat_row2, text="Cycles: --",   font=ctk.CTkFont(size=12), text_color="white")
    bat_cycle_lbl.pack(side="left")

    bat_cap_lbl = ctk.CTkLabel(bat_card, text="Capacity: --", font=ctk.CTkFont(size=11), text_color="#9fb3c8")
    bat_cap_lbl.pack(anchor="w", padx=14, pady=(0,10))

    def _bat_refresh():
        try:
            data = _get_battery_data()
            if not data:
                def _apply_no_battery():
                    if not widget_exists(active_screen):
                        return
                    bat_device.configure(text="No battery detected")
                    bat_level_lbl.configure(text="--%", text_color="#ff7b72")
                    bat_bar["value"] = 0
                    bat_health_lbl.configure(text="Health: N/A")
                    bat_status_lbl.configure(text="Status: N/A")
                    bat_cycle_lbl.configure(text="Cycles: N/A")
                    bat_cap_lbl.configure(text="Capacity: N/A")
                ui_call(_apply_no_battery)
                return
            lv = data["level"] if isinstance(data["level"], int) else 0
            color = _level_color(lv)
            def _apply_data():
                if not widget_exists(active_screen):
                    return
                bat_device.configure(text=data["name"])
                bat_level_lbl.configure(text=data["level_text"], text_color=color)
                bat_bar["value"] = lv
                bat_style.configure("HW.Horizontal.TProgressbar", background=color)
                bat_health_lbl.configure(text=f"Health: {data['health_text']}")
                bat_status_lbl.configure(text=f"Status: {data['status_text']}")
                bat_cycle_lbl.configure(text=f"Cycles: {data['cycle_text']}")
                bat_cap_lbl.configure(text=f"Capacity: {data['capacity_text']}")
            ui_call(_apply_data)
        except Exception as e:
            ui_call(lambda: widget_exists(bat_cap_lbl) and bat_cap_lbl.configure(text=str(e)))

    def _bat_auto():
        if active_screen is None or not active_screen.winfo_exists(): return
        threading.Thread(target=_bat_refresh, daemon=True).start()
        _bat_after_id[0] = app.after(5000, _bat_auto)

    threading.Thread(target=_bat_refresh, daemon=True).start()
    _bat_after_id[0] = app.after(5000, _bat_auto)

    # ══════════════════════════════════════════════════════════════════
    # 2. SPEAKER CARD
    # ══════════════════════════════════════════════════════════════════
    spk_card = card(body, "🔊  Speaker Test")
    spk_status = ctk.CTkLabel(spk_card, text="Press Play to test speakers",
                               font=ctk.CTkFont(size=12), text_color="#9fb3c8")
    spk_status.pack(anchor="w", padx=14, pady=(0,6))

    spk_btn_row = ctk.CTkFrame(spk_card, fg_color="transparent")
    spk_btn_row.pack(anchor="w", padx=14, pady=(0,12))

    spk_play_btn = ctk.CTkButton(spk_btn_row, text="▶  Play", width=100, height=30)
    spk_play_btn.pack(side="left", padx=(0,8))
    spk_stop_btn = ctk.CTkButton(spk_btn_row, text="■  Stop", width=100, height=30,
                                  fg_color="#444", hover_color="#555", state="disabled")
    spk_stop_btn.pack(side="left")

    def _spk_on_finished():
        if active_screen is None or not active_screen.winfo_exists(): return
        spk_status.configure(text="Playback finished.")
        spk_play_btn.configure(state="normal")
        spk_stop_btn.configure(state="disabled")

    def _spk_play():
        spk_status.configure(text="Playing ST.WAV...")
        spk_play_btn.configure(state="disabled")
        spk_stop_btn.configure(state="normal")
        start_speaker_playback(_spk_on_finished)

    def _spk_stop():
        stop_speaker_test()
        spk_status.configure(text="Stopped.")
        spk_play_btn.configure(state="normal")
        spk_stop_btn.configure(state="disabled")

    spk_play_btn.configure(command=_spk_play)
    spk_stop_btn.configure(command=_spk_stop)

    # ══════════════════════════════════════════════════════════════════
    # 3. MIC CARD  (live VU meter via PowerShell)
    # ══════════════════════════════════════════════════════════════════
    mic_card = card(body, "🎤  Microphone Test")
    mic_status = ctk.CTkLabel(mic_card, text="Click Start to begin mic test",
                               font=ctk.CTkFont(size=12), text_color="#9fb3c8")
    mic_status.pack(anchor="w", padx=14, pady=(0,6))

    # Embed the full MICTEST1 UI inside this card (non-fullscreen)
    # Allow the embedded mic tester enough room to use its native layout
    mic_embed_host = tk.Frame(mic_card, bg="#101723", height=480)
    # Do not allow the mic embed to expand and push other cards out of view;
    # give it a fixed height and prevent geometry propagation from its children
    mic_embed_host.pack(fill="both", expand=False, padx=14, pady=(6, 10))
    try:
        mic_embed_host.pack_propagate(False)
    except Exception:
        pass

    try:
        mic_tester = MICTEST1.AudioDiagnosticApp(mic_embed_host, menu_callback=lambda: None)
        # ensure the embedded tester doesn't try to navigate away
        mic_tester.set_menu_callback(lambda: None)
        try:
            mic_embed_host.focus_set()
        except Exception:
            pass

        # Style the embedded ttk Progressbar (mic meter) with a green foreground
        try:
            meter_style = ttk.Style()
            # use clam theme for consistent styling if available
            try:
                meter_style.theme_use('clam')
            except Exception:
                pass
            meter_style.configure('Green.Horizontal.TProgressbar', troughcolor='#1e2a3a', background='#7ee787', thickness=14)
            # apply style if the embedded tester exposed `meter`
            if hasattr(mic_tester, 'meter'):
                try:
                    mic_tester.meter.configure(style='Green.Horizontal.TProgressbar')
                except Exception:
                    pass
        except Exception:
            pass
    except Exception as exc:
        # Fallback to placeholder if embedding fails
        mic_btn_row = ctk.CTkFrame(mic_card, fg_color="transparent")
        mic_btn_row.pack(anchor="w", padx=14, pady=(0,12))
        ctk.CTkButton(
            mic_btn_row,
            text="Mic Test Is Included Here",
            width=200,
            height=30,
            state="disabled",
        ).pack(side="left")

        mic_note = ctk.CTkLabel(
            mic_card,
            text=f"Could not load embedded mic test: {exc}",
            font=ctk.CTkFont(size=10),
            text_color="#ff7b72",
        )
        mic_note.pack(anchor="w", padx=14, pady=(6,10))

    # ══════════════════════════════════════════════════════════════════
    # 4. CAMERA CARD
    # ══════════════════════════════════════════════════════════════════
    # Insert Touchpad Test card before Camera Test
    tp_card = card(body, "🖱️  Touchpad Test")
    tp_status = ctk.CTkLabel(tp_card, text="Click Start to begin touchpad test",
                              font=ctk.CTkFont(size=12), text_color="#9fb3c8")
    tp_status.pack(anchor="w", padx=14, pady=(0,6))

    tp_btn_row = ctk.CTkFrame(tp_card, fg_color="transparent")
    tp_btn_row.pack(anchor="w", padx=14, pady=(0,8))
    tp_start_btn = ctk.CTkButton(tp_btn_row, text="Start", width=140, height=30)
    tp_start_btn.pack(side="left")

    # placeholder for embedded widgets
    tp_host = tk.Frame(tp_card, bg="#0d1117")
    tp_host.pack(fill="both", expand=True, padx=14, pady=(6,10))

    def _embed_touchpad():
        for w in tp_host.winfo_children():
            w.destroy()

        # Click area
        emb_click = tk.Canvas(tp_host, bg="#0b1220", height=80, highlightthickness=1)
        emb_click.pack(fill="x", pady=(0,6))
        emb_click.create_text(140, 40, text="Click here — Left & Right", fill="#a6adc8")

        emb_lbl_frame = tk.Frame(tp_host, bg="#0d1117")
        emb_lbl_frame.pack(fill="x")
        emb_l_lbl = tk.Label(emb_lbl_frame, text="L: 0/10", bg="#0d1117", fg="#cdd6f4")
        emb_l_lbl.pack(side="left", padx=6)
        emb_r_lbl = tk.Label(emb_lbl_frame, text="R: 0/10", bg="#0d1117", fg="#cdd6f4")
        emb_r_lbl.pack(side="left", padx=6)

        emb_click_count = {"l":0, "r":0}

        def _emb_lclick(_e):
            if emb_click_count["l"] < 10:
                emb_click_count["l"] += 1
                emb_l_lbl.config(text=f"L: {emb_click_count['l']}/10")
        def _emb_rclick(_e):
            if emb_click_count["r"] < 10:
                emb_click_count["r"] += 1
                emb_r_lbl.config(text=f"R: {emb_click_count['r']}/10")

        emb_click.bind("<Button-1>", _emb_lclick)
        emb_click.bind("<Button-3>", _emb_rclick)

        # Drag area (small version)
        emb_dc = tk.Canvas(tp_host, bg="#0b1220", height=220, highlightthickness=1)
        emb_dc.pack(fill="both", pady=(6,4))

        # build 3x2 targets
        W, H = 560, 200
        BW, BH = 160, 80
        cols, rows = 3, 2
        gx = (W - cols * BW) // (cols + 1)
        gy = (H - rows * BH) // (rows + 1)

            

    # KEYBOARD CARD (was missing) — create the card container
    kb_card = card(body, "⌨️  Keyboard Test")
    kb_status = ctk.CTkLabel(kb_card, text="Press keys to test keyboard",
                              font=ctk.CTkFont(size=12), text_color="#9fb3c8")
    kb_status.pack(anchor="w", padx=14, pady=(0,6))

    kb_btn_row = ctk.CTkFrame(kb_card, fg_color="transparent")
    kb_btn_row.pack(anchor="w", padx=14, pady=(0,8))

    kb_embed_host = tk.Frame(kb_card, bg="#101723", height=720)
    kb_embed_host.pack(fill="both", expand=True, padx=14, pady=(0, 10))
    kb_embed_host.pack_propagate(False)

    try:
        kb_tester = KeyboardTesterGUI2.KeyboardTesterApp(kb_embed_host)
        kb_tester.set_menu_callback(lambda: None)
        try:
            kb_embed_host.focus_set()
        except Exception:
            pass

        def _forward_keypress(event):
            try:
                kb_tester._handle_physical_keypress(event)
            except Exception:
                pass

        _kb_bind_id[0] = app.bind("<KeyPress>", _forward_keypress, add="+")
    except Exception as exc:
        ctk.CTkLabel(
            kb_embed_host,
            text=f"Could not load keyboard tester: {exc}",
            text_color="#ff7b72",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(pady=14)

    # Bottom padding
    # ══════════════════════════════════════════════════════════════════
    # ACTIVATION CARD (added)
    # ══════════════════════════════════════════════════════════════════
    # ACTIVATION CARD
    # ══════════════════════════════════════════════════════════════════
    act_card = card(body, "🔐  Activation")
    act_label = ctk.CTkLabel(
        act_card,
        text="Activation Check",
        font=ctk.CTkFont(size=12),
        text_color="#9fb3c8",
    )
    act_label.pack(anchor="w", padx=14, pady=(0, 10))

    # Status label for activation result
    act_result_label = ctk.CTkLabel(act_card, text="Checking...", font=ctk.CTkFont(size=13), text_color="#9fb3c8", justify="left")
    act_result_label.pack(anchor="w", padx=14, pady=(0, 10))

    def _load_activation_status():
        try:
            ps_cmd = (
                "$data = Get-CimInstance -ClassName SoftwareLicensingProduct -Filter \"Name like 'Windows%'\" | "
                "Where-Object { $_.PartialProductKey -and $_.LicenseStatus -ne $null } | Select-Object -First 1; "
                "if ($data -and $data.LicenseStatus -eq 1) { Write-Output 'Activated' } "
                "else { Write-Output 'NotActivated' }"
            )
            out = run_powershell(ps_cmd).strip()
        except Exception as e:
            out = f"Error: {e}"

        try:
            app.after(0, lambda: _display_activation(out))
        except Exception:
            _display_activation(out)

    def _display_activation(status):
        try:
            if "Activated" in status and "NotActivated" not in status:
                result_text = "✓ Windows is Activated"
                color = "#7ee787"
            else:
                result_text = "✗ Windows is not Activated"
                color = "#ff7b72"
            app.after(0, lambda: act_result_label.configure(text=result_text, text_color=color))
        except Exception:
            pass

    threading.Thread(target=_load_activation_status, daemon=True).start()

    # Bottom padding
    # ══════════════════════════════════════════════════════════════════
    # VIRUS SCAN CARD (runs windef.ps1 with live output)
    # ══════════════════════════════════════════════════════════════════
    vs_card = card(body, "🦠  Virus Scan")
    vs_status = ctk.CTkLabel(vs_card, text="Starting Virus Scan...", font=ctk.CTkFont(size=12), text_color="#9fb3c8")
    vs_status.pack(anchor="w", padx=14, pady=(0, 10))

    # Live output frame for displaying results
    vs_results_frame = ctk.CTkFrame(vs_card, fg_color="transparent")
    vs_results_frame.pack(fill="both", expand=False, padx=14, pady=(0, 10))
    
    # Dynamic labels for output
    vs_output_labels = []

    def _add_vs_output_line(line):
        try:
            # Create a new label for each line
            lbl = ctk.CTkLabel(vs_results_frame, text=line.strip(), font=ctk.CTkFont(size=10), text_color="#d4af37", justify="left", wraplength=600)
            lbl.pack(anchor="w", pady=2)
            vs_output_labels.append(lbl)
            
            # Keep only last 15 lines visible
            if len(vs_output_labels) > 15:
                old_lbl = vs_output_labels.pop(0)
                old_lbl.destroy()
        except Exception:
            pass

    def _start_windef():
        script_path = os.path.join(BASE, "windef.ps1")
        if not os.path.exists(script_path):
            app.after(0, lambda: _add_vs_output_line(f"Error: Script not found: {script_path}"))
            app.after(0, lambda: vs_status.configure(text="windef.ps1 not found", text_color="#ff7b72"))
            return

        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path]
        creation = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                creationflags=creation,
            )
            ui_call(lambda: vs_status.configure(text=f"Scanning (PID {proc.pid})...", text_color="#7ee787"))

            def _reader():
                try:
                    while True:
                        if proc.stdout is None:
                            break
                        line = proc.stdout.readline()
                        if not line:
                            if proc.poll() is not None:
                                break
                            time.sleep(0.1)
                            continue
                        ui_call(_add_vs_output_line, line)
                    
                    try:
                        stderr = (proc.stderr.read() if proc.stderr else "") or ""
                        if stderr.strip():
                            for ln in stderr.splitlines(True):
                                ui_call(_add_vs_output_line, f"[Error] {ln}")
                    except Exception:
                        pass
                finally:
                    rc = proc.poll() or 0
                    if rc == 0:
                        status_text = "✓ Scan completed"
                        color = "#7ee787"
                    else:
                        status_text = f"✗ Scan failed (exit code {rc})"
                        color = "#ff7b72"
                    ui_call(lambda: vs_status.configure(text=status_text, text_color=color))

            threading.Thread(target=_reader, daemon=True).start()
        except Exception as e:
            app.after(0, lambda: _add_vs_output_line(f"Error launching windef.ps1: {e}"))
            app.after(0, lambda: vs_status.configure(text="Error starting script", text_color="#ff7b72"))

    threading.Thread(target=_start_windef, daemon=True).start()

    ctk.CTkLabel(body, text="", height=16).pack()


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


# ------------------------------------------------------------------
# Start app
# ------------------------------------------------------------------
# Schedule showing the hardware screen after the Tk main loop starts
# so background threads can safely use `app.after`.
app.after(0, show_hardware_test_screen)
app.mainloop()
