#!/usr/bin/env python3

import subprocess
import os
import threading
import io
import tempfile
import time
from typing import Optional
from openai import OpenAI

class OpenAITTS:
    def __init__(self, voice: str = "alloy", api_key: str = None):
        """
        Initialize text-to-speech using OpenAI's TTS API
        
        Args:
            voice: OpenAI voice name (alloy, echo, fable, onyx, nova, shimmer)
            api_key: OpenAI API key
        """
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key required for TTS")
        
        self.client = OpenAI(api_key=api_key)
        self.voice = voice
        self.is_speaking = False
        self.should_stop = False
        self.current_process = None
        self.audio_command = None  # Track which audio command we're using
        
        # Available OpenAI voices
        self.available_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        
        if voice not in self.available_voices:
            print(f"⚠️ Unknown voice '{voice}', using 'alloy'")
            self.voice = "alloy"
        
        print(f"✅ OpenAI TTS initialized with voice '{self.voice}'")
    
    def list_voices(self) -> list:
        """List available OpenAI voices"""
        return self.available_voices
    
    def is_currently_speaking(self) -> bool:
        """Check if TTS is currently playing audio"""
        if not self.is_speaking:
            return False
        if not self.current_process:
            return self.is_speaking  # Still generating/preparing audio
        return self.current_process.poll() is None
    
    def speak(self, text: str, blocking: bool = True) -> bool:
        """
        Speak the given text using OpenAI TTS
        
        Args:
            text: Text to speak
            blocking: Whether to wait for speech to complete
            
        Returns:
            True if successful, False otherwise
        """
        if not text or not text.strip():
            return False
        
        try:
            print(f"🗣️ Speaking with OpenAI TTS: '{text}'")
            
            if blocking:
                self._speak_sync(text)
            else:
                # Set is_speaking immediately for non-blocking mode
                self.is_speaking = True
                thread = threading.Thread(target=self._speak_sync, args=(text,))
                thread.daemon = True
                thread.start()
            
            return True
                
        except Exception as e:
            print(f"❌ Error with OpenAI TTS: {e}")
            # Fallback to macOS say command
            return self._fallback_speak(text, blocking)
    
    def _speak_sync(self, text: str):
        """Synchronous speech using OpenAI TTS"""
        try:
            self.is_speaking = True
            self.should_stop = False
            
            # Check if we should stop before generating
            if self.should_stop:
                return
            
            # Generate speech with OpenAI API
            print("🕐 Starting OpenAI TTS generation...")
            start_time = time.time()
            
            response = self.client.audio.speech.create(
                model="tts-1",  # or tts-1-hd for higher quality
                voice=self.voice,
                input=text,
                response_format="mp3"
            )
            
            end_time = time.time()
            duration = end_time - start_time
            print(f"⏱️ TTS generation took {duration:.2f}s")
            
            # Check if we should stop before playing
            if self.should_stop:
                return
            
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_file.write(response.content)
                temp_filename = temp_file.name
            
            # Play audio (cross-platform)
            try:
                # Try different audio players based on platform
                if os.name == 'posix':  # Unix/Linux/macOS
                    if subprocess.run(["which", "afplay"], capture_output=True).returncode == 0:
                        self.audio_command = "afplay"
                        self.current_process = subprocess.Popen(["afplay", temp_filename])
                    elif subprocess.run(["which", "mpg123"], capture_output=True).returncode == 0:
                        self.audio_command = "mpg123"
                        self.current_process = subprocess.Popen(["mpg123", temp_filename])
                    elif subprocess.run(["which", "paplay"], capture_output=True).returncode == 0:
                        self.audio_command = "paplay"
                        self.current_process = subprocess.Popen(["paplay", temp_filename])
                    else:
                        raise FileNotFoundError("No audio player found (try: sudo apt install mpg123)")
                else:  # Windows
                    self.audio_command = "start"
                    self.current_process = subprocess.Popen(["start", temp_filename], shell=True)
                
                print(f"🔊 Playing audio with {self.audio_command} (PID: {self.current_process.pid})")
                
                # Wait for playback to complete or be interrupted
                if self.current_process:
                    self.current_process.wait()
                    
            finally:
                # Clean up temporary file
                os.unlink(temp_filename)
                self.current_process = None
            
        except Exception as e:
            print(f"❌ OpenAI TTS error: {e}")
            # Fallback - but this shouldn't happen since we handle audio players above
            if not self.should_stop:
                print("⚠️ Unexpected fallback to system TTS")
        finally:
            self.is_speaking = False
            self.current_process = None
            self.audio_command = None
    
    def _fallback_speak(self, text: str, blocking: bool = True) -> bool:
        """Fallback to macOS say command"""
        try:
            self.is_speaking = True
            print("🔄 Falling back to macOS say command")
            if blocking:
                self.current_process = subprocess.Popen(["say", text])
                if self.current_process:
                    self.current_process.wait()
                    self.current_process = None
            else:
                self.current_process = subprocess.Popen(["say", text])
            return True
        except Exception as e:
            print(f"❌ Fallback TTS error: {e}")
            return False
        finally:
            if blocking:
                self.is_speaking = False
    
    def stop_speaking(self):
        """Stop current speech"""
        try:
            self.should_stop = True
            
            # Terminate current process if running
            if self.current_process:
                self.current_process.terminate()
                try:
                    self.current_process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.current_process.kill()
                self.current_process = None
            
            # No need for pkill - we have the direct process handle!
            
            self.is_speaking = False
            print("🛑 Stopped speaking")
        except Exception as e:
            print(f"❌ Error stopping speech: {e}")
    
    def set_voice(self, voice: str):
        """Change the voice"""
        if voice in self.available_voices:
            self.voice = voice
            print(f"🎭 Voice changed to: {voice}")
        else:
            print(f"❌ Voice '{voice}' not available")
            print("Available voices:", self.available_voices)
    
    def test_voice(self, voice: str = None):
        """Test a specific voice"""
        old_voice = self.voice
        if voice:
            self.set_voice(voice)
        
        self.speak("Hello, this is a test of the OpenAI text to speech system.")
        
        if voice:
            self.voice = old_voice

