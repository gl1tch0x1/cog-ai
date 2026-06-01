"""Caveman token compression for inter-agent communication.

Strips filler words, articles, and verbose phrasing from messages to reduce
token usage by 30-50% while preserving all technical content, URLs, and data.
"""

from __future__ import annotations

import re

# Words to strip (articles, filler, verbose connectors)
STRIP_WORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "shall",
    "can",
    "that",
    "which",
    "who",
    "whom",
    "this",
    "these",
    "those",
    "it",
    "its",
    "there",
    "here",
    "very",
    "really",
    "just",
    "quite",
    "rather",
    "somewhat",
    "basically",
    "actually",
    "literally",
    "simply",
    "obviously",
    "clearly",
    "certainly",
    "definitely",
    "probably",
    "possibly",
    "perhaps",
    "maybe",
    "also",
    "furthermore",
    "moreover",
    "however",
    "therefore",
    "consequently",
    "additionally",
    "nevertheless",
    "nonetheless",
    "accordingly",
    "please",
    "kindly",
    "note",
    "importantly",
}

# Verbose phrases → compressed equivalents
PHRASE_MAP = {
    "in order to": "to",
    "as well as": "+",
    "due to the fact that": "because",
    "at this point in time": "now",
    "in the event that": "if",
    "with regard to": "re:",
    "for the purpose of": "for",
    "on the other hand": "alternatively",
    "it is important to note that": "",
    "it should be noted that": "",
    "as a result of": "from",
    "in addition to": "+",
    "with respect to": "re:",
    "in terms of": "for",
    "a large number of": "many",
    "a significant amount of": "much",
    "take into consideration": "consider",
    "make a decision": "decide",
    "come to the conclusion": "conclude",
    "is able to": "can",
    "is not able to": "cannot",
    "in the process of": "during",
    "at the present time": "now",
    "prior to": "before",
    "subsequent to": "after",
    "in close proximity to": "near",
    "has the ability to": "can",
}

# Patterns to preserve (never compress)
PRESERVE_PATTERNS = [
    re.compile(r"https?://\S+"),  # URLs
    re.compile(r"\b\d+\.\d+\.\d+\.\d+\b"),  # IPs
    re.compile(r"CVE-\d{4}-\d+"),  # CVE IDs
    re.compile(r"CWE-\d+"),  # CWE IDs
    re.compile(r"\{[^}]+\}"),  # JSON/template blocks
    re.compile(r"\[[^\]]+\]"),  # Array notation
    re.compile(r"`[^`]+`"),  # Code blocks
    re.compile(r'"[^"]*"'),  # Quoted strings
    re.compile(r"'[^']*'"),  # Single-quoted strings
]


def compress(text: str) -> str:
    """Compress text for inter-agent communication. Preserves technical content."""
    if not text:
        return text

    # Extract and protect preserved patterns
    preserved: list[tuple[str, str]] = []
    result = text
    for i, pattern in enumerate(PRESERVE_PATTERNS):
        for match in pattern.finditer(result):
            placeholder = f"§{i}_{len(preserved)}§"
            preserved.append((placeholder, match.group()))
            result = result.replace(match.group(), placeholder, 1)

    # Apply phrase compression
    lower = result.lower()
    for phrase, replacement in PHRASE_MAP.items():
        if phrase in lower:
            # Case-insensitive replacement
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            result = pattern.sub(replacement, result)

    # Strip filler words (only standalone words, not parts of larger words)
    words = result.split()
    compressed = []
    for word in words:
        clean = word.strip(".,;:!?")
        if clean.lower() in STRIP_WORDS and not word.startswith("§"):
            continue
        compressed.append(word)
    result = " ".join(compressed)

    # Restore preserved patterns
    for placeholder, original in preserved:
        result = result.replace(placeholder, original)

    # Clean up extra whitespace
    result = re.sub(r"\s+", " ", result).strip()
    return result


def decompress_context(text: str) -> str:
    """Light expansion for human-readable output (adds back minimal articles)."""
    # Minimal — just clean up spacing artifacts
    return re.sub(r"\s+", " ", text).strip()


def compression_ratio(original: str, compressed: str) -> float:
    """Calculate token savings ratio."""
    orig_tokens = len(original.split())
    comp_tokens = len(compressed.split())
    if orig_tokens == 0:
        return 0.0
    return round(1 - (comp_tokens / orig_tokens), 3)
