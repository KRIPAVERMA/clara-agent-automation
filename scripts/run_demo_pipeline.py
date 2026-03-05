"""
run_demo_pipeline.py
Batch-processes all demo call transcripts from dataset/demo_calls/,
extracts structured data, generates account memos and agent specs,
and saves them as v1 outputs.

Usage:
    python scripts/run_demo_pipeline.py
"""

import sys
import os

# Add project root to path so imports work when run from any directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from utils.file_utils import load_transcript, save_json, list_files, ensure_directory
from scripts.extract_demo import extract_demo_data
from scripts.generate_agent import generate_agent_spec


def run_demo_pipeline():
    """
    Main entry point for the demo pipeline.
    Processes all .txt files in dataset/demo_calls/ and outputs
    v1 account memos and agent specs.
    """
    demo_dir = os.path.join(PROJECT_ROOT, "dataset", "demo_calls")
    output_base = os.path.join(PROJECT_ROOT, "outputs", "accounts")

    print("=" * 60)
    print("  CLARA AGENT AUTOMATION — Demo Pipeline")
    print("=" * 60)

    # Ensure input directory exists
    ensure_directory(demo_dir)

    # Find all transcript files
    transcript_files = list_files(demo_dir, ".txt")

    if not transcript_files:
        print(f"\n  No transcript files found in {demo_dir}")
        print("  Place .txt transcript files in dataset/demo_calls/ and re-run.")
        return

    print(f"\n  Found {len(transcript_files)} demo transcript(s)\n")

    processed = 0
    errors = 0

    for filepath in transcript_files:
        filename = os.path.basename(filepath)
        print(f"--- Processing: {filename} ---")

        try:
            # Step 1: Load transcript
            transcript = load_transcript(filepath)
            print(f"  Loaded transcript ({len(transcript)} chars)")

            # Step 2: Extract structured data
            account_memo = extract_demo_data(transcript)
            account_id = account_memo["account_id"]
            print(f"  Extracted account: {account_memo['company_name']} ({account_id})")

            # Step 3: Create output directory
            account_dir = os.path.join(output_base, account_id)
            ensure_directory(account_dir)

            # Step 4: Save v1 account memo
            memo_path = os.path.join(account_dir, "v1_account_memo.json")
            save_json(account_memo, memo_path)

            # Step 5: Generate and save v1 agent spec
            agent_spec = generate_agent_spec(account_memo)
            spec_path = os.path.join(account_dir, "v1_agent_spec.json")
            save_json(agent_spec, spec_path)

            processed += 1
            print(f"  ✓ Successfully processed {filename}\n")

        except Exception as e:
            errors += 1
            print(f"  ✗ Error processing {filename}: {e}\n")

    # Summary
    print("=" * 60)
    print(f"  Pipeline Complete")
    print(f"  Processed: {processed}/{len(transcript_files)}")
    if errors:
        print(f"  Errors: {errors}")
    print(f"  Output directory: {output_base}")
    print("=" * 60)


if __name__ == "__main__":
    run_demo_pipeline()
