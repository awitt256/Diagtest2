import tkinter as tk
from tkinter import font as tkfont
import psutil


# ── Live battery detection ────────────────────────────────────────────────────

def get_battery_info():
    """Returns (level, health, is_charging, detected)."""
    b = psutil.sensors_battery()
    if b is None:
        return None, None, False, False
    level = round(b.percent)
    charging = b.power_plugged
    # psutil doesn't expose raw health; we treat 100% as max-normal.
    # If you have a system tool that gives real health, plug it in here.
    health = 100
    return level, health, charging, True


LEVEL, HEALTH, IS_CHARGING, DETECTED = get_battery_info()
APPROVAL_LIMIT = 60


# ── Theme resolution ──────────────────────────────────────────────────────────

def resolve_theme(detected, level, health):
    if not detected or level is None:
        return "red"
    if health is not None and 101 <= health <= 110:
        return "orange"
    if level < APPROVAL_LIMIT:
        return "red"
    return "green"


THEME_NAME = resolve_theme(DETECTED, LEVEL, HEALTH)

THEMES = {
    "green": {
        "bg": "#3a9a3c",
        "card_dark": "#2e7d31",
        "card_light": "#4caf50",
        "pill_base": (0x66, 0xbb, 0x66),
        "pill_txt": "#1b5e20",
        "text_accent": "#a5d6a7",
    },
    "red": {
        "bg": "#c62828",
        "card_dark": "#8e0000",
        "card_light": "#ef5350",
        "pill_base": (0xbb, 0x33, 0x33),
        "pill_txt": "#ffffff",
        "text_accent": "#ffcdd2",
    },
    "orange": {
        "bg": "#e65100",
        "card_dark": "#bf360c",
        "card_light": "#ff7043",
        "pill_base": (0xcc, 0x66, 0x00),
        "pill_txt": "#ffffff",
        "text_accent": "#ffe0b2",
    },
}

T = THEMES[THEME_NAME]
TEXT_WHITE = "#ffffff"
BAR_COLOURS = ["#f44336", "#f44336", "#ff9800", "#ff9800", "#8bc34a", "#8bc34a"]


