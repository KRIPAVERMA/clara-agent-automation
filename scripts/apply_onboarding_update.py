"""
apply_onboarding_update.py
Step 4 of the Clara pipeline.

Reads onboarding transcripts from dataset/onboarding_calls/*.txt,
matches each to an existing account (by name / context matching),
merges the updates into the latest account memo, and writes:

  outputs/accounts/{account_id}/v2_account_memo.json
  outputs/accounts/{account_id}/changes.md

Usage:
    py -3.10 scripts/apply_onboarding_update.py
    python  scripts/apply_onboarding_update.py
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.file_utils import (
    load_transcript, save_json, load_json,
    list_files, ensure_directory, save_text,
)
from utils.version_utils import (
    get_latest_version, get_memo_path, get_changes_path,
    generate_changelog,
)
from scripts.onboarding_update import (
    extract_onboarding_updates, merge_memo, find_account_for_onboarding,
)


def _discover_accounts(output_dir: str) -> dict:
    """Return {account_id: latest_memo_dict} for all accounts with memos."""
    accounts = {}
    if not os.path.isdir(output_dir):
        return accounts
    for entry in os.scandir(output_dir):
        if not entry.is_dir():
            continue
        version = get_latest_version(entry.path)
        if version > 0:
            memo_path = get_memo_path(entry.path, version)
            try:
                accounts[entry.name] = load_json(memo_path)
            except Exception:
                pass
    return accounts


def run():
    onboarding_dir = os.path.join(PROJECT_ROOT, "dataset", "onboarding_calls")
    output_dir     = os.path.join(PROJECT_ROOT, "outputs", "accounts")

    print("=" * 60)
    print("  STEP 4  |  Apply Onboarding Updates")
    print("=" * 60)

    ensure_directory(onboarding_dir)
    ensure_directory(output_dir)

    existing_accounts = _discover_accounts(output_dir)
    if not existing_accounts:
        print(f"\n  No existing accounts found. Run extract_account_data.py first.")
        return

    print(f"\n  Existing accounts : {list(existing_accounts.keys())}")

    txt_files = list_files(onboarding_dir, ".txt")
    if not txt_files:
        print(f"\n  No .txt files found in {onboarding_dir}")
        return

    print(f"  Onboarding files  : {len(txt_files)}\n")

    processed = 0
    errors = 0

    for filepath in txt_files:
        filename = os.path.basename(filepath)
        print(f"--- {filename} ---")
        try:
            transcript = load_transcript(filepath)
            print(f"  Loaded ({len(transcript)} chars)")

            account_id = find_account_for_onboarding(transcript, existing_accounts)
            if not account_id:
                print(f"  [skip] Could not match to any existing account.\n")
                continue

            print(f"  Matched account : {account_id}")

            account_dir  = os.path.join(output_dir, account_id)
            cur_version  = get_latest_version(account_dir)
            old_memo     = load_json(get_memo_path(account_dir, cur_version))

            updates      = extract_onboarding_updates(transcript)
            new_memo     = merge_memo(old_memo, updates)
            new_version  = new_memo["version"]

            # Save vN_account_memo.json
            new_memo_path = os.path.join(account_dir, f"v{new_version}_account_memo.json")
            save_json(new_memo, new_memo_path)
            print(f"  Saved v{new_version}_account_memo.json")

            # Save changelog
            changelog = generate_changelog(old_memo, new_memo)
            changes_path = get_changes_path(account_dir)
            save_text(changelog, changes_path)
            print(f"  Saved changes.md")

            processed += 1
            print(f"  [OK] {account_id}: v{cur_version} -> v{new_version}\n")

        except Exception as exc:
            errors += 1
            print(f"  [ERROR] {filename}: {exc}\n")
            import traceback
            traceback.print_exc()

    print("=" * 60)
    print(f"  Done — {processed} account(s) updated, {errors} error(s)")
    print("=" * 60)


if __name__ == "__main__":
    run()
