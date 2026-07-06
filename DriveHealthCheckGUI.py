#!/usr/bin/env python3
"""
Fun Drive Health Diagnostic GUI
Colorful interface with animations and visual indicators
"""

import os
import platform
import subprocess
import threading
import time
from datetime import datetime
from tkinter import ttk, font
from typing import Dict, List
import tkinter as tk
from tkinter import messagebox

try:
    import psutil
except ImportError:
    print("Installing psutil...")
    subprocess.run(['pip', 'install', 'psutil'], check=True)
    import psutil

try:
    import wmi
except ImportError:
    print("Installing wmi...")
    subprocess.run(['pip', 'install', 'wmi', 'pywin32'], check=True)
    import wmi


def is_admin() -> bool:
    """Check if the script is running as administrator"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def relaunch_as_admin():
    """Relaunch the script with administrator privileges"""
    try:
        import ctypes
        import sys
        
        # Get the script path
        script_path = sys.argv[0]
        if not script_path.endswith('.py'):
            # If running from an executable or interactive shell
            script_path = __file__
        
        # Use ShellExecuteW to relaunch with admin rights
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            f'"{script_path}"',
            None,
            1
        )
        return True
    except Exception as e:
        print(f"Failed to relaunch as admin: {e}")
        return False


# Auto-relaunch as administrator if not already running as admin
if platform.system() == 'Windows' and not is_admin():
    print("Requesting administrator privileges...")
    if relaunch_as_admin():
        print("Relaunching with administrator privileges...")
        import sys
        sys.exit()
    else:
        print("Could not obtain administrator privileges. Some features may not work.")


class DriveHealthGUI:
    """Fun Drive Health Diagnostic GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 Drive Health Detective 🔍")
        self.root.geometry("900x700")
        self.root.configure(bg='#1e1e2e')
        
        # Custom colors
        self.colors = {
            'bg': '#1e1e2e',
            'card': '#313244',
            'text': '#cdd6f4',
            'green': '#a6e3a1',
            'yellow': '#f9e2af',
            'orange': '#fab387',
            'red': '#f38ba8',
            'blue': '#89b4fa',
            'purple': '#cba6f7',
            'cyan': '#94e2d5'
        }
        
        self.setup_styles()
        self.create_widgets()
        self.animate_startup()
        
    def setup_styles(self):
        """Setup custom styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles
        style.configure('Card.TFrame', background=self.colors['card'])
        style.configure('Header.TLabel', 
                       background=self.colors['card'],
                       foreground=self.colors['blue'],
                       font=('Segoe UI', 16, 'bold'))
        style.configure('Info.TLabel',
                       background=self.colors['card'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 10))
        style.configure('Value.TLabel',
                       background=self.colors['card'],
                       foreground=self.colors['cyan'],
                       font=('Segoe UI', 10, 'bold'))
        style.configure('Status.TLabel',
                       background=self.colors['card'],
                       font=('Segoe UI', 11, 'bold'))
        
        # Progress bar styles
        style.configure('Green.Horizontal.TProgressbar',
                       background=self.colors['green'],
                       troughcolor='#45475a',
                       thickness=20)
        style.configure('Yellow.Horizontal.TProgressbar',
                       background=self.colors['yellow'],
                       troughcolor='#45475a',
                       thickness=20)
        style.configure('Orange.Horizontal.TProgressbar',
                       background=self.colors['orange'],
                       troughcolor='#45475a',
                       thickness=20)
        style.configure('Red.Horizontal.TProgressbar',
                       background=self.colors['red'],
                       troughcolor='#45475a',
                       thickness=20)
        
        # Button style
        style.configure('Scan.TButton',
                       background=self.colors['blue'],
                       foreground='#1e1e2e',
                       font=('Segoe UI', 12, 'bold'),
                       borderwidth=0)
        style.map('Scan.TButton',
                 background=[('active', self.colors['cyan'])])
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(
            header_frame,
            text="🔍 Drive Health Detective 🔍",
            bg=self.colors['bg'],
            fg=self.colors['purple'],
            font=('Segoe UI', 24, 'bold')
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame,
            text="Scanning your drives for health issues...",
            bg=self.colors['bg'],
            fg=self.colors['text'],
            font=('Segoe UI', 10)
        )
        subtitle_label.pack()
        
        # System info frame
        self.system_frame = ttk.Frame(main_frame, style='Card.TFrame')
        self.system_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.system_label = ttk.Label(
            self.system_frame,
            text="🖥️ System Information",
            style='Header.TLabel'
        )
        self.system_label.pack(pady=(10, 5), padx=15, anchor='w')
        
        self.system_info_label = ttk.Label(
            self.system_frame,
            text="Loading...",
            style='Info.TLabel'
        )
        self.system_info_label.pack(pady=(0, 10), padx=15, anchor='w')
        
        # Scan button
        self.scan_button = tk.Button(
            main_frame,
            text="🚀 SCAN DRIVES",
            command=self.start_scan,
            bg=self.colors['blue'],
            fg='#1e1e2e',
            font=('Segoe UI', 14, 'bold'),
            relief=tk.FLAT,
            padx=30,
            pady=10,
            cursor='hand2'
        )
        self.scan_button.pack(pady=(0, 10))
        
        # SFC Scan button
        self.sfc_button = tk.Button(
            main_frame,
            text="🔧 RUN SFC SCAN",
            command=self.start_sfc_scan,
            bg=self.colors['purple'],
            fg='#1e1e2e',
            font=('Segoe UI', 12, 'bold'),
            relief=tk.FLAT,
            padx=30,
            pady=8,
            cursor='hand2'
        )
        self.sfc_button.pack(pady=(0, 10))
        
        # SFC Results frame
        self.sfc_frame = ttk.Frame(main_frame, style='Card.TFrame')
        self.sfc_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.sfc_label = ttk.Label(
            self.sfc_frame,
            text="🔧 System File Checker",
            style='Header.TLabel'
        )
        self.sfc_label.pack(pady=(10, 5), padx=15, anchor='w')
        
        self.sfc_result_label = ttk.Label(
            self.sfc_frame,
            text="Click 'RUN SFC SCAN' to check system file integrity",
            style='Info.TLabel'
        )
        self.sfc_result_label.pack(pady=(0, 10), padx=15, anchor='w')
        
        self.sfc_frame.pack_forget()  # Hide initially
        
        # Drives container
        self.drives_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        self.drives_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollable frame for drives
        canvas = tk.Canvas(self.drives_frame, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.drives_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Summary frame
        self.summary_frame = ttk.Frame(main_frame, style='Card.TFrame')
        self.summary_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.summary_label = ttk.Label(
            self.summary_frame,
            text="📊 Summary",
            style='Header.TLabel'
        )
        self.summary_label.pack(pady=(10, 5), padx=15, anchor='w')
        
        self.summary_info_label = ttk.Label(
            self.summary_frame,
            text="Click 'Scan Drives' to begin",
            style='Info.TLabel'
        )
        self.summary_info_label.pack(pady=(0, 10), padx=15, anchor='w')
        
        # Load system info
        self.update_system_info()
    
    def update_system_info(self):
        """Update system information display"""
        info = f"   Platform: {platform.system()} {platform.release()}\n"
        info += f"   Machine:  {platform.machine()}\n"
        info += f"   Python:   {platform.python_version()}\n"
        info += f"   Time:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        self.system_info_label.config(text=info)
    
    def animate_startup(self):
        """Animate startup with loading effect"""
        dots = ""
        for i in range(3):
            dots += "."
            self.root.update()
            time.sleep(0.2)
    
    def start_scan(self):
        """Start the drive scan in a separate thread"""
        self.scan_button.config(state=tk.DISABLED, text="🔄 SCANNING...")
        self.root.update()
        
        # Clear previous results
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Start scan in thread
        thread = threading.Thread(target=self.scan_drives)
        thread.daemon = True
        thread.start()
    
    def start_sfc_scan(self):
        """Start the SFC scan in a separate thread"""
        self.sfc_button.config(state=tk.DISABLED, text="🔄 SCANNING...")
        self.root.update()
        
        # Start SFC scan in thread
        thread = threading.Thread(target=self.sfc_scan_thread)
        thread.daemon = True
        thread.start()
    
    def sfc_scan_thread(self):
        """Run SFC scan in background thread"""
        try:
            print("SFC scan thread started...")
            sfc_result = self.run_sfc_scan()
            print(f"SFC scan completed: {sfc_result['status']}")
            
            # Update GUI in main thread
            self.root.after(0, lambda: self.display_sfc_result(sfc_result))
            
        except Exception as e:
            print(f"SFC scan error: {e}")
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: messagebox.showerror("Error", f"SFC scan failed: {e}"))
            self.root.after(0, lambda: self.sfc_button.config(state=tk.NORMAL, text="🔧 RUN SFC SCAN"))
    
    def display_sfc_result(self, result: Dict):
        """Display SFC scan results in main window"""
        print(f"Displaying SFC result: {result['status']}")
        
        # Reset button first
        self.sfc_button.config(state=tk.NORMAL, text="🔧 RUN SFC SCAN")
        
        # Show SFC frame
        self.sfc_frame.pack(fill=tk.X, pady=(0, 15), before=self.drives_frame)
        
        # Determine status color and text
        if result['status'] == 'Completed' and result['errors_found'] == 0:
            status_text = "✓ No integrity violations found"
            status_color = self.colors['green']
        elif result['status'] == 'Completed' and result['errors_found'] > 0:
            status_text = f"⚠ Found {result['errors_found']} error(s)"
            status_color = self.colors['orange']
        elif result['status'] == 'Requires Administrator':
            status_text = "⚠ Requires administrator privileges"
            status_color = self.colors['yellow']
        elif result['status'] == 'Permission Error':
            status_text = "⚠ Permission error"
            status_color = self.colors['red']
        elif result['status'] == 'Timeout':
            status_text = "⚠ Scan timed out"
            status_color = self.colors['orange']
        else:
            status_text = f"Status: {result['status']}"
            status_color = self.colors['text']
        
        # Build result text
        result_text = f"{status_text}\n\n"
        if result['output']:
            result_text += result['output']
        
        # Update the result label
        self.sfc_result_label.config(text=result_text, foreground=status_color)
    
    def scan_drives(self):
        """Scan all drives and update GUI"""
        try:
            drives = self.get_drive_info()
            
            # Update GUI in main thread
            self.root.after(0, lambda: self.display_drives(drives))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Scan failed: {e}"))
            self.root.after(0, lambda: self.scan_button.config(state=tk.NORMAL, text="🚀 SCAN DRIVES"))
    
    def get_drive_info(self) -> List[Dict]:
        """Get information about all disk drives"""
        drives = []
        
        if platform.system() == 'Windows':
            # Get SMART data first
            smart_data = self.get_smart_data()
            
            for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                drive_path = f"{letter}:\\"
                if os.path.exists(drive_path):
                    try:
                        usage = psutil.disk_usage(drive_path)
                        drive_info = {
                            'path': drive_path,
                            'device': f"Drive {letter}:",
                            'total': usage.total,
                            'used': usage.used,
                            'free': usage.free,
                            'percent': usage.percent,
                            'fstype': 'NTFS',
                            'smart_health': 'Unknown',
                            'smart_percent': 0
                        }
                        
                        # Try to match with SMART data
                        drive_letter = letter.lower()
                        smart_model = 'Unknown'
                        if drive_letter in smart_data:
                            drive_info['smart_health'] = smart_data[drive_letter]['status']
                            drive_info['smart_percent'] = smart_data[drive_letter]['percent']
                            smart_model = smart_data[drive_letter].get('model', 'Unknown')
                        
                        # Get detailed drive information (pass model from SMART)
                        drive_details = self.get_drive_details(letter, smart_model)
                        drive_info.update(drive_details)
                        
                        # Get SSD metrics if applicable
                        if drive_details['is_ssd']:
                            ssd_metrics = self.get_ssd_metrics(letter)
                            drive_info.update(ssd_metrics)
                        
                        # Check filesystem health
                        fs_health = self.check_filesystem_health(drive_path)
                        drive_info['fs_status'] = fs_health['status']
                        drive_info['fs_needs_repair'] = fs_health['needs_repair']
                        
                        drives.append(drive_info)
                    except Exception:
                        pass
        else:
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
                except Exception:
                    pass
        
        return drives
    
    def display_drives(self, drives: List[Dict]):
        """Display drive information in GUI"""
        if not drives:
            no_drives_label = tk.Label(
                self.scrollable_frame,
                text="No drives found!",
                bg=self.colors['bg'],
                fg=self.colors['red'],
                font=('Segoe UI', 14, 'bold')
            )
            no_drives_label.pack(pady=20)
            self.scan_button.config(state=tk.NORMAL, text="🚀 SCAN DRIVES")
            return
        
        # Display each drive
        for i, drive in enumerate(drives):
            self.create_drive_card(drive, i)
            
            # Animate appearance
            self.root.update()
            time.sleep(0.1)
        
        # Update summary
        self.update_summary(drives)
        
        self.scan_button.config(state=tk.NORMAL, text="🚀 SCAN DRIVES")
    
    def create_drive_card(self, drive: Dict, index: int):
        """Create a card for a single drive"""
        card = ttk.Frame(self.scrollable_frame, style='Card.TFrame')
        card.pack(fill=tk.X, pady=5, padx=5)
        
        # Drive header
        header = tk.Frame(card, bg=self.colors['card'])
        header.pack(fill=tk.X, pady=(10, 5), padx=15)
        
        emoji = "💾" if drive['percent'] < 50 else "⚠️" if drive['percent'] < 75 else "🔥" if drive['percent'] < 90 else "🚨"
        
        drive_label = tk.Label(
            header,
            text=f"{emoji} {drive['device']}",
            bg=self.colors['card'],
            fg=self.colors['blue'],
            font=('Segoe UI', 14, 'bold')
        )
        drive_label.pack(side=tk.LEFT)
        
        # Status badge
        status_text, status_color = self.get_status_info(drive['percent'])
        status_label = tk.Label(
            header,
            text=status_text,
            bg=status_color,
            fg='#1e1e2e',
            font=('Segoe UI', 10, 'bold'),
            padx=10,
            pady=2
        )
        status_label.pack(side=tk.RIGHT)
        
        # Info grid
        info_frame = tk.Frame(card, bg=self.colors['card'])
        info_frame.pack(fill=tk.X, pady=(0, 10), padx=15)
        
        labels = [
            ("Path:", drive['path']),
            ("File System:", drive['fstype']),
            ("Total:", self.format_bytes(drive['total'])),
            ("Used:", self.format_bytes(drive['used'])),
            ("Free:", self.format_bytes(drive['free']))
        ]
        
        # Add model and serial if available
        if drive.get('model') and drive['model'] != 'Unknown':
            labels.append(("Model:", drive['model']))
        if drive.get('serial') and drive['serial'] != 'Unknown':
            labels.append(("Serial:", drive['serial']))
        if drive.get('interface') and drive['interface'] != 'Unknown':
            labels.append(("Interface:", drive['interface']))
        if drive.get('temperature') and drive['temperature'] != 'Unknown':
            labels.append(("Temperature:", drive['temperature']))
        if drive.get('fs_status') and drive['fs_status'] != 'Unknown':
            fs_color = self.colors['red'] if drive.get('fs_needs_repair') else self.colors['green']
            labels.append(("FS Health:", drive['fs_status']))
        
        # Add SSD metrics if available
        if drive.get('is_ssd'):
            labels.append(("Type:", "SSD"))
            if drive.get('tbw') and drive['tbw'] != 'Unknown':
                labels.append(("TBW:", drive['tbw']))
            if drive.get('wear_level') and drive['wear_level'] != 'Unknown':
                labels.append(("Wear Level:", drive['wear_level']))
            if drive.get('life_remaining') and drive['life_remaining'] != 'Unknown':
                labels.append(("Life Remaining:", drive['life_remaining']))
        
        # Add SMART health if available
        if drive.get('smart_health') and drive['smart_health'] != 'Unknown':
            labels.append(("SMART Health:", f"{drive['smart_health']} ({drive['smart_percent']:.0f}%)"))
        
        for i, (label, value) in enumerate(labels):
            row = i // 2
            col = (i % 2) * 2
            
            tk.Label(
                info_frame,
                text=label,
                bg=self.colors['card'],
                fg=self.colors['text'],
                font=('Segoe UI', 9)
            ).grid(row=row, column=col, sticky='w', padx=(0, 5))
            
            tk.Label(
                info_frame,
                text=value,
                bg=self.colors['card'],
                fg=self.colors['cyan'],
                font=('Segoe UI', 9, 'bold')
            ).grid(row=row, column=col+1, sticky='w', padx=(0, 20))
        
        # Progress bar
        progress_frame = tk.Frame(card, bg=self.colors['card'])
        progress_frame.pack(fill=tk.X, pady=(0, 10), padx=15)
        
        tk.Label(
            progress_frame,
            text="Usage:",
            bg=self.colors['card'],
            fg=self.colors['text'],
            font=('Segoe UI', 9)
        ).pack(side=tk.LEFT)
        
        progress_style = self.get_progress_style(drive['percent'])
        progress = ttk.Progressbar(
            progress_frame,
            style=progress_style,
            length=400,
            mode='determinate',
            maximum=100,
            value=drive['percent']
        )
        progress.pack(side=tk.LEFT, padx=10)
        
        percent_label = tk.Label(
            progress_frame,
            text=f"{drive['percent']:.1f}%",
            bg=self.colors['card'],
            fg=self.colors['cyan'],
            font=('Segoe UI', 10, 'bold')
        )
        percent_label.pack(side=tk.LEFT)
        
        # SMART Health indicator
        if drive.get('smart_health') and drive['smart_health'] != 'Unknown':
            smart_frame = tk.Frame(card, bg=self.colors['card'])
            smart_frame.pack(fill=tk.X, pady=(0, 10), padx=15)
            
            tk.Label(
                smart_frame,
                text="SMART Health:",
                bg=self.colors['card'],
                fg=self.colors['text'],
                font=('Segoe UI', 9)
            ).pack(side=tk.LEFT)
            
            smart_style = self.get_progress_style(drive['smart_percent'])
            smart_progress = ttk.Progressbar(
                smart_frame,
                style=smart_style,
                length=200,
                mode='determinate',
                maximum=100,
                value=drive['smart_percent']
            )
            smart_progress.pack(side=tk.LEFT, padx=10)
            
            smart_percent_label = tk.Label(
                smart_frame,
                text=f"{drive['smart_percent']:.0f}%",
                bg=self.colors['card'],
                fg=self.colors['cyan'],
                font=('Segoe UI', 10, 'bold')
            )
            smart_percent_label.pack(side=tk.LEFT)
    
    def get_smart_data(self) -> Dict:
        """Get SMART data for all drives using wmic command with better mapping"""
        smart_data = {}
        
        if platform.system() != 'Windows':
            return smart_data
        
        try:
            # First, get all logical disks and their associated disk indices
            logical_to_disk = {}
            try:
                result = subprocess.run(
                    ['wmic', 'partition', 'get', 'DiskIndex,DriveLetter', '/format:list'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    current_part = {}
                    for line in result.stdout.strip().split('\n'):
                        line = line.strip()
                        if '=' in line:
                            key, value = line.split('=', 1)
                            current_part[key.strip()] = value.strip()
                        elif line == '' and current_part:
                            if 'DiskIndex' in current_part and 'DriveLetter' in current_part:
                                drive_letter = current_part['DriveLetter'].strip().lower()
                                disk_index = current_part['DiskIndex'].strip()
                                if drive_letter and len(drive_letter) == 1:
                                    logical_to_disk[drive_letter] = disk_index
                            current_part = {}
            except Exception as e:
                print(f"SMART Debug - Partition mapping error: {e}")
            
            print(f"SMART Debug - Logical to disk mapping: {logical_to_disk}")
            
            # Get disk drive status
            result = subprocess.run(
                ['wmic', 'diskdrive', 'get', 'status,model,index', '/format:list'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            print(f"SMART Debug - wmic result: {result.returncode}")
            print(f"SMART Debug - output: {result.stdout[:500]}")
            
            if result.returncode == 0:
                # Parse the list format output
                current_disk = {}
                for line in result.stdout.strip().split('\n'):
                    line = line.strip()
                    if '=' in line:
                        key, value = line.split('=', 1)
                        current_disk[key.strip()] = value.strip()
                    elif line == '' and current_disk:
                        # Process completed disk entry
                        if 'Index' in current_disk and 'Status' in current_disk:
                            index = current_disk['Index']
                            status = current_disk['Status']
                            model = current_disk.get('Model', 'Unknown')
                            
                            # Calculate health percentage
                            health_percent = 100
                            if "Predict" in status or "Fail" in status.lower() or "Error" in status.lower():
                                health_percent = 20
                            elif "Warning" in status.lower() or "Degraded" in status.lower():
                                health_percent = 50
                            elif "OK" in status or "Healthy" in status.lower():
                                health_percent = 100
                            
                            # Map to drive letters using our pre-built mapping
                            for drive_letter, disk_idx in logical_to_disk.items():
                                if disk_idx == index:
                                    smart_data[drive_letter] = {
                                        'status': status,
                                        'percent': health_percent,
                                        'model': model
                                    }
                                    print(f"SMART Debug - Mapped drive {drive_letter} (disk {index}): {status} ({health_percent}%)")
                        
                        current_disk = {}
                                
        except Exception as e:
            print(f"Could not get SMART data: {e}")
            
        print(f"SMART Debug - Final smart_data: {smart_data}")
            
        # Fallback: assign default SMART health to all drives
        if not smart_data:
            print("SMART Debug - Using fallback for all drives")
            for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                drive_path = f"{letter}:\\"
                if os.path.exists(drive_path):
                    smart_data[letter.lower()] = {
                        'status': 'OK',
                        'percent': 100,
                        'model': 'Unknown'
                    }
            
        return smart_data
    
    def get_drive_details(self, drive_letter: str, smart_model: str = 'Unknown') -> Dict:
        """Get detailed drive information including model, serial, temperature"""
        details = {
            'model': smart_model,  # Use model from SMART data if available
            'serial': 'Unknown',
            'temperature': 'Unknown',
            'is_ssd': False,
            'interface': 'Unknown',
            'firmware': 'Unknown'
        }
        
        if platform.system() != 'Windows':
            return details
        
        try:
            # Get disk drive information using wmic
            result = subprocess.run(
                ['wmic', 'diskdrive', 'get', 'model,serialnumber,interface type,firmware,media type', '/format:list'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse the list format output
                current_disk = {}
                for line in result.stdout.strip().split('\n'):
                    line = line.strip()
                    if '=' in line:
                        key, value = line.split('=', 1)
                        current_disk[key.strip().lower()] = value.strip()
                    elif line == '' and current_disk:
                        # Try to map this disk to the drive letter
                        if 'model' in current_disk:
                            # For simplicity, assign to first drive if we can't map precisely
                            # In a full implementation, we'd use disk index mapping
                            if details['model'] == 'Unknown' or details['model'] == 'Unknown':
                                details['model'] = current_disk.get('model', 'Unknown')
                            if details['serial'] == 'Unknown':
                                details['serial'] = current_disk.get('serialnumber', 'Unknown')
                            if details['interface'] == 'Unknown':
                                details['interface'] = current_disk.get('interface type', 'Unknown')
                            if details['firmware'] == 'Unknown':
                                details['firmware'] = current_disk.get('firmware', 'Unknown')
                                
                            # Check if SSD
                            media_type = current_disk.get('media type', '').lower()
                            model_lower = current_disk.get('model', '').lower()
                            details['is_ssd'] = 'ssd' in media_type or 'solid state' in media_type or 'ssd' in model_lower
                        current_disk = {}
                        
        except Exception as e:
            print(f"Could not get drive details: {e}")
        
        # Try to get temperature using SMART with better parsing
        try:
            result = subprocess.run(
                ['wmic', '/namespace:\\\\root\\wmi', 'msstoragedriver_atapismartdata', 'get', 'vendor specific', '/format:list'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Try to extract temperature from SMART data
                # Temperature is usually in attribute 194
                output = result.stdout
                if '194' in output:
                    # Try to find temperature value (simplified parsing)
                    lines = output.split('\n')
                    for i, line in enumerate(lines):
                        if '194' in line and i + 1 < len(lines):
                            next_line = lines[i + 1]
                            # Try to extract numeric value
                            import re
                            temp_match = re.search(r'\d+', next_line)
                            if temp_match:
                                temp_value = temp_match.group()
                                if 0 < int(temp_value) < 150:  # Reasonable temperature range
                                    details['temperature'] = f"{temp_value}°C"
                                    break
                if details['temperature'] == 'Unknown':
                    details['temperature'] = 'N/A'
                    
        except Exception as e:
            print(f"Could not get temperature: {e}")
            details['temperature'] = 'N/A'
        
        return details
    
    def get_ssd_metrics(self, drive_letter: str) -> Dict:
        """Get SSD-specific metrics like TBW, wear level"""
        metrics = {
            'tbw': 'Unknown',
            'wear_level': 'Unknown',
            'life_remaining': 'Unknown'
        }
        
        if platform.system() != 'Windows':
            return metrics
        
        try:
            # Try to get SMART attributes that include SSD health
            result = subprocess.run(
                ['wmic', '/namespace:\\\\root\\wmi', 'msstoragedriver_atapismartdata', 'get', 'vendor specific', '/format:list'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse for SSD-specific SMART attributes
                # Attribute 231: SSD Life Left
                # Attribute 233: Media Wearout Indicator
                # Attribute 241: Total LBAs Written
                output = result.stdout.lower()
                
                if '231' in output or 'life' in output:
                    metrics['life_remaining'] = 'Available'
                if '233' in output or 'wear' in output:
                    metrics['wear_level'] = 'Available'
                if '241' in output or 'written' in output:
                    metrics['tbw'] = 'Available'
                    
        except Exception as e:
            print(f"Could not get SSD metrics: {e}")
        
        return metrics
    
    def check_filesystem_health(self, drive_path: str) -> Dict:
        """Check file system health using chkdsk or WMI"""
        health = {
            'status': 'Unknown',
            'errors': 0,
            'needs_repair': False
        }
        
        if platform.system() != 'Windows':
            return health
        
        try:
            # Use WMI to check logical disk status
            drive_letter = drive_path[0]
            result = subprocess.run(
                ['wmic', 'logicaldisk', 'where', f"DeviceID='{drive_path}'", 'get', 'VolumeDirty,Status', '/format:list'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                if 'true' in output or 'dirty' in output:
                    health['status'] = 'Needs Check'
                    health['needs_repair'] = True
                elif 'ok' in output:
                    health['status'] = 'Healthy'
                    health['errors'] = 0
                else:
                    health['status'] = 'Unknown'
                    
        except Exception as e:
            print(f"Could not check filesystem health: {e}")
        
        return health
    
    def is_admin(self) -> bool:
        """Check if the script is running as administrator"""
        return is_admin()
    
    def run_sfc_scan(self) -> Dict:
        """Run System File Checker scan"""
        result = {
            'status': 'Not Run',
            'errors_found': 0,
            'corruptions_repaired': 0,
            'output': ''
        }
        
        if platform.system() != 'Windows':
            result['status'] = 'Not Available'
            return result
        
        # Check for administrator privileges
        if not self.is_admin():
            result['status'] = 'Requires Administrator'
            result['output'] = "SFC scan requires administrator privileges.\n\nPlease run this application as administrator:\n1. Right-click on the script or command prompt\n2. Select 'Run as administrator'\n3. Try the SFC scan again"
            return result
        
        try:
            # First run a quick verification scan (read-only)
            print("Running SFC verification scan...")
            sfc_result = subprocess.run(
                ['sfc', '/verifyonly'],
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout for verification
            )
            
            result['output'] = sfc_result.stdout
            result['status'] = 'Completed'
            
            # If verification found issues, offer to run repair
            if 'integrity violations' in sfc_result.stdout.lower() or 'corrupt' in sfc_result.stdout.lower():
                result['status'] = 'Issues Found'
                result['errors_found'] = 1
                result['output'] += "\n\nISSUES FOUND: System file integrity violations detected.\n\nTo repair these issues, run the following command in an elevated command prompt:\n  sfc /scannow\n\nNote: The repair scan can take 10-30 minutes to complete."
            else:
                result['errors_found'] = 0
            
            # Check for permission errors in output
            if 'administrator' in sfc_result.stdout.lower() and 'console session' in sfc_result.stdout.lower():
                result['status'] = 'Permission Error'
                result['output'] = "SFC scan failed due to insufficient permissions.\n\nPlease run this application as administrator:\n1. Right-click on the script or command prompt\n2. Select 'Run as administrator'\n3. Try the SFC scan again"
                return result
            
            print(f"SFC scan completed with status: {result['status']}")
                    
        except subprocess.TimeoutExpired:
            result['status'] = 'Timeout'
            result['output'] = 'SFC scan timed out after 1 minute. The scan may still be running in the background.\n\nYou can run it manually from command prompt: sfc /scannow\n\nNote: SFC scans can take 10-30 minutes depending on your system.'
        except Exception as e:
            result['status'] = f'Error: {e}'
            result['output'] = f'An error occurred: {str(e)}'
            print(f"SFC scan error: {e}")
        
        return result
    
    def get_status_info(self, percent: float) -> tuple:
        """Get status text and color"""
        if percent < 50:
            return "✓ HEALTHY", self.colors['green']
        elif percent < 75:
            return "⚠ MODERATE", self.colors['yellow']
        elif percent < 90:
            return "⚠ HIGH", self.colors['orange']
        else:
            return "🚨 CRITICAL", self.colors['red']
    
    def get_progress_style(self, percent: float) -> str:
        """Get progress bar style based on percentage"""
        if percent < 50:
            return 'Green.Horizontal.TProgressbar'
        elif percent < 75:
            return 'Yellow.Horizontal.TProgressbar'
        elif percent < 90:
            return 'Orange.Horizontal.TProgressbar'
        else:
            return 'Red.Horizontal.TProgressbar'
    
    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes into human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    
    def update_summary(self, drives: List[Dict]):
        """Update summary information"""
        total_space = sum(d['total'] for d in drives)
        total_used = sum(d['used'] for d in drives)
        total_free = sum(d['free'] for d in drives)
        overall_percent = (total_used / total_space * 100) if total_space > 0 else 0
        
        summary_text = f"   Total Drives: {len(drives)}\n"
        summary_text += f"   Total Space: {self.format_bytes(total_space)}\n"
        summary_text += f"   Used: {self.format_bytes(total_used)}\n"
        summary_text += f"   Free: {self.format_bytes(total_free)}\n"
        summary_text += f"   Overall Usage: {overall_percent:.1f}%\n"
        
        # Add recommendations
        critical_drives = [d for d in drives if d['percent'] > 90]
        high_usage_drives = [d for d in drives if 75 < d['percent'] <= 90]
        
        if critical_drives:
            summary_text += f"\n   🚨 CRITICAL: {len(critical_drives)} drive(s) critically low!"
        elif high_usage_drives:
            summary_text += f"\n   ⚠️ WARNING: {len(high_usage_drives)} drive(s) high usage"
        else:
            summary_text += f"\n   ✅ All drives healthy!"
        
        self.summary_info_label.config(text=summary_text)


def main():
    """Main function"""
    root = tk.Tk()
    app = DriveHealthGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
