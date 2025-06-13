#!/usr/bin/env python3

import pyaudio

print("Testing PyAudio...")
try:
    audio = pyaudio.PyAudio()
    print("PyAudio initialized successfully!")
    
    print("Available audio devices:")
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f"  {i}: {info['name']} (channels: {info['maxInputChannels']})")
    
    audio.terminate()
    print("PyAudio test completed successfully!")
    
except Exception as e:
    print(f"Error with PyAudio: {e}")