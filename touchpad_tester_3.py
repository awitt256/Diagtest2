import tkinter as tk
import math

GREY   = "#e0e0e0"
GREEN  = "#4cda4c"
ORANGE = "#FF8C00"
BG     = "#f5f5f5"
RADIUS = 14


def next_color(c):
    return GREEN if (c == GREY or c == ORANGE) else ORANGE


def rounded_rect_points(x1, y1, x2, y2, r, steps=8):
    pts = []
    for cx, cy, start in [
        (x2-r, y1+r, -90),
        (x2-r, y2-r,   0),
        (x1+r, y2-r,  90),
        (x1+r, y1+r, 180),
    ]:
        for i in range(steps+1):
            a = math.radians(start + i * 90 / steps)
            pts.append(cx + r * math.cos(a))
            pts.append(cy + r * math.sin(a))
    return pts


def draw_rounded_rect(canvas, x1, y1, x2, y2, r, fill, outline):
    pts = rounded_rect_points(x1, y1, x2, y2, r)
    canvas.create_polygon(pts, fill=fill, outline=outline, smooth=False)


class TouchpadTester(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Touchpad Tester")
        self.resizable(True, True)
        self.configure(bg=BG)
        self.geometry("520x400")
        self.minsize(440, 360)

        self.show_buttons = tk.BooleanVar(value=False)
        self.pad_state = {
            "left":  {"count": 0, "color": GREY},
            "right": {"count": 0, "color": GREY},
        }
        self.btn_state = {
            "left":  {"count": 0, "color": GREY},
            "right": {"count": 0, "color": GREY},
        }
        self._build_ui()

    def _build_ui(self):
        outer = tk.Frame(self, bg=BG, padx=16, pady=16)
        outer.pack(fill="both", expand=True)

        # top row
        top = tk.Frame(outer, bg=BG)
        top.pack(fill="x", pady=(0, 10))

        self.toggle_canvas = tk.Canvas(top, width=46, height=26, bg=BG,
                                       highlightthickness=0, cursor="hand2")
        self.toggle_canvas.pack(side="left")
        self.toggle_canvas.bind("<Button-1>", self._toggle_buttons)
        self._draw_toggle()

        tk.Label(top, text="Click buttons", bg=BG, fg="#555555",
                 font=("Segoe UI", 11)).pack(side="left", padx=(8, 0))

        tk.Button(top, text="Reset", command=self._reset_all,
                  bg=BG, fg="#555555", relief="groove", bd=1,
                  font=("Segoe UI", 11), cursor="hand2",
                  padx=12, pady=3).pack(side="right")

        # column labels
        lbl_row = tk.Frame(outer, bg=BG)
        lbl_row.pack(fill="x", pady=(0, 6))
        lbl_row.columnconfigure(0, weight=1)
        lbl_row.columnconfigure(1, weight=1)
        for col, text in enumerate(("Left click", "Right click")):
            tk.Label(lbl_row, text=text, bg=BG, fg="#888888",
                     font=("Segoe UI", 10)).grid(row=0, column=col)

        # main grid
        cols = tk.Frame(outer, bg=BG)
        cols.pack(fill="both", expand=True)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=1)
        cols.rowconfigure(1, weight=1)

        self.btn_canvases = {}
        self.pad_canvases = {}

        for col, side in enumerate(("left", "right")):
            padx = (0, 6) if col == 0 else (6, 0)

            bc = tk.Canvas(cols, height=52, bg=BG,
                           highlightthickness=0, cursor="hand2")
            bc.grid(row=0, column=col, padx=padx, pady=(0, 8), sticky="ew")
            bc.bind("<Configure>", lambda e, c=bc, s=side: self._draw_btn(c, s))
            bc.bind("<Button-1>", lambda e, s=side: self._register_btn(s, "left"))
            bc.bind("<Button-3>", lambda e, s=side: self._register_btn(s, "right"))
            bc.grid_remove()
            self.btn_canvases[side] = bc

            pc = tk.Canvas(cols, height=160, bg=BG,
                           highlightthickness=0, cursor="hand2")
            pc.grid(row=1, column=col, padx=padx, sticky="nsew")
            pc.bind("<Configure>", lambda e, c=pc, s=side: self._draw_pad(c, s))
            pc.bind("<Button-1>", lambda e, s=side: self._register_pad(s, "left"))
            pc.bind("<Button-3>", lambda e, s=side: self._register_pad(s, "right"))
            self.pad_canvases[side] = pc

    def _draw_toggle(self):
        c = self.toggle_canvas
        c.delete("all")
        on = self.show_buttons.get()
        track = "#3B6D11" if on else "#bbbbbb"
        pts = rounded_rect_points(0, 1, 46, 25, 12)
        c.create_polygon(pts, fill=track, outline="")
        tx = 24 if on else 2
        c.create_oval(tx, 3, tx+20, 23, fill="white", outline="#cccccc")

    def _draw_btn(self, canvas, side):
        canvas.delete("all")
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 4:
            return
        color = self.btn_state[side]["color"]
        draw_rounded_rect(canvas, 1, 1, w-1, h-1, RADIUS, fill=color, outline="#bbbbbb")
        label = "Left click" if side == "left" else "Right click"
        canvas.create_text(w//2, h//2, text=label,
                           font=("Segoe UI", 12, "bold"), fill="#444444")
        count = str(self.btn_state[side]["count"])
        bx, by = w-22, h-16
        r = 13
        canvas.create_oval(bx-r, by-r, bx+r, by+r, fill="#222222", outline="")
        canvas.create_text(bx, by, text=count, fill="white",
                           font=("Segoe UI", 9, "bold"))

    def _draw_pad(self, canvas, side):
        canvas.delete("all")
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 4:
            return
        color = self.pad_state[side]["color"]
        draw_rounded_rect(canvas, 1, 1, w-1, h-1, RADIUS, fill=color, outline="#bbbbbb")
        count = str(self.pad_state[side]["count"])
        bx, by = w-22, h-18
        r = 13
        canvas.create_oval(bx-r, by-r, bx+r, by+r, fill="#222222", outline="")
        canvas.create_text(bx, by, text=count, fill="white",
                           font=("Segoe UI", 9, "bold"))

    def _toggle_buttons(self, _=None):
        self.show_buttons.set(not self.show_buttons.get())
        self._draw_toggle()
        for side in ("left", "right"):
            if self.show_buttons.get():
                self.btn_canvases[side].grid()
            else:
                self.btn_canvases[side].grid_remove()

    def _register_pad(self, _box, btn_side):
        st = self.pad_state[btn_side]
        st["count"] += 1
        st["color"] = next_color(st["color"])
        self._draw_pad(self.pad_canvases[btn_side], btn_side)

    def _register_btn(self, _box, btn_side):
        st = self.btn_state[btn_side]
        st["count"] += 1
        st["color"] = next_color(st["color"])
        self._draw_btn(self.btn_canvases[btn_side], btn_side)

    def _reset_all(self):
        for side in ("left", "right"):
            self.pad_state[side] = {"count": 0, "color": GREY}
            self.btn_state[side] = {"count": 0, "color": GREY}
            self._draw_pad(self.pad_canvases[side], side)
            self._draw_btn(self.btn_canvases[side], side)


if __name__ == "__main__":
    app = TouchpadTester()
    app.mainloop()
