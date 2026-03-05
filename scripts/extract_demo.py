"""
extract_demo.py
Extracts structured information from demo call transcripts using
regex-based / rule-based extraction. No paid APIs are used.

Extracted fields:
- account_id, company_name, business_hours, office_address
- services_supported, emergency_definition, emergency_routing_rules
- non_emergency_routing_rules, call_transfer_rules
- integration_constraints, after_hours_flow_summary
- office_hours_flow_summary, questions_or_unknowns, notes
"""

import re
import hashlib


def extract_demo_data(transcript: str) -> dict:
    """
    Parse a demo call transcript and return a structured account memo dict.

    The extraction relies on regex patterns that look for labelled sections
    and keyword-based heuristics commonly found in demo call transcripts.

    Args:
        transcript: Raw text of the demo call transcript.

    Returns:
        Dictionary with all extracted account memo fields.
    """
    data = {
        "account_id": _extract_account_id(transcript),
        "company_name": _extract_field(transcript, r"(?:company|business|client)\s*(?:name)?[:\-–]\s*(.+)", "Unknown Company"),
        "business_hours": _extract_field(transcript, r"(?:business\s*hours|office\s*hours|hours\s*of\s*operation|operating\s*hours)[:\-–]\s*(.+)", "Not specified"),
        "office_address": _extract_field(transcript, r"(?:office\s*address|address|location)[:\-–]\s*(.+)", "Not specified"),
        "services_supported": _extract_list_field(transcript, r"(?:services?\s*(?:supported|offered|provided|include)?)[:\-–]\s*(.+)"),
        "emergency_definition": _extract_field(transcript, r"(?:emergency\s*(?:definition|means|is\s*defined\s*as|includes?)?)[:\-–]\s*(.+)", "Not specified"),
        "emergency_routing_rules": _extract_field(transcript, r"(?:emergency\s*routing(?:\s*rules?)?)[:\-–]\s*(.+)", "Transfer to on-call number"),
        "non_emergency_routing_rules": _extract_field(transcript, r"(?:non[_\-\s]?emergency\s*routing(?:\s*rules?)?)[:\-–]\s*(.+)", "Take message and callback next business day"),
        "call_transfer_rules": _extract_field(transcript, r"(?:call\s*transfer(?:\s*rules?)?|transfer\s*(?:protocol|rules?))[:\-–]\s*(.+)", "Warm transfer to office line"),
        "integration_constraints": _extract_field(transcript, r"(?:integration\s*(?:constraints?|limitations?|requirements?))[:\-–]\s*(.+)", "None specified"),
        "after_hours_flow_summary": _extract_after_hours_flow(transcript),
        "office_hours_flow_summary": _extract_office_hours_flow(transcript),
        "questions_or_unknowns": _extract_questions(transcript),
        "notes": _extract_notes(transcript),
        "version": 1,
    }

    # Fallback: try to extract company name from first few lines if not found
    if data["company_name"] == "Unknown Company":
        data["company_name"] = _extract_company_from_context(transcript)

    # Regenerate account_id from company name if needed
    if data["account_id"].startswith("acct_unknown"):
        data["account_id"] = _generate_account_id(data["company_name"])

    return data


def _extract_field(text: str, pattern: str, default: str = "") -> str:
    """
    Extract a single field value using a regex pattern.
    Returns the first captured group, stripped of whitespace.
    """
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    if match:
        return match.group(1).strip().rstrip(".")
    return default


def _extract_list_field(text: str, pattern: str) -> list:
    """
    Extract a field that may contain a comma-separated list, and return
    it as a Python list of trimmed strings.
    """
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    if match:
        raw = match.group(1).strip()
        # Split on commas or semicolons or " and "
        items = re.split(r"[,;]|\band\b", raw)
        return [item.strip().rstrip(".") for item in items if item.strip()]
    return ["General inquiries"]


