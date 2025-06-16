#!/usr/bin/env python3

import pyaudio
import numpy as np
import time
import whisper
import io
import wave
import os
import json
from typing import Callable, Optional
from openai import OpenAI


class ContinuousDetector:
    def __init__(
        self,
        keyword: str = "computer",
        callback: Callable = None,
        api_key: str = None,
        interrupt_callback: Callable = None,
    ):
        """
        Continuous detection that captures wake word + command in one go

        Args:
            keyword: Keyword to detect (e.g., "computer")
            callback: Function to call with full transcription
            api_key: OpenAI API key for high-quality transcription
            interrupt_callback: Function to call when "stop" is detected
        """
        # Load configuration first to get wake word
        self.config = self.load_config()

        # Use config wake word if no keyword provided
        if keyword == "computer":  # Default value
            self.keyword = self.config["wake_word"]["keyword"].lower()
        else:
            self.keyword = keyword.lower()

        self.callback = callback
        self.interrupt_callback = interrupt_callback
        self.is_listening = False
        self.detection_mode = "WAKE_WORD"  # WAKE_WORD or INTERRUPT

        # Use cloud transcription for better accuracy on commands
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required")

        self.client = OpenAI(api_key=api_key)

        # Load tiny local model just for wake word detection
        print("🔄 Loading local Whisper tiny model for wake word detection...")
        self.local_model = whisper.load_model(self.config["wake_word"]["model"])
        print("✅ Local model loaded")

        # Audio parameters from config
        self.CHUNK = self.config["audio"]["chunk_size"]
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = self.config["audio"]["channels"]
        self.RATE = self.config["audio"]["rate"]
        self.WAKE_WINDOW = 2  # Check for wake word in 2-second chunks
        self.MAX_COMMAND_DURATION = 10  # Maximum recording time
        self.SILENCE_THRESHOLD = self.config["audio"]["silence_threshold"]
        self.SILENCE_DURATION = 1.5  # Seconds of silence to end recording
        self.FIXED_RECORDING_MODE = False  # Use silence detection with tuned threshold
        self.FIXED_DURATION = 4  # Fixed recording duration in seconds

        self.audio = pyaudio.PyAudio()

        # Detection state
        self.last_detection_time = 0
        self.detection_cooldown = 3

        print(f"✅ Continuous detector initialized for '{self.keyword}' (threshold: {self.SILENCE_THRESHOLD})")

    def load_config(self) -> dict:
        """Load configuration from defaults + local overrides"""

        def deep_merge(base: dict, override: dict) -> dict:
            """Deep merge override into base dictionary"""
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        # Load defaults first (always exists in repo)
        with open("config.defaults.json", "r") as f:
            config = json.load(f)
            print("✅ Loaded config.defaults.json")

        # Apply local overrides
        try:
            with open("config.local.json", "r") as f:
                local_config = json.load(f)
                config = deep_merge(config, local_config)
                print(f"✅ Applied local overrides (silence threshold: {config['audio']['silence_threshold']})")
        except FileNotFoundError:
            print("ℹ️ No config.local.json found, using defaults only")
        except json.JSONDecodeError as e:
            print(f"⚠️ Error in config.local.json ({e}), ignoring local overrides")

        return config

    def preprocess_audio(self, audio_data: bytes) -> np.ndarray:
        """Convert audio for Whisper"""
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        return audio_array / 32768.0

    def audio_to_wav_bytes(self, audio_data: bytes) -> bytes:
        """Convert raw audio to WAV format"""
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(self.CHANNELS)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.RATE)
            wav_file.writeframes(audio_data)
        wav_buffer.seek(0)
        return wav_buffer.getvalue()

    def check_for_wake_word_local(self, audio_data: bytes, show_transcription: bool = True) -> bool:
        """Quick local check for wake word"""
        try:
            audio_array = self.preprocess_audio(audio_data)

            # Quick transcription with tiny model
            result = self.local_model.transcribe(
                audio_array,
                language="en",
                fp16=False,
                no_speech_threshold=0.3,  # More sensitive to speech
                condition_on_previous_text=False,  # Don't use context
            )

            text = result["text"].strip().lower()

            # Show transcription if requested
            if show_transcription and text:
                print(f"🎧 Listening: '{text}'")

            # Check for wake word variants from config
            wake_variants = self.config["wake_word"].get("variants", [self.keyword])
            found_wake_word = any(variant in text for variant in wake_variants)

            return found_wake_word

        except Exception:
            return False

    def check_for_stop_command(self, audio_data: bytes, show_transcription: bool = True) -> bool:
        """Quick local check for stop command"""
        try:
            audio_array = self.preprocess_audio(audio_data)

            # Quick transcription with tiny model
            result = self.local_model.transcribe(
                audio_array,
                language="en",
                fp16=False,
                no_speech_threshold=0.3,
                condition_on_previous_text=False,
            )

            text = result["text"].strip().lower()

            # Show transcription if requested
            if show_transcription and text:
                print(f"🛑 Interrupt listening: '{text}'")

            # Check for stop commands from config
            stop_variants = self.config["interrupt"].get("stop_words", ["stop"])
            found_stop_command = any(variant in text for variant in stop_variants)

            return found_stop_command

        except Exception:
            return False

    def transcribe_full_command(self, audio_data: bytes) -> Optional[str]:
        """Transcribe full command with cloud Whisper for accuracy"""
        try:
            wav_data = self.audio_to_wav_bytes(audio_data)
            wav_buffer = io.BytesIO(wav_data)
            wav_buffer.name = "command.wav"

            print("🕐 Starting OpenAI Whisper transcription...")
            start_time = time.time()

            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=wav_buffer,
                response_format="text",
                prompt="The user said 'computer' followed by a workshop command like "
                + "'store hammer in toolbox' or 'where is the screwdriver'.",
            )

            end_time = time.time()
            duration = end_time - start_time
            print(f"⏱️ Whisper transcription took {duration:.2f}s")

            return transcript.strip()

        except Exception as e:
            print(f"⚠️ Transcription error: {e}")
            return None

    def extract_command_from_transcript(self, full_transcript: str) -> str:
        """Extract the command part after the wake word"""
        text = full_transcript.lower()

        # Find where the wake word ends using config variants
        wake_variants = self.config["wake_word"].get("variants", [self.keyword])

        for variant in wake_variants:
            if variant in text:
                # Find the position after the wake word
                pos = text.find(variant) + len(variant)
                command = full_transcript[pos:].strip()

                # Remove common filler words at the start
                command = command.lstrip("., ")

                return command

        # If no wake word found, return the whole thing
        return full_transcript

    def has_sufficient_audio(self, audio_data: bytes) -> bool:
        """Check if audio has enough content"""
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            rms = np.sqrt(np.mean(audio_array.astype(np.float64) ** 2))
            return rms > 200
        except Exception:
            return False

    def calculate_audio_level(self, audio_chunk: bytes) -> float:
        """Calculate RMS level of audio chunk"""
        try:
            audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
            rms = np.sqrt(np.mean(audio_array.astype(np.float64) ** 2))
            return rms
        except Exception:
            return 0.0

    def record_command_with_silence_detection(self, initial_frames: list) -> bytes:
        """Record command until silence is detected or max duration reached"""
        try:
            stream = self.audio.stream  # Use existing stream
            command_frames = initial_frames.copy()

            silence_start_time = None
            total_duration = len(initial_frames) * self.CHUNK / self.RATE
            chunk_duration = self.CHUNK / self.RATE

            print("🔴 Recording command... (stop talking when done)")

            while total_duration < self.MAX_COMMAND_DURATION:
                if not self.is_listening:
                    break

                # Read audio chunk
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                command_frames.append(data)
                total_duration += chunk_duration

                # Calculate audio level
                audio_level = self.calculate_audio_level(data)

                # Check for silence
                if audio_level < self.SILENCE_THRESHOLD:
                    if silence_start_time is None:
                        silence_start_time = total_duration
                    else:
                        silence_duration = total_duration - silence_start_time
                        if silence_duration >= self.SILENCE_DURATION:
                            print(f"✅ Silence detected after {total_duration:.1f}s - ending recording")
                            break
                else:
                    # Reset silence timer when speech detected
                    silence_start_time = None

                # Show progress every 0.5 seconds
                if int(total_duration * 2) % 1 == 0:  # Every 0.5s
                    if silence_start_time:
                        silence_so_far = total_duration - silence_start_time
                        print(f"🔴 Recording... {total_duration:.1f}s (silence: {silence_so_far:.1f}s)")
                    else:
                        print(f"🔴 Recording... {total_duration:.1f}s (level: {audio_level:.0f})")

            if total_duration >= self.MAX_COMMAND_DURATION:
                print(f"⏰ Maximum duration ({self.MAX_COMMAND_DURATION}s) reached")

            return b"".join(command_frames)

        except Exception as e:
            print(f"❌ Error during command recording: {e}")
            return b"".join(command_frames)

    def start_listening(self):
        """Start continuous detection"""
        if self.is_listening:
            return

        self.is_listening = True

        try:
            self.audio.stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
            )
            stream = self.audio.stream

            print(f"🎧 Listening for '{self.keyword}' + command with silence detection...")
            print("💡 Say: 'Computer, store hammer in toolbox drawer three' then pause")
            print("💡 Or: 'Computer, where is the hammer?' then pause")
            print("🔇 Recording stops automatically after 1.5s of silence")
            print("👁️ Live transcription will show what I hear...")

            while self.is_listening:
                if self.detection_mode == "WAKE_WORD":
                    self._handle_wake_word_detection(stream)
                elif self.detection_mode == "INTERRUPT":
                    self._handle_interrupt_detection(stream)
                else:
                    time.sleep(0.1)

            stream.close()

        except Exception as e:
            print(f"❌ Error in continuous detection: {e}")
        finally:
            self.is_listening = False

    def stop_listening(self):
        """Stop detection"""
        print("🛑 Stopping continuous detection...")
        self.is_listening = False

    def _handle_wake_word_detection(self, stream):
        """Handle wake word detection mode"""
        # Check cooldown
        current_time = time.time()
        if current_time - self.last_detection_time < self.detection_cooldown:
            time.sleep(0.1)
            return

        # Record wake word detection window
        wake_frames = []
        wake_frames_needed = int(self.RATE / self.CHUNK * self.WAKE_WINDOW)

        for _ in range(wake_frames_needed):
            if not self.is_listening or self.detection_mode != "WAKE_WORD":
                break
            data = stream.read(self.CHUNK, exception_on_overflow=False)
            wake_frames.append(data)

        if not wake_frames:
            return

        wake_audio = b"".join(wake_frames)

        # Quick check if this might contain wake word
        if not self.has_sufficient_audio(wake_audio):
            return

        # Fast local check for wake word
        if self.check_for_wake_word_local(wake_audio):
            print("🎯 Wake word detected! Recording command with silence detection...")

            # Record command with silence detection
            full_audio = self.record_command_with_silence_detection(wake_frames)

            print("✅ Recording complete, transcribing...")
            full_transcript = self.transcribe_full_command(full_audio)

            if full_transcript:
                print(f"📝 Full transcript: '{full_transcript}'")

                # Send the full transcript (including wake word) to the LLM
                print("🎯 Sending full transcript to LLM")
                self.last_detection_time = current_time

                if self.callback:
                    self.callback(full_transcript)
            else:
                print("❌ Failed to transcribe audio")

            print("-" * 40)

    def _handle_interrupt_detection(self, stream):
        """Handle interrupt detection mode"""
        # Record short audio chunks for interrupt detection
        interrupt_frames = []
        interrupt_frames_needed = int(self.RATE / self.CHUNK * 1.5)  # 1.5 second chunks

        for _ in range(interrupt_frames_needed):
            if not self.is_listening or self.detection_mode != "INTERRUPT":
                break
            try:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                interrupt_frames.append(data)
            except Exception:
                break

        if not interrupt_frames:
            return

        interrupt_audio = b"".join(interrupt_frames)

        # Check if this might contain speech
        if self.has_sufficient_audio(interrupt_audio):
            # Check for stop command (no transcription display during interrupt mode)
            if self.check_for_stop_command(interrupt_audio):
                print("🛑 Stop command detected during TTS!")
                if self.interrupt_callback:
                    self.interrupt_callback()

    def set_mode_wake_word(self):
        """Switch to wake word detection mode"""
        self.detection_mode = "WAKE_WORD"
        print("👂 Ready for next command...")

    def set_mode_interrupt(self):
        """Switch to interrupt detection mode"""
        self.detection_mode = "INTERRUPT"
        print("🛑 Listening for stop commands...")

    def cleanup(self):
        """Clean up resources"""
        self.stop_listening()
        if hasattr(self, "audio"):
            self.audio.terminate()
        print("✅ Continuous detector cleaned up")


def test_continuous_detector():
    """Test continuous detector"""

    def on_command(command):
        print(f"🎉 COMMAND RECEIVED: '{command}'")
        print("(This would now be processed by the smart parser)")

    try:
        print("🧪 Testing Continuous Detector with Silence Detection")
        print("Say: 'Computer, store hammer in toolbox' then stop talking")
        print("Or: 'Computer, where is the hammer?' then stop talking")
        print("🔇 Recording will stop automatically after 1.5s of silence")
        print("-" * 40)

        detector = ContinuousDetector(keyword="computer", callback=on_command)
        detector.start_listening()

    except ValueError as e:
        print(f"⚠️  {e}")
        print("Set OPENAI_API_KEY environment variable to test")
    except KeyboardInterrupt:
        print("\n⏹️  Stopping...")
    finally:
        if "detector" in locals():
            detector.cleanup()


if __name__ == "__main__":
    test_continuous_detector()
