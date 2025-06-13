#!/usr/bin/env python3

import os
import time

def test_components():
    """Test individual components without API keys"""
    print("🧪 Testing Workshop Assistant Components")
    print("=" * 45)
    
    # Test 1: Database
    print("\n1️⃣ Testing Database...")
    try:
        from database import WorkshopDatabase
        db = WorkshopDatabase("test_workshop.db")
        db.store_item("test_hammer", "test_toolbox", "test description", "tool")
        item = db.find_item("test_hammer")
        if item and item['location'] == 'test_toolbox':
            print("✅ Database: PASS")
        else:
            print("❌ Database: FAIL")
        os.remove("test_workshop.db")
    except Exception as e:
        print(f"❌ Database: ERROR - {e}")
    
    # Test 2: TTS
    print("\n2️⃣ Testing Text-to-Speech...")
    try:
        from tts import WorkshopTTS
        tts = WorkshopTTS()
        print("✅ TTS: PASS (initialization successful)")
        # Note: Not actually speaking to avoid noise during test
    except Exception as e:
        print(f"❌ TTS: ERROR - {e}")
    
    # Test 3: Wake Detector
    print("\n3️⃣ Testing Simple Wake Detector...")
    try:
        from simple_wake_detector import SimpleWakeDetector
        detector = SimpleWakeDetector(mode="manual")
        detector.cleanup()
        print("✅ Wake Detector: PASS")
    except Exception as e:
        print(f"❌ Wake Detector: ERROR - {e}")
    
    # Test 4: Speech Processor (without API)
    print("\n4️⃣ Testing Speech Processor (basic init)...")
    try:
        # Test basic audio setup
        import pyaudio
        audio = pyaudio.PyAudio()
        audio.terminate()
        print("✅ Speech Processor (audio): PASS")
    except Exception as e:
        print(f"❌ Speech Processor: ERROR - {e}")
    
    # Test 5: Command Parser (without API)
    print("\n5️⃣ Testing Command Parser (requires API key)...")
    if os.getenv("OPENAI_API_KEY"):
        try:
            from command_parser import CommandParser
            parser = CommandParser()
            print("✅ Command Parser: PASS")
        except Exception as e:
            print(f"❌ Command Parser: ERROR - {e}")
    else:
        print("⚠️  Command Parser: SKIP (no API key)")
    
    print("\n🎯 Component Test Summary:")
    print("- Database: Local SQLite storage")
    print("- TTS: macOS say command")  
    print("- Wake Detection: Manual (ENTER) or Voice Activity")
    print("- Speech Processing: OpenAI Whisper API (requires key)")
    print("- Command Parsing: OpenAI GPT-4 (requires key)")
    
    print("\n📋 To run full assistant:")
    print("1. Set OPENAI_API_KEY environment variable")
    print("2. Run: python3 workshop_assistant.py")
    print("3. Choose activation mode (manual recommended)")
    print("4. Press ENTER to activate, then speak commands")

def demo_workflow():
    """Show what the workflow would look like"""
    print("\n🎬 Demo Workflow (simulation)")
    print("=" * 30)
    
    print("User: *presses ENTER*")
    print("Assistant: *beep* 🔔")
    print("User: 'Store hammer in toolbox drawer three'")
    print("Assistant: 'Got it, I've stored the hammer in toolbox drawer three'")
    print()
    print("User: *presses ENTER*") 
    print("Assistant: *beep* 🔔")
    print("User: 'Where is the hammer?'")
    print("Assistant: 'The hammer is in toolbox drawer three'")
    print()
    print("✨ This is the actual workflow once API key is set!")

if __name__ == "__main__":
    test_components()
    demo_workflow()