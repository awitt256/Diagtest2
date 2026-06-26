import ctypes
import threading
import customtkinter as ctk

# ==========================================
# WINDOWS BIOMETRIC FRAMEWORK (WBF) CONSTANTS
# ==========================================
WINBIO_TYPE_FINGERPRINT = 0x00000001
WINBIO_POOL_SYSTEM      = 0x00000001
# Changed from RAW (0x01) to DEFAULT (0x00) to allow normal driver access
WINBIO_FLAG_DEFAULT     = 0x00000000  

class WindowsFingerprintEngine:
    def __init__(self):
        self.winbio = None
        self.session_handle = ctypes.c_uint32(0)
        try:
            self.winbio = ctypes.WinDLL("winbio.dll")
        except Exception:
            self.winbio = None

    def detect_sensor(self):
        """Probes the system to see if a physical fingerprint reader is present."""
        if not self.winbio:
            return False
        
        hr = self.winbio.WinBioOpenSession(
            WINBIO_TYPE_FINGERPRINT,
            WINBIO_POOL_SYSTEM,
            WINBIO_FLAG_DEFAULT,
            None, 0, None,
            ctypes.byref(self.session_handle)
        )
        if hr == 0:
            self.close_session()
            return True
        return False

    def wait_for_touch(self, success_cb, failure_cb):
        """Blocks and waits for a physical finger touch on the reader."""
        try:
            hr = self.winbio.WinBioOpenSession(
                WINBIO_TYPE_FINGERPRINT,
                WINBIO_POOL_SYSTEM,
                WINBIO_FLAG_DEFAULT,
                None, 0, None,
                ctypes.byref(self.session_handle)
            )
            if hr != 0:
                failure_cb(f"Failed to open biometric session. (Code: {hex(hr & 0xFFFFFFFF)})")
                return

            unit_id = ctypes.c_uint32(0)
            reject_detail = ctypes.c_uint32(0)

            # Instruct Windows to capture a sample using the default profile pool
            hr = self.winbio.WinBioCaptureSample(
                self.session_handle,
                1,  # WINBIO_PURPOSE_VERIFY
                WINBIO_FLAG_DEFAULT,
                ctypes.byref(unit_id),
                None, None,
                ctypes.byref(reject_detail)
            )

            if hr == 0:
                success_cb()
            else:
                failure_cb(f"Scan rejected or timed out. (Code: {hex(hr & 0xFFFFFFFF)})")

        except Exception as e:
            failure_cb(f"Driver Error: {str(e)}")
        finally:
            self.close_session()

    def close_session(self):
        if self.winbio and self.session_handle.value != 0:
            self.winbio.WinBioCloseSession(self.session_handle)
            self.session_handle.value = 0


# ==========================================
# GUI APPLICATION
# ==========================================
class WinFingerprintApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Windows Fingerprint Hardware Test")
        self.geometry("450x380")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")

        self.sensor_engine = WindowsFingerprintEngine()

        # UI Elements
        self.title_lbl = ctk.CTkLabel(self, text="Fingerprint Sensor Test", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_lbl.pack(pady=(20, 10))

        self.status_panel = ctk.CTkFrame(self, width=160, height=160, corner_radius=80, fg_color="#2B2B2B")
        self.status_panel.pack_propagate(False)
        self.status_panel.pack(pady=15)

        self.status_lbl = ctk.CTkLabel(self.status_panel, text="READY", font=ctk.CTkFont(size=18, weight="bold"))
        self.status_lbl.place(relx=0.5, rely=0.5, anchor="center")

        self.info_lbl = ctk.CTkLabel(self, text="Checking for Windows Biometric hardware...", font=ctk.CTkFont(size=12))
        self.info_lbl.pack(pady=10)

        self.start_btn = ctk.CTkButton(self, text="Start Test", command=self.run_test, font=ctk.CTkFont(weight="bold"))
        self.start_btn.pack(pady=(10, 20))

        self.verify_hardware()

    def verify_hardware(self):
        if self.sensor_engine.detect_sensor():
            self.info_lbl.configure(text="Windows Fingerprint Reader detected and ready.")
        else:
            self.info_lbl.configure(text="Error: No Windows Biometric Framework sensor found.")
            self.start_btn.configure(state="disabled")

    def run_test(self):
        self.start_btn.configure(state="disabled")
        self.status_panel.configure(fg_color="#3A3A3A")
        self.status_lbl.configure(text="TOUCH SENSOR")
        self.info_lbl.configure(text="Place your finger on the reader chip now...")

        threading.Thread(target=self.hardware_thread_loop, daemon=True).start()

    def hardware_thread_loop(self):
        self.sensor_engine.wait_for_touch(self.handle_pass, self.handle_fail)

    def handle_pass(self):
        self.after(0, lambda: self.status_panel.configure(fg_color="#2ECC71")) 
        self.after(0, lambda: self.status_lbl.configure(text="PASSED", text_color="#FFFFFF"))
        self.after(0, lambda: self.info_lbl.configure(text="Hardware successfully registered a touch scan!"))
        self.after(0, lambda: self.start_btn.configure(state="normal"))

    def handle_fail(self, error_message):
        self.after(0, lambda: self.status_panel.configure(fg_color="#E74C3C")) 
        self.after(0, lambda: self.status_lbl.configure(text="FAILED", text_color="#FFFFFF"))
        self.after(0, lambda: self.info_lbl.configure(text=error_message))
        self.after(0, lambda: self.start_btn.configure(state="normal"))


if __name__ == "__main__":
    app = WinFingerprintApp()
    app.mainloop()