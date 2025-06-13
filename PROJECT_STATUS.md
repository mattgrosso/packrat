# Workshop Voice Assistant - Project Status

## Overview
A hands-free voice assistant for organizing workshop tools and hardware. Say "Computer, store hammer in toolbox drawer three" or "Computer, where is the hammer?" and the assistant will manage your inventory using natural language.

## Current Status: ✅ FULLY FUNCTIONAL

## Core Components (Clean & Minimal)

### Essential Files
- **start_assistant.py** - Quick start script (easiest way to launch)
- **workshop_assistant.py** - Main application entry point
- **continuous_detector.py** - Wake word detection + command recording with silence detection
- **smart_command_parser.py** - LLM-powered command parsing with full database context
- **openai_tts.py** - OpenAI TTS integration (nova voice)
- **database.py** - SQLite database for tool storage
- **workshop.db** - Your tool inventory database
- **tune_silence_threshold.py** - Utility to tune silence detection for your environment
- **inspect_db.py** - Utility to view database contents
- **PROJECT_STATUS.md** - This documentation file

### Working Configuration
- **Wake word**: "computer" (also responds to "compute", "comput")
- **Voice**: "nova" (OpenAI female voice)
- **Silence threshold**: 834 RMS (tuned for workshop environment)
- **Silence duration**: 1.5 seconds to end recording
- **Max recording**: 10 seconds
- **APIs**: OpenAI Whisper, GPT-4, TTS

## Database Schema
```sql
CREATE TABLE tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    location TEXT NOT NULL,
    description TEXT,
    category TEXT,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## How It Works
1. **Continuous Monitoring**: Listens for wake word using local Whisper tiny model
2. **Command Recording**: Records full command with automatic silence detection
3. **Cloud Transcription**: Uses OpenAI Whisper API for accurate command transcription
4. **Smart Parsing**: GPT-4 with function calling processes commands with full database context
5. **Voice Response**: OpenAI TTS responds with confirmation/results

## Usage Examples
- "Computer, store hammer in toolbox drawer three"
- "Computer, where is the hammer?"
- "Computer, what cutting tools do I have?"
- "Computer, list all tools in the garage"

## Dependencies
- openai
- whisper
- pyaudio
- numpy
- sqlite3

## Quick Start
```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Launch the assistant (easiest way)
python3 start_assistant.py

# Or run directly
python3 workshop_assistant.py
```

## Performance Notes
- Wake word detection uses local tiny model (cost-free)
- Command transcription uses OpenAI API (~$0.006 per minute)
- Command parsing uses GPT-4 (~$0.03 per request)
- TTS uses OpenAI API (~$0.015 per 1K characters)

## Recent Improvements
- Improved wake word sensitivity (no_speech_threshold: 0.3)
- Multiple wake word variants for better detection
- Tuned silence threshold for workshop environment
- Switched to OpenAI TTS with nova voice

## Project Cleanup Completed ✅
- Removed 15+ development prototype files
- Removed unused imports and dependencies
- Cleaned up outdated documentation
- Left only essential, working components

## Key Technical Details
- Uses continuous detection approach (not wake-word-then-wait)
- Silence detection prevents timeout issues
- Full database context provided to LLM for intelligent queries
- Fallback TTS to macOS 'say' command if OpenAI fails
- Thread-safe command processing prevents overlapping responses

Last Updated: $(date)