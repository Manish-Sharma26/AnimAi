# test_audio.py
from gtts import gTTS
import subprocess

# Generate audio
tts = gTTS("Hello! AnimAI Studio is working correctly. Your Manim sandbox is ready to use.", lang='en')
tts.save("outputs/test_audio.mp3")
print("✅ Audio generated!")

# Merge with existing silent video
result = subprocess.run([
    "ffmpeg",
    "-i", "outputs/animation.mp4",
    "-i", "outputs/test_audio.mp3",
    "-c:v", "copy",
    "-c:a", "aac",
    "-shortest",
    "-y",
    "outputs/final_with_voice.mp4"
], capture_output=True, text=True)

if result.returncode == 0:
    print("✅ Done! Open outputs/final_with_voice.mp4")
else:
    print("❌ FFmpeg error:")
    print(result.stderr[-500:])