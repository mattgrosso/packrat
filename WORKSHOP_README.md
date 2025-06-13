# 🔧 Workshop Voice Assistant

A hands-free voice assistant for organizing tools and hardware in your workshop. Tell it where you store things, then ask it later where to find them.

## ✨ Features

- **Wake word activation** - Say "Computer" to activate
- **Natural language commands** - "Store hammer in toolbox drawer three"
- **Smart parsing** - Uses GPT-4 to understand variations in phrasing
- **Spoken responses** - Confirms actions and answers questions out loud
- **Persistent storage** - SQLite database remembers everything
- **Offline wake word** - No internet needed for activation
- **Real-time processing** - Fast OpenAI Whisper API transcription

## 🎯 Example Workflow

1. **"Computer"** → *beep* (wake word detected)
2. **"Store hammer in toolbox drawer three"**
3. **Assistant:** "Got it, I've stored the hammer in toolbox drawer three"
4. Later... **"Computer"** → *beep*
5. **"Where is the hammer?"**
6. **Assistant:** "The hammer is in toolbox drawer three"

## 📋 Command Examples

### Storage Commands
- "Store hammer in toolbox drawer three"
- "I put the screwdriver on the pegboard"
- "The drill is on the workbench"
- "Move the wrench to the red cabinet"

### Retrieval Commands
- "Where is the hammer?"
- "Find my screwdriver"
- "Where did I put the drill?"

### List Commands
- "What tools do I have?"
- "List everything in the toolbox"
- "Show me all hand tools"

### Management Commands
- "Delete the old hammer"
- "Remove screwdriver from inventory"

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Install PortAudio for microphone access
brew install portaudio

# Install Python packages
pip3 install pyaudio pvporcupine openai
```

### 2. Get OpenAI API Key
- Get an API key from https://platform.openai.com/api-keys
- Export it as an environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 3. Run the Assistant
```bash
python3 workshop_assistant.py
```

### 4. Test It Out
- Say **"Computer"** (wait for beep)
- Say **"Store hammer in toolbox drawer three"**
- Later, say **"Computer"** then **"Where is the hammer?"**

## 📁 File Structure

```
workshop_assistant/
├── workshop_assistant.py     # Main application
├── wake_word_detector.py     # Porcupine wake word detection
├── speech_processor.py       # Audio recording & Whisper API
├── command_parser.py         # GPT-4 with function calling
├── database.py              # SQLite operations
├── tts.py                   # macOS text-to-speech
├── config.py                # Configuration settings
├── workshop.db              # SQLite database (created automatically)
└── WORKSHOP_ASSISTANT_PLAN.md # Detailed technical plan
```

## ⚙️ Configuration

Edit `config.py` to customize:

- **Wake word**: Choose from built-in Porcupine keywords
- **Voice**: Change macOS TTS voice
- **Recording duration**: Adjust command recording time
- **Database path**: Change where data is stored

Available wake words: `computer`, `hey google`, `jarvis`, `alexa`, `ok google`, etc.

## 🔧 Technical Details

### Architecture
1. **Wake Word Detection**: Porcupine (offline, lightweight)
2. **Speech Recognition**: OpenAI Whisper API (fast, accurate)
3. **Command Parsing**: GPT-4 with function calling (natural language)
4. **Database**: SQLite (local, persistent)
5. **Text-to-Speech**: macOS `say` command

### Database Schema
```sql
CREATE TABLE workshop_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    location TEXT NOT NULL,
    description TEXT,
    category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Function Calling
The assistant uses GPT-4 function calling with these functions:
- `store_item(item_name, location, description, category)`
- `find_item(item_name)`
- `list_items(category, location)`
- `delete_item(item_name)`

## 🧪 Testing Components

Test individual components:

```bash
# Test wake word detection
python3 wake_word_detector.py

# Test database operations
python3 database.py

# Test speech processing (needs API key)
python3 speech_processor.py

# Test text-to-speech
python3 tts.py

# Test command parsing (needs API key)
python3 command_parser.py
```

## 💰 Cost Estimation

**OpenAI API Usage:**
- Whisper API: ~$0.006 per minute of audio
- GPT-4 API: ~$0.03 per request

**Typical usage**: ~$0.10-0.20 per hour of active use

## 🔒 Privacy & Security

- **Wake word detection**: Runs completely offline
- **Audio processing**: Only sent to OpenAI after wake word
- **Database**: Stored locally on your machine
- **No always-on listening**: Only processes audio after activation

## 🐛 Troubleshooting

### "OpenAI API key required"
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### "macOS say command not available"
- This only works on macOS
- Make sure you're running on a Mac

### "Error initializing Porcupine"
```bash
pip3 install pvporcupine
```

### Wake word not detected
- Speak clearly and at normal volume
- Try adjusting sensitivity in `config.py`
- Test different wake words

### Audio recording issues
```bash
brew install portaudio
pip3 install pyaudio
```

## 🎮 Advanced Usage

### Custom Wake Words
Edit `config.py` to choose from available Porcupine keywords:
```python
WAKE_WORD = "jarvis"  # or "hey google", "alexa", etc.
```

### Voice Customization
```python
# List available voices
python3 -c "from tts import TextToSpeech; tts = TextToSpeech(); print(tts.list_voices())"

# Use a specific voice
TTS_VOICE = "Samantha"  # or "Alex", "Victoria", etc.
```

### Database Backup
```bash
# Backup your workshop inventory
cp workshop.db workshop_backup.db

# View database contents
sqlite3 workshop.db "SELECT * FROM workshop_items;"
```

## 🚧 Future Enhancements

- [ ] Custom wake word training
- [ ] Voice activity detection for better audio capture  
- [ ] Location hierarchies (toolbox → drawer 3 → top shelf)
- [ ] Export/import inventory data
- [ ] Web interface for inventory management
- [ ] Multiple user support
- [ ] Integration with workshop management systems

## 📝 License

MIT License - Feel free to modify and use for your workshop!

---

**Built with:** Python, OpenAI APIs, Porcupine Wake Word, SQLite, macOS TTS