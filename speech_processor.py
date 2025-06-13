#!/usr/bin/env python3

import pyaudio
import wave
import io
import os
import time
from typing import Optional
from openai import OpenAI

class SpeechProcessor:
    def __init__(self, api_key: str = None):
        """
        Initialize speech processor for recording and transcription
        
        Args:
            api_key: OpenAI API key (or uses OPENAI_API_KEY env var)
        """
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env var or pass api_key parameter.")
        
        self.client = OpenAI(api_key=api_key)
        
        # Audio parameters
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.RECORD_SECONDS = 4  # Duration to record after wake word
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        print("✅ Speech processor initialized")
    
    def play_beep(self):
        """Play a simple beep to indicate recording start"""
        try:
            # Use macOS system beep
            os.system("afplay /System/Library/Sounds/Tink.aiff")
        except:
            # Fallback - just print
            print("🔔 *beep*")
    
    def record_audio(self, duration: float = None) -> Optional[bytes]:
        """
        Record audio for specified duration
        
        Args:
            duration: Recording duration in seconds (uses default if None)
            
        Returns:
            Raw audio data as bytes, or None if error
        """
        if duration is None:
            duration = self.RECORD_SECONDS
        
        try:
            # Play beep to indicate recording start
            self.play_beep()
            
            # Open audio stream
            stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            print(f"🎤 Recording for {duration} seconds...")
            
            frames = []
            frames_to_record = int(self.RATE / self.CHUNK * duration)
            
            for _ in range(frames_to_record):
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            print("✅ Recording completed")
            
            # Convert to bytes
            audio_data = b''.join(frames)
            return audio_data
            
        except Exception as e:
            print(f"❌ Error recording audio: {e}")
            return None
    
    def audio_to_wav_bytes(self, audio_data: bytes) -> bytes:
        """
        Convert raw audio data to WAV format bytes
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            WAV formatted bytes
        """
        wav_buffer = io.BytesIO()
        
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(self.CHANNELS)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.RATE)
            wav_file.writeframes(audio_data)
        
        wav_buffer.seek(0)
        return wav_buffer.getvalue()
    
    def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe audio using OpenAI Whisper API
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            Transcribed text, or None if error
        """
        try:
            # Convert to WAV format
            wav_data = self.audio_to_wav_bytes(audio_data)
            
            # Create file-like object for API
            wav_buffer = io.BytesIO(wav_data)
            wav_buffer.name = "audio.wav"  # Required by OpenAI API
            
            print("🔄 Transcribing audio...")
            start_time = time.time()
            
            # Transcribe using OpenAI Whisper API
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=wav_buffer,
                response_format="text"
            )
            
            processing_time = time.time() - start_time
            transcribed_text = transcript.strip()
            
            if transcribed_text:
                print(f"✅ Transcribed ({processing_time:.1f}s): '{transcribed_text}'")
                return transcribed_text
            else:
                print("⚠️  No speech detected")
                return None
                
        except Exception as e:
            print(f"❌ Error transcribing audio: {e}")
            return None
    
    def record_and_transcribe(self, duration: float = None) -> Optional[str]:
        """
        Record audio and transcribe it in one step
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Transcribed text, or None if error
        """
        # Record audio
        audio_data = self.record_audio(duration)
        if not audio_data:
            return None
        
        # Transcribe audio
        return self.transcribe_audio(audio_data)
    
    def cleanup(self):
        """Clean up PyAudio resources"""
        if hasattr(self, 'audio'):
            self.audio.terminate()
        print("✅ Speech processor cleaned up")

def test_speech_processor():
    """Test speech processor functionality"""
    print("🧪 Testing Speech Processor")
    print("=" * 30)
    
    try:
        processor = SpeechProcessor()
    except ValueError as e:
        print(f"⚠️  {e}")
        print("Set OPENAI_API_KEY environment variable to test")
        return
    
    try:
        print("\n🎤 Testing recording and transcription...")
        print("Say something after the beep:")
        
        # Test recording and transcription
        text = processor.record_and_transcribe(duration=3)
        
        if text:
            print(f"🎯 Successfully transcribed: '{text}'")
        else:
            print("❌ No text transcribed")
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted")
    finally:
        processor.cleanup()

if __name__ == "__main__":
    test_speech_processor()