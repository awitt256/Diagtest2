import customtkinter as ctk
import tkinter as tk
import os
import sys
import ctypes
import json
import subprocess
import threading
import time
import platform
import socket
from tkinter import messagebox, ttk
from PIL import Image, ImageGrab
import tempfile
import winsound
import datetime

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

# Ensure venv site-packages is in sys.path for embedded microphone module loading
_venv_site_packages = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), ".venv", "Lib", "site-packages")
if _venv_site_packages not in sys.path:
    sys.path.insert(0, _venv_site_packages)

_mic_path = _os.path.join(_os.path.dirname(__file__), "MicTest2.py")
_mic_spec = _importlib_util.spec_from_file_location("MicTest2", _mic_path)
MicTest2 = _importlib_util.module_from_spec(_mic_spec)
try:
    _mic_spec.loader.exec_module(MicTest2)
except Exception:
    MicTest2 = None


# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BASE = os.path.dirname(os.path.abspath(__file__))
SEQUENCE_LOG = os.path.join(tempfile.gettempdir(), "mywintest36_sequence.log")

# Embedded CheckEnrollment.ps1 (Write-Output for stdout capture in the UI)
EMBEDDED_CHECK_ENROLLMENT_PS1 = r"""
Write-Output "========================================================="
Write-Output "  Enrollment and Computrace Check Built By Anthony Witt  "
Write-Output "========================================================="
Write-Output ""

function Write-Result {
    param(
        [string]$TestName,
        [bool]$IsFound,
        [array]$Details = @(),
        [array]$CheckedLocations = @()
    )

    $padLength = 22
    $paddedTestName = $TestName.PadRight($padLength)

    if ($IsFound) {
        Write-Output "$paddedTestName : Enrollment found (FAIL)"
        if ($Details.Count -gt 0) {
            foreach ($detail in $Details) {
                Write-Output "    [!] $detail"
            }
        }
    } else {
        Write-Output "$paddedTestName : No enrollment found (PASS)"
    }

    if ($CheckedLocations.Count -gt 0) {
        Write-Output "    --- Locations Checked ---"
        foreach ($loc in $CheckedLocations) {
            Write-Output "    $loc"
        }
    }
    Write-Output ""
}

$intuneFound = $false
$intuneDetails = @()
$intuneChecked = @(
    "Command: dsregcmd /status",
    "WMI Namespace: ROOT\CIMV2\mdm\dmmap (MDM_Client class)"
)

$dsreg = dsregcmd /status
if ($dsreg -match "MdmEnrolled\s*:\s*YES") {
    $intuneFound = $true
    $intuneDetails += "Found via Command: dsregcmd /status (MdmEnrolled : YES)"
}

$wmiMdm = Get-CimInstance -Namespace "ROOT\CIMV2\mdm\dmmap" -ClassName "MDM_Client" -ErrorAction SilentlyContinue
if ($wmiMdm) {
    $intuneFound = $true
    $intuneDetails += "Found via WMI Namespace: ROOT\CIMV2\mdm\dmmap (MDM_Client class)"
}

Write-Result -TestName "Intune / MDM Status" -IsFound $intuneFound -Details $intuneDetails -CheckedLocations $intuneChecked

$autopilotFound = $false
$autopilotDetails = @()
$autopilotPath = "HKLM:\SOFTWARE\Microsoft\Provisioning\Diagnostics\AutoPilot"
$autopilotChecked = @("Registry Key: $autopilotPath")

if (Test-Path $autopilotPath) {
    $autopilotProps = Get-ItemProperty -Path $autopilotPath -ErrorAction SilentlyContinue

    $tenantMatched = $autopilotProps.TenantMatched
    $tenantId = $autopilotProps.CloudAssignedTenantId

    if ($tenantMatched -eq 1 -or $tenantId) {
        $autopilotFound = $true
        $autopilotDetails += "Active Autopilot Configuration Found:"
        if ($tenantId) { $autopilotDetails += "  - Tenant ID: $tenantId" }
        if ($null -ne $tenantMatched) { $autopilotDetails += "  - Tenant Matched: $tenantMatched" }
    }
}

Write-Result -TestName "Autopilot Status" -IsFound $autopilotFound -Details $autopilotDetails -CheckedLocations $autopilotChecked

$computraceFound = $false
$computraceDetails = @()

$computraceFiles = @(
    "C:\Windows\System32\rpcnet.exe",
    "C:\Windows\System32\rpcnetp.exe",
    "C:\Windows\System32\rpcnet.dll",
    "C:\Windows\System32\rpcnetp.dll",
    "C:\Windows\SysWOW64\rpcnet.exe",
    "C:\Windows\SysWOW64\rpcnetp.exe",
    "C:\Windows\SysWOW64\rpcnet.dll",
    "C:\Windows\SysWOW64\rpcnetp.dll",
    "C:\Windows\System32\abtservice.exe",
    "C:\Windows\SysWOW64\abtservice.exe",
    "C:\Program Files (x86)\Absolute\abtservice.exe",
    "C:\Program Files (x86)\Absolute\abtagent.exe"
)

$computraceServices = @("rpcnet", "rpcnetp", "abtservice", "abtagent")
$computraceProcesses = @("rpcnet", "rpcnetp", "abtservice", "abtagent", "cgecs", "cgexe")

$computraceChecked = @()
$computraceChecked += "Files Checked:"
foreach ($f in $computraceFiles) { $computraceChecked += "  - $f" }
$computraceChecked += "Services Checked: " + ($computraceServices -join ", ")
$computraceChecked += "Processes Checked: " + ($computraceProcesses -join ", ")

foreach ($file in $computraceFiles) {
    if (Test-Path $file) {
        $computraceFound = $true
        $computraceDetails += "Found File: $file"
    }
}

foreach ($srv in $computraceServices) {
    $service = Get-Service -Name $srv -ErrorAction SilentlyContinue
    if ($service) {
        $computraceFound = $true
        $computraceDetails += "Found Service: $srv"
    }
}

foreach ($proc in $computraceProcesses) {
    $process = Get-Process -Name $proc -ErrorAction SilentlyContinue
    if ($process) {
        $computraceFound = $true
        $computraceDetails += "Found Running Process: $proc"
    }
}

Write-Result -TestName "Computrace / Absolute" -IsFound $computraceFound -Details $computraceDetails -CheckedLocations $computraceChecked

if ($intuneFound -or $autopilotFound -or $computraceFound) {
    Write-Output "ENROLLMENT_CHECK_RESULT:FAIL"
    exit 1
} else {
    Write-Output "ENROLLMENT_CHECK_RESULT:PASS"
    exit 0
}
"""


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
_timer_start_time = None
_timer_running = False
_timer_label = None
_timer_after_id = None
_card_widgets = {}
_card_screenshots = []
_enrollment_report_lines = []  # stores raw stdout lines from EnrollmentTest.ps1 for PDF


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


def start_timer():
    """Start the test timer"""
    global _timer_start_time, _timer_running, _timer_after_id
    if _timer_after_id:
        try:
            app.after_cancel(_timer_after_id)
        except Exception:
            pass
        _timer_after_id = None
    _timer_start_time = time.time()
    _timer_running = True
    try:
        if _timer_label is not None:
            _timer_label.configure(text="◷  00:00:00")
    except Exception:
        pass
    update_timer_display()

def update_timer_display():
    """Update the timer display"""
    global _timer_after_id, _timer_running
    if not _timer_running or _timer_label is None:
        return
    
    elapsed = time.time() - _timer_start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    timer_text = f"\u25f7  {hours:02d}:{minutes:02d}:{seconds:02d}"
    
    try:
        _timer_label.configure(text=timer_text)
    except Exception:
        pass
    
    # Schedule next update
    _timer_after_id = app.after(1000, update_timer_display)

def stop_timer():
    """Stop the test timer"""
    global _timer_running, _timer_after_id
    _timer_running = False
    if _timer_after_id:
        try:
            app.after_cancel(_timer_after_id)
        except Exception:
            pass
        _timer_after_id = None

