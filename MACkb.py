import customtkinter as ctk
import sys

# Set dark theme styling to match your diagnostic bench colors
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MacKeyboardTestApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Mac Keyboard Test Suite")
        self.geometry("1100x460")
        self.configure(fg_color="#0d1117")
        
        # Track individual key states globally across layout swaps
        self.press_counts = {}   # Format: {'key_name': int_count}
        self.current_mode = "Compact"  # Mode tracker: "Compact" or "Full"

        # Color mapping array for sequential key presses (Green -> Orange -> Purple)
        self.color_loop = [
            {"bg": "#238636", "border": "#3fb950"},  # 1st press: Premium Green
            {"bg": "#bb8013", "border": "#d29922"},  # 2nd press: Warning Orange
            {"bg": "#6e40c9", "border": "#8957e5"}   # 3rd press: Diagnostic Purple
        ]

        # ------------------------------------------------------------------
        # HEADER CONTROL BAR (With Switch, Reset, & Live Debug Monitor)
        # ------------------------------------------------------------------
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(padx=20, pady=(15, 0), fill="x")
        
        # Left: Title Layout Header
        self.title_lbl = ctk.CTkLabel(
            self.header_frame, 
            text="MAC HARDWARE KEYBOARD DIAGNOSTIC", 
            font=("SF Pro Display", 16, "bold"),
            text_color="#58a6ff"
        )
        self.title_lbl.pack(side="left")
        
        # Right: Actual Toggle Slider Switch
        self.switch_var = ctk.StringVar(value="Compact")
        self.layout_switch = ctk.CTkSwitch(
            self.header_frame,
            text="FULL LAYOUT",
            font=("SF Pro Display", 12, "bold"),
            text_color="#c9d1d9",
            variable=self.switch_var,
            onvalue="Full",
            offvalue="Compact",
            progress_color="#1f6feb",
            command=self.handle_layout_switch
        )
        self.layout_switch.pack(side="right", padx=(15, 0))

        # Right-Center: Physical Master Reset Button
        self.reset_btn = ctk.CTkButton(
            self.header_frame,
            text="RESET BOARD",
            font=("SF Pro Display", 12, "bold"),
            fg_color="#21262d",
            border_color="#f85149", 
            border_width=1,
            hover_color="#30363d",
            text_color="#f85149",
            width=100,
            command=self.reset_entire_board
        )
        self.reset_btn.pack(side="right", padx=(15, 0))

        # Center: Live Debug Key Code Monitor
        self.debug_lbl = ctk.CTkLabel(
            self.header_frame,
            text="DEBUG MONITOR: [ Waiting for key input... ]",
            font=("Consolas", 12, "bold"),
            text_color="#8b949e",
            fg_color="#161b22",
            corner_radius=4,
            padx=12,
            pady=4
        )
        self.debug_lbl.pack(side="right")

        # Main keyboard frame container
        self.keyboard_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.keyboard_frame.pack(padx=20, pady=15, fill="both", expand=True)

        # Build initial layout view
        self.load_layout_definitions()
        self.build_keyboard()

        # Operational native keyboard hooks
        self.bind("<KeyPress>", self.key_pressed)

    def load_layout_definitions(self):
        """Defines layouts with shortened labels and updated physical mapping geometry rules."""
        # --- COMPACT LAYOUT MAP ---
        self.compact_layout = [
            [("esc", 1, 0, 0), ("F1", 1, 0, 1), ("F2", 1, 0, 2), ("F3", 1, 0, 3), ("F4", 1, 0, 4), ("F5", 1, 0, 5), ("F6", 1, 0, 6), ("F7", 1, 0, 7), ("F8", 1, 0, 8), ("F9", 1, 0, 9), ("F10", 1, 0, 10), ("F11", 1, 0, 11), ("F12", 1, 0, 12), ("⌽", 1, 0, 13)],
            [("`", 1, 1, 0), ("1", 1, 1, 1), ("2", 1, 1, 2), ("3", 1, 1, 3), ("4", 1, 1, 4), ("5", 1, 1, 5), ("6", 1, 1, 6), ("7", 1, 1, 7), ("8", 1, 1, 8), ("9", 1, 1, 9), ("0", 1, 1, 10), ("-", 1, 1, 11), ("=", 1, 1, 12), ("delete", 2, 1, 13)],
            [("tab", 2, 2, 0), ("Q", 1, 2, 2), ("W", 1, 2, 3), ("E", 1, 2, 4), ("R", 1, 2, 5), ("T", 1, 2, 6), ("Y", 1, 2, 7), ("U", 1, 2, 8), ("I", 1, 2, 9), ("O", 1, 2, 10), ("P", 1, 2, 11), ("[", 1, 2, 12), ("]", 1, 2, 13), ("\\", 1, 2, 14)],
            [("caps lock", 2, 3, 0), ("A", 1, 3, 2), ("S", 1, 3, 3), ("D", 1, 3, 4), ("F", 1, 3, 5), ("G", 1, 3, 6), ("H", 1, 3, 7), ("J", 1, 3, 8), ("K", 1, 3, 9), ("L", 1, 3, 10), (";", 1, 3, 11), ("'", 1, 3, 12), ("return", 2, 3, 13)],
            [("shift", 3, 4, 0), ("Z", 1, 4, 3), ("X", 1, 4, 4), ("C", 1, 4, 5), ("V", 1, 4, 6), ("B", 1, 4, 7), ("N", 1, 4, 8), ("M", 1, 4, 9), (",", 1, 4, 10), (".", 1, 4, 11), ("/", 1, 4, 12), ("shift ", 2, 4, 13)],
            [("fn", 1, 5, 0), ("ctrl ⌃", 1, 5, 1), ("opt ⌥", 1, 5, 2), ("cmd ⌘", 1, 5, 3), ("space", 5, 5, 4), ("cmd ⌘ ", 1, 5, 9), ("opt ⌥ ", 1, 5, 10), ("◀", 1, 5, 11), ("▲\n▼", 1, 5, 12), ("▶", 1, 5, 13)]
        ]

        # --- FULL LAYOUT MAP ---
        self.full_layout = [
            [("esc", 1, 0, 0), ("F1", 1, 0, 1), ("F2", 1, 0, 2), ("F3", 1, 0, 3), ("F4", 1, 0, 4), ("F5", 1, 0, 5), ("F6", 1, 0, 6), ("F7", 1, 0, 7), ("F8", 1, 0, 8), ("F9", 1, 0, 9), ("F10", 1, 0, 10), ("F11", 1, 0, 11), ("F12", 1, 0, 12), ("⌽", 1, 0, 13),
             ("F13", 1, 0, 15), ("F14", 1, 0, 16), ("F15", 1, 0, 17),
             ("F16", 1, 0, 19), ("F17", 1, 0, 20), ("F18", 1, 0, 21), ("F19", 1, 0, 22)],
            [("`", 1, 1, 0), ("1", 1, 1, 1), ("2", 1, 1, 2), ("3", 1, 1, 3), ("4", 1, 1, 4), ("5", 1, 1, 5), ("6", 1, 1, 6), ("7", 1, 1, 7), ("8", 1, 1, 8), ("9", 1, 1, 9), ("0", 1, 1, 10), ("-", 1, 1, 11), ("=", 1, 1, 12), ("delete", 2, 1, 13),
             ("F13 ", 1, 1, 15), ("home", 1, 1, 16), ("page up", 1, 1, 17),
             ("clear", 1, 1, 19), ("=", 1, 1, 20), ("/", 1, 1, 21), ("*", 1, 1, 22)],
            [("tab", 2, 2, 0), ("Q", 1, 2, 2), ("W", 1, 2, 3), ("E", 1, 2, 4), ("R", 1, 2, 5), ("T", 1, 2, 6), ("Y", 1, 2, 7), ("U", 1, 2, 8), ("I", 1, 2, 9), ("O", 1, 2, 10), ("P", 1, 2, 11), ("[", 1, 2, 12), ("]", 1, 2, 13), ("\\", 1, 2, 14),
             ("del", 1, 2, 15), ("end", 1, 2, 16), ("page down", 1, 2, 17),
             ("7", 1, 2, 19), ("8", 1, 2, 20), ("9", 1, 2, 21), ("-", 1, 2, 22)],
            [("caps lock", 2, 3, 0), ("A", 1, 3, 2), ("S", 1, 3, 3), ("D", 1, 3, 4), ("F", 1, 3, 5), ("G", 1, 3, 6), ("H", 1, 3, 7), ("J", 1, 3, 8), ("K", 1, 3, 9), ("L", 1, 3, 10), (";", 1, 3, 11), ("'", 1, 3, 12), ("return", 2, 3, 13),
             ("4", 1, 3, 19), ("5", 1, 3, 20), ("6", 1, 3, 21), ("+", 1, 3, 22)],
            [("shift", 3, 4, 0), ("Z", 1, 4, 3), ("X", 1, 4, 4), ("C", 1, 4, 5), ("V", 1, 4, 6), ("B", 1, 4, 7), ("N", 1, 4, 8), ("M", 1, 4, 9), (",", 1, 4, 10), (".", 1, 4, 11), ("/", 1, 4, 12), ("shift ", 2, 4, 13),
             ("▲", 1, 4, 16),
             ("1", 1, 4, 19), ("2", 1, 4, 20), ("3", 1, 4, 21), ("enter", 1, 4, 22)],
            # Bottom row alignment: Fixed fn to be to the left of left ctrl ⌃
            [("fn", 1, 5, 0), ("ctrl ⌃", 1, 5, 1), ("opt ⌥", 1, 5, 2), ("cmd ⌘", 1, 5, 3), ("space", 5, 5, 4), ("cmd ⌘ ", 1, 5, 9), ("opt ⌥ ", 1, 5, 10), ("ctrl ⌃ ", 1, 5, 11),
             ("◀", 1, 5, 15), ("▼", 1, 5, 16), ("▶", 1, 5, 17),
             ("0", 2, 5, 19), (".", 1, 5, 21)]
        ]

    def get_subscript_string(self, num):
        """Converts raw integer values to clean right-aligned small button subscripts."""
        subscripts = {"0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄", "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉"}
        return "".join(subscripts.get(char, char) for char in str(num))

    def build_keyboard(self):
        """Clears and renders layout geometry incorporating verified click counts."""
        for widget in self.keyboard_frame.winfo_children():
            widget.destroy()
            
        self.key_widgets = {}
        active_map = self.compact_layout if self.current_mode == "Compact" else self.full_layout

        if self.current_mode == "Full":
            self.keyboard_frame.grid_columnconfigure(14, minsize=15)
            self.keyboard_frame.grid_columnconfigure(18, minsize=15)

        for row in active_map:
            for base_label, col_span, r_idx, c_idx in row:
                k_height = 32 if r_idx == 0 else 44
                row_span = 2 if (base_label == "enter" and self.current_mode == "Full") else 1
                
                lookup_key = base_label.strip().lower()
                
                # Append counter subscripts if historical clicks exist
                display_text = base_label
                if lookup_key in self.press_counts and self.press_counts[lookup_key] > 0:
                    display_text = f"{base_label} {self.get_subscript_string(self.press_counts[lookup_key])}"

                key_btn = ctk.CTkButton(
                    self.keyboard_frame,
                    text=display_text,
                    font=("SF Pro Display", 11 if len(display_text) > 4 else 13),
                    width=50 * col_span,
                    height=k_height if row_span == 1 else 92,
                    fg_color="#161b22",
                    text_color="#c9d1d9",
                    border_color="#30363d",
                    border_width=1,
                    corner_radius=5,
                    hover=False
                )
                key_btn.grid(row=r_idx, column=c_idx, columnspan=col_span, rowspan=row_span, padx=2, pady=3, sticky="nsew")
                self.key_widgets[lookup_key] = key_btn

                # Re-apply structural color states if found
                if lookup_key in self.press_counts and self.press_counts[lookup_key] > 0:
                    current_count = self.press_counts[lookup_key]
                    color_index = (current_count - 1) % 3
                    theme_colors = self.color_loop[color_index]
                    key_btn.configure(
                        fg_color=theme_colors["bg"], 
                        border_color=theme_colors["border"], 
                        text_color="#ffffff"
                    )

    def handle_layout_switch(self):
        """Fired natively by the switch slider component toggle status."""
        self.current_mode = self.switch_var.get()
        if self.current_mode == "Full":
            self.geometry("1460x440")
        else:
            self.geometry("1100x420")
            
        self.build_keyboard()

    def reset_entire_board(self):
        """Wipes historical logs completely, shifting keys back to default dark states."""
        self.press_counts.clear()
        self.debug_lbl.configure(text="DEBUG MONITOR: [ Waiting for key input... ]", text_color="#8b949e")
        self.build_keyboard()

    def key_pressed(self, event):
        """Advances click counts, maps to loop colors, and updates label metrics."""
        key_char = event.keysym.lower()
        vk_code = event.keycode
        
        self.debug_lbl.configure(
            text=f"DEBUG MONITOR: [ keysym: {event.keysym} | vk_code: {vk_code} ]",
            text_color="#58a6ff"
        )
        
        # Core OS Keyboard translate overrides mapped straight to the clean labels
        mapping_overrides = {
            "escape": "esc", "backspace": "delete", "caps_lock": "caps lock",
            "control_l": "ctrl ⌃", "alt_l": "opt ⌥", "alt_r": "opt ⌥ ",
            "win_l": "cmd ⌘", "win_r": "cmd ⌘ ", "space": "space", "control_r": "ctrl ⌃ ",
            "left": "◀", "right": "▶", "up": "▲", "down": "▼", "return": "return",
            "kp_enter": "enter", "kp_0": "0", "kp_1": "1", "kp_2": "2", "kp_3": "3",
            "kp_4": "4", "kp_5": "5", "kp_6": "6", "kp_7": "7", "kp_8": "8", "kp_9": "9",
            "kp_decimal": ".", "kp_add": "+", "kp_subtract": "-", "kp_multiply": "*", "kp_divide": "/"
        }
        
        target_key = mapping_overrides.get(key_char, key_char)

        if self.current_mode == "Compact" and target_key in ["▲", "▼"]:
            target_key = "▲\n▼"

        if target_key in self.key_widgets:
            self.press_counts[target_key] = self.press_counts.get(target_key, 0) + 1
            current_count = self.press_counts[target_key]
            
            color_index = (current_count - 1) % 3
            theme_colors = self.color_loop[color_index]
            
            # Formulate strings binding shortcuts cleanly during append actions
            if "ctrl" in target_key: clean_btn_text = "ctrl ⌃" + (" " if target_key.endswith(" ") else "")
            elif "opt" in target_key: clean_btn_text = "opt ⌥" + (" " if target_key.endswith(" ") else "")
            elif "cmd" in target_key: clean_btn_text = "cmd ⌘" + (" " if target_key.endswith(" ") else "")
            elif target_key == "caps lock": clean_btn_text = "caps lock"
            elif target_key == "page up": clean_btn_text = "page up"
            elif target_key == "page down": clean_btn_text = "page down"
            else:
                clean_btn_text = self.key_widgets[target_key].cget("text").split(" ")[0]
            
            updated_text = f"{clean_btn_text} {self.get_subscript_string(current_count)}"

            self.key_widgets[target_key].configure(
                text=updated_text,
                fg_color=theme_colors["bg"],
                border_color=theme_colors["border"],
                text_color="#ffffff"
            )

if __name__ == "__main__":
    app = MacKeyboardTestApp()
    app.mainloop()