#!/usr/bin/env python3

import pyaudio
import numpy as np


def tune_silence_threshold():
    """Help find the optimal silence threshold for your environment"""

    # Audio parameters
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    audio = pyaudio.PyAudio()

    try:
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )

        print("🔧 Workshop Silence Threshold Tuner")
        print("=" * 40)
        print("This will help you find the right silence threshold for your workshop.")
        print()
        print("1. First, be completely quiet for 10 seconds")
        print("2. Then speak normally for 10 seconds")
        print("3. We'll recommend a threshold based on your environment")
        print()
        input("Press Enter when ready to start...")

        # Measure ambient noise
        print("\n🔇 Measuring ambient noise... (be completely quiet for 10 seconds)")
        ambient_levels = []

        for i in range(100):  # 100 x 0.1s = 10 seconds
            data = stream.read(
                int(RATE * 0.1), exception_on_overflow=False
            )  # 0.1 second chunks
            audio_array = np.frombuffer(data, dtype=np.int16)
            rms = np.sqrt(np.mean(audio_array.astype(np.float64) ** 2))
            ambient_levels.append(rms)
            seconds_left = 10 - (i + 1) * 0.1
            print(f"🔇 Ambient noise: {rms:.0f} ({seconds_left:.1f}s left)", end="\r")

        avg_ambient = sum(ambient_levels) / len(ambient_levels)
        max_ambient = max(ambient_levels)

        print(f"\n✅ Ambient noise measured")
        print(f"   Average: {avg_ambient:.0f}")
        print(f"   Maximum: {max_ambient:.0f}")

        # Measure speech levels
        print(f"\n🗣️ Now speak normally for 10 seconds...")
        speech_levels = []

        for i in range(100):  # 100 x 0.1s = 10 seconds
            data = stream.read(int(RATE * 0.1), exception_on_overflow=False)
            audio_array = np.frombuffer(data, dtype=np.int16)
            rms = np.sqrt(np.mean(audio_array.astype(np.float64) ** 2))
            speech_levels.append(rms)
            seconds_left = 10 - (i + 1) * 0.1
            print(f"🗣️ Speech level: {rms:.0f} ({seconds_left:.1f}s left)", end="\r")

        avg_speech = sum(speech_levels) / len(speech_levels)
        max_speech = max(speech_levels)

        # Filter out pauses - levels significantly above ambient
        speech_only = [level for level in speech_levels if level > max_ambient * 1.2]
        min_speech = min(speech_only) if speech_only else avg_speech

        print(f"\n✅ Speech levels measured")
        print(f"   Average: {avg_speech:.0f}")
        print(f"   Maximum: {max_speech:.0f}")
        print(f"   Minimum (speaking): {min_speech:.0f}")

        # Calculate recommendations
        print(f"\n📊 Analysis:")
        print(f"   Ambient noise range: {avg_ambient:.0f} - {max_ambient:.0f}")
        print(f"   Speech range: {min_speech:.0f} - {max_speech:.0f}")

        # Recommend threshold somewhere between max ambient and min speech
        if min_speech > max_ambient:
            safety_margin = (min_speech - max_ambient) * 0.3
            recommended_threshold = max_ambient + safety_margin
        else:
            # Speech levels overlap with ambient - use higher threshold
            recommended_threshold = max_ambient * 1.5

        print(f"\n💡 Recommendations:")
        print(f"   Conservative (may miss quiet speech): {max_ambient * 1.5:.0f}")
        print(f"   Recommended: {recommended_threshold:.0f}")
        print(f"   Aggressive (may not detect silence): {min_speech * 0.8:.0f}")

        print(f"\n🔧 To use the recommended threshold:")
        print(f"   Edit continuous_detector.py")
        print(f"   Change: self.SILENCE_THRESHOLD = {recommended_threshold:.0f}")

        stream.close()

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        audio.terminate()


if __name__ == "__main__":
    tune_silence_threshold()
