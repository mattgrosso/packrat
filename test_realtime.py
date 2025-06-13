#!/usr/bin/env python3

from realtime_transcriber import RealtimeTranscriber
import time

print("Testing real-time transcriber with local tiny model...")
print("This will run for 10 seconds to test the buffering system.")
print("-" * 50)

try:
    # Create transcriber with tiny model for fast testing
    transcriber = RealtimeTranscriber(mode="local", model_size="tiny")
    
    # List devices
    transcriber.list_audio_devices()
    print()
    
    # Start transcription in a separate thread
    import threading
    
    def run_transcription():
        transcriber.start_transcription()
    
    # Start transcription
    transcription_thread = threading.Thread(target=run_transcription)
    transcription_thread.daemon = True
    transcription_thread.start()
    
    # Let it run for 10 seconds
    time.sleep(10)
    
    # Stop transcription
    transcriber.is_recording = False
    transcription_thread.join(timeout=3)
    
    print("\nTest completed!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()