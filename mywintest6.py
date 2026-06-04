import customtkinter as ctk
import tkinter as tk
import os
import sys
import ctypes
import difflib
import json
import subprocess
import threading
import time
from tkinter import messagebox, ttk
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
_kb2_path = _os.path.join(_os.path.dirname(__file__), "KeyboardTesterGUI2.py")
_spec = _importlib_util.spec_from_file_location("KeyboardTesterGUI2", _kb2_path)
KeyboardTesterGUI2 = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(KeyboardTesterGUI2)

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
    global _speaker_after_id, _speaker_process, _speaker_backend, _speaker_pygame
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
    if _speaker_backend == "pygame" and _speaker_pygame is not None:
        try:
            if _speaker_pygame.mixer.get_init():
                _speaker_pygame.mixer.music.stop()
        except Exception:
            pass
    _speaker_backend = None


def start_speaker_playback(on_finished):
    global _speaker_after_id, _speaker_process, _speaker_backend, _speaker_pygame
    stop_speaker_test()
    mp3_path = os.path.join(BASE, "st.mp3")
    if not os.path.exists(mp3_path):
        messagebox.showwarning("Missing File", f"Cannot find:\n{mp3_path}")
        return False

    try:
        import pygame
        _speaker_pygame = pygame
        if not _speaker_pygame.mixer.get_init():
            _speaker_pygame.mixer.init()
        _speaker_pygame.mixer.music.load(mp3_path)
        _speaker_pygame.mixer.music.play()
        _speaker_backend = "pygame"
    except Exception as pygame_exc:
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
                "Could not play ST.MP3.\n\n"
                f"Pygame error: {pygame_exc}\n\n"
                f"PowerShell error: {ps_exc}"
            )
            stop_speaker_test()
            return False

    def poll_playback():
        global _speaker_after_id, _speaker_process, _speaker_backend
        if active_screen is None or not active_screen.winfo_exists():
            stop_speaker_test()
            return

        if _speaker_backend == "pygame":
            try:
                if _speaker_pygame is not None and _speaker_pygame.mixer.music.get_busy():
                    _speaker_after_id = app.after(350, poll_playback)
                    return
            except Exception:
                pass
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
                        "Could not play ST.MP3 with PowerShell backend.\n\n"
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
        text="Playing ST.MP3 now...",
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
        status_label.configure(text="Playing ST.MP3 now...")
        restart_button.configure(state="disabled")
        menu_button.configure(state="disabled")
        started = start_speaker_playback(on_finished)
        if not started:
            status_label.configure(text="Could not start ST.MP3. Check file location.")
            menu_button.configure(state="normal")

    restart_button.configure(command=restart_test)
    restart_test()


# ------------------------------------------------------------------
# Menus
# ------------------------------------------------------------------

# --- BEGIN: Stubs and helpers for missing PG15 features ---

def run_powershell_script(script_name):
    script_path = os.path.join(BASE, script_name)

    if not os.path.exists(script_path):
        return f"Missing PowerShell script:\n{script_name}"

    try:
        # Try common PowerShell executable names, then fall back to System32 path
        exe_candidates = ["powershell", "powershell.exe", "pwsh"]
        result = None
        last_exc = None
        for exe in exe_candidates:
            try:
                result = subprocess.run(
                    [exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path],
                    capture_output=True, text=True, timeout=300
                )
                break
            except Exception as e:
                last_exc = e

        if result is None:
            # Try absolute Windows PowerShell path
            try:
                system_pw = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "System32", "WindowsPowerShell", "v1.0", "powershell.exe")
                result = subprocess.run([system_pw, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path], capture_output=True, text=True, timeout=300)
            except Exception as e:
                raise last_exc or e
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

def append_console_text(textbox, text):
    textbox.configure(state="normal")
    textbox.insert("end", text)
    textbox.see("end")
    textbox.configure(state="disabled")

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

