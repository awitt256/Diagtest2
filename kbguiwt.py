import tkinter as tk
import KeyboardTesterGUI2


class KeyboardTesterApp(KeyboardTesterGUI2.KeyboardTesterApp):
    """Keyboard tester variant for hardware suite (no Menu/Exit buttons)."""

    def __init__(self, root):
        super().__init__(root)
        self._remove_menu_and_exit_buttons()

    def _remove_menu_and_exit_buttons(self):
        # Remove only the top control buttons labeled Menu and Exit.
        for widget in self.root.winfo_children():
            self._remove_target_buttons_recursive(widget)

    def _remove_target_buttons_recursive(self, parent):
        try:
            children = parent.winfo_children()
        except Exception:
            return

        for child in children:
            if isinstance(child, tk.Button):
                label = str(child.cget("text")).strip().lower()
                if label in {"menu", "exit"}:
                    try:
                        child.destroy()
                    except Exception:
                        pass
                    continue
            self._remove_target_buttons_recursive(child)
