#!/usr/bin/env python3

import pyaudio
import threading
import time
import webrtcvad
import struct
from typing import Callable

class SimpleWakeDetector:
    def __init__(self, callback: Callable = None, mode: str = "manual"):
        """
        Simple wake word detector with multiple modes
        
        Args:
            callback: Function to call when wake word is detected
            mode: "manual" for keyboard activation, "voice" for voice activity detection
        """
        self.callback = callback
        self.mode = mode
        self.is_listening = False
        self.audio = pyaudio.PyAudio()
        
        # Audio parameters
        self.sample_rate = 16000
        self.frame_duration = 30  # ms
        self.frame_size = int(self.sample_rate * self.frame_duration / 1000)
        
        if mode == "voice":
            # Initialize voice activity detector
            self.vad = webrtcvad.Vad(2)  # Aggressiveness 0-3 (3 is most aggressive)
            print("✅ Voice activity wake detector initialized")
        else:
            print("✅ Manual wake detector initialized (press ENTER to activate)")
    
    def start_listening(self):
        """Start listening for wake signal"""
        if self.is_listening:
            print("Already listening for wake signal")
            return
        
        self.is_listening = True
        
        if self.mode == "manual":
            self._manual_detection()
        else:
            self._voice_activity_detection()
    
    def _manual_detection(self):
        """Manual activation by pressing Enter"""
        print("🎧 Manual wake detection active")
        print("Press ENTER to activate the assistant (Ctrl+C to quit)")
        
        try:
            while self.is_listening:
                input()  # Wait for Enter key
                if self.is_listening:  # Check again in case we stopped
                    print("🎯 Manual activation detected!")
                    if self.callback:
                        self.callback()
                    time.sleep(0.5)  # Brief pause
        except EOFError:
            # Handle Ctrl+D
            pass
        except KeyboardInterrupt:
            pass
    
    def _voice_activity_detection(self):
        """Voice activity detection as wake signal"""
        try:
            stream = self.audio.open(
                rate=self.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.frame_size
            )
            
            print("🎧 Voice activity detection active")
            print("Start speaking to activate the assistant")
            
            silence_duration = 0
            speech_detected = False
            
            while self.is_listening:
                # Read audio frame
                frame = stream.read(self.frame_size, exception_on_overflow=False)
                
                # Check if frame contains speech
                is_speech = self.vad.is_speech(frame, self.sample_rate)
                
                if is_speech:
                    if not speech_detected:
                        print("🎯 Voice activity detected!")
                        speech_detected = True
                        if self.callback:
                            self.callback()
                    silence_duration = 0
                else:
                    silence_duration += self.frame_duration
                    
                    # Reset speech detection after 2 seconds of silence
                    if silence_duration > 2000:
                        speech_detected = False
            
            stream.close()
            
        except Exception as e:
            print(f"❌ Error in voice activity detection: {e}")
    
    def stop_listening(self):
        """Stop listening for wake signal"""
        print("🛑 Stopping wake detection...")
        self.is_listening = False
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_listening()
        if hasattr(self, 'audio'):
            self.audio.terminate()
        print("✅ Wake detector cleaned up")

def test_wake_detector():
    """Test wake detector functionality"""
    def on_wake():
        print("🚀 Wake signal callback triggered!")
    
    print("Choose wake detection mode:")
    print("1. Manual (press ENTER)")
    print("2. Voice activity")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "2":
        detector = SimpleWakeDetector(callback=on_wake, mode="voice")
    else:
        detector = SimpleWakeDetector(callback=on_wake, mode="manual")
    
    try:
        detector.start_listening()
    except KeyboardInterrupt:
        print("\n⏹️  Stopping...")
    finally:
        detector.cleanup()

if __name__ == "__main__":
    test_wake_detector()