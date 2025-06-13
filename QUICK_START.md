# Quick Start Guide

## Workshop Voice Assistant - Ready to Use!

### 1. Set API Key
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

### 2. Run Assistant  
```bash
python3 workshop_assistant.py
```

### 3. Choose Manual Mode
When prompted, enter **1** for manual activation (recommended)

### 4. Use the Assistant
- **Press ENTER** → *beep* 
- **Say**: "Store hammer in toolbox drawer three"
- **Assistant responds**: "Got it, I've stored the hammer in toolbox drawer three"

- **Press ENTER** → *beep*
- **Say**: "Where is the hammer?"  
- **Assistant responds**: "The hammer is in toolbox drawer three"

### 5. Example Commands
- "Store [item] in [location]"
- "Where is [item]?"
- "List all tools"
- "What's in the toolbox?"

### Why Manual Mode?
- ✅ No false triggers from workshop noise
- ✅ Precise control over activation
- ✅ More reliable than voice activation
- ✅ Perfect for noisy workshop environments

### Troubleshooting
- If no API key: Set OPENAI_API_KEY environment variable
- If audio issues: Make sure microphone permissions are enabled
- If TTS doesn't work: Only works on macOS

**The system is complete and working!**