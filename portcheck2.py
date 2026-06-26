import ctypes
import os
import uuid
import threading
import time
import tkinter as tk
from tkinter import ttk

try:
    import win32api
    import win32con
    import win32gui
except Exception:
    win32api = None
    win32con = None
    win32gui = None


APP_TITLE = "USB Port Monitor"
WINDOW_SIZE = "640x320"
BG = "#0b1220"
PANEL = "#131c2e"
BORDER = "#24344f"
TEXT = "#e6edf7"
MUTED = "#9fb0c8"
GREEN = "#2ecc71"
WHITE = "#ffffff"
ACCENT = "#5dc7ff"
RED = "#ff6b6b"

VT_LPWSTR = 31
CLSCTX_INPROC_SERVER = 0x1
STGM_READ = 0x0
EDataFlow_RENDER = 0
ERole_CONSOLE = 0
QDC_ONLY_ACTIVE_PATHS = 0x00000002
QDC_VIRTUAL_MODE_AWARE = 0x00000010
ERROR_SUCCESS = 0
ERROR_INSUFFICIENT_BUFFER = 122
DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME = 2
DISPLAYCONFIG_OUTPUT_TECHNOLOGY_HDMI = 5
DISPLAYCONFIG_OUTPUT_TECHNOLOGY_DVI = 4
DISPLAYCONFIG_OUTPUT_TECHNOLOGY_DISPLAYPORT_EXTERNAL = 10
DISPLAYCONFIG_OUTPUT_TECHNOLOGY_DISPLAYPORT_USB_TUNNEL = 18
DISPLAYCONFIG_OUTPUT_TECHNOLOGY_INTERNAL = 0x80000000


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_uint32),
        ("Data2", ctypes.c_uint16),
        ("Data3", ctypes.c_uint16),
        ("Data4", ctypes.c_ubyte * 8),
    ]


def _guid(value):
    return GUID.from_buffer_copy(uuid.UUID(value).bytes_le)


CLSID_MMDeviceEnumerator = _guid("BCDE0395-E52F-467C-8E3D-C4579291692E")
IID_IMMDeviceEnumerator = _guid("A95664D2-9614-4F35-A746-DE8DB63617E6")
IID_IMMDevice = _guid("D666063F-1587-4E43-81F1-B948E807363F")
IID_IPropertyStore = _guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99")
PKEY_Device_FriendlyName = (GUID.from_buffer_copy(uuid.UUID("A45C254E-DF1C-4EFD-8020-67D146A850E0").bytes_le), 14)


def is_windows():
    return os.name == "nt"


def get_usb_drive_letters():
    drive_mask = ctypes.windll.kernel32.GetLogicalDrives()
    drive_letters = []
    for index in range(26):
        if not (drive_mask & (1 << index)):
            continue
        letter = f"{chr(65 + index)}:\\"
        drive_type = ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(letter))
        if drive_type == 2:
            drive_letters.append(letter)
    return drive_letters


def detect_usb():
    drives = get_usb_drive_letters()
    if drives:
        return True, f"Removable USB storage detected ({len(drives)})", "\n".join(f"- {drive}" for drive in drives)
    return False, "No removable USB storage detected", "- No removable drive letters are currently present"


def detect_hdmi():
    try:
        paths = _query_display_paths()
        external_paths = []
        for path in paths:
            tech = int(path.targetInfo.outputTechnology)
            if tech in {
                DISPLAYCONFIG_OUTPUT_TECHNOLOGY_HDMI,
                DISPLAYCONFIG_OUTPUT_TECHNOLOGY_DVI,
                DISPLAYCONFIG_OUTPUT_TECHNOLOGY_DISPLAYPORT_EXTERNAL,
                DISPLAYCONFIG_OUTPUT_TECHNOLOGY_DISPLAYPORT_USB_TUNNEL,
            }:
                external_paths.append(path)

        if external_paths:
            lines = []
            for path in external_paths[:5]:
                name = _display_target_name(path)
                tech = int(path.targetInfo.outputTechnology)
                lines.append(f"- {name} (connector {tech})")
            return True, f"External display detected ({len(external_paths)})", "\n".join(lines)

        return False, "No external display detected", "- No active HDMI/DisplayPort-style paths were reported"
    except Exception as exc:
        try:
            import win32api

            active_displays = []
            for index in range(16):
                try:
                    device = win32api.EnumDisplayDevices(None, index)
                except Exception:
                    break

                state_flags = int(device.StateFlags)
                is_active = bool(state_flags & 0x1)
                if is_active:
                    active_displays.append(
                        (device.DeviceName, device.DeviceString, state_flags)
                    )

            external_displays = [item for item in active_displays if item[0] != r"\\.\DISPLAY1"]
            if external_displays:
                lines = [f"- {name} ({desc})" for name, desc, _flags in external_displays[:5]]
                return True, f"External display detected ({len(external_displays)})", "\n".join(lines)

            return False, "No external display detected", "- Only the primary laptop display is active"
        except Exception:
            return False, "Unable to read HDMI status", f"- {exc}"


