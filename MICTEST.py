import tkinter as tk
from tkinter import ttk, messagebox
import sounddevice as sd
import numpy as np
import threading
import queue
from scipy.io.wavfile import write

# -------------------------------
# Config
# -------------------------------
SAMPLE_RATE = 44100
CHANNELS = 1
RECORD_SECONDS = 6
WAV_FILE = "mic_test.wav"

audio_queue = queue.Queue()
recorded_audio = None
stream = None

# -------------------------------
# Device Discovery
# -------------------------------
devices = sd.query_devices()

input_devices = [
    (i, d['name']) for i, d in enumerate(devices)
    if d['max_input_channels'] > 0
]

output_devices = [
    (i, d['name']) for i, d in enumerate(devices)
    if d['max_output_channels'] > 0
]

# -------------------------------
# Audio Callback (Meter)
# -------------------------------
def audio_callback(indata, frames, time_info, status):
    volume = np.linalg.norm(indata) * 10
    audio_queue.put(volume)

# -------------------------------
# Meter Update
# -------------------------------
def update_meter():
    try:
        level = min(int(audio_queue.get_nowait() * 100), 100)
        meter['value'] = level
    except queue.Empty:
        pass
    root.after(50, update_meter)

# -------------------------------
# Start Monitoring
# -------------------------------
def start_monitor():
    global stream
    try:
        mic_index = int(mic_var.get().split(" | ")[0])
        stream = sd.InputStream(
            device=mic_index,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            callback=audio_callback
        )
        stream.start()
        status.set("Monitoring microphone...")
    except Exception as e:
        messagebox.showerror("Mic Error", str(e))

# -------------------------------
# Stop Monitoring
# -------------------------------
def stop_monitor():
    global stream
    if stream:
        stream.stop()
        stream.close()
        stream = None

# -------------------------------
# Record Audio
# -------------------------------
def record_audio():
    global recorded_audio
    try:
        mic_index = int(mic_var.get().split(" | ")[0])
        sd.default.device = (mic_index, None)
        status.set("Recording...")
        recorded_audio = sd.rec(
            int(SAMPLE_RATE * RECORD_SECONDS),
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='int16'
        )
        sd.wait()
        write(WAV_FILE, SAMPLE_RATE, recorded_audio)
        status.set("Recording complete.")
    except Exception as e:
        messagebox.showerror("Recording Error", str(e))

# -------------------------------
# Playback Audio
# -------------------------------
def play_audio():
    if recorded_audio is None:
        messagebox.showwarning("No Audio", "Record audio first.")
        return
    try:
        speaker_index = int(spk_var.get().split(" | ")[0])
        sd.default.device = (None, speaker_index)
        status.set("Playing back...")
        sd.play(recorded_audio, SAMPLE_RATE)
        sd.wait()
        status.set("Playback finished.")
    except Exception as e:
        messagebox.showerror("Playback Error", str(e))

# -------------------------------
# GUI Setup
# -------------------------------
root = tk.Tk()
root.title("Microphone & Speaker Diagnostic Test")
root.geometry("520x380")
root.resizable(False, False)

tk.Label(root, text="Audio Diagnostic Tool",
         font=("Segoe UI", 14, "bold")).pack(pady=10)

# Microphone dropdown
tk.Label(root, text="Select Microphone").pack()
mic_var = tk.StringVar(value=f"{input_devices[0][0]} | {input_devices[0][1]}")
mic_menu = ttk.Combobox(
    root, textvariable=mic_var,
    values=[f"{i} | {name}" for i, name in input_devices],
    width=60, state="readonly"
)
mic_menu.pack(pady=5)

# Speaker dropdown
tk.Label(root, text="Select Speaker").pack()
spk_var = tk.StringVar(value=f"{output_devices[0][0]} | {output_devices[0][1]}")
spk_menu = ttk.Combobox(
    root, textvariable=spk_var,
    values=[f"{i} | {name}" for i, name in output_devices],
    width=60, state="readonly"
)
spk_menu.pack(pady=5)

# Meter
meter = ttk.Progressbar(root, length=400, maximum=100)
meter.pack(pady=15)

# Buttons
ttk.Button(root, text="▶ Start Mic Monitor", command=start_monitor).pack(pady=3)
ttk.Button(root, text="⏺ Record 6 Seconds",
           command=lambda: threading.Thread(target=record_audio, daemon=True).start()).pack(pady=3)
ttk.Button(root, text="🔊 Play Recording", command=play_audio).pack(pady=3)

status = tk.StringVar(value="Ready")
tk.Label(root, textvariable=status, foreground="gray").pack(pady=15)

# Start meter loop
update_meter()

def on_close():
    stop_monitor()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()