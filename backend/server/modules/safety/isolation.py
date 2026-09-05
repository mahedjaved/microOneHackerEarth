"""
Untrusted-content isolation.

Retrieved passages, document metadata, and user text are treated as untrusted data.
Instructions contained within them MUST NOT alter system behavior, tool permissions,
safety policy, or evaluation logic.
"""

import re
from typing import List


_INJECTION_PATTERNS = [
    r"ignore (previous|above|prior) instructions",
    r"disregard (previous|above|prior) instructions",
    r"forget (previous|above|prior) instructions",
    r"override (previous|above|prior) instructions",
    r"you are now",
    r"act as if",
    r"pretend to be",
    r"simulate being",
    r"new instructions:",
    r"system prompt:",
    r"\[system\]",
    r"\bsystem\b.*\boverride\b",
    r"\badmin\b.*\bcommand\b",
    r"\bexecute\b.*\bcode\b",
    r"\bprint\b.*\bconfig\b",
    r"\bprint\b.*\bsecrets?\b",
    r"\bprint\b.*\bapi.key\b",
    r"\bprint\b.*\bpassword\b",
    r"\bprint\b.*\btoken\b",
]


def detect_injection(text: str) -> List[str]:
    """Detect potential prompt-injection patterns in text."""
    detected = []
    lowered = text.lower()
    for pattern in _INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            detected.append(pattern)
    return detected


def is_safe(text: str) -> bool:
    """Return True if no injection patterns are detected."""
    return len(detect_injection(text)) == 0


def sanitize(text: str) -> str:
    """Remove detected injection patterns from text."""
    sanitized = text
    for pattern in _INJECTION_PATTERNS:
        sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)
    return sanitized
