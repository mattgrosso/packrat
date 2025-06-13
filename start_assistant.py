#!/usr/bin/env python3
"""
Quick start script for Workshop Voice Assistant

This is the simplest way to start your assistant. Just run:
    python3 start_assistant.py

Make sure OPENAI_API_KEY is set in your environment first.
"""

import os
import sys

def main():
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set your OpenAI API key first:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        print("   python3 start_assistant.py")
        sys.exit(1)
    
    # Import and start the assistant
    from workshop_assistant import main as workshop_main
    workshop_main()

if __name__ == "__main__":
    main()