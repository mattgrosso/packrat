# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Setup and installation
pip install -e .                    # Install in development mode
export OPENAI_API_KEY='your-key'    # Required for all functionality

# Running the application
python start_assistant.py           # Quick start (recommended)
python workshop_assistant.py        # Direct entry point

# Development tools
python tune_silence_threshold.py    # Tune audio detection for environment
python inspect_db.py               # View database contents

# Code quality (use these make commands)
make lint                          # Run flake8 linter
make format                        # Run black formatter
make lint-fix                      # Format then lint
make dev-install                   # Install with dev dependencies
make test                          # Run pytest tests
make clean                         # Clean Python cache files
make help                          # Show all commands
```

## Architecture Overview

### Core Design Pattern
This is a **unified detection system** that uses a single thread to handle both wake word detection and interrupt detection by switching modes. This eliminates microphone conflicts that plagued earlier architectures.

### Configuration System
Uses a **two-file configuration pattern**:
- `config.defaults.json` - committed defaults, never modify
- `config.local.json` - local overrides (gitignored), only specify what you want to change
- Config loading uses **deep merge** - load defaults, then apply local overrides

### Audio Pipeline Flow
1. **ContinuousDetector** runs unified detection loop in WAKE_WORD or INTERRUPT mode
2. **Wake word detected** → records full command with silence detection
3. **OpenAI Whisper API** transcribes complete utterance 
4. **GPT-4.1 with function calling** processes command with full database context
5. **OpenAI TTS** generates response, switches to INTERRUPT mode
6. **Mode switching** back to WAKE_WORD when TTS completes

### Key Architectural Decisions
- **Unified thread model**: Single detection thread prevents audio device conflicts
- **Mode-based detection**: Same thread handles wake words vs stop commands
- **Full transcript to LLM**: Skip wake word parsing, let GPT-4.1 ignore it
- **Non-blocking TTS with monitoring**: Start audio in background, monitor process completion
- **Cross-platform audio**: Auto-detect available players (paplay/mpg123/afplay)

### Component Relationships
- `WorkshopAssistant` orchestrates the pipeline and manages mode transitions
- `ContinuousDetector` handles all audio detection with mode switching
- `SmartCommandParser` processes commands with complete database context
- `OpenAITTS` manages speech synthesis with interrupt support
- `WorkshopDatabase` provides tool inventory storage

### Critical Implementation Details
- Configuration changes require updating BOTH the default config structure AND the deep merge logic
- Wake word variants and stop words are fully configurable via config files
- All OpenAI API calls include timing instrumentation for performance monitoring
- TTS interrupt detection requires careful process monitoring and cleanup
- The system expects `config.defaults.json` to always exist (committed to repo)

### Testing and Debugging
- Live transcription shows real-time audio recognition during wake word detection
- Interrupt detection also shows live transcription during TTS playback
- All API calls (Whisper, GPT, TTS) include detailed timing information
- Use `tune_silence_threshold.py` to calibrate audio detection for specific environments

## Code Quality Standards

### Linting and Formatting
This project uses standard Python tooling configured in `pyproject.toml`:
- **Black** for code formatting (no line length restrictions)
- **Flake8** for linting (ignores f-string placeholder warnings and line length)
- **Make commands** for easy execution (`make lint`, `make format`, `make lint-fix`)

### Before Committing Code
Always run `make lint-fix` to ensure code quality:
1. Formats code with black
2. Checks for linting issues with flake8
3. All code should pass both checks

### Configuration
- Line length: No restrictions (long lines are allowed)
- Target Python: 3.8+ for broad compatibility
- Flake8 ignores: F541 (f-string missing placeholders), E501 (line too long)

## Working Practices
- Read PROJECT_STATUS.md at the beginning of sessions and update it from time to time
- Run `make lint-fix` before making commits
- Use `make dev-install` for development setup with linting tools