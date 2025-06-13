# Workshop Voice Assistant Plan

A hands-free voice assistant for organizing tools and hardware in a workshop environment.

## Overview

**Goal**: Tell the assistant where you store tools, then ask it later where to find them.

**Example workflow**:
1. "Hey Computer" (wake word)
2. "Store hammer in toolbox drawer three"
3. Assistant: "Got it, I've stored the hammer in toolbox drawer three"
4. Later... "Hey Computer"
5. "Where is the hammer?"
6. Assistant: "The hammer is in toolbox drawer three"

## Technical Architecture

### 1. Wake Word Detection
- **Library**: `pvporcupine` (Picovoice)
- **Wake word**: Default from library (e.g., "Computer", "Hey Pico")
- **Why**: Lightweight, works offline, no constant processing
- **Flow**: Continuously listen for wake word → trigger command recording

### 2. Speech Recognition
- **Service**: OpenAI Whisper API
- **Trigger**: After wake word detected
- **Duration**: Record 3-5 seconds of audio after wake word
- **Format**: Convert to text for LLM processing

### 3. Command Parsing & Processing
- **Service**: OpenAI GPT-4 with Function Calling
- **Functions**:
  - `store_item(item_name, location, description=None, category=None)`
  - `find_item(item_name)`
  - `list_items(category=None, location=None)`
  - `update_item_location(item_name, new_location)`
  - `delete_item(item_name)`

### 4. Database Schema
- **Type**: SQLite (local, simple, persistent)
- **Table**: `workshop_items`
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

### 5. Text-to-Speech
- **Service**: macOS `say` command
- **Voices**: System default (can be customized later)
- **Alternative**: OpenAI TTS API for more natural speech

### 6. Response Generation
- **Method**: LLM-generated responses with templates
- **Tone**: Friendly, concise, workshop-appropriate
- **Examples**:
  - "Got it, I've stored the [item] in [location]"
  - "The [item] is in [location]"
  - "I don't have any record of [item]. Would you like to store it somewhere?"

## Application Flow

```
1. START: Listen for wake word
   ↓
2. WAKE WORD DETECTED: Play beep, start recording
   ↓
3. RECORD COMMAND: Capture 3-5 seconds of audio
   ↓
4. TRANSCRIBE: Send audio to Whisper API
   ↓
5. PARSE: Send text to GPT-4 with function calling
   ↓
6. EXECUTE: Call appropriate database function
   ↓
7. RESPOND: Generate response and speak with `say`
   ↓
8. RETURN TO STEP 1
```

## Command Categories

### Storage Commands
- "Store [item] in [location]"
- "I put the [item] in [location]"
- "[Item] is in [location]"
- "Move [item] to [location]"

### Retrieval Commands
- "Where is [item]?"
- "Find [item]"
- "Where did I put [item]?"

### List Commands
- "What tools do I have?"
- "List everything in [location]"
- "Show me all [category] items"

### Management Commands
- "Delete [item]"
- "Remove [item] from inventory"

## Error Handling

### Speech Recognition Errors
- Timeout: "I didn't hear anything. Try again."
- Unclear audio: "I couldn't understand that. Please repeat."
- No wake word: Continue listening

### Command Parsing Errors
- Unknown intent: "I'm not sure what you want me to do. Try rephrasing."
- Missing information: "What would you like me to store?" / "Where should I store it?"

### Database Errors
- Item not found: "I don't have any record of [item]. Would you like to store it?"
- Duplicate items: "I already have [item] in [old_location]. Should I move it to [new_location]?"

## Implementation Plan

### Phase 1: Core Functionality
1. Set up wake word detection
2. Implement basic audio recording after wake word
3. Set up OpenAI Whisper API integration
4. Create SQLite database and basic operations
5. Implement OpenAI GPT-4 with function calling
6. Add text-to-speech with `say` command

### Phase 2: Enhanced Features
1. Better error handling and edge cases
2. Confirmation dialogs for destructive operations
3. Fuzzy matching for item names
4. Categories and tags
5. Location hierarchies (e.g., "toolbox → drawer 3 → top shelf")

### Phase 3: Advanced Features
1. Voice training for better recognition
2. Custom wake words
3. Export/import inventory
4. Integration with workshop management systems
5. Multiple user support

## Dependencies

```bash
pip install pvporcupine openai sqlite3 pyaudio numpy
```

## File Structure

```
workshop_assistant/
├── main.py                 # Main application loop
├── wake_word_detector.py   # Porcupine wake word detection
├── speech_processor.py     # Audio recording and Whisper API
├── command_parser.py       # OpenAI GPT-4 with function calling
├── database.py            # SQLite operations
├── tts.py                 # Text-to-speech with say command
├── config.py              # Configuration and API keys
└── workshop.db            # SQLite database file
```

## Configuration

```python
# config.py
OPENAI_API_KEY = "your-api-key"
WAKE_WORD = "computer"  # or pvporcupine default
RECORD_DURATION = 4  # seconds after wake word
WHISPER_MODEL = "whisper-1"
GPT_MODEL = "gpt-4"
TTS_VOICE = "default"  # macOS say voice
DATABASE_PATH = "workshop.db"
```

## Testing Strategy

### Unit Tests
- Database operations (store, retrieve, update, delete)
- Audio processing pipeline
- Function calling parsing

### Integration Tests
- End-to-end workflow simulation
- Error handling scenarios
- Multiple command sequences

### Manual Testing
- Real workshop environment testing
- Background noise tolerance
- Different speaking styles and accents

## Success Metrics

1. **Wake word accuracy**: >95% detection rate
2. **Speech recognition accuracy**: >90% for workshop vocabulary
3. **Command parsing accuracy**: >95% for supported commands
4. **Response time**: <3 seconds from wake word to spoken response
5. **Reliability**: 99% uptime during workshop sessions

---

**Next Steps**: Implement Phase 1 components in order, testing each integration point before moving to the next component.