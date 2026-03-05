"""
extract_account_data.py
Step 2 of the Clara pipeline.

Reads all demo call transcripts from dataset/demo_calls/*.txt,
extracts structured account data, and saves a v1_account_memo.json
for each account under outputs/accounts/{account_id}/.

Extracted fields:
  account_id, company_name, business_hours, office_address,
  services_supported, emergency_definition, emergency_routing_rules,
  non_emergency_routing_rules, call_transfer_rules,
  integration_constraints, after_hours_flow_summary,
  office_hours_flow_summary, questions_or_unknowns, notes

Usage:
    py -3.10 scripts/extract_account_data.py
    python  scripts/extract_account_data.py
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.file_utils import load_transcript, save_json, list_files, ensure_directory
from scripts.extract_demo import extract_demo_data


def run():
    demo_dir   = os.path.join(PROJECT_ROOT, "dataset", "demo_calls")
    output_dir = os.path.join(PROJECT_ROOT, "outputs", "accounts")

    print("=" * 60)
    print("  STEP 2  |  Extract Account Data")
    print("=" * 60)

    ensure_directory(output_dir)
    transcript_files = list_files(demo_dir, ".txt")

    if not transcript_files:
        print(f"\n  No .txt transcripts found in {demo_dir}")
        return []

    print(f"\n  Found {len(transcript_files)} transcript(s)\n")
    account_ids = []
    errors = 0

    for filepath in transcript_files:
        filename = os.path.basename(filepath)
        print(f"--- {filename} ---")
        try:
            transcript  = load_transcript(filepath)
            memo        = extract_demo_data(transcript)
            account_id  = memo["account_id"]
            company     = memo["company_name"]

            account_dir = os.path.join(output_dir, account_id)
            ensure_directory(account_dir)

            memo_path = os.path.join(account_dir, "v1_account_memo.json")
            save_json(memo, memo_path)

            print(f"  Company    : {company}")
            print(f"  Account ID : {account_id}")
            print(f"  Saved      : v1_account_memo.json\n")
            account_ids.append(account_id)

        except Exception as exc:
            errors += 1
            print(f"  [ERROR] {filename}: {exc}\n")
            import traceback
            traceback.print_exc()

    print("=" * 60)
    print(f"  Done — {len(account_ids)} memo(s) saved, {errors} error(s)")
    print("=" * 60)
    return account_ids


if __name__ == "__main__":
    run()