def detect_ethernet():
    try:
        import psutil
        matches = []
        for name, stats in psutil.net_if_stats().items():
            if not stats.isup:
                continue
            lowered = name.lower()
            if "ethernet" in lowered or "eth" in lowered or "802.3" in lowered:
                matches.append(name)
        if matches:
            return True, f"Ethernet link is up ({len(matches)})", "\n".join(f"- {m}" for m in matches[:5])
        return False, "No active ethernet link detected", "- Based on local interface stats"
    except Exception as exc:
        return False, "Unable to read Ethernet status", f"- {exc}"


class PROPERTYKEY(ctypes.Structure):
    _fields_ = [("fmtid", GUID), ("pid", ctypes.c_uint32)]


class PROPVARIANT_UNION(ctypes.Union):
    _fields_ = [
        ("pwszVal", ctypes.c_void_p),
        ("punkVal", ctypes.c_void_p),
        ("bstrVal", ctypes.c_void_p),
        ("llVal", ctypes.c_longlong),
        ("ullVal", ctypes.c_ulonglong),
        ("intVal", ctypes.c_int),
        ("uintVal", ctypes.c_uint),
    ]


class PROPVARIANT(ctypes.Structure):
    _anonymous_ = ("value",)
    _fields_ = [
        ("vt", ctypes.c_ushort),
        ("wReserved1", ctypes.c_ushort),
        ("wReserved2", ctypes.c_ushort),
        ("wReserved3", ctypes.c_ushort),
        ("value", PROPVARIANT_UNION),
    ]


class LUID(ctypes.Structure):
    _fields_ = [
        ("LowPart", ctypes.c_uint32),
        ("HighPart", ctypes.c_int32),
    ]


class DISPLAYCONFIG_RATIONAL(ctypes.Structure):
    _fields_ = [
        ("Numerator", ctypes.c_uint32),
        ("Denominator", ctypes.c_uint32),
    ]


class DISPLAYCONFIG_PATH_SOURCE_INFO(ctypes.Structure):
    _fields_ = [
        ("adapterId", LUID),
        ("id", ctypes.c_uint32),
        ("modeInfoIdx", ctypes.c_uint32),
        ("statusFlags", ctypes.c_uint32),
    ]


class DISPLAYCONFIG_PATH_TARGET_INFO(ctypes.Structure):
    _fields_ = [
        ("adapterId", LUID),
        ("id", ctypes.c_uint32),
        ("modeInfoIdx", ctypes.c_uint32),
        ("outputTechnology", ctypes.c_int32),
        ("rotation", ctypes.c_uint32),
        ("scaling", ctypes.c_uint32),
        ("refreshRate", DISPLAYCONFIG_RATIONAL),
        ("scanLineOrdering", ctypes.c_uint32),
        ("targetAvailable", ctypes.c_int32),
        ("statusFlags", ctypes.c_uint32),
    ]


class DISPLAYCONFIG_PATH_INFO(ctypes.Structure):
    _fields_ = [
        ("sourceInfo", DISPLAYCONFIG_PATH_SOURCE_INFO),
        ("targetInfo", DISPLAYCONFIG_PATH_TARGET_INFO),
        ("flags", ctypes.c_uint32),
    ]


class DISPLAYCONFIG_DEVICE_INFO_HEADER(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_uint32),
        ("size", ctypes.c_uint32),
        ("adapterId", LUID),
        ("id", ctypes.c_uint32),
    ]


class DISPLAYCONFIG_TARGET_DEVICE_NAME(ctypes.Structure):
    _fields_ = [
        ("header", DISPLAYCONFIG_DEVICE_INFO_HEADER),
        ("flags", ctypes.c_uint32),
        ("outputTechnology", ctypes.c_int32),
        ("edidManufactureId", ctypes.c_uint16),
        ("edidProductCodeId", ctypes.c_uint16),
        ("connectorInstance", ctypes.c_uint32),
        ("monitorFriendlyDeviceName", ctypes.c_wchar * 64),
        ("monitorDevicePath", ctypes.c_wchar * 128),
    ]


