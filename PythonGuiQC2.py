import tkinter as tk
from tkinter import messagebox
import subprocess
import os
TRANSPARENT = root["bg"]

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
# Account Settings Sub‑Menu
# -----------------------------------------------------

def open_account_menu():
    acc = tk.Toplevel(root)
    acc.title("Account Settings")
    acc.geometry("400x300")
    acc.config(bg=TRANSPARENT)

    tk.Label(
        acc, text="ACCOUNT SETTINGS",
        fg="cyan", bg=TRANSPARENT,
        font=("Segoe UI", 14, "bold")
    ).pack(pady=15)

    tk.Button(
        acc, text="Manage Users",
        width=35, bg="#333333", fg="white",
        activebackground="#555555",
        command=lambda: (run_cmd("start ms-settings:otherusers"), acc.destroy())
    ).pack(pady=8)

    tk.Button(
        acc, text="Delete User Account",
        width=35, bg="#333333", fg="white",
        activebackground="#555555",
        command=lambda: (run_tool("deleteaccount.bat"), acc.destroy())
    ).pack(pady=8)

    tk.Button(
        acc, text="Create Local Account",
        width=35, bg="#333333", fg="white",
        activebackground="#555555",
        command=lambda: (run_tool("account.bat"), acc.destroy())
    ).pack(pady=8)

    tk.Button(
        acc, text="Back",
        width=35, bg="#444444", fg="white",
        activebackground="#666666",
        command=acc.destroy
    ).pack(pady=15)



# -----------------------------------------------------
# Main Window
# -----------------------------------------------------

root = tk.Tk()
root.title("Diagnostics Test Tool v.66")
root.geometry("750x650")
root.config(bg="#1e1e1e")

# -----------------------------------------------------
# ✅ Fancy Title Banner
# -----------------------------------------------------

title_label = tk.Label(
    root,
    text="✨ DTT — Created By Anthony Witt — 2026 ✨",
    font=("Segoe UI", 18, "bold"),
    fg="cyan",
    bg="#1e1e1e"
)
title_label.pack(pady=10)

# -----------------------------------------------------
# ✅ Safe Background Image Loading (dtt.png)
# -----------------------------------------------------

background_img = None
bg_path = os.path.join(BASE, "dtt.png")

if os.path.exists(bg_path):
    try:
        from PIL import Image, ImageTk
        img = Image.open(bg_path)
        img = img.resize((750, 650))
        background_img = ImageTk.PhotoImage(img)

        bg_label = tk.Label(root, image=background_img)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        title_label.lift()

    except Exception as e:
        print("Background image error:", e)


# -----------------------------------------------------
# ✅ Scrolling Container (No Crashes)
# -----------------------------------------------------

container = tk.Frame(root, bg="#1e1e1e")
container.pack(fill="both", expand=True)

# --- Canvas that will hold background AND content ---
canvas = tk.Canvas(container, highlightthickness=0, bd=0)
canvas.pack(side="left", fill="both", expand=True)

# Expand background image across the whole canvas
if background_img:
    canvas.bg = canvas.create_image(0, 0, image=background_img, anchor="nw")
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas.bg, anchor="nw"))

# --- Frame ON TOP of background ---
scroll_frame = tk.Frame(canvas, bg="#1e1e1e")  # or match bg to image if you want blending
canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

def update_scroll_region(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

scroll_frame.bind("<Configure>", update_scroll_region)

def _on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)

def update_scroll_region(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

scroll_frame.bind("<Configure>", update_scroll_region)

def _on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)


# -----------------------------------------------------
# UI helper functions
# -----------------------------------------------------

def section(title):
    tk.Label(
        scroll_frame,
        text=title,
        fg="cyan",
        bg=TRANSPARENT,
        font=("Segoe UI", 14, "bold")
    ).pack(pady=(20, 5))

def add_button(label, command):
    tk.Button(
        scroll_frame,
        text=label,
        width=45,
        bg=TRANSPARENT,
        fg="white",
        borderwidth=0,
        relief="flat",
        highlightthickness=0,
        activebackground=TRANSPARENT,
        activeforeground="cyan",
        font=("Segoe UI", 11, "bold"),
        command=command
    ).pack(pady=4)
``


# -----------------------------------------------------
# MENU CONTENT
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