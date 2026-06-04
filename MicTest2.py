import queue
import tempfile
import wave
from pathlib import Path
import numpy as np
import pygame
import sounddevice as sd
import tkinter as tk


class MicrophoneTesterApp:
    RECORD_SECONDS = 5
    SAMPLE_RATE = 44100
    CHANNELS = 1
    BLOCKSIZE = 256
    WAVE_WIDTH = 860
    WAVE_HEIGHT = 300
    METER_WIDTH = 860
    METER_HEIGHT = 20

    def __init__(self, root):
        self.root = root
        self.root.title("Mic Test 2")
        self.root.geometry("900x600")
        self.root.configure(bg="#07111f")

        self.audio_queue = queue.Queue()
        self.recorded_frames = []

        self.latest_audio = np.zeros(self.BLOCKSIZE, dtype=np.float32)
        self.waveform_audio = np.zeros(self.WAVE_WIDTH, dtype=np.float32)
        self.wave_x = np.linspace(
            0, self.WAVE_WIDTH, self.WAVE_WIDTH, dtype=np.float32
        )
        self.wave_points = np.empty(self.WAVE_WIDTH * 2, dtype=np.float32)
        self.wave_points[0::2] = self.wave_x

        self.current_level = 0.0

        self.input_stream = None
        self.is_recording = False
        self.last_clip_path = None
        self.last_recording_audio = None
        self.temp_dir = Path(tempfile.gettempdir())
        self.output_path = self.temp_dir / "mictest2.wav"

        self._pygame_ready = False

        self._build_ui()
        self._init_audio()
        self._schedule_update()

    # ---------------- UI ----------------

    def _build_ui(self):
        frame = tk.Frame(self.root, bg="#0c1728")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.wave_canvas = tk.Canvas(
            frame,
            width=self.WAVE_WIDTH,
            height=self.WAVE_HEIGHT,
            bg="#08111f",
            highlightthickness=0,
        )
        self.wave_canvas.pack(pady=10)

        self.meter_canvas = tk.Canvas(
            frame,
            width=self.METER_WIDTH,
            height=self.METER_HEIGHT,
            bg="#111c30",
            highlightthickness=0,
        )
        self.meter_canvas.pack(pady=10)

        self.wave_line = self.wave_canvas.create_line(
            0, self.WAVE_HEIGHT / 2, self.WAVE_WIDTH, self.WAVE_HEIGHT / 2,
            fill="#67edc3",
            width=2,
            smooth=True,
        )
        self.meter_fill = self.meter_canvas.create_rectangle(
            0, 0, 0, self.METER_HEIGHT, fill="#4de0b0", width=0
        )

        btn_frame = tk.Frame(frame, bg="#0c1728")
        btn_frame.pack(pady=15)

        self.start_button = tk.Button(
            btn_frame,
            text="Start",
            command=self.start_test,
            bg="#5ab18e",
            fg="#08111f",
            font=("Segoe UI", 12, "bold"),
            padx=18,
            pady=10,
        )
        self.start_button.pack(side="left", padx=10)

    # ---------------- AUDIO ----------------

    def _init_audio(self):
        try:
            pygame.mixer.init(frequency=self.SAMPLE_RATE)
            self._pygame_ready = True
        except:
            self._pygame_ready = False

    def _audio_callback(self, indata, frames, time_, status):
        if status:
            return
        self.audio_queue.put(indata[:, 0].copy())

    def _drain_audio_queue(self, keep_for_recording):
        updated = False

        while not self.audio_queue.empty():
            data = self.audio_queue.get()

            if keep_for_recording:
                self.recorded_frames.append(data)

            self.latest_audio = data
            self._update_waveform_audio(data)
            updated = True

        return updated

    def start_test(self):
        if self.is_recording:
            return

        sd.stop()
        self.recorded_frames = []
        self.is_recording = True
        self.start_button.config(state="disabled")

        self.input_stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=1,
            blocksize=self.BLOCKSIZE,
            dtype="float32",
            latency="low",
            callback=self._audio_callback,
        )
        self.input_stream.start()

        self.root.after(self.RECORD_SECONDS * 1000, self.stop_test)

    def stop_test(self):
        self.is_recording = False

        if self.input_stream:
            self.input_stream.stop()
            self.input_stream.close()
            self.input_stream = None

        self._drain_audio_queue(keep_for_recording=True)

        if self.recorded_frames:
            audio = np.concatenate(self.recorded_frames)
            self.last_recording_audio = audio.copy()
            self._write_wav(self.output_path, audio)
            self.last_clip_path = self.output_path
            self.root.after(150, self.play_recording)

        self.start_button.config(state="normal")

    def _write_wav(self, filepath, audio):
        pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
        with wave.open(str(filepath), "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(self.SAMPLE_RATE)
            f.writeframes(pcm.tobytes())

    # ---------------- PROCESS AUDIO ----------------

    def _update_waveform_audio(self, data):
        source_positions = np.linspace(
            0, len(data) - 1, self.WAVE_WIDTH, dtype=np.int32
        )
        target = data[source_positions]
        self.waveform_audio *= 0.35
        self.waveform_audio += target * 0.65

    def _process_audio(self):
        updated = self._drain_audio_queue(keep_for_recording=self.is_recording)

        if not updated:
            self.waveform_audio *= 0.9
            self.current_level *= 0.95
            return

        rms = float(np.sqrt(np.mean(np.square(self.latest_audio))))
        self.current_level = min(1.0, rms * 8.0)

    # ---------------- DRAW ----------------

    def _draw_wave(self):
        center = self.WAVE_HEIGHT / 2
        amplitude = 135
        self.wave_points[1::2] = center - (self.waveform_audio * amplitude)
        self.wave_canvas.coords(self.wave_line, *self.wave_points.tolist())

        self._draw_meter(self.current_level)

    def _draw_meter(self, level):
        fill = int(self.METER_WIDTH * level)
        self.meter_canvas.coords(
            self.meter_fill, 0, 0, fill, self.METER_HEIGHT
        )

    # ---------------- LOOP ----------------

    def _schedule_update(self):
        self._process_audio()
        self._draw_wave()
        self.root.after(8, self._schedule_update)  # faster redraw for smoother motion

    # ---------------- PLAYBACK ----------------

    def play_recording(self):
        if not self.last_clip_path or not self._pygame_ready:
            return

        if self.last_recording_audio is None:
            return

        sd.stop()
        sd.play(self.last_recording_audio, self.SAMPLE_RATE)


# ---------------- RUN ----------------

if __name__ == "__main__":
    root = tk.Tk()
    app = MicrophoneTesterApp(root)
    root.mainloop()
