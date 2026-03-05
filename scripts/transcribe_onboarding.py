"""
transcribe_onboarding.py
Transcribes all .mp4 and .m4a audio/video files found in
dataset/onboarding_calls/ using local OpenAI Whisper (no API key required).

Each file is saved as a .txt transcript in the same folder:
    audio1975518882.m4a  ->  audio1975518882.txt
    video1975518882.mp4  ->  video1975518882.txt

Usage:
    py -3.10 scripts/transcribe_onboarding.py
"""

import os
import sys
import glob
import time

# ---------------------------------------------------------------------------
# Dependency check
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
        print("        Run:  py -3.10 -m pip install", " ".join(missing))
        sys.exit(1)

    import shutil
    if not shutil.which("ffmpeg"):
        print("[error] ffmpeg not found on PATH.")
        print("        Install from https://ffmpeg.org or run: winget install ffmpeg")
        sys.exit(1)

_check_deps()

import whisper  # noqa: E402


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ONBOARDING_DIR = os.path.join(PROJECT_ROOT, "dataset", "onboarding_calls")
MODEL_SIZE = "base"
PREVIEW_LINES = 10


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def transcribe_file(model, file_path: str) -> str:
    """Transcribe one audio/video file with Whisper and return the text."""
    print(f"  Transcribing ... (this may take a while for long files)")
    t0 = time.time()
    result = model.transcribe(file_path, fp16=False, verbose=False)
    elapsed = time.time() - t0
    text = result["text"].strip()
    print(f"  Done in {elapsed:.1f}s  |  {len(text.split())} words  |  lang: {result.get('language', '?')}")
    return text


def save_transcript(text: str, txt_path: str) -> None:
    """Write transcript to .txt file (UTF-8)."""
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)
    size_kb = os.path.getsize(txt_path) / 1024
    print(f"  Saved: {txt_path}  ({size_kb:.1f} KB)")


def preview_transcript(txt_path: str, n: int = PREVIEW_LINES) -> None:
    """Print first N non-empty lines of saved transcript."""
    print(f"\n  --- Preview ({os.path.basename(txt_path)}) ---")
    with open(txt_path, "r", encoding="utf-8") as f:
        lines = [ln.rstrip() for ln in f if ln.strip()]
    for ln in lines[:n]:
        print(f"  {ln[:120]}")
    if len(lines) > n:
        print(f"  ... ({len(lines) - n} more lines)")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run():
    print("=" * 65)
    print("  CLARA AGENT AUTOMATION — Onboarding Transcription")
    print("=" * 65)
    print(f"  Model   : Whisper [{MODEL_SIZE}]")
    print(f"  Folder  : {ONBOARDING_DIR}")
    print()

    if not os.path.isdir(ONBOARDING_DIR):
        print(f"  [error] Directory not found: {ONBOARDING_DIR}")
        sys.exit(1)

    # Discover .mp4 and .m4a files
    media_files = sorted(
        glob.glob(os.path.join(ONBOARDING_DIR, "*.mp4")) +
        glob.glob(os.path.join(ONBOARDING_DIR, "*.m4a"))
    )

    if not media_files:
        print(f"  No .mp4 or .m4a files found in {ONBOARDING_DIR}")
        print("  Place audio/video files there and re-run.")
        return

    print(f"  Found {len(media_files)} file(s): {[os.path.basename(f) for f in media_files]}")
    print()

    # Load model once (cached after first download)
    print(f"  Loading Whisper [{MODEL_SIZE}] model ...")
    model = whisper.load_model(MODEL_SIZE)
    print("  Model loaded.\n")

    processed = 0
    skipped = 0
    errors = 0

    for media_path in media_files:
        filename = os.path.basename(media_path)
        stem = os.path.splitext(filename)[0]
        txt_path = os.path.join(ONBOARDING_DIR, f"{stem}.txt")

        print(f"--- [{processed + skipped + errors + 1}/{len(media_files)}] {filename} ---")
        print(f"  Input  : {media_path}")
        print(f"  Output : {txt_path}")

        # Skip if transcript already exists
        if os.path.isfile(txt_path):
            print(f"  [skip] Transcript already exists — delete it to retranscribe.\n")
            skipped += 1
            continue

        try:
            text = transcribe_file(model, media_path)
            save_transcript(text, txt_path)
            preview_transcript(txt_path)
            processed += 1
            print(f"  [OK] {filename} -> {os.path.basename(txt_path)}\n")
        except Exception as exc:
            errors += 1
            print(f"  [ERROR] {filename}: {exc}\n")
            import traceback
            traceback.print_exc()

    print("=" * 65)
    print("  Transcription Summary")
    print(f"  Processed : {processed}  |  Skipped: {skipped}  |  Errors: {errors}")
    print(f"  Output folder : {ONBOARDING_DIR}")
    print("=" * 65)


if __name__ == "__main__":
    run()