class BatteryWidget(tk.Frame):
    def __init__(self, embed_host=None):
        """Initialize battery widget. Embed in the provided host frame."""
        # Don't call super().__init__() as tk.Tk, we're a Frame now
        self._embedded = True

        # Store reference to the root window from embed_host's master
        self._root = embed_host.winfo_toplevel()

        # Initialize as a Frame inside the host
        super().__init__(embed_host, bg=T["bg"], padx=18, pady=14)
        self.pack(fill="both", expand=True)

        # Configure the host
        embed_host.configure(bg=T["bg"])

        self.f_title = tkfont.Font(family="Helvetica", size=11, weight="bold")
        self.f_label = tkfont.Font(family="Helvetica", size=9, weight="bold")
        self.f_value = tkfont.Font(family="Helvetica", size=16, weight="bold")
        self.f_pill = tkfont.Font(family="Helvetica", size=9, weight="bold")

        self._charge_alpha = 0.0
        self._charge_dir = 1
        self._anim_running = True

        self._build_ui()
        self._animate()
        self._refresh()  # live polling

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        BG = T["bg"]
        self._outer = tk.Frame(self, bg=BG, padx=18, pady=14)
        self._outer.pack()

        # Title
        title_row = tk.Frame(self._outer, bg=BG)
        title_row.pack(fill="x", pady=(0, 4))
        tk.Label(title_row, text=f"Total Batteries: {1 if DETECTED else 0}",
                 bg=BG, fg=TEXT_WHITE, font=self.f_title).pack(anchor="center")

        # Status banner
        banner_text, banner_colour = self._status_banner()
        self._banner_lbl = tk.Label(title_row, text=banner_text,
                                    bg=BG, fg=banner_colour,
                                    font=self.f_label)
        self._banner_lbl.pack(anchor="center", pady=(0, 6))

        # Content row
        content = tk.Frame(self._outer, bg=BG)
        content.pack()

        # Battery canvas
        self.canvas = tk.Canvas(content, width=90, height=130,
                                bg=BG, highlightthickness=0)
        self.canvas.grid(row=0, column=0, padx=(0, 18))
        self._draw_battery()

        # Stat cards + pill
        cards_frame = tk.Frame(content, bg=BG)
        cards_frame.grid(row=0, column=1, sticky="n")

        top_cards = tk.Frame(cards_frame, bg=BG)
        top_cards.pack()

        al_text = f"{APPROVAL_LIMIT}%"
        h_text = f"{HEALTH}%" if DETECTED else "N/A"
        lv_text = f"{LEVEL}%" if DETECTED else "N/A"

        self._make_card(top_cards, "Approval\nLimit", al_text,
                        TEXT_WHITE, dark=True).pack(side="left", padx=(0, 4))
        self._make_card(top_cards, "Health", h_text, T["text_accent"]).pack(side="left", padx=(0, 4))
        self._make_card(top_cards, "Level", lv_text, T["text_accent"]).pack(side="left")

        # Charging pill (only shown when actually charging)
        pill_frame = tk.Frame(cards_frame, bg=BG)
        pill_frame.pack(pady=(10, 0))
        self.pill_canvas = tk.Canvas(pill_frame, width=130, height=28,
                                     bg=BG, highlightthickness=0)
        self.pill_canvas.pack()
        self._draw_pill()

    def _status_banner(self):
        if not DETECTED:
            return ("⚠  Battery Not Detected", "#ffeb3b")
        if THEME_NAME == "orange":
            return (f"⚠  Health Overcharge Warning ({HEALTH}%)", "#fff9c4")
        if THEME_NAME == "red":
            return (f"⚠  Level Below Approval Limit ({LEVEL}%)", "#ffeb3b")
        return ("✔  Battery OK", "#c8e6c9")

    def _make_card(self, parent, label_text, value_text, value_colour, dark=False):
        bg = T["card_dark"] if dark else T["card_light"]
        f = tk.Frame(parent, bg=bg, padx=10, pady=8, relief="flat", bd=0)
        tk.Label(f, text=label_text, bg=bg, fg=TEXT_WHITE,
                 font=self.f_label, justify="center").pack()
        tk.Label(f, text=value_text, bg=bg, fg=value_colour,
                 font=self.f_value).pack()
        return f

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw_battery(self):
        c = self.canvas
        c.delete("all")
        W, H = 90, 130
        bx1, bx2 = 12, 78
        by1, by2 = 18, 118
        r = 6

        nw = 20
        nx1 = (W - nw) // 2
        c.create_rectangle(nx1, 8, nx1 + nw, by1 + 2,
                           fill="#bdbdbd", outline="", width=0)
        self._rounded_rect(c, bx1, by1, bx2, by2, r,
                           fill="#e0e0e0", outline="#bdbdbd", width=2)

        n_bars = 6
        padding = 5
        gap = 3
        bar_h = ((by2 - by1) - 2 * padding - (n_bars - 1) * gap) // n_bars
        bar_w = (bx2 - bx1) - 2 * padding
        bars_lit = max(0, min(n_bars, round((LEVEL or 0) / 100 * n_bars))) if DETECTED else 0

        for i in range(n_bars):
            y2 = by2 - padding - i * (bar_h + gap)
            y1 = y2 - bar_h
            x1 = bx1 + padding
            x2 = x1 + bar_w
            colour = BAR_COLOURS[i] if i < bars_lit else "#d0d0d0"
            self._rounded_rect(c, x1, y1, x2, y2, 3,
                               fill=colour, outline="", width=0)

        lx, ly = W // 2, (by1 + by2) // 2
        self._bolt = c.create_text(lx, ly, text="⚡",
                                   font=("Helvetica", 22), fill="#fff176")

    def _draw_pill(self, alpha=0.0):
        c = self.pill_canvas
        c.delete("all")
        W, H = 130, 28

        if not DETECTED:
            # Grey "Not Detected" pill
            self._rounded_rect(c, 0, 0, W, H, H // 2,
                               fill="#777777", outline="", width=0)
            c.create_text(W // 2, H // 2 + 1,
                          text="✖  Not Detected",
                          font=self.f_pill, fill="#ffffff")
            return

        if IS_CHARGING:
            br, bg, bb = T["pill_base"]
            lo, hi = 0.85, 1.0
            s = lo + (hi - lo) * alpha
            fill = f"#{min(255, int(br * s)):02x}{min(255, int(bg * s)):02x}{min(255, int(bb * s)):02x}"
            self._rounded_rect(c, 0, 0, W, H, H // 2,
                               fill=fill, outline="", width=0)
            c.create_text(W // 2, H // 2 + 1,
                          text="⚡  Charging",
                          font=self.f_pill, fill=T["pill_txt"])
        else:
            # Not charging — show discharging pill
            self._rounded_rect(c, 0, 0, W, H, H // 2,
                               fill=T["card_dark"], outline="", width=0)
            c.create_text(W // 2, H // 2 + 1,
                          text="🔋  On Battery",
                          font=self.f_pill, fill="#ffffff")

    @staticmethod
    def _rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
               x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
               x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return canvas.create_polygon(pts, smooth=True, **kwargs)

    # ── Animation ─────────────────────────────────────────────────────────────

    def _animate(self):
        if not self._anim_running:
            return
        self._charge_alpha += 0.04 * self._charge_dir
        if self._charge_alpha >= 1.0:
            self._charge_alpha = 1.0;
            self._charge_dir = -1
        elif self._charge_alpha <= 0.0:
            self._charge_alpha = 0.0;
            self._charge_dir = 1
        self._draw_pill(self._charge_alpha)
        grey = int(0xf1 * (0.5 + 0.5 * self._charge_alpha))
        yell = int(0x76 * (0.7 + 0.3 * self._charge_alpha))
        try:
            self.canvas.itemconfig(self._bolt, fill=f"#{grey:02x}{grey:02x}{yell:02x}")
        except Exception:
            pass
        self.after(30, self._animate)

    def _refresh(self):
        """Re-read battery every 10 s and rebuild UI if state changed."""
        global LEVEL, HEALTH, IS_CHARGING, DETECTED, THEME_NAME, T
        new_level, new_health, new_charging, new_detected = get_battery_info()
        changed = (new_level != LEVEL or new_charging != IS_CHARGING
                   or new_detected != DETECTED)
        if changed:
            LEVEL, HEALTH, IS_CHARGING, DETECTED = new_level, new_health, new_charging, new_detected
            THEME_NAME = resolve_theme(DETECTED, LEVEL, HEALTH)
            T = THEMES[THEME_NAME]
            self.configure(bg=T["bg"])
            for w in self._outer.winfo_children():
                w.destroy()
            self._outer.configure(bg=T["bg"])
            self._build_ui()
        if self._anim_running:
            self.after(10_000, self._refresh)

    def _on_close(self):
        """Stop animations and clean up."""
        self._anim_running = False
        self.destroy()


if __name__ == "__main__":
    # Standalone mode: create a Tk window and embed BatteryWidget in it
    root = tk.Tk()
    root.title("Battery Monitor")
    root.resizable(False, False)
    root.configure(bg=T["bg"])

    app = BatteryWidget(embed_host=root)
    app.pack(fill="both", expand=True)

    root.mainloop()