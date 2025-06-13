#!/usr/bin/env python3

import pyaudio
import struct
import pvporcupine
from typing import Callable

class WakeWordDetector:
    def __init__(self, keyword="computer", sensitivity=0.5, callback: Callable = None):
        """
        Initialize wake word detector using Porcupine
        
        Args:
            keyword: Wake word to detect (built-in options: computer, hey google, etc.)
            sensitivity: Detection sensitivity (0.0 to 1.0)
            callback: Function to call when wake word is detected
        """
        self.keyword = keyword
        self.sensitivity = sensitivity
        self.callback = callback
        self.is_listening = False
        
        # Initialize Porcupine
        try:
            # Use built-in keyword
            self.porcupine = pvporcupine.create(
                keywords=[keyword],
                sensitivities=[sensitivity]
            )
            print(f"✅ Wake word detector initialized with keyword: '{keyword}'")
        except Exception as e:
            print(f"❌ Error initializing Porcupine: {e}")
            print("Available built-in keywords:", pvporcupine.KEYWORDS)
            raise
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Audio parameters (required by Porcupine)
        self.sample_rate = self.porcupine.sample_rate
        self.frame_length = self.porcupine.frame_length
        
        print(f"Audio settings: {self.sample_rate}Hz, {self.frame_length} frames")
    
    def list_available_keywords(self):
        """List all built-in wake words available in Porcupine"""
        print("Available built-in wake words:")
        for keyword in pvporcupine.KEYWORDS:
            print(f"  - {keyword}")
    
    def start_listening(self):
        """Start listening for the wake word"""
        if self.is_listening:
            print("Already listening for wake word")
            return
        
        self.is_listening = True
        
        try:
            # Open audio stream
            stream = self.audio.open(
                rate=self.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.frame_length
            )
            
            print(f"🎧 Listening for wake word '{self.keyword}'...")
            print("Say the wake word to activate the assistant")
            
            while self.is_listening:
                # Read audio frame
                pcm = stream.read(self.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self.frame_length, pcm)
                
                # Check for wake word
                keyword_index = self.porcupine.process(pcm)
                
                if keyword_index >= 0:
                    print(f"🎯 Wake word '{self.keyword}' detected!")
                    
                    # Call callback if provided
                    if self.callback:
                        self.callback()
                    
                    # Brief pause after detection
                    import time
                    time.sleep(0.5)
            
            stream.close()
            
        except Exception as e:
            print(f"❌ Error in wake word detection: {e}")
        finally:
            self.is_listening = False
    
    def stop_listening(self):
        """Stop listening for the wake word"""
        print("🛑 Stopping wake word detection...")
        self.is_listening = False
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_listening()
        if hasattr(self, 'porcupine'):
            self.porcupine.delete()
        if hasattr(self, 'audio'):
            self.audio.terminate()
        print("✅ Wake word detector cleaned up")

def test_wake_word():
    """Test function for wake word detection"""
    def on_wake_word():
        print("🚀 Wake word callback triggered!")
    
    detector = WakeWordDetector(keyword="computer", callback=on_wake_word)
    
    try:
        detector.start_listening()
    except KeyboardInterrupt:
        print("\n⏹️  Stopping...")
    finally:
        detector.cleanup()

if __name__ == "__main__":
    # List available keywords
    detector = WakeWordDetector()
    detector.list_available_keywords()
    print()
    
    # Test wake word detection
    test_wake_word()