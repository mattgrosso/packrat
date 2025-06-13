#!/usr/bin/env python3

import os

# Configuration file for Workshop Assistant

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHISPER_MODEL = "whisper-1"
GPT_MODEL = "gpt-4"

# Wake Word Configuration
WAKE_WORD = "computer"  # Built-in Porcupine keyword
WAKE_WORD_SENSITIVITY = 0.5  # 0.0 to 1.0

# Audio Configuration
RECORD_DURATION = 4  # seconds after wake word
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1024

# Text-to-Speech Configuration
TTS_VOICE = "default"  # macOS system voice
TTS_RATE = 180  # words per minute

# Database Configuration
DATABASE_PATH = "workshop.db"

# Available Porcupine wake words (built-in)
AVAILABLE_WAKE_WORDS = [
    "alexa", "americano", "blueberry", "bumblebee", "computer",
    "grapefruit", "grasshopper", "hey google", "hey siri", "jarvis",
    "ok google", "picovoice", "porcupine", "terminator"
]

# Workshop categories for better organization
TOOL_CATEGORIES = [
    "hand_tool", "power_tool", "measuring", "cutting", "fastener",
    "hardware", "material", "safety", "electrical", "plumbing",
    "automotive", "woodworking", "metalworking", "general"
]

# Common workshop locations
COMMON_LOCATIONS = [
    "toolbox", "pegboard", "workbench", "shelf", "drawer",
    "cabinet", "bin", "rack", "hook", "table"
]