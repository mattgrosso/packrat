# Workshop Voice Assistant - Project Status

## Overview
A hands-free voice assistant for organizing workshop tools and hardware. Fully configurable wake word and voice settings. The assistant manages your inventory using natural language commands.

## Current Status: ✅ PRODUCTION READY

## Core Components

### Essential Files
- **start_assistant.py** - Quick start script (easiest way to launch)
- **workshop_assistant.py** - Main application entry point
- **continuous_detector.py** - Unified wake word + interrupt detection with live transcription
- **smart_command_parser.py** - GPT-4.1 powered command parsing with full database context
- **openai_tts.py** - Cross-platform OpenAI TTS with interrupt support
- **database.py** - SQLite database for tool storage
- **config.defaults.json** - Default configuration (committed to repo)
- **config.local.json** - Local configuration overrides (not committed)
- **pyproject.toml** - Modern Python packaging with dependencies
- **README.md** - Complete setup and configuration guide

### Configuration System
- **Two-file config**: Defaults + local overrides
- **Configurable wake word**: Default "computer", easily changed to any word
- **Configurable voice**: Any OpenAI voice (alloy, echo, fable, onyx, nova, shimmer)  
- **Tunable audio settings**: Silence threshold, chunk size, sample rate
- **Customizable stop words**: For interrupting TTS responses
- **Deep merge**: Only override what you need to change

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
1. **Wake Word Detection**: Unified detection thread listens for configurable wake word using local Whisper tiny model
2. **Command Recording**: Records full command with automatic silence detection (1.5s timeout)
3. **Live Transcription**: Shows real-time transcription of what it hears for transparency
4. **Cloud Transcription**: Uses OpenAI Whisper API for accurate full command transcription
5. **Smart Parsing**: GPT-4.1 with function calling processes commands with complete database context
6. **Voice Response**: OpenAI TTS responds with confirmation/results
7. **Interrupt Support**: Say "stop" to interrupt TTS responses
8. **Mode Switching**: Seamlessly switches between wake word detection and interrupt detection

## Usage Examples
- "[Wake word], store hammer in toolbox drawer three"
- "[Wake word], where is the hammer?"
- "[Wake word], what cutting tools do I have?"
- "[Wake word], list all tools in the garage"
- "stop" / "quiet" / "cancel" (to interrupt responses)

## Dependencies
All dependencies managed via `pyproject.toml`:
- openai (Whisper, GPT-4.1, TTS)
- whisper (local wake word detection) 
- pyaudio (audio capture)
- numpy (audio processing)

## Quick Start
```bash
# Install dependencies
pip install -e .

# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Install audio player (Linux)
sudo apt install mpg123

# Launch the assistant
python start_assistant.py
```

## Performance & Timing
- **Wake word detection**: Local tiny model (cost-free, ~100ms)
- **Whisper transcription**: OpenAI API (~1-2s, $0.006/min)
- **GPT-4.1 completion**: OpenAI API (~1-2s, varies by usage)
- **TTS generation**: OpenAI API (~1-3s, $0.015/1K chars)
- **Total response time**: ~3-7 seconds end-to-end

## Major Features Added
- **Configurable wake words**: Easy customization via config files
- **Interrupt detection**: Unified thread handles wake word + stop commands
- **Live transcription**: Real-time display of what's being heard
- **Cross-platform audio**: Supports Linux (paplay/mpg123), macOS (afplay), Windows
- **Configuration system**: Defaults + local overrides pattern
- **Modern packaging**: pyproject.toml with proper dependency management
- **Performance timing**: Detailed timing for all OpenAI API calls

## Project Cleanup Completed ✅
- Removed 15+ development prototype files
- Removed unused imports and dependencies
- Cleaned up outdated documentation
- Left only essential, working components

## Key Technical Details
- **Unified detection thread**: Single thread handles both wake word and interrupt detection
- **Mode switching**: Seamlessly switches between detection modes without thread conflicts
- **Silence detection**: Automatic recording termination prevents timeout issues
- **Full database context**: Complete inventory provided to GPT-4.1 for intelligent queries
- **Cross-platform TTS**: Automatically detects and uses available audio players
- **Thread-safe processing**: Prevents overlapping command responses
- **Deep config merging**: Sophisticated override system for easy customization
- **Live debugging**: Real-time transcription display for troubleshooting

## Architecture Improvements
- **Eliminated microphone conflicts**: No more competing audio streams
- **Simplified configuration**: Two-file system with intelligent merging
- **Better error handling**: Graceful fallbacks throughout the pipeline
- **Performance monitoring**: Built-in timing for optimization
- **Modern Python practices**: Type hints, proper packaging, clean imports

Last Updated: 2025-06-14

