import os
os.environ["TTS_PROVIDER"] = "gtts"

with open("outputs/last_success_scene.py", "r", encoding="utf-8") as f:
    code = f.read()

from sandbox.sandbox import run_manim_sandbox
print("Running sandbox with gTTS (timeout=900)...")
res = run_manim_sandbox(code, timeout=900)
print(f"Success: {res.get('success')}")
if not res.get('success'):
    print(res.get('error'))
else:
    print("Video generated successfully!")
