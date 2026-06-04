import math
import queue
import tempfile
import time
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
    BLOCKSIZE = 1024
    SOUND_THRESHOLD = 0.01

    def __init__(self, root):
        self.root = root
        self.root.title("Microphone Test")
        self.root.geometry("980x860")
        self.root.minsize(860, 760)
        self.root.configure(bg="#07111f")

        self.audio_queue = queue.Queue()
        self.recorded_frames = []
        self.latest_audio = np.zeros(self.BLOCKSIZE, dtype=np.float32)
        self.display_audio = np.zeros(self.BLOCKSIZE, dtype=np.float32)
        self.current_level = 0.0
        self.wave_activity = 0.0

        self.input_stream = None
        self.record_start_time = None
        self.countdown_job = None
        self.wave_job = None
        self.stop_job = None
        self.playback_poll_job = None
        self.is_recording = False
        self.last_clip_path = None
        self.temp_dir = Path(tempfile.gettempdir())
        self._pygame_ready = False

        self.state_var = tk.StringVar(value="Idle")
        self.timer_var = tk.StringVar(value=f"{self.RECORD_SECONDS}s")
        self.clip_var = tk.StringVar(value="None")
        self.status_var = tk.StringVar(
            value="Ready. Click start to activate the microphone and begin the 5 second test."
        )

        self._build_ui()
        self._init_audio_playback()
        self._draw_idle_wave()
        self._schedule_wave_update()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        outer = tk.Frame(self.root, bg="#07111f")
        outer.pack(fill="both", expand=True, padx=22, pady=20)

        panel = tk.Frame(
            outer,
            bg="#0c1728",
            highlightbackground="#20324b",
            highlightthickness=1,
        )
        panel.pack(fill="both", expand=True)

        hero = tk.Frame(panel, bg="#0c1728")
        hero.pack(fill="x", padx=24, pady=(20, 12))

        tk.Label(
            hero,
            text="Microphone Test With Live Waveform",
            font=("Segoe UI", 28, "bold"),
            bg="#0c1728",
            fg="#e2ecf8",
        ).pack(anchor="w")

        tk.Label(
            hero,
            text=(
                "Press start to allow microphone access, watch the moving synthesizer-style wave react "
                "to your voice, record for 5 seconds, and then play back the captured audio."
            ),
            font=("Segoe UI", 12),
            bg="#0c1728",
            fg="#8ba5c2",
            justify="left",
            wraplength=860,
        ).pack(anchor="w", pady=(6, 0))

        divider = tk.Frame(panel, bg="#1b2a3e", height=1)
        divider.pack(fill="x", padx=1, pady=(6, 0))

        wave_shell = tk.Frame(
            panel,
            bg="#091523",
            highlightbackground="#17413d",
            highlightthickness=1,
        )
        wave_shell.pack(fill="x", padx=22, pady=(22, 18))

        self.wave_canvas = tk.Canvas(
            wave_shell,
            width=900,
            height=300,
            bg="#08111f",
            bd=0,
            highlightthickness=0,
        )
        self.wave_canvas.pack(fill="x", padx=14, pady=14)

        meter_row = tk.Frame(panel, bg="#0c1728")
        meter_row.pack(fill="x", padx=22, pady=(0, 18))

        tk.Label(
            meter_row,
            text="INPUT LEVEL",
            font=("Segoe UI", 10, "bold"),
            bg="#0c1728",
            fg="#8ba5c2",
        ).pack(side="left", padx=(0, 18))

        meter_wrap = tk.Frame(
            meter_row,
            bg="#111c30",
            highlightbackground="#26354c",
            highlightthickness=1,
        )
        meter_wrap.pack(side="left", fill="x", expand=True)

        self.meter_canvas = tk.Canvas(
            meter_wrap,
            width=720,
            height=18,
            bg="#111c30",
            bd=0,
            highlightthickness=0,
        )
        self.meter_canvas.pack(fill="x")

        stats = tk.Frame(panel, bg="#0c1728")
        stats.pack(fill="x", padx=22, pady=(0, 20))

        self._build_stat_card(stats, "RECORDER STATE", self.state_var).pack(
            side="left", fill="both", expand=True, padx=(0, 8)
        )
        self._build_stat_card(stats, "TIME LEFT", self.timer_var).pack(
            side="left", fill="both", expand=True, padx=8
        )
        self._build_stat_card(stats, "LAST CLIP", self.clip_var).pack(
            side="left", fill="both", expand=True, padx=(8, 0)
        )

        controls = tk.Frame(panel, bg="#0c1728")
        controls.pack(fill="x", padx=22, pady=(0, 20))

        self.start_button = tk.Button(
            controls,
            text="Start 5 Second Test",
            command=self.start_test,
            bg="#5ab18e",
            fg="#08111f",
            activebackground="#75c7a5",
            activeforeground="#08111f",
            font=("Segoe UI", 13, "bold"),
            padx=20,
            pady=14,
            bd=0,
            relief="flat",
            cursor="hand2",
        )
        self.start_button.pack(side="left")

        self.play_button = tk.Button(
            controls,
            text="Play Recorded Clip",
            command=self.play_recording,
            bg="#2b4f80",
            fg="#e2ecf8",
            activebackground="#3d67a1",
            activeforeground="#e2ecf8",
            font=("Segoe UI", 12, "bold"),
            padx=18,
            pady=14,
            bd=0,
            relief="flat",
            cursor="hand2",
            state="disabled",
        )
        self.play_button.pack(side="left", padx=(12, 0))

        self.stop_playback_button = tk.Button(
            controls,
            text="Stop Playback",
            command=self.stop_playback,
            bg="#20324b",
            fg="#e2ecf8",
            activebackground="#324866",
            activeforeground="#e2ecf8",
            font=("Segoe UI", 12, "bold"),
            padx=18,
            pady=14,
            bd=0,
            relief="flat",
            cursor="hand2",
            state="disabled",
        )
        self.stop_playback_button.pack(side="left", padx=(12, 0))

        tk.Label(
            controls,
            text="Make a little noise after starting so you can confirm the mic is reacting.",
            font=("Segoe UI", 11),
            bg="#0c1728",
            fg="#8ba5c2",
        ).pack(side="left", padx=(16, 0))

        self.status_frame = tk.Frame(
            panel,
            bg="#14284a",
            highlightbackground="#2a4e85",
            highlightthickness=1,
        )
        self.status_frame.pack(fill="x", padx=22, pady=(0, 22))

        self.status_label = tk.Label(
            self.status_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 12, "bold"),
            bg="#14284a",
            fg="#d6e5ff",
            justify="left",
            wraplength=860,
            padx=16,
            pady=16,
        )
        self.status_label.pack(anchor="w")

        playback_panel = tk.Frame(
            panel,
            bg="#101b2f",
            highlightbackground="#25354b",
            highlightthickness=1,
        )
        playback_panel.pack(fill="x", padx=22, pady=(0, 22))

        tk.Label(
            playback_panel,
            text="Playback",
            font=("Segoe UI", 13, "bold"),
            bg="#101b2f",
            fg="#e2ecf8",
        ).pack(anchor="w", padx=16, pady=(16, 8))

        self.playback_info = tk.Label(
            playback_panel,
            text="No recorded clip yet.",
            font=("Segoe UI", 11),
            bg="#101b2f",
            fg="#9db2ce",
            padx=16,
            pady=0,
        )
        self.playback_info.pack(anchor="w", pady=(0, 16))

    def _build_stat_card(self, parent, label_text, variable):
        card = tk.Frame(
            parent,
            bg="#111c30",
            highlightbackground="#25354b",
            highlightthickness=1,
            padx=16,
            pady=16,
        )

        tk.Label(
            card,
            text=label_text,
            font=("Segoe UI", 10, "bold"),
            bg="#111c30",
            fg="#8ba5c2",
        ).pack(anchor="w")

        tk.Label(
            card,
            textvariable=variable,
            font=("Segoe UI", 24, "bold"),
            bg="#111c30",
            fg="#e2ecf8",
            pady=12,
        ).pack(anchor="w")
        return card

    def _init_audio_playback(self):
        try:
            pygame.mixer.init(frequency=self.SAMPLE_RATE)
            self._pygame_ready = True
        except pygame.error:
            self._pygame_ready = False
            self.status_var.set(
                "Playback engine could not start. Recording will still work, but playback may be unavailable."
            )

    def _set_status(self, message, is_error=False):
        self.status_var.set(message)
        if is_error:
            self.status_frame.configure(bg="#3b1a24", highlightbackground="#a33a50")
            self.status_label.configure(bg="#3b1a24", fg="#ffd5dc")
        else:
            self.status_frame.configure(bg="#14284a", highlightbackground="#2a4e85")
            self.status_label.configure(bg="#14284a", fg="#d6e5ff")

    def _audio_callback(self, indata, frames, callback_time, status):
        if status:
            self.audio_queue.put(("error", str(status)))
            return

        block = np.copy(indata[:, 0])
        self.audio_queue.put(("audio", block))

    def start_test(self):
        if self.is_recording:
            return

        self.stop_playback()
        self._clear_recording_state()
        self.is_recording = True
        self.record_start_time = time.time()
        self.state_var.set("Listening")
        self.timer_var.set(f"{self.RECORD_SECONDS}s")
        self.clip_var.set("Recording")
        self.start_button.configure(state="disabled", text="Recording...", bg="#4e9d7c")
        self.play_button.configure(state="disabled")
        self.stop_playback_button.configure(state="disabled")
        self.playback_info.configure(text="Recording in progress. Playback will unlock when finished.")
        self._set_status("Microphone is active. Speak, tap, or make noise to watch the wave respond.")

        try:
            self.input_stream = sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                blocksize=self.BLOCKSIZE,
                dtype="float32",
                callback=self._audio_callback,
            )
            self.input_stream.start()
        except Exception as error:
            self.is_recording = False
            self.input_stream = None
            self.state_var.set("Error")
            self.timer_var.set(f"{self.RECORD_SECONDS}s")
            self.clip_var.set("None")
            self.start_button.configure(state="normal", text="Start 5 Second Test", bg="#5ab18e")
            self._set_status(
                f"Microphone access failed: {error}. Check the input device and try again.",
                is_error=True,
            )
            return

        self._schedule_countdown()
        self.stop_job = self.root.after(self.RECORD_SECONDS * 1000, self.stop_test)

    def _schedule_countdown(self):
        if not self.is_recording or self.record_start_time is None:
            return

        elapsed = time.time() - self.record_start_time
        remaining = max(0, self.RECORD_SECONDS - int(elapsed))
        self.timer_var.set(f"{remaining}s")
        self.state_var.set("Recording" if remaining > 0 else "Processing")

        if remaining > 0:
            self.countdown_job = self.root.after(200, self._schedule_countdown)

    def stop_test(self):
        if not self.is_recording:
            return

        self.is_recording = False
        if self.stop_job is not None:
            self.root.after_cancel(self.stop_job)
            self.stop_job = None
        if self.countdown_job is not None:
            self.root.after_cancel(self.countdown_job)
            self.countdown_job = None

        self.state_var.set("Processing")
        self.timer_var.set("0s")
        self._set_status("Finalizing the recording and preparing playback...")

        try:
            if self.input_stream is not None:
                self.input_stream.stop()
                self.input_stream.close()
        except Exception:
            pass
        finally:
            self.input_stream = None

        if not self.recorded_frames:
            self.state_var.set("Error")
            self.clip_var.set("None")
            self.start_button.configure(state="normal", text="Start 5 Second Test", bg="#5ab18e")
            self._set_status("No audio was captured. Try again and make sure the microphone is enabled.", True)
            return

        audio = np.concatenate(self.recorded_frames)
        clip_path = self.temp_dir / "microphone_test_recording.wav"
        self._write_wav(clip_path, audio)
        self.last_clip_path = clip_path

        self.clip_var.set(f"{len(audio) / self.SAMPLE_RATE:.1f}s")
        self.state_var.set("Finished")
        self.start_button.configure(state="normal", text="Run Test Again", bg="#5ab18e")
        self.play_button.configure(state="normal")
        self.playback_info.configure(text=f"Saved to {clip_path}")
        self._set_status("Recording complete. Press Play Recorded Clip to hear what was captured.")

    def _write_wav(self, filepath, audio):
        clipped = np.clip(audio, -1.0, 1.0)
        pcm = (clipped * 32767).astype(np.int16)
        with wave.open(str(filepath), "wb") as wav_file:
            wav_file.setnchannels(self.CHANNELS)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.SAMPLE_RATE)
            wav_file.writeframes(pcm.tobytes())

    def _schedule_wave_update(self):
        self._drain_audio_queue()
        self._draw_live_wave()
        self.wave_job = self.root.after(33, self._schedule_wave_update)

    def _drain_audio_queue(self):
        processed_audio = False
        while True:
            try:
                kind, payload = self.audio_queue.get_nowait()
            except queue.Empty:
                break

            if kind == "error":
                self._set_status(f"Audio stream warning: {payload}", is_error=True)
                continue

            processed_audio = True
            self.latest_audio = payload
            if self.is_recording:
                self.recorded_frames.append(payload.copy())

            rms = float(np.sqrt(np.mean(np.square(payload))))
            peak = float(np.max(np.abs(payload))) if len(payload) else 0.0
            self.current_level = min(1.0, rms * 8.0)
            active_level = max(0.0, rms - self.SOUND_THRESHOLD)
            if active_level > 0:
                self.wave_activity = min(1.0, active_level * 40.0)
                if peak > 0:
                    normalized = payload / peak
                    visible_strength = min(1.0, 0.35 + peak * 6.0)
                    self.display_audio = normalized * visible_strength
            else:
                self.display_audio *= 0.7

        if not processed_audio and not self.is_recording:
            self.current_level *= 0.88
            self.display_audio *= 0.7
        self.wave_activity *= 0.84

    def _draw_idle_wave(self):
        self.wave_canvas.delete("all")
        width = self._canvas_width(self.wave_canvas)
        height = self._canvas_height(self.wave_canvas)
        self._draw_wave_background(width, height)

        points = []
        center_y = height / 2
        for x in range(0, width + 1, 6):
            y = center_y + math.sin((x / max(width, 1)) * math.pi * 7) * 12
            points.extend((x, y))

        if len(points) >= 4:
            self.wave_canvas.create_line(*points, fill="#62e4b3", width=3, smooth=True)
        self._draw_meter(0.0)

    def _draw_live_wave(self):
        width = self._canvas_width(self.wave_canvas)
        height = self._canvas_height(self.wave_canvas)
        self.wave_canvas.delete("all")
        self._draw_wave_background(width, height)

        center_y = height / 2
        active = self.wave_activity

        points_main = []
        points_secondary = []
        if active <= 0.01:
            points_main = [0, center_y, width, center_y]
            points_secondary = [0, center_y, width, center_y]
        else:
            samples = self.display_audio
            if len(samples) < 2:
                points_main = [0, center_y, width, center_y]
                points_secondary = [0, center_y, width, center_y]
            else:
                step = max(1, len(samples) // max(2, width // 3))
                visible = samples[::step]
                if len(visible) < 2:
                    visible = samples

                sample_count = len(visible)
                amplitude = 34 + active * 120
                secondary_scale = amplitude * 0.42

                for i, sample in enumerate(visible):
                    x = (i / max(1, sample_count - 1)) * width
                    y_main = center_y - (float(sample) * amplitude)
                    y_secondary = center_y - (float(sample) * secondary_scale)
                    points_main.extend((x, y_main))
                    points_secondary.extend((x, y_secondary))

        if len(points_secondary) >= 4:
            self.wave_canvas.create_line(*points_secondary, fill="#3f6ca7", width=2, smooth=True)
        if len(points_main) >= 4:
            self.wave_canvas.create_line(*points_main, fill="#67edc3", width=3, smooth=True)
        self._draw_meter(self.current_level)

    def _draw_wave_background(self, width, height):
        self.wave_canvas.create_rectangle(0, 0, width, height, fill="#08111f", outline="")
        self.wave_canvas.create_rectangle(0, 0, width, height, fill="", outline="#0c203a", width=2)
        for y in range(22, height, 22):
            self.wave_canvas.create_line(0, y, width, y, fill="#17263b", width=1)

    def _draw_meter(self, level):
        self.meter_canvas.delete("all")
        width = self._canvas_width(self.meter_canvas)
        height = self._canvas_height(self.meter_canvas)
        self.meter_canvas.create_rectangle(0, 0, width, height, fill="#111c30", outline="")

        fill_width = max(0, min(width, int(width * level)))
        if fill_width > 0:
            step = max(1, fill_width // 60)
            for x in range(0, fill_width, step):
                blend = x / max(fill_width, 1)
                if blend < 0.55:
                    color = "#4de0b0"
                elif blend < 0.82:
                    color = "#5ca9f5"
                else:
                    color = "#f39a52"
                self.meter_canvas.create_rectangle(x, 0, min(fill_width, x + step), height, fill=color, outline=color)

        self.meter_canvas.create_rectangle(0, 0, width - 1, height - 1, outline="#26354c")

    def _canvas_width(self, canvas):
        width = canvas.winfo_width()
        if width <= 1:
            width = int(canvas.cget("width"))
        return max(2, width)

    def _canvas_height(self, canvas):
        height = canvas.winfo_height()
        if height <= 1:
            height = int(canvas.cget("height"))
        return max(2, height)

    def play_recording(self):
        if not self.last_clip_path or not self.last_clip_path.exists():
            self._set_status("There is no recording to play yet.", is_error=True)
            return
        if not self._pygame_ready:
            self._set_status("Playback is unavailable because the audio mixer could not be initialized.", True)
            return

        try:
            pygame.mixer.music.load(str(self.last_clip_path))
            pygame.mixer.music.play()
            self.stop_playback_button.configure(state="normal")
            self._set_status("Playing the recorded clip now.")
            self._schedule_playback_poll()
        except pygame.error as error:
            self._set_status(f"Playback failed: {error}", is_error=True)

    def stop_playback(self):
        if self._pygame_ready:
            try:
                pygame.mixer.music.stop()
            except pygame.error:
                pass
        if self.playback_poll_job is not None:
            self.root.after_cancel(self.playback_poll_job)
            self.playback_poll_job = None
        self.stop_playback_button.configure(state="disabled")

    def _schedule_playback_poll(self):
        if not self._pygame_ready:
            return
        if pygame.mixer.music.get_busy():
            self.playback_poll_job = self.root.after(250, self._schedule_playback_poll)
        else:
            self.playback_poll_job = None
            self.stop_playback_button.configure(state="disabled")

    def _clear_recording_state(self):
        self.recorded_frames = []
        self.latest_audio = np.zeros(self.BLOCKSIZE, dtype=np.float32)
        self.display_audio = np.zeros(self.BLOCKSIZE, dtype=np.float32)
        self.current_level = 0.0
        self.wave_activity = 0.0
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

    def _on_close(self):
        if self.stop_job is not None:
            self.root.after_cancel(self.stop_job)
        if self.countdown_job is not None:
            self.root.after_cancel(self.countdown_job)
        if self.wave_job is not None:
            self.root.after_cancel(self.wave_job)
        if self.playback_poll_job is not None:
            self.root.after_cancel(self.playback_poll_job)

        try:
            if self.input_stream is not None:
                self.input_stream.stop()
                self.input_stream.close()
        except Exception:
            pass

        self.stop_playback()
        if self._pygame_ready:
            try:
                pygame.mixer.quit()
            except pygame.error:
                pass
        self.root.destroy()


if __name__ == "__main__":
    app_root = tk.Tk()
    MicrophoneTesterApp(app_root)
    app_root.mainloop()
