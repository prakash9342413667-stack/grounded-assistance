from dataclasses import dataclass
import re

@dataclass
class GuardrailDecision:
    allowed: bool
    message: str
    reason: str

# These checks apply to the user's instruction, not the email being inspected.
# The email itself is untrusted data and must never be followed as instructions.
UNSAFE_PATTERNS = [
    r"\bsteal\b.*\b(password|credential|login|account)\b",
    r"\b(phishing|credential|password)\b.*\b(kit|campaign|page|harvest|steal)\b",
    r"\b(bypass|evade)\b.*\b(security|antivirus|mfa|authentication)\b",
    r"\bkeylogger\b",
    r"\b(write|create|build|deploy)\b.*\bmalware\b",
        r"\bmalware\b.*\b(capture|steal|harvest|keylog)\b",
    r"\bspoof\b.*\b(bank|sender|email|domain)\b",
]

SCOPE_TERMS = {
    "email", "mail", "phishing", "security", "suspicious", "safe",
    "analyze", "analyse", "check", "classify", "inspect", "detect",
    "sender", "header", "link", "attachment", "spam", "fraud"
}

def check_request(request: str) -> GuardrailDecision:
    text = (request or "").strip().lower()

    if not text:
        return GuardrailDecision(False, "Please describe the email-security task.", "empty_request")

    for pattern in UNSAFE_PATTERNS:
        if re.search(pattern, text):
            return GuardrailDecision(
                False,
                "I can’t help create phishing messages, steal credentials, or bypass security. "
                "I can help analyze suspicious emails and explain how to defend against them.",
                "unsafe_request"
            )

    if not any(term in text for term in SCOPE_TERMS):
        return GuardrailDecision(
            False,
            "I’m a phishing email security assistant. I can help analyze emails, suspicious links, "
            "senders, attachments, and phishing indicators.",
            "off_topic"
        )

    return GuardrailDecision(True, "Request accepted.", "in_scope")
