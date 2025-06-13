#!/usr/bin/env python3

import pyaudio
import numpy as np
import threading
import time
import io
import wave
import os
from typing import Callable, Optional
from openai import OpenAI

class ImprovedKeywordDetector:
    def __init__(self, keyword: str = "computer", callback: Callable = None, api_key: str = None):
        """
        Improved keyword detection with better audio handling
        
        Args:
            keyword: Keyword to detect (e.g., "computer")
            callback: Function to call when keyword is detected
            api_key: OpenAI API key for transcription
        """
        self.keyword = keyword.lower()
        self.callback = callback
        self.is_listening = False
        
        # OpenAI client for transcription
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required for keyword detection")
        
        self.client = OpenAI(api_key=api_key)
        
        # Audio parameters - optimized for speech
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.LISTEN_DURATION = 4  # Longer duration for better transcription
        
        self.audio = pyaudio.PyAudio()
        
        # Detection state
        self.last_detection_time = 0
        self.detection_cooldown = 3  # Seconds between detections
        
        # Audio processing settings
        self.min_rms_threshold = 100  # Lower threshold
        self.max_silence_ratio = 0.8  # Allow up to 80% silence
        
        print(f"✅ Improved keyword detector initialized for '{keyword}'")
    
    def audio_to_wav_bytes(self, audio_data: bytes) -> bytes:
        """Convert raw audio to WAV format"""
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(self.CHANNELS)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.RATE)
            wav_file.writeframes(audio_data)
        wav_buffer.seek(0)
        return wav_buffer.getvalue()
    
    def preprocess_audio(self, audio_data: bytes) -> bytes:
        """Clean up audio data"""
        # Convert to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        
        # Normalize audio
        if np.max(np.abs(audio_array)) > 0:
            audio_array = audio_array / np.max(np.abs(audio_array)) * 16000
        
        # Convert back to int16
        audio_array = audio_array.astype(np.int16)
        
        return audio_array.tobytes()
    
    def transcribe_audio_chunk(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio chunk using Whisper API"""
        try:
            # Preprocess audio
            clean_audio = self.preprocess_audio(audio_data)
            
            wav_data = self.audio_to_wav_bytes(clean_audio)
            wav_buffer = io.BytesIO(wav_data)
            wav_buffer.name = "audio.wav"
            
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=wav_buffer,
                response_format="text",
                prompt="The user is saying the word 'computer' to activate a voice assistant."  # Help Whisper
            )
            
            return transcript.strip().lower()
            
        except Exception as e:
            print(f"⚠️ Transcription error: {e}")
            return None
    
    def analyze_audio_quality(self, audio_data: bytes) -> dict:
        """Analyze if audio is worth transcribing"""
        try:
            # Convert to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Calculate metrics safely
            audio_float = audio_array.astype(np.float64)
            
            # RMS calculation
            mean_square = np.mean(audio_float ** 2)
            rms = np.sqrt(mean_square) if mean_square > 0 else 0
            
            # Peak amplitude
            max_amplitude = np.max(np.abs(audio_array))
            
            # Silence ratio
            silence_threshold = 100
            silence_samples = np.sum(np.abs(audio_array) < silence_threshold)
            silence_ratio = silence_samples / len(audio_array)
            
            return {
                "rms": rms,
                "max_amplitude": max_amplitude,
                "silence_ratio": silence_ratio,
                "duration": len(audio_array) / self.RATE,
                "worth_transcribing": (rms > self.min_rms_threshold and 
                                     silence_ratio < self.max_silence_ratio and
                                     max_amplitude > 200)
            }
        except Exception as e:
            print(f"⚠️ Audio analysis error: {e}")
            return {"worth_transcribing": False}
    
    def start_listening(self):
        """Start keyword detection"""
        if self.is_listening:
            return
        
        self.is_listening = True
        
        try:
            stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            print(f"🎧 Listening for keyword '{self.keyword}'...")
            print("💡 Speak clearly: 'Computer' (try speaking louder if needed)")
            
            chunk_count = 0
            
            while self.is_listening:
                chunk_count += 1
                
                # Record audio chunk
                frames = []
                frames_to_record = int(self.RATE / self.CHUNK * self.LISTEN_DURATION)
                
                for _ in range(frames_to_record):
                    if not self.is_listening:
                        break
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    frames.append(data)
                
                if not frames:
                    continue
                
                audio_data = b''.join(frames)
                
                # Check cooldown
                current_time = time.time()
                if current_time - self.last_detection_time < self.detection_cooldown:
                    continue
                
                # Analyze audio quality
                audio_info = self.analyze_audio_quality(audio_data)
                
                # Show periodic status
                if chunk_count % 3 == 0:  # Every ~12 seconds
                    print(f"📊 Listening... (RMS: {audio_info.get('rms', 0):.0f}, "
                          f"Max: {audio_info.get('max_amplitude', 0)}, "
                          f"Silence: {audio_info.get('silence_ratio', 0):.1%})")
                
                if not audio_info.get('worth_transcribing', False):
                    continue
                
                print("🔄 Processing audio...")
                
                # Transcribe audio
                text = self.transcribe_audio_chunk(audio_data)
                
                if text:
                    print(f"📝 Heard: '{text}'")
                    
                    # Check for keyword (more flexible matching)
                    if (self.keyword in text or 
                        "compute" in text or  # Partial match
                        "comput" in text):
                        
                        print(f"🎯 Keyword detected! Activating assistant...")
                        self.last_detection_time = current_time
                        
                        if self.callback:
                            self.callback()
            
            stream.close()
            
        except Exception as e:
            print(f"❌ Error in keyword detection: {e}")
        finally:
            self.is_listening = False
    
    def stop_listening(self):
        """Stop keyword detection"""
        print("🛑 Stopping keyword detection...")
        self.is_listening = False
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_listening()
        if hasattr(self, 'audio'):
            self.audio.terminate()
        print("✅ Keyword detector cleaned up")

def test_improved_detector():
    """Test improved keyword detector"""
    def on_keyword():
        print("🎉 SUCCESS: Keyword detected! Assistant would activate here.")
    
    try:
        detector = ImprovedKeywordDetector(keyword="computer", callback=on_keyword)
        detector.start_listening()
    except ValueError as e:
        print(f"⚠️  {e}")
        print("Set OPENAI_API_KEY environment variable to test")
    except KeyboardInterrupt:
        print("\n⏹️  Stopping...")
    finally:
        if 'detector' in locals():
            detector.cleanup()

if __name__ == "__main__":
    test_improved_detector()