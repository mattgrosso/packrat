#!/usr/bin/env python3

import pyaudio
import wave
import numpy as np
import whisper
import threading
import queue
import time
import sys
from datetime import datetime

class MicrophoneTranscriber:
    def __init__(self, model_size="base"):
        # Audio recording parameters
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.RECORD_SECONDS = 5  # Process audio in 5-second chunks
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Load Whisper model
        print(f"Loading Whisper {model_size} model...")
        self.model = whisper.load_model(model_size)
        print("Model loaded successfully!")
        
        # Audio buffer and threading
        self.audio_queue = queue.Queue()
        self.is_recording = False
        
    def list_audio_devices(self):
        """List available audio input devices"""
        print("Available audio devices:")
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  {i}: {info['name']} (channels: {info['maxInputChannels']})")
    
    def record_audio_chunk(self):
        """Record a chunk of audio and add it to the queue"""
        try:
            stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            print("Recording started. Press Ctrl+C to stop.")
            
            while self.is_recording:
                frames = []
                for _ in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
                    if not self.is_recording:
                        break
                    data = stream.read(self.CHUNK)
                    frames.append(data)
                
                if frames:
                    # Convert to numpy array
                    audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
                    # Normalize to float32
                    audio_data = audio_data.astype(np.float32) / 32768.0
                    self.audio_queue.put(audio_data)
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            print(f"Error in audio recording: {e}")
    
    def transcribe_audio(self):
        """Process audio chunks from the queue and transcribe them"""
        while self.is_recording or not self.audio_queue.empty():
            try:
                # Get audio data from queue (wait up to 1 second)
                audio_data = self.audio_queue.get(timeout=1)
                
                # Skip if audio is too quiet (simple voice activity detection)
                if np.max(np.abs(audio_data)) < 0.01:
                    continue
                
                # Transcribe using Whisper
                result = self.model.transcribe(audio_data, language="en")
                text = result["text"].strip()
                
                if text:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{timestamp}] {text}")
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in transcription: {e}")
    
    def start_transcription(self):
        """Start the real-time transcription process"""
        self.is_recording = True
        
        # Start recording thread
        recording_thread = threading.Thread(target=self.record_audio_chunk)
        recording_thread.daemon = True
        recording_thread.start()
        
        # Start transcription thread
        transcription_thread = threading.Thread(target=self.transcribe_audio)
        transcription_thread.daemon = True
        transcription_thread.start()
        
        try:
            # Keep main thread alive
            while self.is_recording:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping transcription...")
            self.is_recording = False
            
        # Wait for threads to finish
        recording_thread.join(timeout=2)
        transcription_thread.join(timeout=2)
        
        self.audio.terminate()
        print("Transcription stopped.")

def main():
    print("Microphone Transcriber using Whisper")
    print("=====================================")
    
    try:
        # Create transcriber instance
        print("Initializing transcriber...")
        transcriber = MicrophoneTranscriber(model_size="base")
        
        # List available audio devices
        transcriber.list_audio_devices()
        print()
        
        # Start transcription
        print("Starting real-time transcription...")
        print("Speak into your microphone. Press Ctrl+C to stop.")
        print("-" * 50)
        transcriber.start_transcription()
        
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()