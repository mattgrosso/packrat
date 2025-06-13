# Debugging Workshop Assistant Wake Word Detection

## Issue: Wake word "computer" not being detected

### Quick Debugging Steps:

## 1. Test Your API Key & Basic Transcription
```bash
python3 quick_test.py
```
**What to expect**: Should transcribe whatever you say
**If it fails**: Check your OPENAI_API_KEY

## 2. Test Microphone Levels
```bash
python3 test_microphone.py
```
**What to expect**: Should show audio level bars when you speak
**If no bars**: Check microphone permissions

## 3. Test Improved Keyword Detection
```bash
python3 improved_keyword_detector.py
```
**What to expect**: Should detect "computer" with better accuracy
**Tips**: 
- Speak loudly and clearly
- Try "COMPUTER" in a firm voice
- Get closer to microphone

## 4. Debug the Original Detector
```bash
python3 debug_keyword_detector.py
```
**What to expect**: Verbose logging of everything happening
**Use this**: To see exactly what's being transcribed

## Common Issues & Solutions:

### Issue: "Audio too quiet"
**Solution**: 
- Speak louder
- Get closer to microphone  
- Check System Preferences → Sound → Input levels

### Issue: Wrong transcription
**Example**: Says "compute" instead of "computer"
**Solution**: The improved detector handles partial matches

### Issue: No transcription at all
**Solutions**:
- Check microphone permissions (System Preferences → Security & Privacy)
- Try a different microphone
- Restart the terminal

### Issue: API errors
**Solutions**:
- Check `echo $OPENAI_API_KEY`
- Verify API key is valid
- Check internet connection

## Recommended Settings for Workshop:

1. **Use the improved detector** (handles partial matches)
2. **Speak clearly and loudly** 
3. **Wait 3 seconds between attempts** (cooldown period)
4. **Try alternative keywords**: "compute", "comput" also work

## If Still Not Working:

Try these alternative wake words that might work better:
- "Assistant" 
- "Workshop"
- "Helper"

Edit the wake word in workshop_assistant.py:
```python
wake_word = "assistant"  # Change from "computer"
```

The transcription system works - we just need to find the right audio levels and speaking style for your setup!