def open_system_info():
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
        command=return_to_main_menu,
        state="disabled"
    )
    return_button.pack(pady=(0, 14))

    def finish_screen():
        status_label.configure(text="Done. Press Enter to go back to the main menu.")
        return_button.configure(state="normal")
        app.bind("<Return>", return_to_main_menu)
        app.focus_force()

    def load_report():
        try:
            script_path = os.path.join(BASE, "HPLENDELLDEV6.ps1")
            if not os.path.exists(script_path):
                report = f"Error: Script not found at {script_path}"
            else:
                # The script ends with Read-Host which waits for input, so provide a newline to stdin
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    input="\n"
                )
                output = (result.stdout or "").strip()
                error = (result.stderr or "").strip()

                if result.returncode != 0:
                    report = f"PowerShell Error (Exit Code {result.returncode}):\n{error if error else output}"
                elif output:
                    report = output
                else:
                    report = "No output returned from PowerShell script.\n\nCheck if HPLENDELLDEV6.ps1 is working correctly."
        except Exception as e:
            report = f"Exception during script execution:\n{str(e)}"

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
    # Menus removed — fallback to hardware screen. When legacy code calls
    # render_simple_menu we simply go back to the hardware-only UI.
    try:
        show_hardware_test_screen()
    except Exception:
        pass

def render_account_menu():
    render_simple_menu("ACCOUNT SETTINGS", [
        ("Manage Users", lambda: run_cmd("start ms-settings:otherusers")),
        ("Delete User Account", lambda: run_tool("DELETEACCOUNT.BAT")),
        ("Create Local Account", lambda: run_tool("ACCOUNT.BAT")),
    ])

