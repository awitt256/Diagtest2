import tkinter as tk
from tkinter import ttk, messagebox
import sounddevice as sd
import numpy as np
import threading
import queue
import os
from scipy.io.wavfile import write

SAMPLE_RATE = 44100
CHANNELS = 1
RECORD_SECONDS = 6
WAV_FILE = "mic_test.wav"


def auto_select_speaker(devices):
    if not devices:
        return "Select Speakers"

    internal_keywords = [
        "internal", "built-in", "builtin", "realtek",
        "conexant", "high definition audio", "hd audio"
    ]

    for idx, name in devices:
        lname = name.lower()
        if any(keyword in lname for keyword in internal_keywords):
            return f"{idx} | {name}"

    for idx, name in devices:
        if "speaker" in name.lower():
            return f"{idx} | {name}"

    for idx, name in devices:
        if "usb" in name.lower() or "headset" in name.lower():
            return f"{idx} | {name}"

    return f"{devices[0][0]} | {devices[0][1]}"


class AudioDiagnosticApp:
    def __init__(self, parent, menu_callback=None):
        self.parent = parent
        self.menu_callback = menu_callback
        self.audio_queue = queue.Queue()
        self.recorded_audio = None
        self.stream = None
        self.status = tk.StringVar(value="Ready")

        self.devices = sd.query_devices()
        self.input_devices = [
            (i, d["name"]) for i, d in enumerate(self.devices)
            if d["max_input_channels"] > 0
        ]
        self.output_devices = [
            (i, d["name"]) for i, d in enumerate(self.devices)
            if d["max_output_channels"] > 0 and "microsoft sound mapper" not in d["name"].lower()
        ]

        if not self.input_devices:
            raise RuntimeError("No microphone input devices were detected.")
        if not self.output_devices:
            raise RuntimeError("No speaker output devices were detected.")

        self.build_ui()
        self.update_meter()

    def set_menu_callback(self, callback):
        self.menu_callback = callback

    def build_ui(self):
        self.parent.configure(bg="#101723")
        container = tk.Frame(self.parent, bg="#101723")
        container.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(
            container, text="Audio Diagnostic Test",
            font=("Segoe UI", 16, "bold"), bg="#101723", fg="white"
        ).pack(pady=(0, 12))

        # Use system default input/output devices; explicit selection is redundant
        tk.Label(container, text="Microphone monitor (uses system default input)", bg="#101723", fg="#d8e2f2").pack()

        self.meter = ttk.Progressbar(container, length=440, maximum=100)
        self.meter.pack(pady=15)

        ttk.Button(container, text="Start Mic Monitor", command=self.start_monitor).pack(pady=3)
        ttk.Button(
            container, text="Record 6 Seconds",
            command=lambda: threading.Thread(target=self.record_audio, daemon=True).start()
        ).pack(pady=3)
        ttk.Button(container, text="Play Recording", command=self.play_audio).pack(pady=3)

        tk.Label(container, textvariable=self.status, foreground="gray", bg="#101723").pack(pady=(14, 10))

        button_row = tk.Frame(container, bg="#101723")
        button_row.pack(pady=(4, 6))
        ttk.Button(button_row, text="Stop Monitor", command=self.stop_monitor).pack(side="left", padx=6)
        ttk.Button(button_row, text="Back to Main Menu", command=self.on_menu).pack(side="left", padx=6)

    def on_menu(self):
        self.stop_monitor()
        if callable(self.menu_callback):
            self.menu_callback()

    def audio_callback(self, indata, frames, time_info, status):
        try:
            arr = np.asarray(indata, dtype=np.float32)
            # compute RMS (root mean square) for level
            rms = float(np.sqrt(np.mean(np.square(arr))))
            self.audio_queue.put(rms)
        except Exception:
            try:
                self.audio_queue.put(0.0)
            except Exception:
                pass

    def update_meter(self):
        # Drain the queue and keep the most recent value to avoid backlog/lag
        last = None
        try:
            while True:
                last = self.audio_queue.get_nowait()
        except queue.Empty:
            pass

        if last is not None:
            try:
                level = min(int(last * 100), 100)
                self.meter["value"] = level
            except Exception:
                pass

        if self.parent.winfo_exists():
            # Poll faster for smoother updates
            self.parent.after(25, self.update_meter)

    def start_monitor(self):
        self.stop_monitor()
        try:
            # Use system default input device for monitoring
            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                blocksize=1024,
                latency='low',
                dtype='float32',
                channels=CHANNELS,
                callback=self.audio_callback
            )
            self.stream.start()
            self.status.set("Monitoring microphone...")
        except Exception as exc:
            messagebox.showerror("Microphone Error", str(exc))

    def stop_monitor(self):
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

    def record_audio(self):
        try:
            # Record using the default input device
            self.status.set("Recording...")
            self.recorded_audio = sd.rec(
                int(SAMPLE_RATE * RECORD_SECONDS),
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16"
            )
            sd.wait()
            write(os.path.join(os.path.dirname(__file__), WAV_FILE), SAMPLE_RATE, self.recorded_audio)
            self.status.set("Recording complete.")
        except Exception as exc:
            messagebox.showerror("Recording Error", str(exc))

    def play_audio(self):
        if self.recorded_audio is None:
            messagebox.showwarning("No Recording", "Please record audio first.")
            return
        try:
            # Play back using default output device
            self.status.set("Playing back...")
            sd.play(self.recorded_audio, SAMPLE_RATE)
            sd.wait()
            self.status.set("Playback finished.")
        except Exception as exc:
            messagebox.showerror("Playback Error", str(exc))


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Audio Diagnostic Tool")
    root.geometry("640x460")
    root.resizable(False, False)
    app = AudioDiagnosticApp(root)
    root.mainloop()