class WorkshopOpenAITTS(OpenAITTS):
    """Specialized TTS for workshop assistant with predefined responses"""
    
    def __init__(self, voice: str = "alloy", api_key: str = None):
        """Initialize with workshop-optimized settings"""
        super().__init__(voice, api_key)
        
        # Workshop-specific response templates
        self.responses = {
            "wake_acknowledged": ["Yes?", "How can I help?", "I'm listening."],
            "stored": "Got it, I've stored the {item} in {location}.",
            "found": "The {item} is in {location}.",
            "not_found": "I don't have any record of {item}. Would you like to store it somewhere?",
            "updated": "I've moved the {item} from {old_location} to {new_location}.",
            "deleted": "I've removed the {item} from your inventory.",
            "listed": "I found {count} items.",
            "error": "Sorry, I had trouble with that. Could you try again?",
            "no_speech": "I didn't hear anything. Try again.",
            "unclear": "I couldn't understand that. Please repeat.",
            "goodbye": "Goodbye! Let me know if you need help finding anything."
        }
    
    def respond(self, response_type: str, **kwargs) -> bool:
        """
        Speak a predefined response with variable substitution
        
        Args:
            response_type: Type of response from self.responses
            **kwargs: Variables to substitute in the response
            
        Returns:
            True if successful, False otherwise
        """
        if response_type not in self.responses:
            return self.speak(f"Unknown response type: {response_type}")
        
        template = self.responses[response_type]
        
        # Handle list responses (pick first one for now)
        if isinstance(template, list):
            template = template[0]
        
        try:
            # Format template with provided variables
            message = template.format(**kwargs)
            return self.speak(message)
        except KeyError as e:
            print(f"❌ Missing variable for response: {e}")
            return self.speak(template)  # Speak unformatted if variables missing
    
    def acknowledge_wake_word(self):
        """Quick acknowledgment of wake word"""
        return self.respond("wake_acknowledged")
    
    def confirm_storage(self, item: str, location: str):
        """Confirm item storage"""
        return self.respond("stored", item=item, location=location)
    
    def report_location(self, item: str, location: str):
        """Report where an item is located"""
        return self.respond("found", item=item, location=location)
    
    def item_not_found(self, item: str):
        """Report that an item was not found"""
        return self.respond("not_found", item=item)

def test_openai_tts():
    """Test OpenAI TTS functionality"""
    print("🧪 Testing OpenAI Text-to-Speech")
    print("=" * 35)
    
    try:
        # Test basic TTS
        tts = OpenAITTS(voice="alloy")
        
        print("\n🎭 Available OpenAI voices:")
        for voice in tts.list_voices():
            print(f"  {voice}")
        
        print("\n🗣️ Testing OpenAI TTS:")
        tts.speak("Hello, this is a test of OpenAI's text to speech system.")
        
        print("\n🔧 Testing workshop TTS:")
        workshop_tts = WorkshopOpenAITTS(voice="nova")
        
        # Test workshop responses
        workshop_tts.acknowledge_wake_word()
        workshop_tts.confirm_storage("hammer", "toolbox drawer three")
        workshop_tts.report_location("screwdriver", "pegboard")
        workshop_tts.item_not_found("wrench")
        
        print("✅ OpenAI TTS tests completed")
        
    except ValueError as e:
        print(f"⚠️ {e}")
        print("Set OPENAI_API_KEY environment variable to test")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_openai_tts()