def render_settings_menu():
    render_simple_menu("SETTINGS / SECURITY", [
        ("Camera Settings", show_camera_test_screen),
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
        capture_output=True, text=True, timeout=20,
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
                device_label.configure(text="No battery detected")
                level_value.configure(text="--%", text_color="#ff7b72")
                level_bar["value"] = 0
                health_label.configure(text="Battery health: Unavailable")
                status_label.configure(text="Status: Unavailable")
                capacity_label.configure(text="Capacity: Unavailable")
                cycle_label.configure(text="Cycle count: Unavailable")
                message_label.configure(text="This system may be a desktop or may not expose battery data.")
                return
            lv = data["level"] if isinstance(data["level"], int) else 0
            color = _level_color(lv)
            device_label.configure(text=data["name"])
            level_value.configure(text=data["level_text"], text_color=color)
            level_bar["value"] = lv
            style.configure("Battery.Horizontal.TProgressbar", background=color)
            health_label.configure(text=f"Battery health: {data['health_text']}")
            status_label.configure(text=f"Status: {data['status_text']}")
            capacity_label.configure(text=f"Capacity: {data['capacity_text']}")
            cycle_label.configure(text=f"Cycle count: {data['cycle_text']}")
            message_label.configure(text="")
        except Exception as exc:
            message_label.configure(text=str(exc))

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
    ctk.CTkLabel(top_bar, text="Hardware Test Suite — Revision 0.05: Added Component Check Section ",
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
        return f

    # ══════════════════════════════════════════════════════════════════
    # 1. SYSTEM INFO CARD (embedded module)
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
        script_path = os.path.join(BASE, "HPLENDELLDEV6.ps1")
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
                bat_device.configure(text="No battery detected")
                bat_level_lbl.configure(text="--%", text_color="#ff7b72")
                bat_bar["value"] = 0
                bat_health_lbl.configure(text="Health: N/A")
                bat_status_lbl.configure(text="Status: N/A")
                bat_cycle_lbl.configure(text="Cycles: N/A")
                bat_cap_lbl.configure(text="Capacity: N/A")
                return
            lv = data["level"] if isinstance(data["level"], int) else 0
            color = _level_color(lv)
            bat_device.configure(text=data["name"])
            bat_level_lbl.configure(text=data["level_text"], text_color=color)
            bat_bar["value"] = lv
            bat_style.configure("HW.Horizontal.TProgressbar", background=color)
            bat_health_lbl.configure(text=f"Health: {data['health_text']}")
            bat_status_lbl.configure(text=f"Status: {data['status_text']}")
            bat_cycle_lbl.configure(text=f"Cycles: {data['cycle_text']}")
            bat_cap_lbl.configure(text=f"Capacity: {data['capacity_text']}")
        except Exception as e:
            bat_cap_lbl.configure(text=str(e))

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
        spk_status.configure(text="Playing ST.MP3...")
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
        text="Use this card for suite testing. Full-screen mic test is disabled here.",
        font=ctk.CTkFont(size=10),
        text_color="#666",
    )
    mic_note.pack(anchor="w", padx=14, pady=(0,10))

    # ══════════════════════════════════════════════════════════════════
    # 4. CAMERA CARD
    # ══════════════════════════════════════════════════════════════════
    cam_card = card(body, "📷  Camera Test")
    cam_status = ctk.CTkLabel(cam_card, text="Starting camera preview...",
                               font=ctk.CTkFont(size=12), text_color="#d4af37")
    cam_status.pack(anchor="w", padx=14, pady=(0,6))

    cam_preview_row = ctk.CTkFrame(cam_card, fg_color="transparent")
    cam_preview_row.pack(fill="x", padx=14, pady=(0,10))

    def _start_camera():
        try:
            import cv2
            from PIL import ImageTk
        except Exception:
            cam_status.configure(text="OpenCV not installed. Run: pip install opencv-python",
                                  text_color="#ff7b72")
            return

        def discover(max_scan=4, max_found=2):
            found = []
            for idx in range(max_scan):
                cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                if cap.isOpened():
                    found.append(idx)
                try: cap.release()
                except Exception: pass
                if len(found) >= max_found: break
            return found

        indexes = discover()
        if not indexes:
            cam_status.configure(text="No camera found.", text_color="#ff7b72")
            return

        preview_labels = []
        for idx in indexes:
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if not cap.isOpened():
                try: cap.release()
                except Exception: pass
                continue
            _cam_caps_local.append(cap)
            panel = tk.Frame(cam_preview_row, bg="#000000", width=300, height=220)
            panel.pack(side="left", padx=6)
            panel.pack_propagate(False)
            lbl = tk.Label(panel, bg="#000000")
            lbl.pack(fill="both", expand=True)
            preview_labels.append(lbl)

        if not _cam_caps_local:
            cam_status.configure(text="Could not open cameras.", text_color="#ff7b72")
            return

        names = ", ".join(f"Camera {i}" for i in indexes[:len(_cam_caps_local)])
        cam_status.configure(text=f"Live: {names}", text_color="#7ee787")

        def update():
            if active_screen is None or not active_screen.winfo_exists(): return
            for i, cap in enumerate(_cam_caps_local):
                if i >= len(preview_labels): continue
                ok, frame = cap.read()
                if not ok: continue
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img.thumbnail((300, 220))
                tk_img = ImageTk.PhotoImage(image=img)
                preview_labels[i].configure(image=tk_img)
                preview_labels[i].image = tk_img
            _cam_after_local[0] = app.after(33, update)

        update()

    threading.Thread(target=_start_camera, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════
    # 5. KEYBOARD CARD
    # ══════════════════════════════════════════════════════════════════
    kb_card = card(body, "⌨️  Keyboard Test")
    kb_status = ctk.CTkLabel(
        kb_card,
        text="Full keyboard map is embedded below.",
        font=ctk.CTkFont(size=12),
        text_color="#9fb3c8",
    )
    kb_status.pack(anchor="w", padx=14, pady=(0, 6))

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


def get_main_menu_sections():
    return [
        ("SYSTEM / HARDWARE", [
            ("System Info", open_system_info, ["system", "hardware", "info"]),
            ("Bitlocker Check", show_bitlocker_screen, ["bitlocker", "encryption"]),
            ("Hotkeys Test", lambda: run_tool("HK1.BAT"), ["hotkeys", "keyboard"]),
            ("Device Manager", lambda: run_cmd("devmgmt.msc"), ["device", "manager", "drivers"]),
            ("Hardware Test Suite", show_hardware_test_screen, ["battery", "speaker", "mic", "camera", "keyboard", "hardware", "test", "suite"]),
            ("Battery Test", show_hardware_test_screen, ["battery", "power", "suite"]),
            ("Speaker Test", show_hardware_test_screen, ["speaker", "audio", "sound", "suite"]),
            ("Mic Test", show_hardware_test_screen, ["mic", "microphone", "audio", "sound", "suite"]),
            ("Camera Test", show_hardware_test_screen, ["camera", "webcam", "suite"]),
            ("Windows Activation", lambda: run_tool("ACT.bat"), ["activation", "windows key"]),
            ("Keyboard Test", show_hardware_test_screen, ["keyboard", "kb", "double typing", "notepad", "suite"]),
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
            ("Camera Settings", show_camera_test_screen, ["camera", "settings", "webcam"]),
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
    # Menu removed — render_main_menu is intentionally a no-op when running
    # the application in "hardware-only" mode.
    return


# ------------------------------------------------------------------
# Start app
# ------------------------------------------------------------------
show_hardware_test_screen()
app.mainloop()