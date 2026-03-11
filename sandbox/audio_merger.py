import re
import os
import subprocess
from gtts import gTTS
from pathlib import Path


def extract_voiceover_lines(code: str) -> list:
    lines = []
    for line in code.split("\n"):
        match = re.search(r'#\s*VOICEOVER:\s*(.+)', line)
        if match:
            text = match.group(1).strip()
            # Skip template/format example lines
            if "<" in text:
                continue
            lines.append(text)
    return lines


def generate_audio(voiceover_lines: list, output_path: str) -> bool:
    """
    Combines all voiceover lines into one audio file using gTTS.
    """
    if not voiceover_lines:
        print("[Audio] No voiceover lines found in code")
        return False

    full_script = ". ".join(voiceover_lines)
    print(f"[Audio] Generating audio for: {full_script[:80]}...")

    try:
        tts = gTTS(text=full_script, lang='en', slow=False)
        tts.save(output_path)
        print(f"[Audio] ✅ Audio saved to: {output_path}")
        return True
    except Exception as e:
        print(f"[Audio] ❌ Failed to generate audio: {e}")
        return False


def merge_audio_video(video_path: str, audio_path: str, output_path: str) -> bool:
    """
    Uses FFmpeg to merge audio and video into final MP4.
    """
    print(f"[Merger] Merging audio and video...")

    try:
        result = subprocess.run([
            "ffmpeg",
            "-i", video_path,        # input video
            "-i", audio_path,        # input audio
            "-c:v", "copy",          # keep video as is
            "-c:a", "aac",           # encode audio
            "-shortest",             # end when shortest stream ends
            "-y",                    # overwrite output if exists
            output_path
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print(f"[Merger] ✅ Final video saved to: {output_path}")
            return True
        else:
            print(f"[Merger] ❌ FFmpeg failed: {result.stderr[:300]}")
            return False

    except FileNotFoundError:
        print("[Merger] ❌ FFmpeg not found. Installing via imageio...")
        # Fallback: use imageio-ffmpeg which comes with ffmpeg built in
        try:
            import imageio_ffmpeg
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            result = subprocess.run([
                ffmpeg_path,
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                "-y",
                output_path
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print(f"[Merger] ✅ Final video saved to: {output_path}")
                return True
        except Exception as e:
            print(f"[Merger] ❌ Fallback also failed: {e}")
            return False


def add_voice_to_video(code: str, video_path: str, output_path: str) -> dict:
    """
    Main function — takes code + silent video, returns video with voice.
    """
    # Step 1: Extract voiceover script from code comments
    voiceover_lines = extract_voiceover_lines(code)

    if not voiceover_lines:
        print("[Voice] No voiceover lines found — returning silent video")
        import shutil
        shutil.copy(video_path, output_path)
        return {"success": True, "video_path": output_path, "has_audio": False}

    print(f"[Voice] Found {len(voiceover_lines)} voiceover lines")

    # Step 2: Generate audio file
    audio_path = video_path.replace(".mp4", "_audio.mp3")
    audio_success = generate_audio(voiceover_lines, audio_path)

    if not audio_success:
        import shutil
        shutil.copy(video_path, output_path)
        return {"success": True, "video_path": output_path, "has_audio": False}

    # Step 3: Merge audio + video
    merge_success = merge_audio_video(video_path, audio_path, output_path)

    # Cleanup temp audio file
    if os.path.exists(audio_path):
        os.remove(audio_path)

    if merge_success:
        return {"success": True, "video_path": output_path, "has_audio": True}
    else:
        import shutil
        shutil.copy(video_path, output_path)
        return {"success": True, "video_path": output_path, "has_audio": False}