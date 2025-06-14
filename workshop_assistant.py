#!/usr/bin/env python3

import os
import time
import threading
import json

from continuous_detector import ContinuousDetector
from smart_command_parser import SmartCommandParser
from openai_tts import WorkshopOpenAITTS


class WorkshopAssistant:
    def __init__(self, api_key: str = None, wake_word: str = "computer", voice: str = "alloy"):
        """
        Initialize the workshop voice assistant

        Args:
            api_key: OpenAI API key (or uses OPENAI_API_KEY env var)
            wake_word: Wake word for activation (e.g., "computer")
            voice: OpenAI TTS voice (alloy, echo, fable, onyx, nova, shimmer)
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
            self.tts = WorkshopOpenAITTS(voice=voice, api_key=self.api_key)
            self.command_parser = SmartCommandParser(api_key=self.api_key, wake_word=wake_word)
            self.wake_detector = ContinuousDetector(
                keyword=wake_word,
                callback=self.on_command_received,
                api_key=self.api_key,
                interrupt_callback=self.handle_interrupt,
            )

            print("✅ All components initialized successfully!")

        except Exception as e:
            print(f"❌ Error initializing components: {e}")
            raise

    def on_command_received(self, command_text: str):
        """Callback function when full command is received"""
        if self.is_processing_command:
            print("⚠️  Already processing a command, ignoring new command")
            return

        self.is_processing_command = True

        # Run command processing in a separate thread
        thread = threading.Thread(target=self.process_command, args=(command_text,))
        thread.daemon = True
        thread.start()

    def process_command(self, command_text: str):
        """Process a voice command"""
        try:
            print(f"🎯 Processing command: '{command_text}'")

            # Parse and execute command directly (no additional recording needed)
            response = self.command_parser.parse_command(command_text)

            if response:
                print(f"🤖 Response: '{response}'")

                # Switch to interrupt detection mode during TTS
                self.wake_detector.set_mode_interrupt()

                # Start TTS in non-blocking mode
                self.tts.speak(response, blocking=False)

                # Wait for audio to actually start playing
                print("⏳ Waiting for audio to start...")
                while not self.tts.is_currently_speaking() and not self.tts.should_stop:
                    time.sleep(0.05)  # Check every 50ms

                if self.tts.is_currently_speaking():
                    print("🔊 Audio started, interrupt detection active")
                    # Wait for TTS to actually finish while interrupt detection is active
                    while self.tts.is_currently_speaking() and not self.tts.should_stop:
                        time.sleep(0.1)  # Check every 100ms

            else:
                self.tts.respond("error")

        except Exception as e:
            print(f"❌ Error processing command: {e}")
            self.tts.respond("error")
        finally:
            # Make sure to switch back to wake word detection mode
            self.wake_detector.set_mode_wake_word()
            self.is_processing_command = False

    def handle_interrupt(self):
        """Handle interrupt command during TTS playback"""
        print("🛑 Interrupt command received - stopping TTS")
        self.tts.stop_speaking()
        # Mode will be switched back to wake word in the finally block

    def start(self):
        """Start the workshop assistant"""
        if self.is_running:
            print("Assistant is already running")
            return

        self.is_running = True

        print("\n🚀 Workshop Assistant Started!")
        print("=" * 40)
        print(f"🎧 Wake word: '{self.wake_word}'")
        print("🗣️  Say the wake word followed by your command in one go")
        print("⏹️  Press Ctrl+C to stop")
        print("\n📝 Example commands:")
        print(f"  - '{self.wake_word.title()}, store hammer in toolbox drawer three'")
        print(f"  - '{self.wake_word.title()}, where is the hammer?'")
        print(f"  - '{self.wake_word.title()}, list all tools'")
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
        if hasattr(self, "wake_detector"):
            self.wake_detector.cleanup()

        if hasattr(self, "tts"):
            self.tts.stop_speaking()

        print("✅ Workshop Assistant stopped")

    def get_status(self) -> dict:
        """Get current status of the assistant"""
        return {
            "running": self.is_running,
            "processing_command": self.is_processing_command,
            "wake_word": self.wake_word,
            "components_initialized": all(
                [
                    hasattr(self, "tts"),
                    hasattr(self, "command_parser"),
                    hasattr(self, "wake_detector"),
                ]
            ),
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

    # Load configuration using the same pattern as continuous_detector
    def deep_merge(base: dict, override: dict) -> dict:
        """Deep merge override into base dictionary"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    # Load defaults first (always exists in repo)
    with open("config.defaults.json", "r") as f:
        config = json.load(f)

    # Apply local overrides
    try:
        with open("config.local.json", "r") as f:
            local_config = json.load(f)
            config = deep_merge(config, local_config)
    except (FileNotFoundError, json.JSONDecodeError):
        pass  # No local config, use defaults

    wake_word = config["wake_word"]["keyword"]
    voice = config["tts"]["voice"]

    try:
        # Create and start assistant
        assistant = WorkshopAssistant(api_key=api_key, wake_word=wake_word, voice=voice)

        assistant.start()

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
