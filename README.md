# Microphone Transcription App

Real-time speech-to-text transcription with both local and cloud options.

## Features

### Basic Transcription (`mic_transcriber.py`)
- Uses OpenAI's Whisper models locally
- Works completely offline
- Multiple model sizes available
- No API costs

### Enhanced Transcription (`enhanced_transcriber.py`)
- Choose between local or cloud transcription
- OpenAI Whisper API integration for faster cloud processing
- Optimized audio preprocessing
- Performance tracking
- Better accuracy options

### Real-time Transcription (`realtime_transcriber.py`) ⭐ **RECOMMENDED**
- **Solves the buffering lag problem**
- Adaptive chunk sizing based on processing speed
- Queue management with backpressure (drops old audio when overwhelmed)
- Real-time performance monitoring
- Automatic optimization for your hardware

## Performance Comparison

| Method | Speed | Accuracy | Cost | Internet Required |
|--------|-------|----------|------|-------------------|
| Local (tiny) | ~0.5s | Fair | Free | No |
| Local (base) | ~2-3s | Good | Free | No |
| Local (small) | ~4-5s | Better | Free | No |
| Local (medium) | ~8-10s | High | Free | No |
| Local (large) | ~15-20s | Best | Free | No |
| Cloud API | ~0.5-1s | Excellent | $0.006/min | Yes |

## Setup

1. Install dependencies:
```bash
brew install portaudio
pip3 install pyaudio openai-whisper numpy openai
```

2. For cloud transcription, set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Basic Version
```bash
python3 mic_transcriber.py
```

### Enhanced Version
```bash
python3 enhanced_transcriber.py
```

## How the Buffering Problem is Solved

The original issue: If transcription takes longer than audio chunk duration, the queue grows infinitely and lag increases.

**Solutions implemented in `realtime_transcriber.py`:**

1. **Adaptive Chunk Sizing**: Automatically adjusts chunk size based on processing speed
   - If processing is slow → increase chunk size (better efficiency)
   - If processing is fast → decrease chunk size (lower latency)

2. **Queue Management with Backpressure**: 
   - Limited queue size (max 3 chunks)
   - When queue is full, drops oldest audio to add new audio
   - Prevents infinite lag buildup

3. **Performance Monitoring**:
   - Tracks processing times and drop rates
   - Shows real-time status: `[time] (processing_time, queue_size) transcription`
   - Automatic optimization every 5 chunks

4. **Smart Audio Dropping**:
   - Only drops chunks when queue is full
   - Prioritizes recent audio over old audio
   - Reports dropped chunks so you know when processing is overwhelmed

## Recommendations

- **For real-time needs**: Use `realtime_transcriber.py` with cloud API or tiny model
- **For accuracy**: Use cloud API or local medium/large models  
- **For offline use**: Use local models with `realtime_transcriber.py`
- **For cost efficiency**: Use local tiny/base models
- **For best balance**: `realtime_transcriber.py` with cloud API (fast + accurate + no lag)