def _extract_account_id(text: str) -> str:
    """
    Try to extract an explicit account ID from the transcript.
    Falls back to generating one from the company name.
    """
    match = re.search(r"(?:account\s*(?:id|number|#)?)[:\-–]\s*(\S+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "acct_unknown"


def _generate_account_id(company_name: str) -> str:
    """
    Generate a deterministic account ID from a company name using a hash.
    """
    clean = re.sub(r"[^a-zA-Z0-9]", "", company_name.lower())
    short_hash = hashlib.md5(clean.encode()).hexdigest()[:6]
    # Create a readable prefix from the company name
    prefix = re.sub(r"[^a-z0-9]", "", company_name.lower().split()[0]) if company_name.split() else "acct"
    return f"{prefix}_{short_hash}"


def _extract_company_from_context(text: str) -> str:
    """
    Attempt to extract the company name from conversational context.
    Looks for patterns like 'we are [Company]', 'calling from [Company]',
    'representing [Company]', 'this is for [Company]', etc.
    """
    patterns = [
        # Branded call headers: "Clara kickoff call for Ben's Electric Solutions"
        r"Clara\s+\w+\s+call\s+for\s+([A-Z][A-Za-z0-9\s&'.]+?)(?:\s+I['']|\s*\.|,|\s+we\b|\s+team\b)",
        # Generic kickoff/setup/onboarding call
        r"(?:kickoff|setup|onboarding)\s+call\s+for\s+([A-Z][A-Za-z0-9\s&'.]+?)(?:\s+I['']|\s*\.|,|\s+we\b|\s+team\b)",
        r"(?:we\s+are|this\s+is\s+for|I'm\s+(?:with|from)|calling\s+(?:from|for)|representing)\s+([A-Z][A-Za-z\s&']+?)(?:\.|,|\s+and\s+|\s+we|\s+I|\s+our|\s+the)",
        r"(?:this\s+is)\s+([A-Z][A-Za-z\s&']+?)(?:\.|,|\s+and\s+|\s+we|\s+I)",
        r"(?:for\s+)([A-Z][A-Za-z\s&']+?)(?:\s+account|\s+demo|\s+call)",
        r"(?:company|client|business)\s*(?:is|called)\s+([A-Z][A-Za-z\s&']+?)(?:\.|,|\s+and|\s+we)",
        r"Transcript\s*(?:—|-)\s*(.+?)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Filter out obviously wrong matches
            skip_words = {"sure", "yes", "no", "okay", "hi", "hello", "thanks", "the"}
            if name.lower().split()[0] in skip_words if name.split() else True:
                continue
            if len(name) > 2 and len(name) < 80:
                return name

    return "Unknown Company"


def _extract_after_hours_flow(text: str) -> str:
    """
    Extract or summarize the after-hours call flow from the transcript.
    """
    match = re.search(
        r"(?:after\s*hours?\s*(?:flow|protocol|process|handling)?)[:\-–]\s*((?:.+\n?){1,10})",
        text, re.IGNORECASE | re.MULTILINE
    )
    if match:
        return match.group(1).strip()

    # Check for keywords that indicate after-hours handling was discussed
    if re.search(r"after\s*hours?", text, re.IGNORECASE):
        return "After hours: Greet caller, determine urgency, collect info, route emergencies or take messages for callbacks."

    return "Standard after-hours protocol: greet, assess urgency, handle emergencies or take messages."


def _extract_office_hours_flow(text: str) -> str:
    """
    Extract or summarize the office / business hours call flow.
    Only matches when 'flow', 'protocol', 'process', or 'handling' is present
    to avoid capturing the business hours schedule.
    """
    match = re.search(
        r"(?:(?:office|business|during)\s*hours?\s*(?:flow|protocol|process|handling))[:\-–]\s*((?:.+\n?){1,10})",
        text, re.IGNORECASE | re.MULTILINE
    )
    if match:
        return match.group(1).strip()

    return "Standard office hours protocol: greet caller, identify purpose, collect name and phone, transfer to appropriate party, fallback if unavailable."


def _extract_questions(text: str) -> list:
    """
    Extract any unresolved questions or items marked as unknown/TBD.
    Filters out interviewer questions (questions from the Clara team).
    """
    questions = []

    # Find TBD / unknown markers (highest priority)
    tbd_matches = re.findall(r"(?:TBD|to\s*be\s*determined|unknown|not\s*sure|need\s*to\s*confirm)[:\-–]?\s*(.+)", text, re.IGNORECASE)
    for t in tbd_matches:
        questions.append(f"TBD: {t.strip()}")

    # Find explicit question marks but filter out interviewer questions
    q_matches = re.findall(r"([^.!?\n]*\?)", text)
    for q in q_matches:
        q = q.strip()
        if len(q) < 10:
            continue
        # Skip interviewer questions (lines starting with a known interviewer name)
        if re.match(r"^(?:Sarah|Alex|Clara|Agent|Rep)\s*:", q, re.IGNORECASE):
            continue
        # Skip common interview phrasing
        if re.search(r"(?:can you|tell us|what are|what is|how do|how should|any ).*\?", q, re.IGNORECASE):
            continue
        questions.append(q)

    return questions if questions else ["None identified"]


def _extract_notes(text: str) -> str:
    """
    Extract any additional notes or observations from the transcript.
    """
    match = re.search(
        r"(?:notes?|additional\s*(?:info|information|notes?)|observations?)[:\-–]\s*((?:.+\n?){1,5})",
        text, re.IGNORECASE | re.MULTILINE
    )
    if match:
        return match.group(1).strip()

    return "Extracted from demo call transcript via automated pipeline."