def _query_display_paths():
    user32 = ctypes.windll.user32
    path_count = ctypes.c_uint32()
    mode_count = ctypes.c_uint32()
    flags = QDC_ONLY_ACTIVE_PATHS | QDC_VIRTUAL_MODE_AWARE

    while True:
        result = user32.GetDisplayConfigBufferSizes(flags, ctypes.byref(path_count), ctypes.byref(mode_count))
        if result != ERROR_SUCCESS:
            raise OSError(result)

        path_array = (DISPLAYCONFIG_PATH_INFO * max(1, path_count.value))()
        mode_buffer = ctypes.create_string_buffer(max(1, mode_count.value) * 256)
        result = user32.QueryDisplayConfig(
            flags,
            ctypes.byref(path_count),
            path_array,
            ctypes.byref(mode_count),
            mode_buffer,
            None,
        )
        if result == ERROR_INSUFFICIENT_BUFFER:
            continue
        if result != ERROR_SUCCESS:
            raise OSError(result)
        return list(path_array[:path_count.value])


def _display_target_name(path):
    user32 = ctypes.windll.user32
    target = DISPLAYCONFIG_TARGET_DEVICE_NAME()
    target.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME
    target.header.size = ctypes.sizeof(target)
    target.header.adapterId = path.targetInfo.adapterId
    target.header.id = path.targetInfo.id
    result = user32.DisplayConfigGetDeviceInfo(ctypes.byref(target.header))
    if result == ERROR_SUCCESS and target.monitorFriendlyDeviceName:
        return target.monitorFriendlyDeviceName
    return "Unknown display"


def _release_com_object(pointer):
    if pointer:
        try:
            pointer.contents.lpVtbl.contents.Release(pointer)
        except Exception:
            pass


def _read_default_audio_output_name():
    ole32 = ctypes.windll.ole32
    ole32.CoInitialize(None)
    enumerator = None
    device = None
    store = None
    prop = PROPVARIANT()
    try:
        enumerator_ptr = ctypes.c_void_p()
        hr = ole32.CoCreateInstance(
            ctypes.byref(CLSID_MMDeviceEnumerator),
            None,
            CLSCTX_INPROC_SERVER,
            ctypes.byref(IID_IMMDeviceEnumerator),
            ctypes.byref(enumerator_ptr),
        )
        if hr != 0:
            raise OSError(hr)

        class IMMDeviceEnumerator(ctypes.Structure):
            pass

        class IMMDevice(ctypes.Structure):
            pass

        class IPropertyStore(ctypes.Structure):
            pass

        QueryInterfaceProto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p))
        AddRefProto = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)
        ReleaseProto = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)
        GetDefaultAudioEndpointProto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))
        OpenPropertyStoreProto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p))
        GetValueProto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(PROPERTYKEY), ctypes.POINTER(PROPVARIANT))

        class IMMDeviceEnumeratorVtbl(ctypes.Structure):
            _fields_ = [
                ("QueryInterface", QueryInterfaceProto),
                ("AddRef", AddRefProto),
                ("Release", ReleaseProto),
                ("EnumAudioEndpoints", ctypes.c_void_p),
                ("GetDefaultAudioEndpoint", GetDefaultAudioEndpointProto),
                ("GetDevice", ctypes.c_void_p),
                ("RegisterEndpointNotificationCallback", ctypes.c_void_p),
                ("UnregisterEndpointNotificationCallback", ctypes.c_void_p),
            ]

        class IMMDeviceVtbl(ctypes.Structure):
            _fields_ = [
                ("QueryInterface", QueryInterfaceProto),
                ("AddRef", AddRefProto),
                ("Release", ReleaseProto),
                ("Activate", ctypes.c_void_p),
                ("OpenPropertyStore", OpenPropertyStoreProto),
                ("GetId", ctypes.c_void_p),
                ("GetState", ctypes.c_void_p),
            ]

        class IPropertyStoreVtbl(ctypes.Structure):
            _fields_ = [
                ("QueryInterface", QueryInterfaceProto),
                ("AddRef", AddRefProto),
                ("Release", ReleaseProto),
                ("GetCount", ctypes.c_void_p),
                ("GetAt", ctypes.c_void_p),
                ("GetValue", GetValueProto),
                ("SetValue", ctypes.c_void_p),
                ("Commit", ctypes.c_void_p),
            ]

        IMMDeviceEnumerator._fields_ = [("lpVtbl", ctypes.POINTER(IMMDeviceEnumeratorVtbl))]
        IMMDevice._fields_ = [("lpVtbl", ctypes.POINTER(IMMDeviceVtbl))]
        IPropertyStore._fields_ = [("lpVtbl", ctypes.POINTER(IPropertyStoreVtbl))]

        enumerator = ctypes.cast(enumerator_ptr, ctypes.POINTER(IMMDeviceEnumerator))
        device_ptr = ctypes.c_void_p()
        hr = enumerator.contents.lpVtbl.contents.GetDefaultAudioEndpoint(
            enumerator,
            EDataFlow_RENDER,
            ERole_CONSOLE,
            ctypes.byref(device_ptr),
        )
        if hr != 0:
            raise OSError(hr)

        device = ctypes.cast(device_ptr, ctypes.POINTER(IMMDevice))
        store_ptr = ctypes.c_void_p()
        hr = device.contents.lpVtbl.contents.OpenPropertyStore(device, STGM_READ, ctypes.byref(store_ptr))
        if hr != 0:
            raise OSError(hr)

        store = ctypes.cast(store_ptr, ctypes.POINTER(IPropertyStore))
        hr = store.contents.lpVtbl.contents.GetValue(store, ctypes.byref(PROPERTYKEY(*PKEY_Device_FriendlyName)), ctypes.byref(prop))
        if hr != 0:
            raise OSError(hr)

        if prop.vt != VT_LPWSTR or not prop.pwszVal:
            return ""
        return ctypes.wstring_at(prop.pwszVal)
    finally:
        try:
            ctypes.windll.ole32.PropVariantClear(ctypes.byref(prop))
        except Exception:
            pass
        try:
            if store is not None:
                _release_com_object(store)
        except Exception:
            pass
        try:
            if device is not None:
                _release_com_object(device)
        except Exception:
            pass
        try:
            if enumerator is not None:
                _release_com_object(enumerator)
        except Exception:
            pass
        try:
            ole32.CoUninitialize()
        except Exception:
            pass


