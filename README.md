# Packrat - Workshop Voice Assistant

A hands-free voice assistant for organizing your workshop tools and hardware using OpenAI's Whisper, GPT-4.1, and TTS.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -e .
   ```

2. **Set your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```

3. **Install audio player (Linux):**
   ```bash
   sudo apt install mpg123
   # or
   sudo apt install pulseaudio-utils
   ```

4. **Run the assistant:**
   ```bash
   python start_assistant.py
   ```

## Configuration

The assistant uses a two-file configuration system for easy customization:

### Default Configuration (`config.defaults.json`)

This file contains all default settings and is committed to the repository. **Do not modify this file** - it ensures consistent defaults for all users.

```json
{
  "audio": {
    "silence_threshold": 834,
    "chunk_size": 1024,
    "format": "paInt16", 
    "channels": 1,
    "rate": 16000
  },
  "wake_word": {
    "keyword": "computer",
    "variants": ["computer", "compute", "comput"],
    "model": "tiny",
    "timeout": 30
  },
  "interrupt": {
    "stop_words": ["stop", "computer stop", "quiet", "silence", "cancel"]
  },
  "tts": {
    "voice": "alloy",
    "model": "tts-1"
  }
}
```

### Local Overrides (`config.local.json`)

Create this file to customize settings for your specific setup. This file is ignored by git and won't be committed. You only need to specify the settings you want to change:

```json
{
  "audio": {
    "silence_threshold": 1501
  },
  "wake_word": {
    "keyword": "margaret",
    "variants": ["margaret", "margret", "magret"]
  },
  "interrupt": {
    "stop_words": ["stop", "margaret stop", "quiet", "halt"]
  },
  "tts": {
    "voice": "nova"
  }
}
```

### How Configuration Loading Works

1. **Load defaults** from `config.defaults.json` (always present)
2. **Apply overrides** from `config.local.json` (optional)
3. **Deep merge** - only specified keys are overridden, others keep defaults

### Configuration Options

#### Audio Settings
- `silence_threshold`: RMS threshold for silence detection (tune with `tune_silence_threshold.py`)
- `chunk_size`: Audio buffer size (1024 recommended)
- `channels`: Audio channels (1 for mono)
- `rate`: Sample rate in Hz (16000 recommended)

#### Wake Word Settings
- `keyword`: Primary wake word (e.g., "computer", "margaret")
- `variants`: Alternative pronunciations/spellings for better detection
- `model`: Whisper model for wake word detection ("tiny" for speed)

#### Interrupt Settings
- `stop_words`: Phrases that stop TTS playback during responses

#### TTS Settings
- `voice`: OpenAI voice (alloy, echo, fable, onyx, nova, shimmer)
- `model`: TTS model ("tts-1" or "tts-1-hd")

## Usage

Say your wake word followed by a command:

### Inventory Management
- **"Computer, store hammer in toolbox drawer three"**
- **"Computer, where is the hammer?"**
- **"Computer, list all tools"**
- **"Computer, what's in the toolbox?"**

### Persistent Memory (NEW!)
Train the assistant to remember your preferences:
- **"Computer, remember that when I ask for counts, only give me the number"**
- **"Computer, remember I prefer brief responses"**
- **"Computer, remember to always mention safety when discussing power tools"**

The assistant stores these instructions in `MEMORY.md` and includes them in all future conversations, ensuring consistent behavior based on your preferences.

### Interrupting Responses
To interrupt a response, say any configured stop word:
- **"stop"** 
- **"quiet"**
- **"cancel"**

## Customization Examples

### Change Wake Word to "Margaret"
```json
{
  "wake_word": {
    "keyword": "margaret", 
    "variants": ["margaret", "margret", "magret"]
  },
  "interrupt": {
    "stop_words": ["stop", "margaret stop", "quiet"]
  }
}
```

### Adjust Audio Sensitivity
Run the tuning script first:
```bash
python tune_silence_threshold.py
```

Then update your config:
```json
{
  "audio": {
    "silence_threshold": 1200
  }
}
```

### Change Voice
```json
{
  "tts": {
    "voice": "nova"
  }
}
```

## Development

### Code Quality

This project uses standard Python linting and formatting tools:

- **Linting**: `make lint` - Run flake8 to check code style
- **Formatting**: `make format` - Run black to auto-format code  
- **Lint & Fix**: `make lint-fix` - Format code then run linter
- **Install dev deps**: `make dev-install` - Install with development dependencies

Configuration is stored in `pyproject.toml`:
- Line length: No restrictions (long lines allowed)
- Target Python: 3.8+
- Flake8 ignores: f-string placeholder warnings, line length limits

### Other Development Commands

- **Test configurations** without affecting defaults
- **Share setups** by sharing `config.local.json` files
- **Add new options** to `config.defaults.json` with sensible defaults
- **Run tests**: `make test` - Run pytest test suite
- **Clean cache**: `make clean` - Remove Python cache files
- **Help**: `make help` - Show all available commands