def get_system_info():
    """Gather system information for the test report"""
    info = {
        'computer_name': os.environ.get('COMPUTERNAME', 'N/A'),
        'username': os.environ.get('USERNAME', 'N/A'),
        'os_name': platform.system() + ' ' + platform.release(),
        'os_version': platform.version(),
        'architecture': platform.machine(),
        'processor': platform.processor(),
        'hostname': socket.gethostname(),
    }
    
    # Try to get more detailed info via WMI/subprocess
    try:
        # Get CPU info
        result = subprocess.run(['wmic', 'cpu', 'get', 'Name', '/value'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if 'Name=' in line:
                    info['cpu_model'] = line.split('=', 1)[1].strip()
                    break
    except Exception:
        info['cpu_model'] = info['processor']
    
    try:
        # Get total memory
        result = subprocess.run(['wmic', 'computersystem', 'get', 'TotalPhysicalMemory', '/value'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if 'TotalPhysicalMemory=' in line:
                    mem_bytes = int(line.split('=', 1)[1].strip())
                    info['memory_gb'] = round(mem_bytes / (1024**3), 1)
                    break
    except Exception:
        info['memory_gb'] = 'N/A'
    
    try:
        # Get disk info
        result = subprocess.run(['wmic', 'diskdrive', 'get', 'Size,Model', '/value'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for i, line in enumerate(lines):
                if 'Model=' in line:
                    info['storage_model'] = line.split('=', 1)[1].strip()
                if 'Size=' in line:
                    size_bytes = int(line.split('=', 1)[1].strip())
                    info['storage_gb'] = round(size_bytes / (1024**3), 0)
                    break
    except Exception:
        info['storage_model'] = 'N/A'
        info['storage_gb'] = 'N/A'
    
    try:
        # Get GPU info
        result = subprocess.run(['wmic', 'path', 'win32_videocontroller', 'get', 'Name', '/value'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if 'Name=' in line:
                    info['gpu'] = line.split('=', 1)[1].strip()
                    break
    except Exception:
        info['gpu'] = 'N/A'
    
    try:
        # Get detailed battery info
        result = subprocess.run(['wmic', 'path', 'win32_battery', 'get', 
                               'EstimatedChargeRemaining,BatteryStatus,DesignCapacity,FullChargeCapacity',
                               '/value'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if 'EstimatedChargeRemaining=' in line:
                    charge = line.split('=', 1)[1].strip()
                    if charge and charge.isdigit():
                        info['battery_charge'] = charge + '%'
                if 'BatteryStatus=' in line:
                    status_code = line.split('=', 1)[1].strip()
                    if status_code:
                        # BatteryStatus codes: 1=Discharging, 2=On AC, 3=Fully Charged, etc.
                        status_map = {
                            '1': 'Discharging',
                            '2': 'On AC / Charging',
                            '3': 'Fully Charged',
                            '4': 'Low',
                            '5': 'Critical',
                            '6': 'Charging',
                            '7': 'Charging / High',
                            '8': 'Charging / Low',
                            '9': 'Charging / Critical',
                            '10': 'Undefined',
                            '11': 'Partially Charged',
                        }
                        info['battery_status'] = status_map.get(status_code, f'Code {status_code}')
                if 'DesignCapacity=' in line:
                    design = line.split('=', 1)[1].strip()
                    if design and design.isdigit():
                        info['battery_design_capacity'] = design
                if 'FullChargeCapacity=' in line:
                    full = line.split('=', 1)[1].strip()
                    if full and full.isdigit():
                        info['battery_full_charge'] = full
        
        # Check if battery exists and AC status
        result2 = subprocess.run(['wmic', 'path', 'win32_battery', 'get', 'Name', '/value'],
                               capture_output=True, text=True, timeout=5)
        if result2.returncode == 0:
            output = result2.stdout.strip()
            info['has_battery'] = 'Yes' if output and len(output) > 5 else 'No'
        else:
            info['has_battery'] = 'No'
        
        # Calculate health if we have both values
        if 'battery_design_capacity' in info and 'battery_full_charge' in info:
            try:
                design = int(info['battery_design_capacity'])
                full = int(info['battery_full_charge'])
                if design > 0:
                    info['battery_health'] = str(round((full / design) * 100)) + '%'
            except (ValueError, ZeroDivisionError):
                pass
        
        # Check if AC is connected via power supply
        result3 = subprocess.run(['wmic', 'path', 'win32_battery', 'get', 'BatteryStatus', '/value'],
                               capture_output=True, text=True, timeout=5)
        if result3.returncode == 0:
            for line in result3.stdout.strip().split('\n'):
                if 'BatteryStatus=' in line:
                    status = line.split('=', 1)[1].strip()
                    if status in ['2', '6', '7', '8', '9']:
                        info['ac_connected'] = 'Yes'
                    else:
                        info['ac_connected'] = 'No'
                    break
        
    except Exception as e:
        print(f"Battery info error: {e}")
        info['has_battery'] = 'Unknown'
        info['battery_charge'] = 'N/A'
        info['battery_status'] = 'N/A'
    
    try:
        # Get WiFi adapter
        result = subprocess.run(['wmic', 'nic', 'where', 'NetConnectionStatus=2', 'get', 'Name', '/value'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if 'Name=' in line:
                    info['wifi_adapter'] = line.split('=', 1)[1].strip()
                    break
            else:
                info['wifi_adapter'] = 'Not Connected'
    except Exception:
        info['wifi_adapter'] = 'N/A'
    
    try:
        # Check Windows activation
        result = subprocess.run(['cscript', '//Nologo', r'C:\Windows\System32\slmgr.vbs', '/xpr'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            output = result.stdout.lower()
            if 'permanently activated' in output or 'will expire' in output:
                info['windows_activated'] = 'Activated'
            else:
                info['windows_activated'] = 'Not Activated'
        else:
            info['windows_activated'] = 'Unknown'
    except Exception:
        info['windows_activated'] = 'Unknown'
    
    return info


def capture_card_screenshot(key):
    """Capture a screenshot of a specific card when it passes"""
    global _card_screenshots
    try:
        card = _card_widgets.get(key)
        if card is None or not card.winfo_exists():
            return
        
        # Ensure widget is rendered
        app.update_idletasks()
        time.sleep(0.1)
        
        # Get card position and size
        x = card.winfo_rootx()
        y = card.winfo_rooty()
        width = card.winfo_width()
        height = card.winfo_height()
        
        if width < 50 or height < 50:
            return
        
        # Capture the card area with a small padding
        padding = 4
        screenshot = ImageGrab.grab(bbox=(
            x - padding,
            y - padding,
            x + width + padding,
            y + height + padding
        ))
        
        # Save screenshot
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(
            tempfile.gettempdir(),
            f"card_{key}_{timestamp}.png"
        )
        screenshot.save(screenshot_path, "PNG")
        
        # Get display name from test mapping
        test_mapping = {
            'operator': 'Operator',
            'ag': 'Audio Changer',
            'sys': 'System Info',
            'comp': 'Components',
            'net': 'Network Adapters',
            'bat': 'Battery',
            'tp': 'Touchpad',
            'spk': 'Speaker',
            'mic': 'Microphone',
            'br': 'Brightness',
            'smartcard': 'Smart Card',
            'ts': 'Touchscreen',
            'px': 'Pixel Test',
            'cam': 'Camera',
            'kb': 'Keyboard',
            'act': 'Activation',
            'drv': 'Drivers',
            'enroll': 'Enrollment Check',
            'bios': 'BIOS Test',
            'wifi': 'WiFi Test',
            'usb': 'USB Test',
            'bluetooth': 'Bluetooth Test',
            'network': 'Network Test',
            'audio': 'Audio Test',
        }
        display_name = test_mapping.get(key, key)
        
        # Store reference
        _card_screenshots.append({
            'key': key,
            'name': display_name,
            'path': screenshot_path
        })
        
    except Exception as e:
        print(f"Failed to capture card screenshot for {key}: {e}")


def capture_full_scrollable_screenshot(timestamp):
    """Capture the full scrollable content by scrolling and taking multiple screenshots"""
    if active_screen is None:
        raise RuntimeError("No active screen")
    
    # Find the scrollable frame (body) within active_screen
    body = None
    canvas = None
    
    for child in active_screen.winfo_children():
        if isinstance(child, ctk.CTkFrame):
            for subchild in child.winfo_children():
                if hasattr(subchild, '_parent_canvas'):
                    body = subchild
                    canvas = subchild._parent_canvas
                    break
            if body:
                break
    
    if body is None or canvas is None:
        raise RuntimeError("Could not find scrollable frame")
    
    # Get the full scrollable height
    app.update_idletasks()
    bbox = canvas.bbox("all")
    if not bbox:
        raise RuntimeError("Canvas bbox not available")
    
    total_height = bbox[3] - bbox[1]
    
    # Get viewport dimensions
    viewport_height = canvas.winfo_height()
    
    # Save current scroll position
    current_yview = canvas.yview()
    
    # Get the main_container frame to capture full window
    main_container = None
    for child in active_screen.winfo_children():
        if isinstance(child, ctk.CTkFrame):
            main_container = child
            break
    
    if main_container is None:
        raise RuntimeError("Could not find main container")
    
    # Get window position
    win_x = app.winfo_rootx()
    win_y = app.winfo_rooty()
    win_width = app.winfo_width()
    win_height = app.winfo_height()
    
    # Scroll to top first
    canvas.yview_moveto(0)
    app.update_idletasks()
    time.sleep(0.3)
    
    # Capture screenshots while scrolling
    screenshot_paths = []
    scroll_pos = 0
    overlap = 80  # pixels of overlap between captures
    part_num = 1
    
    while scroll_pos < total_height:
        # Capture full window (includes top bar, sidebar, and visible body)
        screenshot = ImageGrab.grab(bbox=(win_x, win_y, win_x + win_width, win_y + win_height))
        screenshot_path = os.path.join(tempfile.gettempdir(), f"screenshot_part{part_num}_{timestamp}.png")
        screenshot.save(screenshot_path, "PNG")
        screenshot_paths.append(screenshot_path)
        part_num += 1
        
        # Calculate next scroll position
        scroll_pos += (viewport_height - overlap)
        
        if scroll_pos >= total_height:
            break
        
        # Scroll down
        fraction = min(1.0, scroll_pos / total_height)
        canvas.yview_moveto(fraction)
        app.update_idletasks()
        time.sleep(0.2)
    
    # Restore scroll position
    canvas.yview_moveto(current_yview[0])
    app.update_idletasks()
    
    return screenshot_paths


def take_screenshot_and_create_pdf(status_summary=None):
    """Create a comprehensive test report PDF matching the WindowsTest_Report format"""
    global _card_screenshots
    try:
        # Gather system info
        sys_info = get_system_info()
        
        # Create output directory
        output_dir = os.path.join(BASE, "TestResults")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"testresults_{timestamp}.pdf"
        pdf_path = os.path.join(output_dir, pdf_filename)
        
        # Calculate duration
        duration_text = "N/A"
        if _timer_start_time:
            elapsed = time.time() - _timer_start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            duration_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Take full-page screenshot by scrolling
        screenshot_paths = []
        try:
            screenshot_paths = capture_full_scrollable_screenshot(timestamp)
        except Exception as e:
            print(f"Full screenshot capture failed: {e}")
            # Fallback to single screenshot
            try:
                app.update_idletasks()
                time.sleep(0.3)
                screenshot = ImageGrab.grab()
                screenshot_path = os.path.join(tempfile.gettempdir(), f"screenshot_{timestamp}.png")
                screenshot.save(screenshot_path, "PNG")
                screenshot_paths = [screenshot_path]
            except Exception as e2:
                print(f"Fallback screenshot failed: {e2}")
        
        # Build PDF with reportlab
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch, mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, PageBreak, Image as RLImage
        from reportlab.platypus.tables import TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Color definitions
        HEADER_BG = colors.HexColor('#1a237e')
        HEADER_TEXT = colors.white
        SECTION_BG = colors.HexColor('#f5f5f5')
        BORDER_COLOR = colors.HexColor('#dddddd')
        PASS_GREEN = colors.HexColor('#4caf50')
        FAIL_RED = colors.HexColor('#f44336')
        
        # Helper function for section headers
        def add_section_header(title):
            header_style = ParagraphStyle(
                'SectionHeader',
                parent=styles['Heading3'],
                fontSize=11,
                textColor=HEADER_TEXT,
                alignment=TA_LEFT,
                spaceAfter=0,
                spaceBefore=10,
                leftIndent=5,
                leading=14
            )
            header_data = [[Paragraph(f"<b>{title}</b>", header_style)]]
            header_table = Table(header_data, colWidths=[doc.width])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HEADER_BG),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(header_table)
            story.append(Spacer(1, 3))
        
        # Helper for key-value rows
        def add_key_value_table(data, col_widths=None):
            if not col_widths:
                col_widths = [doc.width * 0.35, doc.width * 0.65]
            
            kv_style = ParagraphStyle(
                'KVStyle',
                parent=styles['Normal'],
                fontSize=9,
                leading=12,
                spaceAfter=0
            )
            
            table_data = []
            for key, value in data:
                table_data.append([
                    Paragraph(f"<b>{key}</b>", kv_style),
                    Paragraph(str(value), kv_style)
                ])
            
            if table_data:
                t = Table(table_data, colWidths=col_widths)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('LINEBELOW', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ]))
                story.append(t)
                story.append(Spacer(1, 5))
        
        # Title
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=HEADER_BG,
            alignment=TA_CENTER,
            spaceAfter=15,
            spaceBefore=0
        )
        story.append(Paragraph("Hardware Test Report", title_style))
        
        # Subtitle
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        story.append(Paragraph(
            f"Generated on {datetime.datetime.now().strftime('%A, %B %d, %Y - %I:%M:%S %p')}",
            subtitle_style
        ))
        
        # ── GENERAL DATA ──
        add_section_header("General Data")
        general_data = [
            ("Operator", _selected_operator[0] if _selected_operator[0] else "Not Selected"),
            ("Computer Name", sys_info.get('computer_name', 'N/A')),
            ("User", sys_info.get('username', 'N/A')),
            ("Operating System", sys_info.get('os_name', 'N/A')),
            ("OS Version", sys_info.get('os_version', 'N/A')),
            ("Architecture", sys_info.get('architecture', 'N/A')),
            ("Hostname", sys_info.get('hostname', 'N/A')),
            ("Test Duration", duration_text),
        ]
        add_key_value_table(general_data)
        
        # ── CPU ──
        add_section_header("CPU")
        cpu_data = [
            ("Model", sys_info.get('cpu_model', sys_info.get('processor', 'N/A'))),
        ]
        add_key_value_table(cpu_data)
        
        # ── MEMORY ──
        add_section_header("Memory")
        mem_data = [
            ("Total Capacity", f"{sys_info.get('memory_gb', 'N/A')} GB" if sys_info.get('memory_gb') else 'N/A'),
        ]
        add_key_value_table(mem_data)
        
        # ── STORAGE ──
        add_section_header("Storage")
        storage_data = [
            ("Model", sys_info.get('storage_model', 'N/A')),
            ("Capacity", f"{sys_info.get('storage_gb', 'N/A')} GB" if sys_info.get('storage_gb') else 'N/A'),
        ]
        add_key_value_table(storage_data)
        
        # ── GPU ──
        add_section_header("GPU")
        gpu_data = [
            ("Model", sys_info.get('gpu', 'N/A')),
        ]
        add_key_value_table(gpu_data)
        
        # ── WIRELESS ──
        add_section_header("Wireless")
        wireless_data = [
            ("WiFi Adapter", sys_info.get('wifi_adapter', 'N/A')),
        ]
        add_key_value_table(wireless_data)
        
        # ── BATTERY ──
        add_section_header("Battery")
        battery_data = [
            ("Has Battery", sys_info.get('has_battery', 'Unknown')),
            ("Charge Level", sys_info.get('battery_charge', 'N/A')),
            ("Charging Status", sys_info.get('battery_status', 'N/A')),
            ("AC Connected", sys_info.get('ac_connected', 'Unknown')),
            ("Status", sys_info.get('battery_status', 'N/A')),
            ("Health", sys_info.get('battery_health', 'N/A')),
        ]
        add_key_value_table(battery_data)
        
        # ── WINDOWS STATUS ──
        add_section_header("Windows Status")
        windows_data = [
            ("Operating System", sys_info.get('os_name', 'N/A')),
            ("Activation Status", sys_info.get('windows_activated', 'Unknown')),
        ]
        add_key_value_table(windows_data)
        
        # ── COMPONENTS ──
        add_section_header("Components")
        comp_style = ParagraphStyle(
            'CompStyle',
            parent=styles['Normal'],
            fontSize=9,
            leading=12
        )
        
        # Build components from status_summary
        comp_data = [['Description', 'Status']]
        test_mapping = {
            'operator': 'Operator',
            'ag': 'Audio Changer',
            'sys': 'System Info',
            'comp': 'Components',
            'net': 'Network Adapters',
            'bat': 'Battery',
            'tp': 'Touchpad',
            'spk': 'Speaker',
            'mic': 'Microphone',
            'br': 'Brightness',
            'smartcard': 'Smart Card',
            'ts': 'Touchscreen',
            'px': 'Pixel Test',
            'cam': 'Camera',
            'kb': 'Keyboard',
            'act': 'Activation',
            'drv': 'Drivers',
            'enroll': 'Enrollment Check',
            'bios': 'BIOS Test',
            'wifi': 'WiFi Test',
            'usb': 'USB Test',
            'bluetooth': 'Bluetooth Test',
            'network': 'Network Test',
            'audio': 'Audio Test',
        }
        
        if status_summary:
            for key, display_name in test_mapping.items():
                if key in status_summary:
                    status = status_summary[key]
                    if '✔' in status:
                        status_text = 'PRESENT'
                        status_color = PASS_GREEN
                    elif '✖' in status:
                        status_text = 'NOT PRESENT'
                        status_color = FAIL_RED
                    else:
                        status_text = 'NOT TESTED'
                        status_color = colors.HexColor('#9e9e9e')
                    comp_data.append([display_name, status_text])
        
        if len(comp_data) > 1:
            comp_table = Table(comp_data, colWidths=[doc.width * 0.7, doc.width * 0.3])
            comp_style_list = [
                ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
                ('TEXTCOLOR', (0, 0), (-1, 0), HEADER_TEXT),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ('BOX', (0, 0), (-1, -1), 1, HEADER_BG),
            ]
            
            for i in range(1, len(comp_data)):
                status = comp_data[i][1]
                if status == 'PRESENT':
                    comp_style_list.append(('TEXTCOLOR', (1, i), (1, i), PASS_GREEN))
                    comp_style_list.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#e8f5e9')))
                elif status == 'NOT PRESENT':
                    comp_style_list.append(('TEXTCOLOR', (1, i), (1, i), FAIL_RED))
                    comp_style_list.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#ffebee')))
                else:
                    comp_style_list.append(('TEXTCOLOR', (1, i), (1, i), colors.HexColor('#9e9e9e')))
                    comp_style_list.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#fafafa')))
            
            comp_table.setStyle(TableStyle(comp_style_list))
            story.append(comp_table)
            story.append(Spacer(1, 10))
        
        # ── RESULT TEST ──
        add_section_header("Result Test")
        
        # Count passes/fails
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        result_data = [['Check', 'Result']]
        if status_summary:
            for key, display_name in test_mapping.items():
                if key in status_summary:
                    total_tests += 1
                    status = status_summary[key]
                    if '✔' in status:
                        result_text = 'PASSED'
                        passed_tests += 1
                    elif '✖' in status:
                        result_text = 'FAILED'
                        failed_tests += 1
                    else:
                        result_text = 'NOT TESTED'
                    result_data.append([display_name, result_text])
        
        # Add summary row
        if total_tests > 0:
            result_data.append(['', ''])
            result_data.append([f'Total: {total_tests}', f'Passed: {passed_tests} / Failed: {failed_tests}'])
        
        if len(result_data) > 1:
            result_table = Table(result_data, colWidths=[doc.width * 0.6, doc.width * 0.4])
            result_style_list = [
                ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
                ('TEXTCOLOR', (0, 0), (-1, 0), HEADER_TEXT),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ('BOX', (0, 0), (-1, -1), 1, HEADER_BG),
            ]
            
            for i in range(1, len(result_data) - 2):
                result_val = result_data[i][1]
                if result_val == 'PASSED':
                    result_style_list.append(('TEXTCOLOR', (1, i), (1, i), PASS_GREEN))
                    result_style_list.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#e8f5e9')))
                elif result_val == 'FAILED':
                    result_style_list.append(('TEXTCOLOR', (1, i), (1, i), FAIL_RED))
                    result_style_list.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#ffebee')))
                else:
                    result_style_list.append(('TEXTCOLOR', (1, i), (1, i), colors.HexColor('#9e9e9e')))
                    result_style_list.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#fafafa')))
            
            # Style summary row
            if total_tests > 0:
                result_style_list.append(('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e3f2fd')))
                result_style_list.append(('TEXTCOLOR', (0, -1), (-1, -1), HEADER_BG))
                result_style_list.append(('FONTSIZE', (0, -1), (-1, -1), 10))
                result_style_list.append(('SPAN', (0, -2), (-1, -2)))
            
            result_table.setStyle(TableStyle(result_style_list))
            story.append(result_table)
            story.append(Spacer(1, 10))
        
        # ── ENROLLMENT TEST ──
        # Parse the stored EnrollmentTest.ps1 output lines into a Property/Value table
        global _enrollment_report_lines
        enroll_rows = []
        observations_list = []
        in_observations = False
        for raw in _enrollment_report_lines:
            stripped = raw.strip()
            # Skip separator lines, headers, result markers, empty lines, file-save lines
            if not stripped:
                in_observations = False
                continue
            if stripped.startswith('-' * 5) or stripped.startswith('=' * 5):
                continue
            if stripped.upper().startswith('ENROLLMENT_CHECK_RESULT:'):
                continue
            if stripped.lower().startswith('text report saved') or stripped.lower().startswith('json report saved'):
                continue
            # "Observations" section header
            if stripped.lower() == 'observations':
                in_observations = True
                continue
            # Bullet observation items
            if in_observations and (stripped.startswith('*') or stripped.startswith('-') or stripped.startswith('•')):
                observations_list.append(stripped.lstrip('*-• ').strip())
                continue
            # Header row: "Property | Value" — skip
            if '|' in stripped and stripped.lower().replace(' ', '').startswith('property|'):
                continue
            # Data row: "Property   | Value"
            if '|' in stripped:
                parts = stripped.split('|', 1)
                prop = parts[0].strip()
                val  = parts[1].strip() if len(parts) > 1 else ''
                if prop and prop.lower() not in ('property', 'enrollment test'):
                    enroll_rows.append((prop, val))
                continue

        if enroll_rows:
            story.append(Spacer(1, 6))
            add_section_header("Enrollment Test")
            enroll_kv_style = ParagraphStyle(
                'EnrollKV',
                parent=styles['Normal'],
                fontSize=9,
                leading=12,
                spaceAfter=0
            )
            enroll_table_data = [
                [
                    Paragraph('<b>Property</b>', enroll_kv_style),
                    Paragraph('<b>Value</b>', enroll_kv_style)
                ]
            ]
            for prop, val in enroll_rows:
                enroll_table_data.append([
                    Paragraph(prop, enroll_kv_style),
                    Paragraph(val,  enroll_kv_style)
                ])
            enroll_col_w = [doc.width * 0.40, doc.width * 0.60]
            enroll_t = Table(enroll_table_data, colWidths=enroll_col_w)
            enroll_t_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#cccccc')),
                ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE',   (0, 0), (-1, -1), 9),
                ('ALIGN',      (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING',    (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING',   (0, 0), (-1, -1), 6),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ('BOX',  (0, 0), (-1, -1), 0.8, colors.black),
            ]
            # Alternate row shading
            for ri in range(1, len(enroll_table_data)):
                if ri % 2 == 0:
                    enroll_t_style.append(('BACKGROUND', (0, ri), (-1, ri), colors.HexColor('#f9f9f9')))
            enroll_t.setStyle(TableStyle(enroll_t_style))
            story.append(enroll_t)

            # Observations bullets below the table
            if observations_list:
                story.append(Spacer(1, 6))
                obs_bold_style = ParagraphStyle(
                    'ObsBold', parent=styles['Normal'], fontSize=9,
                    fontName='Helvetica-Bold', spaceAfter=2
                )
                obs_item_style = ParagraphStyle(
                    'ObsItem', parent=styles['Normal'], fontSize=9,
                    leftIndent=12, spaceAfter=2
                )
                story.append(Paragraph('<b>Observations</b>', obs_bold_style))
                for obs in observations_list:
                    story.append(Paragraph(f'• {obs}', obs_item_style))
            story.append(Spacer(1, 10))

        # ── SCREEN CAPTURE ──
        if screenshot_paths and len(screenshot_paths) > 0:
            story.append(PageBreak())
            add_section_header("Screen Capture")
            
            for idx, screenshot_path in enumerate(screenshot_paths):
                if not os.path.exists(screenshot_path):
                    continue
                
                # Component / Part header row with separator line
                header_data = [['Component', f'Part {idx + 1}']]
                header_table = Table(header_data, colWidths=[doc.width * 0.5, doc.width * 0.5])
                header_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f0f0f0')),
                    ('BACKGROUND', (1, 0), (1, 0), colors.white),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('FONTSIZE', (0, 0), (-1, -1), 11),
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('LINEBELOW', (0, 0), (-1, -1), 1.5, colors.black),
                ]))
                story.append(header_table)
                story.append(Spacer(1, 8))
                
                # Load and embed screenshot
                img = Image.open(screenshot_path)
                img_w, img_h = img.size
                
                # Scale to fit page width
                max_width = doc.width
                max_height = doc.height * 0.80
                aspect = img_w / img_h
                
                new_width = max_width
                new_height = max_width / aspect
                if new_height > max_height:
                    new_height = max_height
                    new_width = max_height * aspect
                
                pdf_img = RLImage(screenshot_path, width=new_width, height=new_height)
                story.append(pdf_img)
                
                # Clean up temp file
                try:
                    os.remove(screenshot_path)
                except Exception:
                    pass
                
                # Page break between parts
                if idx < len(screenshot_paths) - 1:
                    story.append(PageBreak())
        
        # Also add individual card screenshots if any were captured
        card_only_screenshots = [c for c in _card_screenshots if c.get('path') and os.path.exists(c.get('path'))]
        if card_only_screenshots and len(card_only_screenshots) > 0:
            if screenshot_paths and len(screenshot_paths) > 0:
                story.append(PageBreak())
            else:
                story.append(PageBreak())
                add_section_header("Test Images")
            
            for idx, card_info in enumerate(card_only_screenshots):
                screenshot_path = card_info.get('path')
                if not screenshot_path or not os.path.exists(screenshot_path):
                    continue
                
                # Component / Name header row with separator line
                header_data = [['Component', card_info['name']]]
                header_table = Table(header_data, colWidths=[doc.width * 0.5, doc.width * 0.5])
                header_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f0f0f0')),
                    ('BACKGROUND', (1, 0), (1, 0), colors.white),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('FONTSIZE', (0, 0), (-1, -1), 11),
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('LINEBELOW', (0, 0), (-1, -1), 1.5, colors.black),
                ]))
                story.append(header_table)
                story.append(Spacer(1, 8))
                
                img = Image.open(screenshot_path)
                img_w, img_h = img.size
                aspect = img_w / img_h
                
                # Full width for keyboard, smaller for others
                if card_info.get('key') == 'kb':
                    max_width = doc.width
                    max_height = doc.height * 0.75
                else:
                    max_width = doc.width * 0.85
                    max_height = doc.height * 0.50
                
                new_width = max_width
                new_height = max_width / aspect
                if new_height > max_height:
                    new_height = max_height
                    new_width = max_height * aspect
                
                pdf_img = RLImage(screenshot_path, width=new_width, height=new_height)
                story.append(pdf_img)
                
                # Clean up
                try:
                    os.remove(screenshot_path)
                except Exception:
                    pass
                
                if idx < len(card_only_screenshots) - 1:
                    story.append(PageBreak())
        
        # Footer
        story.append(Spacer(1, 20))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#999999'),
            alignment=TA_CENTER
        )
        story.append(Paragraph("Generated by Hardware Test Suite v0.41", footer_style))
        
        # Build PDF
        doc.build(story)
        
        return pdf_path
    except Exception as e:
        print(f"Error creating PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


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


def _ensure_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _get_network_adapter_data():
    command = r"""
$allAdapters = Get-NetAdapter -Physical -ErrorAction SilentlyContinue

$wifiAdapters = $allAdapters | Where-Object {
    $_.InterfaceDescription -match 'Wireless|Wi-Fi|802\.11|WLAN' -or
    $_.Name -match 'Wi-Fi|Wireless|WLAN'
}

$ethernetAdapters = $allAdapters | Where-Object {
    $_.InterfaceDescription -notmatch 'Wireless|Wi-Fi|802\.11|WLAN|Bluetooth' -and
    $_.Name -notmatch 'Wi-Fi|Wireless|WLAN|Bluetooth'
}

function Convert-AdapterData {
    param([array]$Adapters)

    $result = @()
    foreach ($adapter in @($Adapters)) {
        if (-not $adapter) { continue }
        $profile = Get-NetConnectionProfile -InterfaceIndex $adapter.ifIndex -ErrorAction SilentlyContinue
        $active = $adapter.Status -eq 'Up'
        $connected = $active -and $null -ne $profile

        $result += [pscustomobject]@{
            Name            = $adapter.Name
            Description     = $adapter.InterfaceDescription
            AdapterStatus   = $adapter.Status
            Active          = if ($active) { 'Yes' } else { 'No' }
            Connected       = if ($connected) { 'Yes' } else { 'No' }
            NetworkName     = if ($connected) { $profile.Name } else { $null }
            NetworkCategory = if ($connected) { $profile.NetworkCategory } else { $null }
        }
    }
    return $result
}

[pscustomobject]@{
    WifiAdapters     = @(Convert-AdapterData -Adapters $wifiAdapters)
    EthernetAdapters = @(Convert-AdapterData -Adapters $ethernetAdapters)
} | ConvertTo-Json -Compress -Depth 4
"""

    data = _run_powershell_json(command) or {}
    return {
        "wifi": _ensure_list(data.get("WifiAdapters")),
        "ethernet": _ensure_list(data.get("EthernetAdapters")),
    }




# ------------------------------------------------------------------
# Combined Hardware Test Screen
# ------------------------------------------------------------------
def show_hardware_test_screen():
    global active_screen, _camera_captures, _camera_after_id, _card_widgets, _card_screenshots
    clear_screen()
    
    # Reset card tracking
    _card_widgets = {}
    _card_screenshots = []
    
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

    active_screen = ctk.CTkFrame(app, fg_color="#d8eefc")
    active_screen.pack(fill="both", expand=True)

    THEMES = {
        "light": {
            "screen_bg": "#d8eefc",
            "top_bg": "#9fd2f6",
            "sidebar_bg": "#eef9ea",
            "card_bg": "#ffffff",
            "card_border": "#dbe3ea",
            "header_bg": "#f4f4f4",
            "title": "#111111",
            "subtle": "#6b7280",
            "primary": "#2f8ee5",
            "pass": "#49b64e",
            "fail": "#ff4d3d",
            "neutral": "#a3a3a3",
            "refresh_hover": "#dff0d7",
            "sidebar_hover": "#e4f4dd",
            "submit_hover": "#3aa643",
            "timer_text": "#1f4f7a",
            "timer_bg": "#f3b63f",
            "prod_bg": "#cf1628",
            "lang_bg": "#8dc4ee",
            "lang_button": "#78b8e9",
            "lang_hover": "#6faee0",
            "close_hover": "#c9e3f7",
            "inactive_btn": "#d9dde3",
            "pass_hover": "#86d98e",
            "fail_hover": "#ff7d71",
            "status_bg": "#ffffff",
            "embed_bg": "#eef9ea",
            "embed_text": "#1f2937",
            "embed_border": "#d8e9d0",
            "body_text": "#111111",
            "muted_text": "#4b5563",
            "success_text": "#111111",
        },
        "dark": {
            "screen_bg": "#0d1117",
            "top_bg": "#1f2a44",
            "sidebar_bg": "#161b22",
            "card_bg": "#161b22",
            "card_border": "#30363d",
            "header_bg": "#202938",
            "title": "#58a6ff",
            "subtle": "#9fb3c8",
            "primary": "#2a5298",
            "pass": "#2ecc71",
            "fail": "#ff6b6b",
            "neutral": "#9aa4b2",
            "refresh_hover": "#22324f",
            "sidebar_hover": "#1f242c",
            "submit_hover": "#2a8f4a",
            "timer_text": "#7ee787",
            "timer_bg": "#1f3a5f",
            "prod_bg": "#cf1628",
            "lang_bg": "#1f3a5f",
            "lang_button": "#2a5298",
            "lang_hover": "#3a62a8",
            "close_hover": "#253041",
            "inactive_btn": "#2f3338",
            "pass_hover": "#28b463",
            "fail_hover": "#ff5252",
            "status_bg": "#161b22",
            "embed_bg": "#0d1117",
            "embed_text": "#c9d1d9",
            "embed_border": "#30363d",
            "body_text": "#ffffff",
            "muted_text": "#c9d1d9",
            "success_text": "#7ee787",
        },
    }
    _current_theme = ["light"]
    _current_language = ["en"]
    _go_back_ref = [lambda: None]
    _apply_theme_ref = [lambda _theme: None]

    I18N_EXACT = {
        "es": {
            "System Tests": "Pruebas del Sistema",
            "Production": "Producción",
            "Submit  ✔": "Enviar  ✔",
            "Submitted ✔": "Enviado ✔",
            "Run Sequence": "Ejecutar Secuencia",
            "Running...": "Ejecutando...",
            "NOT RUN": "SIN EJECUTAR",
            "PASS  ✔": "APROBADO  ✔",
            "FAIL  ✖": "FALLA  ✖",
            "👤  Operator Selection": "👤  Selección de Operador",
            "🔈  Audio Changer": "🔈  Cambio de Audio",
            "🔈 Audio Changer": "🔈 Cambio de Audio",
            "🖥️  System Info": "🖥️  Información del Sistema",
            "🖥️ System Info": "🖥️ Información del Sistema",
            "🧩  Components": "🧩  Componentes",
            "🧩 Components": "🧩 Componentes",
            "📶  Network Adapters": "📶  Adaptadores de Red",
            "📶 Network Adapters": "📶 Adaptadores de Red",
            "🔋  Battery": "🔋  Batería",
            "🔋 Battery": "🔋 Batería",
            "🖱️  Touchpad": "🖱️  Panel Táctil",
            "🖱️ Touchpad": "🖱️ Panel Táctil",
            "🔊  Speaker": "🔊  Bocina",
            "🔊 Speaker": "🔊 Bocina",
            "🎤  Microphone Test": "🎤  Prueba de Micrófono",
            "🎙️ Microphone": "🎙️ Micrófono",
            "💡  Brightness": "💡  Brillo",
            "☀️ Brightness": "☀️ Brillo",
            "💳  Smart Card Reader": "💳  Lector de Tarjeta Inteligente",
            "💳 Smart Card": "💳 Tarjeta Inteligente",
            "🔌  USB Port Detection": "🔌  Detección de Puertos USB",
            "🔌 USB Port Detection": "🔌 Detección de Puertos USB",
            "📡  NFC Reader": "📡  Lector NFC",
            "📡 NFC Reader": "📡 Lector NFC",
            "👆  Fingerprint Reader": "👆  Lector de Huella Digital",
            "👆 Fingerprint": "👆 Huella Digital",
            "👆  Touchscreen": "👆  Pantalla Táctil",
            "👆 Touchscreen": "👆 Pantalla Táctil",
            "🟥  Pixel Test": "🟥  Prueba de Píxeles",
            "📷  Camera": "📷  Cámara",
            "⌨️  Keyboard Test": "⌨️  Prueba de Teclado",
            "⌨️ Keyboard": "⌨️ Teclado",
            "🔐  Activation": "🔐  Activación",
            "✅ Activation": "✅ Activación",
            "🛠️  Drivers": "🛠️  Controladores",
            "💾 Drivers": "💾 Controladores",
            "🎮  GPU": "🎮  GPU",
            "🎮 GPU": "🎮 GPU",
            "🔐  Enrollment Check": "🔐  Verificación de Inscripción",
            "🦠  Virus Scan": "🦠  Escaneo de Virus",
            "🛡️ Virus Scan": "🛡️ Escaneo de Virus",
            "WWAN": "WWAN",
            "WLAN": "WLAN",
            "Privacy": "Privacidad",
            "Smart Card": "Tarjeta Inteligente",
            "Backlight": "Retroiluminación",
            "RGB Keyboard": "Teclado RGB",
            "Fingerprint": "Huella Digital",
            "System Info": "Información del Sistema",
            "Select your name to begin testing": "Seleccione su nombre para comenzar las pruebas",
            "Components locked until System Info PASS": "Componentes bloqueados hasta que Información del Sistema sea APROBADO",
            "✅ Components active  —  ⚠️ Physically check Privacy Indicator lights on device": "✅ Componentes activos  —  ⚠️ Revise físicamente las luces indicadoras de privacidad en el equipo",
            "Run refresh or sequencer to check adapters.": "Use actualizar o el secuenciador para revisar los adaptadores.",
            "Wi-Fi Adapters": "Adaptadores Wi-Fi",
            "Ethernet Adapters": "Adaptadores Ethernet",
            "No adapters detected": "No se detectaron adaptadores",
            "No adapters detected.": "No se detectaron adaptadores.",
            "Adapter detected:": "Adaptador detectado:",
            "Loading...": "Cargando...",
            "Activation Check": "Verificación de Activación",
            "Driver Checker": "Verificación de Controladores",
            "Graphics Controller": "Controlador Gráfico",
            "Checking...": "Verificando...",
            "Click Start to load touchpad module.": "Haga clic en Iniciar para cargar el módulo del panel táctil.",
            "Click Start to run camera preview.": "Haga clic en Iniciar para ejecutar la vista previa de la cámara.",
            "Click Start to load keyboard module.": "Haga clic en Iniciar para cargar el módulo del teclado.",
            "Click Run to start touchscreen test.": "Haga clic en Ejecutar para iniciar la prueba táctil.",
            "Start the pixel test to cycle full-screen colors.": "Inicie la prueba de píxeles para alternar colores en pantalla completa.",
            "Loading brightness info...": "Cargando información de brillo...",
            "Checking for smart card readers...": "Buscando lectores de tarjeta inteligente...",
            "Checking for NFC readers...": "Buscando lectores NFC...",
            "Checking for fingerprint readers...": "Buscando lectores de huellas...",
            "Starting Virus Scan...": "Iniciando escaneo de virus...",
            "Starting enrollment check...": "Iniciando verificación de inscripción...",
            "Running audio configuration...": "Ejecutando configuración de audio...",
            "Fingerprint: PASS": "Huella Digital: APROBADO",
            "Fingerprint: FAIL": "Huella Digital: FALLA",
            "NFC: PASS": "NFC: APROBADO",
            "NFC: FAIL": "NFC: FALLA",
            "USB Test: PASS": "Prueba USB: APROBADO",
            "USB Test: FAIL": "Prueba USB: FALLA",
            "Windows is Activated": "Windows está activado",
            "Windows is not Activated": "Windows no está activado",
            "No devices with missing drivers found.": "No se encontraron dispositivos con controladores faltantes.",
            "Checking for missing drivers...": "Buscando controladores faltantes...",
            "Camera preview stopped.": "Vista previa de cámara detenida.",
            "Keyboard module stopped.": "Módulo de teclado detenido.",
            "Keyboard module running.": "Módulo de teclado en ejecución.",
            "Touchscreen test stopped.": "Prueba táctil detenida.",
            "Brightness test stopped.": "Prueba de brillo detenida.",
            "Brightness cycle complete.": "Ciclo de brillo completado.",
            "Stopped.": "Detenido.",
            "Playing ST.WAV (looping)...": "Reproduciendo ST.WAV (en bucle)...",
            "Playback finished.": "Reproducción terminada.",
            "Start": "Iniciar",
            "Start Test": "Iniciar Prueba",
            "Capture": "Capturar",
        }
    }

    I18N_REPLACEMENTS = {
        "es": [
            ("Name:", "Nombre:"),
            ("Description:", "Descripción:"),
            ("Adapter status:", "Estado del adaptador:"),
            ("Active:", "Activo:"),
            ("Connected to network:", "Conectado a la red:"),
            ("Network name:", "Nombre de la red:"),
            ("Network category:", "Categoría de red:"),
            ("Service:", "Servicio:"),
            ("Readers Found:", "Lectores encontrados:"),
            ("Controllers:", "Controladores:"),
            ("Hubs:", "Concentradores:"),
            ("Devices:", "Dispositivos:"),
            ("Active Connections:", "Conexiones activas:"),
            ("USB 2.0:", "USB 2.0:"),
            ("USB 3.0:", "USB 3.0:"),
            ("USB-C:", "USB-C:"),
            ("Biometric:", "Biométrico:"),
            ("Fingerprint:", "Huella Digital:"),
            ("NFC Devices:", "Dispositivos NFC:"),
            ("Contactless:", "Sin contacto:"),
            ("Capacity:", "Capacidad:"),
            ("Health:", "Salud:"),
            ("Status:", "Estado:"),
            ("Cycles:", "Ciclos:"),
            ("Current:", "Actual:"),
            ("Battery:", "Batería:"),
            ("Microphone", "Micrófono"),
            ("Brightness", "Brillo"),
            ("Speaker", "Bocina"),
            ("Battery", "Batería"),
            ("Components", "Componentes"),
            ("Keyboard", "Teclado"),
            ("Mouse", "Ratón"),
            ("Webcam", "Cámara web"),
            ("Touch Screen", "Pantalla táctil"),
            ("Drivers", "Controladores"),
            ("Operator", "Operador"),
            ("Touchpad", "Panel táctil"),
            ("Camera", "Cámara"),
            ("Start camera first, then press Capture.", "Primero inicie la cámara y luego presione Capturar."),
            ("No touchscreen is detected.", "No se detectó pantalla táctil."),
            ("Checking enrollment", "Verificando inscripción"),
            ("Scanning", "Escaneando"),
        ]
    }

    LAYOUT = {
        "outer_gap": 10,
        "card_pad_x": 12,
        "card_pad_y": 8,
        "card_inner_x": 16,
        "card_inner_y": 10,
        "header_height": 54,
        "sidebar_width": 255,
        "sidebar_row_y": 1,
        "sidebar_row_pad_x": 6,
        "sidebar_label_pad_x": 8,
        "status_pad_y": 10,
    }

    def theme_value(key):
        return THEMES[_current_theme[0]][key]

    themed_ctk_frames = []
    themed_tk_frames = []
    themed_text_widgets = []
    themed_subtle_labels = []
    themed_title_labels = []
    themed_refresh_buttons = []
    i18n_widgets = []

    def _register_ctk_frame(widget):
        themed_ctk_frames.append(widget)
        return widget

    def _register_tk_frame(widget):
        themed_tk_frames.append(widget)
        return widget

    def _register_text_widget(widget):
        themed_text_widgets.append(widget)
        return widget

    def _register_subtle_label(widget):
        themed_subtle_labels.append(widget)
        return widget

    def _register_title_label(widget):
        themed_title_labels.append(widget)
        return widget

    def _register_refresh_button(widget):
        themed_refresh_buttons.append(widget)
        return widget

    def tr(text):
        if not isinstance(text, str):
            return text
        if _current_language[0] == "en":
            return text
        translated = I18N_EXACT.get(_current_language[0], {}).get(text, text)
        for src, dst in I18N_REPLACEMENTS.get(_current_language[0], []):
            translated = translated.replace(src, dst)
        return translated

    def _install_i18n_widget(widget):
        if getattr(widget, "_i18n_installed", False):
            return
        try:
            original_configure = widget.configure
        except Exception:
            return

        widget._i18n_installed = True
        widget._i18n_original_configure = original_configure

        try:
            current_text = widget.cget("text")
            if isinstance(current_text, str):
                widget._i18n_source_text = current_text
        except Exception:
            pass

        def _wrapped_configure(*args, **kwargs):
            if args and len(args) == 1 and isinstance(args[0], dict):
                merged = dict(args[0])
                merged.update(kwargs)
                kwargs = merged
                args = ()
            if "text" in kwargs and isinstance(kwargs["text"], str):
                widget._i18n_source_text = kwargs["text"]
                kwargs["text"] = tr(kwargs["text"])
            return original_configure(*args, **kwargs)

        try:
            widget.configure = _wrapped_configure
            widget.config = _wrapped_configure
        except Exception:
            pass

        i18n_widgets.append(widget)

    def _install_i18n_tree(widget):
        try:
            _install_i18n_widget(widget)
        except Exception:
            pass
        try:
            for child in widget.winfo_children():
                _install_i18n_tree(child)
        except Exception:
            pass

    def _apply_language(choice):
        lowered = str(choice or "").strip().lower()
        _current_language[0] = "es" if lowered.startswith("es") else "en"
        try:
            lang_var.set("Español" if _current_language[0] == "es" else "English")
        except Exception:
            pass
        for widget in i18n_widgets:
            try:
                source_text = getattr(widget, "_i18n_source_text", None)
                if isinstance(source_text, str):
                    widget._i18n_original_configure(text=tr(source_text))
            except Exception:
                pass

    def _restyle_tk_tree(widget, kind="generic"):
        try:
            children = widget.winfo_children()
        except Exception:
            children = []

        try:
            if isinstance(widget, tk.Frame):
                widget.configure(bg=theme_value("embed_bg"))
            elif isinstance(widget, tk.Canvas):
                if kind == "mic_wave":
                    widget.configure(bg="#f3fbef" if _current_theme[0] == "light" else "#08111f")
                elif kind == "mic_meter":
                    widget.configure(bg="#e6f5df" if _current_theme[0] == "light" else "#111c30")
                else:
                    widget.configure(bg=theme_value("embed_bg"))
            elif isinstance(widget, tk.Label):
                widget.configure(bg=theme_value("embed_bg"), fg=theme_value("embed_text"))
            elif isinstance(widget, tk.Button):
                widget.configure(
                    bg="#5ab18e" if _current_theme[0] == "light" else "#5ab18e",
                    fg="#08111f",
                    activebackground="#79c8a8" if _current_theme[0] == "light" else "#6abe9d",
                    activeforeground="#08111f",
                )
        except Exception:
            pass

        for child in children:
            try:
                child_kind = kind
                if hasattr(child, "winfo_class"):
                    name = str(child.winfo_class()).lower()
                    if "canvas" in name and "meter" in str(child):
                        child_kind = "mic_meter"
                _restyle_tk_tree(child, child_kind)
            except Exception:
                pass

    # Real-time status tracking for sidebar
    status_indicators = {}
    def update_sidebar_status(key, status):
        """status can be 'pass', 'fail', or 'none'"""
        ind = status_indicators.get(key)
        if not ind: return
        if status == 'pass':
            ind.configure(text="✔", text_color=theme_value("pass"))
            # Capture card screenshot when passed
            capture_card_screenshot(key)
        elif status == 'fail':
            ind.configure(text="✖", text_color=theme_value("fail"))
        else:
            ind.configure(text="✔", text_color=theme_value("neutral"))
    try:
        # Ensure hardware screen is on top of the main menu
        active_screen.lift()
    except Exception:
        pass

    # ── Top bar ──────────────────────────────────────────────────────
    top_bar = ctk.CTkFrame(active_screen, fg_color=theme_value("top_bg"), corner_radius=0, height=60)
    top_bar.pack(fill="x", side="top")
    top_bar.pack_propagate(False)
    ctk.CTkLabel(
        top_bar,
        text="",
        font=ctk.CTkFont(size=18, weight="bold"),
        text_color=theme_value("title"),
    ).pack(side="left", padx=18, pady=8)

    top_actions = ctk.CTkFrame(top_bar, fg_color="transparent")
    top_actions.pack(side="right", padx=14, pady=10)
    
    # Timer display at the top right
    global _timer_label
    _timer_label = ctk.CTkLabel(
        top_actions,
        text="◷  00:00:00",
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color=theme_value("timer_text"),
        fg_color=theme_value("timer_bg"),
        corner_radius=20,
        width=148,
        height=38,
    )
    _timer_label.pack(side="right", padx=(8, 0))

    ctk.CTkButton(
        top_actions,
        text="⚙",
        width=34,
        height=34,
        corner_radius=8,
        fg_color=theme_value("primary"),
        hover_color=theme_value("lang_hover"),
        font=ctk.CTkFont(size=16, weight="bold"),
    ).pack(side="right", padx=(8, 0))

    ctk.CTkLabel(
        top_actions,
        text="Production",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color="#ffffff",
        fg_color=theme_value("prod_bg"),
        corner_radius=8,
        width=118,
        height=30,
    ).pack(side="right", padx=(8, 0))

    theme_var = tk.StringVar(value="Light")
    theme_menu = ctk.CTkOptionMenu(
        top_actions,
        variable=theme_var,
        values=["Light", "Dark"],
        width=110,
        height=40,
        fg_color=theme_value("lang_bg"),
        button_color=theme_value("lang_button"),
        button_hover_color=theme_value("lang_hover"),
        text_color=theme_value("title"),
        dropdown_text_color=theme_value("title"),
        corner_radius=8,
        command=lambda choice: _apply_theme_ref[0](choice.lower()),
    )
    theme_menu.pack(side="right", padx=(8, 0))

    lang_var = tk.StringVar(value="English")
    lang_menu = ctk.CTkOptionMenu(
        top_actions,
        variable=lang_var,
        values=["Español", "English"],
        width=132,
        height=40,
        fg_color=theme_value("lang_bg"),
        button_color=theme_value("lang_button"),
        button_hover_color=theme_value("lang_hover"),
        text_color=theme_value("title"),
        dropdown_text_color=theme_value("title"),
        corner_radius=8,
        command=_apply_language,
    )
    lang_menu.pack(side="right", padx=(8, 0))

    ctk.CTkButton(
        top_actions,
        text="✕",
        width=34,
        height=34,
        corner_radius=8,
        fg_color="transparent",
        hover_color=theme_value("close_hover"),
        text_color=theme_value("title"),
        font=ctk.CTkFont(size=18, weight="bold"),
        command=lambda: _go_back_ref[0](),
    ).pack(side="right", padx=(8, 0))
    
    # Timer starts AFTER operator selection, not here
    # start_timer()  # Moved to operator card
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
        stop_timer()
        return_to_main_menu()

    _go_back_ref[0] = _go_back

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
    device_strip = ctk.CTkFrame(active_screen, fg_color=theme_value("top_bg"), corner_radius=0, height=100)
    device_strip.pack(fill="x", side="top")
    device_strip.pack_propagate(False)

    device_tabs = ctk.CTkFrame(device_strip, fg_color="transparent")
    device_tabs.pack(pady=(12, 12))

    device_tab_buttons = []
    for label, icon, active in [
        ("DESKTOP", "🗄️", False),  # Desktop tower
        ("LAPTOP", "💻", True),
        ("ALL-IN-ONE", "🖥️", False),  # All-in-One (monitor)
        ("TABLET", "📱", False),  # Tablet
        ("COM\nCOMPONENTS", "🖼", False),
    ]:
        btn = ctk.CTkButton(
            device_tabs,
            text=f"{icon}\n{label}",
            width=118,
            height=70,
            corner_radius=14,
            fg_color=theme_value("card_bg"),
            hover_color="#f7fbff",
            border_width=3 if active else 1,
            border_color=theme_value("primary") if active else theme_value("card_border"),
            text_color=theme_value("title"),
            font=ctk.CTkFont(size=12, weight="bold" if active else "normal"),
        )
        btn._is_active_device = active
        btn.pack(side="left", padx=9)
        device_tab_buttons.append(btn)

    main_container = ctk.CTkFrame(active_screen, fg_color="transparent")
    main_container.pack(fill="both", expand=True, padx=(0, 8), pady=(6, 10))

    sidebar = ctk.CTkFrame(main_container, width=LAYOUT["sidebar_width"], fg_color=theme_value("sidebar_bg"), corner_radius=0,
                           border_width=0, border_color=theme_value("sidebar_bg"))
    sidebar.pack(side="left", fill="y", padx=(0, 6), pady=(0, 0))
    sidebar.pack_propagate(False)

    # Sidebar header row: "Test Summary" + global refresh button
    _sb_header = ctk.CTkFrame(sidebar, fg_color="transparent")
    _sb_header.pack(fill="x", padx=12, pady=(16, 6))
    _sb_title = ctk.CTkLabel(_sb_header, text="System Tests",
                 font=ctk.CTkFont(size=16, weight="bold"),
                 text_color=theme_value("title"))
    _sb_title.pack(side="left", padx=(6, 0))
    _global_refresh_btn = ctk.CTkButton(
        _sb_header,
        text="⟳",
        width=30,
        height=30,
        fg_color="transparent",
        hover_color=theme_value("refresh_hover"),
        corner_radius=8,
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color=theme_value("subtle"),
        command=lambda: _do_global_refresh(),
    )
    _global_refresh_btn.pack(side="right", padx=(0, 4))
    _refresh_running = [False]

    sidebar_list = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
    sidebar_list.pack(fill="both", expand=True, padx=4, pady=(4, 8))
    try:
        sidebar_list._scrollbar.configure(width=12)
    except Exception:
        pass
    
    def add_sidebar_item(key, display_name, target_widget):
        # Store card widget reference for screenshot capture
        if target_widget is not None:
            _card_widgets[key] = target_widget
        
        row = ctk.CTkFrame(sidebar_list, fg_color="transparent", cursor="hand2")
        row.pack(fill="x", padx=LAYOUT["sidebar_row_pad_x"], pady=LAYOUT["sidebar_row_y"])
        row.pack_propagate(False)
        row.configure(height=42)

        lbl = ctk.CTkLabel(row, text=display_name, font=ctk.CTkFont(size=13), text_color=theme_value("title"), anchor="w")
        lbl.pack(side="left", fill="x", expand=True, padx=(LAYOUT["sidebar_label_pad_x"], 10), pady=4)

        ind = ctk.CTkLabel(row, text="✔", font=ctk.CTkFont(size=20, weight="bold"), text_color=theme_value("neutral"))
        ind.pack(side="right", padx=(8, 8))
        status_indicators[key] = ind

        row._sidebar_label = lbl

        # Hover effects
        def on_enter(e): row.configure(fg_color=theme_value("sidebar_hover"))
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
            # Stop the timer
            stop_timer()
            
            # Gather a simple summary of sidebar statuses
            summary = {}
            for k, lbl in status_indicators.items():
                try:
                    text = (lbl.cget('text') or '').strip()
                except Exception:
                    text = ''
                summary[k] = text
            
            # Take screenshot and create PDF with the summary data
            pdf_path = take_screenshot_and_create_pdf(status_summary=summary)
            # Log and show confirmation
            _log_sequence(f"results submitted: {json.dumps(summary)}")
            
            # Show success message with PDF location
            if pdf_path:
                try:
                    messagebox.showinfo("Submit", f"Test results submitted.\n\nPDF saved to:\n{pdf_path}")
                except Exception:
                    pass
            else:
                try:
                    messagebox.showinfo("Submit", "Test results submitted.\n\nPDF creation failed.")
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
        fg_color=theme_value("pass"),
        hover_color=theme_value("submit_hover"),
        corner_radius=10,
        font=ctk.CTkFont(size=12, weight="bold"),
        command=_submit_results,
    )
    submit_btn.pack(side="bottom", pady=16, padx=16)

    # ── Scrollable body (Left) ────────────────────────────────────────
    body = ctk.CTkScrollableFrame(main_container, fg_color=theme_value("screen_bg"))
    body.pack(side="right", fill="both", expand=True, padx=(0, 4), pady=0)
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
        f = ctk.CTkFrame(parent, fg_color=theme_value("card_bg"), corner_radius=10,
                         border_width=1, border_color=theme_value("card_border"))
        # default: card fills horizontally only; callers may override to expand
        f.pack(fill="x", padx=LAYOUT["card_pad_x"], pady=LAYOUT["card_pad_y"])
        header_strip = ctk.CTkFrame(f, fg_color=theme_value("header_bg"), corner_radius=10, height=LAYOUT["header_height"])
        header_strip.pack(fill="x")
        header_strip.pack_propagate(False)
        title_label = ctk.CTkLabel(header_strip, text=title, font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=theme_value("title"))
        title_label.pack(anchor="w", padx=LAYOUT["card_inner_x"], pady=(12, 6))
        _register_title_label(title_label)
        # Status area at bottom of every card: interactive PASS and FAIL
        try:
            # Use CTkFrame for the status area so CTk widgets inside it render correctly
            status_frame = ctk.CTkFrame(f, fg_color=theme_value("status_bg"), corner_radius=0)
            status_frame.pack(side="bottom", fill="x", padx=LAYOUT["card_inner_x"], pady=(6, LAYOUT["status_pad_y"]))

            # Status display (shows NOT RUN / PASS / FAIL with color + icon)
            status_display = ctk.CTkLabel(status_frame, text="NOT RUN",
                                           font=ctk.CTkFont(size=11, weight="bold"),
                                           text_color=theme_value("subtle"))
            status_display.pack(side="right", padx=(6, 12))

            # Colors for active/inactive button states
            _pass_active = theme_value("pass")
            _fail_active = theme_value("fail")
            _btn_inactive = theme_value("inactive_btn")

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
                    try:
                        evt = getattr(f, '_sequence_done_event', None)
                        if evt is not None:
                            evt.set()
                    except Exception:
                        pass
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
                    try:
                        evt = getattr(f, '_sequence_done_event', None)
                        if evt is not None:
                            evt.set()
                    except Exception:
                        pass
                except Exception:
                    pass

            # Icon-style circular buttons to mark PASS / FAIL (matches screenshot)
            pass_btn = ctk.CTkButton(
                status_frame,
                text="✔",
                width=34,
                height=34,
                fg_color=_btn_inactive,
                hover_color=theme_value("pass_hover"),
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
                hover_color=theme_value("fail_hover"),
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
                f.header_strip = header_strip
                f.status_frame = status_frame
            except Exception:
                pass
        except Exception:
            # If something goes wrong creating status area, ignore and continue
            pass
        return f

    def _apply_theme(theme_name):
        _current_theme[0] = theme_name
        ctk.set_appearance_mode("dark" if theme_name == "dark" else "light")

        active_screen.configure(fg_color=theme_value("screen_bg"))
        top_bar.configure(fg_color=theme_value("top_bg"))
        device_strip.configure(fg_color=theme_value("top_bg"))
        sidebar.configure(fg_color=theme_value("sidebar_bg"), border_color=theme_value("sidebar_bg"))
        sidebar_list.configure(fg_color="transparent")
        body.configure(fg_color=theme_value("screen_bg"))
        _sb_title.configure(text_color=theme_value("title"))
        _global_refresh_btn.configure(text_color=theme_value("subtle"), hover_color=theme_value("refresh_hover"))
        submit_btn.configure(fg_color=theme_value("pass"), hover_color=theme_value("submit_hover"))
        _timer_label.configure(text_color=theme_value("timer_text"), fg_color=theme_value("timer_bg"))
        theme_menu.configure(
            fg_color=theme_value("lang_bg"),
            button_color=theme_value("lang_button"),
            button_hover_color=theme_value("lang_hover"),
            text_color=theme_value("title"),
            dropdown_text_color=theme_value("title"),
        )
        lang_menu.configure(
            fg_color=theme_value("lang_bg"),
            button_color=theme_value("lang_button"),
            button_hover_color=theme_value("lang_hover"),
            text_color=theme_value("title"),
            dropdown_text_color=theme_value("title"),
        )

        for btn in device_tab_buttons:
            is_active = getattr(btn, "_is_active_device", False)
            btn.configure(
                fg_color=theme_value("card_bg"),
                border_color=theme_value("primary") if is_active else theme_value("card_border"),
                text_color=theme_value("title"),
                hover_color=theme_value("header_bg"),
            )

        for row in sidebar_list.winfo_children():
            label = getattr(row, "_sidebar_label", None)
            if label is not None:
                try:
                    label.configure(text_color=theme_value("title"))
                except Exception:
                    pass

        for ind in status_indicators.values():
            try:
                current = ind.cget("text")
                if current == "✔" and str(ind.cget("text_color")) != str(theme_value("pass")):
                    ind.configure(text_color=theme_value("neutral"))
            except Exception:
                pass

        for card_widget in _card_widgets.values():
            try:
                card_widget.configure(fg_color=theme_value("card_bg"), border_color=theme_value("card_border"))
            except Exception:
                pass
            try:
                if hasattr(card_widget, "header_strip"):
                    card_widget.header_strip.configure(fg_color=theme_value("header_bg"))
            except Exception:
                pass
            try:
                if hasattr(card_widget, "status_frame"):
                    card_widget.status_frame.configure(fg_color=theme_value("status_bg"))
            except Exception:
                pass
            try:
                if hasattr(card_widget, "status_display"):
                    txt = str(card_widget.status_display.cget("text"))
                    if "PASS" in txt:
                        card_widget.status_display.configure(text_color=theme_value("pass"))
                    elif "FAIL" in txt:
                        card_widget.status_display.configure(text_color=theme_value("fail"))
                    else:
                        card_widget.status_display.configure(text_color=theme_value("subtle"))
            except Exception:
                pass
            try:
                if hasattr(card_widget, "pass_btn"):
                    card_widget.pass_btn.configure(hover_color=theme_value("pass_hover"))
                if hasattr(card_widget, "fail_btn"):
                    card_widget.fail_btn.configure(hover_color=theme_value("fail_hover"))
            except Exception:
                pass

        for widget in themed_ctk_frames:
            try:
                widget.configure(fg_color=theme_value("embed_bg"), border_color=theme_value("embed_border"))
            except Exception:
                try:
                    widget.configure(fg_color=theme_value("embed_bg"))
                except Exception:
                    pass

        for widget in themed_tk_frames:
            try:
                widget.configure(bg=theme_value("embed_bg"))
            except Exception:
                pass

        for widget in themed_text_widgets:
            try:
                widget.configure(bg=theme_value("embed_bg"), fg=theme_value("embed_text"), insertbackground=theme_value("embed_text"))
            except Exception:
                pass

        for widget in themed_subtle_labels:
            try:
                widget.configure(text_color=theme_value("subtle"))
            except Exception:
                pass

        for widget in themed_title_labels:
            try:
                widget.configure(text_color=theme_value("title"))
            except Exception:
                pass

        for widget in themed_refresh_buttons:
            try:
                widget.configure(
                    fg_color=theme_value("inactive_btn"),
                    hover_color=theme_value("refresh_hover"),
                    text_color=theme_value("title"),
                )
            except Exception:
                pass

        try:
            _restyle_tk_tree(mic_embed_host)
        except Exception:
            pass
        try:
            _restyle_tk_tree(kb_embed_host)
        except Exception:
            pass
        try:
            kb_canvas.configure(bg=theme_value("embed_bg"))
        except Exception:
            pass
        try:
            _comp_grid.configure(bg=theme_value("embed_bg"))
        except Exception:
            pass
        try:
            bat_bar_frame.configure(bg=theme_value("embed_bg"))
        except Exception:
            pass
        try:
            bat_style.configure(
                "HW.Horizontal.TProgressbar",
                troughcolor="#dfead7" if _current_theme[0] == "light" else "#1e2a3a",
                background=theme_value("pass"),
            )
        except Exception:
            pass
        try:
            br_canvas.configure(bg=theme_value("embed_bg"))
            _draw_brightness_bar(int(str(brightness_value.cget("text")).replace("Current:", "").replace("%", "").strip() or "0"))
        except Exception:
            pass

    _apply_theme_ref[0] = _apply_theme

    # ══════════════════════════════════════════════════════════════════
    # 0. OPERATOR SELECTION CARD (must select before tests begin)
    # ══════════════════════════════════════════════════════════════════
    _selected_operator = [None]  # Stores selected operator name
    _operator_confirmed = [False]  # Tracks if operator has been selected
    
    operator_card = card(body, "👤  Operator Selection", track_key="operator")
    
    # Header
    try:
        first_child = operator_card.winfo_children()[0]
        try:
            first_child.destroy()
        except Exception:
            pass
    except Exception:
        pass
    op_header_row = ctk.CTkFrame(operator_card, fg_color="transparent")
    op_header_row.pack(fill="x", padx=LAYOUT["card_inner_x"], pady=(12, 6))
    ctk.CTkLabel(op_header_row, text="👤  Operator Selection", 
                 font=ctk.CTkFont(size=14, weight="bold"), 
                 text_color=theme_value("title")).pack(side="left")
    
    # Status label
    operator_status = ctk.CTkLabel(operator_card, text="Select your name to begin testing", 
                                    font=ctk.CTkFont(size=12), text_color=theme_value("subtle"))
    operator_status.pack(anchor="w", padx=LAYOUT["card_inner_x"], pady=(0,10))
    
    # Operator buttons
    op_buttons_frame = ctk.CTkFrame(operator_card, fg_color="transparent")
    op_buttons_frame.pack(fill="x", padx=LAYOUT["card_inner_x"], pady=(0,10))
    
    operators = [
        ("AWITT", "#238636"),
        ("WCAHEE", "#1f6feb"),
        ("JVILLORIA", "#a371f7"),
    ]
    
    def _select_operator(name, color):
        """Handle operator selection."""
        _selected_operator[0] = name
        _operator_confirmed[0] = True
        
        # Update status
        operator_status.configure(
            text=f"✅ Operator: {name}",
            text_color="#7ee787"
        )
        
        # Disable all buttons after selection
        for btn in op_buttons:
            btn.configure(state="disabled", fg_color="#333333")
        
        # Highlight selected button
        sender_btn = None
        for btn in op_buttons:
            if btn._name == f"op_btn_{name}":
                sender_btn = btn
                btn.configure(fg_color=color, hover_color=color)
        
        # Auto-advance to Audio Changer after selection
        def _show_next():
            try:
                _highlight_and_show(ag_card)
            except Exception:
                pass
            try:
                # Start timer AFTER operator selection
                start_timer()
            except Exception:
                pass
            try:
                _run_audiog_clicked()
            except Exception:
                pass
            # Run network detection to pull info (NO auto-pass/fail yet)
            try:
                threading.Thread(target=lambda: _net_refresh(auto_pass_fail=False), daemon=True).start()
            except Exception:
                pass
        ui_call(_show_next)
    
    op_buttons = []
    for op_name, op_color in operators:
        btn = ctk.CTkButton(
            op_buttons_frame,
            text=op_name,
            width=140,
            height=36,
            fg_color=op_color,
            hover_color=op_color,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda n=op_name, c=op_color: _select_operator(n, c)
        )
        btn._name = f"op_btn_{op_name}"  # For identification
        btn.pack(side="left", padx=5, pady=5)
        op_buttons.append(btn)
    
    # Auto-advance: Operator -> Audio Changer (handled in _select_operator)
    # No need for button override since operator card auto-advances

    # ══════════════════════════════════════════════════════════════════
    # 1. AUDIOG RUNNER CARD (runs audiog.ps1 with result display)
    # ══════════════════════════════════════════════════════════════════
    ag_sys_row = ctk.CTkFrame(body, fg_color="transparent")
    ag_sys_row.pack(fill="x", padx=LAYOUT["card_pad_x"], pady=(8, 4))

    _AG_CARD_WIDTH = 300

    ag_card = card(ag_sys_row, "🔈  Audio Changer", track_key="ag")
    try:
        ag_card.pack_forget()
    except Exception:
        pass
    try:
        ag_card.configure(width=_AG_CARD_WIDTH)
        try:
            ag_card.pack_propagate(False)
        except Exception:
            pass
        ag_card.pack(side="left", fill="y", expand=False, padx=(0, 7), pady=0)
    except Exception:
        pass
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

    ag_status_label = _register_subtle_label(ctk.CTkLabel(ag_card, text="Running audio configuration...", font=ctk.CTkFont(size=12), text_color="#9fb3c8"))
    ag_status_label.pack(anchor="w", padx=14, pady=(0, 10))

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
            lbl = ctk.CTkLabel(ag_results_frame, text=line.strip(), font=ctk.CTkFont(size=10), text_color="#d4af37", justify="left", wraplength=260)
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
    sys_card = card(ag_sys_row, "🖥️  System Info", track_key="sys")
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
    try:
        sys_card.pack(side="left", fill="both", expand=True, padx=(7, 0), pady=0)
    except Exception:
        sys_card.pack(side="left", fill="both", expand=True, padx=(7, 0), pady=0)

    # Host frame — flow layout for system info chips (wraps to next row when full)
    _sys_host = ctk.CTkFrame(sys_card, fg_color="transparent")
    _sys_host.pack(fill="both", expand=True, padx=12, pady=(6, 12))

    sys_output_frame = ctk.CTkFrame(_sys_host, fg_color="transparent")
    sys_output_frame.pack(fill="both", expand=True)
    sys_output_labels = []
    sys_output_items = []
    _sys_reflow_after = [None]
    _sys_chip_font = None

    def _sys_line_allowed(line):
        try:
            low = str(line).lower()
        except Exception:
            return False
        if "system name" in low:
            return False
        allowed_keywords = (
            "system serial",
            "system sku",
            "system model",
            "bios password",
            "computrace",
            "cpu",
            "processor",
            "core",
            "intel",
            "amd",
            "ryzen",
            "gpu",
            "graphics",
            "video memory",
            "memory",
            "size:",
            "name:",
            "hard drive",
            "hard disk",
            "disk",
            "drive",
            "ssd",
            "hdd",
            "nvme",
            "model:",
            "storage",
            "omen",
            "monitor",
            "display",
        )
        return any(k in low for k in allowed_keywords)

    def _sys_chip_width(text):
        nonlocal _sys_chip_font
        try:
            if _sys_chip_font is None:
                import tkinter.font as tkfont
                _sys_chip_font = tkfont.Font(family="Segoe UI", size=10)
            return _sys_chip_font.measure(str(text)) + 22
        except Exception:
            return len(str(text)) * 7 + 22

    def _clear_sys_output():
        sys_output_items.clear()
        try:
            for w in sys_output_frame.winfo_children():
                w.destroy()
        except Exception:
            pass
        sys_output_labels.clear()

    def _reflow_sys_output():
        try:
            for w in sys_output_frame.winfo_children():
                w.destroy()
        except Exception:
            pass
        sys_output_labels.clear()

        try:
            max_w = max(sys_output_frame.winfo_width(), _sys_host.winfo_width(), 500) - 20
        except Exception:
            max_w = 900
        if max_w < 240:
            max_w = 1000

        row = None
        row_used = 0
        gap = 14

        for text in sys_output_items:
            text = str(text).strip()
            if not text:
                continue
            chip_w = _sys_chip_width(text)
            if row is None or (row_used > 0 and row_used + chip_w > max_w):
                row = ctk.CTkFrame(sys_output_frame, fg_color="transparent")
                row.pack(fill="x", anchor="w", pady=(0, 4))
                row_used = 0
            lbl = ctk.CTkLabel(
                row,
                text=text,
                font=ctk.CTkFont(size=10),
                text_color="#d4af37",
                anchor="w",
            )
            lbl.pack(side="left", padx=(0, gap), pady=2)
            sys_output_labels.append(lbl)
            row_used += chip_w

    def _schedule_sys_reflow():
        try:
            if _sys_reflow_after[0] is not None:
                app.after_cancel(_sys_reflow_after[0])
        except Exception:
            pass
        try:
            _sys_reflow_after[0] = app.after(60, _reflow_sys_output)
        except Exception:
            _reflow_sys_output()

    def _append_sys_line(line):
        try:
            if not _sys_line_allowed(line):
                return
            text = str(line).rstrip()
            if not text:
                return
            # Parse serial/SKU for the Form card
            low = text.lower()
            try:
                if "system serial" in low and ":" in text:
                    val = text.split(":", 1)[1].strip()
                    if val:
                        app.after(0, lambda v=val: _update_form_serial(v))
                elif "system sku" in low and ":" in text:
                    val = text.split(":", 1)[1].strip()
                    if val:
                        app.after(0, lambda v=val: _update_form_sku(v))
            except Exception:
                pass
            sys_output_items.append(text)
            if len(sys_output_items) > 120:
                sys_output_items.pop(0)
            _schedule_sys_reflow()
        except Exception:
            pass

    def _on_sys_output_configure(_event=None):
        _schedule_sys_reflow()

    try:
        sys_output_frame.bind("<Configure>", _on_sys_output_configure)
        _sys_host.bind("<Configure>", _on_sys_output_configure)
    except Exception:
        pass

    # Shared component state — populated during system info load
    _comp_vars = {}
    _comp_widgets = []
    comp_state_label = None

    # Form card serial/SKU state
    _bios_serial_base = [None]   # serial minus last 2 chars
    _bios_sku_base    = [None]   # sku minus last 4 chars
    _form_serial_entry = [None]  # tk.Entry widget reference
    _form_sku_entry    = [None]  # tk.Entry widget reference
    _form_serial_placeholder_active = [False]
    _form_sku_placeholder_active    = [False]

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
                        text_color=theme_value("success_text")
                    )
                else:
                    comp_state_label.configure(text="Components locked until System Info PASS", text_color="#9fb3c8")
        except Exception:
            pass

    def _update_form_serial(serial_full):
        """Called from system info parser with the full BIOS serial string."""
        try:
            serial_full = str(serial_full).strip()
            if len(serial_full) > 2:
                base = serial_full[:-2]
                suffix = serial_full[-2:]
            else:
                base = serial_full
                suffix = ""
            _bios_serial_base[0] = base
            entry = _form_serial_entry[0]
            if entry is None:
                return
            entry.configure(state="normal")
            entry.delete(0, "end")
            entry.insert(0, base + "  ← Add last 2 digits")
            entry.configure(fg="#888888")
            _form_serial_placeholder_active[0] = True
        except Exception:
            pass

    def _update_form_sku(sku_full):
        """Called from system info parser with the full BIOS SKU string."""
        try:
            sku_full = str(sku_full).strip()
            # Strip trailing model suffix like #ABA if present
            if "#" in sku_full:
                sku_full = sku_full.split("#")[0].strip()
            if len(sku_full) > 4:
                base = sku_full[:-4]
            else:
                base = sku_full
            _bios_sku_base[0] = base
            entry = _form_sku_entry[0]
            if entry is None:
                return
            entry.configure(state="normal")
            entry.delete(0, "end")
            entry.insert(0, base + "  ← Add last 4 digits")
            entry.configure(fg="#888888")
            _form_sku_placeholder_active[0] = True
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
                _clear_sys_output()
                for ln in str(report).splitlines():
                    if _sys_line_allowed(ln):
                        text = str(ln).rstrip()
                        if text:
                            sys_output_items.append(text)
                _reflow_sys_output()
                report_lower = str(report).lower()
                sys_ok = ("error" not in report_lower and "timed out" not in report_lower)
                if sys_ok:
                    if hasattr(sys_card, 'set_pass'):
                        try:
                            sys_card.set_pass()
                        except Exception:
                            pass
                    _set_components_active(True)
                else:
                    if hasattr(sys_card, 'set_fail'):
                        try:
                            sys_card.set_fail()
                        except Exception:
                            pass
                    _set_components_active(False)
                # After System Info finishes, return focus to Components only.
                # Battery should run only when manually refreshed or when the
                # sequencer explicitly reaches the battery step.
                try:
                    def _after_sys_next():
                        try:
                            _highlight_and_show(comp_card)
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
            _clear_sys_output()
        except Exception:
            pass
        try:
            ui_call(lambda: _highlight_and_show(sys_card))
        except Exception:
            pass
        threading.Thread(target=_load_system_info, daemon=True).start()

    # Run button removed; use header ⟳ to trigger system info

    comp_network_row = ctk.CTkFrame(body, fg_color="transparent")
    comp_network_row.pack(fill="x", padx=0, pady=0)

    # ══════════════════════════════════════════════════════════════════
    # 3. FORM CARD (replaces Components — serial & SKU entry)
    # ══════════════════════════════════════════════════════════════════
    comp_card = card(comp_network_row, "📋  Form", track_key="comp")
    try:
        comp_card.pack_configure(side="left", fill="x", expand=True, anchor="n", padx=(14, 7), pady=8)
    except Exception:
        pass
    try:
        try:
            comp_card.winfo_children()[0].destroy()
        except Exception:
            pass
        _form_header_row = ctk.CTkFrame(comp_card, fg_color="transparent")
        _form_header_row.pack(fill="x", padx=14, pady=(10, 6))
        _register_title_label(ctk.CTkLabel(_form_header_row, text="📋  Form",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#58a6ff")).pack(side="left")
        try:
            _register_refresh_button(ctk.CTkButton(_form_header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=_start_system_info_once)).pack(side="right")
        except Exception:
            pass
    except Exception:
        pass

    try:
        form_frame = ctk.CTkFrame(comp_card, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=14, pady=(4, 8))

        # ════════════════════════════════════════════════════════════
        # TOP ROW: Check Label (left) | Hotkeys (right)
        # ════════════════════════════════════════════════════════════
        form_top_row = _register_ctk_frame(ctk.CTkFrame(form_frame, fg_color="transparent"))
        form_top_row.pack(fill="x", pady=(0, 6))

        # ── Check Label sub-section ──────────────────────────────────
        check_label_frame = _register_ctk_frame(ctk.CTkFrame(form_top_row, fg_color=theme_value("embed_bg"), corner_radius=8))
        check_label_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))

        _register_title_label(ctk.CTkLabel(
            check_label_frame,
            text="  ● Check Label",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2ecc8a",
            anchor="w"
        )).pack(fill="x", padx=10, pady=(8, 6))

        fields_row = _register_ctk_frame(ctk.CTkFrame(check_label_frame, fg_color="transparent"))
        fields_row.pack(fill="x", padx=10, pady=(0, 10))

        # --- Serial column ---
        serial_col = _register_ctk_frame(ctk.CTkFrame(fields_row, fg_color="transparent"))
        serial_col.pack(side="left", fill="x", expand=True, padx=(0, 8))

        _register_subtle_label(ctk.CTkLabel(
            serial_col, text="Serial",
            font=ctk.CTkFont(size=11), text_color="#9fb3c8", anchor="w"
        )).pack(anchor="w", pady=(0, 3))

        serial_entry_frame = _register_ctk_frame(ctk.CTkFrame(serial_col, fg_color=theme_value("card_bg"), corner_radius=6, border_width=1, border_color="#3a3f4a"))
        serial_entry_frame.pack(fill="x")
        _serial_tk_entry = _register_tk_frame(tk.Entry(
            serial_entry_frame, font=("Segoe UI", 11),
            fg="#888888", bg=theme_value("card_bg"),
            insertbackground="#58a6ff", relief="flat", bd=4,
        ))
        _serial_tk_entry.pack(fill="x", ipady=4)
        _serial_tk_entry.insert(0, "Waiting for System Info...")
        _serial_tk_entry.configure(state="disabled")
        _form_serial_entry[0] = _serial_tk_entry

        _register_subtle_label(ctk.CTkLabel(
            serial_col, text="Write the last 2 digits",
            font=ctk.CTkFont(size=10), text_color="#6b7a8d", anchor="w"
        )).pack(anchor="w", pady=(3, 0))

        # --- SKU/Model column ---
        sku_col = _register_ctk_frame(ctk.CTkFrame(fields_row, fg_color="transparent"))
        sku_col.pack(side="left", fill="x", expand=True, padx=(8, 0))

        _register_subtle_label(ctk.CTkLabel(
            sku_col, text="SKU/Model",
            font=ctk.CTkFont(size=11), text_color="#9fb3c8", anchor="w"
        )).pack(anchor="w", pady=(0, 3))

        sku_entry_frame = _register_ctk_frame(ctk.CTkFrame(sku_col, fg_color=theme_value("card_bg"), corner_radius=6, border_width=1, border_color="#3a3f4a"))
        sku_entry_frame.pack(fill="x")
        _sku_tk_entry = _register_tk_frame(tk.Entry(
            sku_entry_frame, font=("Segoe UI", 11),
            fg="#888888", bg=theme_value("card_bg"),
            insertbackground="#58a6ff", relief="flat", bd=4,
        ))
        _sku_tk_entry.pack(fill="x", ipady=4)
        _sku_tk_entry.insert(0, "Waiting for System Info...")
        _sku_tk_entry.configure(state="disabled")
        _form_sku_entry[0] = _sku_tk_entry

        _register_subtle_label(ctk.CTkLabel(
            sku_col, text="Write the last 4 digits",
            font=ctk.CTkFont(size=10), text_color="#6b7a8d", anchor="w"
        )).pack(anchor="w", pady=(3, 0))

        # ── Serial entry click / keyboard logic ─────────────────────
        def _serial_on_click(event=None):
            try:
                entry = _form_serial_entry[0]
                if entry is None:
                    return
                if _form_serial_placeholder_active[0]:
                    entry.configure(state="normal", fg="#e0e0e0")
                    entry.delete(0, "end")
                    entry.insert(0, _bios_serial_base[0] or "")
                    entry.icursor("end")
                    _form_serial_placeholder_active[0] = False
            except Exception:
                pass

        def _serial_on_key(event=None):
            try:
                entry = _form_serial_entry[0]
                if entry is None:
                    return
                base = _bios_serial_base[0] or ""
                current = entry.get()
                if len(current) - len(base) > 2:
                    entry.delete(len(base) + 2, "end")
                if entry.index("insert") < len(base):
                    entry.icursor(len(base))
            except Exception:
                pass

        def _serial_on_backspace(event=None):
            try:
                entry = _form_serial_entry[0]
                if entry is None:
                    return
                base = _bios_serial_base[0] or ""
                if entry.index("insert") <= len(base):
                    return "break"
            except Exception:
                pass

        _serial_tk_entry.bind("<Button-1>", _serial_on_click)
        _serial_tk_entry.bind("<KeyRelease>", _serial_on_key)
        _serial_tk_entry.bind("<BackSpace>", _serial_on_backspace)

        # ── SKU entry click / keyboard logic ───────────────────────
        def _sku_on_click(event=None):
            try:
                entry = _form_sku_entry[0]
                if entry is None:
                    return
                if _form_sku_placeholder_active[0]:
                    entry.configure(state="normal", fg="#e0e0e0")
                    entry.delete(0, "end")
                    entry.insert(0, _bios_sku_base[0] or "")
                    entry.icursor("end")
                    _form_sku_placeholder_active[0] = False
            except Exception:
                pass

        def _sku_on_key(event=None):
            try:
                entry = _form_sku_entry[0]
                if entry is None:
                    return
                base = _bios_sku_base[0] or ""
                current = entry.get()
                if len(current) - len(base) > 4:
                    entry.delete(len(base) + 4, "end")
                if entry.index("insert") < len(base):
                    entry.icursor(len(base))
            except Exception:
                pass

        def _sku_on_backspace(event=None):
            try:
                entry = _form_sku_entry[0]
                if entry is None:
                    return
                base = _bios_sku_base[0] or ""
                if entry.index("insert") <= len(base):
                    return "break"
            except Exception:
                pass

        _sku_tk_entry.bind("<Button-1>", _sku_on_click)
        _sku_tk_entry.bind("<KeyRelease>", _sku_on_key)
        _sku_tk_entry.bind("<BackSpace>", _sku_on_backspace)

        # ── Hotkeys sub-section (top-right) ─────────────────────────
        hotkeys_frame = _register_ctk_frame(ctk.CTkFrame(form_top_row, fg_color=theme_value("embed_bg"), corner_radius=8))
        hotkeys_frame.pack(side="left", fill="both", padx=(6, 0))

        _register_title_label(ctk.CTkLabel(
            hotkeys_frame,
            text="  ● Hotkeys",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2ecc8a",
            anchor="w"
        )).pack(fill="x", padx=10, pady=(8, 6))

        hotkeys_cb_frame = _register_ctk_frame(ctk.CTkFrame(hotkeys_frame, fg_color="transparent"))
        hotkeys_cb_frame.pack(fill="x", padx=10, pady=(0, 10))

        _hotkey_vars = {}
        hotkey_items = [("Mic", "hk_mic"), ("Privacy", "hk_privacy"), ("Speakers", "hk_speakers"), ("Brightness", "hk_brightness")]
        for hk_label, hk_key in hotkey_items:
            hk_var = tk.BooleanVar(value=False)
            hk_cb = ctk.CTkCheckBox(hotkeys_cb_frame, text=hk_label, variable=hk_var,
                                    font=ctk.CTkFont(size=12))
            hk_cb.pack(side="left", padx=(0, 14), pady=4)
            _hotkey_vars[hk_key] = hk_var
            _comp_widgets.append(hk_cb)

        # ════════════════════════════════════════════════════════════
        # BOTTOM ROW: Components (left) | Unit Color (right)
        # ════════════════════════════════════════════════════════════
        form_bot_row = _register_ctk_frame(ctk.CTkFrame(form_frame, fg_color="transparent"))
        form_bot_row.pack(fill="x", pady=(0, 0))

        # ── Components sub-section (bottom-left) ────────────────────
        comp_inner_frame = _register_ctk_frame(ctk.CTkFrame(form_bot_row, fg_color=theme_value("embed_bg"), corner_radius=8))
        comp_inner_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))

        _register_title_label(ctk.CTkLabel(
            comp_inner_frame,
            text="  ● Components",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2ecc8a",
            anchor="w"
        )).pack(fill="x", padx=10, pady=(8, 6))

        comp_state_label = _register_subtle_label(ctk.CTkLabel(
            comp_inner_frame,
            text="Components locked until System Info PASS",
            font=ctk.CTkFont(size=10),
            text_color="#9fb3c8",
            anchor="w"
        ))
        comp_state_label.pack(anchor="w", padx=12, pady=(0, 4))

        _comp_grid = _register_tk_frame(tk.Frame(comp_inner_frame, bg=theme_value("embed_bg")))
        _comp_grid.pack(fill="x", padx=10, pady=(0, 8))

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

        # ── Unit Color sub-section (bottom-right) ───────────────────
        color_frame = _register_ctk_frame(ctk.CTkFrame(form_bot_row, fg_color=theme_value("embed_bg"), corner_radius=8))
        color_frame.pack(side="left", fill="both", padx=(6, 0))

        _register_title_label(ctk.CTkLabel(
            color_frame,
            text="  ● Unit Color",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2ecc8a",
            anchor="w"
        )).pack(fill="x", padx=10, pady=(8, 6))

        color_swatches_frame = _register_ctk_frame(ctk.CTkFrame(color_frame, fg_color="transparent"))
        color_swatches_frame.pack(fill="x", padx=10, pady=(0, 10))

        _selected_color = [None]

        unit_colors = [
            ("BLACK",  "#1a1a1a", "#ffffff"),
            ("WHITE",  "#f0f0f0", "#888888"),
            ("RED",    "#cc2222", "#ffffff"),
            ("BLUE",   "#1a50cc", "#ffffff"),
            ("GREEN",  "#1a8c1a", "#ffffff"),
            ("YELLOW", "#cccc00", "#333333"),
            ("ORANGE", "#cc6600", "#ffffff"),
            ("PURPLE", "#7722cc", "#ffffff"),
            ("PINK",   "#f0a0b0", "#333333"),
            ("BROWN",  "#7a2a10", "#ffffff"),
            ("GRAY",   "#707070", "#ffffff"),
            ("SILVER", "#c0c0c0", "#333333"),
        ]

        _color_btn_refs = {}

        def _make_color_swatch(parent, label, bg_hex, fg_hex):
            swatch_outer = _register_ctk_frame(ctk.CTkFrame(
                parent, fg_color=theme_value("card_bg"), corner_radius=8,
                border_width=2, border_color="#3a3f4a", width=62, height=62
            ))
            swatch_outer.pack_propagate(False)

            color_dot = _register_tk_frame(tk.Frame(swatch_outer, bg=bg_hex, width=36, height=36, cursor="hand2"))
            color_dot.pack(pady=(6, 2))

            lbl = ctk.CTkLabel(swatch_outer, text=label, font=ctk.CTkFont(size=9, weight="bold"),
                               text_color="#9fb3c8")
            lbl.pack()

            def _select(l=label, outer=swatch_outer, dot=color_dot, bg=bg_hex):
                _selected_color[0] = l
                # Reset all borders
                for ref in _color_btn_refs.values():
                    try:
                        ref.configure(border_color="#3a3f4a")
                    except Exception:
                        pass
                # Highlight selected
                try:
                    outer.configure(border_color="#2ecc8a")
                except Exception:
                    pass

            color_dot.bind("<Button-1>", lambda e, fn=_select: fn())
            swatch_outer.bind("<Button-1>", lambda e, fn=_select: fn())
            lbl.bind("<Button-1>", lambda e, fn=_select: fn())
            _color_btn_refs[label] = swatch_outer
            return swatch_outer

        # Row 1: first 9 colors
        color_row1 = _register_ctk_frame(ctk.CTkFrame(color_swatches_frame, fg_color="transparent"))
        color_row1.pack(fill="x", pady=(0, 4))
        for label, bg, fg in unit_colors[:9]:
            _make_color_swatch(color_row1, label, bg, fg).pack(side="left", padx=3)

        # Row 2: last 3 colors
        color_row2 = _register_ctk_frame(ctk.CTkFrame(color_swatches_frame, fg_color="transparent"))
        color_row2.pack(fill="x")
        for label, bg, fg in unit_colors[9:]:
            _make_color_swatch(color_row2, label, bg, fg).pack(side="left", padx=3)

    except Exception:
        pass

    # ══════════════════════════════════════════════════════════════════
    # 3B. NETWORK ADAPTERS INFO CARD
    # ══════════════════════════════════════════════════════════════════
    net_card = card(comp_network_row, "📶  Network Adapters", track_key="net")
    try:
        net_card.pack_configure(side="left", fill="both", expand=True, padx=(7, 14), pady=8)
    except Exception:
        pass
    try:
        try:
            net_card.winfo_children()[0].destroy()
        except Exception:
            pass
    except Exception:
        pass

    net_header_row = ctk.CTkFrame(net_card, fg_color="transparent")
    net_header_row.pack(fill="x", padx=14, pady=(10, 6))
    _register_title_label(ctk.CTkLabel(
        net_header_row,
        text="📶  Network Adapters",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color="#58a6ff"
    )).pack(side="left")

    net_content = ctk.CTkFrame(net_card, fg_color="transparent")
    net_content.pack(fill="x", expand=False, padx=14, pady=(2, 12))

    net_status_lbl = _register_subtle_label(ctk.CTkLabel(
        net_content,
        text="Run refresh or sequencer to check adapters.",
        font=ctk.CTkFont(size=11),
        text_color="#9fb3c8",
        justify="left"
    ))
    net_status_lbl.pack(anchor="w", pady=(0, 8))

    net_section_row = ctk.CTkFrame(net_content, fg_color="transparent")
    net_section_row.pack(fill="x", expand=False)

    net_sections = {}

    def _make_net_section(parent, title):
        section = _register_ctk_frame(ctk.CTkFrame(parent, fg_color=theme_value("embed_bg"), corner_radius=8))
        section.pack(side="left", fill="both", expand=True, padx=4, pady=(0, 4))

        _register_title_label(ctk.CTkLabel(
            section,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#58a6ff"
        )).pack(anchor="w", padx=10, pady=(8, 2))

        status_label = _register_subtle_label(ctk.CTkLabel(
            section,
            text="No adapters detected",
            font=ctk.CTkFont(size=11),
            text_color="#9fb3c8",
            justify="left"
        ))
        status_label.pack(anchor="w", padx=10, pady=(2, 0))

        detail_labels = []
        detail_rows = [
            ("Name", "body_text"),
            ("Description", "muted_text"),
            ("Adapter status", "body_text"),
            ("Active", "body_text"),
            ("Connected to network", "body_text"),
            ("Network name", "muted_text"),
            ("Network category", "muted_text"),
        ]
        for label_text, color_key in detail_rows:
            lbl = ctk.CTkLabel(
                section,
                text=f"{label_text}: --",
                font=ctk.CTkFont(size=11),
                text_color=theme_value(color_key),
                justify="left",
                wraplength=180
            )
            lbl._theme_color_key = color_key
            lbl.pack(anchor="w", padx=(10, 0), pady=0)
            detail_labels.append(lbl)

        return {
            "status": status_label,
            "labels": detail_labels,
        }

    net_sections["wifi"] = _make_net_section(net_section_row, "Wi-Fi Adapters")
    net_sections["ethernet"] = _make_net_section(net_section_row, "Ethernet Adapters")

    def _set_net_section(section_widgets, adapter):
        labels = section_widgets["labels"]
        if not adapter:
            section_widgets["status"].configure(text="No adapters detected.", text_color="#ff7b72")
            for lbl in labels:
                lbl.configure(text="")
            return

        connected = str(adapter.get("Connected") or "No")
        connected_color = "#2ecc71" if connected.lower() == "yes" else "#e3b341"

        section_widgets["status"].configure(text="Adapter detected:", text_color="#2ecc71")
        label_values = [
            f"Name: {adapter.get('Name') or '--'}",
            f"Description: {adapter.get('Description') or '--'}",
            f"Adapter status: {adapter.get('AdapterStatus') or '--'}",
            f"Active: {adapter.get('Active') or 'No'}",
            f"Connected to network: {connected}",
            f"Network name: {adapter.get('NetworkName') or '--'}",
            f"Network category: {adapter.get('NetworkCategory') or '--'}",
        ]
        for idx, text in enumerate(label_values):
            try:
                base_color = theme_value(getattr(labels[idx], "_theme_color_key", "body_text"))
                color = connected_color if idx == 4 else base_color
                labels[idx].configure(text=text, text_color=color)
            except Exception:
                pass

    def _net_refresh(auto_pass_fail=True):
        """Run network adapter detection.
        
        Args:
            auto_pass_fail: If True, automatically set pass/fail based on WiFi detection.
                           If False, only collect data without setting pass/fail.
        """
        try:
            data = _get_network_adapter_data()
            wifi_adapter = data.get("wifi", [None])[0] if data.get("wifi") else None
            ethernet_adapter = data.get("ethernet", [None])[0] if data.get("ethernet") else None

            def _apply():
                if not widget_exists(net_card):
                    return

                wifi_count = len(data.get("wifi", []))
                ethernet_count = len(data.get("ethernet", []))
                total_count = wifi_count + ethernet_count

                net_status_lbl.configure(
                    text=f"Detected {wifi_count} Wi-Fi / {ethernet_count} Ethernet adapter(s)",
                    text_color="#9fb3c8"
                )

                _set_net_section(net_sections["wifi"], wifi_adapter)
                _set_net_section(net_sections["ethernet"], ethernet_adapter)

                # Only auto-pass/fail if called from sequencer (not from operator selection)
                if auto_pass_fail:
                    try:
                        if wifi_count > 0 and hasattr(net_card, "set_pass"):
                            net_card.set_pass()
                        elif wifi_count == 0 and hasattr(net_card, "set_fail"):
                            net_card.set_fail()
                    except Exception:
                        pass

            ui_call(_apply)

        except Exception as e:
            def _apply_error():
                if not widget_exists(net_card):
                    return
                net_status_lbl.configure(text=f"Network check error: {e}", text_color="#ff7b72")
                # Only auto-fail if called from sequencer
                if auto_pass_fail:
                    try:
                        if hasattr(net_card, "set_fail"):
                            net_card.set_fail()
                    except Exception:
                        pass
            ui_call(_apply_error)

    # AUTO MOVE TO BATTERY WHEN NETWORK FINISHES
    def _on_net_marked():
        """After Network PASS/FAIL, show Battery card and run battery check."""
        def _show_and_start_bat():
            try:
                _highlight_and_show(bat_card)
            except Exception:
                pass
            try:
                threading.Thread(target=_bat_refresh, daemon=True).start()
            except Exception:
                pass
        ui_call(_show_and_start_bat)

    try:
        if hasattr(net_card, 'set_pass') and hasattr(net_card, 'pass_btn'):
            _net_orig_pass = net_card.set_pass
            _net_orig_fail = net_card.set_fail

            def _net_pass():
                _net_orig_pass()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(bat_card))
                    return
                _on_net_marked()

            def _net_fail():
                _net_orig_fail()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(bat_card))
                    return
                _on_net_marked()

            net_card.set_pass = _net_pass
            net_card.set_fail = _net_fail
            net_card.pass_btn.configure(command=_net_pass)
            net_card.fail_btn.configure(command=_net_fail)
    except Exception:
        pass

    try:
        ctk.CTkButton(
            net_header_row,
            text="⟳",
            width=28,
            height=28,
            fg_color="#444444",
            hover_color="#555555",
            command=lambda: threading.Thread(target=_net_refresh, daemon=True).start()
        ).pack(side="right")
    except Exception:
        pass

    def _on_components_marked():
        """After Components PASS/FAIL, show Network card and run adapter check."""
        def _show_net():
            try:
                _highlight_and_show(net_card)
            except Exception:
                pass
        ui_call(_show_net)
        threading.Thread(target=_net_refresh, daemon=True).start()

    try:
        if hasattr(comp_card, 'set_pass') and hasattr(comp_card, 'pass_btn'):
            _comp_orig_pass = comp_card.set_pass
            _comp_orig_fail = comp_card.set_fail

            def _comp_pass():
                _comp_orig_pass()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(net_card))
                    return
                _on_components_marked()

            def _comp_fail():
                _comp_orig_fail()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(net_card))
                    return
                _on_components_marked()

            comp_card.set_pass = _comp_pass
            comp_card.set_fail = _comp_fail
            comp_card.pass_btn.configure(command=_comp_pass)
            comp_card.fail_btn.configure(command=_comp_fail)
    except Exception:
        pass

    # ══════════════════════════════════════════════════════════════════
    # 4. BATTERY + TOUCHPAD ROW
    # ══════════════════════════════════════════════════════════════════
    bat_tp_row = ctk.CTkFrame(body, fg_color="transparent")
    bat_tp_row.pack(fill="x", padx=14, pady=8)

    bat_card = card(bat_tp_row, "🔋  Battery", track_key="bat")
    try:
        bat_card.pack_forget()
    except Exception:
        pass
    try:
        bat_card.pack(side="left", fill="both", expand=True, padx=(0, 7), pady=0)
    except Exception:
        pass
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
        _register_title_label(ctk.CTkLabel(header_row, text="🔋  Battery", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff")).pack(side="left")
        try:
            _register_refresh_button(ctk.CTkButton(header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=lambda: threading.Thread(target=_bat_refresh, daemon=True).start())).pack(side="right")
        except Exception:
            pass
    except Exception:
        pass

    bat_device  = _register_subtle_label(ctk.CTkLabel(bat_card, text="Loading...", font=ctk.CTkFont(size=11), text_color="#9fb3c8"))
    bat_device.pack(anchor="w", padx=14)

    bat_level_lbl = ctk.CTkLabel(bat_card, text="--%", font=ctk.CTkFont(size=28, weight="bold"), text_color="#7ee787")
    bat_level_lbl.pack(anchor="w", padx=14, pady=(4,0))

    bat_bar_frame = _register_tk_frame(tk.Frame(bat_card, bg=theme_value("embed_bg")))
    bat_bar_frame.pack(anchor="w", padx=14, pady=(4, 8))
    bat_style = ttk.Style()
    bat_style.theme_use("clam")
    bat_style.configure("HW.Horizontal.TProgressbar", thickness=14, troughcolor="#1e2a3a", background="#7ee787")
    bat_bar = ttk.Progressbar(bat_bar_frame, orient="horizontal", length=240,
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

    bat_cap_lbl = _register_subtle_label(ctk.CTkLabel(bat_card, text="Capacity: --", font=ctk.CTkFont(size=11), text_color="#9fb3c8"))
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

    # Battery refresh is intentionally manual or sequencer-driven only.
    # Do not auto-start this card on app load because it can interfere with
    # the active sequence flow before the battery step is reached.

    # AUTO ADVANCE: Battery -> Touchpad
    def _on_bat_marked():
        """After Battery PASS/FAIL, show Touchpad card and start touchpad test."""
        def _show_and_start_tp():
            try:
                _highlight_and_show(tp_card)
            except Exception:
                pass
            try:
                _start_touchpad_embed()
            except Exception:
                pass
        ui_call(_show_and_start_tp)

    try:
        if hasattr(bat_card, 'set_pass') and hasattr(bat_card, 'pass_btn'):
            _bat_orig_pass = bat_card.set_pass
            _bat_orig_fail = bat_card.set_fail

            def _bat_pass():
                _bat_orig_pass()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(tp_card))
                    return
                _on_bat_marked()

            def _bat_fail():
                _bat_orig_fail()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(tp_card))
                    return
                _on_bat_marked()

            bat_card.set_pass = _bat_pass
            bat_card.set_fail = _bat_fail
            bat_card.pass_btn.configure(command=_bat_pass)
            bat_card.fail_btn.configure(command=_bat_fail)
    except Exception:
        pass

    # Row for Speaker, Mic, and Brightness
    test_row_compact_top = _register_tk_frame(tk.Frame(body, bg=theme_value("screen_bg")))
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
    # AUTO ADVANCE: Speaker -> Microphone
    def _on_spk_marked():
        """After Speaker PASS/FAIL, show Microphone card and start mic test."""
        def _show_and_start_mic():
            try:
                _highlight_and_show(mic_card)
            except Exception:
                pass
            try:
                if 'mic_tester' in dir() and mic_tester is not None:
                    if hasattr(mic_tester, 'start_test'):
                        mic_tester.start_test()
                    elif hasattr(mic_tester, 'start'):
                        mic_tester.start()
                    elif hasattr(mic_tester, 'run_test'):
                        mic_tester.run_test()
            except Exception:
                pass
        ui_call(_show_and_start_mic)

    try:
        if hasattr(spk_card, 'set_pass') and hasattr(spk_card, 'pass_btn'):
            _spk_orig_pass = spk_card.set_pass
            _spk_orig_fail = spk_card.set_fail

            def _spk_pass():
                _spk_stop()
                _spk_orig_pass()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(mic_card))
                    return
                _on_spk_marked()

            def _spk_fail():
                _spk_stop()
                _spk_orig_fail()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(mic_card))
                    return
                _on_spk_marked()

            spk_card.set_pass = _spk_pass
            spk_card.set_fail = _spk_fail
            spk_card.pass_btn.configure(command=_spk_pass)
            spk_card.fail_btn.configure(command=_spk_fail)
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
        _register_title_label(ctk.CTkLabel(header_row, text="🎤  Microphone Test", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff")).pack(side="left")
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
                pass
            except Exception:
                pass
        try:
            _register_refresh_button(ctk.CTkButton(header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=lambda: _mic_refresh_clicked())).pack(side="right")
        except Exception:
            pass
    except Exception:
        pass
    # Embed the full MicTest2 UI inside this card (non-fullscreen)
    mic_embed_host = _register_tk_frame(tk.Frame(mic_card, bg=theme_value("embed_bg"), height=300))
    # give it a fixed height and prevent geometry propagation
    mic_embed_host.pack(fill="both", expand=False, padx=14, pady=(0, 10))
    try:
        mic_embed_host.pack_propagate(False)
    except Exception:
        pass

    try:
        # MicTest2.MicrophoneTesterApp calls window-only methods
        # (.title, .geometry, .minsize, .protocol) on whatever is passed as root.
        # Wrap mic_embed_host in a subclass that silently absorbs those calls
        # so the app builds its widgets into the embedded frame correctly.
        class _FrameWindowProxy(tk.Frame):
            """A tk.Frame that silently swallows window-manager-only calls."""
            def title(self, *a, **k): pass
            def geometry(self, *a, **k): pass
            def minsize(self, *a, **k): pass
            def maxsize(self, *a, **k): pass
            def resizable(self, *a, **k): pass
            def protocol(self, *a, **k): pass
            def iconbitmap(self, *a, **k): pass
            def state(self, *a, **k): return "normal"
            def attributes(self, *a, **k): pass
            def withdraw(self, *a, **k): pass
            def deiconify(self, *a, **k): pass

        mic_tester = None
        if 'MicTest2' in globals() and MicTest2 is not None:
            try:
                proxy = _FrameWindowProxy(mic_embed_host, bg=theme_value("embed_bg"))
                proxy.pack(fill="both", expand=True, padx=0, pady=0)
                mic_tester = MicTest2.MicrophoneTesterApp(proxy)
                try:
                    _restyle_tk_tree(proxy)
                except Exception:
                    pass
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
    
    # AUTO ADVANCE: Microphone -> Brightness
    def _on_mic_marked():
        """After Microphone PASS/FAIL, show Brightness card and start brightness test."""
        def _show_and_start_br():
            try:
                _highlight_and_show(brightness_card)
            except Exception:
                pass
            try:
                threading.Thread(target=_start_brightness_test, daemon=True).start()
            except Exception:
                pass
        ui_call(_show_and_start_br)
    
    try:
        if hasattr(mic_card, 'set_pass') and hasattr(mic_card, 'pass_btn'):
            _mic_orig_pass = mic_card.set_pass
            _mic_orig_fail = mic_card.set_fail
    
            def _mic_pass():
                _mic_orig_pass()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(brightness_card))
                    return
                _on_mic_marked()
    
            def _mic_fail():
                _mic_orig_fail()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(brightness_card))
                    return
                _on_mic_marked()
    
            mic_card.set_pass = _mic_pass
            mic_card.set_fail = _mic_fail
            mic_card.pass_btn.configure(command=_mic_pass)
            mic_card.fail_btn.configure(command=_mic_fail)
    except Exception:
        pass
    
    # \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
    # 4. CAMERA CARD
    # \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
    # Touchpad Test card (paired with Battery on the same row)
    tp_card = card(bat_tp_row, "🖱️  Touchpad Test", track_key="tp")
    try:
        tp_card.pack_forget()
        tp_card.pack(side="left", fill="both", expand=True, padx=(7, 0), pady=0)
    except Exception:
        pass
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
    tp_host = _register_tk_frame(tk.Frame(tp_card, bg=theme_value("embed_bg")))
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
    # AUTO ADVANCE: Touchpad -> Speaker
    def _on_tp_marked():
        """After Touchpad PASS/FAIL, show Speaker card and start speaker test."""
        def _show_and_start_spk():
            try:
                _highlight_and_show(spk_card)
            except Exception:
                pass
            try:
                _spk_play()
            except Exception:
                pass
        ui_call(_show_and_start_spk)

    try:
        if hasattr(tp_card, 'set_pass') and hasattr(tp_card, 'pass_btn'):
            _tp_orig_pass = tp_card.set_pass
            _tp_orig_fail = tp_card.set_fail

            def _tp_pass():
                _stop_touchpad_embed()
                _tp_orig_pass()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(spk_card))
                    return
                _on_tp_marked()

            def _tp_fail():
                _stop_touchpad_embed()
                _tp_orig_fail()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(spk_card))
                    return
                _on_tp_marked()

            tp_card.set_pass = _tp_pass
            tp_card.set_fail = _tp_fail
            tp_card.pass_btn.configure(command=_tp_pass)
            tp_card.fail_btn.configure(command=_tp_fail)
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
    br_canvas_frame = _register_tk_frame(tk.Frame(brightness_card, bg=theme_value("embed_bg")))
    br_canvas_frame.pack(fill="x", padx=14, pady=(6,6))
    br_canvas = tk.Canvas(br_canvas_frame, height=40, bg=theme_value("embed_bg"), highlightthickness=0)
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
    
    # AUTO ADVANCE: Brightness -> Smart Card Reader (Port Checker removed)
    def _on_br_marked():
        """After Brightness PASS/FAIL, show Smart Card Reader card and start smart card test."""
        def _show_and_start_smartcard():
            try:
                _highlight_and_show(smartcard_card)
            except Exception:
                pass
            try:
                threading.Thread(target=_smartcard_refresh, daemon=True).start()
            except Exception:
                pass
        ui_call(_show_and_start_smartcard)
    
    try:
        if hasattr(brightness_card, 'set_pass') and hasattr(brightness_card, 'pass_btn'):
            _br_orig_pass = brightness_card.set_pass
            _br_orig_fail = brightness_card.set_fail
    
            def _br_pass():
                _br_orig_pass()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(smartcard_card))
                    return
                _on_br_marked()
    
            def _br_fail():
                _br_orig_fail()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(smartcard_card))
                    return
                _on_br_marked()
    
            brightness_card.set_pass = _br_pass
            brightness_card.set_fail = _br_fail
            brightness_card.pass_btn.configure(command=_br_pass)
            brightness_card.fail_btn.configure(command=_br_fail)
    except Exception:
        pass

    # ══════════════════════════════════════════════════════════════════
    # SMART CARD READER CARD
    # ══════════════════════════════════════════════════════════════════
    smartcard_card = card(body, "💳  Smart Card Reader", track_key="smartcard")
    try:
        smartcard_card.pack_forget()
    except Exception:
        pass
    try:
        smartcard_card.winfo_children()[0].destroy()
    except Exception:
        pass

    # Header with refresh button
    sc_header_row = ctk.CTkFrame(smartcard_card, fg_color="transparent")
    sc_header_row.pack(fill="x", padx=14, pady=(10,6))
    ctk.CTkLabel(sc_header_row, text="💳  Smart Card Reader", 
                 font=ctk.CTkFont(size=14, weight="bold"), 
                 text_color="#58a6ff").pack(side="left")

    # Refresh button
    ctk.CTkButton(
        sc_header_row, 
        text="⟳", 
        width=28, 
        height=28, 
        fg_color="#444444", 
        hover_color="#555555", 
        command=lambda: threading.Thread(target=_smartcard_refresh, daemon=True).start()
    ).pack(side="right")

    # Status display
    sc_status = ctk.CTkLabel(
        smartcard_card,
        text="Checking for smart card readers...",
        font=ctk.CTkFont(size=12),
        text_color="#9fb3c8",
    )
    sc_status.pack(anchor="w", padx=14, pady=(0, 6))

    # Smart card info display frame
    sc_info_frame = _register_ctk_frame(ctk.CTkFrame(smartcard_card, fg_color=theme_value("embed_bg"), corner_radius=8))
    sc_info_frame.pack(fill="x", padx=14, pady=(0, 10))

    sc_service_lbl = _register_subtle_label(ctk.CTkLabel(
        sc_info_frame, 
        text="Service: --", 
        font=ctk.CTkFont(size=11), 
        text_color="#9fb3c8"
    ))
    sc_service_lbl.pack(anchor="w", padx=12, pady=(10, 4))

    sc_readers_lbl = _register_subtle_label(ctk.CTkLabel(
        sc_info_frame, 
        text="Readers Found: --", 
        font=ctk.CTkFont(size=11), 
        text_color="#9fb3c8"
    ))
    sc_readers_lbl.pack(anchor="w", padx=12, pady=(4, 4))

    sc_details_text = _register_text_widget(tk.Text(
        sc_info_frame,
        bg=theme_value("embed_bg"),
        fg=theme_value("embed_text"),
        font=("Consolas", 10),
        height=6,
        wrap="word",
        borderwidth=0,
        highlightthickness=0,
    ))
    sc_details_text.pack(fill="x", padx=12, pady=(4, 10))
    sc_details_text.configure(state="disabled")

    # Smart card detection variables
    _sc_check_running = [False]

    def _smartcard_refresh():
        """Run PowerShell script to detect smart card readers"""
        if _sc_check_running[0]:
            return
        _sc_check_running[0] = True
        
        try:
            ui_call(lambda: sc_status.configure(text="Detecting smart card readers...", text_color="#58a6ff"))
            
            # Run the PowerShell script
            ps_path = os.path.join(BASE, "SmartCardTest.ps1")
            
            if not os.path.exists(ps_path):
                ui_call(lambda: sc_status.configure(text="SmartCardTest.ps1 not found!", text_color="#ff7b72"))
                _sc_check_running[0] = False
                return
            
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout
            error = result.stderr
            
            # Parse the output
            service_name = "Not Found"
            service_status = "Unknown"
            readers_found = 0
            working_readers = 0
            reader_details = []
            test_result = "FAIL"
            
            for line in output.split('\n'):
                line = line.strip()
                if line.startswith("SERVICE_NAME:"):
                    service_name = line.split(":", 1)[1].strip()
                elif line.startswith("SERVICE_STATUS:"):
                    service_status = line.split(":", 1)[1].strip()
                elif line.startswith("READER_FOUND:") and "NONE" not in line:
                    readers_found += 1
                    reader_details.append(line.split(":", 1)[1].strip())
                elif line.startswith("READER_STATUS:") and "OK" in line.upper():
                    working_readers += 1
                elif line.startswith("TOTAL_READERS:"):
                    readers_found = int(line.split(":", 1)[1].strip())
                elif line.startswith("WORKING_READERS:"):
                    working_readers = int(line.split(":", 1)[1].strip())
                elif line.startswith("TEST_RESULT:"):
                    test_result = line.split(":", 1)[1].strip()
            
            # Update UI
            def _update_ui():
                sc_status.configure(
                    text=f"Smart Card Test: {test_result}",
                    text_color="#7ee787" if test_result == "PASS" else "#ff7b72"
                )
                
                sc_service_lbl.configure(
                    text=f"Service: {service_name} ({service_status})"
                )
                
                sc_readers_lbl.configure(
                    text=f"Readers Found: {readers_found} ({working_readers} working)"
                )
                
                # Update details text
                sc_details_text.configure(state="normal")
                sc_details_text.delete(1.0, "end")
                
                if reader_details:
                    sc_details_text.insert("end", "Detected Readers:\n")
                    for i, reader in enumerate(reader_details, 1):
                        sc_details_text.insert("end", f"  {i}. {reader}\n")
                else:
                    sc_details_text.insert("end", "No smart card readers detected.\n\n")
                    sc_details_text.insert("end", "Possible reasons:\n")
                    sc_details_text.insert("end", "  • No smart card reader hardware present\n")
                    sc_details_text.insert("end", "  • Driver not installed\n")
                    sc_details_text.insert("end", "  • Reader disabled in BIOS\n")
                
                sc_details_text.configure(state="disabled")
                
                # Auto-mark pass/fail
                if test_result == "PASS":
                    if hasattr(smartcard_card, 'set_pass'):
                        smartcard_card.set_pass()
                else:
                    if hasattr(smartcard_card, 'set_fail'):
                        smartcard_card.set_fail()
            
            ui_call(_update_ui)
            
        except subprocess.TimeoutExpired:
            ui_call(lambda: sc_status.configure(text="Smart card detection timed out", text_color="#ff7b72"))
        except Exception as e:
            ui_call(lambda: sc_status.configure(text=f"Error: {str(e)}", text_color="#ff7b72"))
        finally:
            _sc_check_running[0] = False

    # AUTO ADVANCE: Smart Card Reader -> USB Port Detection
    def _on_smartcard_marked():
        """After Smart Card Reader PASS/FAIL, show USB Port Detection card and start USB test."""
        def _show_and_start_usb():
            try:
                _highlight_and_show(usb_card)
            except Exception:
                pass
            try:
                threading.Thread(target=_usbport_refresh, daemon=True).start()
            except Exception:
                pass
        ui_call(_show_and_start_usb)

    try:
        if hasattr(smartcard_card, 'set_pass') and hasattr(smartcard_card, 'pass_btn'):
            _sc_orig_pass = smartcard_card.set_pass
            _sc_orig_fail = smartcard_card.set_fail
            
            def _sc_pass():
                _sc_orig_pass()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(usb_card))
                    return
                _on_smartcard_marked()
            
            def _sc_fail():
                _sc_orig_fail()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(usb_card))
                    return
                _on_smartcard_marked()
            
            smartcard_card.set_pass = _sc_pass
            smartcard_card.set_fail = _sc_fail
            smartcard_card.pass_btn.configure(command=_sc_pass)
            smartcard_card.fail_btn.configure(command=_sc_fail)
    except Exception:
        pass

    # ══════════════════════════════════════════════════════════════════
    # USB PORT DETECTION CARD
    # ══════════════════════════════════════════════════════════════════
    usb_card = card(body, "🔌  USB Port Detection", track_key="usb")
    try:
        usb_card.pack_forget()
    except Exception:
        pass
    try:
        usb_card.winfo_children()[0].destroy()
    except Exception:
        pass

    # Header with refresh button
    usb_header_row = ctk.CTkFrame(usb_card, fg_color="transparent")
    usb_header_row.pack(fill="x", padx=14, pady=(10,6))
    ctk.CTkLabel(usb_header_row, text="🔌  USB Port Detection", 
                 font=ctk.CTkFont(size=14, weight="bold"), 
                 text_color="#58a6ff").pack(side="left")

    # Refresh button
    ctk.CTkButton(
        usb_header_row, 
        text="⟳", 
        width=28, 
        height=28, 
        fg_color="#444444", 
        hover_color="#555555", 
        command=lambda: threading.Thread(target=_usbport_refresh, daemon=True).start()
    ).pack(side="right")

    # Status display
    usb_status = ctk.CTkLabel(
        usb_card,
        text="Detecting USB ports and testing connectivity...",
        font=ctk.CTkFont(size=12),
        text_color="#9fb3c8",
    )
    usb_status.pack(anchor="w", padx=14, pady=(0, 6))

    # USB info display frame
    usb_info_frame = _register_ctk_frame(ctk.CTkFrame(usb_card, fg_color=theme_value("embed_bg"), corner_radius=8))
    usb_info_frame.pack(fill="x", padx=14, pady=(0, 10))

    usb_summary_lbl = _register_subtle_label(ctk.CTkLabel(
        usb_info_frame, 
        text="Controllers: -- | Hubs: -- | Devices: --", 
        font=ctk.CTkFont(size=11, weight="bold"), 
        text_color="#9fb3c8"
    ))
    usb_summary_lbl.pack(anchor="w", padx=12, pady=(10, 4))

    usb_versions_lbl = _register_subtle_label(ctk.CTkLabel(
        usb_info_frame, 
        text="USB 2.0: -- | USB 3.0: -- | USB-C: --", 
        font=ctk.CTkFont(size=11), 
        text_color="#9fb3c8"
    ))
    usb_versions_lbl.pack(anchor="w", padx=12, pady=(4, 4))

    usb_connections_lbl = _register_subtle_label(ctk.CTkLabel(
        usb_info_frame, 
        text="Active Connections: --", 
        font=ctk.CTkFont(size=11), 
        text_color="#9fb3c8"
    ))
    usb_connections_lbl.pack(anchor="w", padx=12, pady=(4, 10))

    # USB device list
    usb_details_text = _register_text_widget(tk.Text(
        usb_info_frame,
        bg=theme_value("embed_bg"),
        fg=theme_value("embed_text"),
        font=("Consolas", 10),
        height=8,
        wrap="word",
        borderwidth=0,
        highlightthickness=0,
    ))
    usb_details_text.pack(fill="x", padx=12, pady=(0, 10))
    usb_details_text.configure(state="disabled")

    # USB port detection variables
    _usb_check_running = [False]

    def _usbport_refresh():
        """Run PowerShell script to detect USB ports and test connectivity"""
        if _usb_check_running[0]:
            return
        _usb_check_running[0] = True
        
        try:
            ui_call(lambda: usb_status.configure(text="Enumerating USB ports...", text_color="#58a6ff"))
            
            # Run the PowerShell script
            ps_path = os.path.join(BASE, "USBPortTest.ps1")
            
            if not os.path.exists(ps_path):
                ui_call(lambda: usb_status.configure(text="USBPortTest.ps1 not found!", text_color="#ff7b72"))
                _usb_check_running[0] = False
                return
            
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout
            error = result.stderr
            
            # Parse the output
            controllers = 0
            hubs = 0
            total_devices = 0
            working_devices = 0
            failed_devices = 0
            active_connections = 0
            usb2_count = 0
            usb3_count = 0
            usbc_count = 0
            test_result = "FAIL"
            test_message = "Unknown"
            working_list = []
            failed_list = []
            
            parsing_section = None
            
            for line in output.split('\n'):
                line = line.strip()
                
                # Track sections
                if "WORKING DEVICE LIST:" in line:
                    parsing_section = "working"
                    continue
                elif "DEVICES WITH ISSUES:" in line:
                    parsing_section = "failed"
                    continue
                
                # Parse working/failed device lists
                if parsing_section == "working" and line.startswith("[OK]"):
                    working_list.append(line.replace("[OK]", "").strip())
                    continue
                elif parsing_section == "failed" and line.startswith("[ERR]"):
                    failed_list.append(line.replace("[ERR]", "").strip())
                    continue
                
                # Parse summary data
                if line.startswith("USB_CONTROLLERS_FOUND:"):
                    controllers = int(line.split(":", 1)[1].strip())
                elif line.startswith("USB_HUBS_FOUND:"):
                    hubs = int(line.split(":", 1)[1].strip())
                elif line.startswith("TOTAL_USB_DEVICES:"):
                    total_devices = int(line.split(":", 1)[1].strip())
                elif line.startswith("WORKING_DEVICES:"):
                    working_devices = int(line.split(":", 1)[1].strip())
                elif line.startswith("FAILED_DEVICES:"):
                    failed_devices = int(line.split(":", 1)[1].strip())
                elif line.startswith("ACTIVE_USB_CONNECTIONS:"):
                    active_connections = int(line.split(":", 1)[1].strip())
                elif line.startswith("USB_2_0_PORTS:"):
                    usb2_count = int(line.split(":", 1)[1].strip())
                elif line.startswith("USB_3_0_PORTS:"):
                    usb3_count = int(line.split(":", 1)[1].strip())
                elif line.startswith("USB_C_PORTS:"):
                    try:
                        usbc_count = int(line.split(":", 1)[1].strip())
                    except:
                        usbc_count = 0
                elif line.startswith("TEST_RESULT:"):
                    test_result = line.split(":", 1)[1].strip()
                elif line.startswith("TEST_MESSAGE:"):
                    test_message = line.split(":", 1)[1].strip()
            
            # Update UI
            def _update_ui():
                usb_status.configure(
                    text=f"USB Test: {test_result} - {test_message}",
                    text_color="#7ee787" if test_result == "PASS" else "#ff7b72"
                )
                
                usb_summary_lbl.configure(
                    text=f"Controllers: {controllers} | Hubs: {hubs} | Devices: {total_devices}"
                )
                
                usb_versions_lbl.configure(
                    text=f"USB 2.0: {usb2_count} | USB 3.0: {usb3_count} | USB-C: {usbc_count}"
                )
                
                usb_connections_lbl.configure(
                    text=f"Active Connections: {active_connections}"
                )
                
                # Update details text
                usb_details_text.configure(state="normal")
                usb_details_text.delete(1.0, "end")
                
                if working_list:
                    usb_details_text.insert("end", f"✓ WORKING DEVICES ({len(working_list)}):\n")
                    for device in working_list[:10]:  # Show first 10
                        usb_details_text.insert("end", f"  {device}\n")
                    if len(working_list) > 10:
                        usb_details_text.insert("end", f"  ... and {len(working_list) - 10} more\n")
                    usb_details_text.insert("end", "\n")
                
                if failed_list:
                    usb_details_text.insert("end", f"✗ DEVICES WITH ISSUES ({len(failed_list)}):\n")
                    for device in failed_list[:5]:  # Show first 5
                        usb_details_text.insert("end", f"  {device}\n")
                    if len(failed_list) > 5:
                        usb_details_text.insert("end", f"  ... and {len(failed_list) - 5} more\n")
                
                if not working_list and not failed_list:
                    usb_details_text.insert("end", "No USB devices detected.\n\n")
                    usb_details_text.insert("end", "Possible reasons:\n")
                    usb_details_text.insert("end", "  • No USB devices connected\n")
                    usb_details_text.insert("end", "  • USB drivers not installed\n")
                    usb_details_text.insert("end", "  • USB ports disabled in BIOS\n")
                
                usb_details_text.configure(state="disabled")
                
                # Auto-mark pass/fail
                if test_result == "PASS":
                    if hasattr(usb_card, 'set_pass'):
                        usb_card.set_pass()
                else:
                    if hasattr(usb_card, 'set_fail'):
                        usb_card.set_fail()
            
            ui_call(_update_ui)
            
        except subprocess.TimeoutExpired:
            ui_call(lambda: usb_status.configure(text="USB port detection timed out", text_color="#ff7b72"))
        except Exception as e:
            ui_call(lambda: usb_status.configure(text=f"Error: {str(e)}", text_color="#ff7b72"))
        finally:
            _usb_check_running[0] = False

    # AUTO ADVANCE: USB Port Detection -> NFC
    def _on_usb_marked():
        """After USB Port Detection PASS/FAIL, show NFC card and start NFC test."""
        def _show_and_start_nfc():
            try:
                _highlight_and_show(nfc_card)
            except Exception:
                pass
            try:
                threading.Thread(target=_nfc_refresh, daemon=True).start()
            except Exception:
                pass
        ui_call(_show_and_start_nfc)

    try:
        if hasattr(usb_card, 'set_pass') and hasattr(usb_card, 'pass_btn'):
            _usb_orig_pass = usb_card.set_pass
            _usb_orig_fail = usb_card.set_fail
            
            def _usb_pass():
                _usb_orig_pass()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(nfc_card))
                    return
                _on_usb_marked()
            
            def _usb_fail():
                _usb_orig_fail()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(nfc_card))
                    return
                _on_usb_marked()
            
            usb_card.set_pass = _usb_pass
            usb_card.set_fail = _usb_fail
            usb_card.pass_btn.configure(command=_usb_pass)
            usb_card.fail_btn.configure(command=_usb_fail)
    except Exception:
        pass

    # Row for Touchscreen, Pixel, and Camera
    test_row_compact = _register_tk_frame(tk.Frame(body, bg=theme_value("screen_bg")))
    test_row_compact.pack(fill="x", padx=14, pady=8)

    # ══════════════════════════════════════════════════════════════════
    # NFC READER CARD
    # ══════════════════════════════════════════════════════════════════
    nfc_card = card(body, "📡  NFC Reader", track_key="nfc")
    try:
        nfc_card.pack_forget()
    except Exception:
        pass
    nfc_card.pack(fill="x", padx=14, pady=8)

    nfc_header_row = ctk.CTkFrame(nfc_card, fg_color="transparent")
    nfc_header_row.pack(fill="x", padx=14, pady=(10,6))
    ctk.CTkLabel(nfc_header_row, text="📡  NFC Reader", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff").pack(side="left")
    ctk.CTkButton(nfc_header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=lambda: threading.Thread(target=_nfc_refresh, daemon=True).start()).pack(side="right")

    nfc_status_lbl = _register_subtle_label(ctk.CTkLabel(nfc_card, text="Checking for NFC readers...", font=ctk.CTkFont(size=12), text_color="#9fb3c8"))
    nfc_status_lbl.pack(anchor="w", padx=14, pady=(0, 6))

    nfc_info = _register_ctk_frame(ctk.CTkFrame(nfc_card, fg_color=theme_value("embed_bg"), corner_radius=8))
    nfc_info.pack(fill="x", padx=14, pady=(0, 10))
    nfc_svc = _register_subtle_label(ctk.CTkLabel(nfc_info, text="Service: --", font=ctk.CTkFont(size=11), text_color="#9fb3c8"))
    nfc_svc.pack(anchor="w", padx=12, pady=(10, 4))
    nfc_dev = _register_subtle_label(ctk.CTkLabel(nfc_info, text="NFC Devices: -- | Contactless: --", font=ctk.CTkFont(size=11), text_color="#9fb3c8"))
    nfc_dev.pack(anchor="w", padx=12, pady=(4, 10))
    nfc_txt = _register_text_widget(tk.Text(nfc_info, bg=theme_value("embed_bg"), fg=theme_value("embed_text"), font=("Consolas", 10), height=6, wrap="word", borderwidth=0, highlightthickness=0))
    nfc_txt.pack(fill="x", padx=12, pady=(0, 10))
    nfc_txt.configure(state="disabled")

    _nfc_running = [False]
    def _nfc_refresh():
        if _nfc_running[0]: return
        _nfc_running[0] = True
        try:
            ui_call(lambda: nfc_status_lbl.configure(text="Detecting NFC...", text_color="#58a6ff"))
            ps = os.path.join(BASE, "NFCTest.ps1")
            if not os.path.exists(ps):
                ui_call(lambda: nfc_status_lbl.configure(text="NFCTest.ps1 not found!", text_color="#ff7b72"))
                _nfc_running[0] = False
                return
            r = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", ps], capture_output=True, text=True, timeout=30)
            out = r.stdout
            svc="Unknown"; tot=0; con=0; wrk=0; res="FAIL"; msg=""; devs=[]
            for line in out.split('\n'):
                line = line.strip()
                if line.startswith("NFC_SERVICE_STATUS:"): svc = line.split(":", 1)[1].strip()
                elif line.startswith("TOTAL_NFC_DEVICES:"): tot = int(line.split(":", 1)[1].strip())
                elif line.startswith("CONTACTLESS_READERS:"): con = int(line.split(":", 1)[1].strip())
                elif line.startswith("WORKING_NFC_DEVICES:"): wrk = int(line.split(":", 1)[1].strip())
                elif line.startswith("TEST_RESULT:"): res = line.split(":", 1)[1].strip()
                elif line.startswith("TEST_MESSAGE:"): msg = line.split(":", 1)[1].strip()
                elif line.startswith("[") and ("[OK]" in line or "[ERR]" in line): devs.append(line)
            def _upd():
                nfc_status_lbl.configure(text=f"NFC: {res}", text_color="#7ee787" if res=="PASS" else "#ff7b72")
                nfc_svc.configure(text=f"Service: {svc}")
                nfc_dev.configure(text=f"NFC Devices: {tot} | Contactless: {con}")
                nfc_txt.configure(state="normal"); nfc_txt.delete(1.0, "end")
                if devs:
                    for d in devs: nfc_txt.insert("end", f"{d}\n")
                else:
                    nfc_txt.insert("end", "No NFC readers detected.\n\nNFC is not common on most laptops.\n")
                nfc_txt.configure(state="disabled")
                if res=="PASS" and hasattr(nfc_card, 'set_pass'): nfc_card.set_pass()
                elif res=="FAIL" and hasattr(nfc_card, 'set_fail'): nfc_card.set_fail()
            ui_call(_upd)
        except Exception as e:
            ui_call(lambda: nfc_status_lbl.configure(text=f"Error: {e}", text_color="#ff7b72"))
        finally:
            _nfc_running[0] = False

    def _on_nfc_marked():
        def _show():
            try: _highlight_and_show(fingerprint_card)
            except: pass
            try: threading.Thread(target=_fingerprint_refresh, daemon=True).start()
            except: pass
        ui_call(_show)

    try:
        if hasattr(nfc_card, 'set_pass'):
            _nfc_op = nfc_card.set_pass; _nfc_of = nfc_card.set_fail
            def _nfc_p():
                _nfc_op()
                if _sequence_running[0]: ui_call(lambda: _highlight_and_show(fingerprint_card)); return
                _on_nfc_marked()
            def _nfc_f():
                _nfc_of()
                if _sequence_running[0]: ui_call(lambda: _highlight_and_show(fingerprint_card)); return
                _on_nfc_marked()
            nfc_card.set_pass=_nfc_p; nfc_card.set_fail=_nfc_f
            nfc_card.pass_btn.configure(command=_nfc_p); nfc_card.fail_btn.configure(command=_nfc_f)
    except: pass

    # ══════════════════════════════════════════════════════════════════
    # FINGERPRINT READER CARD
    # ══════════════════════════════════════════════════════════════════
    fingerprint_card = card(body, "👆  Fingerprint Reader", track_key="fingerprint")
    try:
        fingerprint_card.pack_forget()
    except Exception:
        pass
    fingerprint_card.pack(fill="x", padx=14, pady=8)

    fp_header = ctk.CTkFrame(fingerprint_card, fg_color="transparent")
    fp_header.pack(fill="x", padx=14, pady=(10,6))
    ctk.CTkLabel(fp_header, text="👆  Fingerprint Reader", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff").pack(side="left")
    ctk.CTkButton(fp_header, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=lambda: threading.Thread(target=_fingerprint_refresh, daemon=True).start()).pack(side="right")

    fp_status_lbl = ctk.CTkLabel(fingerprint_card, text="Checking for fingerprint readers...", font=ctk.CTkFont(size=12), text_color="#9fb3c8")
    fp_status_lbl.pack(anchor="w", padx=14, pady=(0, 6))

    fp_info = _register_ctk_frame(ctk.CTkFrame(fingerprint_card, fg_color=theme_value("embed_bg"), corner_radius=8))
    fp_info.pack(fill="x", padx=14, pady=(0, 10))
    fp_svc = _register_subtle_label(ctk.CTkLabel(fp_info, text="Service: --", font=ctk.CTkFont(size=11), text_color="#9fb3c8"))
    fp_svc.pack(anchor="w", padx=12, pady=(10, 4))
    fp_dev = _register_subtle_label(ctk.CTkLabel(fp_info, text="Biometric: -- | Fingerprint: --", font=ctk.CTkFont(size=11), text_color="#9fb3c8"))
    fp_dev.pack(anchor="w", padx=12, pady=(4, 10))
    fp_txt = _register_text_widget(tk.Text(fp_info, bg=theme_value("embed_bg"), fg=theme_value("embed_text"), font=("Consolas", 10), height=6, wrap="word", borderwidth=0, highlightthickness=0))
    fp_txt.pack(fill="x", padx=12, pady=(0, 10))
    fp_txt.configure(state="disabled")

    _fp_running = [False]
    def _fingerprint_refresh():
        if _fp_running[0]: return
        _fp_running[0] = True
        try:
            ui_call(lambda: fp_status_lbl.configure(text="Detecting fingerprint...", text_color="#58a6ff"))
            ps = os.path.join(BASE, "FingerprintTest.ps1")
            if not os.path.exists(ps):
                ui_call(lambda: fp_status_lbl.configure(text="FingerprintTest.ps1 not found!", text_color="#ff7b72"))
                _fp_running[0] = False
                return
            r = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", ps], capture_output=True, text=True, timeout=30)
            out = r.stdout
            svc="Unknown"; bio=0; fp_r=0; wrk=0; hello=False; res="FAIL"; msg=""; devs=[]
            for line in out.split('\n'):
                line = line.strip()
                if line.startswith("BIO_SERVICE_STATUS:"): svc = line.split(":", 1)[1].strip()
                elif line.startswith("TOTAL_BIOMETRIC_DEVICES:"):
                    try: bio = int(line.split(":", 1)[1].strip())
                    except: bio = 0
                elif line.startswith("FINGERPRINT_READERS:"):
                    try: fp_r = int(line.split(":", 1)[1].strip())
                    except: fp_r = 0
                elif line.startswith("WORKING_FINGERPRINT_DEVICES:"):
                    try: wrk = int(line.split(":", 1)[1].strip())
                    except: wrk = 0
                elif line.startswith("WINDOWS_HELLO_AVAILABLE:"): hello = ("True" in line)
                elif line.startswith("TEST_RESULT:"): res = line.split(":", 1)[1].strip()
                elif line.startswith("TEST_MESSAGE:"): msg = line.split(":", 1)[1].strip()
                elif line.startswith("[") and ("[OK]" in line or "[ERR]" in line): devs.append(line)
            def _upd():
                fp_status_lbl.configure(text=f"Fingerprint: {res}", text_color="#7ee787" if res=="PASS" else "#ff7b72")
                fp_svc.configure(text=f"Service: {svc}")
                fp_dev.configure(text=f"Biometric: {bio} | Fingerprint: {fp_r}")
                fp_txt.configure(state="normal"); fp_txt.delete(1.0, "end")
                if devs:
                    for d in devs: fp_txt.insert("end", f"{d}\n")
                    if hello: fp_txt.insert("end", "\nWindows Hello: Available\n")
                else:
                    fp_txt.insert("end", "No fingerprint readers detected.\n\nCommon on business laptops and ultrabooks.\n")
                fp_txt.configure(state="disabled")
                if res=="PASS" and hasattr(fingerprint_card, 'set_pass'): fingerprint_card.set_pass()
                elif res=="FAIL" and hasattr(fingerprint_card, 'set_fail'): fingerprint_card.set_fail()
            ui_call(_upd)
        except Exception as e:
            ui_call(lambda: fp_status_lbl.configure(text=f"Error: {e}", text_color="#ff7b72"))
        finally:
            _fp_running[0] = False

    def _on_fp_marked():
        def _show():
            try: _highlight_and_show(touchscreen_card)
            except: pass
            try: _run_touchscreen_test()
            except: pass
        ui_call(_show)

    try:
        if hasattr(fingerprint_card, 'set_pass'):
            _fp_op = fingerprint_card.set_pass; _fp_of = fingerprint_card.set_fail
            def _fp_p():
                _fp_op()
                if _sequence_running[0]: ui_call(lambda: _highlight_and_show(touchscreen_card)); return
                _on_fp_marked()
            def _fp_f():
                _fp_of()
                if _sequence_running[0]: ui_call(lambda: _highlight_and_show(touchscreen_card)); return
                _on_fp_marked()
            fingerprint_card.set_pass=_fp_p; fingerprint_card.set_fail=_fp_f
            fingerprint_card.pass_btn.configure(command=_fp_p); fingerprint_card.fail_btn.configure(command=_fp_f)
    except: pass

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

    ts_host = _register_tk_frame(tk.Frame(touchscreen_card, bg=theme_value("embed_bg")))
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
    
    # AUTO ADVANCE: Touchscreen -> Pixel Test
    def _on_ts_marked():
        """After Touchscreen PASS/FAIL, show Pixel Test card and start pixel test."""
        def _show_and_start_px():
            try:
                _stop_touchscreen_test()
            except Exception:
                pass
            try:
                _highlight_and_show(pixel_card)
            except Exception:
                pass
            try:
                _start_pixel_test()
            except Exception:
                pass
        ui_call(_show_and_start_px)
    
    try:
        if hasattr(touchscreen_card, 'set_pass') and hasattr(touchscreen_card, 'pass_btn'):
            _ts_orig_pass = touchscreen_card.set_pass
            _ts_orig_fail = touchscreen_card.set_fail
    
            def _ts_pass():
                try: _stop_touchscreen_test()
                except Exception: pass
                _ts_orig_pass()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(pixel_card))
                    return
                _on_ts_marked()
    
            def _ts_fail():
                try: _stop_touchscreen_test()
                except Exception: pass
                _ts_orig_fail()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(pixel_card))
                    return
                _on_ts_marked()
    
            touchscreen_card.set_pass = _ts_pass
            touchscreen_card.set_fail = _ts_fail
            touchscreen_card.pass_btn.configure(command=_ts_pass)
            touchscreen_card.fail_btn.configure(command=_ts_fail)
    except Exception:
        pass
    
    # PIXEL TEST CARD
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
    
    # AUTO ADVANCE: Pixel Test -> Camera
    def _on_px_marked():
        """After Pixel Test PASS/FAIL, show Camera card and start camera preview."""
        def _show_and_start_cam():
            try:
                _stop_pixel_test()
            except Exception:
                pass
            try:
                _highlight_and_show(cam_card)
            except Exception:
                pass
            try:
                threading.Thread(target=_start_camera_preview, daemon=True).start()
            except Exception:
                pass
        ui_call(_show_and_start_cam)
    
    try:
        if hasattr(pixel_card, 'set_pass') and hasattr(pixel_card, 'pass_btn'):
            _px_orig_pass = pixel_card.set_pass
            _px_orig_fail = pixel_card.set_fail
    
            def _px_pass():
                try: _stop_pixel_test()
                except Exception: pass
                _px_orig_pass()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(cam_card))
                    return
                _on_px_marked()
    
            def _px_fail():
                try: _stop_pixel_test()
                except Exception: pass
                _px_orig_fail()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(cam_card))
                    return
                _on_px_marked()
    
            pixel_card.set_pass = _px_pass
            pixel_card.set_fail = _px_fail
            pixel_card.pass_btn.configure(command=_px_pass)
            pixel_card.fail_btn.configure(command=_px_fail)
    except Exception:
        pass
    
    # CAMERA CARD (inline preview in main menu)
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
    # AUTO ADVANCE: Camera -> Keyboard
    def _on_cam_marked():
        """After Camera PASS/FAIL, show Keyboard card and start keyboard test."""
        def _show_and_start_kb():
            try:
                _stop_camera_preview_local()
            except Exception:
                pass
            try:
                _highlight_and_show(kb_card)
            except Exception:
                pass
            try:
                _start_keyboard_module()
            except Exception:
                pass
        ui_call(_show_and_start_kb)

    try:
        if hasattr(cam_card, 'set_pass') and hasattr(cam_card, 'pass_btn'):
            _cam_orig_pass = cam_card.set_pass
            _cam_orig_fail = cam_card.set_fail

            def _cam_pass():
                _stop_camera_preview_local()
                _cam_orig_pass()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(kb_card))
                    return
                _on_cam_marked()

            def _cam_fail():
                _stop_camera_preview_local()
                _cam_orig_fail()
                if _sequence_running[0]:
                    ui_call(lambda: _highlight_and_show(kb_card))
                    return
                _on_cam_marked()

            cam_card.set_pass = _cam_pass
            cam_card.set_fail = _cam_fail
            cam_card.pass_btn.configure(command=_cam_pass)
            cam_card.fail_btn.configure(command=_cam_fail)
    except Exception:
        pass

    try:
        smartcard_card.pack(fill="x", padx=14, pady=8)
    except Exception:
        pass

    try:
        usb_card.pack(fill="x", padx=14, pady=8)
    except Exception:
        pass

    # KEYBOARD CARD (own full-width row — keyboard tester needs horizontal space)
    kb_card = card(body, "⌨️  Keyboard Test", track_key="kb")
    try:
        kb_card.pack_forget()
        kb_card.pack(fill="x", padx=14, pady=8)
    except Exception:
        pass

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
                            _kb_update_scroll_region()
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

    kb_scroll_wrap = ctk.CTkFrame(kb_card, fg_color="transparent")
    kb_scroll_wrap.pack(fill="both", expand=True, padx=14, pady=(0, 4))

    kb_canvas = tk.Canvas(kb_scroll_wrap, bg=theme_value("embed_bg"), highlightthickness=0, height=300)
    kb_canvas.pack(side="top", fill="both", expand=True)

    kb_embed_host = _register_tk_frame(tk.Frame(kb_canvas, bg=theme_value("embed_bg")))
    _kb_canvas_window = kb_canvas.create_window((0, 0), window=kb_embed_host, anchor="nw")

    # Stretch the embedded keyboard host to fill the full canvas width
    def _kb_resize_embed(event=None):
        try:
            kb_canvas.itemconfig(_kb_canvas_window, width=kb_canvas.winfo_width())
        except Exception:
            pass
    kb_canvas.bind("<Configure>", _kb_resize_embed)

    def _kb_update_scroll_region(_event=None):
        try:
            kb_canvas.update_idletasks()
            kb_canvas.configure(scrollregion=kb_canvas.bbox("all"))
            req_h = max(kb_embed_host.winfo_reqheight(), 260)
            kb_canvas.configure(height=min(req_h + 8, 360))
        except Exception:
            pass

    kb_embed_host.bind("<Configure>", _kb_update_scroll_region)

    for _w in (kb_canvas, kb_embed_host, kb_scroll_wrap):
        try:
            _w.bind("<Shift-MouseWheel>", _kb_update_scroll_region, add="+")
            _w.bind("<Shift-Button-4>", _kb_update_scroll_region, add="+")
            _w.bind("<Shift-Button-5>", _kb_update_scroll_region, add="+")
        except Exception:
            pass

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
            try:
                app.after(50, _kb_update_scroll_region)
            except Exception:
                _kb_update_scroll_region()

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

    # Marking PASS/FAIL keeps the keyboard visible but disables further input.
    def _kb_disable_input():
        """Unbind all key handlers so the keyboard stays visible but stops responding."""
        kb_state["active"] = False
        # Unbind our forwarded keypress handler
        bind_id = kb_state.get("bind_id")
        if bind_id:
            try:
                app.unbind("<KeyPress>", bind_id)
            except Exception:
                pass
            kb_state["bind_id"] = None
        # Also unbind the tester's own bind_all handlers so keys stop lighting up
        tester = kb_state.get("tester")
        if tester is not None:
            try:
                toplevel = getattr(tester, '_toplevel', app)
                toplevel.unbind_all("<KeyPress>")
                toplevel.unbind_all("<KeyRelease>")
            except Exception:
                pass
            try:
                toplevel.unbind_all("<Tab>")
                toplevel.unbind_all("<Key-Tab>")
                toplevel.unbind_all("<ISO_Left_Tab>")
            except Exception:
                pass
            for i in range(1, 13):
                try:
                    toplevel.unbind_all(f"<F{i}>")
                except Exception:
                    pass
            try:
                toplevel.unbind_all('<Alt_L>')
                toplevel.unbind_all('<Alt_R>')
            except Exception:
                pass

    try:
        if hasattr(kb_card, 'pass_btn') and hasattr(kb_card, 'set_pass'):
            kb_card.pass_btn.configure(command=lambda: (_kb_disable_input(), kb_card.set_pass()))
        if hasattr(kb_card, 'fail_btn') and hasattr(kb_card, 'set_fail'):
            kb_card.fail_btn.configure(command=lambda: (_kb_disable_input(), kb_card.set_fail()))
    except Exception:
        pass

    # (Duplicate Touchpad card removed — single embedded instance appears earlier)

    # Bottom padding
    # ══════════════════════════════════════════════════════════════════
    # ACTIVATION + DRIVERS ROW
    # ══════════════════════════════════════════════════════════════════
    # Create a horizontal row to hold Activation and Drivers cards side-by-side
    row_frame = _register_tk_frame(tk.Frame(body, bg=theme_value("screen_bg")))
    row_frame.pack(fill="x", padx=14, pady=8)

    # Activation card (left)
    act_card = ctk.CTkFrame(row_frame, fg_color=theme_value("card_bg"), corner_radius=10,
                             border_width=1, border_color=theme_value("card_border"))
    act_card.pack(side="left", fill="both", expand=True, padx=(0,5))
    
    # Activation header (Drivers-style with small refresh icon)
    try:
        header_row = ctk.CTkFrame(act_card, fg_color="transparent")
        header_row.pack(fill="x", padx=14, pady=(10,6))
        _register_title_label(ctk.CTkLabel(header_row, text="🔐  Activation", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff")).pack(side="left")
        try:
            # Use lambda so callback resolves after local funcs are defined.
            _register_refresh_button(ctk.CTkButton(header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=lambda: _run_activation_check())).pack(side="right")
        except Exception:
            pass
    except Exception:
        pass
    act_label = _register_subtle_label(ctk.CTkLabel(
        act_card,
        text="Activation Check",
        font=ctk.CTkFont(size=12),
        text_color="#9fb3c8",
    ))
    act_label.pack(anchor="w", padx=14, pady=(0, 10))
    act_result_label = _register_subtle_label(ctk.CTkLabel(act_card, text="Checking...", font=ctk.CTkFont(size=13), text_color="#9fb3c8", justify="left"))
    act_result_label.pack(anchor="w", padx=14, pady=(0, 10))
# Add PASS/FAIL status controls to Activation card (mirrors other cards)
    try:
        act_status_frame = ctk.CTkFrame(act_card, fg_color=theme_value("status_bg"), corner_radius=0)
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
            act_card.status_frame = act_status_frame
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
    drv_card = ctk.CTkFrame(row_frame, fg_color=theme_value("card_bg"), corner_radius=10,
                            border_width=1, border_color=theme_value("card_border"))
    drv_card.pack(side="left", fill="both", expand=True, padx=5)
    
    # Header with title + refresh button
    header_row = ctk.CTkFrame(drv_card, fg_color="transparent")
    header_row.pack(fill="x", padx=14, pady=(10,6))
    _register_title_label(ctk.CTkLabel(header_row, text="🛠️  Drivers", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff")).pack(side="left")
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
        refresh_btn = _register_refresh_button(ctk.CTkButton(header_row, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=_drv_refresh_clicked))
        refresh_btn.pack(side="right")
    except Exception:
        pass

    drv_status_label = _register_subtle_label(ctk.CTkLabel(drv_card, text="Driver Checker", font=ctk.CTkFont(size=12), text_color="#9fb3c8"))
    drv_status_label.pack(anchor="w", padx=14, pady=(0, 8))

    drv_output_frame = ctk.CTkFrame(drv_card, fg_color="transparent")
    drv_output_frame.pack(fill="both", expand=False, padx=14, pady=(0,10))
    drv_output_labels = []

    # Status area (PASS / FAIL) for Drivers card — mirrors `card()` helper
    try:
        drv_status_frame = ctk.CTkFrame(drv_card, fg_color=theme_value("status_bg"), corner_radius=0)
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
            drv_card.status_frame = drv_status_frame
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
    gpu_card = ctk.CTkFrame(row_frame, fg_color=theme_value("card_bg"), corner_radius=10,
                            border_width=1, border_color=theme_value("card_border"))
    gpu_card.pack(side="left", fill="both", expand=True, padx=(5,0))

    
    header_row_gpu = ctk.CTkFrame(gpu_card, fg_color="transparent")
    header_row_gpu.pack(fill="x", padx=14, pady=(10,6))
    _register_title_label(ctk.CTkLabel(header_row_gpu, text="🎮  GPU", font=ctk.CTkFont(size=14, weight="bold"), text_color="#58a6ff")).pack(side="left")
    
    def _gpu_refresh_clicked():
        try:
            _reset_gpu_card()
            threading.Thread(target=_run_gpu_check, daemon=True).start()
        except Exception:
            pass
            
    try:
        _register_refresh_button(ctk.CTkButton(header_row_gpu, text="⟳", width=28, height=28, fg_color="#444444", hover_color="#555555", command=_gpu_refresh_clicked)).pack(side="right")
    except Exception:
        pass

    gpu_status_label = _register_subtle_label(ctk.CTkLabel(gpu_card, text="Graphics Controller", font=ctk.CTkFont(size=12), text_color="#9fb3c8"))
    gpu_status_label.pack(anchor="w", padx=14, pady=(0, 8))

    gpu_output_frame = ctk.CTkFrame(gpu_card, fg_color="transparent")
    gpu_output_frame.pack(fill="both", expand=False, padx=14, pady=(0,10))
    gpu_output_labels = []

    # Status area for GPU card (Pass/Fail)
    try:
        gpu_status_frame = ctk.CTkFrame(gpu_card, fg_color=theme_value("status_bg"), corner_radius=0)
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
        gpu_card.status_display = gpu_status_display
        gpu_card.pass_btn = gpu_pass_btn
        gpu_card.fail_btn = gpu_fail_btn
        gpu_card.status_frame = gpu_status_frame
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
    # ENROLLMENT CHECK CARD (embedded CheckEnrollment.ps1)
    # ══════════════════════════════════════════════════════════════════
    enroll_card = card(body, "🔐  Enrollment Check", track_key="enr")
    try:
        enroll_card.pack_forget()
        enroll_card.pack(fill="x", padx=14, pady=8)
    except Exception:
        pass
    try:
        try:
            first_child = enroll_card.winfo_children()[0]
            try:
                first_child.destroy()
            except Exception:
                pass
        except Exception:
            pass
        enroll_header_row = ctk.CTkFrame(enroll_card, fg_color="transparent")
        enroll_header_row.pack(fill="x", padx=14, pady=(10, 6))
        ctk.CTkLabel(
            enroll_header_row,
            text="🔐  Enrollment Check",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#58a6ff",
        ).pack(side="left")
    except Exception:
        pass

    enroll_status = ctk.CTkLabel(
        enroll_card,
        text="Starting enrollment check...",
        font=ctk.CTkFont(size=12),
        text_color="#9fb3c8",
    )
    enroll_status.pack(anchor="w", padx=14, pady=(0, 10))

    enroll_results_frame = ctk.CTkFrame(enroll_card, fg_color="transparent")
    enroll_results_frame.pack(fill="both", expand=False, padx=14, pady=(0, 10))
    enroll_output_labels = []

    def _enroll_line_color(line):
        low = (line or "").lower()
        # Check PASS first — "no enrollment found" contains the substring "enrollment found"
        if "no enrollment found" in low or "enrollment_check_result:pass" in low:
            return "#7ee787"
        if "enrollment found" in low or "enrollment_check_result:fail" in low:
            return "#ff7b72"
        # Detail lines only appear when something was found
        if "[!]" in line or any(
            tok in low
            for tok in ("found file:", "found service:", "found running process:", "found via", "active autopilot")
        ):
            return "#ff7b72"
        return "#9fb3c8"

    def _reset_enroll_card():
        try:
            for lbl in list(enroll_output_labels):
                try:
                    lbl.destroy()
                except Exception:
                    pass
            enroll_output_labels.clear()
            ui_call(lambda: enroll_status.configure(text="Running enrollment check...", text_color="#9fb3c8"))
        except Exception:
            pass

    def _add_enroll_output_line(line):
        try:
            text = (line or "").strip()
            if not text or text.upper().startswith("ENROLLMENT_CHECK_RESULT:"):
                return
            lbl = ctk.CTkLabel(
                enroll_results_frame,
                text=text,
                font=ctk.CTkFont(size=10),
                text_color=_enroll_line_color(text),
                justify="left",
                wraplength=700,
            )
            lbl.pack(anchor="w", pady=1)
            enroll_output_labels.append(lbl)
            if len(enroll_output_labels) > 40:
                old_lbl = enroll_output_labels.pop(0)
                old_lbl.destroy()
        except Exception:
            pass

    def _start_enrollment_check():
        _reset_enroll_card()
        try:
            script_path = os.path.join(BASE, "EnrollmentTest.ps1")
            if not os.path.exists(script_path):
                app.after(0, lambda: _add_enroll_output_line(f"Error: Script not found: {script_path}"))
                app.after(0, lambda: enroll_status.configure(text="EnrollmentTest.ps1 not found", text_color="#ff7b72"))
                return

            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path]
            creation = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                creationflags=creation,
            )
            ui_call(lambda: enroll_status.configure(text=f"Checking enrollment (PID {proc.pid})...", text_color="#9fb3c8"))

            def _reader():
                global _enrollment_report_lines
                saw_fail = False
                saw_pass_marker = False
                _enrollment_report_lines.clear()
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
                        low = line.lower()
                        if "enrollment found (fail)" in low or "enrollment_check_result:fail" in low:
                            saw_fail = True
                        if "enrollment_check_result:pass" in low:
                            saw_pass_marker = True
                        _enrollment_report_lines.append(line.rstrip())
                        ui_call(_add_enroll_output_line, line)
                    try:
                        stderr = (proc.stderr.read() if proc.stderr else "") or ""
                        if stderr.strip():
                            saw_fail = True
                            for ln in stderr.splitlines(True):
                                ui_call(_add_enroll_output_line, f"[Error] {ln}")
                    except Exception:
                        pass
                finally:
                    rc = proc.poll() or 0
                    if rc != 0 or saw_fail:
                        status_text = "✗ Enrollment or Computrace detected"
                        color = "#ff7b72"
                        try:
                            ui_call(lambda: hasattr(enroll_card, "set_fail") and enroll_card.set_fail())
                        except Exception:
                            pass
                    elif saw_pass_marker or rc == 0:
                        status_text = "✓ No enrollment or Computrace found"
                        color = "#7ee787"
                        try:
                            ui_call(lambda: hasattr(enroll_card, "set_pass") and enroll_card.set_pass())
                        except Exception:
                            pass
                    else:
                        status_text = "✗ Unable to confirm enrollment result"
                        color = "#ff7b72"
                        try:
                            ui_call(lambda: hasattr(enroll_card, "set_fail") and enroll_card.set_fail())
                        except Exception:
                            pass
                    ui_call(lambda: enroll_status.configure(text=status_text, text_color=color))

            threading.Thread(target=_reader, daemon=True).start()
        except Exception as e:
            app.after(0, lambda: _add_enroll_output_line(f"Error launching enrollment check: {e}"))
            app.after(0, lambda: enroll_status.configure(text="Error starting check", text_color="#ff7b72"))

    try:
        ctk.CTkButton(
            enroll_header_row,
            text="⟳",
            width=28,
            height=28,
            fg_color="#444444",
            hover_color="#555555",
            command=lambda: threading.Thread(target=_start_enrollment_check, daemon=True).start(),
        ).pack(side="right")
    except Exception:
        pass

    threading.Thread(target=_start_enrollment_check, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════
    # VIRUS SCAN CARD (runs windef.ps1 with live output)
    # ══════════════════════════════════════════════════════════════════
    vs_card = card(body, "🦠  Virus Scan", track_key="vs")
    try:
        vs_card.pack_forget()
        vs_card.pack(fill="x", padx=14, pady=8)
    except Exception:
        pass
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
    add_sidebar_item("operator", "👤 Operator", operator_card)
    add_sidebar_item("ag",   "🔈 Audio Changer",  ag_card)
    add_sidebar_item("sys",  "🖥️ System Info",     sys_card)
    add_sidebar_item("comp", "🧩 Components",      comp_card)
    add_sidebar_item("net",  "📶 Network Adapters", net_card)
    add_sidebar_item("bat",  "🔋 Battery",         bat_card)
    add_sidebar_item("tp",   "🖱️ Touchpad",        tp_card)
    add_sidebar_item("spk",  "🔊 Speaker",         spk_card)
    add_sidebar_item("mic",  "🎙️ Microphone",      mic_card)
    add_sidebar_item("br",   "☀️ Brightness",      brightness_card)
    add_sidebar_item("smartcard", "💳 Smart Card", smartcard_card)
    add_sidebar_item("usb",  "🔌 USB Port Detection", usb_card)
    add_sidebar_item("nfc",  "📡 NFC Reader", nfc_card)
    add_sidebar_item("fingerprint", "👆 Fingerprint", fingerprint_card)
    add_sidebar_item("ts",   "👆 Touchscreen",     touchscreen_card)
    add_sidebar_item("px",   "🟥 Pixel Test",      pixel_card)
    add_sidebar_item("cam",  "📷 Camera",          cam_card)
    add_sidebar_item("kb",   "⌨️ Keyboard",        kb_card)
    add_sidebar_item("act",  "✅ Activation",      act_card)
    add_sidebar_item("drv",  "💾 Drivers",         drv_card)
    add_sidebar_item("gpu",  "🎮 GPU",             gpu_card)
    add_sidebar_item("enr",  "🔐 Enrollment Check", enroll_card)
    add_sidebar_item("vs",   "🛡️ Virus Scan",      vs_card)

    _install_i18n_tree(active_screen)
    _apply_language(lang_var.get())
    _apply_theme(theme_var.get().lower())

    # ──────────────────────────────────────────────────────────────────
    # SEQUENCE RUNNER: run cards in order, waiting for PASS/FAIL before next
    sequence_keys = [
        "operator", "ag", "sys", "comp", "net", "bat", "tp", "spk", "mic", "br",
        "smartcard", "usb", "nfc", "fingerprint", "ts", "px", "cam", "kb", "act", "drv", "gpu", "enr", "vs"
    ]

    def _get_card_by_key(key):
        try:
            return {
                'operator': operator_card,
                'ag': ag_card,
                'sys': sys_card,
                'comp': comp_card,
                'net': net_card,
                'bat': bat_card,
                'spk': spk_card,
                'mic': mic_card,
                'br': brightness_card,
                'tp': tp_card,
                'smartcard': smartcard_card,
                'usb': usb_card,
                'nfc': nfc_card,
                'fingerprint': fingerprint_card,
                'ts': touchscreen_card,
                'px': pixel_card,
                'cam': cam_card,
                'kb': kb_card,
                'act': act_card,
                'drv': drv_card,
                'gpu': gpu_card,
                'enr': enroll_card,
                'vs': vs_card,
            }.get(key)
        except Exception:
            return None

    def _extract_card_result(text):
        txt = str(text or "").upper()
        if "FAIL" in txt or "FALLA" in txt or "✖" in txt or "✗" in txt:
            return "fail"
        if "PASS" in txt or "APROBADO" in txt or "✔" in txt or "✓" in txt:
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
                        if any(tok in txt for tok in ('PASS', 'FAIL', 'APROBADO', 'FALLA', '✓', '✗', 'NOT RUN', 'SIN EJECUTAR')):
                            return txt
                except Exception:
                    pass
            return None

        try:
            return ui_call_wait(_read_status, timeout=3.0)
        except Exception:
            return None

    def _wait_for_card_result(card, timeout=300, run_id=None, min_time=None):
        start = time.time()
        if min_time is None:
            min_time = 0
        done_evt = threading.Event()
        try:
            card._sequence_done_event = done_evt
        except Exception:
            pass
        try:
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
                        if last >= min_time or done_evt.is_set():
                            _log_sequence(f"wait result for card: {txt}")
                            return txt
                    if not _sequence_running[0]:
                        _log_sequence("wait aborted: sequence cancelled")
                        return None
                except Exception:
                    pass
                if done_evt.wait(0.25):
                    try:
                        txt = _get_card_status_text(card) or ""
                        if _extract_card_result(txt):
                            _log_sequence(f"wait result for card (event): {txt}")
                            return txt
                    except Exception:
                        pass
                if active_screen is None or not widget_exists(active_screen):
                    _log_sequence("wait aborted: active screen missing")
                    return None
        finally:
            try:
                del card._sequence_done_event
            except Exception:
                try:
                    card._sequence_done_event = None
                except Exception:
                    pass
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
            if key == 'net':
                _net_refresh()
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
            if key == 'enr':
                threading.Thread(target=_start_enrollment_check, daemon=True).start()
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
                _reset_card_status(card)
                ui_call(lambda c=card: _highlight_and_show(c))
                min_time = time.time()
                _start_card_by_key(key)
                # wait for operator pass/fail, or automatic result (e.g. network refresh)
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




