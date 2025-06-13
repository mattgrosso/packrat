#!/usr/bin/env python3

import subprocess
import os
import threading
from typing import Optional

class TextToSpeech:
    def __init__(self, voice: str = "default", rate: int = 200):
        """
        Initialize text-to-speech using macOS say command
        
        Args:
            voice: Voice name (use list_voices() to see options)
            rate: Speaking rate (words per minute, 100-500)
        """
        self.voice = voice if voice != "default" else None
        self.rate = rate
        self.is_speaking = False
        
        # Test if say command is available
        try:
            subprocess.run(["say", ""], capture_output=True, check=False, timeout=1)
            print("✅ Text-to-speech initialized with macOS say command")
        except FileNotFoundError:
            print("❌ macOS say command not available")
            raise RuntimeError("macOS say command required for text-to-speech")
    
    def list_voices(self) -> list:
        """List available system voices"""
        try:
            result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, check=True)
            voices = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    # Parse voice name (first word before space)
                    voice_name = line.split()[0]
                    voices.append(voice_name)
            return voices
        except subprocess.CalledProcessError:
            return []
    
    def speak(self, text: str, blocking: bool = True) -> bool:
        """
        Speak the given text
        
        Args:
            text: Text to speak
            blocking: Whether to wait for speech to complete
            
        Returns:
            True if successful, False otherwise
        """
        if not text or not text.strip():
            return False
        
        try:
            # Build say command
            cmd = ["say"]
            
            if self.voice:
                cmd.extend(["-v", self.voice])
            
            cmd.extend(["-r", str(self.rate)])
            cmd.append(text)
            
            print(f"🗣️  Speaking: '{text}'")
            
            if blocking:
                # Run synchronously
                self.is_speaking = True
                result = subprocess.run(cmd, check=True)
                self.is_speaking = False
                return result.returncode == 0
            else:
                # Run asynchronously
                def speak_async():
                    self.is_speaking = True
                    try:
                        subprocess.run(cmd, check=True)
                    except subprocess.CalledProcessError as e:
                        print(f"❌ Error speaking: {e}")
                    finally:
                        self.is_speaking = False
                
                thread = threading.Thread(target=speak_async)
                thread.daemon = True
                thread.start()
                return True
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Error speaking text: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def stop_speaking(self):
        """Stop current speech"""
        try:
            # Kill any running say processes
            subprocess.run(["pkill", "say"], check=False)
            self.is_speaking = False
            print("🛑 Stopped speaking")
        except Exception as e:
            print(f"❌ Error stopping speech: {e}")
    
    def set_voice(self, voice: str):
        """Change the voice"""
        available_voices = self.list_voices()
        if voice in available_voices:
            self.voice = voice
            print(f"🎭 Voice changed to: {voice}")
        else:
            print(f"❌ Voice '{voice}' not available")
            print("Available voices:", available_voices[:5], "...")
    
    def set_rate(self, rate: int):
        """Change the speaking rate"""
        if 50 <= rate <= 500:
            self.rate = rate
            print(f"⚡ Speaking rate changed to: {rate} WPM")
        else:
            print(f"❌ Rate must be between 50-500 WPM")
    
    def test_voice(self, voice: str = None):
        """Test a specific voice"""
        old_voice = self.voice
        if voice:
            self.set_voice(voice)
        
        self.speak("Hello, this is a test of the text to speech system.")
        
        if voice:
            self.voice = old_voice

class WorkshopTTS(TextToSpeech):
    """Specialized TTS for workshop assistant with predefined responses"""
    
    def __init__(self, voice: str = "default", rate: int = 180):
        """Initialize with workshop-optimized settings"""
        super().__init__(voice, rate)
        
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

def test_tts():
    """Test TTS functionality"""
    print("🧪 Testing Text-to-Speech")
    print("=" * 30)
    
    # Test basic TTS
    tts = TextToSpeech()
    
    print("\n🎭 Available voices:")
    voices = tts.list_voices()
    for i, voice in enumerate(voices[:5]):  # Show first 5
        print(f"  {voice}")
    if len(voices) > 5:
        print(f"  ... and {len(voices) - 5} more")
    
    print("\n🗣️  Testing basic speech:")
    tts.speak("Hello, this is a test of the text to speech system.")
    
    print("\n🔧 Testing workshop TTS:")
    workshop_tts = WorkshopTTS()
    
    # Test workshop responses
    workshop_tts.acknowledge_wake_word()
    workshop_tts.confirm_storage("hammer", "toolbox drawer three")
    workshop_tts.report_location("screwdriver", "pegboard")
    workshop_tts.item_not_found("wrench")
    
    print("✅ TTS tests completed")

if __name__ == "__main__":
    test_tts()