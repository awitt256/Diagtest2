"""
Keyboard GUI tester
- Full-size ANSI layout with numeric keypad
- Clicking a key or pressing the corresponding physical key starts/stops a color loop
- Numpad keys are treated separately from the regular number row

Run: python keyboard_gui.py
"""

import tkinter as tk
from tkinter import ttk

# Colors to cycle through
COLORS = ["#2ecc71", "#ff9900"]  # green, orange
CYCLE_INTERVAL_MS = 500


class CycleKey:
    def __init__(self, master, key_id, label, width=6, height=None):
        self.key_id = key_id
        self.label = label
        # start at -1 so first press -> index 0 (green), second -> index 1 (orange), etc.
        self.color_index = -1

        # Style keys as white caps with black outline/text
        btn_opts = dict(text=label, width=width, bd=0, relief="flat",
                        bg="#ffffff", fg="#000000",
                        activebackground="#e6e6e6", activeforeground="#000000",
                        highlightthickness=2, highlightbackground="#000000", highlightcolor="#000000",
                        font=("Helvetica", 10, "bold"))
        # Prevent buttons from taking focus so Tab doesn't traverse widgets
        btn_opts['takefocus'] = 0
        if height is not None:
            btn_opts['height'] = height
        self.btn = tk.Button(master, **btn_opts)
        self.btn.bind("<Button-1>", self._on_click)

    def grid(self, **kwargs):
        self.btn.grid(**kwargs)

    def _on_click(self, event=None):
        self.press()

    def press(self):
        """Advance color state on each press: 1->green, 2->orange, 3->green, ..."""
        try:
            self.color_index += 1
            c = COLORS[self.color_index % len(COLORS)]
            self.set_color(c)
        except Exception:
            pass

    def toggle(self):
        # kept for compatibility; behaves like a press
        self.press()

    def set_color(self, bg_hex, fg=None):
        """Set the key background and text color."""
        if fg is None:
            try:
                h = bg_hex.lstrip('#')
                r = int(h[0:2], 16)
                g = int(h[2:4], 16)
                b = int(h[4:6], 16)
                lum = 0.2126*r + 0.7152*g + 0.0722*b
                fg = '#ffffff' if lum < 128 else '#000000'
            except Exception:
                fg = '#000000'
        try:
            self.btn.configure(bg=bg_hex, fg=fg)
        except Exception:
            pass


