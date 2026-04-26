"""
Run the fixed showcase scene directly through the sandbox.
"""
import os, sys, shutil
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sandbox.sandbox import run_manim_sandbox

# Read the fixed scene code
with open("outputs/last_failed_scene.py", "r", encoding="utf-8") as f:
    code = f.read()

print("=" * 70)
print("AnimAi Studio — Running Fixed Showcase Video")
print("=" * 70)
print(f"Code length: {len(code)} chars, {len(code.splitlines())} lines")

result = run_manim_sandbox(code, timeout=300)

print("\n" + "=" * 70)
print(f"SUCCESS: {result.get('success')}")

if result.get("success"):
    video_path = result.get("video_path", "")
    print(f"VIDEO: {video_path}")
    
    # Copy to named output
    dest = os.path.join("outputs", "animai_showcase_video.mp4")
    if video_path and os.path.exists(video_path):
        shutil.copy(video_path, dest)
        print(f"SAVED AS: {dest}")
    print("\n🎬 Project showcase video generated successfully!")
else:
    print(f"ERROR: {(result.get('error', '') or '')[:3000]}")
