import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sandbox.sandbox import run_manim_sandbox
from sandbox.audio_merger import add_voice_to_video

# Read the test scene
with open("test_scene.py", "r") as f:
    test_code = f.read()

print("=" * 50)
print("AnimAI Studio — Full Pipeline Test")
print("=" * 50)

# Step 1: Render silent video
print("\n[Step 1] Rendering animation in Docker...")
result = run_manim_sandbox(test_code)

if not result["success"]:
    print("❌ Sandbox failed:")
    print(result["error"][:500])
    exit()

print("✅ Silent video rendered!")

# Step 2: Add voice narration
print("\n[Step 2] Adding voice narration...")
final_result = add_voice_to_video(
    code=test_code,
    video_path=result["video_path"],
    output_path="outputs/final_with_voice.mp4"
)

print()
print("=" * 50)
if final_result["success"]:
    print("✅ PIPELINE COMPLETE!")
    print(f"Video: {final_result['video_path']}")
    if final_result["has_audio"]:
        print("🔊 Voice narration included!")
    else:
        print("🔇 Silent video (audio generation failed)")
    print()
    print("Open outputs/final_with_voice.mp4 to watch!")
else:
    print("❌ Pipeline failed")
print("=" * 50)