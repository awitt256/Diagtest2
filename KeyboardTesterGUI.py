import tkinter as tk

# ============================================================
# Layouts
# ============================================================

COMPACT_LAYOUT = [
    [("Esc", "Escape", 1.0), ("F1", "F1", 1.0), ("F2", "F2", 1.0), ("F3", "F3", 1.0),
     ("F4", "F4", 1.0), ("F5", "F5", 1.0), ("F6", "F6", 1.0),
     ("F7", "F7", 1.0), ("F8", "F8", 1.0), ("F9", "F9", 1.0),
     ("F10", "F10", 1.0), ("F11", "F11", 1.0), ("F12", "F12", 1.0)],

    [("`", "grave", 1.0), ("1", "1", 1.0), ("2", "2", 1.0), ("3", "3", 1.0),
     ("4", "4", 1.0), ("5", "5", 1.0), ("6", "6", 1.0),
     ("7", "7", 1.0), ("8", "8", 1.0), ("9", "9", 1.0),
     ("0", "0", 1.0), ("-", "minus", 1.0), ("=", "equal", 1.0),
     ("Backspace", "BackSpace", 2.1)],

    [("Tab", "Tab", 1.5), ("Q", "q", 1.0), ("W", "w", 1.0), ("E", "e", 1.0),
     ("R", "r", 1.0), ("T", "t", 1.0), ("Y", "y", 1.0),
     ("U", "u", 1.0), ("I", "i", 1.0), ("O", "o", 1.0),
     ("P", "p", 1.0), ("[", "bracketleft", 1.0),
     ("]", "bracketright", 1.0), ("\\", "backslash", 1.6)],

    [("Caps", "Caps_Lock", 1.8), ("A", "a", 1.0), ("S", "s", 1.0),
     ("D", "d", 1.0), ("F", "f", 1.0), ("G", "g", 1.0),
     ("H", "h", 1.0), ("J", "j", 1.0), ("K", "k", 1.0),
     ("L", "l", 1.0), (";", "semicolon", 1.0),
     ("'", "apostrophe", 1.0), ("Enter", "Return", 2.3)],

    [("Shift", "Shift_L", 2.3), ("Z", "z", 1.0), ("X", "x", 1.0),
     ("C", "c", 1.0), ("V", "v", 1.0), ("B", "b", 1.0),
     ("N", "n", 1.0), ("M", "m", 1.0),
     (",", "comma", 1.0), (".", "period", 1.0),
     ("/", "slash", 1.0), ("Shift", "Shift_R", 2.7)],

    [("Ctrl", "Control_L", 1.3), ("Win", "Super_L", 1.2),
     ("Alt", "Alt_L", 1.2), ("Space", "space", 6.6),
     ("Alt", "Alt_R", 1.2), ("Fn", "fn", 1.2),
     ("Menu", "Menu", 1.2), ("Ctrl", "Control_R", 1.3)],
]

KEY_ALIASES = {
    "Return": "Return",
    "BackSpace": "BackSpace",
    "space": "space",
    "Escape": "Escape",
}


# ============================================================
# Keyboard Tester App
# ============================================================

class KeyboardTesterApp:
    def __init__(self, parent):
        self.root = parent
        self.root.configure(bg="#101723")

        self.key_states = {}
        self.key_buttons = {}
        self.key_log_var = tk.StringVar(value="Key log:")

        self.default_bg = "#e6edf5"
        self.green_bg = "#43c46b"
        self.orange_bg = "#f0a54a"

        self._build_ui()
        self._render_keyboard()

        # ✅ KEY FIXES
        self.root.bind_all("<KeyPress>", self._handle_key)
        self.root.focus_set()
        self.root.focus_force()

    # --------------------------------------------------------

    def _build_ui(self):
        header = tk.Label(
            self.root,
            text="Keyboard Tester (Press F3 to return)",
            font=("Segoe UI", 18, "bold"),
            bg="#101723",
            fg="white"
        )
        header.pack(pady=10)

        self.keyboard_frame = tk.Frame(self.root, bg="#101723")
        self.keyboard_frame.pack(pady=10)

        self.footer = tk.Label(
            self.root,
            textvariable=self.key_log_var,
            bg="#182437",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
            padx=15
        )
        self.footer.pack(fill="x", side="bottom", ipady=10)

    # --------------------------------------------------------

    def _render_keyboard(self):
        for w in self.keyboard_frame.winfo_children():
            w.destroy()

        for r, row in enumerate(COMPACT_LAYOUT):
            row_frame = tk.Frame(self.keyboard_frame, bg="#101723")
            row_frame.grid(row=r, column=0, pady=3)

            for label, key_id, width in row:
                btn = tk.Button(
                    row_frame,
                    text=label,
                    width=max(4, int(width * 5)),
                    height=2,
                    bg=self.default_bg,
                    relief="flat",
                    command=lambda k=key_id, l=label: self._register_key(k, l)
                )
                btn.pack(side="left", padx=3)
                self.key_buttons[key_id] = btn

    # --------------------------------------------------------

    def _register_key(self, key_id, label):
        state = self.key_states.get(key_id, 0) + 1
        if state > 2:
            state = 1
        self.key_states[key_id] = state

        color = self.green_bg if state == 1 else self.orange_bg
        btn = self.key_buttons.get(key_id)
        if btn:
            btn.configure(bg=color)

        current = self.key_log_var.get().replace("Key log:", "").strip()
        updated = f"{current} {label}".strip()
        self.key_log_var.set(f"Key log: {updated}")

    # --------------------------------------------------------

    def _handle_key(self, event):
        key = event.keysym
        if key in self.key_buttons:
            self._register_key(key, key)
        elif key in KEY_ALIASES:
            alias = KEY_ALIASES[key]
            if alias in self.key_buttons:
                self._register_key(alias, key)


# ============================================================
# Embedded wrapper for PG16
# ============================================================

class KeyboardTesterFrame(tk.Frame):
    def __init__(self, parent, on_exit_callback):
        super().__init__(parent, bg="#101723")
        self.pack(fill="both", expand=True)

        self.on_exit_callback = on_exit_callback
        KeyboardTesterApp(self)

        self.bind_all("<F3>", lambda e=None: self.on_exit_callback())


# ============================================================
# Standalone execution
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Keyboard Tester")
    root.geometry("1380x760")
    KeyboardTesterApp(root)
    root.mainloop()