"""
generate_agent_spec.py
Step 3 of the Clara pipeline.

Reads every v1_account_memo.json found under outputs/accounts/,
generates a Retell Agent Draft Spec, and saves it as v1_agent_spec.json
in the same account directory.

Agent spec fields:
  agent_name, voice_style, system_prompt, key_variables,
  call_transfer_protocol, fallback_protocol,
  office_hours_flow, after_hours_flow

Usage:
    py -3.10 scripts/generate_agent_spec.py
    python  scripts/generate_agent_spec.py
"""

import sys
import os
import glob

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.file_utils import load_json, save_json, ensure_directory
from scripts.generate_agent import generate_agent_spec


def _discover_memos(output_dir: str) -> list:
    """Return all v1_account_memo.json paths sorted by account dir."""
    return sorted(glob.glob(
        os.path.join(output_dir, "**", "v1_account_memo.json"),
        recursive=True
    ))


def run(account_ids: list = None):
    output_dir = os.path.join(PROJECT_ROOT, "outputs", "accounts")

    print("=" * 60)
    print("  STEP 3  |  Generate v1 Agent Spec")
    print("=" * 60)

    memo_paths = _discover_memos(output_dir)

    # Filter to specific account IDs if caller passes them
    if account_ids:
        memo_paths = [
            p for p in memo_paths
            if any(aid in p for aid in account_ids)
        ]

    if not memo_paths:
        print(f"\n  No v1_account_memo.json files found in {output_dir}")
        print("  Run extract_account_data.py first.")
        return

    print(f"\n  Found {len(memo_paths)} memo(s)\n")
    processed = 0
    errors = 0

    for memo_path in memo_paths:
        account_dir = os.path.dirname(memo_path)
        account_id  = os.path.basename(account_dir)
        spec_path   = os.path.join(account_dir, "v1_agent_spec.json")

        print(f"--- {account_id} ---")
        try:
            memo = load_json(memo_path)
            spec = generate_agent_spec(memo)
            save_json(spec, spec_path)
            print(f"  Agent : {spec['agent_name']}")
            print(f"  Saved : v1_agent_spec.json\n")
            processed += 1
        except Exception as exc:
            errors += 1
            print(f"  [ERROR] {account_id}: {exc}\n")
            import traceback
            traceback.print_exc()

    print("=" * 60)
    print(f"  Done — {processed} spec(s) saved, {errors} error(s)")
    print("=" * 60)


if __name__ == "__main__":
    run()
