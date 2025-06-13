#!/usr/bin/env python3

import pyaudio
import wave
import numpy as np
import whisper
import threading
import queue
import time
import sys
import os
import io
from datetime import datetime
from openai import OpenAI

class EnhancedTranscriber:
    def __init__(self, mode="local", model_size="base", api_key=None):
        """
        Initialize transcriber with local or cloud options
        
        Args:
            mode: "local" for local Whisper, "cloud" for OpenAI API
            model_size: For local mode - "tiny", "base", "small", "medium", "large"
            api_key: OpenAI API key for cloud mode
        """
        # Audio recording parameters
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.RECORD_SECONDS = 3  # Shorter chunks for better responsiveness
        
        self.mode = mode
        self.model_size = model_size
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Initialize transcription engine
        if mode == "cloud":
            if not api_key:
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OpenAI API key required for cloud mode. Set OPENAI_API_KEY env var or pass api_key parameter.")
            self.client = OpenAI(api_key=api_key)
            print("Using OpenAI Whisper API (cloud)")
        else:
            print(f"Loading local Whisper {model_size} model...")
            self.model = whisper.load_model(model_size)
            print("Local model loaded successfully!")
        
        # Audio buffer and threading
        self.audio_queue = queue.Queue()
        self.is_recording = False
        
        # Performance tracking
        self.transcription_times = []
    
    def list_audio_devices(self):
        """List available audio input devices"""
        print("Available audio devices:")
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  {i}: {info['name']} (channels: {info['maxInputChannels']})")
    
    def preprocess_audio(self, audio_data):
        """Enhance audio quality for better transcription"""
        # Normalize audio
        audio_data = audio_data / np.max(np.abs(audio_data))
        
        # Simple noise gate - remove very quiet sections
        noise_threshold = 0.02
        audio_data = np.where(np.abs(audio_data) < noise_threshold, 0, audio_data)
        
        return audio_data
    
    def transcribe_with_cloud(self, audio_data):
        """Transcribe audio using OpenAI's Whisper API"""
        try:
            # Convert numpy array to WAV bytes
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(self.CHANNELS)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.RATE)
                wav_file.writeframes(audio_int16.tobytes())
            
            wav_buffer.seek(0)
            wav_buffer.name = "audio.wav"  # Required by OpenAI API
            
            # Transcribe using OpenAI API
            start_time = time.time()
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=wav_buffer,
                response_format="text"
            )
            processing_time = time.time() - start_time
            self.transcription_times.append(processing_time)
            
            return transcript.strip(), processing_time
            
        except Exception as e:
            print(f"Cloud transcription error: {e}")
            return "", 0
    
    def transcribe_with_local(self, audio_data):
        """Transcribe audio using local Whisper model"""
        try:
            start_time = time.time()
            
            # Preprocess audio
            audio_data = self.preprocess_audio(audio_data)
            
            # Transcribe using local Whisper
            result = self.model.transcribe(
                audio_data, 
                language="en",
                fp16=False,  # Better compatibility
                no_speech_threshold=0.6,  # More aggressive silence detection
                logprob_threshold=-1.0
            )
            
            processing_time = time.time() - start_time
            self.transcription_times.append(processing_time)
            
            return result["text"].strip(), processing_time
            
        except Exception as e:
            print(f"Local transcription error: {e}")
            return "", 0
    
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
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    frames.append(data)
                
                if frames:
                    # Convert to numpy array
                    audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
                    # Normalize to float32
                    audio_data = audio_data.astype(np.float32) / 32768.0
                    
                    # Simple voice activity detection
                    if np.max(np.abs(audio_data)) > 0.01:
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
                
                # Transcribe using selected method
                if self.mode == "cloud":
                    text, proc_time = self.transcribe_with_cloud(audio_data)
                else:
                    text, proc_time = self.transcribe_with_local(audio_data)
                
                if text:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{timestamp}] ({proc_time:.2f}s) {text}")
                    
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
        
        # Print performance stats
        if self.transcription_times:
            avg_time = sum(self.transcription_times) / len(self.transcription_times)
            print(f"\nPerformance Stats:")
            print(f"- Average transcription time: {avg_time:.2f}s")
            print(f"- Total transcriptions: {len(self.transcription_times)}")
            print(f"- Mode: {self.mode}")
            if self.mode == "local":
                print(f"- Model: {self.model_size}")
        
        print("Transcription stopped.")

def main():
    print("Enhanced Microphone Transcriber")
    print("================================")
    print("Options:")
    print("1. Local transcription (faster startup, runs offline)")
    print("2. Cloud transcription (faster processing, requires OpenAI API key)")
    print()
    
    # Get user preference
    while True:
        choice = input("Choose mode (1 for local, 2 for cloud): ").strip()
        if choice in ['1', '2']:
            break
        print("Please enter 1 or 2")
    
    try:
        if choice == '1':
            # Local mode - ask for model size
            print("\nLocal model sizes:")
            print("- tiny: Fastest, least accurate")
            print("- base: Good balance (recommended)")
            print("- small: Better accuracy, slower")
            print("- medium: High accuracy, much slower")
            print("- large: Best accuracy, very slow")
            
            model_size = input("Choose model size (default: base): ").strip() or "base"
            if model_size not in ["tiny", "base", "small", "medium", "large"]:
                model_size = "base"
            
            transcriber = EnhancedTranscriber(mode="local", model_size=model_size)
        else:
            # Cloud mode
            api_key = input("Enter OpenAI API key (or press Enter to use OPENAI_API_KEY env var): ").strip()
            if not api_key:
                api_key = None  # Will use environment variable
            
            transcriber = EnhancedTranscriber(mode="cloud", api_key=api_key)
        
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