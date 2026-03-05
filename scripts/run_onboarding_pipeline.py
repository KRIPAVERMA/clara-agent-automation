"""
run_onboarding_pipeline.py
Batch-processes onboarding call transcripts from dataset/onboarding_calls/,
matches them to existing accounts, merges updates into the account memo,
regenerates the agent spec, and produces a changelog.

Usage:
    python scripts/run_onboarding_pipeline.py
"""

import sys
import os

# Add project root to path so imports work when run from any directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from utils.file_utils import load_transcript, save_json, load_json, list_files, save_text, ensure_directory
from utils.version_utils import (
    get_latest_version,
    get_memo_path,
    get_spec_path,
    get_changes_path,
    generate_changelog,
)
from scripts.onboarding_update import extract_onboarding_updates, merge_memo, find_account_for_onboarding
from scripts.generate_agent import generate_agent_spec


def run_onboarding_pipeline():
    """
    Main entry point for the onboarding pipeline.
    Processes all .txt files in dataset/onboarding_calls/ and updates
    existing accounts with new data.
    """
    onboarding_dir = os.path.join(PROJECT_ROOT, "dataset", "onboarding_calls")
    output_base = os.path.join(PROJECT_ROOT, "outputs", "accounts")

    print("=" * 60)
    print("  CLARA AGENT AUTOMATION — Onboarding Pipeline")
    print("=" * 60)

    # Ensure directories exist
    ensure_directory(onboarding_dir)
    ensure_directory(output_base)

    # Discover existing accounts
    existing_accounts = _discover_accounts(output_base)
    if not existing_accounts:
        print(f"\n  No existing accounts found in {output_base}")
        print("  Run the demo pipeline first: python scripts/run_demo_pipeline.py")
        return

    print(f"\n  Found {len(existing_accounts)} existing account(s): {list(existing_accounts.keys())}")

    # Find onboarding transcripts
    transcript_files = list_files(onboarding_dir, ".txt")
    if not transcript_files:
        print(f"\n  No onboarding transcripts found in {onboarding_dir}")
        print("  Place .txt transcript files in dataset/onboarding_calls/ and re-run.")
        return

    print(f"  Found {len(transcript_files)} onboarding transcript(s)\n")

    processed = 0
    errors = 0

    for filepath in transcript_files:
        filename = os.path.basename(filepath)
        print(f"--- Processing: {filename} ---")

        try:
            # Step 1: Load transcript
            transcript = load_transcript(filepath)
            print(f"  Loaded transcript ({len(transcript)} chars)")

            # Step 2: Match to existing account
            account_id = find_account_for_onboarding(transcript, existing_accounts)
            if not account_id:
                print(f"  ⚠ Could not match to an existing account. Skipping.\n")
                errors += 1
                continue

            account_dir = existing_accounts[account_id]
            print(f"  Matched to account: {account_id}")

            # Step 3: Load existing memo
            latest_version = get_latest_version(account_dir)
            if latest_version == 0:
                print(f"  ⚠ No existing memo found for {account_id}. Skipping.\n")
                errors += 1
                continue

            old_memo_path = get_memo_path(account_dir, latest_version)
            old_memo = load_json(old_memo_path)
            print(f"  Loaded v{latest_version} memo")

            # Step 4: Extract updates from onboarding transcript
            updates = extract_onboarding_updates(transcript)
            print(f"  Extracted {len(updates)} updated field(s): {list(updates.keys())}")

            if not updates:
                print(f"  No updates found in transcript. Skipping.\n")
                continue

            # Step 5: Merge updates into new memo
            new_version = latest_version + 1
            new_memo = merge_memo(old_memo, updates)
            new_memo_path = get_memo_path(account_dir, new_version)
            save_json(new_memo, new_memo_path)

            # Step 6: Regenerate agent spec
            new_spec = generate_agent_spec(new_memo)
            new_spec_path = get_spec_path(account_dir, new_version)
            save_json(new_spec, new_spec_path)

            # Step 7: Generate changelog
            changelog = generate_changelog(old_memo, new_memo)
            changes_path = get_changes_path(account_dir)
            save_text(changelog, changes_path)

            processed += 1
            print(f"  ✓ Successfully updated to v{new_version}\n")

        except Exception as e:
            errors += 1
            print(f"  ✗ Error processing {filename}: {e}\n")

    # Summary
    print("=" * 60)
    print(f"  Pipeline Complete")
    print(f"  Updated: {processed}/{len(transcript_files)}")
    if errors:
        print(f"  Skipped/Errors: {errors}")
    print(f"  Output directory: {output_base}")
    print("=" * 60)


def _discover_accounts(output_base: str) -> dict:
    """
    Scan the outputs/accounts/ directory and return a mapping of
    account_id -> account_directory_path for all existing accounts.
    """
    accounts = {}
    if not os.path.isdir(output_base):
        return accounts

    for entry in os.listdir(output_base):
        entry_path = os.path.join(output_base, entry)
        if os.path.isdir(entry_path):
            accounts[entry] = entry_path

    return accounts


if __name__ == "__main__":
    run_onboarding_pipeline()
