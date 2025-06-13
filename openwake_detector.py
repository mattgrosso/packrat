#!/usr/bin/env python3

import pyaudio
import numpy as np
import threading
import time
from typing import Callable
import openwakeword
from openwakeword.model import Model

class OpenWakeDetector:
    def __init__(self, wake_phrase: str = "hey computer", callback: Callable = None):
        """
        Wake word detector using OpenWakeWord library
        
        Args:
            wake_phrase: Wake phrase to detect (default: "hey computer")
            callback: Function to call when wake phrase is detected
        """
        self.wake_phrase = wake_phrase
        self.callback = callback
        self.is_listening = False
        
        # Initialize OpenWakeWord model
        try:
            # OpenWakeWord comes with built-in models
            # Try common wake phrases
            if "hey computer" in wake_phrase.lower():
                model_path = None  # Use default model
            else:
                model_path = None  # Use default model
            
            # Initialize the model with default settings
            self.model = Model()
            print(f"✅ OpenWakeWord initialized with default models")
            
        except Exception as e:
            print(f"❌ Error initializing OpenWakeWord: {e}")
            raise
        
        # Audio parameters (required by OpenWakeWord)
        self.sample_rate = 16000
        self.chunk_size = 1280  # 80ms chunks at 16kHz
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Detection settings
        self.detection_threshold = 0.5
        self.cooldown_time = 2.0  # seconds between detections
        self.last_detection = 0
    
    def start_listening(self):
        """Start listening for wake phrase"""
        if self.is_listening:
            print("Already listening for wake phrase")
            return
        
        self.is_listening = True
        
        try:
            # Open audio stream
            stream = self.audio.open(
                rate=self.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            print(f"🎧 Listening for '{self.wake_phrase}'...")
            print("Say the wake phrase to activate the assistant")
            
            while self.is_listening:
                # Read audio chunk
                audio_data = stream.read(self.chunk_size, exception_on_overflow=False)
                
                # Convert to numpy array (int16 to float32)
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Get prediction from model
                prediction = self.model.predict(audio_array)
                
                # Check if wake phrase was detected
                for wake_word, score in prediction.items():
                    if score >= self.detection_threshold:
                        current_time = time.time()
                        
                        # Check cooldown period
                        if current_time - self.last_detection >= self.cooldown_time:
                            print(f"🎯 Wake phrase '{self.wake_phrase}' detected! (confidence: {score:.2f})")
                            self.last_detection = current_time
                            
                            if self.callback:
                                self.callback()
                            
                            # Brief pause after detection
                            time.sleep(0.5)
            
            stream.close()
            
        except Exception as e:
            print(f"❌ Error in wake word detection: {e}")
        finally:
            self.is_listening = False
    
    def stop_listening(self):
        """Stop listening for wake phrase"""
        print("🛑 Stopping wake word detection...")
        self.is_listening = False
    
    def set_threshold(self, threshold: float):
        """Set detection threshold (0.0 to 1.0)"""
        if 0.0 <= threshold <= 1.0:
            self.detection_threshold = threshold
            print(f"🎛️ Detection threshold set to {threshold}")
        else:
            print("❌ Threshold must be between 0.0 and 1.0")
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_listening()
        if hasattr(self, 'audio'):
            self.audio.terminate()
        print("✅ OpenWakeWord detector cleaned up")

def test_openwake_detector():
    """Test OpenWakeWord detection"""
    def on_wake_phrase():
        print("🚀 Wake phrase detected callback!")
    
    try:
        # Create detector
        detector = OpenWakeDetector(callback=on_wake_phrase)
        
        print(f"\n🧪 Testing with wake phrase: '{detector.wake_phrase}'")
        print("Speak the wake phrase to test detection")
        print("Press Ctrl+C to stop")
        
        # Start detection
        detector.start_listening()
        
    except KeyboardInterrupt:
        print("\n⏹️  Stopping test...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'detector' in locals():
            detector.cleanup()

if __name__ == "__main__":
    test_openwake_detector()