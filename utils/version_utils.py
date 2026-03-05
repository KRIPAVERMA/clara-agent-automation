"""
version_utils.py
Utility functions for version management:
- Determining the latest version of an account's files
- Generating next-version file paths
- Comparing memo versions to produce changelogs
"""

import os
import re
from utils.file_utils import load_json


def get_latest_version(account_dir: str) -> int:
    """
    Scan an account directory and return the highest version number found.

    Looks for files named v{N}_account_memo.json.

    Args:
        account_dir: Path to the account's output directory.

    Returns:
        The highest version number (int), or 0 if no versions exist.
    """
    if not os.path.isdir(account_dir):
        return 0

    versions = []
    for fname in os.listdir(account_dir):
        match = re.match(r"v(\d+)_account_memo\.json", fname)
        if match:
            versions.append(int(match.group(1)))

    return max(versions) if versions else 0


def get_memo_path(account_dir: str, version: int) -> str:
    """Return the file path for a given version's account memo."""
    return os.path.join(account_dir, f"v{version}_account_memo.json")


def get_spec_path(account_dir: str, version: int) -> str:
    """Return the file path for a given version's agent spec."""
    return os.path.join(account_dir, f"v{version}_agent_spec.json")


def get_changes_path(account_dir: str) -> str:
    """Return the file path for the changelog."""
    return os.path.join(account_dir, "changes.md")


def generate_changelog(old_memo: dict, new_memo: dict) -> str:
    """
    Compare two account memo dictionaries and produce a Markdown changelog
    describing what was added, removed, or modified.

    Args:
        old_memo: The previous version memo dict.
        new_memo: The updated version memo dict.

    Returns:
        A Markdown-formatted changelog string.
    """
    lines = [
        f"# Changelog: v{old_memo.get('version', 1)} → v{new_memo.get('version', 2)}",
        "",
        f"**Account:** {new_memo.get('company_name', 'Unknown')}",
        f"**Account ID:** {new_memo.get('account_id', 'Unknown')}",
        "",
        "---",
        "",
    ]

    all_keys = sorted(set(list(old_memo.keys()) + list(new_memo.keys())))

    changes_found = False
    for key in all_keys:
        if key == "version":
            continue

        old_val = old_memo.get(key)
        new_val = new_memo.get(key)

        if old_val != new_val:
            changes_found = True
            lines.append(f"## `{key}`")
            lines.append("")

            if old_val is None:
                lines.append(f"**Added:**")
                lines.append(f"```")
                lines.append(f"{_format_value(new_val)}")
                lines.append(f"```")
            elif new_val is None:
                lines.append(f"**Removed:**")
                lines.append(f"```")
                lines.append(f"{_format_value(old_val)}")
                lines.append(f"```")
            else:
                lines.append(f"**Before:**")
                lines.append(f"```")
                lines.append(f"{_format_value(old_val)}")
                lines.append(f"```")
                lines.append(f"**After:**")
                lines.append(f"```")
                lines.append(f"{_format_value(new_val)}")
                lines.append(f"```")
            lines.append("")

    if not changes_found:
        lines.append("No changes detected.")

    return "\n".join(lines)


def _format_value(value) -> str:
    """Format a value for display in the changelog."""
    if isinstance(value, list):
        return "\n".join(f"- {item}" for item in value)
    elif isinstance(value, dict):
        import json
        return json.dumps(value, indent=2)
    else:
        return str(value)
