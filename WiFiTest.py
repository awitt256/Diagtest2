"""
WiFi Test Tool
Displays WiFi adapter information and available networks
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import re
import json
import sys
import ctypes


def is_admin():
    """Check if running as administrator"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    """Re-run the script as administrator"""
    if not is_admin():
        # Re-run the program with admin rights
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()


class WiFiTestTool:
    def __init__(self, root):
        self.root = root
        self.root.title("WiFi Test Tool")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")
        
        # Header
        header_frame = tk.Frame(root, bg="#2196F3", height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="WiFi Test Tool",
            font=("Segoe UI", 20, "bold"),
            bg="#2196F3",
            fg="white"
        )
        title_label.pack(pady=15)
        
        # Main container
        main_container = tk.Frame(root, bg="#f0f0f0")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # WiFi Detection Status Banner
        self.detection_banner = tk.Label(
            main_container,
            text="Checking...",
            font=("Segoe UI", 16, "bold"),
            bg="#f0f0f0",
            fg="#666666",
            pady=15
        )
        self.detection_banner.pack(fill=tk.X, pady=(0, 10))
        
        # WiFi Adapter Info Section
        adapter_frame = tk.LabelFrame(
            main_container,
            text="WiFi Adapter Information",
            font=("Segoe UI", 12, "bold"),
            bg="#f0f0f0",
            padx=10,
            pady=10
        )
        adapter_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.adapter_info_text = scrolledtext.ScrolledText(
            adapter_frame,
            height=8,
            font=("Consolas", 10),
            bg="#ffffff",
            state=tk.DISABLED
        )
        self.adapter_info_text.pack(fill=tk.X)
        
        # Available Networks Section
        networks_frame = tk.LabelFrame(
            main_container,
            text="Available Networks",
            font=("Segoe UI", 12, "bold"),
            bg="#f0f0f0",
            padx=10,
            pady=10
        )
        networks_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Treeview for networks
        columns = ("SSID", "Signal", "Security", "Frequency")
        self.networks_tree = ttk.Treeview(
            networks_frame,
            columns=columns,
            show="headings",
            height=15
        )
        
        self.networks_tree.heading("SSID", text="Network Name (SSID)")
        self.networks_tree.heading("Signal", text="Signal Strength")
        self.networks_tree.heading("Security", text="Security Type")
        self.networks_tree.heading("Frequency", text="Frequency")
        
        self.networks_tree.column("SSID", width=300)
        self.networks_tree.column("Signal", width=120)
        self.networks_tree.column("Security", width=150)
        self.networks_tree.column("Frequency", width=100)
        
        scrollbar = ttk.Scrollbar(networks_frame, orient=tk.VERTICAL, command=self.networks_tree.yview)
        self.networks_tree.configure(yscrollcommand=scrollbar.set)
        
        self.networks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button Frame
        button_frame = tk.Frame(main_container, bg="#f0f0f0")
        button_frame.pack(fill=tk.X)
        
        self.scan_button = tk.Button(
            button_frame,
            text="Scan Networks",
            command=self.scan_networks,
            font=("Segoe UI", 11, "bold"),
            bg="#2196F3",
            fg="white",
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.scan_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.refresh_button = tk.Button(
            button_frame,
            text="Refresh All",
            command=self.refresh_all,
            font=("Segoe UI", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.refresh_button.pack(side=tk.LEFT)
        
        # Debug button
        self.debug_button = tk.Button(
            button_frame,
            text="Debug",
            command=self.show_debug_info,
            font=("Segoe UI", 11, "bold"),
            bg="#FF9800",
            fg="white",
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.debug_button.pack(side=tk.RIGHT)
        
        # Status bar
        self.status_label = tk.Label(
            main_container,
            text="Ready",
            font=("Segoe UI", 9),
            bg="#f0f0f0",
            fg="#666666"
        )
        self.status_label.pack(anchor=tk.W, pady=(10, 0))
        
        # Initial load
        self.refresh_all()
    
    def run_command(self, command):
        """Run a PowerShell command and return output"""
        try:
            result = subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout, result.returncode
        except Exception as e:
            return f"Error: {str(e)}", 1
    
    def get_wifi_adapter_info(self):
        """Get WiFi adapter information"""
        self.adapter_info_text.config(state=tk.NORMAL)
        self.adapter_info_text.delete(1.0, tk.END)
        
        self.status_label.config(text="Scanning for WiFi adapters...", fg="#FF9800")
        self.detection_banner.config(text="Checking...", fg="#666666")
        self.root.update()
        
        # Get WiFi adapter details using PowerShell
        command = """
        $adapters = Get-NetAdapter | Where-Object { $_.InterfaceDescription -like "*Wireless*" -or $_.InterfaceDescription -like "*Wi-Fi*" }
        if ($adapters) {
            foreach ($adapter in $adapters) {
                $ipConfig = Get-NetIPAddress -InterfaceIndex $adapter.InterfaceIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue
                $ip = if ($ipConfig) { $ipConfig.IPAddress } else { "N/A" }
                Write-Output "Adapter Name: $($adapter.Name)"
                Write-Output "Description: $($adapter.InterfaceDescription)"
                Write-Output "Status: $($adapter.Status)"
                Write-Output "MAC Address: $($adapter.MacAddress)"
                Write-Output "IP Address: $ip"
                Write-Output "Link Speed: $($adapter.LinkSpeed)"
                Write-Output "---"
            }
        } else {
            Write-Output "NO_WIFI_ADAPTER"
        }
        """
        
        output, code = self.run_command(command)
        
        if code == 0 and "NO_WIFI_ADAPTER" not in output:
            # Parse and display adapter info
            adapters = output.strip().split("---")
            adapter_count = 0
            
            for adapter in adapters:
                if adapter.strip():
                    adapter_count += 1
                    info_lines = adapter.strip().split("\n")
                    for line in info_lines:
                        self.adapter_info_text.insert(tk.END, line + "\n")
                    self.adapter_info_text.insert(tk.END, "\n")
            
            if adapter_count > 0:
                self.detection_banner.config(text="WiFi Card Detected", fg="#4CAF50")
                self.status_label.config(text=f"Found {adapter_count} WiFi adapter(s)", fg="#4CAF50")
            else:
                self.adapter_info_text.insert(tk.END, "No WiFi adapters detected.\n")
                self.detection_banner.config(text="No WiFi Card Detected", fg="#F44336")
                self.status_label.config(text="No WiFi adapters found", fg="#F44336")
        else:
            self.adapter_info_text.insert(tk.END, "No WiFi adapter detected in this system.\n")
            self.detection_banner.config(text="No WiFi Card Detected", fg="#F44336")
            self.status_label.config(text="No WiFi adapter found", fg="#F44336")
        
        self.adapter_info_text.config(state=tk.DISABLED)
    
    def scan_networks(self):
        """Scan for available WiFi networks"""
        # Clear existing entries
        for item in self.networks_tree.get_children():
            self.networks_tree.delete(item)
        
        self.status_label.config(text="Scanning for available networks...", fg="#FF9800")
        self.root.update()
        
        # Try multiple methods to get networks
        networks = []
        location_permission_error = False
        elevation_error = False
        
        # Method 1: Try netsh wlan show networks (basic mode first)
        try:
            result = subprocess.run(
                ["cmd", "/c", "netsh", "wlan", "show", "networks"],
                capture_output=True,
                text=True,
                timeout=15
            )
            output = result.stdout
            
            # Check for permission errors
            if "location permission" in output.lower():
                location_permission_error = True
            if "requires elevation" in output.lower():
                elevation_error = True
            
            # Check if we got valid output
            if "SSID" in output and "is not running" not in output:
                networks = self.parse_networks(output)
            else:
                # Try with BSSID mode
                result = subprocess.run(
                    ["cmd", "/c", "netsh", "wlan", "show", "networks", "mode=bssid"],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                output = result.stdout
                if "location permission" in output.lower():
                    location_permission_error = True
                if "requires elevation" in output.lower():
                    elevation_error = True
                if "SSID" in output:
                    networks = self.parse_networks(output)
                    
        except Exception as e:
            print(f"Method 1 failed: {e}")
        
        # Method 2: If no networks found, try PowerShell with Wi-Fi profile
        if not networks and not location_permission_error and not elevation_error:
            try:
                ps_command = """
                # Check if WiFi adapter exists and is enabled
                $wifiAdapter = Get-NetAdapter | Where-Object { $_.InterfaceDescription -like "*Wireless*" -or $_.InterfaceDescription -like "*Wi-Fi*" }
                
                if ($wifiAdapter -and $wifiAdapter.Status -eq "Up") {
                    # Try to get networks using netsh
                    $scanOutput = netsh wlan show networks mode=bssid 2>&1
                    Write-Output $scanOutput
                } elseif ($wifiAdapter) {
                    Write-Output "WiFi adapter exists but status is: $($wifiAdapter.Status)"
                } else {
                    Write-Output "NO_WIFI_ADAPTER_FOUND"
                }
                """
                output, code = self.run_command(ps_command)
                if "location permission" in output.lower():
                    location_permission_error = True
                if "requires elevation" in output.lower():
                    elevation_error = True
                if "SSID" in output:
                    networks = self.parse_networks(output)
            except Exception as e:
                print(f"Method 2 failed: {e}")
        
        # Method 3: Use Windows WiFi API (most reliable)
        if not networks and not location_permission_error and not elevation_error:
            try:
                ps_api_command = """
                Add-Type -AssemblyName System.Runtime.WindowsRuntime
                
                # Try to get WiFi networks using Windows Runtime API
                try {
                    $wifiAdapter = Get-NetAdapter | Where-Object { $_.InterfaceDescription -like "*Wireless*" -or $_.InterfaceDescription -like "*Wi-Fi*" } | Select-Object -First 1
                    
                    if ($wifiAdapter) {
                        # Force a scan
                        netsh wlan show networks mode=bssid | Out-Null
                        
                        # Get the output
                        $networkOutput = netsh wlan show networks mode=bssid
                        Write-Output $networkOutput
                    }
                } catch {
                    Write-Output "API_FAILED: $_"
                }
                """
                output, code = self.run_command(ps_api_command)
                if "location permission" in output.lower():
                    location_permission_error = True
                if "requires elevation" in output.lower():
                    elevation_error = True
                if "SSID" in output:
                    networks = self.parse_networks(output)
            except Exception as e:
                print(f"Method 3 failed: {e}")
        
        if networks:
            for network in networks:
                self.networks_tree.insert("", tk.END, values=(
                    network.get("ssid", "Unknown"),
                    network.get("signal", "N/A"),
                    network.get("security", "N/A"),
                    network.get("frequency", "N/A")
                ))
            self.status_label.config(text=f"Found {len(networks)} available network(s)", fg="#4CAF50")
        elif location_permission_error:
            # Try to auto-enable and retry once
            self.status_label.config(text="Enabling Location Services and retrying...", fg="#FF9800")
            self.root.update()
            try:
                enable_cmd = """
                $key = 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\location'
                if (Test-Path $key) { Set-ItemProperty -Path $key -Name 'Value' -Value 'Allow' -Type String -Force }
                $userKey = 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\location'
                if (!(Test-Path $userKey)) { New-Item -Path $userKey -Force | Out-Null }
                Set-ItemProperty -Path $userKey -Name 'Value' -Value 'Allow' -Type String -Force
                """
                subprocess.run(["powershell", "-Command", enable_cmd], capture_output=True, timeout=10)
                # Brief pause and retry scan
                import time
                time.sleep(2)
                self.scan_networks()  # Retry once
                return
            except:
                pass
            self.status_label.config(text="Location Services required - enabling in progress", fg="#F44336")
            self.networks_tree.insert("", tk.END, values=(
                "Location Services Required",
                "-",
                "Enabling...",
                "-"
            ))
        elif elevation_error:
            self.status_label.config(text="Administrator rights required - Please restart as admin", fg="#F44336")
            self.networks_tree.insert("", tk.END, values=(
                "Admin Rights Required",
                "-",
                "Restart as Admin",
                "-"
            ))
        else:
            # Provide helpful message
            self.status_label.config(text="No networks found. Try clicking 'Refresh All' or check WiFi.", fg="#FF9800")
            # Add a note to the treeview
            self.networks_tree.insert("", tk.END, values=(
                "Click 'Refresh All' to scan again",
                "-",
                "Or check WiFi switch",
                "-"
            ))
    
    def parse_networks(self, output):
        """Parse netsh wlan output to extract network information"""
        networks = []
        current_network = {}
        
        lines = output.split("\n")
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Look for SSID line (format: "SSID 1 : NetworkName" or "SSID: NetworkName")
            if "SSID" in line_stripped and ":" in line_stripped:
                if current_network:
                    networks.append(current_network)
                current_network = {}
                
                # Extract SSID name - handle multiple formats
                match = re.search(r'SSID\s*\d*\s*:\s*(.+)', line_stripped, re.IGNORECASE)
                if match:
                    ssid = match.group(1).strip()
                    # Skip if it's just a header or empty
                    if ssid and not ssid.startswith("BSSID"):
                        current_network["ssid"] = ssid
            
            elif "Signal" in line_stripped and current_network:
                match = re.search(r'Signal\s*:\s*(\d+%)', line_stripped)
                if match:
                    current_network["signal"] = match.group(1)
            
            elif "Authentication" in line_stripped and current_network:
                match = re.search(r'Authentication\s*:\s*(.+)', line_stripped)
                if match:
                    auth = match.group(1).strip()
                    current_network["security"] = auth
            
            elif "Encryption" in line_stripped and current_network:
                match = re.search(r'Encryption\s*:\s*(.+)', line_stripped)
                if match:
                    encryption = match.group(1).strip()
                    if "security" not in current_network:
                        current_network["security"] = encryption
            
            elif "Channel" in line_stripped and current_network:
                match = re.search(r'Channel\s*:\s*(\d+)', line_stripped)
                if match:
                    channel = int(match.group(1))
                    # Determine frequency band
                    if channel <= 14:
                        current_network["frequency"] = "2.4 GHz"
                    else:
                        current_network["frequency"] = "5 GHz"
            
            elif "Network type" in line_stripped and current_network:
                match = re.search(r'Network type\s*:\s*(.+)', line_stripped)
                if match:
                    net_type = match.group(1).strip()
                    if "Infrastructure" in net_type:
                        current_network.setdefault("frequency", "2.4/5 GHz")
        
        # Add last network
        if current_network:
            networks.append(current_network)
        
        # Remove duplicates (same SSID appearing multiple times) and filter out empty SSIDs
        unique_networks = []
        seen_ssids = set()
        for net in networks:
            ssid = net.get("ssid", "").strip()
            if ssid and ssid not in seen_ssids and ssid != "No networks detected":
                unique_networks.append(net)
                seen_ssids.add(ssid)
        
        # Sort by signal strength (if available)
        def get_signal_strength(net):
            signal = net.get("signal", "0%")
            try:
                return int(signal.replace("%", ""))
            except:
                return 0
        
        unique_networks.sort(key=get_signal_strength, reverse=True)
        
        return unique_networks
    
    def refresh_all(self):
        """Refresh both adapter info and network list"""
        self.get_wifi_adapter_info()
        self.scan_networks()
    
    def show_debug_info(self):
        """Show debug information in a new window"""
        debug_window = tk.Toplevel(self.root)
        debug_window.title("WiFi Debug Info")
        debug_window.geometry("800x600")
        
        debug_text = scrolledtext.ScrolledText(
            debug_window,
            font=("Consolas", 9),
            wrap=tk.WORD
        )
        debug_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        debug_text.insert(tk.END, "=== WiFi Debug Information ===\n\n", "header")
        debug_text.tag_config("header", font=("Consolas", 11, "bold"))
        
        # Run netsh commands and show output
        commands = [
            ("netsh wlan show interfaces", "WiFi Interfaces"),
            ("netsh wlan show networks", "Available Networks (basic)"),
            ("netsh wlan show networks mode=bssid", "Available Networks (detailed)"),
            ("netsh wlan show profiles", "WiFi Profiles"),
        ]
        
        for cmd, description in commands:
            debug_text.insert(tk.END, f"\n{'='*60}\n", "header")
            debug_text.insert(tk.END, f"{description}\n", "header")
            debug_text.insert(tk.END, f"Command: {cmd}\n")
            debug_text.insert(tk.END, f"{'='*60}\n\n", "header")
            
            try:
                result = subprocess.run(
                    ["cmd", "/c", cmd],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                debug_text.insert(tk.END, result.stdout + "\n")
                if result.stderr:
                    debug_text.insert(tk.END, f"\nErrors:\n{result.stderr}\n", "error")
                    debug_text.tag_config("error", foreground="red")
            except Exception as e:
                debug_text.insert(tk.END, f"Error running command: {str(e)}\n", "error")
        
        debug_text.insert(tk.END, "\n" + "="*60 + "\n", "header")
        debug_text.insert(tk.END, "End of Debug Output\n", "header")


def main():
    # Check if running as admin, if not, restart as admin silently
    if not is_admin():
        # Re-launch as admin silently
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit()
        except Exception as e:
            # If user declines or error, continue anyway
            pass
    
    # Enable Location Services automatically using multiple methods
    try:
        enable_location_command = """
        # Method 1: Enable via Registry - System Level
        $key1 = 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\location'
        if (!(Test-Path $key1)) { New-Item -Path $key1 -Force | Out-Null }
        Set-ItemProperty -Path $key1 -Name 'Value' -Value 'Allow' -Type String -Force
        
        # Method 2: Enable via Registry - User Level
        $key2 = 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\location'
        if (!(Test-Path $key2)) { New-Item -Path $key2 -Force | Out-Null }
        Set-ItemProperty -Path $key2 -Name 'Value' -Value 'Allow' -Type String -Force
        
        # Method 3: Enable via Policy
        $key3 = 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\LocationAndSensors'
        if (!(Test-Path $key3)) { New-Item -Path $key3 -Force | Out-Null }
        Set-ItemProperty -Path $key3 -Name 'DisableLocation' -Value 0 -Type DWord -Force
        Remove-ItemProperty -Path $key3 -Name 'DisableWindowsLocationPlatform' -ErrorAction SilentlyContinue
        
        # Method 4: Enable Non-Packaged apps access
        $key4 = 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\location\\NonPackaged'
        if (!(Test-Path $key4)) { New-Item -Path $key4 -Force | Out-Null }
        Set-ItemProperty -Path $key4 -Name 'Value' -Value 'Allow' -Type String -Force
        
        # Method 5: Restart Location Service
        $svc = Get-Service -Name 'lfsvc' -ErrorAction SilentlyContinue
        if ($svc) {
            if ($svc.Status -ne 'Running') {
                Start-Service -Name 'lfsvc' -ErrorAction SilentlyContinue
            } else {
                Restart-Service -Name 'lfsvc' -ErrorAction SilentlyContinue
            }
        }
        
        # Method 6: Enable via WMI (if available)
        try {
            $location = Get-WmiObject -Namespace "root\\SecurityCenter2" -Class AntiVirusProduct -ErrorAction SilentlyContinue
        } catch {}
        
        Write-Output "Location Services enabled successfully"
        """
        result = subprocess.run(
            ["powershell", "-Command", enable_location_command],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        # Also try using reg.exe directly (works even if PowerShell has issues)
        subprocess.run(
            ["reg", "add", 
             "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\location",
             "/v", "Value", "/t", "REG_SZ", "/d", "Allow", "/f"],
            capture_output=True, timeout=5
        )
        subprocess.run(
            ["reg", "add",
             "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\location",
             "/v", "Value", "/t", "REG_SZ", "/d", "Allow", "/f"],
            capture_output=True, timeout=5
        )
        
    except Exception as e:
        print(f"Could not auto-enable location: {e}")
    
    # Brief pause to let settings take effect
    import time
    time.sleep(1)
    
    root = tk.Tk()
    app = WiFiTestTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
