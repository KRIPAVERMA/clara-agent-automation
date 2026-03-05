"""
generate_agent.py
Generates a Retell AI Agent Draft Spec JSON from an account memo.
Uses the agent prompt template to build a system prompt, and
assembles all required agent configuration fields.
"""

import os


def generate_agent_spec(account_memo: dict, template_path: str = None) -> dict:
    """
    Generate a Retell Agent Draft Spec from an account memo dictionary.

    Args:
        account_memo: Dictionary containing extracted account memo fields.
        template_path: Path to the agent prompt template file.
                       Defaults to templates/agent_prompt_template.txt.

    Returns:
        Dictionary representing the Retell Agent Draft Spec.
    """
    if template_path is None:
        # Resolve relative to project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(project_root, "templates", "agent_prompt_template.txt")

    system_prompt = _build_system_prompt(account_memo, template_path)

    agent_spec = {
        "agent_name": f"Clara - {account_memo.get('company_name', 'Unknown')}",
        "voice_style": "professional, friendly, empathetic",
        "system_prompt": system_prompt,
        "key_variables": _build_key_variables(account_memo),
        "call_transfer_protocol": _build_transfer_protocol(account_memo),
        "fallback_protocol": _build_fallback_protocol(account_memo),
        "version": account_memo.get("version", 1),
        "account_id": account_memo.get("account_id", "unknown"),
        "office_hours_flow": _build_office_hours_flow(account_memo),
        "after_hours_flow": _build_after_hours_flow(account_memo),
    }

    return agent_spec


def _build_system_prompt(memo: dict, template_path: str) -> str:
    """
    Load the prompt template and fill in placeholders with account memo data.
    """
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        print(f"  [warning] Template not found at {template_path}, using inline prompt.")
        template = _get_fallback_template()

    # Format list fields for display
    services = memo.get("services_supported", [])
    if isinstance(services, list):
        services_str = ", ".join(services)
    else:
        services_str = str(services)

    replacements = {
        "{company_name}": memo.get("company_name", "the company"),
        "{business_hours}": memo.get("business_hours", "Not specified"),
        "{office_address}": memo.get("office_address", "Not specified"),
        "{services_supported}": services_str,
        "{emergency_definition}": memo.get("emergency_definition", "Not specified"),
        "{emergency_routing_rules}": memo.get("emergency_routing_rules", "Transfer to on-call"),
        "{non_emergency_routing_rules}": memo.get("non_emergency_routing_rules", "Take message"),
        "{call_transfer_rules}": memo.get("call_transfer_rules", "Warm transfer"),
        "{integration_constraints}": memo.get("integration_constraints", "None"),
        "{notes}": memo.get("notes", "None"),
    }

    prompt = template
    for placeholder, value in replacements.items():
        prompt = prompt.replace(placeholder, value)

    return prompt


def _get_fallback_template() -> str:
    """Return a minimal inline template if the file is missing."""
    return (
        "You are Clara, a virtual receptionist for {company_name}.\n"
        "Business Hours: {business_hours}\n"
        "Services: {services_supported}\n"
        "Handle calls professionally. Transfer to appropriate parties.\n"
        "Emergency definition: {emergency_definition}\n"
        "Notes: {notes}"
    )


def _build_key_variables(memo: dict) -> dict:
    """
    Build the key_variables section of the agent spec.
    These are dynamic values the agent needs at runtime.
    """
    return {
        "company_name": memo.get("company_name", "Unknown"),
        "business_hours": memo.get("business_hours", "Not specified"),
        "office_address": memo.get("office_address", "Not specified"),
        "services_supported": memo.get("services_supported", []),
        "emergency_definition": memo.get("emergency_definition", "Not specified"),
    }


def _build_transfer_protocol(memo: dict) -> dict:
    """
    Build the call transfer protocol from the account memo.
    """
    return {
        "type": "warm_transfer",
        "rules": memo.get("call_transfer_rules", "Warm transfer to office line"),
        "emergency_routing": memo.get("emergency_routing_rules", "Transfer to on-call number"),
        "non_emergency_routing": memo.get("non_emergency_routing_rules", "Take message and callback"),
    }


