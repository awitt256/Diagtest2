import customtkinter as ctk
import tkinter as tk
import os
import sys
import ctypes
import json
import subprocess
import threading
import time
from tkinter import messagebox, ttk
from PIL import Image
import tempfile
import winsound

# banner image placeholder (unused)


# ✅ Catch crashes so the window doesn't close silently
import traceback
def excepthook(exc_type, exc_value, exc_tb):
    traceback.print_exception(exc_type, exc_value, exc_tb)
    input("Press ENTER to exit...")
sys.excepthook = excepthook

# ✅ Import embedded keyboard tester (full-featured)
import importlib.util as _importlib_util
import os as _os
_kb2_path = _os.path.join(_os.path.dirname(__file__), "keyboard_gui3.py")
_spec = _importlib_util.spec_from_file_location("keyboard_gui3", _kb2_path)
KeyboardGUI2 = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(KeyboardGUI2)

# Ensure venv site-packages is in sys.path for MICTEST1 module loading
_venv_site_packages = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), ".venv", "Lib", "site-packages")
if _venv_site_packages not in sys.path:
    sys.path.insert(0, _venv_site_packages)

_mic_path = _os.path.join(_os.path.dirname(__file__), "MicrophoneTesterGUI.py")
_mic_spec = _importlib_util.spec_from_file_location("MicrophoneTesterGUI", _mic_path)
MicrophoneTesterGUI = _importlib_util.module_from_spec(_mic_spec)
try:
    _mic_spec.loader.exec_module(MicrophoneTesterGUI)
except Exception:
    # Leave graceful fallback to existing MICTEST1 if available
    try:
        _mic_path = _os.path.join(_os.path.dirname(__file__), "MICTEST1.py")
        _mic_spec = _importlib_util.spec_from_file_location("MICTEST1", _mic_path)
        MICTEST1 = _importlib_util.module_from_spec(_mic_spec)
        _mic_spec.loader.exec_module(MICTEST1)
    except Exception:
        MicrophoneTesterGUI = None


# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BASE = os.path.dirname(os.path.abspath(__file__))
SEQUENCE_LOG = os.path.join(tempfile.gettempdir(), "mywintest36_sequence.log")


def _log_sequence(message):
    try:
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(SEQUENCE_LOG, "a", encoding="utf-8") as fh:
            fh.write(f"{stamp} {message}\n")
    except Exception:
        pass


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
app.title("Diagnostics Test Tool V 0.36 (Modern UI)")
app.geometry("850x700")
try:
    # Start the main window maximized on Windows (zoomed) where available
    app.state('zoomed')
except Exception:
    try:
        app.attributes("-zoomed", True)
    except Exception:
        pass

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
_camera_captures = []
_camera_after_id = None
_camera_index = 0


# Main menu containers removed (app now starts directly into Hardware Test Suite)


# ------------------------------------------------------------------
def clear_screen():
    """Tear down the current active screen and stop any background tests."""
    global active_screen
    try:
        stop_speaker_test()
    except Exception:
        pass
    try:
        stop_camera_preview()
    except Exception:
        pass
    if active_screen is not None:
        try:
            active_screen.destroy()
        except Exception:
            pass
        active_screen = None



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
    # If winsound was used for async playback, explicitly stop it
    try:
        if _speaker_backend == "winsound":
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                try:
                    # Fallback: stop any async playback
                    winsound.PlaySound(None, winsound.SND_ASYNC)
                except Exception:
                    pass
    except Exception:
        pass
    _speaker_backend = None


