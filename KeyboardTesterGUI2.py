import tkinter as tk


COMPACT_LAYOUT = [
    [
        ("Esc", "Escape", 1.0),
        ("F1", "F1", 1.0), ("F2", "F2", 1.0), ("F3", "F3", 1.0), ("F4", "F4", 1.0),
        ("F5", "F5", 1.0), ("F6", "F6", 1.0), ("F7", "F7", 1.0), ("F8", "F8", 1.0),
        ("F9", "F9", 1.0), ("F10", "F10", 1.0), ("F11", "F11", 1.0), ("F12", "F12", 1.0),
    ],
    [
        ("`", "grave", 1.0), ("1", "1", 1.0), ("2", "2", 1.0), ("3", "3", 1.0), ("4", "4", 1.0),
        ("5", "5", 1.0), ("6", "6", 1.0), ("7", "7", 1.0), ("8", "8", 1.0), ("9", "9", 1.0),
        ("0", "0", 1.0), ("-", "minus", 1.0), ("=", "equal", 1.0), ("Backspace", "BackSpace", 2.1),
    ],
    [
        ("Tab", "Tab", 1.5), ("Q", "q", 1.0), ("W", "w", 1.0), ("E", "e", 1.0), ("R", "r", 1.0),
        ("T", "t", 1.0), ("Y", "y", 1.0), ("U", "u", 1.0), ("I", "i", 1.0), ("O", "o", 1.0),
        ("P", "p", 1.0), ("[", "bracketleft", 1.0), ("]", "bracketright", 1.0), ("\\", "backslash", 1.6),
    ],
    [
        ("Caps", "Caps_Lock", 1.8), ("A", "a", 1.0), ("S", "s", 1.0), ("D", "d", 1.0), ("F", "f", 1.0),
        ("G", "g", 1.0), ("H", "h", 1.0), ("J", "j", 1.0), ("K", "k", 1.0), ("L", "l", 1.0),
        (";", "semicolon", 1.0), ("'", "apostrophe", 1.0), ("Enter", "Return", 2.3),
    ],
    [
        ("Shift", "Shift_L", 2.3), ("Z", "z", 1.0), ("X", "x", 1.0), ("C", "c", 1.0), ("V", "v", 1.0),
        ("B", "b", 1.0), ("N", "n", 1.0), ("M", "m", 1.0), (",", "comma", 1.0), (".", "period", 1.0),
        ("/", "slash", 1.0), ("Shift", "Shift_R", 2.7),
    ],
    [
        ("Ctrl", "Control_L", 1.3), ("Win", "Super_L", 1.2), ("Alt", "Alt_L", 1.2),
        ("Space", "space", 6.6),
        ("Alt", "Alt_R", 1.2), ("Fn", "fn", 1.2), ("Menu", "Menu", 1.2), ("Ctrl", "Control_R", 1.3),
    ],
    [
        ("Ins", "Insert", 1.0), ("Home", "Home", 1.0), ("PgUp", "Prior", 1.0),
        ("Del", "Delete", 1.0), ("End", "End", 1.0), ("PgDn", "Next", 1.0),
        ("Up", "Up", 1.0),
    ],
    [
        ("Left", "Left", 1.0), ("Down", "Down", 1.0), ("Right", "Right", 1.0),
    ],
]

NUMPAD_LAYOUT = [
    [("Num", "Num_Lock", 1.0), ("/", "KP_Divide", 1.0), ("*", "KP_Multiply", 1.0), ("-", "KP_Subtract", 1.0)],
    [("7", "KP_7", 1.0), ("8", "KP_8", 1.0), ("9", "KP_9", 1.0), ("+", "KP_Add", 1.0, 2)],
    [("4", "KP_4", 1.0), ("5", "KP_5", 1.0), ("6", "KP_6", 1.0)],
    [("1", "KP_1", 1.0), ("2", "KP_2", 1.0), ("3", "KP_3", 1.0), ("Enter", "KP_Enter", 1.0, 2)],
    [("0", "KP_0", 2.0), (".", "KP_Decimal", 1.0)],
]

KEY_ALIASES = {
    "Escape": "Escape",
    "BackSpace": "BackSpace",
    "Return": "Return",
    "space": "space",
    "grave": "grave",
    "minus": "minus",
    "equal": "equal",
    "bracketleft": "bracketleft",
    "bracketright": "bracketright",
    "backslash": "backslash",
    "semicolon": "semicolon",
    "apostrophe": "apostrophe",
    "comma": "comma",
    "period": "period",
    "slash": "slash",
}


