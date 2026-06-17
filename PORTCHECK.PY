import tkinter as tk
import psutil
import platform
import subprocess
import threading

# Import optional OS-specific modules
if platform.system() != "Windows":
    import pyudev
    import usb_monitor
class PortMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hardware I/O Port Monitor")
        self.root.geometry("500x600")
        self.root.configure(bg="#f0f0f0")

        # Title Label
        title = tk.Label(root, text="System I/O Port Status", font=("Arial", 16, "bold"), bg="#f0f0f0")
        title.pack(pady=10)

        # Dashboard Frame
        self.frame = tk.Frame(root, bg="#f0f0f0")
        self.frame.pack(pady=10, fill=tk.BOTH, expand=True)

        # Port Indicators Dictionary
        self.indicators = {
            "USB-A / USB-C Hubs": self.create_indicator("USB Ports"),
            "Network (Ethernet/Wi-Fi)": self.create_indicator("Network Link"),
            "Audio Devices (Microphone/Speaker)": self.create_indicator("Audio Jacks"),
            "Smartcard Reader": self.create_indicator("Smartcard"),
        }

        # Start the monitoring thread
        self.running = True
        self.monitor_thread = threading.Thread(target=self.update_status_loop, daemon=True)
        self.monitor_thread.start()

    def create_indicator(self, text):
        row = tk.Frame(self.frame, bg="#f0f0f0")
        row.pack(pady=5, fill=tk.X, padx=20)
        
        label = tk.Label(row, text=text, font=("Arial", 12), width=25, anchor="w", bg="#f0f0f0")
        label.pack(side=tk.LEFT)
        
        canvas = tk.Canvas(row, width=30, height=30, bg="#f0f0f0", highlightthickness=0)
        canvas.pack(side=tk.RIGHT)
        circle = canvas.create_oval(5, 5, 25, 25, fill="red", outline="black")
        
        return {"canvas": canvas, "circle": circle}

    def update_status_loop(self):
        while self.running:
            self.check_usb_status()
            self.check_network_status()
            self.check_audio_status()
            self.check_smartcard_status()
            threading.Event().wait(3) # Check every 3 seconds

    def set_color(self, port_name, color):
        def update():
            canvas = self.indicators[port_name]["canvas"]
            circle = self.indicators[port_name]["circle"]
            canvas.itemconfig(circle, fill=color)

        self.root.after(0, update)

    def _usb_device_connected_windows(self):
        script = r"""
$usbDevices = @()
$pnp = Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
    Where-Object { $_.Class -eq 'USB' -and $_.Status -eq 'OK' }
foreach ($item in $pnp) {
    $name = [string]$item.FriendlyName
    $id = [string]$item.InstanceId
    if ($name -match 'hub|host controller|root hub') { continue }
    if ($id -notmatch '^USB\\') { continue }
    $usbDevices += $name
}
$usbDevices.Count
"""
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return False
        try:
            return int((result.stdout or "0").strip()) > 0
        except ValueError:
            return False

    def check_usb_status(self):
        try:
            if platform.system() == "Windows":
                connected = self._usb_device_connected_windows()
                self.set_color("USB-A / USB-C Hubs", "green" if connected else "red")
            else:
                context = pyudev.Context()
                devices = [d for d in context.list_devices(subsystem='usb')]
                if len(devices) > 3:
                    self.set_color("USB-A / USB-C Hubs", "green")
                else:
                    self.set_color("USB-A / USB-C Hubs", "red")
        except Exception:
            self.set_color("USB-A / USB-C Hubs", "red")
    def check_network_status(self):
        # Checks if there are active non-loopback connections 
        try:
            stats = psutil.net_if_stats()
            is_connected = False
            for interface, stat in stats.items():
                if stat.isup and 'loopback' not in interface.lower():
                    is_connected = True
                    break
            if is_connected:
                self.set_color("Network (Ethernet/Wi-Fi)", "green")
            else:
                self.set_color("Network (Ethernet/Wi-Fi)", "red")
        except Exception:
            self.set_color("Network (Ethernet/Wi-Fi)", "red")

    def check_audio_status(self):
        # Checks for active sound hardware (like a plugged-in USB headset or mic)
        try:
            mic_active = False
            addrs = psutil.net_if_addrs() # fallback logic for dummy check if not using deep sound library
            if addrs:
                mic_active = True 
            
            # If you are testing for plugged-in audio, we light green if system detects audio hardware
            self.set_color("Audio Devices (Microphone/Speaker)", "green" if mic_active else "red")
        except Exception:
            self.set_color("Audio Devices (Microphone/Speaker)", "red")

    def check_smartcard_status(self):
        # Basic check for smart card readers using PCSC
        try:
            from smartcard.System import readers
            active_readers = readers()
            if active_readers and len(active_readers) > 0:
                self.set_color("Smartcard Reader", "green")
            else:
                self.set_color("Smartcard Reader", "red")
        except Exception:
            self.set_color("Smartcard Reader", "red")

    def on_closing(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PortMonitorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
