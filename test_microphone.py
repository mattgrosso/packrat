#!/usr/bin/env python3

import pyaudio
import numpy as np
import time

def test_microphone():
    """Test microphone input levels"""
    
    # Audio parameters
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    audio = pyaudio.PyAudio()
    
    try:
        # List available input devices
        print("🎤 Available audio input devices:")
        for i in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  {i}: {info['name']} (channels: {info['maxInputChannels']})")
        
        print(f"\n🔊 Testing microphone levels...")
        print("Speak into your microphone - you should see audio levels")
        print("Press Ctrl+C to stop")
        print("-" * 50)
        
        # Open audio stream
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        for i in range(100):  # Test for ~10 seconds
            # Read audio
            data = stream.read(CHUNK, exception_on_overflow=False)
            
            # Convert to numpy array
            audio_array = np.frombuffer(data, dtype=np.int16)
            
            # Calculate audio metrics
            rms = np.sqrt(np.mean(audio_array**2))
            max_amplitude = np.max(np.abs(audio_array))
            
            # Create visual level meter
            level_bars = int(rms / 1000)  # Scale for display
            level_meter = "█" * min(level_bars, 20)
            
            print(f"\r🔊 RMS: {rms:6.0f} | Max: {max_amplitude:5d} | {level_meter:<20}", end="", flush=True)
            
            time.sleep(0.1)
        
        stream.close()
        
    except KeyboardInterrupt:
        print("\n⏹️  Microphone test stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        audio.terminate()
        print("✅ Microphone test completed")

if __name__ == "__main__":
    test_microphone()