def _build_fallback_protocol(memo: dict) -> dict:
    """
    Build the fallback protocol for when transfers fail.
    """
    return {
        "on_transfer_failure": "Apologize, confirm caller's information, and assure a callback.",
        "on_emergency_transfer_failure": "Log urgently, notify on-call team via backup channel, assure caller of immediate follow-up.",
        "on_system_error": "Apologize for technical difficulty, collect callback number, and end call gracefully.",
    }


def _build_office_hours_flow(memo: dict) -> list:
    """
    Build the structured office hours call flow.
    """
    company = memo.get("company_name", "the company")
    return [
        {
            "step": 1,
            "action": "greeting",
            "script": f"Thank you for calling {company}. My name is Clara, how can I help you today?"
        },
        {
            "step": 2,
            "action": "ask_purpose",
            "script": "Could you please tell me the reason for your call?"
        },
        {
            "step": 3,
            "action": "collect_info",
            "script": "May I have your full name and a phone number where we can reach you?",
            "fields": ["full_name", "phone_number"]
        },
        {
            "step": 4,
            "action": "transfer_call",
            "script": "Let me transfer you to the right person. One moment please.",
            "rules": memo.get("call_transfer_rules", "Warm transfer to office line")
        },
        {
            "step": 5,
            "action": "fallback_on_transfer_fail",
            "script": "I'm sorry, the line is currently busy. I've noted your information and someone will call you back shortly."
        },
        {
            "step": 6,
            "action": "ask_anything_else",
            "script": "Is there anything else I can help you with?"
        },
        {
            "step": 7,
            "action": "close_call",
            "script": f"Thank you for calling {company}. Have a great day!"
        }
    ]


def _build_after_hours_flow(memo: dict) -> dict:
    """
    Build the structured after-hours call flow with emergency and
    non-emergency branches.
    """
    company = memo.get("company_name", "the company")
    hours = memo.get("business_hours", "regular business hours")

    return {
        "greeting": {
            "step": 1,
            "action": "greeting",
            "script": f"Thank you for calling {company}. Our office is currently closed. Our business hours are {hours}."
        },
        "ask_purpose": {
            "step": 2,
            "action": "ask_purpose",
            "script": "Are you calling about an emergency or a general inquiry?"
        },
        "confirm_emergency": {
            "step": 3,
            "action": "confirm_emergency",
            "script": "Let me confirm — can you describe the nature of your issue so I can determine the best way to assist you?",
            "emergency_definition": memo.get("emergency_definition", "Not specified")
        },
        "emergency_flow": {
            "collect_info": {
                "step": 4,
                "action": "collect_emergency_info",
                "script": "I understand this is urgent. I need to collect some information from you.",
                "fields": ["full_name", "phone_number", "address"]
            },
            "attempt_transfer": {
                "step": 5,
                "action": "emergency_transfer",
                "script": "Let me connect you with our on-call team right away.",
                "routing": memo.get("emergency_routing_rules", "Transfer to on-call number")
            },
            "transfer_fail": {
                "step": 6,
                "action": "emergency_transfer_fallback",
                "script": "I understand this is urgent. I've logged your information and our on-call team will be notified immediately. Someone will contact you as soon as possible."
            }
        },
        "non_emergency_flow": {
            "collect_details": {
                "step": 4,
                "action": "collect_details",
                "script": "I'd be happy to help with that. Could you please provide me with the details of your inquiry?"
            },
            "confirm_callback": {
                "step": 5,
                "action": "confirm_callback",
                "script": "I've noted your information. Someone from our team will call you back on the next business day."
            },
            "close_call": {
                "step": 6,
                "action": "close_call",
                "script": f"Thank you for calling {company}. Have a good evening!"
            }
        }
    }
