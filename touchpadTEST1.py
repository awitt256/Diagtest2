import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import sys
import os
import json


class TouchpadTester:
    # ── Catppuccin Mocha palette ──────────────────────────────────────
    BG      = "#1e1e2e"
    SURFACE = "#313244"
    CRUST   = "#181825"
    OVERLAY = "#6c7086"
    TEXT    = "#cdd6f4"
    SUBTEXT = "#a6adc8"
    BLUE    = "#89b4fa"
    GREEN   = "#a6e3a1"
    RED     = "#f38ba8"
    YELLOW  = "#f9e2af"
    ORANGE  = "#fab387"
    MANTLE  = "#181825"

    def __init__(self, root=None, embedded=False):
        self._embedded = embedded
        self.lc = 0
        self.rc = 0
        self.btn_lc = 0
        self.btn_rc = 0
        self._dragging = False
        self._scene_ok = False
        self.completed = [False] * 10
        self._cur_box = 0
        self._has_physical_buttons = False
        self._btn_prompt_asked = False
        self._btn_user_confirmed = False
        self._btn_global_handler_bound = False
        self._emb_dragging = False
        self._emb_lc = 0
        self._emb_rc = 0
        self._emb_btn_lc = 0
        self._emb_btn_rc = 0
        self._lc_box_state = False
        self._rc_box_state = False
        self._btn_l_box_state = False
        self._btn_r_box_state = False

        if root is None:
            self.root = tk.Tk()
            self.root.title("Touchpad Tester")
            self.root.configure(bg=self.BG)
            self.root.geometry("1100x600")
            own_root = True
        else:
            self.root = root
            own_root = False

        # ── scrollable container ──────────────────────────────────────
        outer = tk.Frame(self.root, bg=self.BG)
        outer.pack(fill="both", expand=True)

        self._scroll_canvas = tk.Canvas(outer, bg=self.BG, highlightthickness=0)
        vsb = tk.Scrollbar(outer, orient="vertical", command=self._scroll_canvas.yview)
        self._scroll_canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._scroll_canvas.pack(side="left", fill="both", expand=True)

        root_pad = tk.Frame(self._scroll_canvas, bg=self.BG)
        self._scroll_win = self._scroll_canvas.create_window(
            (0, 0), window=root_pad, anchor="nw")

        root_pad.bind("<Configure>", self._on_frame_configure)
        self._scroll_canvas.bind("<Configure>", self._on_canvas_configure)
        self._scroll_canvas.bind("<MouseWheel>", self._on_mousewheel)

        # ── optional top status label (used by _mark_tp) ─────────────
        self._tp_status = tk.Label(root_pad, text="",
                                   font=("Segoe UI", 12, "bold"),
                                   bg=self.BG, fg=self.GREEN)
        self._tp_status.pack(anchor="w", padx=12, pady=(8, 0))

        # ── _build_touchpad_ui is the body of the original __init__ ──
        self._build_touchpad_ui(root_pad)

        if own_root:
            self.root.mainloop()

    def _build_touchpad_ui(self, root_pad):
        # NOTE: the remainder of this method is the body that was
        # originally at module level in the uploaded fragment.
        # It starts by handling the old _tp_run_status dummy guard,
        # then builds the full UI.
        try:
            if not hasattr(self, '_tp_run_status'):
                class _Dummy:
                    def config(self, *a, **k):
                        return None
                self._tp_run_status = _Dummy()
        except Exception:
            pass


        # Arrange Click Test and Drag Test side-by-side to avoid scrolling
        tests_row = tk.Frame(root_pad, bg=self.BG)
        # keep the tests row compact and left-aligned so unused space to the right is avoided
        tests_row.pack(fill="x", expand=False, pady=(0,8), anchor="w")

        left_col = tk.Frame(tests_row, bg=self.BG)
        # keep left column a fixed, smaller width so click area doesn't expand
        left_col.pack(side="left", fill="y", expand=False, padx=(0,8))
        try:
            left_col.configure(width=620)
            left_col.pack_propagate(False)
        except Exception:
            pass

        right_col = tk.Frame(tests_row, bg=self.BG)
        # do not let the right column expand to fill remaining space
        right_col.pack(side="left", fill="y", expand=False)

        # ── CLICK TEST (left column) ────────────────────────────────────────
        ct_hdr = tk.Frame(left_col, bg=self.BG)
        ct_hdr.pack(fill="x", pady=(0, 6))
        tk.Label(ct_hdr, text="Touchpad Test",
                 font=("Segoe UI", 18, "bold"), bg=self.BG, fg=self.BLUE).pack(side="left")
        self._click_pass = tk.Label(ct_hdr, text="",
                                    font=("Segoe UI", 13, "bold"), bg=self.BG, fg=self.GREEN)
        self._click_pass.pack(side="right", pady=2)

        cards = tk.Frame(left_col, bg=self.BG)
        cards.pack(fill="x", pady=(0, 8))
        cards.columnconfigure(0, weight=1)
        cards.columnconfigure(1, weight=1)
        self._lc_lbl, self._lc_bar, self._lc_st = self._make_card(cards, "Left Clicks",  col=0)
        self._rc_lbl, self._rc_bar, self._rc_st = self._make_card(cards, "Right Clicks", col=1)
        # bind clicks on the card widgets to register left/right clicks
        try:
            for w in (self._lc_lbl, self._lc_bar, self._lc_st):
                try:
                    w.bind('<Button-1>', self._lc_box_click)
                    w.bind('<Button-3>', self._lc_box_click)
                except Exception:
                    pass
            try:
                # also bind the card frame itself
                card = getattr(self, '_lc_lbl', None).master
                card.bind('<Button-1>', self._lc_box_click)
                card.bind('<Button-3>', self._lc_box_click)
            except Exception:
                pass
        except Exception:
            pass
        try:
            for w in (self._rc_lbl, self._rc_bar, self._rc_st):
                try:
                    w.bind('<Button-1>', self._rc_box_click)
                    w.bind('<Button-3>', self._rc_box_click)
                except Exception:
                    pass
            try:
                card = getattr(self, '_rc_lbl', None).master
                card.bind('<Button-1>', self._rc_box_click)
                card.bind('<Button-3>', self._rc_box_click)
            except Exception:
                pass
        except Exception:
            pass

        cz_wrap = tk.Frame(left_col, bg=self.SURFACE, padx=4, pady=4)
        cz_wrap.pack(fill="both", expand=True)
        # smaller decorative click area — users will click the Left/Right cards instead
        self.cz = tk.Canvas(cz_wrap, bg=self.CRUST, height=56,
                            highlightthickness=1, highlightbackground=self.BLUE,
                            cursor="arrow")
        self.cz.pack(fill="both", expand=True)
        # do not bind direct click handlers on this canvas; top cards will handle clicks
        self.cz.bind("<Configure>", lambda e: self.cz.coords(
            self._cz_txt, e.width // 2, e.height // 2))
        self._cz_txt = self.cz.create_text(
            440, 32,
            text="Click the Left / Right boxes to register clicks",
            font=("Segoe UI", 11), fill=self.SUBTEXT, justify="center")

        # Label to display detected pointing devices (touchpad vs physical click buttons)
        try:
            self._device_info = tk.Label(cz_wrap, text="Detecting pointing devices...",
                                         font=("Segoe UI", 9), bg=self.CRUST, fg=self.SUBTEXT)
            self._device_info.pack(fill="x", pady=(6,0))
        except Exception:
            self._device_info = None
        # Kick off detection in background
        try:
            threading.Thread(target=self._detect_pointing_devices, daemon=True).start()
        except Exception:
            pass

        # Placeholder frame for physical button click section (created only when needed)
        try:
            self._btn_frame = tk.Frame(left_col, bg=self.SURFACE)
        except Exception:
            self._btn_frame = None

        # ── DRAG TEST (right column) ─────────────────────────────────────────
        dt_hdr = tk.Frame(right_col, bg=self.BG)
        dt_hdr.pack(fill="x", pady=(0, 6))
        tk.Label(dt_hdr, text="Drag Test",
                 font=("Segoe UI", 18, "bold"), bg=self.BG, fg=self.YELLOW).pack(side="left")
        # stack Reset button above the drag status on the right
        right_stack = tk.Frame(dt_hdr, bg=self.BG)
        right_stack.pack(side="right")
        tk.Button(right_stack, text="Reset Test", bg=self.OVERLAY, fg=self.TEXT,
              font=("Segoe UI", 10, "bold"), command=self._reset_all).pack(pady=(0,4))
        self._drag_st = tk.Label(right_stack,
                 text="Drag the square into all 10 boxes",
                     font=("Segoe UI", 13), bg=self.BG, fg=self.SUBTEXT)
        self._drag_st.pack()

        dc_wrap = tk.Frame(right_col, bg=self.SURFACE, padx=4, pady=4)
        dc_wrap.pack(fill="both", expand=True)
        # reduce canvas height to avoid excess vertical empty space
        self.dc = tk.Canvas(dc_wrap, bg=self.CRUST, height=360,
                            highlightthickness=2, highlightbackground=self.SURFACE)
        # prefer a compact left-aligned canvas so the scene doesn't leave empty space to the right
        try:
            self.dc.config(width=560)
        except Exception:
            pass
        self.dc.pack(fill="y", expand=False, anchor="w")
        self.dc.bind("<Configure>",       self._build_scene)
        self.dc.bind("<ButtonPress-1>",   self._press)
        self.dc.bind("<B1-Motion>",       self._move)
        self.dc.bind("<ButtonRelease-1>", self._release)

        

    # ── scroll helpers ──────────────────────────────────────────────
    def _on_frame_configure(self, _event):
        self._scroll_canvas.configure(
            scrollregion=self._scroll_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._scroll_canvas.itemconfig(self._scroll_win, width=event.width)

    def _on_mousewheel(self, event):
        self._scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── click-test helpers ───────────────────────────────────────
    def _make_card(self, parent, label, col):
        # Use a fixed, smaller width so click-test cards don't expand too wide
        card = tk.Frame(parent, bg=self.SURFACE, padx=14, pady=10)
        card.grid(row=0, column=col, padx=8)
        try:
            card.configure(width=260)
            card.grid_propagate(False)
        except Exception:
            pass
        tk.Label(card, text=label, font=("Segoe UI", 12, "bold"),
                 bg=self.SURFACE, fg=self.SUBTEXT).pack()
        count = tk.Label(card, text="0 / 10", font=("Segoe UI", 30, "bold"),
                         bg=self.SURFACE, fg=self.TEXT)
        count.pack()
        bar = tk.Canvas(card, height=8, bg=self.OVERLAY, highlightthickness=0)
        bar.pack(fill="x", pady=4)
        status = tk.Label(card, text="Waiting...", font=("Segoe UI", 11),
                          bg=self.SURFACE, fg=self.YELLOW)
        status.pack()
        return count, bar, status

    # ---------- Physical-button click section (created on demand) ----------
    def _show_button_click_section(self):
        try:
            if getattr(self, '_btn_frame', None) is None:
                return
            # If already populated, just ensure it's visible
            if getattr(self, '_btn_frame_populated', False):
                try:
                    self._btn_frame.pack(fill="x", pady=(8,4))
                except Exception:
                    pass
                return

            # Build two small cards for Left Button / Right Button inside the placeholder
            try:
                self._btn_frame.pack(fill="x", pady=(8,4))
                b_cards = tk.Frame(self._btn_frame, bg=self.SURFACE)
                b_cards.pack(fill="x")
                b_cards.columnconfigure(0, weight=1)
                b_cards.columnconfigure(1, weight=1)

                # Left Button card (matching top card style)
                lb = tk.Frame(b_cards, bg=self.SURFACE, padx=14, pady=10)
                lb.grid(row=0, column=0, padx=8)
                try:
                    lb.configure(width=260)
                    lb.grid_propagate(False)
                except Exception:
                    pass
                tk.Label(lb, text="Left Button", font=("Segoe UI", 12, "bold"),
                         bg=self.SURFACE, fg=self.SUBTEXT).pack()
                self._btn_l_lbl = tk.Label(lb, text="0 / 10", font=("Segoe UI", 30, "bold"),
                                           bg=self.SURFACE, fg=self.TEXT)
                self._btn_l_lbl.pack()
                self._btn_l_bar = tk.Canvas(lb, height=8, bg=self.OVERLAY, highlightthickness=0)
                self._btn_l_bar.pack(fill="x", pady=4)
                self._btn_l_st = tk.Label(lb, text="Waiting...", font=("Segoe UI", 11),
                                          bg=self.SURFACE, fg=self.YELLOW)
                self._btn_l_st.pack()
                self._btn_l_area = None
                def _lb_click(event, _lb=lb):
                    try:
                        self._btn_l_box_state = not getattr(self, '_btn_l_box_state', False)
                        col = self.GREEN if self._btn_l_box_state else self.ORANGE
                        _lb.config(bg=col)
                        for child in _lb.winfo_children():
                            try:
                                child.config(bg=col, fg=self.BG)
                            except Exception:
                                pass
                    except Exception:
                        pass
                lb.bind('<Button-1>', _lb_click)
                for _w in lb.winfo_children():
                    try:
                        _w.bind('<Button-1>', _lb_click)
                    except Exception:
                        pass

                # Right Button card (matching top card style)
                rb = tk.Frame(b_cards, bg=self.SURFACE, padx=14, pady=10)
                rb.grid(row=0, column=1, padx=8)
                try:
                    rb.configure(width=260)
                    rb.grid_propagate(False)
                except Exception:
                    pass
                tk.Label(rb, text="Right Button", font=("Segoe UI", 12, "bold"),
                         bg=self.SURFACE, fg=self.SUBTEXT).pack()
                self._btn_r_lbl = tk.Label(rb, text="0 / 10", font=("Segoe UI", 30, "bold"),
                                           bg=self.SURFACE, fg=self.TEXT)
                self._btn_r_lbl.pack()
                self._btn_r_bar = tk.Canvas(rb, height=8, bg=self.OVERLAY, highlightthickness=0)
                self._btn_r_bar.pack(fill="x", pady=4)
                self._btn_r_st = tk.Label(rb, text="Waiting...", font=("Segoe UI", 11),
                                          bg=self.SURFACE, fg=self.YELLOW)
                self._btn_r_st.pack()
                self._btn_r_area = None
                def _rb_click(event, _rb=rb):
                    try:
                        self._btn_r_box_state = not getattr(self, '_btn_r_box_state', False)
                        col = self.GREEN if self._btn_r_box_state else self.ORANGE
                        _rb.config(bg=col)
                        for child in _rb.winfo_children():
                            try:
                                child.config(bg=col, fg=self.BG)
                            except Exception:
                                pass
                    except Exception:
                        pass
                rb.bind('<Button-1>', _rb_click)
                for _w in rb.winfo_children():
                    try:
                        _w.bind('<Button-1>', _rb_click)
                    except Exception:
                        pass

                # Click area for testing physical buttons
                try:
                    test_wrap = tk.Frame(self._btn_frame, bg=self.SURFACE, pady=4)
                    test_wrap.pack(fill="x")
                    # create a smaller canvas but do not bind handlers yet; activation occurs after user confirmation
                    self._btn_click_canvas = tk.Canvas(test_wrap, bg=self.CRUST, height=32, cursor="arrow")
                    self._btn_click_canvas.pack(fill="x", padx=2, pady=2)
                    # show disabled hint until the user explicitly confirms
                    try:
                        self._btn_click_text = self._btn_click_canvas.create_text(
                            120, 16,
                            text="Click here using physical buttons\n(Left & Right)\n(Disabled until confirmed)",
                            fill=self.SUBTEXT, font=("Segoe UI", 8), justify="center")
                    except Exception:
                        # fallback without storing id
                        self._btn_click_canvas.create_text(120, 16, text="Click here using physical buttons\n(Left & Right)", fill=self.SUBTEXT, font=("Segoe UI", 8), justify="center")
                    # bindings and global handlers are attached by _activate_physical_button_areas()
                    
                except Exception:
                    pass

                self._btn_frame_populated = True
                try:
                    if getattr(self, '_scroll_canvas', None) is not None and not getattr(self, '_embedded', False):
                        try:
                            # schedule a reliable scroll after geometry settles
                            self._scroll_canvas.after(60, lambda: self._scroll_widget_into_view(self._btn_frame, margin=20))
                            # second attempt a bit later in case nested geometry still changes
                            self._scroll_canvas.after(300, lambda: self._scroll_widget_into_view(self._btn_frame, margin=20))
                        except Exception:
                            try:
                                self._scroll_widget_into_view(self._btn_frame, margin=20)
                            except Exception:
                                pass
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            pass
    def _scroll_widget_into_view(self, widget, margin=20):
        """Scroll the main scroll canvas so `widget` is visible with a small margin."""
        try:
            canvas = getattr(self, '_scroll_canvas', None)
            if canvas is None or getattr(self, '_embedded', False):
                return
            try:
                canvas.update_idletasks()
            except Exception:
                pass
            bbox_all = canvas.bbox("all") or (0, 0, 0, 0)
            content_height = max(1, bbox_all[3] - bbox_all[1])
            canvas_height = max(1, canvas.winfo_height())
            # get widget and canvas root coordinates
            try:
                widget_rooty = widget.winfo_rooty()
                canvas_rooty = canvas.winfo_rooty()
            except Exception:
                return
            try:
                content_top = canvas.canvasy(0)
            except Exception:
                content_top = 0
            widget_y_in_content = content_top + (widget_rooty - canvas_rooty)
            desired_top = max(0, widget_y_in_content - margin)
            denom = max(1, content_height - canvas_height)
            frac = min(max(desired_top / denom, 0.0), 1.0)
            try:
                canvas.yview_moveto(frac)
            except Exception:
                try:
                    canvas.yview_moveto(float(frac))
                except Exception:
                    pass
        except Exception:
            pass


    def _btn_lclick(self, _event):
        try:
            if self.btn_lc < 10:
                self.btn_lc += 1
                self._refresh_btn_click()
        except Exception:
            pass

    def _btn_rclick(self, _event):
        try:
            if self.btn_rc < 10:
                self.btn_rc += 1
                self._refresh_btn_click()
        except Exception:
            pass

    def _refresh_btn_click(self):
        try:
            lp = self.btn_lc >= 10
            rp = self.btn_rc >= 10
            try:
                self._btn_l_lbl.config(text=f"{self.btn_lc} / 10", fg=self.GREEN if lp else self.TEXT)
                self._btn_r_lbl.config(text=f"{self.btn_rc} / 10", fg=self.GREEN if rp else self.TEXT)
            except Exception:
                pass
            try:
                # draw progress bars for the dedicated button cards
                self._bar_draw(self._btn_l_bar, self.btn_lc)
                self._bar_draw(self._btn_r_bar, self.btn_rc)
            except Exception:
                pass
            try:
                if lp:
                    self._btn_l_st.config(text="PASSED", fg=self.GREEN)
                if rp:
                    self._btn_r_st.config(text="PASSED", fg=self.GREEN)
            except Exception:
                pass
        except Exception:
            pass

    def _make_run_card(self, parent, col):
        card = tk.Frame(parent, bg=self.SURFACE, padx=14, pady=10)
        card.grid(row=0, column=col, padx=8, sticky="ew")
        tk.Label(card, text="Touchpad Test", font=("Segoe UI", 12, "bold"),
                 bg=self.SURFACE, fg=self.SUBTEXT).pack()
        self._tp_run_status = tk.Label(card, text="Idle", font=("Segoe UI", 14),
                                       bg=self.SURFACE, fg=self.TEXT)
        self._tp_run_status.pack(pady=(6, 4))
        tk.Button(card, text="Start", bg=self.BLUE, fg=self.BG, font=("Segoe UI", 11, "bold"),
              command=lambda: self._embed_touchpad(card)).pack(pady=4)
        # (ClickButton Test section removed)
        return card

    def _detect_pointing_devices(self):
        """
        Detect pointing devices via WMI (Win32_PointingDevice) using PowerShell.
        Populate `self._device_info` label and set `self._has_physical_buttons` flag.
        """
        devices = []
        try:
            ps = "Get-CimInstance -ClassName Win32_PointingDevice | Select-Object -Property Name,Manufacturer | ConvertTo-Json -Compress"
            proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=10)
            out = (proc.stdout or "").strip()
            if out:
                try:
                    parsed = json.loads(out)
                    # parsed may be an object or array
                    if isinstance(parsed, list):
                        for it in parsed:
                            nm = (it.get('Name') or '').strip()
                            man = (it.get('Manufacturer') or '').strip()
                            if nm or man:
                                devices.append((nm, man))
                    elif isinstance(parsed, dict):
                        nm = (parsed.get('Name') or '').strip()
                        man = (parsed.get('Manufacturer') or '').strip()
                        if nm or man:
                            devices.append((nm, man))
                except Exception:
                    # fallback: treat raw output lines as names
                    for ln in out.splitlines():
                        if ln.strip():
                            devices.append((ln.strip(), ''))
        except Exception:
            devices = []

        # Heuristic: if any device name/manufacturer contains known keywords,
        # assume there are separate physical click buttons (e.g., Synaptics, ClickPad, TrackPoint)
        keywords = ('synapt', 'elan', 'alps', 'trackpoint', 'pointing', 'click', 'button', 'touchpad')
        vendor_keywords = ('synapt', 'alps', 'elan', 'trackpoint')
        has_buttons = False
        dev_names = []
        for nm, man in devices:
            s = f"{nm} {man}".lower()
            dev_names.append((nm or man) if (nm or man) else 'Unknown')
            # If vendor is known to include separate click hardware (Synaptics/Alps/Elan), assume buttons
            if any(v in s for v in vendor_keywords):
                has_buttons = True
                continue
            # Otherwise look for explicit indicators like 'click', 'button', 'trackpoint', 'point', or 'hid'
            if any(k in s for k in ('click', 'button', 'trackpoint', 'point', 'hid')):
                has_buttons = True

        # UI update
        try:
            def _update_label():
                try:
                    if self._device_info is None:
                        return
                    if not dev_names:
                        self._device_info.configure(text="Pointing devices: Unknown")
                    else:
                        self._device_info.configure(text="Pointing devices: " + ", ".join(dev_names))
                    self._has_physical_buttons = has_buttons
                    # If physical buttons detected, append a hint
                    if has_buttons:
                        self._device_info.configure(text=self._device_info.cget('text') + "  —  Physical click buttons detected")
                except Exception:
                    pass
            try:
                # schedule on UI thread
                if hasattr(self, 'cz') and hasattr(self.cz, 'after'):
                    self.cz.after(0, _update_label)
                else:
                    _update_label()
            except Exception:
                _update_label()
        except Exception:
            pass

        # If physical buttons detected, schedule creating the UI sections
        try:
            if has_buttons:
                try:
                    if hasattr(self, 'cz') and hasattr(self.cz, 'after'):
                        # non-embedded button section lives under left_col; schedule create
                        try:
                            self.cz.after(50, lambda: self._show_button_click_section())
                        except Exception:
                            try:
                                self._show_button_click_section()
                            except Exception:
                                pass
                    else:
                        try:
                            self._show_button_click_section()
                        except Exception:
                            pass
                except Exception:
                    pass
            else:
                # ensure flag cleared
                try:
                    self._has_physical_buttons = False
                except Exception:
                    pass
        except Exception:
            pass
        except Exception:
            pass

    def _run_touchpad(self):
        # Launch a separate instance of the touchpad test script
        try:
            path = os.path.abspath(__file__)
            proc = subprocess.Popen([sys.executable, path])
            self._tp_run_status.config(text=f"Running (pid {proc.pid})", fg=self.BLUE)
        except Exception as e:
            self._tp_run_status.config(text="Error", fg="red")

    def _embed_touchpad(self, card):
        for w in card.winfo_children():
            w.destroy()
        tk.Label(card, text="Touchpad Test", font=("Segoe UI", 12, "bold"),
                 bg=self.SURFACE, fg=self.SUBTEXT).pack()

        # embedded click area
        self._emb_lc = 0
        self._emb_rc = 0
        cl = tk.Frame(card, bg=self.SURFACE)
        cl.pack(fill="x", pady=(6, 4))
        self._emb_click_canvas = tk.Canvas(cl, bg=self.CRUST, height=60, cursor="crosshair")
        self._emb_click_canvas.pack(fill="x", padx=4, pady=4)
        self._emb_click_canvas.create_text(140, 40, text="Click here\nLeft & Right",
                                           fill=self.SUBTEXT, font=("Segoe UI", 10), justify="center")
        self._emb_click_canvas.bind("<Button-1>", self._emb_lclick)
        self._emb_click_canvas.bind("<Button-3>", self._emb_rclick)

        # If physical click buttons were detected, show an embedded button-click area
        try:
            if getattr(self, '_has_physical_buttons', False):
                bcl = tk.Frame(card, bg=self.SURFACE)
                bcl.pack(fill="x", pady=(6,4))
                # create embedded button canvas but do not bind handlers until user confirms
                self._emb_btn_click_canvas = tk.Canvas(bcl, bg=self.CRUST, height=28, cursor="arrow")
                self._emb_btn_click_canvas.pack(fill="x", padx=4, pady=4)
                try:
                    self._emb_btn_click_text = self._emb_btn_click_canvas.create_text(
                        120, 14,
                        text="Physical buttons area\nClick using the hardware buttons\n(Disabled until confirmed)",
                        fill=self.SUBTEXT, font=("Segoe UI", 7), justify="center")
                except Exception:
                    self._emb_btn_click_canvas.create_text(120, 14, text="Physical buttons area\nClick using the hardware buttons",
                                                           fill=self.SUBTEXT, font=("Segoe UI", 7), justify="center")
                # If user already confirmed, activate handlers immediately
                try:
                    if getattr(self, '_btn_user_confirmed', False):
                        try:
                            self._activate_physical_button_areas()
                        except Exception:
                            pass
                except Exception:
                    pass
                # counters
                try:
                    lbls = tk.Frame(bcl, bg=self.SURFACE)
                    lbls.pack(fill="x")
                    self._emb_btn_l_lbl = tk.Label(lbls, text="L: 0/10", bg=self.SURFACE, fg=self.TEXT)
                    self._emb_btn_l_lbl.pack(side="left", padx=6)
                    self._emb_btn_r_lbl = tk.Label(lbls, text="R: 0/10", bg=self.SURFACE, fg=self.TEXT)
                    self._emb_btn_r_lbl.pack(side="left", padx=6)
                except Exception:
                    pass
        except Exception:
            pass

        # (Removed small inline L/R labels here to avoid duplicate counters)

        # embedded drag area
        dr = tk.Frame(card, bg=self.SURFACE)
        dr.pack(fill="both", expand=True, pady=(6, 4))
        self._emb_dc = tk.Canvas(dr, bg=self.CRUST, height=180)
        self._emb_dc.pack(fill="both", expand=True, padx=4, pady=4)
        self._emb_dc.bind("<ButtonPress-1>", self._emb_press)
        self._emb_dc.bind("<B1-Motion>", self._emb_move)
        self._emb_dc.bind("<ButtonRelease-1>", self._emb_release)

        # build small scene (10 targets, 5x2) with zig-zag numbering (compact)
        W, H = 300, 180
        cols, rows = 5, 2
        BW = max(36, (W - (cols + 1) * 4) // cols)
        # make embedded boxes square
        BH = BW
        # cap embedded boxes to keep them compact inside the card
        BW = min(BW, 60)
        BH = BW
        gx = max(2, (W - cols * BW) // (cols + 1))
        gy = max(3, (H - rows * BH) // (rows + 1))
        self._emb_targets = []
        for i in range(10):
            c = i % cols
            r = i // cols
            x1 = gx + c * (BW + gx)
            y1 = gy + r * (BH + gy)
            x2, y2 = x1 + BW, y1 + BH
            if r == 0:
                num = i + 1
            else:
                num = 15 - i
            rid = self._emb_dc.create_rectangle(x1, y1, x2, y2, fill=self.SURFACE, outline=self.OVERLAY, width=1)
            tid = self._emb_dc.create_text((x1 + x2) // 2, (y1 + y2) // 2, text=str(num), fill=self.OVERLAY, font=("Segoe UI", 10, "bold"))
            self._emb_targets.append(dict(rid=rid, tid=tid, x1=x1, y1=y1, x2=x2, y2=y2, done=False, num=num))

        # create embedded connecting lines following numeric order
        self._emb_lines = []
        centers_by_num = [None] * 10
        for t in self._emb_targets:
            centers_by_num[t['num'] - 1] = (((t['x1'] + t['x2']) // 2), ((t['y1'] + t['y2']) // 2))
        for i in range(len(centers_by_num) - 1):
            x1, y1 = centers_by_num[i]
            x2, y2 = centers_by_num[i + 1]
            lid = self._emb_dc.create_line(x1, y1, x2, y2, fill=self.OVERLAY, width=3, capstyle='round')
            try:
                self._emb_dc.tag_lower(lid)
            except Exception:
                pass
            self._emb_lines.append(lid)

        # make draggable square slightly larger relative to the embedded box
        SQ = min(44, max(16, int(min(BW, BH) * 0.85)))
        # find index of target number 1 for embedded scene
        idx0 = next((i for i, t in enumerate(self._emb_targets) if t.get('num') == 1), 0)
        t0 = self._emb_targets[idx0]
        sx = (t0['x1'] + t0['x2']) // 2 - SQ // 2
        sy = (t0['y1'] + t0['y2']) // 2 - SQ // 2
        self._emb_SQ = SQ
        # create the draggable square and label
        self._emb_sq = self._emb_dc.create_rectangle(sx, sy, sx + SQ, sy + SQ, fill=self.BLUE, outline=self.OVERLAY, width=1)
        self._emb_st = self._emb_dc.create_text(sx + SQ // 2, sy + SQ // 2, text='DRAG', fill=self.BG, font=("Segoe UI", 8, "bold"))
        self._emb_cur = idx0

        self._tp_run_status.config(text="Embedded", fg=self.BLUE)

    def _mark_tp(self, passed: bool):
        if passed:
            self._tp_status.config(text="Touchpad Test: PASS", fg=self.GREEN)
        else:
            self._tp_status.config(text="Touchpad Test: FAIL", fg=self.TEXT)

    # ── embedded touch handlers ─────────────────────────────────────
    def _emb_lclick(self, _event):
        if self._emb_lc < 10:
            self._emb_lc += 1
            try:
                self._emb_l_lbl.config(text=f"L: {self._emb_lc}/10")
            except Exception:
                pass

    def _emb_rclick(self, _event):
        if self._emb_rc < 10:
            self._emb_rc += 1
            try:
                self._emb_r_lbl.config(text=f"R: {self._emb_rc}/10")
            except Exception:
                pass

    def _emb_press(self, event):
        hits = set(self._emb_dc.find_overlapping(event.x-3, event.y-3, event.x+3, event.y+3))
        sq = getattr(self, '_emb_sq', None)
        if sq is not None and sq in hits:
            self._emb_dragging = True
            c = self._emb_dc.coords(sq)
            self._emb_off = (event.x - c[0], event.y - c[1])
            try:
                self._emb_dc.tag_raise(sq)
            except Exception:
                pass

    def _emb_move(self, event):
        if not getattr(self, '_emb_dragging', False):
            return
        SQ = getattr(self, '_emb_SQ', 24)
        nx = event.x - self._emb_off[0]
        ny = event.y - self._emb_off[1]
        # clamp to canvas bounds
        try:
            w = int(self._emb_dc.winfo_width())
            h = int(self._emb_dc.winfo_height())
            nx = max(0, min(nx, w - SQ))
            ny = max(0, min(ny, h - SQ))
        except Exception:
            pass
        self._emb_dc.coords(self._emb_sq, nx, ny, nx+SQ, ny+SQ)
        self._emb_dc.coords(self._emb_st, nx+SQ//2, ny+SQ//2)

    def _emb_release(self, event):
        if not getattr(self, '_emb_dragging', False):
            return
        self._emb_dragging = False
        c = self._emb_dc.coords(self._emb_sq)
        cx = (c[0] + c[2]) / 2
        cy = (c[1] + c[3]) / 2
        landed = None
        for i, t in enumerate(self._emb_targets):
            if (not t['done'] and t['x1'] < cx < t['x2'] and t['y1'] < cy < t['y2']):
                landed = i
                break
        if landed is not None:
            t = self._emb_targets[landed]
            self._emb_dc.itemconfig(t['rid'], fill="#1a3828", outline=self.GREEN)
            self._emb_dc.itemconfig(t['tid'], fill=self.GREEN, text='\u2713')
            t['done'] = True
            prev = self._emb_cur
            try:
                prev_num = self._emb_targets[prev]['num']
            except Exception:
                prev_num = 1
            landed_num = t['num']
            # light connecting line segments between prev and landed based on numeric order
            try:
                start = min(prev_num, landed_num) - 1
                end = max(prev_num, landed_num) - 1
                for idx in range(start, end):
                    lid = self._emb_lines[idx]
                    self._emb_dc.itemconfig(lid, fill=self.GREEN)
            except Exception:
                pass
            self._emb_cur = landed

        cur = self._emb_targets[self._emb_cur]
        SQ = self._emb_SQ
        sx = (cur['x1'] + cur['x2']) // 2 - SQ // 2
        sy = (cur['y1'] + cur['y2']) // 2 - SQ // 2
        self._emb_dc.coords(self._emb_sq, sx, sy, sx+SQ, sy+SQ)
        self._emb_dc.coords(self._emb_st, sx+SQ//2, sy+SQ//2)

        # update embedded progress text if present
        try:
            done = sum(1 for t in self._emb_targets if t.get('done'))
            if done == len(self._emb_targets):
                self._emb_dc.config(highlightbackground=self.GREEN)
            else:
                # no-op: embedded widget uses visual ticks on boxes
                pass
        except Exception:
            pass

    def _emb_btn_lclick(self, _event):
        try:
            if self._emb_btn_lc < 10:
                self._emb_btn_lc += 1
                try:
                    self._emb_btn_l_lbl.config(text=f"L: {self._emb_btn_lc}/10")
                except Exception:
                    pass
        except Exception:
            pass

    def _emb_btn_rclick(self, _event):
        try:
            if self._emb_btn_rc < 10:
                self._emb_btn_rc += 1
                try:
                    self._emb_btn_r_lbl.config(text=f"R: {self._emb_btn_rc}/10")
                except Exception:
                    pass
        except Exception:
            pass

    def _create_embedded_button_section(self):
        """Create embedded physical-button UI in an already-embedded tester view."""
        try:
            # Ensure we have an embedded canvas to attach to
            if not hasattr(self, '_emb_dc'):
                return
            # If embedded button canvas already exists, do nothing
            if getattr(self, '_emb_btn_click_canvas', None) is not None:
                return
            # card is two levels up from _emb_dc: dr = _emb_dc.master; card = dr.master
            try:
                dr = self._emb_dc.master
                card = dr.master
            except Exception:
                card = None
            if card is None:
                return
            # Embedded physical-button section removed; clicks are handled via top cards.
            return
        except Exception:
            pass

    def _activate_physical_button_areas(self):
        """Bind handlers and global captures for physical-button canvases.
        This is called only after the user confirms via the prompt.
        """
        try:
            # Bind the non-embedded canvas if present
            try:
                c = getattr(self, '_btn_click_canvas', None)
                if c is not None:
                    try:
                        c.config(cursor='hand2')
                        c.bind('<Button-1>', self._btn_lclick)
                        c.bind('<Button-3>', self._btn_rclick)
                        # update text to remove disabled hint if present
                        try:
                            if hasattr(self, '_btn_click_text'):
                                c.itemconfig(self._btn_click_text, text='Click here using physical buttons\n(Left & Right)')
                        except Exception:
                            pass
                    except Exception:
                        pass
            except Exception:
                pass

            # Enable per-card left area if present
            try:
                la = getattr(self, '_btn_l_area', None)
                if la is not None:
                    try:
                        la.config(cursor='hand2')
                        la.bind('<Button-1>', self._btn_lclick)
                        la.bind('<Button-3>', self._btn_rclick)
                        try:
                            if hasattr(self, '_btn_l_area_text'):
                                la.itemconfig(self._btn_l_area_text, text='Click anywhere in this box')
                        except Exception:
                            pass
                    except Exception:
                        pass
            except Exception:
                pass

            # Enable per-card right area if present
            try:
                ra = getattr(self, '_btn_r_area', None)
                if ra is not None:
                    try:
                        ra.config(cursor='hand2')
                        ra.bind('<Button-1>', self._btn_lclick)
                        ra.bind('<Button-3>', self._btn_rclick)
                        try:
                            if hasattr(self, '_btn_r_area_text'):
                                ra.itemconfig(self._btn_r_area_text, text='Click anywhere in this box')
                        except Exception:
                            pass
                    except Exception:
                        pass
            except Exception:
                pass

            # Bind the embedded canvas if present
            try:
                ec = getattr(self, '_emb_btn_click_canvas', None)
                if ec is not None:
                    try:
                        ec.config(cursor='hand2')
                        ec.bind('<Button-1>', self._emb_btn_lclick)
                        ec.bind('<Button-3>', self._emb_btn_rclick)
                        # update embedded label to remove disabled hint
                        try:
                            if hasattr(self, '_emb_btn_click_text'):
                                ec.itemconfig(self._emb_btn_click_text, text='Physical buttons area\nClick using the hardware buttons')
                        except Exception:
                            pass
                    except Exception:
                        pass
            except Exception:
                pass

            # Single global handler to route hardware clicks to whichever canvas they land in
            if not getattr(self, '_btn_global_handler_bound', False):
                # Only bind a global handler if there are actual canvases to watch
                try:
                    canvases_present = any(
                        x is not None for x in (
                            getattr(self, '_btn_click_canvas', None),
                            getattr(self, '_btn_l_area', None),
                            getattr(self, '_btn_r_area', None),
                            getattr(self, '_emb_btn_click_canvas', None),
                        )
                    )
                except Exception:
                    canvases_present = False
                if not canvases_present:
                    return
                def _global_btn_handler(e):
                    try:
                        for canvas, lfunc, rfunc in (
                            (getattr(self, '_btn_click_canvas', None), self._btn_lclick, self._btn_rclick),
                            (getattr(self, '_btn_l_area', None), self._btn_lclick, self._btn_rclick),
                            (getattr(self, '_btn_r_area', None), self._btn_lclick, self._btn_rclick),
                            (getattr(self, '_emb_btn_click_canvas', None), self._emb_btn_lclick, self._emb_btn_rclick),
                        ):
                            if canvas is None:
                                continue
                            try:
                                rx = canvas.winfo_rootx()
                                ry = canvas.winfo_rooty()
                                rw = canvas.winfo_width()
                                rh = canvas.winfo_height()
                            except Exception:
                                continue
                            if rw <= 0 or rh <= 0:
                                continue
                            if rx <= getattr(e, 'x_root', -9999) <= rx + rw and ry <= getattr(e, 'y_root', -9999) <= ry + rh:
                                if getattr(e, 'num', None) == 1:
                                    try:
                                        lfunc(e)
                                    except Exception:
                                        pass
                                elif getattr(e, 'num', None) == 3:
                                    try:
                                        rfunc(e)
                                    except Exception:
                                        pass
                    except Exception:
                        pass

                try:
                    tl = self.root.winfo_toplevel()
                    tl.bind_all('<Button-1>', _global_btn_handler, add='+')
                    tl.bind_all('<Button-3>', _global_btn_handler, add='+')
                    self._btn_global_handler_bound = True
                except Exception:
                    try:
                        self.root.bind_all('<Button-1>', _global_btn_handler, add='+')
                        self.root.bind_all('<Button-3>', _global_btn_handler, add='+')
                        self._btn_global_handler_bound = True
                    except Exception:
                        pass
        except Exception:
            pass


    def _lclick(self, _event):
        if self.lc < 10:
            self.lc += 1
            self._refresh_click()

    def _rclick(self, _event):
        if self.rc < 10:
            self.rc += 1
            self._refresh_click()

    def _lc_box_click(self, _event):
        """Handle clicks on the Left Clicks card area — register a left click and toggle color."""
        try:
            if self.lc < 10:
                self.lc += 1
                self._refresh_click()
            # toggle full card color between GREEN and ORANGE
            try:
                self._lc_box_state = not getattr(self, '_lc_box_state', False)
                col = self.GREEN if self._lc_box_state else self.ORANGE
                try:
                    card = getattr(self, '_lc_lbl', None).master
                except Exception:
                    card = None
                if card is not None:
                    try:
                        card.config(bg=col)
                    except Exception:
                        pass
                    # update child widgets' bg/fg for readability
                    try:
                        for child in card.winfo_children():
                            try:
                                try:
                                    child.config(bg=col, fg=self.BG)
                                except Exception:
                                    pass
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

    def _rc_box_click(self, _event):
        """Handle clicks on the Right Clicks card area — register a right click and toggle color."""
        try:
            if self.rc < 10:
                self.rc += 1
                self._refresh_click()
            # toggle full card color between GREEN and ORANGE
            try:
                self._rc_box_state = not getattr(self, '_rc_box_state', False)
                col = self.GREEN if self._rc_box_state else self.ORANGE
                try:
                    card = getattr(self, '_rc_lbl', None).master
                except Exception:
                    card = None
                if card is not None:
                    try:
                        card.config(bg=col)
                    except Exception:
                        pass
                    try:
                        for child in card.winfo_children():
                            try:
                                try:
                                    child.config(bg=col, fg=self.BG)
                                except Exception:
                                    pass
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

    def _refresh_click(self):
        lp = self.lc >= 10
        rp = self.rc >= 10
        self._lc_lbl.config(text=f"{self.lc} / 10", fg=self.GREEN if lp else self.TEXT)
        self._rc_lbl.config(text=f"{self.rc} / 10", fg=self.GREEN if rp else self.TEXT)
        self._bar_draw(self._lc_bar, self.lc)
        self._bar_draw(self._rc_bar, self.rc)
        if lp:
            self._lc_st.config(text="PASSED", fg=self.GREEN)
        if rp:
            self._rc_st.config(text="PASSED", fg=self.GREEN)
        if lp and rp:
            self._click_pass.config(text="PASSED!")
            self.cz.config(highlightbackground=self.GREEN)
            # After primary click test completes, ask whether unit has separate
            # physical click buttons (Synaptics/HID). Prompt only once.
            try:
                if not getattr(self, '_btn_prompt_asked', False):
                    self._btn_prompt_asked = True
                    ask = messagebox.askyesno("Click Buttons?", "Does this unit have separate physical click buttons (separate from the touchpad)?")
                    if ask:
                        self._has_physical_buttons = True
                        try:
                            self._show_button_click_section()
                        except Exception:
                            pass
                        try:
                            # if an embedded tester is present, add embedded button UI
                            self._create_embedded_button_section()
                        except Exception:
                            pass
                        # User explicitly confirmed — activate the button click areas and global handlers
                        try:
                            self._btn_user_confirmed = True
                            try:
                                self._activate_physical_button_areas()
                            except Exception:
                                pass
                        except Exception:
                            pass
                    else:
                        self._has_physical_buttons = False
                        try:
                            if getattr(self, '_device_info', None) is not None:
                                self._device_info.configure(text=(self._device_info.cget('text') + "  —  No physical click buttons present"))
                        except Exception:
                            pass
            except Exception:
                pass

    def _bar_draw(self, canvas, val, maxv=10):
        canvas.update_idletasks()
        w = canvas.winfo_width() or 300
        h = canvas.winfo_height() or 8
        canvas.delete("all")
        canvas.create_rectangle(0, 0, w, h, fill=self.OVERLAY, outline="")
        fw = int(w * min(val, maxv) / maxv)
        if fw > 0:
            canvas.create_rectangle(0, 0, fw, h,
                                    fill=self.GREEN if val >= maxv else self.BLUE,
                                    outline="")

    def _build_scene(self, event):
        if self._scene_ok:
            return

        # Prefer event sizes, but use the canvas's real size where possible.
        # The initial <Configure> event can be unreliable; call update_idletasks()
        # and retry a few times to let geometry managers settle.
        try:
            # Ensure geometry is processed
            try:
                self.dc.update_idletasks()
            except Exception:
                pass
            W = getattr(event, 'width', None) or self.dc.winfo_width()
            H = getattr(event, 'height', None) or self.dc.winfo_height()
        except Exception:
            W, H = 0, 0

        # Retry a small number of times if size still looks uninitialized
        if W <= 1 or H <= 1:
            tries = getattr(self, '_build_scene_retries', 0)
            if tries < 6:
                try:
                    self._build_scene_retries = tries + 1
                    def _retry():
                        e = type('E', (), {'width': self.dc.winfo_width(), 'height': self.dc.winfo_height()})()
                        # reset flag so recursion can proceed
                        try:
                            self._build_scene_retries = getattr(self, '_build_scene_retries', 0)
                        except Exception:
                            pass
                        self._build_scene(e)
                    self.dc.after(40, _retry)
                except Exception:
                    pass
            return
        # clear any retry counter when we have a usable size
        if hasattr(self, '_build_scene_retries'):
            try:
                delattr = False
                # safe delete
                del self._build_scene_retries
            except Exception:
                try:
                    del self.__dict__['_build_scene_retries']
                except Exception:
                    pass
        self._scene_ok = True
        self.dc.delete("all")

        # Layout 10 targets in 5 columns x 2 rows
        cols, rows = 5, 2
        # compute reasonable box sizes based on available area (smaller boxes)
        BW = max(32, (W - (cols + 1) * 4) // cols)
        # Make boxes square
        BH = BW
        # reduce gaps between boxes so grid is more compact
        gx = max(2, (W - cols * BW) // (cols + 1))
        gy = max(3, (H - rows * BH) // (rows + 1))
        # cap box width so the grid fits comfortably in unmaximized windows
        BW = min(BW, 64)
        gx = (W - cols * BW) // (cols + 1)
        gy = (H - rows * BH) // (rows + 1)

        self.targets = []
        for i in range(10):
            c = i % cols
            r = i // cols
            x1 = gx + c * (BW + gx)
            y1 = gy + r * (BH + gy)
            x2, y2 = x1 + BW, y1 + BH
            # numbering: top row left->right = 1..5; bottom row right->left = 6..10 reversed
            if r == 0:
                num = i + 1
            else:
                num = 15 - i
            # thinner outline for compact look
            rid = self.dc.create_rectangle(x1, y1, x2, y2,
                                           fill=self.SURFACE, outline=self.OVERLAY, width=1)
            tid = self.dc.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                                      text=str(num), font=("Segoe UI", 14, "bold"),
                                      fill=self.OVERLAY)
            self.targets.append(dict(rid=rid, tid=tid,
                                     x1=x1, y1=y1, x2=x2, y2=y2, done=False, num=num))

        # create connecting lines between centers following numeric order 1->2->...->10
        self.lines = []
        centers_by_num = [None] * 10
        for t in self.targets:
            centers_by_num[t['num'] - 1] = (((t['x1'] + t['x2']) // 2), ((t['y1'] + t['y2']) // 2))
        for i in range(len(centers_by_num) - 1):
            x1, y1 = centers_by_num[i]
            x2, y2 = centers_by_num[i + 1]
            # thinner connector lines
            lid = self.dc.create_line(x1, y1, x2, y2, fill=self.OVERLAY, width=3, capstyle='round')
            try:
                self.dc.tag_lower(lid)
            except Exception:
                pass
            self.lines.append(lid)

        # place square in box 1, mark it done
        # square size should scale with box size but stay smaller than BW/BH
        # make draggable square slightly larger relative to the box so it feels substantial
        SQ = min(64, max(18, int(min(BW, BH) * 0.85)))
        self._SQ = SQ
        # find index of target number 1
        idx0 = next((i for i, t in enumerate(self.targets) if t.get('num') == 1), 0)
        self._cur_box = idx0
        t0 = self.targets[idx0]
        self.dc.itemconfig(t0["rid"], fill="#1a3828", outline=self.GREEN, width=3)
        self.dc.itemconfig(t0["tid"], fill=self.GREEN, text="\u2713")
        t0["done"] = True
        try:
            self.completed[idx0] = True
        except Exception:
            pass

        sx = (t0["x1"] + t0["x2"]) // 2 - SQ // 2
        sy = (t0["y1"] + t0["y2"]) // 2 - SQ // 2
        self._sq_r = self.dc.create_rectangle(sx, sy, sx + SQ, sy + SQ,
                                              fill=self.YELLOW, outline=self.TEXT,
                                              width=2, tags="sq")
        self._sq_t = self.dc.create_text(sx + SQ // 2, sy + SQ // 2,
                                         text="DRAG\nME", font=("Segoe UI", 10, "bold"),
                                         fill=self.BG, tags="sq")
        self._drag_st.config(text="Drag the square into all 10 boxes  (1 / 10)",
                     fg=self.SUBTEXT)

    def _reset_all(self):
        # Reset click counters
        try:
            self.lc = 0
            self.rc = 0
            self._lc_st.config(text="Waiting...", fg=self.YELLOW)
            self._rc_st.config(text="Waiting...", fg=self.YELLOW)
            self._click_pass.config(text="")
            self.cz.config(highlightbackground=self.BLUE)
            self._refresh_click()
        except Exception:
            pass

        # restore top cards' visual background
        try:
            try:
                lcard = getattr(self, '_lc_lbl', None).master
            except Exception:
                lcard = None
            if lcard is not None:
                try:
                    lcard.config(bg=self.SURFACE)
                except Exception:
                    pass
                try:
                    for child in lcard.winfo_children():
                        try:
                            child.config(bg=self.SURFACE, fg=self.TEXT)
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass
        try:
            try:
                rcard = getattr(self, '_rc_lbl', None).master
            except Exception:
                rcard = None
            if rcard is not None:
                try:
                    rcard.config(bg=self.SURFACE)
                except Exception:
                    pass
                try:
                    for child in rcard.winfo_children():
                        try:
                            child.config(bg=self.SURFACE, fg=self.TEXT)
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

        # Reset bottom button cards
        for attr, state_attr in (('_btn_l_lbl', '_btn_l_box_state'), ('_btn_r_lbl', '_btn_r_box_state')):
            try:
                card = getattr(self, attr, None)
                if card is not None:
                    card = card.master
                    card.config(bg=self.SURFACE)
                    for child in card.winfo_children():
                        try:
                            child.config(bg=self.SURFACE, fg=self.TEXT)
                        except Exception:
                            pass
                    setattr(self, state_attr, False)
            except Exception:
                pass

        # Reset main drag scene
        try:
            self.completed = [False] * 10
            self._scene_ok = False
            # clear and rebuild scene using current canvas size
            self.dc.delete("all")
            e = type('E', (), {'width': self.dc.winfo_width(), 'height': self.dc.winfo_height()})()
            self._build_scene(e)
        except Exception:
            pass

        # Reset embedded (if present)
        try:
            if hasattr(self, '_emb_dc') and hasattr(self, '_emb_targets'):
                self._emb_lc = 0
                self._emb_rc = 0
                try:
                    self._emb_l_lbl.config(text="L: 0/10")
                    self._emb_r_lbl.config(text="R: 0/10")
                except Exception:
                    pass
                for i, t in enumerate(self._emb_targets):
                    try:
                        self._emb_dc.itemconfig(t['rid'], fill=self.SURFACE, outline=self.OVERLAY)
                        self._emb_dc.itemconfig(t['tid'], fill=self.OVERLAY, text=str(t.get('num', i+1)))
                    except Exception:
                        pass
                    t['done'] = False
                # reset embedded connecting lines colors
                try:
                    if hasattr(self, '_emb_lines'):
                        for lid in self._emb_lines:
                            try:
                                self._emb_dc.itemconfig(lid, fill=self.OVERLAY)
                            except Exception:
                                pass
                except Exception:
                    pass
                # mark first box (number 1) done and move square there
                t0 = next((t for t in self._emb_targets if t.get('num') == 1), self._emb_targets[0])
                try:
                    self._emb_dc.itemconfig(t0['rid'], fill="#1a3828", outline=self.GREEN)
                    self._emb_dc.itemconfig(t0['tid'], fill=self.GREEN, text="\u2713")
                except Exception:
                    pass
                t0['done'] = True
                # set embedded current index to the index of t0
                try:
                    self._emb_cur = next(i for i, tt in enumerate(self._emb_targets) if tt is t0)
                except Exception:
                    self._emb_cur = 0
                SQ = getattr(self, '_emb_SQ', 36)
                sx = (t0['x1'] + t0['x2']) // 2 - SQ // 2
                sy = (t0['y1'] + t0['y2']) // 2 - SQ // 2
                try:
                    self._emb_dc.coords(self._emb_sq, sx, sy, sx + SQ, sy + SQ)
                    self._emb_dc.coords(self._emb_st, sx + SQ // 2, sy + SQ // 2)
                except Exception:
                    pass
        except Exception:
            pass

        # Reset run/embedded status labels
        try:
            if hasattr(self, '_tp_run_status'):
                self._tp_run_status.config(text="Idle", fg=self.TEXT)
        except Exception:
            pass

    def _press(self, event):
        hits = set(self.dc.find_overlapping(event.x - 3, event.y - 3,
                                             event.x + 3, event.y + 3))
        if {self._sq_r, self._sq_t} & hits:
            self._dragging = True
            c = self.dc.coords(self._sq_r)
            self._drag_off = (event.x - c[0], event.y - c[1])

    def _move(self, event):
        if not self._dragging:
            return
        SQ = self._SQ
        nx = event.x - self._drag_off[0]
        ny = event.y - self._drag_off[1]
        self.dc.coords(self._sq_r, nx, ny, nx + SQ, ny + SQ)
        self.dc.coords(self._sq_t, nx + SQ // 2, ny + SQ // 2)

    def _release(self, event):
        if not self._dragging:
            return
        self._dragging = False

        c  = self.dc.coords(self._sq_r)
        cx = (c[0] + c[2]) / 2
        cy = (c[1] + c[3]) / 2

        landed = None
        for i, t in enumerate(self.targets):
            if (not t["done"]
                    and t["x1"] < cx < t["x2"]
                    and t["y1"] < cy < t["y2"]):
                landed = i
                break

        if landed is not None:
            t = self.targets[landed]
            # Only allow sequential moves (adjacent numbers). If not adjacent,
            # snap back to previous box and do not mark or light lines.
            try:
                prev_num = self.targets[self._cur_box]['num']
            except Exception:
                prev_num = 1
            landed_num = t.get('num', landed + 1)
            if abs(landed_num - prev_num) == 1:
                # accept move
                self.dc.itemconfig(t["rid"], fill="#1a3828", outline=self.GREEN, width=3)
                self.dc.itemconfig(t["tid"], fill=self.GREEN, text="\u2713")
                t["done"] = True
                self.completed[landed] = True
                # light the single connecting segment between prev and landed
                try:
                    seg_idx = min(prev_num, landed_num) - 1
                    if 0 <= seg_idx < len(self.lines):
                        self.dc.itemconfig(self.lines[seg_idx], fill=self.GREEN)
                except Exception:
                    pass
                self._cur_box = landed
            else:
                # invalid non-sequential move: snap back to previous
                try:
                    cur = self.targets[self._cur_box]
                    sx = (cur["x1"] + cur["x2"]) // 2 - self._SQ // 2
                    sy = (cur["y1"] + cur["y2"]) // 2 - self._SQ // 2
                    self.dc.coords(self._sq_r, sx, sy, sx + self._SQ, sy + self._SQ)
                    self.dc.coords(self._sq_t, sx + self._SQ // 2, sy + self._SQ // 2)
                except Exception:
                    pass

        # snap square to center of whichever box it's now in
        SQ = self._SQ
        cur = self.targets[self._cur_box]
        sx = (cur["x1"] + cur["x2"]) // 2 - SQ // 2
        sy = (cur["y1"] + cur["y2"]) // 2 - SQ // 2
        self.dc.coords(self._sq_r, sx, sy, sx + SQ, sy + SQ)
        self.dc.coords(self._sq_t, sx + SQ // 2, sy + SQ // 2)

        done = sum(self.completed)
        if done == 10:
            self._drag_st.config(text="PASSED!", fg=self.GREEN)
            self.dc.config(highlightbackground=self.GREEN)
        else:
            self._drag_st.config(
                text=f"Drag the square into all 10 boxes  ({done} / 10)",
                fg=self.SUBTEXT)


if __name__ == "__main__":
    TouchpadTester()
