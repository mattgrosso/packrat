#!/usr/bin/env python3

import os
import time
import threading
from typing import Optional

from local_keyword_detector import LocalKeywordDetector
from speech_processor import SpeechProcessor
from smart_command_parser import SmartCommandParser
from tts import WorkshopTTS

class WorkshopAssistant:
    def __init__(self, api_key: str = None, wake_word: str = "computer", voice: str = "default"):
        """
        Initialize the workshop voice assistant
        
        Args:
            api_key: OpenAI API key (or uses OPENAI_API_KEY env var)
            wake_word: Wake word for activation (e.g., "computer")
            voice: TTS voice to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env var or pass api_key parameter.")
        
        self.wake_word = wake_word
        self.is_running = False
        self.is_processing_command = False
        
        print("🔧 Initializing Workshop Assistant...")
        print("=" * 40)
        
        # Initialize components
        try:
            self.tts = WorkshopTTS(voice=voice, rate=180)
            self.speech_processor = SpeechProcessor(api_key=self.api_key)
            self.command_parser = SmartCommandParser(api_key=self.api_key)
            self.wake_detector = LocalKeywordDetector(
                keyword=wake_word,
                callback=self.on_wake_word_detected,
                model_size="tiny"  # Fast local model for wake words
            )
            
            print("✅ All components initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing components: {e}")
            raise
    
    def on_wake_word_detected(self):
        """Callback function when wake word is detected"""
        if self.is_processing_command:
            print("⚠️  Already processing a command, ignoring wake word")
            return
        
        self.is_processing_command = True
        
        # Run command processing in a separate thread to avoid blocking wake word detection
        thread = threading.Thread(target=self.process_command)
        thread.daemon = True
        thread.start()
    
    def process_command(self):
        """Process a voice command after wake word detection"""
        try:
            # Acknowledge wake word
            print("🎯 Processing voice command...")
            self.tts.acknowledge_wake_word()
            
            # Record and transcribe command
            command_text = self.speech_processor.record_and_transcribe(duration=4)
            
            if not command_text:
                self.tts.respond("no_speech")
                return
            
            # Parse and execute command
            print(f"💬 Command: '{command_text}'")
            response = self.command_parser.parse_command(command_text)
            
            if response:
                print(f"🤖 Response: '{response}'")
                self.tts.speak(response)
            else:
                self.tts.respond("error")
                
        except Exception as e:
            print(f"❌ Error processing command: {e}")
            self.tts.respond("error")
        finally:
            self.is_processing_command = False
            print("✅ Command processing completed\n")
    
    def start(self):
        """Start the workshop assistant"""
        if self.is_running:
            print("Assistant is already running")
            return
        
        self.is_running = True
        
        print("\n🚀 Workshop Assistant Started!")
        print("=" * 40)
        print(f"🎧 Wake word: '{self.wake_word}'")
        print("🗣️  Say the wake phrase, then give a command")
        print("⏹️  Press Ctrl+C to stop")
        print("\n📝 Example commands:")
        print("  - 'Store hammer in toolbox drawer three'")
        print("  - 'Where is the hammer?'")
        print("  - 'List all tools'")
        print("-" * 40)
        
        try:
            # Start wake word detection (blocking)
            self.wake_detector.start_listening()
            
        except KeyboardInterrupt:
            print("\n🛑 Stopping Workshop Assistant...")
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the workshop assistant"""
        self.is_running = False
        
        print("🔄 Cleaning up...")
        
        # Stop components
        if hasattr(self, 'wake_detector'):
            self.wake_detector.cleanup()
        
        if hasattr(self, 'speech_processor'):
            self.speech_processor.cleanup()
        
        if hasattr(self, 'tts'):
            self.tts.stop_speaking()
        
        print("✅ Workshop Assistant stopped")
    
    def get_status(self) -> dict:
        """Get current status of the assistant"""
        return {
            "running": self.is_running,
            "processing_command": self.is_processing_command,
            "wake_word": self.wake_word,
            "components_initialized": all([
                hasattr(self, 'tts'),
                hasattr(self, 'speech_processor'),
                hasattr(self, 'command_parser'),
                hasattr(self, 'wake_detector')
            ])
        }

def main():
    """Main function to run the workshop assistant"""
    print("🔧 Workshop Voice Assistant")
    print("==========================")
    print("A hands-free assistant for organizing your workshop tools and hardware")
    print()
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OpenAI API key required!")
        print("Set the OPENAI_API_KEY environment variable:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Configuration
    wake_word = "computer"  # Simple keyword detection
    voice = "default"       # macOS system voice
    
    try:
        # Create and start assistant
        assistant = WorkshopAssistant(
            api_key=api_key,
            wake_word=wake_word,
            voice=voice
        )
        
        assistant.start()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()