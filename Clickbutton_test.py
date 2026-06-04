import sys
import argparse
import tkinter as tk

"""
Minimal Clickbutton_test module.
When launched with `--name <device_name>`, it opens a small window and
listens for Button-1 and Button-3 events on a dedicated canvas. It's
intended to be run separately from the main touchpad tester so it can be
used to isolate physical click-button presses.

This module intentionally ignores touchpad-type clicks by not embedding
it into the main app; it simply provides a focused UI for physical
buttons.
"""

parser = argparse.ArgumentParser()
parser.add_argument('--name', help='Device name hint', default='')
args = parser.parse_args()

root = tk.Tk()
root.title('Clickbutton Test')
root.geometry('420x160')
root.configure(bg='#1e1e2e')

label = tk.Label(root, text=f"Listening for physical click buttons: {args.name}", bg='#1e1e2e', fg='#cdd6f4', font=("Segoe UI", 10))
label.pack(pady=(8,0))

count_frame = tk.Frame(root, bg='#313244')
count_frame.pack(fill='x', padx=12, pady=10)

l_lbl = tk.Label(count_frame, text='Left: 0/10', bg='#313244', fg='#89b4fa', font=("Segoe UI", 12, 'bold'))
l_lbl.pack(side='left', padx=6)
r_lbl = tk.Label(count_frame, text='Right: 0/10', bg='#313244', fg='#89b4fa', font=("Segoe UI", 12, 'bold'))
r_lbl.pack(side='left', padx=6)

c = tk.Canvas(root, bg='#181825', height=60, cursor='hand2')
c.pack(fill='x', padx=12, pady=(0,12))

state = {'lc': 0, 'rc': 0}


def refresh():
    l_lbl.config(text=f"Left: {state['lc']}/10")
    r_lbl.config(text=f"Right: {state['rc']}/10")


def on_l(e):
    if state['lc'] < 10:
        state['lc'] += 1
        refresh()


def on_r(e):
    if state['rc'] < 10:
        state['rc'] += 1
        refresh()


c.bind('<Button-1>', on_l)
c.bind('<Button-3>', on_r)

# Also bind to top-level to catch clicks that may be delivered to the window
root.bind_all('<Button-1>', lambda e: None)
root.bind_all('<Button-3>', lambda e: None)

root.mainloop()
