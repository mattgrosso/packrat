#!/usr/bin/env python3

import whisper

print("Testing Whisper model loading...")
try:
    model = whisper.load_model("base")
    print("Whisper model loaded successfully!")
    print("Model details:", type(model))
except Exception as e:
    print(f"Error loading model: {e}")