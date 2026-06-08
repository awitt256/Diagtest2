#!/usr/bin/env python3
"""
World Cup 2026 — Group-stage fixtures with win odds (graphical).

Opens a scrollable window showing every group-stage match with each team's
flag, win odds, and a highlighted "Pick" (the favorite).

Groups are the real Final Draw (Washington, D.C., 5 Dec 2025).
Win odds are estimated from approximate FIFA-ranking strength ratings using
the standard Elo expected-score formula. Ratings are a built-in snapshot and
are approximate, so treat the odds as a rough guide, not betting advice.

Flags are fetched from flagcdn.com the first time the app runs, so an internet
connection is needed for the images (the app still works without them — it just
shows the country code instead of a flag).

Usage: python wcscore.py
"""

import base64
import tkinter as tk
from tkinter import font as tkfont
import urllib.request

# Approximate FIFA-ranking strength ratings (snapshot, late 2025).
RATINGS = {
    "Spain": 1875, "Argentina": 1870, "France": 1860, "England": 1820,
    "Portugal": 1770, "Brazil": 1760, "Netherlands": 1750, "Belgium": 1740,
    "Germany": 1720, "Croatia": 1700, "Morocco": 1710, "Colombia": 1690,
    "Uruguay": 1680, "Senegal": 1680, "USA": 1660, "Mexico": 1650,
    "Switzerland": 1650, "Japan": 1650, "Iran": 1630, "South Korea": 1580,
    "Austria": 1580, "Türkiye": 1580, "Ecuador": 1570, "Sweden": 1560,
    "Norway": 1550, "Canada": 1530, "Egypt": 1520, "Scotland": 1500,
    "Czechia": 1500, "Algeria": 1500, "Australia": 1500, "Tunisia": 1490,
    "Ivory Coast": 1490, "Bosnia-Herzegovina": 1490, "DR Congo": 1480,
    "Paraguay": 1480, "Ghana": 1450, "Uzbekistan": 1440, "Panama": 1430,
    "Qatar": 1430, "South Africa": 1430, "Saudi Arabia": 1410,
    "Cape Verde": 1390, "Iraq": 1380, "Jordan": 1340, "Curaçao": 1300,
    "New Zealand": 1280, "Haiti": 1280,
}

# 2026 FIFA World Cup Final Draw — 12 groups of 4.
GROUPS = {
    "A": ["Mexico", "South Korea", "South Africa", "Czechia"],
    "B": ["Canada", "Switzerland", "Qatar", "Bosnia-Herzegovina"],
    "C": ["Brazil", "Morocco", "Scotland", "Haiti"],
    "D": ["USA", "Paraguay", "Australia", "Türkiye"],
    "E": ["Germany", "Ivory Coast", "Ecuador", "Curaçao"],
    "F": ["Netherlands", "Sweden", "Tunisia", "Japan"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

# ISO 3166-1 codes used by flagcdn.com (gb-eng / gb-sct are special-cased).
CODES = {
    "Mexico": "mx", "South Korea": "kr", "South Africa": "za", "Czechia": "cz",
    "Canada": "ca", "Switzerland": "ch", "Qatar": "qa",
    "Bosnia-Herzegovina": "ba", "Brazil": "br", "Morocco": "ma",
    "Scotland": "gb-sct", "Haiti": "ht", "USA": "us", "Paraguay": "py",
    "Australia": "au", "Türkiye": "tr", "Germany": "de", "Ivory Coast": "ci",
    "Ecuador": "ec", "Curaçao": "cw", "Netherlands": "nl", "Sweden": "se",
    "Tunisia": "tn", "Japan": "jp", "Belgium": "be", "Egypt": "eg",
    "Iran": "ir", "New Zealand": "nz", "Spain": "es", "Cape Verde": "cv",
    "Saudi Arabia": "sa", "Uruguay": "uy", "France": "fr", "Senegal": "sn",
    "Iraq": "iq", "Norway": "no", "Argentina": "ar", "Algeria": "dz",
    "Austria": "at", "Jordan": "jo", "Portugal": "pt", "DR Congo": "cd",
    "Uzbekistan": "uz", "Colombia": "co", "England": "gb-eng", "Croatia": "hr",
    "Ghana": "gh", "Panama": "pa",
}

# Colors.
BG = "#0f1b2d"
CARD = "#16263f"
HEADER = "#1f6feb"
TEXT = "#e6edf3"
MUTED = "#8b98a5"
PICK = "#2ea043"


def win_odds(team_a, team_b):
    """Return (p_a, p_b) win probabilities for team_a vs team_b."""
    ra = RATINGS.get(team_a, 1450)
    rb = RATINGS.get(team_b, 1450)
    p_a = 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))
    return p_a, 1.0 - p_a