class KeyboardTesterApp:
    def __init__(self, root):
        self.root = root
        # Only set window properties if root is a Tk or Toplevel
        if isinstance(self.root, (tk.Tk, tk.Toplevel)):
            self.root.title("Keyboard Tester")
            self.root.geometry("1380x760")
            self.root.minsize(1120, 660)
        self.root.configure(bg="#101723")

        self.key_states = {}
        self.key_buttons = {}
        self.layout_mode = tk.StringVar(value="full")
        self.key_log_var = tk.StringVar(value="Key log: ")

        self.default_bg = "#e6edf5"
        self.default_fg = "#132033"
        self.green_bg = "#43c46b"
        self.orange_bg = "#f0a54a"

        self._build_ui()
        self._render_keyboard()
        self.root.bind("<KeyPress>", self._handle_physical_keypress)
        self._menu_callback = None
        try:
            self.root.focus_force()
        except Exception:
            pass

    def set_menu_callback(self, callback):
        self._menu_callback = callback

    def _build_ui(self):
        outer = tk.Frame(self.root, bg="#101723")
        outer.pack(fill="both", expand=True, padx=18, pady=18)

        header = tk.Frame(outer, bg="#101723")
        header.pack(fill="x", pady=(0, 14))

        tk.Label(
            header,
            text="Keyboard Tester",
            font=("Segoe UI", 22, "bold"),
            bg="#101723",
            fg="#f8fafc",
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Toggle between compact and full layouts. Click keys or press your real keyboard to test.",
            font=("Segoe UI", 11),
            bg="#101723",
            fg="#9db2ce",
        ).pack(anchor="w", pady=(4, 0))

        controls = tk.Frame(outer, bg="#101723")
        controls.pack(fill="x", expand=True, pady=(0, 16))

        toggle_box = tk.Frame(controls, bg="#182437", bd=0, highlightthickness=0)
        toggle_box.pack(side="left", padx=(0, 20))

        tk.Label(
            toggle_box,
            text="Layout",
            font=("Segoe UI", 11, "bold"),
            bg="#182437",
            fg="#f8fafc",
            padx=10,
            pady=10,
        ).pack(side="left")

        switch_frame = tk.Frame(toggle_box, bg="#182437")
        switch_frame.pack(side="left", padx=(0, 6))

        tk.Label(
            switch_frame,
            text="Compact KB",
            font=("Segoe UI", 10, "bold"),
            bg="#182437",
            fg="#f8fafc",
        ).pack(side="left", padx=(0, 8))

        self.layout_switch = tk.Canvas(
            switch_frame,
            width=68,
            height=30,
            bg="#182437",
            highlightthickness=0,
            bd=0,
        )
        self.layout_switch.pack(side="left")
        self.layout_switch.bind("<Button-1>", self._toggle_layout_mode)

        tk.Label(
            switch_frame,
            text="Full KB",
            font=("Segoe UI", 10, "bold"),
            bg="#182437",
            fg="#f8fafc",
        ).pack(side="left", padx=(8, 0))

        self._update_layout_switch()

        # Menu button (returns to menu if callback is set)
        def menu_action():
            if self._menu_callback:
                self._menu_callback()
            else:
                # If running standalone, close the window
                try:
                    self.root.destroy()
                except Exception:
                    pass
        tk.Button(
            controls,
            text="Menu",
            command=menu_action,
            bg="#38bdf8",
            fg="#0f172a",
            activebackground="#0ea5e9",
            activeforeground="#0f172a",
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=8,
            bd=0,
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            controls,
            text="Reset Colors",
            command=self._reset_keys,
            bg="#fbbf24",
            fg="#0f172a",
            activebackground="#f59e0b",
            activeforeground="#0f172a",
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=8,
            bd=0,
        ).pack(side="right", padx=(8, 0))
        def exit_action():
            if self._menu_callback:
                self._menu_callback()
            else:
                try:
                    self.root.destroy()
                except Exception:
                    pass
        tk.Button(
            controls,
            text="Exit",
            command=exit_action,
            bg="#ef4444",
            fg="#ffffff",
            activebackground="#dc2626",
            activeforeground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=8,
            bd=0,
        ).pack(side="right")

        self.keyboard_wrap = tk.Frame(outer, bg="#101723")
        self.keyboard_wrap.pack(fill="both", expand=True)

        self.keyboard_frame = tk.Frame(self.keyboard_wrap, bg="#101723")
        self.keyboard_frame.pack(anchor="n", pady=(0, 18))

        footer = tk.Frame(outer, bg="#182437", padx=18, pady=14)
        footer.pack(fill="x")

        tk.Label(
            footer,
            textvariable=self.key_log_var,
            font=("Segoe UI", 14, "bold"),
            bg="#182437",
            fg="#f8fafc",
            anchor="w",
            justify="left",
            wraplength=1240,
        ).pack(fill="x")

    def _render_keyboard(self):
        for child in self.keyboard_frame.winfo_children():
            child.destroy()

        self.key_buttons.clear()
        compact_frame = tk.Frame(self.keyboard_frame, bg="#101723")
        compact_frame.grid(row=0, column=0, sticky="nw")
        self._build_layout(compact_frame, COMPACT_LAYOUT)

        if self.layout_mode.get() == "full":
            numpad_frame = tk.Frame(self.keyboard_frame, bg="#101723")
            numpad_frame.grid(row=0, column=1, sticky="ne", padx=(22, 0))
            self._build_layout(numpad_frame, NUMPAD_LAYOUT)

    def _toggle_layout_mode(self, event=None):
        if self.layout_mode.get() == "full":
            self.layout_mode.set("compact")
        else:
            self.layout_mode.set("full")
        self._update_layout_switch()
        self._render_keyboard()

    def _update_layout_switch(self):
        self.layout_switch.delete("all")
        if self.layout_mode.get() == "full":
            track_color = "#2563eb"
            knob_left = 38
        else:
            track_color = "#334155"
            knob_left = 4

        # Draw a rounded rectangle for the track (simulate with two circles and a rectangle)
        self.layout_switch.create_oval(4, 4, 28, 28, fill=track_color, outline=track_color)  # left end
        self.layout_switch.create_oval(40, 4, 64, 28, fill=track_color, outline=track_color)  # right end
        self.layout_switch.create_rectangle(16, 4, 52, 28, fill=track_color, outline=track_color)  # center

        # Draw the knob as a fully rounded circle
        self.layout_switch.create_oval(knob_left, 4, knob_left + 24, 28, fill="#f8fafc", outline="#cbd5e1")

    def _build_layout(self, parent, layout):
        for row_index, row in enumerate(layout):
            row_frame = tk.Frame(parent, bg="#101723")
            row_frame.grid(row=row_index, column=0, sticky="w", pady=4)

            for key_def in row:
                label = key_def[0]
                key_id = key_def[1]
                width_units = key_def[2]
                row_span = key_def[3] if len(key_def) > 3 else 1

                button = tk.Button(
                    row_frame,
                    text=label,
                    width=max(4, int(width_units * 5)),
                    height=max(2, row_span * 2),
                    bg=self._color_for_state(self.key_states.get(key_id, 0)),
                    fg=self.default_fg,
                    activebackground=self._color_for_state(self.key_states.get(key_id, 0)),
                    activeforeground=self.default_fg,
                    font=("Segoe UI", 10, "bold"),
                    bd=0,
                    relief="flat",
                    command=lambda current_key=key_id, current_label=label: self._register_key(current_key, current_label),
                )
                button.pack(side="left", padx=3, pady=1)
                self.key_buttons[key_id] = button

    def _color_for_state(self, state):
        if state == 1:
            return self.green_bg
        if state == 2:
            return self.orange_bg
        return self.default_bg

    def _register_key(self, key_id, key_label):
        current_state = self.key_states.get(key_id, 0)
        # Cycle: 0 (default) -> 1 (green) -> 2 (orange) -> 1 (green) -> 2 (orange) ...
        if current_state == 0:
            next_state = 1
        elif current_state == 1:
            next_state = 2
        elif current_state == 2:
            next_state = 1
        else:
            next_state = 1
        self.key_states[key_id] = next_state
        current_log = self.key_log_var.get().replace("Key log: ", "", 1).strip()
        updated_log = f"{current_log} {key_label}".strip() if current_log else key_label
        self.key_log_var.set(f"Key log: {updated_log}")

        button = self.key_buttons.get(key_id)
        if button:
            new_color = self._color_for_state(next_state)
            button.configure(bg=new_color, activebackground=new_color)

    def _handle_physical_keypress(self, event):
        key_id = event.keysym
        key_label = event.keysym

        if key_id in self.key_buttons:
            self._register_key(key_id, key_label)
            return

        alias_key = KEY_ALIASES.get(key_id)
        if alias_key and alias_key in self.key_buttons:
            self._register_key(alias_key, key_label)
            return

        lower_key = key_id.lower()
        if lower_key in self.key_buttons:
            self._register_key(lower_key, key_label)

    def _reset_keys(self):
        self.key_states = {}
        self.key_log_var.set("Key log: ")
        for key_id, button in self.key_buttons.items():
            button.configure(bg=self.default_bg, activebackground=self.default_bg)


def main():
    root = tk.Tk()
    KeyboardTesterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