def detect_audio_jack():
    try:
        name = _read_default_audio_output_name()
        if not name:
            return False, "No default audio output detected", "- Windows has no active default playback device"
        lowered = name.lower()

        if any(token in lowered for token in ("headphone", "headset", "earphone", "line out", "line-out")):
            return True, "Headphones are the active output", f"- Default output device: {name}"

        return False, "Speakers are still the active output", f"- Default output device: {name}"
    except Exception as exc:
        return False, "Unable to read audio status", f"- {exc}"


class AudioJackWatcher:
    def __init__(self, on_change):
        self._on_change = on_change
        self._state_lock = threading.Lock()
        self._refresh_lock = threading.Lock()
        self._pending_timer = None
        self._stop_event = threading.Event()
        self._hwnd = None
        self.connected = False
        self.summary = "Checking audio jack..."
        self.details = "- Waiting for initial device state"
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def get_state(self):
        with self._state_lock:
            return self.connected, self.summary, self.details

    def stop(self):
        self._stop_event.set()
        hwnd = self._hwnd
        if hwnd and win32gui is not None:
            try:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            except Exception:
                pass

    def _set_state(self, connected, summary, details, notify=True):
        with self._state_lock:
            changed = (
                connected != self.connected
                or summary != self.summary
                or details != self.details
            )
            self.connected = connected
            self.summary = summary
            self.details = details
        if changed and notify and self._on_change:
            self._on_change(connected, summary, details)

    def _refresh_state(self, notify=True):
        with self._refresh_lock:
            connected, summary, details = detect_audio_jack()
            self._set_state(connected, summary, details, notify=notify)

    def _schedule_refresh(self):
        with self._refresh_lock:
            if self._pending_timer is not None:
                return

            def _run_refresh():
                try:
                    self._refresh_state(notify=True)
                finally:
                    with self._refresh_lock:
                        self._pending_timer = None

            self._pending_timer = threading.Timer(0.12, _run_refresh)
            self._pending_timer.daemon = True
            self._pending_timer.start()

    def _wndproc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_DEVICECHANGE:
            self._schedule_refresh()
            return 0
        if msg == win32con.WM_CLOSE:
            try:
                win32gui.DestroyWindow(hwnd)
            except Exception:
                pass
            return 0
        if msg == win32con.WM_DESTROY:
            try:
                win32gui.PostQuitMessage(0)
            except Exception:
                pass
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _run(self):
        self._refresh_state(notify=False)
        threading.Thread(target=self._poll_state_loop, daemon=True).start()
        if win32gui is None or win32con is None or win32api is None:
            return

        class_name = "AudioJackWatcherWindow"
        message_map = {
            win32con.WM_DEVICECHANGE: self._wndproc,
            win32con.WM_CLOSE: self._wndproc,
            win32con.WM_DESTROY: self._wndproc,
        }

        def _window_proc(hwnd, msg, wparam, lparam):
            handler = message_map.get(msg)
            if handler is not None:
                return handler(hwnd, msg, wparam, lparam)
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

        wndclass = win32gui.WNDCLASS()
        wndclass.lpszClassName = class_name
        wndclass.lpfnWndProc = _window_proc
        wndclass.hInstance = win32api.GetModuleHandle(None)

        try:
            win32gui.RegisterClass(wndclass)
        except win32gui.error:
            pass

        self._hwnd = win32gui.CreateWindow(
            class_name,
            class_name,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            wndclass.hInstance,
            None,
        )
        try:
            self._schedule_refresh()
            win32gui.PumpMessages()
        except Exception:
            pass

    def _poll_state_loop(self):
        while not self._stop_event.is_set():
            try:
                self._refresh_state(notify=True)
            except Exception:
                pass
            self._stop_event.wait(0.35)


