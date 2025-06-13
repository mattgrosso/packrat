#!/usr/bin/env python3

import pyaudio
import numpy as np
import threading
import time
import whisper
from typing import Callable, Optional

class LocalKeywordDetector:
    def __init__(self, keyword: str = "computer", callback: Callable = None, model_size: str = "tiny"):
        """
        Local keyword detection using local Whisper model
        
        Args:
            keyword: Keyword to detect (e.g., "computer")
            callback: Function to call when keyword is detected
            model_size: Local Whisper model size ("tiny", "base", "small")
        """
        self.keyword = keyword.lower()
        self.callback = callback
        self.is_listening = False
        
        # Load local Whisper model
        print(f"🔄 Loading local Whisper {model_size} model...")
        self.model = whisper.load_model(model_size)
        print(f"✅ Local Whisper model loaded")
        
        # Audio parameters - optimized for speech
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.LISTEN_DURATION = 3  # Shorter for faster processing
        
        self.audio = pyaudio.PyAudio()
        
        # Detection state
        self.last_detection_time = 0
        self.detection_cooldown = 2  # Shorter cooldown with local processing
        
        # Audio processing settings
        self.min_rms_threshold = 150  # Minimum audio level
        self.max_silence_ratio = 0.9  # Allow up to 90% silence
        
        print(f"✅ Local keyword detector initialized for '{keyword}'")
    
    def preprocess_audio(self, audio_data: bytes) -> np.ndarray:
        """Clean up audio data and convert to format Whisper expects"""
        # Convert to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        
        # Normalize to [-1, 1] range (Whisper expects this)
        audio_array = audio_array / 32768.0
        
        # Simple noise reduction - remove very quiet parts
        noise_threshold = 0.01
        audio_array = np.where(np.abs(audio_array) < noise_threshold, 0, audio_array)
        
        return audio_array
    
    def transcribe_audio_chunk(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio chunk using local Whisper model"""
        try:
            # Preprocess audio
            audio_array = self.preprocess_audio(audio_data)
            
            # Transcribe with local Whisper
            result = self.model.transcribe(
                audio_array,
                language="en",
                fp16=False,  # Better compatibility
                no_speech_threshold=0.6,  # Be more aggressive about detecting speech
                logprob_threshold=-1.0,
                initial_prompt="The user is saying the word 'computer' to activate a voice assistant."
            )
            
            return result["text"].strip().lower()
            
        except Exception as e:
            print(f"⚠️ Local transcription error: {e}")
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
            
            print(f"🎧 Listening for keyword '{self.keyword}' (using local Whisper)...")
            print("💡 Speak clearly: 'Computer'")
            
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
                if chunk_count % 5 == 0:  # Every ~15 seconds
                    print(f"📊 Listening... (RMS: {audio_info.get('rms', 0):.0f}, "
                          f"Max: {audio_info.get('max_amplitude', 0)})")
                
                if not audio_info.get('worth_transcribing', False):
                    continue
                
                print("🔄 Processing audio locally...")
                start_time = time.time()
                
                # Transcribe audio locally
                text = self.transcribe_audio_chunk(audio_data)
                
                processing_time = time.time() - start_time
                
                if text:
                    print(f"📝 Heard ({processing_time:.1f}s): '{text}'")
                    
                    # Check for keyword (flexible matching)
                    if (self.keyword in text or 
                        "compute" in text or  # Partial match
                        "comput" in text):
                        
                        print(f"🎯 Keyword detected! Activating assistant...")
                        self.last_detection_time = current_time
                        
                        if self.callback:
                            self.callback()
                else:
                    print(f"🔇 No speech detected ({processing_time:.1f}s)")
            
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
        print("✅ Local keyword detector cleaned up")

def test_local_detector():
    """Test local keyword detector"""
    def on_keyword():
        print("🎉 SUCCESS: Keyword detected! Assistant would activate here.")
    
    try:
        print("🧪 Testing Local Keyword Detector")
        print("Using local Whisper model - no API costs!")
        print("-" * 40)
        
        detector = LocalKeywordDetector(keyword="computer", callback=on_keyword, model_size="tiny")
        detector.start_listening()
        
    except KeyboardInterrupt:
        print("\n⏹️  Stopping...")
    finally:
        if 'detector' in locals():
            detector.cleanup()

if __name__ == "__main__":
    test_local_detector()