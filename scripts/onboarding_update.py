"""
onboarding_update.py
Processes onboarding call transcripts to update an existing account memo
from v1 to v2 (or vN to vN+1). Merges new data from the onboarding
transcript with the existing memo and regenerates the agent spec.
"""

import re


def extract_onboarding_updates(transcript: str) -> dict:
    """
    Extract updated fields from an onboarding call transcript.
    Only returns fields that have identifiable new data.

    Args:
        transcript: Raw text of the onboarding call transcript.

    Returns:
        Dictionary containing updated fields (partial — only changed fields).
    """
    updates = {}

    # Try extracting each field; only include if a value is found
    field_patterns = {
        "company_name": r"(?:company|business|client)\s*(?:name)?[:\-–]\s*(.+)",
        "business_hours": r"(?:business\s*hours|office\s*hours|hours\s*of\s*operation|updated?\s*hours)[:\-–]\s*(.+)",
        "office_address": r"(?:office\s*address|new\s*address|address|location)[:\-–]\s*(.+)",
        "emergency_definition": r"(?:emergency\s*(?:definition|means|is\s*defined\s*as|should\s*be|now\s*includes?)?)[:\-–]\s*(.+)",
        "emergency_routing_rules": r"(?:emergency\s*routing(?:\s*rules?)?)[:\-–]\s*(.+)",
        "non_emergency_routing_rules": r"(?:non[_\-\s]?emergency\s*routing(?:\s*rules?)?)[:\-–]\s*(.+)",
        "call_transfer_rules": r"(?:call\s*transfer(?:\s*rules?)?|transfer\s*(?:protocol|rules?))[:\-–]\s*(.+)",
        "integration_constraints": r"(?:integration\s*(?:constraints?|limitations?|requirements?))[:\-–]\s*(.+)",
    }

    for field, pattern in field_patterns.items():
        match = re.search(pattern, transcript, re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1).strip().rstrip(".")
            if value:
                updates[field] = value

    # Services — may be a list
    services_match = re.search(
        r"(?:services?\s*(?:supported|offered|provided|include|updated?)?)[:\-–]\s*(.+)",
        transcript, re.IGNORECASE | re.MULTILINE
    )
    if services_match:
        raw = services_match.group(1).strip()
        items = re.split(r"[,;]|\band\b", raw)
        cleaned = []
        for item in items:
            item = item.strip().rstrip(".")
            # Remove trailing conversational fragments like "We added X as a new service"
            item = re.split(r"\. (?:We|They|Also|Note)", item)[0].strip()
            if item:
                cleaned.append(item)
        updates["services_supported"] = cleaned

    # After-hours flow
    after_match = re.search(
        r"(?:after\s*hours?\s*(?:flow|protocol|process|handling|update)?)[:\-–]\s*((?:.+\n?){1,10})",
        transcript, re.IGNORECASE | re.MULTILINE
    )
    if after_match:
        updates["after_hours_flow_summary"] = after_match.group(1).strip()

    # Office hours flow — require a flow/protocol/process keyword to avoid matching schedule
    office_match = re.search(
        r"(?:(?:office|business|during)\s*hours?\s*(?:flow|protocol|process|handling))[:\-–]\s*((?:.+\n?){1,10})",
        transcript, re.IGNORECASE | re.MULTILINE
    )
    if office_match:
        updates["office_hours_flow_summary"] = office_match.group(1).strip()

    # Notes
    notes_match = re.search(
        r"(?:notes?|additional\s*(?:info|information|notes?)|observations?)[:\-–]\s*((?:.+\n?){1,5})",
        transcript, re.IGNORECASE | re.MULTILINE
    )
    if notes_match:
        updates["notes"] = notes_match.group(1).strip()

    # Questions / unknowns
    questions = []
    q_matches = re.findall(r"([^.!?\n]*\?)", transcript)
    for q in q_matches:
        q = q.strip()
        if len(q) > 10:
            questions.append(q)
    if questions:
        updates["questions_or_unknowns"] = questions

    return updates


def merge_memo(existing_memo: dict, updates: dict) -> dict:
    """
    Merge updates from the onboarding transcript into the existing account memo.
    Creates a new version of the memo.

    - List fields are merged (union of old and new items).
    - Scalar fields are overwritten with the new value.
    - Version is incremented.

    Args:
        existing_memo: The current account memo dictionary.
        updates: Dictionary of fields to update.

    Returns:
        A new dictionary representing the updated memo.
    """
    merged = dict(existing_memo)

    for key, new_value in updates.items():
        if key == "version":
            continue

        old_value = merged.get(key)

        if isinstance(old_value, list) and isinstance(new_value, list):
            # Merge lists, preserving order and avoiding duplicates
            seen = set()
            combined = []
            for item in old_value + new_value:
                item_lower = item.lower().strip()
                if item_lower not in seen:
                    seen.add(item_lower)
                    combined.append(item)
            merged[key] = combined
        else:
            merged[key] = new_value

    # Increment version
    merged["version"] = existing_memo.get("version", 1) + 1

    return merged


