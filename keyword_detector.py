#!/usr/bin/env python3

import pyaudio
import numpy as np
import threading
import time
import io
import wave
from typing import Callable, Optional
import os
from openai import OpenAI

class KeywordDetector:
    def __init__(self, keyword: str = "computer", callback: Callable = None, api_key: str = None):
        """
        Simple keyword detection using continuous transcription with OpenAI Whisper
        
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
        self.BUFFER_SECONDS = 3  # Continuous 3-second audio buffer
        
        self.audio = pyaudio.PyAudio()
        
        # Circular buffer for audio
        self.audio_buffer = []
        self.buffer_lock = threading.Lock()
        
        # Detection state
        self.last_detection_time = 0
        self.detection_cooldown = 2  # Seconds between detections
        
        print(f"✅ Keyword detector initialized for '{keyword}'")
    
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
        except Exception as e:
            # Silently handle transcription errors to avoid spam
            return None
    
    def check_for_keyword(self):
        """Continuously check audio buffer for keyword"""
        while self.is_listening:
            try:
                # Wait for enough audio data
                time.sleep(1)
                
                with self.buffer_lock:
                    if len(self.audio_buffer) < self.BUFFER_SECONDS:
                        continue
                    
                    # Get recent audio data
                    recent_audio = b''.join(self.audio_buffer[-self.BUFFER_SECONDS:])
                    self.audio_buffer = self.audio_buffer[-self.BUFFER_SECONDS:]  # Keep only recent
                
                # Check if we're in cooldown period
                current_time = time.time()
                if current_time - self.last_detection_time < self.detection_cooldown:
                    continue
                
                # Transcribe recent audio
                text = self.transcribe_audio_chunk(recent_audio)
                
                if text and self.keyword in text:
                    print(f"🎯 Keyword '{self.keyword}' detected in: '{text}'")
                    self.last_detection_time = current_time
                    
                    if self.callback:
                        self.callback()
                
            except Exception as e:
                print(f"❌ Error in keyword detection: {e}")
                time.sleep(1)
    
    def record_audio(self):
        """Continuously record audio into buffer"""
        try:
            stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            frames_per_second = int(self.RATE / self.CHUNK)
            
            while self.is_listening:
                # Record one second of audio
                frames = []
                for _ in range(frames_per_second):
                    if not self.is_listening:
                        break
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    frames.append(data)
                
                if frames:
                    audio_data = b''.join(frames)
                    
                    with self.buffer_lock:
                        self.audio_buffer.append(audio_data)
                        # Keep buffer size manageable
                        if len(self.audio_buffer) > 10:  # Max 10 seconds
                            self.audio_buffer.pop(0)
            
            stream.close()
            
        except Exception as e:
            print(f"❌ Error recording audio: {e}")
    
    def start_listening(self):
        """Start keyword detection"""
        if self.is_listening:
            return
        
        self.is_listening = True
        
        print(f"🎧 Listening for keyword '{self.keyword}'...")
        print("Say the keyword to activate the assistant")
        
        # Start recording thread
        self.recording_thread = threading.Thread(target=self.record_audio)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        # Start detection thread
        self.detection_thread = threading.Thread(target=self.check_for_keyword)
        self.detection_thread.daemon = True
        self.detection_thread.start()
        
        # Keep main thread alive
        try:
            while self.is_listening:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop_listening()
    
    def stop_listening(self):
        """Stop keyword detection"""
        print("🛑 Stopping keyword detection...")
        self.is_listening = False
        
        # Wait for threads to finish
        if hasattr(self, 'recording_thread'):
            self.recording_thread.join(timeout=2)
        if hasattr(self, 'detection_thread'):
            self.detection_thread.join(timeout=2)
    
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
        detector = KeywordDetector(keyword="computer", callback=on_keyword)
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