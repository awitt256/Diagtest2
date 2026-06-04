#!/usr/bin/env python3
"""
HP/Lenovo/Dell BIOS and System Diagnostics Tool
Equivalent to HPLENDELLDEV5.ps1
Uses PowerShell for all system queries - no external dependencies
"""

import os
import sys
import subprocess
import json
import ctypes
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class HardwareInspector:
    """Main class for hardware inspection and diagnostics"""

    def __init__(self):
        print("[DEBUG] __init__ starting")
        self.is_admin = self.check_admin()
        print(f"[DEBUG] Is admin: {self.is_admin}")
        self.script_directory = Path(__file__).parent
        self.log_file = self.script_directory / f"{Path(__file__).stem}.log"

    def check_admin(self) -> bool:
        """Check if running with admin privileges"""
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except:
            return False

    def run_ps_command(self, command: str) -> str:
        """Run a PowerShell command and return output"""
        try:
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', command],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return "TIMEOUT"
        except Exception as e:
            return f"ERROR: {e}"

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information via PowerShell"""
        print("[DEBUG] Getting system info...")
        
        ps_script = """
        $systemInfo = Get-CimInstance -ClassName Win32_ComputerSystem
        $biosInfo = Get-CimInstance -ClassName Win32_BIOS
        
        @{
            SystemName = $systemInfo.Name
            SystemModel = $systemInfo.Model
            SystemSKU = $systemInfo.SystemSKUNumber
            BiosSerial = $biosInfo.SerialNumber
            BiosManufacturer = $biosInfo.Manufacturer
            BiosVersion = $biosInfo.SMBIOSBIOSVersion
        } | ConvertTo-Json
        """
        
        output = self.run_ps_command(ps_script)
        try:
            return json.loads(output) if output.startswith('{') else {}
        except:
            return {}

    def get_cpu_info(self) -> List[Dict[str, Any]]:
        """Get CPU information"""
        print("[DEBUG] Getting CPU info...")
        
        ps_script = """
        $cpus = Get-CimInstance -ClassName Win32_Processor
        $cpus | ForEach-Object {
            @{
                Name = $_.Name
                Manufacturer = $_.Manufacturer
                MaxClockSpeed = $_.MaxClockSpeed
                Cores = $_.NumberOfCores
            }
        } | ConvertTo-Json
        """
        
        output = self.run_ps_command(ps_script)
        try:
            data = json.loads(output)
            return data if isinstance(data, list) else [data]
        except:
            return []

    def get_disk_info(self) -> List[Dict[str, Any]]:
        """Get disk information"""
        print("[DEBUG] Getting disk info...")
        
        ps_script = """
        $disks = Get-CimInstance -ClassName Win32_DiskDrive
        $disks | ForEach-Object {
            @{
                Model = $_.Model
                Size = $_.Size
                InterfaceType = $_.InterfaceType
            }
        } | ConvertTo-Json
        """
        
        output = self.run_ps_command(ps_script)
        try:
            data = json.loads(output)
            return data if isinstance(data, list) else [data]
        except:
            return []

    def get_ram_info(self) -> List[Dict[str, Any]]:
        """Get RAM information"""
        print("[DEBUG] Getting RAM info...")
        
        ps_script = """
        $ram = Get-CimInstance -ClassName Win32_PhysicalMemory
        $ram | ForEach-Object {
            @{
                Manufacturer = $_.Manufacturer
                PartNumber = $_.PartNumber
                Capacity = $_.Capacity
            }
        } | ConvertTo-Json
        """
        
        output = self.run_ps_command(ps_script)
        try:
            data = json.loads(output)
            return data if isinstance(data, list) else [data]
        except:
            return []

    def get_gpu_info(self) -> List[Dict[str, Any]]:
        """Get GPU information"""
        print("[DEBUG] Getting GPU info...")
        
        ps_script = """
        $gpus = Get-CimInstance -ClassName Win32_VideoController | Where-Object {
            $_.AdapterRAM -gt 0 -and $_.Name -notmatch 'Microsoft|Remote|VMware|Virtual'
        }
        $gpus | ForEach-Object {
            @{
                Name = $_.Name
                VRAM = $_.AdapterRAM
            }
        } | ConvertTo-Json
        """
        
        output = self.run_ps_command(ps_script)
        try:
            data = json.loads(output)
            return data if isinstance(data, list) else [data]
        except:
            return []

    def format_bytes_to_gb(self, bytes_val: int) -> float:
        """Convert bytes to GB"""
        if bytes_val:
            return round(bytes_val / (1024**3), 2)
        return 0

    def format_capacity_label(self, size_gb: float) -> str:
        """Format capacity as readable label"""
        if size_gb >= 1024:
            size_tb = size_gb / 1024
            if abs(size_tb - round(size_tb)) < 0.001:
                return f"{int(round(size_tb))} TB"
            return f"{size_tb:.2f} TB"
        
        if abs(size_gb - round(size_gb)) < 0.001:
            return f"{int(round(size_gb))} GB"
        
        return f"{size_gb:.2f} GB"

    def print_header(self, title: str):
        """Print a formatted section header"""
        line = "=" * max(len(title), 40)
        print(f"\n{line}")
        print(title)
        print(line)

    def run_diagnostics(self):
        """Run the diagnostics"""
        print("[DEBUG] Starting diagnostics...")
        
        self.print_header("System Information")
        sys_info = self.get_system_info()
        if sys_info:
            print(f"System Name: {sys_info.get('SystemName', 'N/A')}")
            print(f"Model: {sys_info.get('SystemModel', 'N/A')}")
            print(f"BIOS Serial: {sys_info.get('BiosSerial', 'N/A')}")
            print(f"BIOS Version: {sys_info.get('BiosVersion', 'N/A')}")
        else:
            print("ERROR: Could not retrieve system info")

        self.print_header("CPU Information")
        cpus = self.get_cpu_info()
        if cpus:
            for cpu in cpus:
                print(f"Name: {cpu.get('Name', 'N/A')}")
                print(f"Manufacturer: {cpu.get('Manufacturer', 'N/A')}")
                print(f"Max Speed: {cpu.get('MaxClockSpeed', 'N/A')} MHz")
                print(f"Cores: {cpu.get('Cores', 'N/A')}")
                print()
        else:
            print("ERROR: Could not retrieve CPU info")

        self.print_header("Disk Information")
        disks = self.get_disk_info()
        if disks:
            for disk in disks:
                size_gb = self.format_bytes_to_gb(int(disk.get('Size', 0)))
                print(f"Model: {disk.get('Model', 'N/A')}")
                print(f"Size: {self.format_capacity_label(size_gb)}")
                print(f"Type: {disk.get('InterfaceType', 'N/A')}")
                print()
        else:
            print("No disk information available")

        self.print_header("RAM Information")
        ram_list = self.get_ram_info()
        if ram_list:
            for ram in ram_list:
                capacity_gb = self.format_bytes_to_gb(int(ram.get('Capacity', 0)))
                print(f"Manufacturer: {ram.get('Manufacturer', 'N/A')}")
                print(f"Part Number: {ram.get('PartNumber', 'N/A')}")
                print(f"Capacity: {capacity_gb} GB")
                print()
        else:
            print("No RAM information available")

        self.print_header("GPU Information")
        gpus = self.get_gpu_info()
        if gpus:
            for gpu in gpus:
                vram_gb = self.format_bytes_to_gb(int(gpu.get('VRAM', 0)))
                print(f"Name: {gpu.get('Name', 'N/A')}")
                print(f"VRAM: {vram_gb} GB")
                print()
        else:
            print("No GPU information available")

        self.print_header("Diagnostics Complete")
        print("[DEBUG] Diagnostics finished")


def main():
    """Main entry point"""
    print("[DEBUG] Script started")
    print(f"[DEBUG] Python version: {sys.version}")
    
    try:
        print("[DEBUG] Creating inspector...")
        inspector = HardwareInspector()
        
        if not inspector.is_admin:
            print("\nWARNING: Not running as administrator.")
            print("Some system information may be restricted.")
            print("Continuing anyway...\n")
        
        print("[DEBUG] Running diagnostics...")
        inspector.run_diagnostics()
        
    except Exception as e:
        print(f"\n[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n[DEBUG] Script complete.")
    print("Press Enter to exit...")
    try:
        input()
    except EOFError:
        pass


if __name__ == "__main__":
    print("[DEBUG] Main block executing")
    main()
