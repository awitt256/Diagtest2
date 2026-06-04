import tkinter as tk
from tkinter import messagebox
import subprocess
import os
from PIL import Image, ImageTk

BASE = os.path.dirname(os.path.abspath(__file__))

# -----------------------------------------------------
# Helper functions
# -----------------------------------------------------

def run_cmd(command):
    try:
        subprocess.Popen(command, shell=True)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def run_tool(path):
    full = os.path.join(BASE, path)
    if not os.path.exists(full):
        messagebox.showerror("Missing File", f"Cannot find:\n{full}")
        return
    run_cmd(f'"{full}"')


# -----------------------------------------------------
# Main Window
# -----------------------------------------------------

root = tk.Tk()
root.title("Diagnostics Test Tool v.66")
root.geometry("750x650")

# ✅ NOW we can set transparency reference
TRANSPARENT = root["bg"]

# -----------------------------------------------------
# Background Image (Full Window)
# -----------------------------------------------------

bg_path = os.path.join(BASE, "dtt.png")
background_img = None

if os.path.exists(bg_path):
    img = Image.open(bg_path).resize((750, 650))
    background_img = ImageTk.PhotoImage(img)

background_canvas = tk.Canvas(root, width=750, height=650, highlightthickness=0, bd=0)
background_canvas.place(x=0, y=0, relwidth=1, relheight=1)

if background_img:
    background_canvas.create_image(0, 0, image=background_img, anchor="nw")


# -----------------------------------------------------
# Title Banner (Floating)
# -----------------------------------------------------

title_label = tk.Label(
    root,
    text="✨ DTT — Created By Anthony Witt — 2026 ✨",
    font=("Segoe UI", 20, "bold"),
    fg="cyan",
    bg=TRANSPARENT
)
title_label.pack(pady=10)
title_label.lift()


# -----------------------------------------------------
# Scrollable Transparent Layer
# -----------------------------------------------------

container = tk.Frame(root, bg=TRANSPARENT)
container.pack(fill="both", expand=True)

canvas = tk.Canvas(container, bg=TRANSPARENT, highlightthickness=0, bd=0)
canvas.pack(fill="both", expand=True)

scroll_frame = tk.Frame(canvas, bg=TRANSPARENT)
canvas.create_window((0, 0), anchor="nw", window=scroll_frame)

def update_scroll(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

scroll_frame.bind("<Configure>", update_scroll)

def wheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind_all("<MouseWheel>", wheel)


# -----------------------------------------------------
# UI Components
# -----------------------------------------------------

def section(title):
    tk.Label(
        scroll_frame,
        text=title,
        fg="cyan",
        bg=TRANSPARENT,
        font=("Segoe UI", 16, "bold")
    ).pack(pady=(20, 5))

def add_button(text, command):
    tk.Button(
        scroll_frame,
        text=text,
        fg="white",
        bg=TRANSPARENT,
        borderwidth=0,
        relief="flat",
        highlightthickness=0,
        activebackground=TRANSPARENT,
        activeforeground="cyan",
        font=("Segoe UI", 12, "bold"),
        command=command
    ).pack(pady=4)


# -----------------------------------------------------
# Account Settings Menu
# -----------------------------------------------------

def open_account_menu():
    acc = tk.Toplevel(root)
    acc.title("Account Settings")
    acc.geometry("400x300")
    acc.config(bg=TRANSPARENT)

    tk.Label(
        acc, text="ACCOUNT SETTINGS",
        fg="cyan", bg=TRANSPARENT,
        font=("Segoe UI", 16, "bold")
    ).pack(pady=10)

    def tbtn(text, cmd):
        tk.Button(
            acc,
            text=text,
            fg="white",
            bg=TRANSPARENT,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            activebackground=TRANSPARENT,
            activeforeground="cyan",
            font=("Segoe UI", 12, "bold"),
            command=lambda: (cmd(), acc.destroy())
        ).pack(pady=8)

    tbtn("Manage Users", lambda: run_cmd("start ms-settings:otherusers"))
    tbtn("Delete User Account", lambda: run_tool("deleteaccount.bat"))
    tbtn("Create Local Account", lambda: run_tool("account.bat"))

    tk.Button(
        acc,
        text="Back",
        fg="white",
        bg=TRANSPARENT,
        relief="flat",
        borderwidth=0,
        activebackground=TRANSPARENT,
        activeforeground="cyan",
        font=("Segoe UI", 12, "bold"),
        command=acc.destroy
    ).pack(pady=20)


# -----------------------------------------------------
# Main Menu Content
# -----------------------------------------------------

section("SYSTEM / HARDWARE")
add_button("System Info", lambda: run_tool("Tools/sysinfo3.bat"))
add_button("Bitlocker Check", lambda: run_tool("Tools/bitlockercheck1.bat"))
add_button("Hotkeys Test", lambda: run_tool("Tools/hk1.bat"))
add_button("Device Manager", lambda: run_cmd("devmgmt.msc"))
add_button("Battery Test", lambda: run_tool("Apps/bat"))
add_button("Speaker Test", lambda: run_tool("Media/st.mp3"))
add_button("Mic Test", lambda: run_tool("Apps/soundcheck.exe"))
add_button("Camera Test", lambda: run_cmd("start microsoft.windows.camera:"))
add_button("Windows Activation", lambda: run_tool("Tools/ACT.bat"))
add_button("Keyboard Test", lambda: run_tool("Tools/Kbtest.bat"))

section("SYSTEM DIAGNOSTICS & HEALTH")
add_button("System File Checker", lambda: run_cmd("sfc /scannow"))
add_button("SMART Drive Health", lambda: run_cmd('powershell "Get-CimInstance Win32_DiskDrive | ft Model,SerialNumber,Status"'))
add_button("Memory Diagnostic", lambda: run_cmd("mdsched.exe"))
add_button("Disk Cleanup", lambda: run_cmd("cleanmgr"))

section("ADVANCED HARDWARE TESTING")
add_button("Stress Test Suite", lambda: run_tool("Tools/stresstestmenu.bat"))
add_button("Performance Tests", lambda: run_tool("Tools/Install-PerfTest-WithWinget.bat"))
add_button("USB Port Test", lambda: run_tool("Apps/USBTreeView.exe"))
add_button("SSD Test", lambda: run_tool("Apps/CrystalDiskInfo.exe"))

section("NETWORK")
add_button("Network Settings", lambda: run_cmd("start ms-settings:network"))
add_button("WiFi Info", lambda: run_cmd("netsh wlan show interfaces"))

section("ACCOUNT / USER SETTINGS")
add_button("Account Settings", open_account_menu)

section("UTILITIES / POWER")
add_button("Clear Temp Files", lambda: run_cmd('powershell "Remove-Item $env:TEMP\\* -Recurse -Force"'))
add_button("Restart PC", lambda: run_cmd("shutdown /r /t 0"))
add_button("Shutdown PC", lambda: run_cmd("shutdown /s /t 0"))
add_button("Exit Program", root.quit)

root.mainloop()