def start_speaker_playback(on_finished, loop=False):
    """Play st.wav once (loop=False) or seamlessly loop until stop_speaker_test() is called (loop=True).

    When loop=True the winsound backend uses SND_LOOP|SND_ASYNC which lets Windows
    restart the WAV file the instant it ends — no gap, no Python timer involved.
    on_finished is NOT called while looping; it is only called after a single
    non-looping play completes.
    """
    global _speaker_after_id, _speaker_process, _speaker_backend
    stop_speaker_test()
    mp3_path = os.path.join(BASE, "st.wav")
    if not os.path.exists(mp3_path):
        messagebox.showwarning("Missing File", f"Cannot find:\n{mp3_path}")
        return False
    try:
        if loop:
            # SND_LOOP requires SND_ASYNC; Windows handles the seamless repeat internally
            winsound.PlaySound(mp3_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
        else:
            winsound.PlaySound(mp3_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        _speaker_backend = "winsound"
    except Exception as winsound_exc:
        try:
            escaped_path = mp3_path.replace("'", "''")
            if loop:
                # PowerShell fallback: loop via a while-true that restarts MediaPlayer each iteration
                ps_script = (
                    "Add-Type -AssemblyName PresentationCore; "
                    f"$uri = [System.Uri]::new('{escaped_path}'); "
                    "$player = New-Object System.Windows.Media.MediaPlayer; "
                    "$player.Open($uri); "
                    "while ($true) { "
                    "  $player.Position = [TimeSpan]::Zero; "
                    "  $player.Play(); "
                    "  $done = $false; "
                    "  $player.add_MediaEnded({ $script:done = $true }); "
                    "  while (-not $done) { Start-Sleep -Milliseconds 50 }; "
                    "  $player.remove_MediaEnded({ $script:done = $true }); "
                    "}; "
                    "$player.Close();"
                )
            else:
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

    # When looping with winsound, Windows drives the repeat — nothing to poll.
    if loop and _speaker_backend == "winsound":
        return True

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




# legacy helper `run_cmd`/`run_tool` removed (not used by hardware screen)

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


def ui_call_wait(callback, timeout=2.0):
    """Run a Tk read on the main thread and wait briefly for the result."""
    done = threading.Event()
    result = {"value": None, "error": None}

    def _runner():
        try:
            result["value"] = callback()
        except Exception as exc:
            result["error"] = exc
        finally:
            done.set()

    try:
        if not app.winfo_exists():
            return None
        app.after(0, _runner)
    except Exception:
        return None

    if not done.wait(timeout):
        return None
    if result["error"] is not None:
        raise result["error"]
    return result["value"]


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




# ------------------------------------------------------------------
# Combined Hardware Test Screen
# ------------------------------------------------------------------
def show_hardware_test_screen():
    global active_screen, _camera_captures, _camera_after_id
    clear_screen()
    try:
        # Give the embedded keyboard tester enough room to avoid clipping.
        app.geometry("1460x900")
    except Exception:
        pass

    _bat_after_id = [None]
    _cam_after_local = [None]
    _cam_caps_local = []
    _kb_bind_id = [None]
    _scroll_bind_ids = {}

    active_screen = ctk.CTkFrame(app, fg_color="#0d1117")
    active_screen.pack(fill="both", expand=True)

    # Real-time status tracking for sidebar
    status_indicators = {}
    def update_sidebar_status(key, status):
        """status can be 'pass', 'fail', or 'none'"""
        ind = status_indicators.get(key)
        if not ind: return
        if status == 'pass':
            ind.configure(text="✔", text_color="#7ee787") # Green check
        elif status == 'fail':
            ind.configure(text="✖", text_color="#ff7b72") # Red X
        else:
            ind.configure(text="○", text_color="#9aa4b2") # Neutral circle
    try:
        # Ensure hardware screen is on top of the main menu
        active_screen.lift()
    except Exception:
        pass

    # ── Top bar ──────────────────────────────────────────────────────
    top_bar = ctk.CTkFrame(active_screen, fg_color="#1f2a44", corner_radius=0, height=46)
    top_bar.pack(fill="x", side="top")
    top_bar.pack_propagate(False)
    ctk.CTkLabel(
        top_bar,
        text="Hardware Test Suite — Revision 0.36: Added Sequencer And Minor Tweaks",
        font=ctk.CTkFont(size=18, weight="bold"),
        text_color="#f5d76e",
    ).pack(side="left", padx=18, pady=8)
    # Run full sequence button
    _sequence_running = [False]
    _sequence_run_id = [0]
    seq_btn = None

    def _set_sequence_button_idle():
        try:
            if seq_btn is not None:
                seq_btn.configure(text="Run Sequence", state="normal")
        except Exception:
            pass

    def _set_sequence_button_running():
        try:
            if seq_btn is not None:
                seq_btn.configure(text="Running...", state="disabled")
        except Exception:
            pass

    def _cancel_sequence():
        _sequence_run_id[0] += 1
        _sequence_running[0] = False
        _log_sequence("sequence cancelled")
        _set_sequence_button_idle()

    def _start_new_sequence(start_key=None):
        _sequence_run_id[0] += 1
        run_id = _sequence_run_id[0]
        _sequence_running[0] = True
        _set_sequence_button_running()
        threading.Thread(target=_run_full_sequence, args=(start_key, run_id), daemon=True).start()

    def _toggle_sequence():
        if _sequence_running[0]:
            return
        _start_new_sequence()

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
        for sequence, bind_id in list(_scroll_bind_ids.items()):
            try:
                app.unbind(sequence, bind_id)
            except Exception:
                pass
        _scroll_bind_ids.clear()
        stop_speaker_test()
        return_to_main_menu()

    def scroll_to_widget(widget):
        try:
            app.update_idletasks()

            # Confirmed via runtime inspection:
            # - Canvas is body._parent_canvas
            # - Widgets are direct children of body (the CTkScrollableFrame)
            # - There is no _scrollable_label on this version of customtkinter

            canvas = getattr(body, "_parent_canvas", None)
            if not canvas:
                return

            # Get the absolute Y position of the target widget and the canvas content start
            widget_abs_y = widget.winfo_rooty()
            canvas_abs_y = body.winfo_rooty()

            # Relative position of widget inside the scrollable area
            relative_y = widget_abs_y - canvas_abs_y

            # Total scrollable height from canvas bounding box
            bbox = canvas.bbox("all")
            if not bbox:
                return

            total_h = bbox[3] - bbox[1]
            if total_h <= 0:
                return

            fraction = relative_y / total_h
            fraction = max(0.0, min(1.0, fraction))
            canvas.yview_moveto(fraction)
        except Exception:
            pass


    # ── Main Content Container (Body + Sidebar) ─────────────────────
    main_container = ctk.CTkFrame(active_screen, fg_color="transparent")
    main_container.pack(fill="both", expand=True)

    sidebar = ctk.CTkFrame(main_container, width=220, fg_color="#161b22", corner_radius=0,
                           border_width=1, border_color="#30363d")
    sidebar.pack(side="right", fill="y", padx=(1, 0))
    sidebar.pack_propagate(False)

    # Sidebar header row: "Test Summary" + global refresh button
    _sb_header = ctk.CTkFrame(sidebar, fg_color="transparent")
    _sb_header.pack(fill="x", padx=10, pady=(20, 4))
    ctk.CTkLabel(_sb_header, text="Test Summary",
                 font=ctk.CTkFont(size=16, weight="bold"),
                 text_color="#58a6ff").pack(side="left", padx=(6, 0))
    _global_refresh_btn = ctk.CTkButton(
        _sb_header,
        text="⟳",
        width=30,
        height=30,
        fg_color="#1f3a5f",
        hover_color="#2a5298",
        corner_radius=8,
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color="#58a6ff",
        command=lambda: _do_global_refresh(),
    )
    _global_refresh_btn.pack(side="right", padx=(0, 4))
    _refresh_running = [False]
    
    def add_sidebar_item(key, display_name, target_widget):
        row = ctk.CTkFrame(sidebar, fg_color="transparent", cursor="hand2")
        row.pack(fill="x", padx=10, pady=2)
        
        # Circle indicator
        ind = ctk.CTkLabel(row, text="○", font=ctk.CTkFont(size=18, weight="bold"), text_color="#9aa4b2")
        ind.pack(side="left", padx=(5, 10))
        status_indicators[key] = ind
        
        # Name label
        lbl = ctk.CTkLabel(row, text=display_name, font=ctk.CTkFont(size=12), text_color="#c9d1d9")
        lbl.pack(side="left")

        # Hover effects
        def on_enter(e): row.configure(fg_color="#1f242c")
        def on_leave(e): row.configure(fg_color="transparent")
        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)

        # Click to scroll
        def on_click(e):
            if target_widget:
                # Add a tiny delay to ensure focus and layout are ready
                app.after(10, lambda: scroll_to_widget(target_widget))
        
        row.bind("<Button-1>", on_click)
        ind.bind("<Button-1>", on_click)
        lbl.bind("<Button-1>", on_click)

    # Submit button for the Test Summary (bottom of sidebar)
    def _submit_results():
        try:
            # Gather a simple summary of sidebar statuses
            summary = {}
            for k, lbl in status_indicators.items():
                try:
                    text = (lbl.cget('text') or '').strip()
                except Exception:
                    text = ''
                summary[k] = text
            # Log and show confirmation
            _log_sequence(f"results submitted: {json.dumps(summary)}")
            try:
                messagebox.showinfo("Submit", "Test results submitted.")
            except Exception:
                pass
            # disable after submit to avoid duplicates
            try:
                submit_btn.configure(state="disabled", text="Submitted ✔")
            except Exception:
                pass
        except Exception:
            try:
                messagebox.showerror("Submit", "Failed to submit results.")
            except Exception:
                pass

    submit_btn = ctk.CTkButton(
        sidebar,
        text="Submit  ✔",
        width=200,
        height=36,
        fg_color="#1f6e3a",
        hover_color="#2a8f4a",
        corner_radius=10,
        font=ctk.CTkFont(size=12, weight="bold"),
        command=_submit_results,
    )
    submit_btn.pack(side="bottom", pady=16, padx=14)

    # ── Scrollable body (Left) ────────────────────────────────────────
    body = ctk.CTkScrollableFrame(main_container, fg_color="#0d1117")
    body.pack(side="left", fill="both", expand=True, padx=0, pady=0)
    try:
        body._scrollbar.grid_remove()
    except Exception:
        pass

    def _is_text_input_widget(widget):
        current = widget
        while current is not None:
            try:
                class_name = str(current.winfo_class()).lower()
            except Exception:
                class_name = ""
            if any(name in class_name for name in ("text", "entry", "listbox", "treeview", "combobox", "spinbox")):
                return True
            current = getattr(current, "master", None)
        return False

    _scroll_speed_multiplier = 36

    def _scroll_hardware_body(step_count):
        try:
            canvas = getattr(body, "_parent_canvas", None)
            if canvas is not None and canvas.winfo_exists():
                canvas.yview_scroll(step_count, "units")
        except Exception:
            pass

    def _on_hardware_mousewheel(event):
        if active_screen is None or not active_screen.winfo_exists():
            return
        if _is_text_input_widget(getattr(event, "widget", None)):
            return

        delta = getattr(event, "delta", 0)
        if delta == 0:
            return "break"

        steps = max(1, abs(int(delta)) // 120) * _scroll_speed_multiplier
        direction = -1 if delta > 0 else 1
        _scroll_hardware_body(direction * steps)
        return "break"

    def _on_hardware_button_scroll(event):
        if active_screen is None or not active_screen.winfo_exists():
            return
        if _is_text_input_widget(getattr(event, "widget", None)):
            return

        num = getattr(event, "num", None)
        if num == 4:
            _scroll_hardware_body(-_scroll_speed_multiplier)
        elif num == 5:
            _scroll_hardware_body(_scroll_speed_multiplier)
        return "break"

    try:
        _scroll_bind_ids["<MouseWheel>"] = app.bind("<MouseWheel>", _on_hardware_mousewheel, add="+")
        _scroll_bind_ids["<Button-4>"] = app.bind("<Button-4>", _on_hardware_button_scroll, add="+")
        _scroll_bind_ids["<Button-5>"] = app.bind("<Button-5>", _on_hardware_button_scroll, add="+")
    except Exception:
        pass

    def card(parent, title, track_key=None):
        f = ctk.CTkFrame(parent, fg_color="#161b22", corner_radius=10,
                         border_width=1, border_color="#30363d")
        # default: card fills horizontally only; callers may override to expand
        f.pack(fill="x", padx=14, pady=8)
        ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#58a6ff").pack(anchor="w", padx=14, pady=(10, 6))
        # Status area at bottom of every card: interactive PASS and FAIL
        try:
            # Use CTkFrame for the status area so CTk widgets inside it render correctly
            status_frame = ctk.CTkFrame(f, fg_color="#161b22", corner_radius=0)
            status_frame.pack(side="bottom", fill="x", padx=14, pady=(6, 10))

            # Status display (shows NOT RUN / PASS / FAIL with color + icon)
            status_display = ctk.CTkLabel(status_frame, text="NOT RUN",
                                           font=ctk.CTkFont(size=11, weight="bold"),
                                           text_color="#9aa4b2")
            status_display.pack(side="right", padx=(6, 12))

            # Colors for active/inactive button states
            _pass_active = "#2ecc71"
            _fail_active = "#ff6b6b"
            _btn_inactive = "#2f3338"

            def set_pass():
                try:
                    status_display.configure(text="PASS  ✔", text_color=_pass_active)
                    pass_btn.configure(fg_color=_pass_active)
                    fail_btn.configure(fg_color=_btn_inactive)
                    try:
                        f._last_status_time = time.time()
                    except Exception:
                        pass
                    if track_key: update_sidebar_status(track_key, 'pass')
                except Exception:
                    pass

            def set_fail():
                try:
                    status_display.configure(text="FAIL  ✖", text_color=_fail_active)
                    fail_btn.configure(fg_color=_fail_active)
                    pass_btn.configure(fg_color=_btn_inactive)
                    try:
                        f._last_status_time = time.time()
                    except Exception:
                        pass
                    if track_key: update_sidebar_status(track_key, 'fail')
                except Exception:
                    pass

            # Icon-style circular buttons to mark PASS / FAIL (matches screenshot)
            pass_btn = ctk.CTkButton(
                status_frame,
                text="✔",
                width=34,
                height=34,
                fg_color=_btn_inactive,
                hover_color="#28b463",
                corner_radius=18,
                font=ctk.CTkFont(size=14, weight="bold"),
                command=set_pass,
                text_color="white",
            )
            pass_btn.pack(side="right", padx=(6, 4))

            fail_btn = ctk.CTkButton(
                status_frame,
                text="✖",
                width=34,
                height=34,
                fg_color=_btn_inactive,
                hover_color="#ff5252",
                corner_radius=18,
                font=ctk.CTkFont(size=14, weight="bold"),
                command=set_fail,
                text_color="white",
            )
            fail_btn.pack(side="right", padx=(6, 4))

            # Expose helpers on the card frame for programmatic control
            try:
                f.set_pass = set_pass
                f.set_fail = set_fail
                f.status_display = status_display
                f.pass_btn = pass_btn
                f.fail_btn = fail_btn
                f.track_key = track_key
            except Exception:
                pass
        except Exception:
            # If something goes wrong creating status area, ignore and continue
            pass
        return f

    # ══════════════════════════════════════════════════════════════════
    # 1. AUDIOG RUNNER CARD (runs audiog.ps1 with result display)
    # ══════════════════════════════════════════════════════════════════
    ag_card = card(body, "🔈  Audio Changer", track_key="ag")
    # Replace default title with a header row that includes a small refresh icon (Drivers-style)
    try:
        try:
            first_child = ag_card.winfo_children()[0]
            try:
                first_child.destroy()
            except Exception:
                pass
        except Exception:
            pass
        header_row = ctk.CTkFrame(ag_card, fg_color="transparent")
        header_row.pack(fill="x", padx=14, pady=(10,6))
        ctk.CTkLabel(header_row, text="🔈  Audio Changer", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff").pack(side="left")
        try:
            ctk.CTkButton(header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=_run_audiog_clicked).pack(side="right")
        except Exception:
            pass
    except Exception:
        pass

    ag_status_label = ctk.CTkLabel(ag_card, text="Running audio configuration...", font=ctk.CTkFont(size=12), text_color="#9fb3c8")
    ag_status_label.pack(anchor="w", padx=14, pady=(0, 10))

    ag_btn_row = ctk.CTkFrame(ag_card, fg_color="transparent")
    ag_btn_row.pack(anchor="w", padx=14, pady=(0, 8))
    ag_is_running = [False]
    # Current highlighted card (outline when active)
    _current_highlight = [None]
    _default_border_color = "#30363d"
    _highlight_color = "#7ee787"

    def _clear_highlight():
        try:
            cur = _current_highlight[0]
            if cur is not None and widget_exists(cur):
                try:
                    cur.configure(border_color=_default_border_color, border_width=1)
                except Exception:
                    pass
            _current_highlight[0] = None
        except Exception:
            pass

    def _highlight_and_show(card, color=None):
        try:
            if color is None:
                color = _highlight_color
            # clear previous
            try:
                prev = _current_highlight[0]
                if prev is not None and prev is not card and widget_exists(prev):
                    try:
                        prev.configure(border_color=_default_border_color, border_width=1)
                    except Exception:
                        pass
            except Exception:
                pass

            # apply highlight
            try:
                if widget_exists(card):
                    try:
                        card.configure(border_color=color, border_width=3)
                    except Exception:
                        pass
                    try:
                        card.lift()
                    except Exception:
                        pass
                    # scroll into view if possible
                    try:
                        scroll_to_widget(card)
                    except Exception:
                        pass
                    _current_highlight[0] = card
            except Exception:
                pass
        except Exception:
            pass
    
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
    # Removed summary labels (Current Device / Switched To / Input Device)
    # to keep the Audio Changer output contained in the dynamic results frame.

    def _start_audiog():
        if ag_is_running[0]:
            return
        ag_is_running[0] = True
        script_path = os.path.join(BASE, "audiog.ps1")
        if not os.path.exists(script_path):
            ui_call(lambda: ag_status_label.configure(text="audiog.ps1 not found", text_color="#ff7b72"))
            ag_is_running[0] = False
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
            # highlight audio card when starting
            try:
                ui_call(lambda: _highlight_and_show(ag_card))
            except Exception:
                pass
            
            def _reader():
                try:
                    # Read combined stdout+stderr and append every line to the results frame
                    while True:
                        if proc.stdout is None:
                            break
                        line = proc.stdout.readline()
                        if not line:
                            if proc.poll() is not None:
                                break
                            time.sleep(0.1)
                            continue

                        ui_call(_add_ag_line, line)
                finally:
                    rc = proc.poll() or 0
                    if rc == 0:
                        status_text = "✓ Completed successfully"
                        color = "#7ee787"
                    else:
                        status_text = f"✗ Failed (exit code {rc})"
                        color = "#ff7b72"
                    ui_call(lambda: ag_status_label.configure(text=status_text, text_color=color))
                    # Also update the Audio Changer card status buttons automatically
                    try:
                        if rc == 0:
                            ui_call(lambda: hasattr(ag_card, 'set_pass') and ag_card.set_pass())
                        else:
                            ui_call(lambda: hasattr(ag_card, 'set_fail') and ag_card.set_fail())
                    except Exception:
                        pass
                    # After audio completes, jump to System Info and highlight it
                    try:
                        ui_call(lambda: _highlight_and_show(sys_card))
                        ui_call(_start_system_info_once)
                    except Exception:
                        pass
                    ag_is_running[0] = False

            threading.Thread(target=_reader, daemon=True).start()
            
        except Exception as e:
            ui_call(lambda: ag_status_label.configure(text=f"Error: {str(e)}", text_color="#ff7b72"))
            ag_is_running[0] = False

    def _run_audiog_clicked():
        if ag_is_running[0]:
            return
        try:
            for lbl in list(ag_output_labels):
                try:
                    lbl.destroy()
                except Exception:
                    pass
            ag_output_labels.clear()
        except Exception:
            pass
        threading.Thread(target=_start_audiog, daemon=True).start()

    # Run button removed; use header ⟳ to trigger audio changer

    # Start audiog.ps1 after the Tk event loop begins
    try:
        app.after(0, lambda: threading.Thread(target=_start_audiog, daemon=True).start())
    except Exception:
        threading.Thread(target=_start_audiog, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════
    # 2. SYSTEM INFO CARD (embedded module)
    # ══════════════════════════════════════════════════════════════════
    # Create a System Info card that expands vertically and is scrollable
    sys_card = card(body, "🖥️  System Info", track_key="sys")
    # Replace default title with Drivers-style header + refresh icon
    try:
        try:
            first_child = sys_card.winfo_children()[0]
            try:
                first_child.destroy()
            except Exception:
                pass
        except Exception:
            pass
        header_row = ctk.CTkFrame(sys_card, fg_color="transparent")
        header_row.pack(fill="x", padx=14, pady=(10,6))
        ctk.CTkLabel(header_row, text="🖥️  System Info", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff").pack(side="left")
        try:
            ctk.CTkButton(header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=_start_system_info_once).pack(side="right")
        except Exception:
            pass
    except Exception:
        pass
    # Repack the card to allow vertical expansion
    try:
        sys_card.pack_forget()
    except Exception:
        pass
    sys_card.pack(fill="both", expand=True, padx=14, pady=8)

    # Host frame to manage multiline results area (Drivers-style output)
    _sys_host = ctk.CTkFrame(sys_card, fg_color="transparent")
    _sys_host.pack(fill="both", expand=True, padx=12, pady=(6, 12))

    sys_output_frame = ctk.CTkFrame(_sys_host, fg_color="transparent")
    sys_output_frame.pack(fill="both", expand=True)
    sys_output_labels = []

    sys_btn_row = ctk.CTkFrame(sys_card, fg_color="transparent")
    sys_btn_row.pack(anchor="w", padx=14, pady=(0, 8))

    def _append_sys_line(line):
        try:
            # Only show the requested System Info fields: Serial, SKU, Model, BIOS Password
            try:
                low = str(line).lower()
            except Exception:
                low = ""
            # Keep requested System Info fields plus CPU/GPU/Memory identifiers.
            # Exclude System Name explicitly.
            if "system name" in low:
                return
            allowed_keywords = (
                "system serial",
                "system sku",
                "system model",
                "bios password",
                # Computrace
                "computrace",
                # CPU identifiers
                "cpu",
                "processor",
                "core",
                "intel",
                "amd",
                "ryzen",
                # GPU identifiers
                "gpu",
                "graphics",
                "video memory",
                # Memory identifiers
                "memory",
                "size:",
                "name:",
                # Hard Drive / Disk identifiers
                "hard drive",
                "hard disk",
                "disk",
                "drive",
                "ssd",
                "hdd",
                "nvme",
                "model:",
                "storage",
            )
            if not any(k in low for k in allowed_keywords):
                return

            lbl = ctk.CTkLabel(sys_output_frame, text=line.rstrip(), font=ctk.CTkFont(size=10), text_color="#d4af37", justify="left", wraplength=800)
            lbl.pack(anchor="w", pady=2)
            sys_output_labels.append(lbl)
            if len(sys_output_labels) > 120:
                old = sys_output_labels.pop(0)
                try:
                    old.destroy()
                except Exception:
                    pass
        except Exception:
            pass

    # Shared component state — populated during system info load
    _comp_vars = {}
    _comp_widgets = []
    comp_state_label = None

    def _set_components_active(is_active):
        state = "normal" if is_active else "disabled"
        for widget in _comp_widgets:
            try:
                widget.configure(state=state)
            except Exception:
                pass
        try:
            if comp_state_label is not None:
                if is_active:
                    comp_state_label.configure(
                        text="✅ Components active  —  ⚠️ Physically check Privacy Indicator lights on device",
                        text_color="#7ee787"
                    )
                else:
                    comp_state_label.configure(text="Components locked until System Info PASS", text_color="#9fb3c8")
        except Exception:
            pass


    def _load_system_info():
        _set_components_active(False)
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
                        app.after(0, lambda ln=line: _append_sys_line(ln))
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

                # Capture any remaining stderr and append through the same UI path
                try:
                    stderr = (proc.stderr.read() if proc.stderr is not None else "") or ""
                    if stderr.strip():
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
            try:
                # clear existing labels and write fallback report into the multiline frame
                for lbl in list(sys_output_labels):
                    try:
                        lbl.destroy()
                    except Exception:
                        pass
                sys_output_labels.clear()
                for ln in str(report).splitlines():
                    _append_sys_line(ln)
                report_lower = str(report).lower()
                sys_ok = ("error" not in report_lower and "timed out" not in report_lower)
                if sys_ok:
                    if hasattr(sys_card, 'set_pass'):
                        try:
                            sys_card.set_pass()
                        except Exception:
                            pass
                    _set_components_active(True)
                    # Auto-PASS the Components card and sidebar indicator
                    try:
                        if hasattr(comp_card, 'set_pass'):
                            comp_card.set_pass()
                    except Exception:
                        pass
                else:
                    if hasattr(sys_card, 'set_fail'):
                        try:
                            sys_card.set_fail()
                        except Exception:
                            pass
                    _set_components_active(False)
                # After System Info finishes, jump to Components then Battery (start battery refresh)
                try:
                    def _after_sys_next():
                        try:
                            _highlight_and_show(comp_card)
                            def _to_bat():
                                try:
                                    _highlight_and_show(bat_card)
                                    threading.Thread(target=_bat_refresh, daemon=True).start()
                                except Exception:
                                    pass
                            try:
                                app.after(700, _to_bat)
                            except Exception:
                                _to_bat()
                        except Exception:
                            pass
                    ui_call(_after_sys_next)
                except Exception:
                    pass
            except Exception:
                pass

        app.after(0, _update)

    def _start_system_info_once():
        try:
            for lbl in list(sys_output_labels):
                try:
                    lbl.destroy()
                except Exception:
                    pass
            sys_output_labels.clear()
        except Exception:
            pass
        try:
            ui_call(lambda: _highlight_and_show(sys_card))
        except Exception:
            pass
        threading.Thread(target=_load_system_info, daemon=True).start()

    # Run button removed; use header ⟳ to trigger system info

    # ══════════════════════════════════════════════════════════════════
    # 3. COMPONENTS CARD (separate from System Info)
    # ══════════════════════════════════════════════════════════════════
    comp_card = card(body, "🧩  Components", track_key="comp")
    try:
        try:
            comp_card.winfo_children()[0].destroy()
        except Exception:
            pass
        _comp_header_row = ctk.CTkFrame(comp_card, fg_color="transparent")
        _comp_header_row.pack(fill="x", padx=14, pady=(10, 6))
        ctk.CTkLabel(_comp_header_row, text="🧩  Components",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#58a6ff").pack(side="left")
        try:
            ctk.CTkButton(_comp_header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=_start_system_info_once).pack(side="right")
        except Exception:
            pass
    except Exception:
        pass

    try:
        comp_frame = ctk.CTkFrame(comp_card, fg_color="transparent")
        comp_frame.pack(fill="x", padx=14, pady=(4, 8))

        # Use a simple tk.Frame for grid layout of checkboxes
        _comp_grid = tk.Frame(comp_frame, bg="#161b22")
        _comp_grid.pack(fill="x", pady=(0, 6))

        comp_state_label = ctk.CTkLabel(
            comp_frame,
            text="Components locked until System Info PASS",
            font=ctk.CTkFont(size=11),
            text_color="#9fb3c8"
        )
        comp_state_label.pack(anchor="w", padx=2, pady=(4, 4))

        comp_labels = [
            ("WWAN",         "wwan"),
            ("WLAN",         "wlan"),
            ("Privacy",      "privacy"),
            ("NFC",          "nfc"),
            ("Smart Card",   "smartcard"),
            ("Backlight",    "backlight"),
            ("RGB Keyboard", "rgb_keyboard"),
            ("Fingerprint",  "fingerprint"),
        ]

        for i, (label_text, key) in enumerate(comp_labels):
            var = tk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(_comp_grid, text=label_text, variable=var)
            cb.grid(row=i // 4, column=i % 4, sticky="w", padx=8, pady=4)
            _comp_vars[key] = var
            _comp_widgets.append(cb)

        _set_components_active(False)
    except Exception:
        pass

    # ══════════════════════════════════════════════════════════════════
    # 4. BATTERY CARD
    # ══════════════════════════════════════════════════════════════════
    bat_card = card(body, "🔋  Battery", track_key="bat")
    # Header like Drivers with small refresh icon
    try:
        try:
            first_child = bat_card.winfo_children()[0]
            try:
                first_child.destroy()
            except Exception:
                pass
        except Exception:
            pass
        header_row = ctk.CTkFrame(bat_card, fg_color="transparent")
        header_row.pack(fill="x", padx=14, pady=(10,6))
        ctk.CTkLabel(header_row, text="🔋  Battery", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff").pack(side="left")
        try:
            ctk.CTkButton(header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=lambda: threading.Thread(target=_bat_refresh, daemon=True).start()).pack(side="right")
        except Exception:
            pass
    except Exception:
        pass

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
            _log_sequence("battery refresh started")
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
                    # mark hardware card as FAIL when no battery detected
                    try:
                        if hasattr(bat_card, 'set_fail'):
                            bat_card.set_fail()
                            _log_sequence("battery result fail: no battery detected")
                    except Exception:
                        pass
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
                # Auto-mark the hardware battery card pass/fail based on health
                try:
                    hp = data.get('health_percent')
                    if isinstance(hp, (int, float)):
                        if hp >= 60:
                            if hasattr(bat_card, 'set_pass'):
                                bat_card.set_pass()
                                _log_sequence(f"battery result pass: health_percent={hp}")
                        else:
                            if hasattr(bat_card, 'set_fail'):
                                bat_card.set_fail()
                                _log_sequence(f"battery result fail: health_percent={hp}")
                    else:
                        # health unknown -> fail
                        if hasattr(bat_card, 'set_fail'):
                            bat_card.set_fail()
                            _log_sequence("battery result fail: health unknown")
                except Exception:
                    pass
            ui_call(_apply_data)
        except Exception as e:
            _log_sequence(f"battery refresh exception: {e}")
            ui_call(lambda: widget_exists(bat_cap_lbl) and bat_cap_lbl.configure(text=str(e)))

    def _bat_auto():
        try:
            if active_screen is None or not active_screen.winfo_exists():
                return
            # Avoid running automatic battery refresh while an automated sequence runs
            try:
                if _sequence_running[0]:
                    _bat_after_id[0] = app.after(5000, _bat_auto)
                    return
            except Exception:
                pass
            threading.Thread(target=_bat_refresh, daemon=True).start()
            _bat_after_id[0] = app.after(5000, _bat_auto)
        except Exception:
            pass

    threading.Thread(target=_bat_refresh, daemon=True).start()
    _bat_after_id[0] = app.after(5000, _bat_auto)

    # Row for Speaker, Mic, and Brightness
    test_row_compact_top = tk.Frame(body, bg="#161b22")
    test_row_compact_top.pack(fill="x", padx=14, pady=8)

    # ══════════════════════════════════════════════════════════════════
    # SPEAKER CARD
    # ══════════════════════════════════════════════════════════════════
    spk_card = card(test_row_compact_top, "🔊  Speaker Test", track_key="spk")
    spk_card.pack_forget()
    spk_card.pack(side="left", fill="both", expand=True, padx=(0, 5))
    # Header like Drivers with small refresh icon
    try:
        try:
            first_child = spk_card.winfo_children()[0]
            try:
                first_child.destroy()
            except Exception:
                pass
        except Exception:
            pass
        header_row = ctk.CTkFrame(spk_card, fg_color="transparent")
        header_row.pack(fill="x", padx=14, pady=(10,6))
        ctk.CTkLabel(header_row, text="🔊  Speaker Test", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff").pack(side="left")
        try:
            # Use lambda so callback resolves after local funcs are defined.
            ctk.CTkButton(header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=lambda: _spk_play()).pack(side="right")
        except Exception:
            pass
    except Exception:
        pass
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
    # Whether speaker should loop playback until user marks PASS/FAIL
    spk_loop = [False]

    def _spk_on_finished():
        if active_screen is None or not active_screen.winfo_exists(): return
        # If looping is enabled and the card hasn't been marked PASS/FAIL, restart playback immediately
        try:
            if spk_loop[0]:
                txt = _get_card_status_text(spk_card) or ""
                if not _extract_card_result(txt):
                    try:
                        _spk_play()
                    except Exception:
                        try:
                            threading.Thread(target=_spk_play, daemon=True).start()
                        except Exception:
                            pass
                    return
        except Exception:
            pass

        spk_status.configure(text="Playback finished.")
        spk_play_btn.configure(state="normal")
        spk_stop_btn.configure(state="disabled")

    def _spk_play():
        spk_status.configure(text="Playing ST.WAV (looping)...")
        spk_play_btn.configure(state="disabled")
        spk_stop_btn.configure(state="normal")
        # enable looping flag (used by powershell fallback path via _spk_on_finished)
        spk_loop[0] = True
        # loop=True: winsound uses SND_LOOP|SND_ASYNC for gapless repeat; no poll needed
        start_speaker_playback(_spk_on_finished, loop=True)

    def _spk_stop():
        # stop looping and playback
        spk_loop[0] = False
        stop_speaker_test()
        spk_status.configure(text="Stopped.")
        spk_play_btn.configure(state="normal")
        spk_stop_btn.configure(state="disabled")

    spk_play_btn.configure(command=_spk_play)
    spk_stop_btn.configure(command=_spk_stop)

    # Ensure PASS/FAIL clicks stop looping playback immediately
    try:
        if hasattr(spk_card, 'pass_btn') and hasattr(spk_card, 'set_pass'):
            spk_card.pass_btn.configure(command=lambda: (_spk_stop(), spk_card.set_pass()))
        if hasattr(spk_card, 'fail_btn') and hasattr(spk_card, 'set_fail'):
            spk_card.fail_btn.configure(command=lambda: (_spk_stop(), spk_card.set_fail()))
    except Exception:
        pass

    # ══════════════════════════════════════════════════════════════════
    # MIC CARD
    # ══════════════════════════════════════════════════════════════════
    mic_card = card(test_row_compact_top, "🎤  Microphone Test", track_key="mic")
    mic_card.pack_forget()
    mic_card.pack(side="left", fill="both", expand=True, padx=5)
    # Header like Drivers with small refresh icon
    try:
        try:
            first_child = mic_card.winfo_children()[0]
            try:
                first_child.destroy()
            except Exception:
                pass
        except Exception:
            pass
        header_row = ctk.CTkFrame(mic_card, fg_color="transparent")
        header_row.pack(fill="x", padx=14, pady=(10,6))
        ctk.CTkLabel(header_row, text="🎤  Microphone Test", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff").pack(side="left")
        def _mic_refresh_clicked():
            try:
                # Re-run the embedded mic test when supported by the loaded tester.
                if 'mic_tester' in locals() and mic_tester is not None:
                    if hasattr(mic_tester, 'start_test'):
                        mic_tester.start_test()
                    elif hasattr(mic_tester, 'start'):
                        mic_tester.start()
                    elif hasattr(mic_tester, 'run_test'):
                        mic_tester.run_test()
                try:
                    mic_status.configure(text="Mic refresh requested.", text_color="#9fb3c8")
                except Exception:
                    pass
            except Exception:
                pass
        try:
            ctk.CTkButton(header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=lambda: _mic_refresh_clicked()).pack(side="right")
        except Exception:
            pass
    except Exception:
        pass
    mic_status = ctk.CTkLabel(mic_card, text="Click Start to begin mic test",
                               font=ctk.CTkFont(size=12), text_color="#9fb3c8")
    mic_status.pack(anchor="w", padx=14, pady=(0,6))

    # Embed the full MICTEST1 UI inside this card (non-fullscreen)
    mic_embed_host = tk.Frame(mic_card, bg="#101723", height=240)
    # give it a fixed height and prevent geometry propagation
    mic_embed_host.pack(fill="both", expand=False, padx=14, pady=(6, 10))
    try:
        mic_embed_host.pack_propagate(False)
    except Exception:
        pass

    try:
        # Prefer MicrophoneTesterGUI if available (provides live waveform)
        if 'MicrophoneTesterGUI' in globals() and MicrophoneTesterGUI is not None:
            try:
                # Some tester classes expect a root/Toplevel; pass the host frame
                mic_tester = MicrophoneTesterGUI.MicrophoneTesterApp(mic_embed_host)
            except Exception:
                # Fallback to attempting to embed into a Toplevel if the class sets window attributes
                try:
                    win = tk.Toplevel(mic_embed_host)
                    win.transient(app)
                    mic_tester = MicrophoneTesterGUI.MicrophoneTesterApp(win)
                except Exception:
                    mic_tester = None
        else:
            mic_tester = None

        # If MicrophoneTesterGUI wasn't usable, fall back to MICTEST1 if present
        if mic_tester is None and 'MICTEST1' in globals():
            try:
                mic_tester = MICTEST1.AudioDiagnosticApp(mic_embed_host, menu_callback=lambda: None)
                mic_tester.set_menu_callback(lambda: None)
            except Exception:
                mic_tester = None

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
    tp_card = card(body, "🖱️  Touchpad Test", track_key="tp")
    try:
        try:
            tp_card.winfo_children()[0].destroy()
        except Exception:
            pass
        tp_header_row = ctk.CTkFrame(tp_card, fg_color="transparent")
        tp_header_row.pack(fill="x", padx=14, pady=(10,6))
        ctk.CTkLabel(tp_header_row, text="🖱️  Touchpad Test", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff").pack(side="left")
        try:
            ctk.CTkButton(tp_header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=lambda: _start_touchpad_embed()).pack(side="right")
        except Exception:
            pass
    except Exception:
        pass
    tp_status = ctk.CTkLabel(tp_card, text="Click Start to load touchpad module.",
                              font=ctk.CTkFont(size=12), text_color="#9fb3c8")
    tp_status.pack(anchor="w", padx=14, pady=(0,6))

    tp_btn_row = ctk.CTkFrame(tp_card, fg_color="transparent")
    tp_btn_row.pack(anchor="w", padx=14, pady=(0, 8))
    tp_active = [False]
    

    # placeholder for embedded widgets (this host will receive the full TouchpadTester)
    tp_host = tk.Frame(tp_card, bg="#0d1117")
    # Allow the embedded touchpad tester to size the host so its
    # canvas and controls are not clipped. Let the host expand.
    try:
        tp_host.pack(fill="both", expand=True, padx=14, pady=(6,0))
    except Exception:
        tp_host.pack(fill="both", expand=True, padx=14, pady=(6,0))

    def _start_touchpad_embed():
        tp_active[0] = True
        try:
            tp_status.configure(text="Touchpad module running.", text_color="#7ee787")
        except Exception:
            pass
        # clear any existing children
        for w in tp_host.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

        _tp_path = os.path.join(BASE, "touchpad_test.py")
        if not os.path.exists(_tp_path):
            ctk.CTkLabel(tp_host, text=f"touchpad_test.py not found: {_tp_path}", text_color="#ff7b72").pack(pady=14)
            tp_active[0] = False
            return

        try:
            _tp_spec = _importlib_util.spec_from_file_location("touchpad_test", _tp_path)
            touchpad_mod = _importlib_util.module_from_spec(_tp_spec)
            _tp_spec.loader.exec_module(touchpad_mod)
            # instantiate embedded tester inside the visible host
            touchpad_mod.TouchpadTester(embed_host=tp_host)
        except Exception as e:
            ctk.CTkLabel(tp_host, text=f"Could not embed touchpad tester: {e}", text_color="#ff7b72").pack(pady=14)
            tp_active[0] = False

    def _stop_touchpad_embed():
        tp_active[0] = False
        for w in tp_host.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass
        try:
            tp_status.configure(text="Touchpad module stopped.", text_color="#9fb3c8")
        except Exception:
            pass

    ctk.CTkButton(tp_btn_row, text="Start", width=120, height=32, command=_start_touchpad_embed).pack(side="left", padx=(0, 8))

    # Marking PASS/FAIL also deactivates this module.
    try:
        if hasattr(tp_card, 'pass_btn') and hasattr(tp_card, 'set_pass'):
            tp_card.pass_btn.configure(command=lambda: (_stop_touchpad_embed(), tp_card.set_pass()))
        if hasattr(tp_card, 'fail_btn') and hasattr(tp_card, 'set_fail'):
            tp_card.fail_btn.configure(command=lambda: (_stop_touchpad_embed(), tp_card.set_fail()))
    except Exception:
        pass

    # ══════════════════════════════════════════════════════════════════
    # BRIGHTNESS CARD
    # ══════════════════════════════════════════════════════════════════
    brightness_card = card(test_row_compact_top, "💡  Brightness", track_key="br")
    brightness_card.pack_forget()
    brightness_card.pack(side="left", fill="both", expand=True, padx=(5, 0))
    try:
        try:
            brightness_card.winfo_children()[0].destroy()
        except Exception:
            pass
        br_header_row = ctk.CTkFrame(brightness_card, fg_color="transparent")
        br_header_row.pack(fill="x", padx=14, pady=(10,6))
        ctk.CTkLabel(br_header_row, text="💡  Brightness", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff").pack(side="left")
        try:
            ctk.CTkButton(br_header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=lambda: threading.Thread(target=_start_brightness_test, daemon=True).start()).pack(side="right")
        except Exception:
            pass
    except Exception:
        pass
    brightness_status = ctk.CTkLabel(brightness_card, text="Loading brightness info...", font=ctk.CTkFont(size=12), text_color="#9fb3c8")
    brightness_status.pack(anchor="w", padx=14, pady=(0,6))
    brightness_value = ctk.CTkLabel(brightness_card, text="Current: --", font=ctk.CTkFont(size=18, weight="bold"), text_color="#7ee787")
    brightness_value.pack(anchor="w", padx=14, pady=(0,8))

    # Graphical brightness bar (Canvas) with a circular knob
    br_canvas_frame = tk.Frame(brightness_card, bg="#0d1117")
    br_canvas_frame.pack(fill="x", padx=14, pady=(6,6))
    br_canvas = tk.Canvas(br_canvas_frame, height=40, bg="#0d1117", highlightthickness=0)
    br_canvas.pack(fill="x", expand=True)

    br_btn_row = ctk.CTkFrame(brightness_card, fg_color="transparent")
    br_btn_row.pack(anchor="w", padx=14, pady=(0,10))
    br_start_btn = ctk.CTkButton(br_btn_row, text="Start Test", width=120, command=lambda: threading.Thread(target=_start_brightness_test, daemon=True).start())
    br_start_btn.pack(side="left", padx=(6,8))

    # Internal state for brightness test
    _br_test_stop = threading.Event()
    _br_test_thread = [None]

    def _draw_brightness_bar(percent):
        try:
            br_canvas.delete('all')
            w = br_canvas.winfo_width() or 180
            h = br_canvas.winfo_height() or 40
            pad = 12
            bar_h = 14
            bar_y = (h // 2) - (bar_h // 2)
            # Track background
            br_canvas.create_rectangle(pad, bar_y, w-pad, bar_y+bar_h, fill="#20262b", outline="#2f3338")
            # Filled portion
            fill_w = int((w - pad*2) * (max(0, min(100, percent)) / 100.0))
            br_canvas.create_rectangle(pad, bar_y, pad+fill_w, bar_y+bar_h, fill="#7ee787", outline="")
            # Knob
            knob_x = pad + fill_w
            knob_r = 12
            br_canvas.create_oval(knob_x-knob_r, (h//2)-knob_r, knob_x+knob_r, (h//2)+knob_r, fill="#d4af37", outline="#a07e2a")
        except Exception:
            pass

    def _set_monitor_brightness(percent):
        try:
            p = int(max(0, min(100, int(percent))))
        except Exception:
            p = 0
        # Try several methods to set brightness; some systems respond to one but not others.
        try:
            # 1) Try Get-WmiObject method
            ps1 = f"Get-WmiObject -Namespace root\\wmi -Class WmiMonitorBrightnessMethods | ForEach-Object {{ $_.WmiSetBrightness(1,{p}) }}"
            rc1, out1 = run_process_capture(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps1], shell=False)
            if rc1 == 0:
                return True

            # 2) Try Invoke-CimMethod which can invoke the WMI method directly
            ps2 = f"Invoke-CimMethod -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods -MethodName WmiSetBrightness -Arguments @{{Timeout=1;Brightness={p}}}"
            rc2, out2 = run_process_capture(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps2], shell=False)
            if rc2 == 0:
                return True

            # 3) Fallback: Get-CimInstance then call instance method
            ps3 = f"$m = Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods -ErrorAction SilentlyContinue; if ($m) {{ $m | ForEach-Object {{ $_.WmiSetBrightness(1,{p}) }} ; exit 0 }} else {{ exit 2 }}"
            rc3, out3 = run_process_capture(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps3], shell=False)
            if rc3 == 0:
                return True

            # If none succeeded, return False
            try:
                ui_call(lambda: brightness_status.configure(text=f"Brightness command failed (codes {rc1},{rc2},{rc3})", text_color="#ff7b72"))
            except Exception:
                pass
            return False
        except Exception as e:
            try:
                ui_call(lambda: brightness_status.configure(text=f"Brightness error: {e}", text_color="#ff7b72"))
            except Exception:
                pass
            return False

    def _start_brightness_test():
        if _br_test_thread[0] is not None and _br_test_thread[0].is_alive():
            return
        _br_test_stop.clear()

        def worker():
            try:
                # read initial brightness
                ps_cmd = "(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness | Select-Object -ExpandProperty CurrentBrightness | ForEach-Object { $_ }) -join ','"
                rc, out = run_process_capture(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd], shell=False)
                if rc != 0 or not out.strip():
                    ui_call(lambda: brightness_status.configure(text="Could not read current brightness.", text_color="#ff7b72"))
                    return
                try:
                    orig = int(str(out).split(',')[0].strip())
                except Exception:
                    ui_call(lambda: brightness_status.configure(text="Could not parse brightness.", text_color="#ff7b72"))
                    return

                ui_call(lambda: brightness_status.configure(text="Running brightness cycle...", text_color="#7ee787"))
                ui_call(lambda: br_stop_btn.configure(state="normal"))

                # Run the full cycle within ~6 seconds: divide into three equal phases
                frames_per_phase = 10
                total_frames = frames_per_phase * 3
                interval = 6.0 / total_frames

                # Phase 1: original -> 0
                for i in range(1, frames_per_phase + 1):
                    if _br_test_stop.is_set():
                        break
                    p = int(round(orig * (1 - (i / frames_per_phase))))
                    ok = _set_monitor_brightness(p)
                    ui_call(lambda v=p: (brightness_value.configure(text=f"Current: {v}%"), _draw_brightness_bar(v)))
                    time.sleep(interval)

                # Phase 2: 0 -> 100
                for i in range(1, frames_per_phase + 1):
                    if _br_test_stop.is_set():
                        break
                    p = int(round(0 + (100 - 0) * (i / frames_per_phase)))
                    ok = _set_monitor_brightness(p)
                    ui_call(lambda v=p: (brightness_value.configure(text=f"Current: {v}%"), _draw_brightness_bar(v)))
                    time.sleep(interval)

                # Phase 3: 100 -> original
                for i in range(1, frames_per_phase + 1):
                    if _br_test_stop.is_set():
                        break
                    p = int(round(100 + (orig - 100) * (i / frames_per_phase)))
                    ok = _set_monitor_brightness(p)
                    ui_call(lambda v=p: (brightness_value.configure(text=f"Current: {v}%"), _draw_brightness_bar(v)))
                    time.sleep(interval)

                # restore original explicitly
                if not _br_test_stop.is_set():
                    _set_monitor_brightness(orig)
                    ui_call(lambda: brightness_value.configure(text=f"Current: {orig}%"))
                    ui_call(lambda: brightness_status.configure(text="Brightness cycle complete.", text_color="#7ee787"))
                else:
                    ui_call(lambda: brightness_status.configure(text="Brightness test stopped.", text_color="#9fb3c8"))
            except Exception as e:
                ui_call(lambda: brightness_status.configure(text=f"Error: {e}", text_color="#ff7b72"))
            finally:
                ui_call(lambda: br_stop_btn.configure(state="disabled"))

        _br_test_thread[0] = threading.Thread(target=worker, daemon=True)
        _br_test_thread[0].start()

    def _stop_brightness_test():
        try:
            _br_test_stop.set()
        except Exception:
            pass

    # Populate UI with initial brightness read
    def _initial_draw():
        try:
            ps_cmd = "(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness | Select-Object -ExpandProperty CurrentBrightness | ForEach-Object { $_ }) -join ','"
            rc, out = run_process_capture(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd], shell=False)
            if rc == 0 and out.strip():
                try:
                    val = int(str(out).split(',')[0].strip())
                except Exception:
                    val = 0
            else:
                val = 0
            ui_call(lambda v=val: (brightness_value.configure(text=f"Current: {v}%"), _draw_brightness_bar(v)))
        except Exception:
            ui_call(lambda: brightness_status.configure(text="Could not initialize brightness UI.", text_color="#ff7b72"))

    threading.Thread(target=_initial_draw, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════
    # PORT CHECKER CARD
    # ══════════════════════════════════════════════════════════════════
    port_card = card(body, "🔌  Port Checker", track_key="port")
    try:
        try:
            port_card.winfo_children()[0].destroy()
        except Exception:
            pass
        port_header_row = ctk.CTkFrame(port_card, fg_color="transparent")
        port_header_row.pack(fill="x", padx=14, pady=(10,6))
        ctk.CTkLabel(port_header_row, text="🔌  Port Checker", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff").pack(side="left")
    except Exception:
        port_header_row = None

    port_status = ctk.CTkLabel(
        port_card,
        text="Checking USB, HDMI, DisplayPort, Audio Jack, Ethernet, and USB-C...",
        font=ctk.CTkFont(size=12),
        text_color="#9fb3c8",
    )
    port_status.pack(anchor="w", padx=14, pady=(0, 6))

    port_note = ctk.CTkLabel(
        port_card,
        text="HDMI/DisplayPort/Ethernet are strongest. Audio jack and USB-C are best-effort on some systems.",
        font=ctk.CTkFont(size=10),
        text_color="#8b949e",
        justify="left",
        wraplength=780,
    )
    port_note.pack(anchor="w", padx=14, pady=(0, 8))

    port_grid = ctk.CTkFrame(port_card, fg_color="transparent")
    port_grid.pack(fill="x", padx=14, pady=(0, 10))
    try:
        port_grid.grid_columnconfigure(0, weight=1)
        port_grid.grid_columnconfigure(1, weight=1)
    except Exception:
        pass

    port_rows = {}

    def _make_port_row(parent, row, col, label_text):
        item = ctk.CTkFrame(parent, fg_color="#0d1117", corner_radius=8, border_width=1, border_color="#30363d")
        item.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
        ctk.CTkLabel(item, text=label_text, font=ctk.CTkFont(size=13, weight="bold"), text_color="#c9d1d9").pack(anchor="w", padx=12, pady=(10, 4))
        status_lbl = ctk.CTkLabel(item, text="Waiting...", font=ctk.CTkFont(size=12, weight="bold"), text_color="#f2cc60")
        status_lbl.pack(anchor="w", padx=12, pady=(0, 4))
        detail_lbl = ctk.CTkLabel(item, text="No data yet", font=ctk.CTkFont(size=10), text_color="#8b949e", justify="left", wraplength=320)
        detail_lbl.pack(anchor="w", padx=12, pady=(0, 10))
        return {"frame": item, "status": status_lbl, "detail": detail_lbl}

    _port_names = ["USB", "HDMI", "DisplayPort", "Audio Jack", "Ethernet", "USB-C"]
    for idx, _port_name in enumerate(_port_names):
        _r, _c = divmod(idx, 2)
        port_rows[_port_name] = _make_port_row(port_grid, _r, _c, _port_name)

    _port_poll_after_id = [None]
    _port_check_running = [False]
    _port_last_signature = [None]

    def _set_port_result(name, status_text, color, detail_text):
        try:
            row = port_rows.get(name)
            if row is None:
                return
            row["status"].configure(text=status_text, text_color=color)
            row["detail"].configure(text=detail_text)
        except Exception:
            pass

    def _port_detect_usb(items):
        matches = []
        for dev in items:
            if dev.get("Class") != "USB":
                continue
            friendly = str(dev.get("FriendlyName") or "")
            instance_id = str(dev.get("InstanceId") or "")
            lowered = friendly.lower()
            if any(skip in lowered for skip in ("hub", "host controller", "root hub")):
                continue
            if not instance_id.upper().startswith("USB\\"):
                continue
            matches.append(friendly or instance_id)
        if matches:
            return ("CONNECTED", "#7ee787", "\n".join(matches[:3]))
        return ("NOT DETECTED", "#ff7b72", "No external USB device detected.")

    def _port_detect_display(monitors, target_code, label):
        matches = []
        for monitor in monitors:
            try:
                if not monitor.get("Active"):
                    continue
                if int(monitor.get("VideoOutputTechnology", -1)) == target_code:
                    matches.append(str(monitor.get("InstanceName") or "Active display"))
            except Exception:
                continue
        if matches:
            return ("CONNECTED", "#7ee787", "\n".join(matches[:3]))
        return ("NOT DETECTED", "#ff7b72", f"No active {label} display detected.")

    def _port_detect_ethernet(adapters):
        matches = []
        for adapter in adapters:
            name = str(adapter.get("Name") or "")
            desc = str(adapter.get("InterfaceDescription") or "")
            haystack = f"{name} {desc}".lower()
            if "ethernet" not in haystack and "802.3" not in haystack:
                continue
            status = str(adapter.get("Status") or "").lower()
            media_state = str(adapter.get("MediaConnectionState") or "")
            if status == "up" or media_state == "1":
                matches.append(f"{name} ({desc})")
        if matches:
            return ("CONNECTED", "#7ee787", "\n".join(matches[:3]))
        return ("NOT DETECTED", "#ff7b72", "No active ethernet link detected.")

    def _port_detect_audio(items):
        matches = []
        for dev in items:
            if dev.get("Class") != "AudioEndpoint":
                continue
            friendly = str(dev.get("FriendlyName") or "")
            lowered = friendly.lower()
            if any(skip in lowered for skip in ("display audio", "intel(", "nvidia", "amd hd audio", "usb")):
                continue
            if any(key in lowered for key in ("headphone", "headset", "line in", "line-in", "line out", "line-out", "mic in", "front mic")):
                matches.append(friendly)
        if matches:
            return ("LIKELY CONNECTED", "#f2cc60", "\n".join(matches[:3]))
        return ("NOT DETECTED", "#ff7b72", "No wired audio-jack endpoint detected.")

    def _port_detect_usbc(items):
        matches = []
        for dev in items:
            friendly = str(dev.get("FriendlyName") or "")
            lowered = friendly.lower()
            if any(key in lowered for key in ("usb-c", "type-c", "usb4", "thunderbolt", "billboard", "dock")):
                matches.append(friendly)
        if matches:
            return ("LIKELY CONNECTED", "#f2cc60", "\n".join(matches[:3]))
        return ("UNKNOWN", "#f2cc60", "No clear USB-C-specific device evidence.")

    def _normalize_port_data(value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def _start_port_check():
        if _port_check_running[0]:
            return
        _port_check_running[0] = True
        try:
            port_status.configure(text="Refreshing port status...", text_color="#58a6ff")
        except Exception:
            pass

        ps_script = r"""
$ErrorActionPreference = 'Stop'

$monitors = @()
try {
    $monitors = Get-CimInstance -Namespace root\wmi -ClassName WmiMonitorConnectionParams |
        Select-Object InstanceName, VideoOutputTechnology, Active
} catch {
    $monitors = @()
}

$adapters = @()
try {
    $adapters = Get-NetAdapter -Physical |
        Select-Object Name, Status, MediaConnectionState, InterfaceDescription
} catch {
    $adapters = @()
}

$pnp = @()
try {
    $pnp = Get-PnpDevice -PresentOnly |
        Where-Object { $_.Class -in @('USB', 'AudioEndpoint', 'MEDIA', 'Net') } |
        Select-Object Class, FriendlyName, InstanceId, Status
} catch {
    $pnp = @()
}

[pscustomobject]@{
    monitors = $monitors
    adapters = $adapters
    pnp      = $pnp
} | ConvertTo-Json -Compress -Depth 5
"""
        creation = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        def _worker():
            try:
                proc = subprocess.run(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                    capture_output=True,
                    text=True,
                    timeout=20,
                    creationflags=creation,
                )
                if proc.returncode != 0:
                    raise RuntimeError((proc.stderr or proc.stdout or "PowerShell query failed").strip())

                payload = json.loads((proc.stdout or "{}").strip() or "{}")
                monitors = _normalize_port_data(payload.get("monitors"))
                adapters = _normalize_port_data(payload.get("adapters"))
                pnp = _normalize_port_data(payload.get("pnp"))

                results = {
                    "USB": _port_detect_usb(pnp),
                    "HDMI": _port_detect_display(monitors, 6, "HDMI"),
                    "DisplayPort": _port_detect_display(monitors, 10, "DisplayPort"),
                    "Audio Jack": _port_detect_audio(pnp),
                    "Ethernet": _port_detect_ethernet(adapters),
                    "USB-C": _port_detect_usbc(pnp),
                }
                result_signature = json.dumps(results, sort_keys=True)

                def _apply():
                    for key, (state_text, color, detail_text) in results.items():
                        _set_port_result(key, state_text, color, detail_text)
                    try:
                        if _port_last_signature[0] is None:
                            port_status.configure(text="Port check complete. Watching for plug and unplug changes...", text_color="#7ee787")
                        elif _port_last_signature[0] != result_signature:
                            port_status.configure(text="Port change detected. Status updated.", text_color="#7ee787")
                        else:
                            port_status.configure(text="Watching for plug and unplug changes...", text_color="#9fb3c8")
                    except Exception:
                        pass
                    _port_last_signature[0] = result_signature
                    _port_check_running[0] = False

                ui_call(_apply)
            except Exception as exc:
                def _show_error():
                    try:
                        port_status.configure(text=f"Port check failed: {exc}", text_color="#ff7b72")
                    except Exception:
                        pass
                    for key in _port_names:
                        _set_port_result(key, "ERROR", "#ff7b72", str(exc))
                    _port_check_running[0] = False

                ui_call(_show_error)

        threading.Thread(target=_worker, daemon=True).start()

    def _port_auto_refresh():
        if active_screen is None or not active_screen.winfo_exists():
            return
        try:
            _start_port_check()
        finally:
            try:
                _port_poll_after_id[0] = app.after(2000, _port_auto_refresh)
            except Exception:
                _port_poll_after_id[0] = None

    if port_header_row is not None:
        try:
            ctk.CTkButton(port_header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=_start_port_check).pack(side="right")
        except Exception:
            pass

    try:
        app.after(300, _start_port_check)
        _port_poll_after_id[0] = app.after(2200, _port_auto_refresh)
    except Exception:
        _start_port_check()
        _port_auto_refresh()

    # Row for Touchscreen, Pixel, and Camera
    test_row_compact = tk.Frame(body, bg="#161b22")
    test_row_compact.pack(fill="x", padx=14, pady=8)

    # ══════════════════════════════════════════════════════════════════
    # TOUCHSCREEN CARD
    # ══════════════════════════════════════════════════════════════════
    touchscreen_card = card(test_row_compact, "👆  Touchscreen", track_key="ts")
    touchscreen_card.pack_forget()
    touchscreen_card.pack(side="left", fill="both", expand=True, padx=(0, 5))
    try:
        try:
            touchscreen_card.winfo_children()[0].destroy()
        except Exception:
            pass
        ts_header_row = ctk.CTkFrame(touchscreen_card, fg_color="transparent")
        ts_header_row.pack(fill="x", padx=14, pady=(10,6))
        ctk.CTkLabel(ts_header_row, text="👆  Touchscreen", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff").pack(side="left")
        try:
            # Use lambda so callback resolves after local funcs are defined.
            ctk.CTkButton(ts_header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=lambda: _run_touchscreen_test()).pack(side="right")
        except Exception:
            pass
    except Exception:
        pass
    touchscreen_status = ctk.CTkLabel(touchscreen_card, text="Click Run to start touchscreen test.", font=ctk.CTkFont(size=12), text_color="#9fb3c8")
    touchscreen_status.pack(anchor="w", padx=14, pady=(0,6))

    ts_btn_row = ctk.CTkFrame(touchscreen_card, fg_color="transparent")
    ts_btn_row.pack(anchor="w", padx=14, pady=(0, 8))

    ts_host = tk.Frame(touchscreen_card, bg="#0d1117")
    ts_host.pack(fill="both", expand=False, padx=14, pady=(6,0))
    try:
        # Reduce touchscreen embed height to half
        ts_host.configure(height=210)
        ts_host.pack_propagate(False)
    except Exception:
        pass

    # Helper: detect touchscreen presence on Windows using GetSystemMetrics
    def _has_touchscreen():
        try:
            import ctypes
            SM_DIGITIZER = 94
            SM_MAXIMUMTOUCHES = 95
            val = ctypes.windll.user32.GetSystemMetrics(SM_DIGITIZER)
            # NID_INTEGRATED_TOUCH (0x01) or NID_EXTERNAL_TOUCH (0x02)
            if (val & 0x1) or (val & 0x2):
                return True
            # fallback: check maximum touches
            max_touches = ctypes.windll.user32.GetSystemMetrics(SM_MAXIMUMTOUCHES)
            return int(max_touches) > 0
        except Exception:
            return False

    touchscreen_window = [None]

    def _stop_touchscreen_test():
        try:
            win = touchscreen_window[0]
            if win is not None and widget_exists(win):
                win.destroy()
        except Exception:
            pass
        touchscreen_window[0] = None
        try:
            touchscreen_status.configure(text="Touchscreen test stopped.", text_color="#9fb3c8")
        except Exception:
            pass

    def _start_touchscreen_test():
        try:
            ts_path = os.path.join(BASE, "Touchscreentest.py")
            if not os.path.exists(ts_path):
                ui_call(lambda: touchscreen_status.configure(text=f"Touchscreentest.py not found: {ts_path}", text_color="#ff7b72"))
                return

            # load module then instantiate its app in a fullscreen Toplevel
            _spec = _importlib_util.spec_from_file_location("touchscreentest", ts_path)
            ts_mod = _importlib_util.module_from_spec(_spec)
            _spec.loader.exec_module(ts_mod)

            def _open_window():
                try:
                    win = tk.Toplevel(app)
                    try:
                        win.attributes("-fullscreen", True)
                    except Exception:
                        try:
                            win.state('zoomed')
                        except Exception:
                            pass
                    touchscreen_window[0] = win
                    # instantiate the embedded tester using the Toplevel as root
                    try:
                        ts_app = ts_mod.TouchscreenTestApp(win)
                    except Exception as e:
                        ui_call(lambda: touchscreen_status.configure(text=f"Error launching test: {e}", text_color="#ff7b72"))
                        try:
                            win.destroy()
                        except Exception:
                            pass
                        return
                    ui_call(lambda: touchscreen_status.configure(text="Touchscreen test running (press Close in test window to finish)", text_color="#7ee787"))
                except Exception as e:
                    ui_call(lambda: touchscreen_status.configure(text=f"Error opening touchscreen window: {e}", text_color="#ff7b72"))

            # open the Toplevel on the UI thread
            app.after(0, _open_window)
        except Exception as e:
            ui_call(lambda: touchscreen_status.configure(text=f"Error preparing touchscreen test: {e}", text_color="#ff7b72"))

    def _run_touchscreen_test():
        try:
            _stop_touchscreen_test()
            # If touchscreen is present, run it. Otherwise prompt the operator Yes/No.
            if _has_touchscreen():
                ui_call(lambda: touchscreen_status.configure(text="Touchscreen detected — starting test...", text_color="#7ee787"))
                threading.Thread(target=_start_touchscreen_test, daemon=True).start()
                return

            # No touchscreen detected: present inline Yes/No controls so operator can
            # confirm whether the unit actually has a touchscreen.
            def _on_yes():
                try:
                    # restore normal buttons and start test
                    _create_touchscreen_buttons()
                    ui_call(lambda: touchscreen_status.configure(text="Operator confirmed touchscreen — starting test...", text_color="#7ee787"))
                    threading.Thread(target=_start_touchscreen_test, daemon=True).start()
                except Exception:
                    pass

            def _on_no():
                try:
                    _create_touchscreen_buttons()
                    ui_call(lambda: touchscreen_status.configure(text="No touchscreen is detected.", text_color="#9fb3c8"))
                    try:
                        if hasattr(touchscreen_card, 'set_pass'):
                            ui_call(lambda: touchscreen_card.set_pass())
                    except Exception:
                        pass
                except Exception:
                    pass

            # Replace the Run/Stop buttons with Yes/No for this prompt
            try:
                for w in list(ts_btn_row.winfo_children()):
                    try: w.destroy()
                    except Exception: pass
            except Exception:
                pass
            try:
                ctk.CTkButton(ts_btn_row, text="Yes", width=120, height=30, fg_color="#2ecc71", command=_on_yes).pack(side="left", padx=(0,8))
                ctk.CTkButton(ts_btn_row, text="No", width=120, height=30, fg_color="#ff6b6b", command=_on_no).pack(side="left")
            except Exception:
                # fallback to messagebox prompt if inline creation fails
                ans = messagebox.askyesno("Touchscreen?", "No touchscreen detected. Does this unit have a touchscreen?")
                if ans:
                    threading.Thread(target=_start_touchscreen_test, daemon=True).start()
                else:
                    ui_call(lambda: touchscreen_status.configure(text="No touchscreen is detected.", text_color="#9fb3c8"))
                    try:
                        if hasattr(touchscreen_card, 'set_pass'):
                            ui_call(lambda: touchscreen_card.set_pass())
                    except Exception:
                        pass
        except Exception:
            ui_call(lambda: touchscreen_status.configure(text="Touchscreen test failed to start.", text_color="#ff7b72"))

    def _create_touchscreen_buttons():
        try:
            for w in list(ts_btn_row.winfo_children()):
                try: w.destroy()
                except Exception: pass
        except Exception:
            pass
        try:
            ctk.CTkButton(ts_btn_row, text="Run", width=120, height=30, command=_run_touchscreen_test).pack(side="left", padx=(0, 8))
        except Exception:
            pass

    _create_touchscreen_buttons()

    # ══════════════════════════════════════════════════════════════════
    # PIXEL TEST CARD
    # ══════════════════════════════════════════════════════════════════
    pixel_card = card(test_row_compact, "🧪  Pixel Test", track_key="px")
    pixel_card.pack_forget()
    pixel_card.pack(side="left", fill="both", expand=True, padx=5)
    try:
        try:
            pixel_card.winfo_children()[0].destroy()
        except Exception:
            pass
        px_header_row = ctk.CTkFrame(pixel_card, fg_color="transparent")
        px_header_row.pack(fill="x", padx=14, pady=(10,6))
        ctk.CTkLabel(px_header_row, text="🧪  Pixel Test", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff").pack(side="left")
        try:
            ctk.CTkButton(px_header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=lambda: _start_pixel_test()).pack(side="right")
        except Exception:
            pass
    except Exception:
        pass
    try:
        # Reduce pixel card height to approximately half
        pixel_card.configure(height=140)
        pixel_card.pack_propagate(False)
    except Exception:
        pass
    pixel_status = ctk.CTkLabel(pixel_card, text="Start the pixel test to cycle full-screen colors.", font=ctk.CTkFont(size=12), text_color="#9fb3c8")
    pixel_status.pack(anchor="w", padx=14, pady=(0,6))
    px_btn_row = ctk.CTkFrame(pixel_card, fg_color="transparent")
    px_btn_row.pack(anchor="w", padx=14, pady=(0,4))
    px_start_btn = ctk.CTkButton(px_btn_row, text="Start", width=100, command=lambda: _start_pixel_test())
    px_start_btn.pack(side="left", padx=(0,8))
    # Pixel test does not need a Stop button in the card UI; ESC stops fullscreen.
    class _DummyBtn:
        def configure(self, *a, **k):
            pass
    px_stop_btn = _DummyBtn()

    # Keep PASS/FAIL in the standard card status area; reduce the card height
    # and button row padding above so the gap between Start/Stop and PASS/FAIL
    # is minimized.

    pixel_window = [None]
    pixel_cycle_id = [None]
    pixel_colors = ["red", "blue", "green", "black", "white", "orange"]

    def _stop_pixel_test():
        if pixel_window[0] is not None and widget_exists(pixel_window[0]):
            try:
                pixel_window[0].destroy()
            except Exception:
                pass
        pixel_window[0] = None
        if widget_exists(active_screen):
            pixel_status.configure(text="Pixel test stopped.", text_color="#9fb3c8")
            px_start_btn.configure(state="normal")
            px_stop_btn.configure(state="disabled")

    def _cycle_pixel_colors():
        if pixel_window[0] is None or not widget_exists(pixel_window[0]):
            return
        try:
            color = pixel_colors[pixel_cycle_id[0] % len(pixel_colors)]
            pixel_window[0].configure(bg=color)
            pixel_cycle_id[0] += 1
            # Slow down cycle to 2 seconds between colors
            pixel_window[0].after(2000, _cycle_pixel_colors)
        except Exception:
            _stop_pixel_test()

    def _start_pixel_test():
        if pixel_window[0] is not None and widget_exists(pixel_window[0]):
            return
        try:
            win = tk.Toplevel(app)
            # Try a robust fullscreen approach: remove decorations, force topmost,
            # and set geometry to the screen size. This covers cases where
            # attributes("-fullscreen") doesn't behave as expected on Windows.
            try:
                win.overrideredirect(True)
            except Exception:
                pass
            try:
                win.attributes("-topmost", True)
            except Exception:
                pass
            # Ensure geometry is full-screen for the monitor
            try:
                sw = win.winfo_screenwidth()
                sh = win.winfo_screenheight()
                win.geometry(f"{sw}x{sh}+0+0")
            except Exception:
                try:
                    sw = app.winfo_screenwidth()
                    sh = app.winfo_screenheight()
                    win.geometry(f"{sw}x{sh}+0+0")
                except Exception:
                    pass
            try:
                win.deiconify()
            except Exception:
                pass
            try:
                win.configure(bg="black")
            except Exception:
                pass
            try:
                win.focus_set()
            except Exception:
                pass
            win.bind("<Escape>", lambda event: _stop_pixel_test())
            pixel_window[0] = win
            pixel_cycle_id[0] = 0
            _cycle_pixel_colors()
            ui_call(lambda: pixel_status.configure(text="Pixel test running. Press ESC to stop.", text_color="#7ee787"))
            ui_call(lambda: px_start_btn.configure(state="disabled"))

            # PASS / FAIL overlay controls inside fullscreen window
            def _pixel_mark_and_close(pass_state=True):
                try:
                    if pass_state:
                        if hasattr(pixel_card, 'pass_btn') and getattr(pixel_card, 'pass_btn') is not None:
                            try:
                                ui_call(lambda: pixel_card.pass_btn.invoke())
                            except Exception:
                                ui_call(lambda: pixel_card.set_pass() if hasattr(pixel_card, 'set_pass') else None)
                        else:
                            ui_call(lambda: pixel_card.set_pass() if hasattr(pixel_card, 'set_pass') else None)
                    else:
                        if hasattr(pixel_card, 'fail_btn') and getattr(pixel_card, 'fail_btn') is not None:
                            try:
                                ui_call(lambda: pixel_card.fail_btn.invoke())
                            except Exception:
                                ui_call(lambda: pixel_card.set_fail() if hasattr(pixel_card, 'set_fail') else None)
                        else:
                            ui_call(lambda: pixel_card.set_fail() if hasattr(pixel_card, 'set_fail') else None)
                except Exception:
                    pass
                try:
                    _stop_pixel_test()
                except Exception:
                    pass

            try:
                ctrl = tk.Frame(win, bg='#000000')
                ctrl.place(relx=1.0, rely=1.0, anchor='se', x=-20, y=-20)
                fail_btn = tk.Button(ctrl, text='FAIL', bg='#ff6b6b', fg='white', activebackground='#ff5252',
                                     font=('Segoe UI', 12, 'bold'), padx=12, pady=6,
                                     command=lambda: _pixel_mark_and_close(False))
                fail_btn.pack(side='right', padx=(6,4))
                pass_btn = tk.Button(ctrl, text='PASS', bg='#2ecc71', fg='white', activebackground='#28b463',
                                     font=('Segoe UI', 12, 'bold'), padx=12, pady=6,
                                     command=lambda: _pixel_mark_and_close(True))
                pass_btn.pack(side='right', padx=(6,4))
                try:
                    ctrl.lift()
                except Exception:
                    pass
            except Exception:
                pass
        except Exception as e:
            ui_call(lambda: pixel_status.configure(text=f"Error: {e}", text_color="#ff7b72"))
            try:
                if hasattr(pixel_card, 'set_fail'):
                    pixel_card.set_fail()
            except Exception:
                pass


    # ══════════════════════════════════════════════════════════════════
    # CAMERA CARD (inline preview in main menu)
    # ══════════════════════════════════════════════════════════════════
    cam_card = card(test_row_compact, "📷  Camera Test", track_key="cam")
    cam_card.pack_forget()
    cam_card.pack(side="left", fill="both", expand=True, padx=(5, 0))
    # Drivers-style header with small refresh icon
    try:
        try:
            first_child = cam_card.winfo_children()[0]
            try:
                first_child.destroy()
            except Exception:
                pass
        except Exception:
            pass
        header_row = ctk.CTkFrame(cam_card, fg_color="transparent")
        header_row.pack(fill="x", padx=14, pady=(10,6))
        ctk.CTkLabel(header_row, text="📷  Camera Test", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff").pack(side="left")
        try:
            ctk.CTkButton(header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=lambda: threading.Thread(target=_start_camera_preview, daemon=True).start()).pack(side="right")
        except Exception:
            pass
    except Exception:
        pass

    cam_status = ctk.CTkLabel(cam_card, text="Click Start to run camera preview.",
                               font=ctk.CTkFont(size=12), text_color="#d4af37")
    cam_status.pack(anchor="w", padx=14, pady=(0,6))

    cam_btn_row = ctk.CTkFrame(cam_card, fg_color="transparent")
    cam_btn_row.pack(anchor="w", padx=14, pady=(0, 8))
    cam_active = [False]

    cam_preview_row = ctk.CTkFrame(cam_card, fg_color="transparent")
    cam_preview_row.pack(fill="x", padx=14, pady=(0,10))

    def _show_captured_frame(frame):
        try:
            import cv2
            from PIL import ImageTk, Image
        except Exception:
            return

        try:
            for child in cam_preview_row.winfo_children():
                try:
                    child.destroy()
                except Exception:
                    pass

            panel = tk.Frame(cam_preview_row, bg="#000000", width=180, height=67)
            panel.pack(side="left", padx=6)
            panel.pack_propagate(False)
            lbl = tk.Label(panel, bg="#000000")
            lbl.pack(fill="both", expand=True)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            img.thumbnail((180, 135))
            tk_img = ImageTk.PhotoImage(image=img)
            lbl.configure(image=tk_img)
            lbl.image = tk_img
        except Exception:
            pass

    def _stop_camera_preview_local():
        cam_active[0] = False
        if _cam_after_local[0]:
            try:
                app.after_cancel(_cam_after_local[0])
            except Exception:
                pass
            _cam_after_local[0] = None
        for cap in list(_cam_caps_local):
            try:
                cap.release()
            except Exception:
                pass
        _cam_caps_local.clear()
        for child in cam_preview_row.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass
        try:
            cam_status.configure(text="Camera preview stopped.", text_color="#9fb3c8")
        except Exception:
            pass

    def _start_camera_preview():
        cam_active[0] = True
        _stop_camera_preview_local()
        cam_active[0] = True
        try:
            import cv2
            from PIL import ImageTk, Image
        except Exception:
            cam_status.configure(text="OpenCV not installed. Run: pip install opencv-python", text_color="#ff7b72")
            cam_active[0] = False
            return

        def discover(max_scan=6, max_found=2):
            found = []
            for idx in range(max_scan):
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

        indexes = discover()
        if not indexes:
            cam_status.configure(text="No camera found.", text_color="#ff7b72")
            cam_active[0] = False
            return

        preview_labels = []

        for idx in indexes:
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if not cap.isOpened():
                try:
                    cap.release()
                except Exception:
                    pass
                continue
            _cam_caps_local.append(cap)

            panel = tk.Frame(cam_preview_row, bg="#000000", width=180, height=67)
            panel.pack(side="left", padx=6)
            panel.pack_propagate(False)
            lbl = tk.Label(panel, bg="#000000")
            lbl.pack(fill="both", expand=True)
            preview_labels.append(lbl)

        if not _cam_caps_local:
            cam_status.configure(text="Could not open cameras.", text_color="#ff7b72")
            cam_active[0] = False
            return

        names = ", ".join(f"Camera {i}" for i in indexes[:len(_cam_caps_local)])
        cam_status.configure(text=f"Live: {names}", text_color="#7ee787")

        def update():
            if not cam_active[0] or not cam_preview_row.winfo_exists():
                # host destroyed -> release
                _stop_camera_preview_local()
                return
            for i, cap in enumerate(_cam_caps_local):
                if i >= len(preview_labels):
                    continue
                ok, frame = cap.read()
                if not ok:
                    continue
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img.thumbnail((180, 135))
                tk_img = ImageTk.PhotoImage(image=img)
                preview_labels[i].configure(image=tk_img)
                preview_labels[i].image = tk_img
            _cam_after_local[0] = app.after(100, update)

        update()

    def _capture_camera_image():
        if not cam_active[0] or not _cam_caps_local:
            try:
                cam_status.configure(text="Start camera first, then press Capture.", text_color="#ff7b72")
            except Exception:
                pass
            return

        captured = None
        try:
            ok, frame = _cam_caps_local[0].read()
            if ok:
                captured = frame
        except Exception:
            captured = None

        if captured is None:
            try:
                cam_status.configure(text="Could not capture image.", text_color="#ff7b72")
            except Exception:
                pass
            return

        _stop_camera_preview_local()
        _show_captured_frame(captured)
        try:
            cam_status.configure(text="Image captured. Live camera stopped.", text_color="#7ee787")
        except Exception:
            pass

    ctk.CTkButton(cam_btn_row, text="Start", width=110, height=30, command=lambda: threading.Thread(target=_start_camera_preview, daemon=True).start()).pack(side="left", padx=(0, 8))
    ctk.CTkButton(cam_btn_row, text="Capture", width=110, height=30, fg_color="#2f6feb", hover_color="#3b82f6", command=_capture_camera_image).pack(side="left", padx=(0, 8))

    # Marking PASS/FAIL also deactivates this module.
    try:
        if hasattr(cam_card, 'pass_btn') and hasattr(cam_card, 'set_pass'):
            cam_card.pass_btn.configure(command=lambda: (_stop_camera_preview_local(), cam_card.set_pass()))
        if hasattr(cam_card, 'fail_btn') and hasattr(cam_card, 'set_fail'):
            cam_card.fail_btn.configure(command=lambda: (_stop_camera_preview_local(), cam_card.set_fail()))
    except Exception:
        pass

    # KEYBOARD CARD (was missing) — create the card container
    kb_card = card(body, "⌨️  Keyboard Test", track_key="kb")
    # Drivers-style header with small refresh icon
    try:
        try:
            first_child = kb_card.winfo_children()[0]
            try:
                first_child.destroy()
            except Exception:
                pass
        except Exception:
            pass
        header_row = ctk.CTkFrame(kb_card, fg_color="transparent")
        header_row.pack(fill="x", padx=14, pady=(10,6))
        ctk.CTkLabel(header_row, text="⌨️  Keyboard Test", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff").pack(side="left")
        # Refresh button: reset the embedded keyboard tester if running, otherwise start it
        def _kb_refresh_clicked():
            try:
                # Access the keyboard module state from the enclosing scope
                try:
                    tester = kb_state.get("tester")
                except Exception:
                    tester = None

                # If tester exists, try to reset it in-place
                if tester is not None:
                    try:
                        if hasattr(tester, 'reset_colors'):
                            tester.reset_colors()
                        elif hasattr(tester, 'reset'):
                            tester.reset()
                        # ensure embed host is visible and focused
                        try:
                            kb_embed_host.pack(fill='both', expand=True)
                            kb_embed_host.focus_set()
                        except Exception:
                            pass
                        try:
                            kb_status.configure(text="Keyboard module running.", text_color="#7ee787")
                        except Exception:
                            pass
                        return
                    except Exception:
                        # fall through to restart the module
                        pass

                # If no tester, start the keyboard module
                try:
                    _start_keyboard_module()
                except Exception:
                    pass
            except Exception:
                pass
        try:
            ctk.CTkButton(header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=_kb_refresh_clicked).pack(side="right")
        except Exception:
            pass
    except Exception:
        pass

    kb_status = ctk.CTkLabel(kb_card, text="Click Start to load keyboard module.",
                              font=ctk.CTkFont(size=12), text_color="#9fb3c8")
    kb_status.pack(anchor="w", padx=14, pady=(0,6))

    kb_btn_row = ctk.CTkFrame(kb_card, fg_color="transparent")
    kb_btn_row.pack(anchor="w", padx=14, pady=(0, 8))

    kb_embed_host = tk.Frame(kb_card, bg="#101723")
    kb_embed_host.pack(fill="x", expand=False, padx=14, pady=(0, 4))

    kb_state = {
        "tester": None,
        "bind_id": None,
        "active": False,
    }

    def _stop_keyboard_module():
        kb_state["active"] = False
        bind_id = kb_state.get("bind_id")
        if bind_id:
            try:
                app.unbind("<KeyPress>", bind_id)
            except Exception:
                pass
            kb_state["bind_id"] = None
        for w in kb_embed_host.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass
        kb_state["tester"] = None
        try:
            kb_status.configure(text="Keyboard module stopped.", text_color="#9fb3c8")
        except Exception:
            pass

    def _start_keyboard_module():
        if kb_state["active"]:
            return
        _stop_keyboard_module()
        kb_state["active"] = True
        try:
            kb_tester = KeyboardGUI2.KeyboardGUI(kb_embed_host)
            kb_tester.set_menu_callback(lambda: None)
            kb_state["tester"] = kb_tester
            try:
                kb_embed_host.focus_set()
            except Exception:
                pass

            def _forward_keypress(event):
                if not kb_state["active"]:
                    return
                tester = kb_state.get("tester")
                if tester is None:
                    return
                try:
                    tester._handle_physical_keypress(event)
                except Exception:
                    pass

            kb_state["bind_id"] = app.bind("<KeyPress>", _forward_keypress, add="+")
            try:
                kb_status.configure(text="Keyboard module running.", text_color="#7ee787")
            except Exception:
                pass
        except Exception as exc:
            kb_state["active"] = False
            ctk.CTkLabel(
                kb_embed_host,
                text=f"Could not load keyboard tester: {exc}",
                text_color="#ff7b72",
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(pady=14)
            try:
                kb_status.configure(text="Keyboard module failed to start.", text_color="#ff7b72")
            except Exception:
                pass

    ctk.CTkButton(kb_btn_row, text="Start", width=110, height=30, command=_start_keyboard_module).pack(side="left", padx=(0, 8))

    # Marking PASS/FAIL also deactivates this module.
    try:
        if hasattr(kb_card, 'pass_btn') and hasattr(kb_card, 'set_pass'):
            kb_card.pass_btn.configure(command=lambda: (_stop_keyboard_module(), kb_card.set_pass()))
        if hasattr(kb_card, 'fail_btn') and hasattr(kb_card, 'set_fail'):
            kb_card.fail_btn.configure(command=lambda: (_stop_keyboard_module(), kb_card.set_fail()))
    except Exception:
        pass

    # (Duplicate Touchpad card removed — single embedded instance appears earlier)

    # Bottom padding
    # ══════════════════════════════════════════════════════════════════
    # ACTIVATION + DRIVERS ROW
    # ══════════════════════════════════════════════════════════════════
    # Create a horizontal row to hold Activation and Drivers cards side-by-side
    row_frame = tk.Frame(body, bg="#161b22")
    row_frame.pack(fill="x", padx=14, pady=8)

    # Activation card (left)
    act_card = ctk.CTkFrame(row_frame, fg_color="#161b22", corner_radius=10,
                             border_width=1, border_color="#30363d")
    act_card.pack(side="left", fill="both", expand=True, padx=(0,5))
    
    # Activation header (Drivers-style with small refresh icon)
    try:
        header_row = ctk.CTkFrame(act_card, fg_color="transparent")
        header_row.pack(fill="x", padx=14, pady=(10,6))
        ctk.CTkLabel(header_row, text="🔐  Activation", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff").pack(side="left")
        try:
            # Use lambda so callback resolves after local funcs are defined.
            ctk.CTkButton(header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=lambda: _run_activation_check()).pack(side="right")
        except Exception:
            pass
    except Exception:
        pass
    act_label = ctk.CTkLabel(
        act_card,
        text="Activation Check",
        font=ctk.CTkFont(size=12),
        text_color="#9fb3c8",
    )
    act_label.pack(anchor="w", padx=14, pady=(0, 10))
    act_result_label = ctk.CTkLabel(act_card, text="Checking...", font=ctk.CTkFont(size=13), text_color="#9fb3c8", justify="left")
    act_result_label.pack(anchor="w", padx=14, pady=(0, 10))
# Add PASS/FAIL status controls to Activation card (mirrors other cards)
    try:
        act_status_frame = ctk.CTkFrame(act_card, fg_color="#161b22", corner_radius=0)
        act_status_frame.pack(side="bottom", fill="x", padx=14, pady=(6, 10))

        act_status_display = ctk.CTkLabel(act_status_frame, text="NOT RUN",
                                           font=ctk.CTkFont(size=11, weight="bold"),
                                           text_color="#9aa4b2")
        act_status_display.pack(side="right", padx=(6, 12))

        _act_pass_active = "#2ecc71"
        _act_fail_active = "#ff6b6b"
        _act_btn_inactive = "#2f3338"

        def act_set_pass():
            try:
                act_status_display.configure(text="PASS  ✔", text_color=_act_pass_active)
                act_pass_btn.configure(fg_color=_act_pass_active)
                act_fail_btn.configure(fg_color=_act_btn_inactive)
                update_sidebar_status("act", 'pass')
            except Exception:
                pass

        def act_set_fail():
            try:
                act_status_display.configure(text="FAIL  ✖", text_color=_act_fail_active)
                act_fail_btn.configure(fg_color=_act_fail_active)
                act_pass_btn.configure(fg_color=_act_btn_inactive)
                update_sidebar_status("act", 'fail')
            except Exception:
                pass

        act_pass_btn = ctk.CTkButton(
            act_status_frame,
            text="✔",
            width=34,
            height=34,
            fg_color=_act_btn_inactive,
            hover_color="#28b463",
            corner_radius=18,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=act_set_pass,
            text_color="white",
        )
        act_pass_btn.pack(side="right", padx=(6, 4))

        act_fail_btn = ctk.CTkButton(
            act_status_frame,
            text="✖",
            width=34,
            height=34,
            fg_color=_act_btn_inactive,
            hover_color="#ff5252",
            corner_radius=18,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=act_set_fail,
            text_color="white",
        )
        act_fail_btn.pack(side="right", padx=(6, 4))

        try:
            act_card.set_pass = act_set_pass
            act_card.set_fail = act_set_fail
            act_card.status_display = act_status_display
            act_card.pass_btn = act_pass_btn
            act_card.fail_btn = act_fail_btn
        except Exception:
            pass
    except Exception:
        pass

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
                try:
                    if hasattr(act_card, 'set_pass'):
                        ui_call(lambda: act_card.set_pass())
                except Exception:
                    pass
            else:
                result_text = "✗ Windows is not Activated"
                color = "#ff7b72"
                try:
                    if hasattr(act_card, 'set_fail'):
                        ui_call(lambda: act_card.set_fail())
                except Exception:
                    pass
            app.after(0, lambda: act_result_label.configure(text=result_text, text_color=color))
        except Exception:
            pass

    def _run_activation_check():
        try:
            act_result_label.configure(text="Checking...", text_color="#9fb3c8")
        except Exception:
            pass
        threading.Thread(target=_load_activation_status, daemon=True).start()
    threading.Thread(target=_load_activation_status, daemon=True).start()

    # Drivers card (right)
    drv_card = ctk.CTkFrame(row_frame, fg_color="#161b22", corner_radius=10,
                            border_width=1, border_color="#30363d")
    drv_card.pack(side="left", fill="both", expand=True, padx=5)
    
    # Header with title + refresh button
    header_row = ctk.CTkFrame(drv_card, fg_color="transparent")
    header_row.pack(fill="x", padx=14, pady=(10,6))
    ctk.CTkLabel(header_row, text="🛠️  Drivers", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff").pack(side="left")
    # small refresh icon button
    def _drv_refresh_clicked():
        try:
            _reset_drv_card()
            _reset_gpu_card()
            threading.Thread(target=_run_drivers_check, daemon=True).start()
            threading.Thread(target=_run_gpu_check, daemon=True).start()
        except Exception:
            pass

    try:
        refresh_btn = ctk.CTkButton(header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=_drv_refresh_clicked)
        refresh_btn.pack(side="right")
    except Exception:
        pass

    drv_status_label = ctk.CTkLabel(drv_card, text="Driver Checker", font=ctk.CTkFont(size=12), text_color="#9fb3c8")
    drv_status_label.pack(anchor="w", padx=14, pady=(0, 8))

    drv_output_frame = ctk.CTkFrame(drv_card, fg_color="transparent")
    drv_output_frame.pack(fill="both", expand=False, padx=14, pady=(0,10))
    drv_output_labels = []

    # Status area (PASS / FAIL) for Drivers card — mirrors `card()` helper
    try:
        drv_status_frame = ctk.CTkFrame(drv_card, fg_color="#161b22", corner_radius=0)
        drv_status_frame.pack(side="bottom", fill="x", padx=14, pady=(6, 10))

        drv_status_display = ctk.CTkLabel(drv_status_frame, text="NOT RUN",
                                           font=ctk.CTkFont(size=11, weight="bold"),
                                           text_color="#9aa4b2")
        drv_status_display.pack(side="right", padx=(6, 12))

        _drv_pass_active = "#2ecc71"
        _drv_fail_active = "#ff6b6b"
        _drv_btn_inactive = "#2f3338"

        def drv_set_pass():
            try:
                drv_status_display.configure(text="PASS  ✔", text_color=_drv_pass_active)
                drv_pass_btn.configure(fg_color=_drv_pass_active)
                drv_fail_btn.configure(fg_color=_drv_btn_inactive)
                update_sidebar_status("drv", 'pass')
            except Exception:
                pass

        def drv_set_fail():
            try:
                drv_status_display.configure(text="FAIL  ✖", text_color=_drv_fail_active)
                drv_fail_btn.configure(fg_color=_drv_fail_active)
                drv_pass_btn.configure(fg_color=_drv_btn_inactive)
                update_sidebar_status("drv", 'fail')
            except Exception:
                pass


        drv_pass_btn = ctk.CTkButton(
            drv_status_frame,
            text="✔",
            width=34,
            height=34,
            fg_color=_drv_btn_inactive,
            hover_color="#28b463",
            corner_radius=18,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=drv_set_pass,
            text_color="white",
        )
        drv_pass_btn.pack(side="right", padx=(6, 4))

        drv_fail_btn = ctk.CTkButton(
            drv_status_frame,
            text="✖",
            width=34,
            height=34,
            fg_color=_drv_btn_inactive,
            hover_color="#ff5252",
            corner_radius=18,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=drv_set_fail,
            text_color="white",
        )
        drv_fail_btn.pack(side="right", padx=(6, 4))

        # Expose helpers on drv_card for programmatic control
        try:
            drv_card.set_pass = drv_set_pass
            drv_card.set_fail = drv_set_fail
            drv_card.status_display = drv_status_display
            drv_card.pass_btn = drv_pass_btn
            drv_card.fail_btn = drv_fail_btn
        except Exception:
            pass
    except Exception:
        pass

    def _reset_drv_card():
        try:
            # clear output labels
            for lbl in list(drv_output_labels):
                try:
                    lbl.destroy()
                except Exception:
                    pass
            drv_output_labels.clear()
            # reset status label
            ui_call(lambda: drv_status_label.configure(text="Driver Checker", text_color="#9fb3c8"))
            # reset card button states to NOT RUN
            try:
                ui_call(lambda: drv_card.status_display.configure(text="NOT RUN", text_color="#9aa4b2"))
                ui_call(lambda: drv_card.pass_btn.configure(fg_color="#2f3338"))
                ui_call(lambda: drv_card.fail_btn.configure(fg_color="#2f3338"))
            except Exception:
                pass
        except Exception:
            pass

    def _append_drv_line(line):
        try:
            lbl = ctk.CTkLabel(drv_output_frame, text=line.strip(), font=ctk.CTkFont(size=10), text_color="#d4af37", justify="left", wraplength=600)
            lbl.pack(anchor="w", pady=2)
            drv_output_labels.append(lbl)
            # keep the list from growing indefinitely
            if len(drv_output_labels) > 20:
                old = drv_output_labels.pop(0)
                try:
                    old.destroy()
                except Exception:
                    pass
        except Exception:
            pass

    def _run_drivers_check():
        # Write the provided PowerShell script to a temp file and execute it
        # PowerShell script: only list devices with ConfigManagerErrorCode != 0
        # Output is plain lines (device names) or a special marker NO_MISSING_DRIVERS
        ps_script = r"""
$ErrorActionPreference = 'Stop'

try {
    $pnpDevices = Get-WmiObject Win32_PnPEntity | Where-Object { $_.ConfigManagerErrorCode -ne 0 }
    if (-not $pnpDevices -or $pnpDevices.Count -eq 0) {
        Write-Output "NO_MISSING_DRIVERS"
        exit 0
    }
    foreach ($device in $pnpDevices) {
        # Output only the device name on each line for concise parsing
        Write-Output $device.Name
    }
    exit 0
}
catch {
    Write-Output "ERROR: Driver check failed: $_"
    exit 2
}
"""
        try:
            tf = tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False)
            tf.write(ps_script)
            tf.flush()
            tf.close()
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", tf.name]
            rc, out = run_process_capture(cmd, shell=False)
            # Parse output: if special marker NO_MISSING_DRIVERS appears -> show friendly message
            lines = [(ln or "").strip() for ln in (out or "").splitlines()]
            ui_lines = []
            ui_lines.append("Checking for missing drivers...")
            if rc == 0 and (not lines or (len(lines) == 1 and lines[0] == "NO_MISSING_DRIVERS")):
                ui_lines.append("No devices with missing drivers found.")
            elif rc == 0:
                ui_lines.append("Found the following devices with missing/problematic drivers:")
                for ln in lines:
                    if ln and not ln.upper().startswith("NO_MISSING_DRIVERS"):
                        ui_lines.append(f"  - {ln}")
            else:
                # Error case: show raw output for debugging
                ui_lines.append("Driver check encountered an error:")
                for ln in lines:
                    ui_lines.append(ln)

            for l in ui_lines:
                _append_drv_line(l)
            # Auto-mark the Drivers card pass/fail
            try:
                if rc == 0 and (not lines or (len(lines) == 1 and lines[0] == "NO_MISSING_DRIVERS")):
                    ui_call(lambda: hasattr(drv_card, 'set_pass') and drv_card.set_pass())
                else:
                    ui_call(lambda: hasattr(drv_card, 'set_fail') and drv_card.set_fail())
            except Exception:
                pass
        except Exception as e:
            _append_drv_line(f"Error starting driver check: {e}")
        finally:
            try:
                os.unlink(tf.name)
            except Exception:
                pass

    # Start driver check automatically (no manual button)
    try:
        app.after(0, lambda: threading.Thread(target=_run_drivers_check, daemon=True).start())
        app.after(0, lambda: threading.Thread(target=_run_gpu_check, daemon=True).start())
    except Exception:
        try:
            threading.Thread(target=_run_drivers_check, daemon=True).start()
            threading.Thread(target=_run_gpu_check, daemon=True).start()
        except Exception:
            pass

    # GPU card (right)
    gpu_card = ctk.CTkFrame(row_frame, fg_color="#161b22", corner_radius=10,
                            border_width=1, border_color="#30363d")
    gpu_card.pack(side="left", fill="both", expand=True, padx=(5,0))

    
    header_row_gpu = ctk.CTkFrame(gpu_card, fg_color="transparent")
    header_row_gpu.pack(fill="x", padx=14, pady=(10,6))
    ctk.CTkLabel(header_row_gpu, text="🎮  GPU", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff").pack(side="left")
    
    def _gpu_refresh_clicked():
        try:
            _reset_gpu_card()
            threading.Thread(target=_run_gpu_check, daemon=True).start()
        except Exception:
            pass
            
    try:
        ctk.CTkButton(header_row_gpu, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=_gpu_refresh_clicked).pack(side="right")
    except Exception:
        pass

    gpu_status_label = ctk.CTkLabel(gpu_card, text="Graphics Controller", font=ctk.CTkFont(size=12), text_color="#9fb3c8")
    gpu_status_label.pack(anchor="w", padx=14, pady=(0, 8))

    gpu_output_frame = ctk.CTkFrame(gpu_card, fg_color="transparent")
    gpu_output_frame.pack(fill="both", expand=False, padx=14, pady=(0,10))
    gpu_output_labels = []

    # Status area for GPU card (Pass/Fail)
    try:
        gpu_status_frame = ctk.CTkFrame(gpu_card, fg_color="#161b22", corner_radius=0)
        gpu_status_frame.pack(side="bottom", fill="x", padx=14, pady=(6, 10))

        gpu_status_display = ctk.CTkLabel(gpu_status_frame, text="NOT RUN",
                                           font=ctk.CTkFont(size=11, weight="bold"),
                                           text_color="#9aa4b2")
        gpu_status_display.pack(side="right", padx=(6, 12))

        _gpu_pass_active = "#2ecc71"
        _gpu_fail_active = "#ff6b6b"
        _gpu_btn_inactive = "#2f3338"

        def gpu_set_pass():
            try:
                gpu_status_display.configure(text="PASS  ✔", text_color=_gpu_pass_active)
                gpu_pass_btn.configure(fg_color=_gpu_pass_active)
                gpu_fail_btn.configure(fg_color=_gpu_btn_inactive)
                update_sidebar_status("gpu", 'pass')
            except Exception:
                pass

        def gpu_set_fail():
            try:
                gpu_status_display.configure(text="FAIL  ✖", text_color=_gpu_fail_active)
                gpu_fail_btn.configure(fg_color=_gpu_fail_active)
                gpu_pass_btn.configure(fg_color=_gpu_btn_inactive)
                update_sidebar_status("gpu", 'fail')
            except Exception:
                pass

        gpu_pass_btn = ctk.CTkButton(
            gpu_status_frame,
            text="✔",
            width=34,
            height=34,
            fg_color=_gpu_btn_inactive,
            hover_color="#28b463",
            corner_radius=18,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=gpu_set_pass,
            text_color="white",
        )
        gpu_pass_btn.pack(side="right", padx=(6, 4))

        gpu_fail_btn = ctk.CTkButton(
            gpu_status_frame,
            text="✖",
            width=34,
            height=34,
            fg_color=_gpu_btn_inactive,
            hover_color="#ff5252",
            corner_radius=18,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=gpu_set_fail,
            text_color="white",
        )
        gpu_fail_btn.pack(side="right", padx=(6, 4))
        
        gpu_card.set_pass = gpu_set_pass
        gpu_card.set_fail = gpu_set_fail
    except Exception:
        pass

    def _reset_gpu_card():
        try:
            for lbl in list(gpu_output_labels):
                try: lbl.destroy()
                except Exception: pass
            gpu_output_labels.clear()
            ui_call(lambda: gpu_status_label.configure(text="Graphics Controller", text_color="#9fb3c8"))
        except Exception: pass

    def _append_gpu_line(line):
        try:
            lbl = ctk.CTkLabel(gpu_output_frame, text=line.strip(), font=ctk.CTkFont(size=10), text_color="#d4af37", justify="left", wraplength=600)
            lbl.pack(anchor="w", pady=2)
            gpu_output_labels.append(lbl)
            if len(gpu_output_labels) > 10:
                old = gpu_output_labels.pop(0)
                try: old.destroy()
                except Exception: pass
        except Exception: pass

    def _run_gpu_check():
        try:
            # GPU logic pulled from system info: identifiers like gpu, graphics, video controller
            ps_cmd = "Get-CimInstance Win32_VideoController | Select-Object Name | ForEach-Object { $_.Name }"
            out = run_powershell(ps_cmd).strip()
            if not out or out == "Not Available":
                ui_call(lambda: _append_gpu_line("No GPU info found."))
                ui_call(lambda: gpu_set_fail() if 'gpu_set_fail' in locals() else None)
                return
            
            ui_call(lambda: gpu_set_pass() if 'gpu_set_pass' in locals() else None)
            for line in out.splitlines():
                if line.strip():
                    ui_call(lambda ln=line: _append_gpu_line(ln))
        except Exception as e:
            ui_call(lambda: _append_gpu_line(f"Error: {e}"))

    # Bottom padding
    # ══════════════════════════════════════════════════════════════════
    # VIRUS SCAN CARD (runs windef.ps1 with live output)
    # ══════════════════════════════════════════════════════════════════
    vs_card = card(body, "🦠  Virus Scan", track_key="vs")
    # Replace default title with Drivers-style header + small refresh icon
    try:
        try:
            first_child = vs_card.winfo_children()[0]
            try:
                first_child.destroy()
            except Exception:
                pass
        except Exception:
            pass
        header_row = ctk.CTkFrame(vs_card, fg_color="transparent")
        header_row.pack(fill="x", padx=14, pady=(10,6))
        ctk.CTkLabel(header_row, text="🦠  Virus Scan", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff").pack(side="left")
        try:
            ctk.CTkButton(header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=lambda: threading.Thread(target=_start_windef, daemon=True).start()).pack(side="right")
        except Exception:
            pass
    except Exception:
        pass

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
                saw_no_threats = False
                saw_threat_or_error = False
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
                        lower_line = line.lower()
                        if "no threats detected" in lower_line:
                            saw_no_threats = True
                        if ("threat" in lower_line and "no threats detected" not in lower_line) or "error" in lower_line:
                            saw_threat_or_error = True
                        ui_call(_add_vs_output_line, line)
                    
                    try:
                        stderr = (proc.stderr.read() if proc.stderr else "") or ""
                        if stderr.strip():
                            saw_threat_or_error = True
                            for ln in stderr.splitlines(True):
                                ui_call(_add_vs_output_line, f"[Error] {ln}")
                    except Exception:
                        pass
                finally:
                    rc = proc.poll() or 0
                    if rc != 0 or saw_threat_or_error:
                        status_text = "✗ Threat detected or scan error"
                        color = "#ff7b72"
                        try:
                            ui_call(lambda: hasattr(vs_card, 'set_fail') and vs_card.set_fail())
                        except Exception:
                            pass
                    elif saw_no_threats:
                        status_text = "✓ No threats detected"
                        color = "#7ee787"
                        try:
                            ui_call(lambda: hasattr(vs_card, 'set_pass') and vs_card.set_pass())
                        except Exception:
                            pass
                    else:
                        status_text = "✗ Unable to confirm scan result"
                        color = "#ff7b72"
                        try:
                            ui_call(lambda: hasattr(vs_card, 'set_fail') and vs_card.set_fail())
                        except Exception:
                            pass
                    ui_call(lambda: vs_status.configure(text=status_text, text_color=color))

            threading.Thread(target=_reader, daemon=True).start()
        except Exception as e:
            app.after(0, lambda: _add_vs_output_line(f"Error launching windef.ps1: {e}"))
            app.after(0, lambda: vs_status.configure(text="Error starting script", text_color="#ff7b72"))

    # Retry button moved to header (small ⟳) to match Drivers card

    threading.Thread(target=_start_windef, daemon=True).start()

    ctk.CTkLabel(body, text="", height=16).pack()

    # Final pass: ensure specific cards have a small header refresh icon like Drivers
    try:
        def _ensure_header_refresh(card, title_prefix, cmd):
            try:
                for child in card.winfo_children():
                    # find the header frame by looking for a label with matching prefix
                    try:
                        for sub in child.winfo_children():
                            txt = getattr(sub, 'cget', lambda k: '')('text') if hasattr(sub, 'cget') else ''
                            if isinstance(txt, str) and txt.strip().startswith(title_prefix):
                                # found header frame
                                # check for existing button
                                has_btn = any((hasattr(s, 'cget') and s.cget('text') == '⟳') for s in child.winfo_children())
                                if not has_btn:
                                    try:
                                        ctk.CTkButton(child, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=cmd).pack(side="right")
                                    except Exception:
                                        pass
                                return
                    except Exception:
                        pass
                # if not found, create a small header at top
                try:
                    header = ctk.CTkFrame(card, fg_color="transparent")
                    header.pack(fill="x", padx=14, pady=(10,6), before=(card.winfo_children()[0] if card.winfo_children() else None))
                    ctk.CTkLabel(header, text=title_prefix.strip(), font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff").pack(side="left")
                    try:
                        ctk.CTkButton(header, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=cmd).pack(side="right")
                    except Exception:
                        pass
                except Exception:
                    pass
            except Exception:
                pass

        # Audio changer: title starts with the emoji
        _ensure_header_refresh(ag_card, "🔈  Audio Changer", _run_audiog_clicked)
        # System Info
        _ensure_header_refresh(sys_card, "🖥️  System Info", _start_system_info_once)

        # Clean up any empty frames that are purely placeholders causing blank gaps
        for chk_card in (ag_card, sys_card):
            try:
                for ch in list(chk_card.winfo_children()):
                    try:
                        if isinstance(ch, ctk.CTkFrame) and len(ch.winfo_children()) == 0:
                            ch.destroy()
                    except Exception:
                        pass
            except Exception:
                pass
    except Exception:
        pass


    # ══════════════════════════════════════════════════════════════════
    # POPULATE SIDEBAR (at end so widgets exist)
    # ══════════════════════════════════════════════════════════════════
    add_sidebar_item("ag",   "🔈 Audio Changer",  ag_card)
    add_sidebar_item("sys",  "🖥️ System Info",     sys_card)
    add_sidebar_item("comp", "🧩 Components",      comp_card)
    add_sidebar_item("bat",  "🔋 Battery",         bat_card)
    add_sidebar_item("spk",  "🔊 Speaker",         spk_card)
    add_sidebar_item("mic",  "🎙️ Microphone",      mic_card)
    add_sidebar_item("br",   "☀️ Brightness",      brightness_card)
    add_sidebar_item("port", "🔌 Port Checker",    port_card)
    add_sidebar_item("tp",   "🖱️ Touchpad",        tp_card)
    add_sidebar_item("ts",   "👆 Touchscreen",     touchscreen_card)
    add_sidebar_item("px",   "🟥 Pixel Test",      pixel_card)
    add_sidebar_item("cam",  "📷 Camera",          cam_card)
    add_sidebar_item("kb",   "⌨️ Keyboard",        kb_card)
    add_sidebar_item("act",  "✅ Activation",      act_card)
    add_sidebar_item("drv",  "💾 Drivers",         drv_card)
    add_sidebar_item("gpu",  "🎮 GPU",             gpu_card)
    add_sidebar_item("vs",   "🛡️ Virus Scan",      vs_card)

    # ──────────────────────────────────────────────────────────────────
    # SEQUENCE RUNNER: run cards in order, waiting for PASS/FAIL before next
    sequence_keys = [
        "ag", "sys", "comp", "bat", "spk", "mic", "br", "tp",
        "port", "ts", "px", "cam", "kb", "act", "drv", "gpu", "vs"
    ]

    def _get_card_by_key(key):
        try:
            return {
                'ag': ag_card,
                'sys': sys_card,
                'comp': comp_card,
                'bat': bat_card,
                'spk': spk_card,
                'mic': mic_card,
                'br': brightness_card,
                'tp': tp_card,
                'port': port_card,
                'ts': touchscreen_card,
                'px': pixel_card,
                'cam': cam_card,
                'kb': kb_card,
                'act': act_card,
                'drv': drv_card,
                'gpu': gpu_card,
                'vs': vs_card,
            }.get(key)
        except Exception:
            return None

    def _extract_card_result(text):
        txt = str(text or "").upper()
        if "FAIL" in txt or "✖" in txt or "✗" in txt:
            return "fail"
        if "PASS" in txt or "✔" in txt or "✓" in txt:
            return "pass"
        return None

    def _reset_card_status(card):
        def _reset():
            if not widget_exists(card):
                return
            try:
                if hasattr(card, 'status_display'):
                    card.status_display.configure(text="NOT RUN", text_color="#9aa4b2")
            except Exception:
                pass
            try:
                if hasattr(card, 'pass_btn'):
                    card.pass_btn.configure(fg_color="#2f3338")
            except Exception:
                pass
            try:
                if hasattr(card, 'fail_btn'):
                    card.fail_btn.configure(fg_color="#2f3338")
            except Exception:
                pass
            try:
                track_key = getattr(card, 'track_key', None)
                if track_key:
                    update_sidebar_status(track_key, 'none')
            except Exception:
                pass
            try:
                setattr(card, '_last_status_time', 0)
            except Exception:
                pass

        try:
            ui_call_wait(_reset, timeout=1.0)
        except Exception:
            pass

    def _get_card_status_text(card):
        def _read_status():
            if not widget_exists(card):
                return None
            if hasattr(card, 'status_display'):
                try:
                    return str(card.status_display.cget('text'))
                except Exception:
                    pass
            for ch in card.winfo_children():
                try:
                    if hasattr(ch, 'cget'):
                        txt = str(ch.cget('text'))
                        if any(tok in txt for tok in ('PASS', 'FAIL', '✓', '✗', 'NOT RUN')):
                            return txt
                except Exception:
                    pass
            return None

        try:
            return ui_call_wait(_read_status, timeout=1.0)
        except Exception:
            return None

    def _wait_for_card_result(card, timeout=300, run_id=None, min_time=None):
        start = time.time()
        if min_time is None:
            min_time = 0
        while time.time() - start < timeout:
            try:
                if run_id is not None and run_id != _sequence_run_id[0]:
                    _log_sequence("wait aborted: stale sequence run")
                    return None
                txt = _get_card_status_text(card) or ""
                if _extract_card_result(txt):
                    # ensure the result was set after the wait began (avoid stale PASS/FAIL)
                    try:
                        last = getattr(card, '_last_status_time', 0) or 0
                    except Exception:
                        last = 0
                    if last >= min_time:
                        _log_sequence(f"wait result for card: {txt}")
                        return txt
                    else:
                        # ignore stale result and continue waiting
                        pass
                if not _sequence_running[0]:
                    _log_sequence("wait aborted: sequence cancelled")
                    return None
            except Exception:
                pass
            time.sleep(0.25)
            if active_screen is None or not widget_exists(active_screen):
                _log_sequence("wait aborted: active screen missing")
                return None
        _log_sequence("wait timed out with no pass/fail result")
        return None

    def _start_card_by_key(key):
        try:
            _log_sequence(f"start card requested: {key}")
            if key == 'ag':
                # run audio changer
                try:
                    app.after(0, _run_audiog_clicked)
                except Exception:
                    threading.Thread(target=_start_audiog, daemon=True).start()
                return True
            if key == 'sys':
                app.after(0, _start_system_info_once)
                return True
            if key == 'comp':
                # Components depend on System Info; nothing to start
                return True
            if key == 'bat':
                threading.Thread(target=_bat_refresh, daemon=True).start()
                return True
            if key == 'spk':
                _log_sequence("starting speaker playback")
                try: app.after(0, _spk_play)
                except Exception: _spk_play()
                return True
            if key == 'mic':
                try:
                    try:
                        tester = mic_tester
                    except NameError:
                        tester = None
                    if tester is not None:
                        if hasattr(tester, 'start_test'):
                            tester.start_test()
                        elif hasattr(tester, 'start'):
                            tester.start()
                        elif hasattr(tester, 'run_test'):
                            tester.run_test()
                    return True
                except Exception:
                    return False
            if key == 'br':
                threading.Thread(target=_start_brightness_test, daemon=True).start()
                return True
            if key == 'tp':
                app.after(0, _start_touchpad_embed)
                return True
            if key == 'ts':
                app.after(0, _run_touchscreen_test)
                return True
            if key == 'px':
                app.after(0, _start_pixel_test)
                return True
            if key == 'cam':
                threading.Thread(target=_start_camera_preview, daemon=True).start()
                return True
            if key == 'kb':
                app.after(0, _start_keyboard_module)
                return True
            if key == 'act':
                threading.Thread(target=_load_activation_status, daemon=True).start()
                return True
            if key == 'drv':
                threading.Thread(target=_run_drivers_check, daemon=True).start()
                return True
            if key == 'gpu':
                threading.Thread(target=_run_gpu_check, daemon=True).start()
                return True
            if key == 'vs':
                threading.Thread(target=_start_windef, daemon=True).start()
                return True
        except Exception:
            _log_sequence(f"start card exception: {traceback.format_exc()}")
            pass
        return False

    def _run_full_sequence(start_key=None, run_id=None):
        try:
            if run_id is None:
                run_id = _sequence_run_id[0]
            _log_sequence("sequence run started")
            # build ordered list of existing cards
            keys = [k for k in sequence_keys if _get_card_by_key(k) is not None]
            if start_key and start_key in keys:
                idx = keys.index(start_key)
            else:
                idx = 0
            while idx < len(keys) and _sequence_running[0] and run_id == _sequence_run_id[0]:
                key = keys[idx]
                card = _get_card_by_key(key)
                if card is None:
                    _log_sequence(f"sequence skip missing card: {key}")
                    idx += 1
                    continue
                # highlight and start
                _log_sequence(f"sequence entering card: {key}")
                if key != 'comp':
                    _reset_card_status(card)
                ui_call(lambda c=card: _highlight_and_show(c))
                _start_card_by_key(key)
                # wait for operator to mark pass/fail (or automatic set)
                min_time = time.time()
                result = _wait_for_card_result(card, timeout=300, run_id=run_id, min_time=min_time)
                _log_sequence(f"sequence leaving card: {key} result={result!r}")
                # small pause before next
                time.sleep(0.5)
                idx += 1
            if run_id == _sequence_run_id[0]:
                _sequence_running[0] = False
                _log_sequence("sequence run finished")
                _set_sequence_button_idle()
                _clear_highlight()
        except Exception:
            _log_sequence(f"sequence run exception: {traceback.format_exc()}")
            if run_id == _sequence_run_id[0]:
                _sequence_running[0] = False
                _set_sequence_button_idle()
    # GLOBAL REFRESH — rerun every auto-refreshable card
    # ──────────────────────────────────────────────────────────────────
    def _do_global_refresh():
        if _refresh_running[0]:
            return
        _refresh_running[0] = True
        try:
            _global_refresh_btn.configure(text="...", state="disabled", text_color="#888888")
        except Exception:
            pass
        _log_sequence("summary refresh requested: restarting tests and sequence")
        _cancel_sequence()

        def _reset_for_restart():
            try:
                stop_speaker_test()
            except Exception:
                pass
            try:
                _stop_brightness_test()
            except Exception:
                pass
            try:
                _stop_touchpad_embed()
            except Exception:
                pass
            try:
                _stop_touchscreen_test()
            except Exception:
                pass
            try:
                _stop_pixel_test()
            except Exception:
                pass
            try:
                _stop_camera_preview_local()
            except Exception:
                pass
            try:
                _stop_keyboard_module()
            except Exception:
                pass

            for key in list(status_indicators):
                update_sidebar_status(key, 'none')

            for key in sequence_keys:
                if key == 'comp':
                    continue
                try:
                    card = _get_card_by_key(key)
                    if card is not None:
                        _reset_card_status(card)
                except Exception:
                    pass

            _clear_highlight()

        def _restart_sequence():
            try:
                _reset_for_restart()
                _start_new_sequence()
            finally:
                _refresh_running[0] = False
                try:
                    _global_refresh_btn.configure(text="⟳", state="normal", text_color="#58a6ff")
                except Exception:
                    pass

        try:
            app.after(400, _restart_sequence)
        except Exception:
            _restart_sequence()


# Search helpers removed (search UI not present in hardware screen)


# ------------------------------------------------------------------
# Start app
# ------------------------------------------------------------------
# Schedule showing the hardware screen after the Tk main loop starts
# so background threads can safely use `app.after`.
app.after(0, show_hardware_test_screen)
app.mainloop()