def load_flags():
    """Download each team's flag PNG once; return {team: PhotoImage or None}."""
    flags = {}
    for team, code in CODES.items():
        try:
            url = f"https://flagcdn.com/w40/{code}.png"
            req = urllib.request.Request(url, headers={"User-Agent": "wcscore"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read()
            flags[team] = tk.PhotoImage(data=base64.b64encode(raw))
        except Exception:
            flags[team] = None
    return flags


def build_match(parent, a, b, flags, f_team, f_pct, f_pick):
    """Render one match card into parent."""
    p_a, p_b = win_odds(a, b)
    pick, pick_pct = (a, p_a) if p_a >= p_b else (b, p_b)

    card = tk.Frame(parent, bg=CARD, padx=14, pady=10)
    card.pack(fill="x", padx=12, pady=5)

    row = tk.Frame(card, bg=CARD)
    row.pack(fill="x")

    def side(team, pct, favored):
        col = tk.Frame(row, bg=CARD)
        if flags.get(team) is not None:
            tk.Label(col, image=flags[team], bg=CARD).pack(side="left", padx=(0, 8))
        else:
            tk.Label(col, text=f"[{CODES.get(team, '??')}]", fg=MUTED,
                     bg=CARD, font=f_pct).pack(side="left", padx=(0, 8))
        name_color = PICK if favored else TEXT
        tk.Label(col, text=team, fg=name_color, bg=CARD,
                 font=f_team).pack(side="left")
        tk.Label(col, text=f"  {pct * 100:.0f}%", fg=name_color, bg=CARD,
                 font=f_pct).pack(side="left")
        return col

    side(a, p_a, pick == a).pack(side="left")
    tk.Label(row, text="vs", fg=MUTED, bg=CARD, font=f_team).pack(side="left", padx=16)
    side(b, p_b, pick == b).pack(side="left")

    tk.Label(card, text=f"Pick:  {pick}  ({pick_pct * 100:.0f}%)",
             fg=PICK, bg=CARD, font=f_pick).pack(anchor="w", pady=(6, 0))


def main():
    root = tk.Tk()
    root.title("World Cup 2026 — Match Odds")
    root.geometry("640x760")
    root.configure(bg=BG)

    f_title = tkfont.Font(family="Segoe UI", size=18, weight="bold")
    f_group = tkfont.Font(family="Segoe UI", size=13, weight="bold")
    f_team = tkfont.Font(family="Segoe UI", size=11, weight="bold")
    f_pct = tkfont.Font(family="Segoe UI", size=11)
    f_pick = tkfont.Font(family="Segoe UI", size=10, weight="bold")

    tk.Label(root, text="World Cup 2026 — Match Odds", fg=TEXT, bg=BG,
             font=f_title).pack(pady=(14, 4))
    status = tk.Label(root, text="Downloading flags…", fg=MUTED, bg=BG, font=f_pct)
    status.pack()
    root.update()

    flags = load_flags()
    status.config(text="Odds are rough estimates from FIFA-ranking ratings.")

    # Scrollable area.
    canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=BG)
    inner.bind("<Configure>",
               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw", width=620)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True, padx=(6, 0))
    scrollbar.pack(side="right", fill="y")
    canvas.bind_all("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

    for letter, teams in GROUPS.items():
        tk.Label(inner, text=f"Group {letter}", fg=TEXT, bg=HEADER,
                 font=f_group, anchor="w", padx=12, pady=4).pack(
                     fill="x", padx=12, pady=(12, 2))
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                build_match(inner, teams[i], teams[j], flags,
                            f_team, f_pct, f_pick)

    root.mainloop()


if __name__ == "__main__":
    main()
