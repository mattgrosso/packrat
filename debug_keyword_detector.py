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

class DebugKeywordDetector:
    def __init__(self, keyword: str = "computer", callback: Callable = None, api_key: str = None):
        """Debug version of keyword detector with verbose logging"""
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
        self.LISTEN_DURATION = 3  # Listen for 3 seconds at a time
        
        self.audio = pyaudio.PyAudio()
        
        # Detection state
        self.last_detection_time = 0
        self.detection_cooldown = 2  # Reduced cooldown for testing
        self.chunk_count = 0
        
        print(f"🔧 DEBUG: Keyword detector initialized for '{keyword}'")
        print(f"🔧 DEBUG: Audio rate: {self.RATE}Hz, chunk size: {self.CHUNK}")
    
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
            print("🔧 DEBUG: Sending audio to Whisper API...")
            start_time = time.time()
            
            wav_data = self.audio_to_wav_bytes(audio_data)
            wav_buffer = io.BytesIO(wav_data)
            wav_buffer.name = "audio.wav"
            
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=wav_buffer,
                response_format="text"
            )
            
            result = transcript.strip().lower()
            elapsed = time.time() - start_time
            print(f"🔧 DEBUG: Transcription ({elapsed:.1f}s): '{result}'")
            return result
            
        except Exception as e:
            print(f"🔧 DEBUG: Transcription error: {e}")
            return None
    
    def analyze_audio(self, audio_data: bytes) -> dict:
        """Analyze audio properties for debugging"""
        # Convert to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Calculate audio metrics
        rms = np.sqrt(np.mean(audio_array**2))
        max_amplitude = np.max(np.abs(audio_array))
        
        return {
            "rms": rms,
            "max_amplitude": max_amplitude,
            "duration": len(audio_array) / self.RATE,
            "samples": len(audio_array)
        }
    
    def start_listening(self):
        """Start keyword detection with debug output"""
        if self.is_listening:
            return
        
        self.is_listening = True
        
        try:
            stream = self.audio.open(
                format=self.FORMAT,
                channels=1,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            print(f"🎧 DEBUG: Listening for keyword '{self.keyword}'...")
            print("🎤 DEBUG: Speak clearly and loudly!")
            print("=" * 50)
            
            while self.is_listening:
                self.chunk_count += 1
                print(f"\n📊 DEBUG: Processing chunk #{self.chunk_count}")
                
                # Record audio chunk
                frames = []
                frames_to_record = int(self.RATE / self.CHUNK * self.LISTEN_DURATION)
                
                print(f"🔧 DEBUG: Recording {frames_to_record} frames for {self.LISTEN_DURATION}s...")
                
                for i in range(frames_to_record):
                    if not self.is_listening:
                        break
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    frames.append(data)
                    
                    # Show progress
                    if i % 20 == 0:
                        progress = (i / frames_to_record) * 100
                        print(f"🔧 DEBUG: Recording... {progress:.0f}%")
                
                if not frames:
                    continue
                
                audio_data = b''.join(frames)
                
                # Analyze audio
                audio_info = self.analyze_audio(audio_data)
                print(f"🔊 DEBUG: Audio - RMS: {audio_info['rms']:.0f}, Max: {audio_info['max_amplitude']}, Duration: {audio_info['duration']:.1f}s")
                
                # Check cooldown
                current_time = time.time()
                time_since_last = current_time - self.last_detection_time
                print(f"⏰ DEBUG: Time since last detection: {time_since_last:.1f}s (cooldown: {self.detection_cooldown}s)")
                
                if time_since_last < self.detection_cooldown:
                    print("⏸️ DEBUG: In cooldown period, skipping transcription")
                    continue
                
                # Check audio level
                if audio_info['rms'] < 300:  # Lower threshold for testing
                    print(f"🔇 DEBUG: Audio too quiet (RMS: {audio_info['rms']:.0f} < 300), skipping transcription")
                    continue
                
                print("✅ DEBUG: Audio level sufficient, transcribing...")
                
                # Transcribe audio
                text = self.transcribe_audio_chunk(audio_data)
                
                if text:
                    print(f"📝 DEBUG: Looking for '{self.keyword}' in '{text}'")
                    
                    if self.keyword in text:
                        print(f"🎯 DEBUG: KEYWORD FOUND! '{self.keyword}' detected in '{text}'")
                        self.last_detection_time = current_time
                        
                        if self.callback:
                            print("🚀 DEBUG: Calling callback function...")
                            self.callback()
                        else:
                            print("⚠️ DEBUG: No callback function set")
                    else:
                        print(f"❌ DEBUG: Keyword '{self.keyword}' NOT found in '{text}'")
                else:
                    print("❌ DEBUG: No text transcribed")
                
                print("-" * 30)
            
            stream.close()
            
        except Exception as e:
            print(f"❌ DEBUG: Error in keyword detection: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_listening = False
    
    def stop_listening(self):
        """Stop keyword detection"""
        print("🛑 DEBUG: Stopping keyword detection...")
        self.is_listening = False
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_listening()
        if hasattr(self, 'audio'):
            self.audio.terminate()
        print("✅ DEBUG: Keyword detector cleaned up")

def test_debug_detector():
    """Test debug keyword detector"""
    def on_keyword():
        print("🎉 SUCCESS: Keyword detected callback triggered!")
    
    try:
        print("🧪 Starting DEBUG keyword detection test")
        print("Say 'computer' clearly and loudly")
        print("Press Ctrl+C to stop")
        print("=" * 50)
        
        detector = DebugKeywordDetector(keyword="computer", callback=on_keyword)
        detector.start_listening()
        
    except ValueError as e:
        print(f"⚠️  {e}")
        print("Set OPENAI_API_KEY environment variable to test")
    except KeyboardInterrupt:
        print("\n⏹️  Stopping debug test...")
    finally:
        if 'detector' in locals():
            detector.cleanup()

if __name__ == "__main__":
    test_debug_detector()