class PortRow:
    def __init__(self, parent, title, note):
        self.frame = tk.Frame(parent, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        self.frame.columnconfigure(1, weight=1)
        self.indicator = tk.Canvas(self.frame, width=28, height=28, bg=PANEL, highlightthickness=0)
        self.indicator_circle = self.indicator.create_oval(4, 4, 24, 24, fill=WHITE, outline="#cfd7e3", width=2)
        self.indicator.grid(row=0, column=0, rowspan=3, sticky="n", padx=(16, 12), pady=16)

        body = tk.Frame(self.frame, bg=PANEL)
        body.grid(row=0, column=1, rowspan=3, sticky="nsew", padx=(0, 16), pady=14)
        body.columnconfigure(0, weight=1)

        self.title_label = tk.Label(body, text=title, bg=PANEL, fg=TEXT, font=("Segoe UI Semibold", 17))
        self.title_label.grid(row=0, column=0, sticky="w")

        self.state_label = tk.Label(body, text=note, bg=PANEL, fg=MUTED, font=("Segoe UI", 10))
        self.state_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.details_label = tk.Label(
            body,
            text="Waiting for detection...",
            bg=PANEL,
            fg=MUTED,
            font=("Consolas", 9),
            justify="left",
            anchor="nw",
            wraplength=520,
        )
        self.details_label.grid(row=2, column=0, sticky="w", pady=(6, 0))

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

    def set_state(self, connected, summary, details):
        fill = GREEN if connected else WHITE
        outline = GREEN if connected else "#cfd7e3"
        self.indicator.itemconfigure(self.indicator_circle, fill=fill, outline=outline)
        self.state_label.configure(fg=GREEN if connected else MUTED, text=summary)
        self.details_label.configure(text=details)

    def set_error(self, message):
        self.indicator.itemconfigure(self.indicator_circle, fill=WHITE, outline="#cfd7e3")
        self.state_label.configure(fg=RED, text="Unable to read status")
        self.details_label.configure(text=f"- {message}")


class UsbPortMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("760x560")
        self.root.configure(bg=BG)
        self.root.minsize(680, 480)

        self.refresh_in_progress = False
        self.status_text = tk.StringVar(value="Monitoring for USB, HDMI, Ethernet, and Audio Jack changes...")
        self.last_update_text = tk.StringVar(value="Last update: never")
        self.audio_watcher = None

        self._build_ui()
        self._start_audio_watcher()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(150, self.refresh)
        self.root.after(300, self._poll_loop)

    def _build_ui(self):
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill="both", expand=True, padx=18, pady=18)

        header = tk.Frame(outer, bg=BG)
        header.pack(fill="x")

        tk.Label(
            header,
            text="I/O Port Monitor",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI Semibold", 22),
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Live polling for USB, HDMI, Ethernet, and audio jack presence.",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(3, 0))

        toolbar = tk.Frame(outer, bg=BG)
        toolbar.pack(fill="x", pady=(12, 10))

        tk.Button(
            toolbar,
            text="Refresh Now",
            command=self.refresh,
            bg=ACCENT,
            fg="#04111d",
            activebackground="#82d9ff",
            activeforeground="#04111d",
            relief="flat",
            padx=14,
            pady=7,
            font=("Segoe UI Semibold", 10),
            cursor="hand2",
        ).pack(side="left")

        tk.Button(
            toolbar,
            text="Exit",
            command=self.close,
            bg="#3a2230",
            fg=TEXT,
            activebackground="#4a2d3d",
            activeforeground=TEXT,
            relief="flat",
            padx=14,
            pady=7,
            font=("Segoe UI Semibold", 10),
            cursor="hand2",
        ).pack(side="right")

        tk.Label(
            toolbar,
            textvariable=self.last_update_text,
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 10),
        ).pack(side="right", padx=(0, 12))

        tk.Label(
            outer,
            textvariable=self.status_text,
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        card = tk.Frame(outer, bg=BG)
        card.pack(fill="both", expand=True)

        self.port_rows = {}
        self.port_rows["USB"] = PortRow(card, "USB", "External USB device")
        self.port_rows["HDMI"] = PortRow(card, "HDMI", "Active display connection")
        self.port_rows["Ethernet"] = PortRow(card, "Ethernet", "Physical network link")
        self.port_rows["Audio Jack"] = PortRow(card, "Audio Jack", "Wired audio endpoint")

        for index, name in enumerate(("USB", "HDMI", "Ethernet", "Audio Jack")):
            self.port_rows[name].grid(row=index, column=0, sticky="nsew", padx=0, pady=(0, 10))

        card.grid_columnconfigure(0, weight=1)
        for row_index in range(4):
            card.grid_rowconfigure(row_index, weight=1 if row_index < 3 else 0)

        tk.Label(
            outer,
            text="White = not detected   |   Green = detected",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(fill="x", pady=(8, 0))

    def _start_audio_watcher(self):
        def _apply_audio(connected, summary, details):
            self.root.after(0, lambda: self._set_audio_state(connected, summary, details))

        self.audio_watcher = AudioJackWatcher(_apply_audio)
        connected, summary, details = self.audio_watcher.get_state()
        self._set_audio_state(connected, summary, details)

    def _set_audio_state(self, connected, summary, details):
        self.port_rows["Audio Jack"].set_state(connected, summary, details)

    def refresh(self):
        if self.refresh_in_progress:
            return
        self.refresh_in_progress = True
        self.status_text.set("Checking port status...")
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self):
        try:
            usb_connected, usb_summary, usb_details = detect_usb()
            hdmi_connected, hdmi_summary, hdmi_details = detect_hdmi()
            ethernet_connected, ethernet_summary, ethernet_details = detect_ethernet()
            audio_connected, audio_summary, audio_details = self.audio_watcher.get_state() if self.audio_watcher else detect_audio_jack()

            result = {
                "USB": (usb_connected, usb_summary, usb_details),
                "HDMI": (hdmi_connected, hdmi_summary, hdmi_details),
                "Ethernet": (ethernet_connected, ethernet_summary, ethernet_details),
                "Audio Jack": (audio_connected, audio_summary, audio_details),
            }
            self.root.after(0, lambda: self._apply_result(result))
        except Exception as exc:
            self.root.after(0, lambda: self._apply_error(str(exc)))

    def _apply_result(self, result):
        for name, (connected, summary, details) in result.items():
            self.port_rows[name].set_state(connected, summary, details)

        self.status_text.set("Status updated.")
        self.last_update_text.set(f"Last update: {time.strftime('%Y-%m-%d %I:%M:%S %p')}")
        self.refresh_in_progress = False

    def _apply_error(self, message):
        for row in self.port_rows.values():
            row.set_error(message)
        self.status_text.set("Port detection error.")
        self.last_update_text.set(f"Last update: {time.strftime('%Y-%m-%d %I:%M:%S %p')}")
        self.refresh_in_progress = False

    def _poll_loop(self):
        if not self.refresh_in_progress:
            self.refresh()
        self.root.after(300, self._poll_loop)

    def close(self):
        if self.audio_watcher is not None:
            try:
                self.audio_watcher.stop()
            except Exception:
                pass
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TSeparator", background=BORDER)
    except Exception:
        pass
    UsbPortMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
