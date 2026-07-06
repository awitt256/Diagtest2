#!/usr/bin/env python3
"""
Fun Drive Health Diagnostic Script
Checks disk usage, SMART status, and provides colorful output
"""

import os
import platform
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple

try:
    import psutil
except ImportError:
    print("Installing psutil...")
    subprocess.run(['pip', 'install', 'psutil'], check=True)
    import psutil


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str) -> None:
    """Print a styled header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def get_health_indicator(percentage: float) -> str:
    """Get a visual health indicator based on disk usage percentage"""
    if percentage < 50:
        return f"{Colors.OKGREEN}✓ HEALTHY{Colors.ENDC}"
    elif percentage < 75:
        return f"{Colors.OKCYAN}⚠ MODERATE{Colors.ENDC}"
    elif percentage < 90:
        return f"{Colors.WARNING}⚠ HIGH USAGE{Colors.ENDC}"
    else:
        return f"{Colors.FAIL}✗ CRITICAL{Colors.ENDC}"


def get_usage_bar(percentage: float, width: int = 30) -> str:
    """Create a visual usage bar"""
    filled = int(width * percentage / 100)
    bar = '█' * filled + '░' * (width - filled)
    
    if percentage < 50:
        color = Colors.OKGREEN
    elif percentage < 75:
        color = Colors.OKCYAN
    elif percentage < 90:
        color = Colors.WARNING
    else:
        color = Colors.FAIL
    
    return f"{color}[{bar}]{Colors.ENDC} {percentage:.1f}%"


def get_drive_info() -> List[Dict]:
    """Get information about all disk drives"""
    drives = []
    
    if platform.system() == 'Windows':
        # On Windows, check all drive letters
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            drive_path = f"{letter}:\\"
            if os.path.exists(drive_path):
                try:
                    usage = psutil.disk_usage(drive_path)
                    drives.append({
                        'path': drive_path,
                        'device': f"Drive {letter}:",
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent,
                        'fstype': 'NTFS'  # Default assumption
                    })
                except Exception as e:
                    pass
    else:
        # On Unix-like systems
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                drives.append({
                    'path': partition.mountpoint,
                    'device': partition.device,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent,
                    'fstype': partition.fstype
                })
            except Exception as e:
                pass
    
    return drives


def get_smart_status(drive_path: str) -> Tuple[str, str]:
    """Get SMART status for a drive (Windows only)"""
    if platform.system() != 'Windows':
        return "N/A", "GRAY"
    
    try:
        # Extract drive letter
        drive_letter = drive_path[0]
        
        # Use wmic to get SMART status
        result = subprocess.run(
            ['wmic', 'diskdrive', 'get', 'status', '/format:list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and 'OK' in result.stdout:
            return "OK", Colors.OKGREEN
        else:
            return "Unknown", Colors.WARNING
    except Exception:
        return "N/A", Colors.WARNING


def format_bytes(bytes_value: int) -> str:
    """Format bytes into human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def print_drive_info(drive: Dict) -> None:
    """Print information for a single drive"""
    print(f"{Colors.BOLD}{Colors.OKCYAN}📁 {drive['device']}{Colors.ENDC}")
    print(f"   Path: {drive['path']}")
    print(f"   File System: {drive['fstype']}")
    print(f"   Total Space: {format_bytes(drive['total'])}")
    print(f"   Used Space:  {format_bytes(drive['used'])}")
    print(f"   Free Space:  {format_bytes(drive['free'])}")
    print(f"   Usage:       {get_usage_bar(drive['percent'])}")
    print(f"   Status:      {get_health_indicator(drive['percent'])}")
    
    # Try to get SMART status
    smart_status, smart_color = get_smart_status(drive['path'])
    print(f"   SMART:       {smart_color}{smart_status}{Colors.ENDC}")
    print()


def print_system_info() -> None:
    """Print general system information"""
    print(f"{Colors.BOLD}System Information:{Colors.ENDC}")
    print(f"   Platform: {platform.system()} {platform.release()}")
    print(f"   Machine:  {platform.machine()}")
    print(f"   Python:   {platform.python_version()}")
    print(f"   Time:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def main():
    """Main function"""
    print_header("🔍 DRIVE HEALTH DIAGNOSTIC TOOL 🔍")
    
    print_system_info()
    
    drives = get_drive_info()
    
    if not drives:
        print(f"{Colors.FAIL}No drives found!{Colors.ENDC}")
        return
    
    print(f"{Colors.BOLD}Found {len(drives)} drive(s):{Colors.ENDC}\n")
    
    for drive in drives:
        print_drive_info(drive)
    
    # Summary
    print_header("📊 SUMMARY")
    
    total_space = sum(d['total'] for d in drives)
    total_used = sum(d['used'] for d in drives)
    total_free = sum(d['free'] for d in drives)
    overall_percent = (total_used / total_space * 100) if total_space > 0 else 0
    
    print(f"{Colors.BOLD}Combined Storage:{Colors.ENDC}")
    print(f"   Total: {format_bytes(total_space)}")
    print(f"   Used:  {format_bytes(total_used)}")
    print(f"   Free:  {format_bytes(total_free)}")
    print(f"   Usage: {get_usage_bar(overall_percent)}")
    print(f"   Status: {get_health_indicator(overall_percent)}")
    
    # Health check recommendations
    print(f"\n{Colors.BOLD}💡 Recommendations:{Colors.ENDC}")
    
    critical_drives = [d for d in drives if d['percent'] > 90]
    high_usage_drives = [d for d in drives if 75 < d['percent'] <= 90]
    
    if critical_drives:
        print(f"   {Colors.FAIL}⚠ CRITICAL: {len(critical_drives)} drive(s) critically low on space!{Colors.ENDC}")
        for drive in critical_drives:
            print(f"      - {drive['device']}: {drive['percent']:.1f}% used")
    
    if high_usage_drives:
        print(f"   {Colors.WARNING}⚠ WARNING: {len(high_usage_drives)} drive(s) high on space{Colors.ENDC}")
        for drive in high_usage_drives:
            print(f"      - {drive['device']}: {drive['percent']:.1f}% used")
    
    if not critical_drives and not high_usage_drives:
        print(f"   {Colors.OKGREEN}✓ All drives are healthy!{Colors.ENDC}")
    
    print(f"\n{Colors.OKCYAN}Scan complete!{Colors.ENDC}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Scan interrupted by user.{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}Error: {e}{Colors.ENDC}")
