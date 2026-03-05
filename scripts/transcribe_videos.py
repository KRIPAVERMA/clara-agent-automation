"""
transcribe_videos.py
Automatically transcribes all .mp4 video files inside dataset/demo_calls/
using the local open-source OpenAI Whisper model (no API key required).

Output:
  dataset/demo_calls/demo_call_1.mp4  →  dataset/demo_calls/demo_call_1.txt

Usage:
  py scripts/transcribe_videos.py
"""

import os
import sys
import glob
import time

# ---------------------------------------------------------------------------
# Dependency check with helpful messages
# ---------------------------------------------------------------------------

def _check_deps():
    missing = []
    try:
        import whisper  # noqa: F401
    except ImportError:
        missing.append("openai-whisper")
    try:
        import torch  # noqa: F401
    except ImportError:
        missing.append("torch")

    if missing:
        print("[error] Missing Python packages:", ", ".join(missing))
        print("        Run:  py -m pip install", " ".join(missing))
        sys.exit(1)

    # Check ffmpeg is on PATH
    import shutil
    if not shutil.which("ffmpeg"):
        print("[error] ffmpeg is not found on PATH.")
        print("        Download from https://ffmpeg.org/download.html or run:")
        print("        winget install ffmpeg")
        sys.exit(1)

_check_deps()

import whisper  # noqa: E402 (imported after dep check)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_CALLS_DIR = os.path.join(PROJECT_ROOT, "dataset", "demo_calls")

# Whisper model size: "tiny" is fastest; swap for "base", "small", "medium", "large" for accuracy
MODEL_SIZE = "base"

PREVIEW_LINES = 10   # How many lines to print as preview after transcription


# ---------------------------------------------------------------------------
# Core transcription logic
# ---------------------------------------------------------------------------

def transcribe_file(model, video_path: str) -> str:
    """
    Run Whisper transcription on a single video file.
    Returns the full transcript text.
    """
    print(f"  Transcribing ... (this may take a moment)")
    t0 = time.time()
    result = model.transcribe(video_path, fp16=False, verbose=False)
    elapsed = time.time() - t0
    text = result["text"].strip()
    print(f"  Done in {elapsed:.1f}s  |  {len(text)} chars  |  {len(text.split())} words")
    return text


def save_transcript(text: str, txt_path: str) -> None:
    """Write transcript text to a .txt file at the same location as the video."""
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"  Saved: {txt_path}")


def preview_transcript(txt_path: str, n: int = PREVIEW_LINES) -> None:
    """Print the first N non-empty lines of the saved transcript."""
    print(f"\n  --- Preview (first {n} lines of {os.path.basename(txt_path)}) ---")
    with open(txt_path, "r", encoding="utf-8") as f:
        lines = [l.rstrip() for l in f if l.strip()]
    for line in lines[:n]:
        print(f"  {line}")
    if len(lines) > n:
        print(f"  ... ({len(lines) - n} more lines)")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run():
    print("=" * 65)
    print("  CLARA AGENT AUTOMATION — Video Transcription Pipeline")
    print("=" * 65)
    print(f"  Model        : Whisper [{MODEL_SIZE}]")
    print(f"  Input folder : {DEMO_CALLS_DIR}")
    print()

    # Discover .mp4 files
    mp4_files = sorted(glob.glob(os.path.join(DEMO_CALLS_DIR, "*.mp4")))
    if not mp4_files:
        print(f"  No .mp4 files found in {DEMO_CALLS_DIR}")
        print("  Place video files there and re-run.")
        return

    print(f"  Found {len(mp4_files)} video(s): {[os.path.basename(f) for f in mp4_files]}")
    print()

    # Load Whisper model once (cached locally after first download)
    print(f"  Loading Whisper [{MODEL_SIZE}] model ...")
    model = whisper.load_model(MODEL_SIZE)
    print(f"  Model loaded.\n")

    processed = 0
    errors = 0

    for video_path in mp4_files:
        filename = os.path.basename(video_path)
        stem = os.path.splitext(filename)[0]
        txt_path = os.path.join(DEMO_CALLS_DIR, f"{stem}.txt")

        print(f"--- [{processed + 1}/{len(mp4_files)}] {filename} ---")
        print(f"  Video  : {video_path}")
        print(f"  Output : {txt_path}")

        try:
            text = transcribe_file(model, video_path)
            save_transcript(text, txt_path)

            # Confirm file exists
            if os.path.isfile(txt_path):
                size_kb = os.path.getsize(txt_path) / 1024
                print(f"  Confirmed: file exists ({size_kb:.1f} KB)")
            else:
                print(f"  [warning] File not found after save?")

            preview_transcript(txt_path)
            processed += 1
            print(f"  [OK] {filename}  ->  {os.path.basename(txt_path)}\n")

        except Exception as e:
            errors += 1
            print(f"  [ERROR] processing {filename}: {e}\n")
            import traceback
            traceback.print_exc()

    # Summary
    print("=" * 65)
    print(f"  Transcription Complete")
    print(f"  Processed : {processed}/{len(mp4_files)}")
    if errors:
        print(f"  Errors    : {errors}")
    print(f"  Transcripts saved in: {DEMO_CALLS_DIR}")
    print("=" * 65)


if __name__ == "__main__":
    run()
