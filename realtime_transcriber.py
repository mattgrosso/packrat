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
from collections import deque

class RealtimeTranscriber:
    def __init__(self, mode="local", model_size="base", api_key=None):
        """
        Real-time transcriber with proper buffering management
        
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
        
        # Dynamic chunk sizing based on processing speed
        self.initial_chunk_seconds = 2.0
        self.current_chunk_seconds = self.initial_chunk_seconds
        self.min_chunk_seconds = 1.0
        self.max_chunk_seconds = 5.0
        
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
        
        # Queue management
        self.MAX_QUEUE_SIZE = 3  # Maximum audio chunks in queue
        self.audio_queue = queue.Queue(maxsize=self.MAX_QUEUE_SIZE)
        self.is_recording = False
        
        # Performance tracking for adaptive behavior
        self.processing_times = deque(maxlen=10)  # Keep last 10 processing times
        self.dropped_chunks = 0
        self.processed_chunks = 0
        
        # Threading
        self.recording_thread = None
        self.transcription_thread = None
    
    def list_audio_devices(self):
        """List available audio input devices"""
        print("Available audio devices:")
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  {i}: {info['name']} (channels: {info['maxInputChannels']})")
    
    def adapt_chunk_size(self):
        """Dynamically adjust chunk size based on processing performance"""
        if len(self.processing_times) < 3:
            return
        
        avg_processing_time = sum(self.processing_times) / len(self.processing_times)
        
        # If processing is slower than chunk duration, increase chunk size
        # If processing is much faster, decrease chunk size for lower latency
        if avg_processing_time > self.current_chunk_seconds * 1.2:
            # Processing too slow, increase chunk size
            self.current_chunk_seconds = min(
                self.current_chunk_seconds * 1.2, 
                self.max_chunk_seconds
            )
            print(f"⚡ Increased chunk size to {self.current_chunk_seconds:.1f}s (processing: {avg_processing_time:.1f}s)")
        elif avg_processing_time < self.current_chunk_seconds * 0.5:
            # Processing very fast, decrease chunk size for lower latency
            self.current_chunk_seconds = max(
                self.current_chunk_seconds * 0.8,
                self.min_chunk_seconds
            )
            print(f"🚀 Decreased chunk size to {self.current_chunk_seconds:.1f}s (processing: {avg_processing_time:.1f}s)")
    
    def preprocess_audio(self, audio_data):
        """Enhance audio quality for better transcription"""
        # Normalize audio
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val
        
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
            
            return result["text"].strip(), processing_time
            
        except Exception as e:
            print(f"Local transcription error: {e}")
            return "", 0
    
    def record_audio_chunk(self):
        """Record audio and manage queue with backpressure"""
        try:
            stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            print("🎤 Recording started. Press Ctrl+C to stop.")
            
            while self.is_recording:
                frames = []
                frames_to_record = int(self.RATE / self.CHUNK * self.current_chunk_seconds)
                
                for _ in range(frames_to_record):
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
                        # Try to add to queue, drop if full (backpressure)
                        try:
                            self.audio_queue.put(audio_data, block=False)
                        except queue.Full:
                            # Queue is full - drop oldest chunk and add new one
                            try:
                                self.audio_queue.get(block=False)  # Remove oldest
                                self.audio_queue.put(audio_data, block=False)  # Add new
                                self.dropped_chunks += 1
                                if self.dropped_chunks % 5 == 0:  # Report every 5 drops
                                    print(f"⚠️  Dropped {self.dropped_chunks} chunks (processing too slow)")
                            except queue.Empty:
                                pass
            
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
                
                # Track performance
                self.processing_times.append(proc_time)
                self.processed_chunks += 1
                
                # Adapt chunk size based on performance
                if self.processed_chunks % 5 == 0:  # Adapt every 5 chunks
                    self.adapt_chunk_size()
                
                if text:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    queue_size = self.audio_queue.qsize()
                    status = f"[{timestamp}] ({proc_time:.1f}s, Q:{queue_size})"
                    print(f"{status} {text}")
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in transcription: {e}")
    
    def start_transcription(self):
        """Start the real-time transcription process"""
        self.is_recording = True
        
        # Start recording thread
        self.recording_thread = threading.Thread(target=self.record_audio_chunk)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        # Start transcription thread
        self.transcription_thread = threading.Thread(target=self.transcribe_audio)
        self.transcription_thread.daemon = True
        self.transcription_thread.start()
        
        try:
            # Keep main thread alive and show status
            last_status_time = time.time()
            
            while self.is_recording:
                time.sleep(0.5)
                
                # Show periodic status
                current_time = time.time()
                if current_time - last_status_time > 10:  # Every 10 seconds
                    queue_size = self.audio_queue.qsize()
                    if len(self.processing_times) > 0:
                        avg_proc_time = sum(self.processing_times) / len(self.processing_times)
                        print(f"📊 Status: Q:{queue_size}, AvgProc:{avg_proc_time:.1f}s, ChunkSize:{self.current_chunk_seconds:.1f}s, Dropped:{self.dropped_chunks}")
                    last_status_time = current_time
                    
        except KeyboardInterrupt:
            print("\n🛑 Stopping transcription...")
            self.is_recording = False
            
        # Wait for threads to finish
        if self.recording_thread:
            self.recording_thread.join(timeout=3)
        if self.transcription_thread:
            self.transcription_thread.join(timeout=3)
        
        self.audio.terminate()
        
        # Print final performance stats
        if self.processing_times:
            avg_time = sum(self.processing_times) / len(self.processing_times)
            print(f"\n📈 Final Performance Stats:")
            print(f"- Average processing time: {avg_time:.2f}s")
            print(f"- Final chunk size: {self.current_chunk_seconds:.1f}s")
            print(f"- Total processed: {self.processed_chunks}")
            print(f"- Total dropped: {self.dropped_chunks}")
            print(f"- Drop rate: {(self.dropped_chunks/(self.processed_chunks+self.dropped_chunks)*100):.1f}%")
            print(f"- Mode: {self.mode}")
            if self.mode == "local":
                print(f"- Model: {self.model_size}")
        
        print("✅ Transcription stopped.")

def main():
    print("🎯 Real-time Microphone Transcriber")
    print("==================================")
    print("✨ Features:")
    print("- Adaptive chunk sizing")
    print("- Queue management with backpressure")
    print("- Performance monitoring")
    print("- Real-time optimization")
    print()
    print("Options:")
    print("1. Local transcription (offline, adaptive)")
    print("2. Cloud transcription (fast, accurate)")
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
            print("- tiny: ~0.5s processing (recommended for real-time)")
            print("- base: ~2s processing (good balance)")
            print("- small: ~4s processing (better accuracy)")
            print("- medium: ~8s processing (high accuracy)")
            print("- large: ~15s processing (best accuracy)")
            
            model_size = input("Choose model size (default: tiny): ").strip() or "tiny"
            if model_size not in ["tiny", "base", "small", "medium", "large"]:
                model_size = "tiny"
            
            transcriber = RealtimeTranscriber(mode="local", model_size=model_size)
        else:
            # Cloud mode
            api_key = input("Enter OpenAI API key (or press Enter to use OPENAI_API_KEY env var): ").strip()
            if not api_key:
                api_key = None  # Will use environment variable
            
            transcriber = RealtimeTranscriber(mode="cloud", api_key=api_key)
        
        # List available audio devices
        transcriber.list_audio_devices()
        print()
        
        # Start transcription
        print("🚀 Starting real-time transcription...")
        print("🗣️  Speak into your microphone. Press Ctrl+C to stop.")
        print("📊 Status format: [time] (processing_time, queue_size) transcription")
        print("-" * 60)
        transcriber.start_transcription()
        
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()