"""
run_all.py
Master pipeline for the Clara Agent Automation project.

Executes all steps in sequence:
  1. Transcribe onboarding audio/video  (dataset/onboarding_calls -> .txt)
  2. Extract account data               (demo .txt  ->  v1_account_memo.json)
  3. Generate v1 agent spec             (v1_account_memo -> v1_agent_spec.json)
  4. Apply onboarding updates           (onboarding .txt -> v2_account_memo.json + changes.md)
  5. Generate v2 agent spec             (v2_account_memo -> v2_agent_spec.json)

Usage:
    python scripts/run_all.py
    py     scripts/run_all.py
"""

import sys
import os
import traceback

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.transcribe_onboarding import run as transcribe_onboarding
from scripts.extract_account_data   import run as extract_account_data
from scripts.generate_agent_spec    import run as generate_agent_spec
from scripts.apply_onboarding_update import run as apply_onboarding_update
from scripts.generate_agent_v2      import run as generate_agent_v2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _step(number: int, name: str):
    print(f"\n{'#' * 65}")
    print(f"  STEP {number} — {name}")
    print(f"{'#' * 65}\n")


def _show_outputs(output_dir: str):
    print("\n" + "=" * 65)
    print("  PIPELINE COMPLETE — Generated Outputs")
    print("=" * 65)
    if not os.path.isdir(output_dir):
        print("  (no outputs found)")
        return
    for root, dirs, files in sorted(os.walk(output_dir)):
        dirs.sort()
        files.sort()
        rel = os.path.relpath(root, output_dir)
        prefix = "  " if rel == "." else f"  {rel}/"
        for f in files:
            size = os.path.getsize(os.path.join(root, f))
            print(f"{prefix}{f}  ({size / 1024:.1f} KB)")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    outputs_base = os.path.join(PROJECT_ROOT, "outputs", "accounts")

    steps = [
        (1, "Transcribe Onboarding Audio/Video",  transcribe_onboarding),
        (2, "Extract Account Data from Demo Calls", extract_account_data),
        (3, "Generate v1 Agent Specs",             generate_agent_spec),
        (4, "Apply Onboarding Updates",            apply_onboarding_update),
        (5, "Generate v2 Agent Specs",             generate_agent_v2),
    ]

    failed = []
    for number, name, fn in steps:
        _step(number, name)
        try:
            fn()
        except Exception:
            failed.append(name)
            print(f"\n  [PIPELINE ERROR] Step {number} — {name} failed:")
            traceback.print_exc()
            print("  Continuing with next step...\n")

    _show_outputs(outputs_base)

    if failed:
        print(f"  Steps with errors: {failed}")
    else:
        print("  All steps completed successfully.")


if __name__ == "__main__":
    main()

