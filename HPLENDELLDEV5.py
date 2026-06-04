#!/usr/bin/env python3
"""
HP/Lenovo/Dell BIOS and System Diagnostics Tool
Equivalent to HPLENDELLDEV5.ps1
"""

import os
import sys
import subprocess
import re
import ctypes
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json

try:
    import wmi
except ImportError:
    print("ERROR: The 'wmi' module is not installed.")
    print("Install it with: pip install pywin32")
    sys.exit(1)


@dataclass
class SystemData:
    """Container for system information"""
    system_info: Dict[str, Any] = None
    bios_info: Dict[str, Any] = None
    processor: Dict[str, Any] = None
    disks: List[Dict[str, Any]] = None
    ram_modules: List[Dict[str, Any]] = None
    display_info: List[Dict[str, Any]] = None
    gpus: List[Dict[str, Any]] = None


class HardwareInspector:
    """Main class for hardware inspection and diagnostics"""

    def __init__(self):
        self.is_admin = self.check_admin()
        self.script_directory = Path(__file__).parent
        self.log_file = self.script_directory / f"{Path(__file__).stem}.log"
        self.last_bcu_files = None
        self.wmi_conn = None
        self.setup_logging()
        
        try:
            self.wmi_conn = wmi.WMI()
        except Exception as e:
            logging.error(f"Failed to connect to WMI: {e}")
            print(f"ERROR: Could not connect to WMI service: {e}")

    def check_admin(self) -> bool:
        """Check if running with admin privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def setup_logging(self):
        """Setup logging to file"""
        try:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(self.log_file),
                    logging.StreamHandler()
                ]
            )
        except Exception as e:
            print(f"Warning: Unable to start logging at {self.log_file}. {e}")

    def run_as_admin(self):
        """Re-run script with admin privileges"""
        if not self.is_admin:
            script_path = sys.argv[0]
            print(f"[DEBUG] Attempting to elevate. Script path: {script_path}")
            try:
                # Use ShellExecuteEx with 'runas' verb
                import ctypes
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, f'"{script_path}"', None, 1
                )
                print("[DEBUG] Elevation command sent. Exiting this instance...")
                sys.exit(0)
            except Exception as e:
                print(f"[ERROR] Failed to elevate: {e}")
                sys.exit(1)

    def get_common_system_data(self) -> SystemData:
        """Gather common system information"""
        data = SystemData()
        
        if not self.wmi_conn:
            logging.error("WMI connection not available")
            return data
        
        try:
            # System information
            system_info = self.wmi_conn.Win32_ComputerSystem()[0]
            data.system_info = {
                'Name': system_info.Name,
                'Model': system_info.Model,
                'Manufacturer': system_info.Manufacturer,
                'SystemSKUNumber': system_info.SystemSKUNumber,
                'AdminPasswordStatus': system_info.AdminPasswordStatus,
            }

            # BIOS information
            bios_info = self.wmi_conn.Win32_BIOS()[0]
            data.bios_info = {
                'SerialNumber': bios_info.SerialNumber,
                'Manufacturer': bios_info.Manufacturer,
                'SMBIOSBIOSVersion': bios_info.SMBIOSBIOSVersion,
                'Version': bios_info.Version,
                'Name': bios_info.Name,
            }

            # Processor information
            processors = self.wmi_conn.Win32_Processor()
            data.processor = []
            for cpu in processors:
                data.processor.append({
                    'Name': cpu.Name,
                    'Manufacturer': cpu.Manufacturer,
                    'MaxClockSpeed': cpu.MaxClockSpeed,
                    'Cores': cpu.NumberOfCores,
                })

            # Disk information
            disks = self.wmi_conn.Win32_DiskDrive()
            data.disks = []
            for disk in disks:
                data.disks.append({
                    'Model': disk.Model,
                    'Size': disk.Size,
                    'InterfaceType': disk.InterfaceType,
                    'PNPDeviceID': disk.PNPDeviceID,
                })

            # RAM information
            ram_modules = self.wmi_conn.Win32_PhysicalMemory()
            data.ram_modules = []
            for ram in ram_modules:
                data.ram_modules.append({
                    'Manufacturer': ram.Manufacturer,
                    'PartNumber': ram.PartNumber,
                    'Capacity': ram.Capacity,
                })

            # GPU information
            video_controllers = self.wmi_conn.Win32_VideoController()
            data.gpus = []
            for gpu in video_controllers:
                if gpu.AdapterRAM and gpu.AdapterRAM > 0:
                    if not re.search(
                        r'Microsoft Basic Display|Remote Display|VMware|Virtual',
                        gpu.Name or '',
                        re.IGNORECASE
                    ):
                        data.gpus.append({
                            'Name': gpu.Name,
                            'AdapterRAM': gpu.AdapterRAM,
                        })

        except Exception as e:
            logging.error(f"Error gathering system data: {e}")

        return data

    @staticmethod
    def get_admin_password_text(status: int) -> str:
        """Convert admin password status to readable text"""
        status_map = {
            0: "No",
            1: "Yes",
            2: "NA",
            3: "Unknown",
        }
        return status_map.get(status, "Unknown")

    @staticmethod
    def get_internal_physical_disks(disks: List[Dict]) -> List[Dict]:
        """Filter USB drives and external disks"""
        internal = []
        for disk in disks:
            interface_type = str(disk.get('InterfaceType', ''))
            model = str(disk.get('Model', ''))
            pnp_id = str(disk.get('PNPDeviceID', ''))

            if (
                not re.search(r'^USB$', interface_type, re.IGNORECASE) and
                not re.search(r'\bUSB\b', model, re.IGNORECASE) and
                not re.search(r'^USBSTOR\\', pnp_id, re.IGNORECASE)
            ):
                internal.append(disk)

        return internal

    @staticmethod
    def get_rounded_drive_capacity_gb(size_gb: float) -> float:
        """Round drive capacity to standard sizes"""
        if size_gb <= 32:
            return 32
        elif 45 <= size_gb <= 64:
            return 64
        elif 90 <= size_gb <= 128:
            return 128
        elif 160 <= size_gb <= 256:
            return 256
        elif 400 <= size_gb <= 512:
            return 512
        elif 800 <= size_gb <= 1024:
            return 1024
        elif 1800 <= size_gb <= 2048:
            return 2048
        else:
            return round(size_gb, 2)

    @staticmethod
    def format_drive_capacity_label(size_gb: float) -> str:
        """Format drive capacity as readable string"""
        if size_gb >= 1024:
            size_tb = size_gb / 1024
            if abs(size_tb - round(size_tb, 0)) < 0.001:
                return f"{int(round(size_tb, 0))} TB"
            return f"{size_tb:.2f} TB"

        if abs(size_gb - round(size_gb, 0)) < 0.001:
            return f"{int(round(size_gb, 0))} GB"

        return f"{size_gb:.2f} GB"

    def write_section_header(self, title: str):
        """Write formatted section header"""
        line_length = max(len(title), 16)
        line = "=" * line_length
        print(f"\n{line}\n{title}\n{line}")

    def write_common_system_info(self, data: SystemData):
        """Write common system information report"""
        self.write_section_header("System Info")
        print(f"System Serial: {data.bios_info.get('SerialNumber', 'N/A')}")
        print(f"System SKU: {data.system_info.get('SystemSKUNumber', 'N/A')}")
        print(f"System Model: {data.system_info.get('Model', 'N/A')}")
        print(f"System Name: {data.system_info.get('Name', 'N/A')}")

        admin_status = data.system_info.get('AdminPasswordStatus', 3)
        print(f"BIOS Password: {self.get_admin_password_text(admin_status)}")

        self.write_section_header("CPU Info")
        for cpu in data.processor:
            print(f"Name: {cpu.get('Name', 'N/A')}")
            print(f"Manufacturer: {cpu.get('Manufacturer', 'N/A')}")
            print(f"Max Clock Speed (MHz): {cpu.get('MaxClockSpeed', 'N/A')}")
            print(f"Cores: {cpu.get('Cores', 'N/A')}")
            print()

        self.write_section_header("Hard Drives")
        internal_disks = self.get_internal_physical_disks(data.disks)
        rounded_total_gb = 0

        for disk in internal_disks:
            size_gb = int(disk.get('Size', 0)) / (1024**3) if disk.get('Size') else 0
            rounded_size_gb = self.get_rounded_drive_capacity_gb(size_gb)
            print(f"Model: {disk.get('Model', 'N/A')}")
            print(f"Size: {self.format_drive_capacity_label(rounded_size_gb)}")
            rounded_total_gb += rounded_size_gb

        if not internal_disks:
            print("No internal HDDs or SSDs detected.")
        elif len(internal_disks) > 1:
            print(f"Total: {self.format_drive_capacity_label(rounded_total_gb)}")

        self.write_section_header("Memory")
        for ram in data.ram_modules:
            ram_size_gb = round(int(ram.get('Capacity', 0)) / (1024**3), 2)
            print(f"Name: {ram.get('Manufacturer', 'N/A')} {ram.get('PartNumber', 'N/A')}")
            print(f"Size: {ram_size_gb} GB")
            print()

        self.write_section_header("GPU Info")
        for gpu in data.gpus:
            vram_gb = round(int(gpu.get('AdapterRAM', 0)) / (1024**3), 2)
            print(f"Name: {gpu.get('Name', 'N/A')}")
            print(f"Video Memory: {vram_gb} GB")
            print()

    def get_windows_activation_status(self) -> Tuple[bool, str]:
        """Check Windows activation status"""
        try:
            result = subprocess.run(
                ['powershell', '-Command',
                 'Get-CimInstance -ClassName SoftwareLicensingProduct -Filter "Name like \'Windows%\'" | '
                 'Where-Object { $_.PartialProductKey -and $_.LicenseStatus -ne $null } | '
                 'Select-Object -First 1 -ExpandProperty LicenseStatus'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                license_status = result.stdout.strip()
                if license_status == "1":
                    return True, "Windows is Activated."
                else:
                    return False, "Windows is not activated."
        except Exception as e:
            logging.error(f"Error checking activation: {e}")

        return False, "Unable to determine activation status."

    def run_diagnostics(self):
        """Run full diagnostics"""
        print("\n" + "="*50)
        print("HP/Lenovo/Dell BIOS Diagnostics Tool")
        print("="*50 + "\n")

        data = self.get_common_system_data()
        self.write_common_system_info(data)

        # Windows activation
        self.write_section_header("Windows Activation Status")
        is_activated, activation_message = self.get_windows_activation_status()
        print(activation_message)

        print("\n" + "="*50)
        print("Diagnostics Complete")
        print("="*50 + "\n")


def main():
    """Main entry point"""
    print("[DEBUG] Script started")
    print("[DEBUG] Python version:", sys.version)
    
    try:
        print("[DEBUG] Creating HardwareInspector...")
        inspector = HardwareInspector()
        print(f"[DEBUG] Inspector created. Is admin: {inspector.is_admin}")

        # Elevate if not admin
        if not inspector.is_admin:
            print("[DEBUG] Not running as admin, attempting elevation...")
            print("This script requires administrator privileges.")
            print("Attempting to elevate...")
            inspector.run_as_admin()
            print("[DEBUG] Should have elevated and exited, but didn't?")

        print("[DEBUG] Starting diagnostics...")
        # Run diagnostics
        inspector.run_diagnostics()
        
        print("[DEBUG] Diagnostics complete")
        
    except Exception as e:
        print(f"\n[ERROR] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n[DEBUG] Script finished. Press Enter to exit...")
    try:
        input()
    except EOFError:
        pass


if __name__ == "__main__":
    print("[DEBUG] __main__ block executing")
    main()
