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

class SimpleKeywordDetector:
    def __init__(self, keyword: str = "computer", callback: Callable = None, api_key: str = None):
        """
        Simple keyword detection using periodic audio transcription
        
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
        
        # Audio parameters
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.LISTEN_DURATION = 2  # Listen for 2 seconds at a time
        
        self.audio = pyaudio.PyAudio()
        
        # Detection state
        self.last_detection_time = 0
        self.detection_cooldown = 3  # Seconds between detections
        
        print(f"✅ Simple keyword detector initialized for '{keyword}'")
    
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
    
    def transcribe_audio_chunk(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio chunk using Whisper API"""
        try:
            wav_data = self.audio_to_wav_bytes(audio_data)
            wav_buffer = io.BytesIO(wav_data)
            wav_buffer.name = "audio.wav"
            
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=wav_buffer,
                response_format="text"
            )
            
            return transcript.strip().lower()
        except Exception:
            # Silently handle transcription errors
            return None
    
    def has_sufficient_audio(self, audio_data: bytes) -> bool:
        """Check if audio has sufficient volume to warrant transcription"""
        # Convert to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Check RMS volume
        rms = np.sqrt(np.mean(audio_array**2))
        
        # Only transcribe if there's sufficient audio activity
        return rms > 500  # Adjust threshold as needed
    
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
            print("Say the keyword clearly to activate the assistant")
            
            while self.is_listening:
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
                
                # Check if we're in cooldown period
                current_time = time.time()
                if current_time - self.last_detection_time < self.detection_cooldown:
                    continue
                
                # Only transcribe if there's sufficient audio activity
                if not self.has_sufficient_audio(audio_data):
                    continue
                
                # Transcribe recent audio
                text = self.transcribe_audio_chunk(audio_data)
                
                if text and self.keyword in text:
                    print(f"🎯 Keyword '{self.keyword}' detected in: '{text}'")
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

def test_keyword_detector():
    """Test keyword detection"""
    def on_keyword():
        print("🚀 Keyword detected callback!")
    
    try:
        detector = SimpleKeywordDetector(keyword="computer", callback=on_keyword)
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
    test_keyword_detector()