class KeyboardGUI:
    def __init__(self, root):
        # container where widgets are created (Frame or Tk)
        self.root = root
        try:
            # top-level window (Tk) used for global bindings and title
            self._toplevel = root if isinstance(root, tk.Tk) else root.winfo_toplevel()
        except Exception:
            self._toplevel = root

        # Set window title only when running as a standalone, plain tkinter.Tk
        # (avoid changing title when embedded inside customtkinter.CTk or other wrappers)
        try:
            if type(self._toplevel) is tk.Tk:
                self._toplevel.title("Keyboard Visualizer")
        except Exception:
            pass

        # Use navy background on the container
        try:
            root.configure(bg="#001f3f")
        except Exception:
            pass

        # Controls row at top: toggle Full/Compact and Reset button
        self.controls_frame = tk.Frame(root, bg="#001f3f")
        self.controls_frame.pack(fill="x", padx=8, pady=(6,2))
        self.full_var = tk.BooleanVar(value=True)
        # Layout label + custom toggle (Compact KB / Full KB)
        self.layout_label = tk.Label(self.controls_frame, text="Layout", bg="#0b0b0b", fg="#ffffff")
        self.layout_label.pack(side="left", padx=(2,8))
        # left text, switch, right text
        self.compact_label = tk.Label(self.controls_frame, text="Compact KB", bg="#0b0b0b", fg="#888888")
        self.compact_label.pack(side="left")
        self.toggle_canvas = tk.Canvas(self.controls_frame, width=66, height=28, bg="#001f3f", highlightthickness=0)
        self.toggle_canvas.pack(side="left", padx=6)
        self.full_label = tk.Label(self.controls_frame, text="Full KB", bg="#0b0b0b", fg="#ffffff")
        self.full_label.pack(side="left", padx=(6,2))
        self.toggle_canvas.bind("<Button-1>", lambda e: self._toggle_switch())
        self._draw_toggle()
        self.reset_btn = tk.Button(self.controls_frame, text="Reset Colors", command=self.reset_colors,
                   bg="#ff9900", fg="#000000", activebackground="#ffb84d", takefocus=0)
        self.reset_btn.pack(side="right")

        # On-screen debug label to show last event keysym/char and mapping status
        self.debug_label = tk.Label(self.controls_frame, text="", bg="#001f3f", fg="#ffffff")
        self.debug_label.pack(side="left", padx=(8,2))

        # Main keyboard host uses navy background
        self.frame = tk.Frame(root, bg="#001f3f")
        self.frame.pack(fill="both", expand=True, padx=8, pady=8)

        # dictionary of key_id -> CycleKey
        self.keys = {}

        self._build_layout()

        # bind physical keypresses on the application toplevel so embedding works
        bind_root = getattr(self, '_toplevel', root)
        try:
            bind_root.bind_all("<KeyPress>", self._on_keypress)
            bind_root.bind_all("<KeyRelease>", self._on_keyrelease)
        except Exception:
            try:
                root.bind_all("<KeyPress>", self._on_keypress)
                root.bind_all("<KeyRelease>", self._on_keyrelease)
            except Exception:
                pass
        # Ensure toplevel has focus so key events are delivered
        try:
            bind_root.focus_set()
            bind_root.focus_force()
            # create a custom bindtag 'kbd' and place it first so our Tab handler runs before default focus traversal
            try:
                current = bind_root.bindtags()
                if 'kbd' not in current:
                    bind_root.bindtags(('kbd',) + current)
                bind_root.bind_class('kbd', '<Tab>', self._handle_tab)
                bind_root.bind_class('kbd', '<ISO_Left_Tab>', self._handle_tab)
                bind_root.bind_class('kbd', '<Key-Tab>', self._handle_tab)
            except Exception:
                pass
        except Exception:
            pass

        # Also bind function keys explicitly to ensure F10/F11/F12 are captured
        for i in range(1, 13):
            try:
                bind_root.bind_all(f"<F{i}>", lambda e, k=f"F{i}": self._press_by_id(k))
            except Exception:
                pass
        # bind left/right Alt explicitly to ensure they register
        try:
            bind_root.bind_all('<Alt_L>', lambda e: self._press_by_id('Alt'))
        except Exception:
            pass
        try:
            bind_root.bind_all('<Alt_R>', lambda e: self._press_by_id('AltGr'))
        except Exception:
            pass
        # Explicit Tab handlers — bind several Tab variants to ensure we capture Tab
        try:
            bind_root.bind_all('<Tab>', self._handle_tab)
        except Exception:
            pass
        try:
            bind_root.bind_all('<Key-Tab>', self._handle_tab)
        except Exception:
            pass
        try:
            bind_root.bind_all('<ISO_Left_Tab>', self._handle_tab)
        except Exception:
            pass

    def _press_by_id(self, key_id):
        try:
            key = self.keys.get(key_id)
            found = key is not None
            # update debug (no event available here; show key_id)
            try:
                self._set_debug(key_id, '', None, key_id, found)
            except Exception:
                pass
            if key:
                key.press()
        except Exception:
            pass

    def _handle_tab(self, event):
        """Dedicated Tab handler: show debug, press Tab key, and stop focus traversal."""
        try:
            ks = getattr(event, 'keysym', None)
            ch = getattr(event, 'char', '')
            kc = getattr(event, 'keycode', None)
            key_id = 'Tab'
            key = self.keys.get(key_id)
            found = key is not None
            try:
                self._set_debug(ks, ch, kc, key_id, found)
                # also print to console for extra visibility when testing
                print(f"DEBUG: keysym={ks} keycode={kc} char={ch!r} -> id={key_id} {'FOUND' if found else 'MISSING'}")
            except Exception:
                pass
            if key:
                key.press()
        except Exception:
            pass
        return 'break'

    def _set_debug(self, keysym, char, keycode, key_id, found):
        # Show keysym, keycode and char and whether we found a matching key widget
        try:
            txt = f"keysym={keysym}  keycode={keycode}  char={char!r}  -> id={key_id}  {'FOUND' if found else 'MISSING'}"
            color = "#00ff66" if found else "#ff4444"
            self.debug_label.config(text=txt, fg=color)
        except Exception:
            pass

    def _add_key(self, container, key_id, label, **grid_opts):
        width = grid_opts.pop("w", 6)
        height = grid_opts.pop("h", None)
        key = CycleKey(container, key_id, label, width=width, height=height)
        key.grid(**grid_opts)
        self.keys[key_id] = key
        return key

    def _build_layout(self):
        # Use a grid of frames for keyboard rows
        r = 0
        # Function row (F1..F12) - simplified sizes
        fn_frame = tk.Frame(self.frame, bg="#001f3f")
        fn_frame.grid(row=r, column=0, sticky="w")
        f_keys = [f"F{i}" for i in range(1, 13)]
        # Esc key to the left of F1, above the ` key
        self._add_key(fn_frame, 'Esc', 'Esc', row=0, column=0, padx=2, pady=2, w=6)
        for i, k in enumerate(f_keys):
            # shift F1..F12 to start at column 1
            self._add_key(fn_frame, k, k, row=0, column=i+1, padx=2, pady=2)
        r += 1

        # Number row (with regular numbers) - note that numpad is separate
        row_frame = tk.Frame(self.frame, bg="#001f3f")
        row_frame.grid(row=r, column=0, sticky="w", pady=(6,0))
        numrow = ['`', '1','2','3','4','5','6','7','8','9','0','-','=','Backspace']
        for i, k in enumerate(numrow):
            keyid = k if k != 'Backspace' else 'Backspace'
            w = 6 if k != 'Backspace' else 10
            self._add_key(row_frame, keyid, k, row=0, column=i, padx=2, pady=2, w=w)
        r += 1

        # QWERTY rows
        q_row = ['Tab','Q','W','E','R','T','Y','U','I','O','P','[',']','\\']
        q_frame = tk.Frame(self.frame, bg="#001f3f")
        q_frame.grid(row=r, column=0, sticky="w", pady=(6,0))
        for i, k in enumerate(q_row):
            w = 8 if k=='Tab' else 6
            self._add_key(q_frame, k, k, row=0, column=i, padx=2, pady=2, w=w)
        r += 1

        a_row = ['Caps','A','S','D','F','G','H','J','K','L',';','\'', 'Enter']
        a_frame = tk.Frame(self.frame, bg="#001f3f")
        a_frame.grid(row=r, column=0, sticky="w", pady=(6,0))
        for i, k in enumerate(a_row):
            w = 9 if k in ('Caps','Enter') else 6
            self._add_key(a_frame, k, k, row=0, column=i, padx=2, pady=2, w=w)
        r += 1

        s_row = ['Shift','Z','X','C','V','B','N','M',',','.','/','ShiftR']
        s_frame = tk.Frame(self.frame, bg="#001f3f")
        s_frame.grid(row=r, column=0, sticky="w", pady=(6,0))
        for i, k in enumerate(s_row):
            w = 12 if k in ('Shift','ShiftR') else 6
            # display same label for left/right shifts
            display = 'Shift' if k in ('Shift','ShiftR') else k
            self._add_key(s_frame, k, display, row=0, column=i, padx=2, pady=2, w=w)
        r += 1

        # Bottom row: Ctrl, Win, Alt, Space, AltGr, Menu, Ctrl
        b_frame = tk.Frame(self.frame, bg="#001f3f")
        b_frame.grid(row=r, column=0, sticky="w", pady=(8,0))
        bottom_keys = ['Ctrl','Win','Alt','Space','AltGr','Menu','CtrlR']
        widths = [6,6,6,50,6,6,6]
        for i, k in enumerate(bottom_keys):
            # unify display for left/right modifiers
            if k in ('Ctrl','CtrlR'):
                display = 'Ctrl'
            elif k in ('Alt','AltGr'):
                display = 'Alt'
            else:
                display = k
            self._add_key(b_frame, k, display, row=0, column=i, padx=2, pady=2, w=widths[i])

        # Top-right cluster above the middle cluster: PrtSc / Scroll Lock / Pause Break
        top_right_frame = tk.Frame(self.frame, bg="#001f3f")
        top_right_frame.grid(row=0, column=1, sticky="n", padx=(12,6), pady=(6,0))
        # match size of middle-cluster keys below (w=6)
        # force same height as middle-cluster keys by specifying height
        self._add_key(top_right_frame, 'PrtSc', 'PrtSc', row=0, column=0, padx=2, pady=2, w=6, h=2)
        self._add_key(top_right_frame, 'ScrollLock', 'Scroll\nLock', row=0, column=1, padx=2, pady=2, w=6, h=2)
        self._add_key(top_right_frame, 'PauseBreak', 'Pause\nBreak', row=0, column=2, padx=2, pady=2, w=6, h=2)

        # Middle cluster (Insert/Home/PgUp over Delete/End/PgDn)
        mid_frame = tk.Frame(self.frame, bg="#001f3f")
        mid_frame.grid(row=1, column=1, rowspan=5, sticky="n", padx=(12,6))

        # Numpad on the right (separate from numbers)
        num_frame = tk.Frame(self.frame, bg="#001f3f")
        # shift numpad one column to the right to make room for middle cluster
        num_frame.grid(row=1, column=2, rowspan=5, sticky="ne", padx=(12,0))
        # keep a reference so we can hide/show the numpad for compact mode
        self.num_frame = num_frame
        # allow numpad rows/columns to expand so tall keys (rowspan) fill vertically
        for ri in range(6):
            num_frame.grid_rowconfigure(ri, weight=1)
        for ci in range(4):
            num_frame.grid_columnconfigure(ci, weight=1)

        # Numpad layout with a single vertical '+' and a single vertical Enter key
        # Row 0 of numpad
        self._add_key(num_frame, 'NumLock', 'Num', row=0, column=0, padx=2, pady=2, w=6)
        self._add_key(num_frame, 'KP_Divide', '/', row=0, column=1, padx=2, pady=2, w=6)
        self._add_key(num_frame, 'KP_Multiply', '*', row=0, column=2, padx=2, pady=2, w=6)
        self._add_key(num_frame, 'KP_Subtract', '-', row=0, column=3, padx=2, pady=2, w=6)

        # Row 1
        self._add_key(num_frame, 'KP_7', '7', row=1, column=0, padx=2, pady=2, w=6)
        self._add_key(num_frame, 'KP_8', '8', row=1, column=1, padx=2, pady=2, w=6)
        self._add_key(num_frame, 'KP_9', '9', row=1, column=2, padx=2, pady=2, w=6)
        # '+' spans rows 1-2 (vertical) to match combined height of '9' and '6'
        # make '+' vertical: span two rows and request a taller height
        self._add_key(num_frame, 'KP_Add', '+', row=1, column=3, rowspan=2, padx=2, pady=2, w=6, h=3, sticky='ns')

        # Row 2
        self._add_key(num_frame, 'KP_4', '4', row=2, column=0, padx=2, pady=2, w=6)
        self._add_key(num_frame, 'KP_5', '5', row=2, column=1, padx=2, pady=2, w=6)
        self._add_key(num_frame, 'KP_6', '6', row=2, column=2, padx=2, pady=2, w=6)

        # Row 3
        self._add_key(num_frame, 'KP_1', '1', row=3, column=0, padx=2, pady=2, w=6)
        self._add_key(num_frame, 'KP_2', '2', row=3, column=1, padx=2, pady=2, w=6)
        self._add_key(num_frame, 'KP_3', '3', row=3, column=2, padx=2, pady=2, w=6)
        # Enter spans rows 3-4 (vertical) and stretch vertically like the '+' key
        self._add_key(num_frame, 'EnterKP', 'Enter', row=3, column=3, rowspan=2, padx=2, pady=2, w=6, h=3, sticky='ns')

        # Row 4
        # KP_0 spans two columns (0 and 1)
        self._add_key(num_frame, 'KP_0', '0', row=4, column=0, columnspan=2, padx=2, pady=2, w=13)
        self._add_key(num_frame, 'KP_Decimal', '.', row=4, column=2, padx=2, pady=2, w=6)

        # Middle cluster keys (between main keyboard and numpad)
        # Top row: Insert, Home, PgUp
        self._add_key(mid_frame, 'Insert', 'Insert', row=0, column=0, padx=2, pady=2, w=6)
        self._add_key(mid_frame, 'Home', 'Home', row=0, column=1, padx=2, pady=2, w=6)
        self._add_key(mid_frame, 'PgUp', 'PgUp', row=0, column=2, padx=2, pady=2, w=6)
        # Bottom row: Delete, End, PgDn
        self._add_key(mid_frame, 'Delete', 'Delete', row=1, column=0, padx=2, pady=2, w=6)
        self._add_key(mid_frame, 'End', 'End', row=1, column=1, padx=2, pady=2, w=6)
        self._add_key(mid_frame, 'PgDn', 'PgDn', row=1, column=2, padx=2, pady=2, w=6)

        # Arrow keys cluster under the middle cluster (T-layout)
        arrow_frame = tk.Frame(mid_frame, bg="#001f3f")
        arrow_frame.grid(row=2, column=0, columnspan=3, pady=(8,0))

        # Place arrows in a T layout: Up above, Left/Down/Right in a row
        self._add_key(arrow_frame, 'Up', '↑', row=0, column=1, padx=2, pady=2, w=6)
        self._add_key(arrow_frame, 'Left', '←', row=1, column=0, padx=2, pady=2, w=6)
        self._add_key(arrow_frame, 'Down', '↓', row=1, column=1, padx=2, pady=2, w=6)
        self._add_key(arrow_frame, 'Right', '→', row=1, column=2, padx=2, pady=2, w=6)

    def reset_colors(self):
        """Reset all keys to default (black) and reset cycle state."""
        for k in self.keys.values():
            try:
                k.color_index = -1
                k.btn.configure(bg="#ffffff", fg="#000000")
            except Exception:
                pass

    def _on_toggle(self):
        # If full_var True -> show numpad, else hide it
        if getattr(self, 'num_frame', None) is None:
            return
        if self.full_var.get():
            self.toggle_btn.configure(text="Full KB")
            self.num_frame.grid()
        else:
            self.toggle_btn.configure(text="Compact KB")
            self.num_frame.grid_remove()

    def _draw_toggle(self):
        """Draw the switch on the canvas based on `self.full_var`."""
        c = self.toggle_canvas
        c.delete("all")
        w = int(c['width'])
        h = int(c['height'])
        radius = h // 2
        # track color when active vs inactive
        active = self.full_var.get()
        track_color = '#0a84ff' if active else '#444444'
        knob_x = w - radius - 3 if active else 3 + radius
        # draw rounded track: left oval, right oval, center rect
        c.create_oval(3, 3, 3 + h - 6, 3 + h - 6, fill=track_color, outline=track_color)
        c.create_oval(w - (3 + h - 6), 3, w - 3, 3 + h - 6, fill=track_color, outline=track_color)
        c.create_rectangle(radius, 3, w - radius, 3 + h - 6, fill=track_color, outline=track_color)
        # knob
        knob_color = '#ffffff'
        c.create_oval(knob_x - radius + 3, 3, knob_x + radius - 3, 3 + h - 6, fill=knob_color, outline='#bbbbbb')
        # update text highlights
        if active:
            self.full_label.config(fg="#ffffff")
            self.compact_label.config(fg="#888888")
        else:
            self.full_label.config(fg="#888888")
            self.compact_label.config(fg="#ffffff")

    def _toggle_switch(self):
        # flip state and redraw, then call handler to show/hide numpad
        self.full_var.set(not self.full_var.get())
        self._draw_toggle()
        # show or hide numpad
        if self.full_var.get():
            self.num_frame.grid()
        else:
            self.num_frame.grid_remove()

    def _on_keypress(self, event):
        ks = getattr(event, 'keysym', None)
        if not ks:
            return

        # Always handle Tab explicitly and prevent focus traversal
        if ks in ('Tab', 'ISO_Left_Tab'):
            key_id = 'Tab'
            key = self.keys.get(key_id)
            found = key is not None
            try:
                self._set_debug(ks, getattr(event, 'char', ''), getattr(event, 'keycode', None), key_id, found)
            except Exception:
                pass
            if key:
                key.press()
            return "break"

        # If the keysym indicates a keypad key (KP_*), prefer that mapping
        if ks and ks.startswith('KP_'):
            key_id = ks
        # Prefer event.char for printable characters (handles punctuation)
        ch = getattr(event, 'char', '')
        key_id = None
        # Only treat event.char as a printable character when it's truly printable
        # (this avoids control characters like Escape '\x1b' overriding keysym)
        if ch and ch != '\x00' and ch.isprintable():
            # space char -> Space key id
            if ch == ' ':
                key_id = 'Space'
            else:
                # letters -> uppercase; punctuation use exact char
                if ch.isalpha():
                    key_id = ch.upper()
                else:
                    key_id = ch

        # If no printable char, map common keysym names and modifiers
        if key_id is None:
            mapping = {
                'space': 'Space',
                'Return': 'Enter',
                'Enter': 'Enter',
                'BackSpace': 'Backspace',
                'Tab': 'Tab',
                'Escape': 'Esc',
                'Prior': 'PgUp',
                'Next': 'PgDn',
                'Page_Up': 'PgUp',
                'Page_Down': 'PgDn',
                    # alternate names for Alt/Meta keys
                    'Menu': 'Menu', 'Meta_L': 'Win', 'Meta_R': 'Win',
                    'AltGr': 'AltGr', 'ISO_Level3_Shift': 'AltGr', 'Mode_switch': 'AltGr',
                    'Option_L': 'Alt', 'Option_R': 'AltGr',
                # punctuation names
                'comma': ',', 'period': '.', 'slash': '/', 'minus': '-', 'equal': '=',
                'bracketleft': '[', 'bracketright': ']', 'backslash': '\\', 'semicolon': ';', 'apostrophe': "'",
                # modifiers unified
                'Shift_L': 'Shift', 'Shift_R': 'ShiftR',
                'Control_L': 'Ctrl', 'Control_R': 'CtrlR',
                'Alt_L': 'Alt', 'Alt_R': 'AltGr',
                'Win_L': 'Win', 'Win_R': 'Win',
                'Caps_Lock': 'Caps',
                'Super_L': 'Win', 'Super_R': 'Win'
            }
            # function keys (F1..F12) map by name
            if ks.startswith('F') and ks[1:].isdigit():
                key_id = ks
            elif ks in mapping:
                key_id = mapping[ks]

        # If still not found, as a fallback use keysym directly
        if key_id is None:
            key_id = ks

        # Lookup and press
        key = self.keys.get(key_id)
        found = key is not None
        # update on-screen debug info so user can see keysym/char mapping
        try:
            self._set_debug(ks, ch, getattr(event, 'keycode', None), key_id, found)
        except Exception:
            pass
        if key:
            key.press()
            # Prevent default focus traversal for Tab so it behaves like a key press
            if key_id == 'Tab' or ks == 'Tab' or ks == 'ISO_Left_Tab':
                return "break"

    def _on_keyrelease(self, event):
        # optional: nothing for now
        pass

    def set_menu_callback(self, callback):
        """Allow embedding container to set a Menu callback. Creates a Menu button if needed."""
        try:
            self._menu_callback = callback
            # create a small Menu button on the controls row if not present
            if not hasattr(self, 'menu_btn'):
                try:
                    self.menu_btn = tk.Button(self.controls_frame, text="Menu", command=lambda: self._menu_callback() if callable(self._menu_callback) else None,
                                               bg="#444444", fg="#ffffff", takefocus=0)
                    self.menu_btn.pack(side="right", padx=(6,2))
                except Exception:
                    pass
        except Exception:
            pass


if __name__ == '__main__':
    root = tk.Tk()
    gui = KeyboardGUI(root)
    root.mainloop()
