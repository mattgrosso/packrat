#!/usr/bin/env python3

import pyaudio
import wave
import io
import os
from openai import OpenAI

def quick_transcription_test():
    """Quick test of audio recording and transcription"""
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No API key found. Set OPENAI_API_KEY environment variable.")
        return
    
    client = OpenAI(api_key=api_key)
    
    # Audio parameters
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    RECORD_SECONDS = 3
    
    audio = pyaudio.PyAudio()
    
    try:
        print("🎤 Quick transcription test")
        print("=" * 30)
        
        # Record audio
        print("🔴 Recording 3 seconds... Say 'computer' now!")
        
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        frames = []
        for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)
        
        stream.close()
        print("✅ Recording completed")
        
        # Convert to WAV
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(2)
            wav_file.setframerate(RATE)
            wav_file.writeframes(b''.join(frames))
        
        wav_buffer.seek(0)
        wav_buffer.name = "test.wav"
        
        # Transcribe
        print("🔄 Transcribing...")
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=wav_buffer,
            response_format="text"
        )
        
        result = transcript.strip()
        print(f"📝 Transcription: '{result}'")
        
        # Check for keyword
        if "computer" in result.lower():
            print("🎯 SUCCESS: 'computer' detected in transcription!")
        else:
            print("❌ 'computer' NOT found in transcription")
            print("💡 Try speaking louder or closer to the microphone")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        audio.terminate()

if __name__ == "__main__":
    quick_transcription_test()