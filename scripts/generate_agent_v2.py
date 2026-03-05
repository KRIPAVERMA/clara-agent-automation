"""
generate_agent_v2.py
Step 5 of the Clara pipeline.

Reads the latest vN_account_memo.json (N >= 2) for each account and
generates the corresponding vN_agent_spec.json using the same
generate_agent_spec function.

Usage:
    py -3.10 scripts/generate_agent_v2.py
    python  scripts/generate_agent_v2.py
"""

import sys
import os
import glob
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.file_utils import load_json, save_json
from utils.version_utils import get_latest_version, get_memo_path, get_spec_path
from scripts.generate_agent import generate_agent_spec


def _discover_accounts(output_dir: str) -> list:
    """Return list of account directory paths that have version >= 2 memos."""
    accounts = []
    if not os.path.isdir(output_dir):
        return accounts
    for entry in os.scandir(output_dir):
        if entry.is_dir() and get_latest_version(entry.path) >= 2:
            accounts.append(entry.path)
    return sorted(accounts)


def run():
    output_dir = os.path.join(PROJECT_ROOT, "outputs", "accounts")

    print("=" * 60)
    print("  STEP 5  |  Generate v2 Agent Spec")
    print("=" * 60)

    account_dirs = _discover_accounts(output_dir)

    if not account_dirs:
        print(f"\n  No accounts with v2+ memos found in {output_dir}")
        print("  Run apply_onboarding_update.py first.")
        return

    print(f"\n  Found {len(account_dirs)} account(s) with updated memos\n")
    processed = 0
    errors = 0

    for account_dir in account_dirs:
        account_id = os.path.basename(account_dir)
        version    = get_latest_version(account_dir)

        print(f"--- {account_id}  (v{version}) ---")
        try:
            memo      = load_json(get_memo_path(account_dir, version))
            spec      = generate_agent_spec(memo)
            spec_path = get_spec_path(account_dir, version)

            save_json(spec, spec_path)
            print(f"  Agent : {spec['agent_name']}")
            print(f"  Saved : v{version}_agent_spec.json\n")
            processed += 1

        except Exception as exc:
            errors += 1
            print(f"  [ERROR] {account_id}: {exc}\n")
            import traceback
            traceback.print_exc()

    print("=" * 60)
    print(f"  Done — {processed} v2 spec(s) saved, {errors} error(s)")
    print("=" * 60)


if __name__ == "__main__":
    run()