def find_account_for_onboarding(transcript: str, existing_accounts: dict) -> str:
    """
    Determine which existing account an onboarding transcript belongs to.
    Matches by company name or account ID found in the transcript.

    Args:
        transcript: Raw onboarding transcript text.
        existing_accounts: Dictionary mapping account_id -> account_dir_path.

    Returns:
        Matching account_id, or None if no match found.
    """
    # Try explicit account ID
    id_match = re.search(r"(?:account\s*(?:id|number|#)?)[:\-–]\s*(\S+)", transcript, re.IGNORECASE)
    if id_match:
        aid = id_match.group(1).strip()
        if aid in existing_accounts:
            return aid

    # Collect candidate company names from the transcript
    candidate_names = []

    # Pattern 0: Branded call headers — "Clara kickoff call for Ben's Electric Solutions"
    branded_match = re.search(
        r"Clara\s+\w+\s+call\s+for\s+([A-Z][A-Za-z0-9\s&'.]+?)(?:\s+I\b|\s*\.|,|\s+we\b|\s+team\b|\s+I've)",
        transcript, re.IGNORECASE
    )
    if branded_match:
        candidate_names.append(branded_match.group(1).strip())

    # Pattern 0b: Generic kickoff/setup/onboarding call header
    kickoff_match = re.search(
        r"(?:kickoff|setup|onboarding)\s+call\s+for\s+([A-Z][A-Za-z0-9\s&'.]+?)(?:\s+I\b|\s*\.|,|\s+we\b|\s+team\b|\s+I've)",
        transcript, re.IGNORECASE
    )
    if kickoff_match:
        candidate_names.append(kickoff_match.group(1).strip())

    # Pattern 0c: Email domain reference — "Ben's electric solutions team.com"
    domain_match = re.search(
        r"([A-Z][A-Za-z0-9\s&'.]+?)\s+team\.com",
        transcript, re.IGNORECASE
    )
    if domain_match:
        candidate_names.append(domain_match.group(1).strip())

    # Pattern 1: Title line — "Transcript — Company Name"
    title_match = re.search(r"Transcript\s*(?:—|-)\s*(.+?)$", transcript, re.MULTILINE | re.IGNORECASE)
    if title_match:
        candidate_names.append(title_match.group(1).strip())

    # Pattern 2: "company name is [still] Company" (conversational)
    conv_match = re.search(
        r"(?:company|business|client)\s*name\s+(?:is\s+)?(?:still\s+)?([A-Z][A-Za-z\s&']+?)(?:\.|,|\s+that|\s+and|\s+we|\s+I)",
        transcript, re.IGNORECASE | re.MULTILINE
    )
    if conv_match:
        candidate_names.append(conv_match.group(1).strip())

    # Pattern 3: Standard "Company Name: Value"
    label_match = re.search(
        r"(?:company|business|client)\s*(?:name)?[:\-–]\s*(.+)",
        transcript, re.IGNORECASE | re.MULTILINE
    )
    if label_match:
        candidate_names.append(label_match.group(1).strip())

    # Pattern 4: Context patterns
    context_patterns = [
        r"(?:we\s+are|this\s+is\s+for|I'm\s+(?:with|from)|calling\s+(?:from|for)|representing)\s+([A-Z][A-Za-z\s&']+?)(?:\.|,|\s+and\s+|\s+we|\s+I)",
        r"(?:for\s+)([A-Z][A-Za-z\s&']+?)(?:\s+account|\s+onboarding)",
    ]
    for pattern in context_patterns:
        match = re.search(pattern, transcript, re.MULTILINE | re.IGNORECASE)
        if match:
            candidate_names.append(match.group(1).strip())

    # Try to match each candidate name against existing accounts
    for name in candidate_names:
        name_lower = name.lower()
        name_words = re.sub(r"[^a-z0-9\s]", "", name_lower).split()

        for account_id in existing_accounts:
            aid_lower = account_id.lower()
            # Match on first word of company name
            if name_words and name_words[0] in aid_lower:
                return account_id
            # Match on full name substring
            name_clean = re.sub(r"[^a-z0-9]", "", name_lower)
            if name_clean[:8] in aid_lower or aid_lower.split("_")[0] in name_clean:
                return account_id

    return None
