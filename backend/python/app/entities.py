"""Entity extraction from document text using regex patterns.

Extracts structured entities (people, organizations, dates, monetary values,
technical identifiers, regulations, etc.) from ingested chunks.  No external
NLP dependencies required — uses compiled regex patterns for portability.
"""

import re
from dataclasses import dataclass, asdict


@dataclass
class Entity:
    text: str
    label: str
    start: int
    end: int
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Pre-compiled patterns — order matters (first match wins for overlaps)
# ---------------------------------------------------------------------------

# Common words to exclude from PROPER_NOUN matches
_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "as", "is", "was", "are",
    "were", "been", "be", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "shall",
    "can", "not", "no", "nor", "so", "if", "then", "than",
    "too", "very", "just", "about", "above", "after", "again",
    "all", "also", "any", "because", "before", "between", "both",
    "each", "few", "more", "most", "other", "some", "such",
    "this", "that", "these", "those", "it", "its", "their",
    "they", "them", "we", "our", "you", "your", "he", "him",
    "his", "she", "her", "my", "me", "i",
})


_PATTERNS: list[tuple[str, re.Pattern]] = [
    # Monetary values: $49, $1,000, $1.5M, USD 50,000
    ("MONETARY", re.compile(
        r"\$[\d,]+(?:\.\d+)?[MBKk]?"
        r"|USD\s+[\d,]+(?:\.\d+)?"
        r"|\b\d{1,3}(?:,\d{3})+\s+(?:USD|EUR|GBP)\b",
        re.IGNORECASE,
    )),
    # Percentages: 30%, 99.95%, 60 percent
    ("PERCENTAGE", re.compile(
        r"\b\d+(?:\.\d+)?\s*%(?!\w)"
        r"|\b\d+(?:\.\d+)?\s+percent\b",
        re.IGNORECASE,
    )),
    # ISO dates: 2024-01-15, 2024/01/15
    ("DATE", re.compile(
        r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",
    )),
    # Written dates: January 15, 2024 / 15 January 2024
    ("DATE", re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{1,2},?\s+\d{4}\b"
        r"|\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{4}\b",
        re.IGNORECASE,
    )),
    # Email addresses
    ("EMAIL", re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    )),
    # URLs
    ("URL", re.compile(
        r"https?://[^\s<>\"']+",
        re.IGNORECASE,
    )),
    # Technical IDs: EQ-1001, PRM-2026-5000, WO-2026-1000
    ("TECHNICAL_ID", re.compile(
        r"\b[A-Z]{2,5}-\d{2,6}(?:-\d{2,6})?\b",
    )),
    # Version numbers: v2.1, version 3.0 (must follow "version" or "v" to
    # avoid matching standalone decimals like 99.99 in "99.99 percent")
    ("VERSION", re.compile(
        r"\bv\d+\.\d+(?:\.\d+)?\b"
        r"|\bversion\s+\d+\.\d+(?:\.\d+)?",
        re.IGNORECASE,
    )),
    # Durations: 30 days, 14-day, 2 weeks, 4 hours
    ("DURATION", re.compile(
        r"\b\d+[-\s]?(?:day|week|month|year|hour|minute|second)s?\b",
        re.IGNORECASE,
    )),
    # Quoted strings (likely named entities or key phrases)
    ("QUOTED", re.compile(
        r"\"([^\"]{2,80})\""
        r"|'([^']{2,80})'",
    )),
    # Abbreviations in parentheses: (CEO), (CTO), (SRE)
    ("ABBREVIATION", re.compile(
        r"\(([A-Z]{2,6})\)",
    )),
    # Section references: Section 36, Section 3.2
    ("SECTION_REF", re.compile(
        r"\bSection\s+\d+(?:\.\d+)*\b",
        re.IGNORECASE,
    )),
    # Article references: Article 15, Article 3(2)
    ("ARTICLE_REF", re.compile(
        r"\bArticle\s+\d+(?:\(\d+\))?\b",
        re.IGNORECASE,
    )),
    # Regulation references: OISD-116, DGMS Circular 2022-05
    # (must start with known regulatory prefix to avoid matching AES-256 etc.)
    ("REGULATION", re.compile(
        r"\b[A-Z]{2,10}\s+Circular\s+\d{4}-\d{1,3}\b",
        re.IGNORECASE,
    )),
    # Capitalized multi-word phrases: "Aurora Labs", "Microsoft Teams"
    ("PROPER_NOUN", re.compile(
        r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b",
    )),
    # Single capitalized words after sentence boundary: ". Atlas", "! Beacon"
    # Uses lookbehind for sentence start (period/exclamation/question + space)
    ("PROPER_NOUN", re.compile(
        r"(?<=[.!?]\s)([A-Z][a-z]{2,15})\b",
    )),
    # Standalone capitalized word at start of text
    ("PROPER_NOUN", re.compile(
        r"^([A-Z][a-z]{2,15})\b",
    )),
]


def extract_entities(text: str, *, dedupe: bool = True) -> list[Entity]:
    """Extract entities from text using regex patterns.

    Returns a list of Entity objects sorted by position.  When *dedupe* is
    True, duplicate entities (same text + label) are collapsed to the first
    occurrence.
    """
    entities: list[Entity] = []
    seen: set[tuple[str, str]] = set()

    for label, pattern in _PATTERNS:
        for m in pattern.finditer(text):
            # Quoted strings capture group 1 or 2; lookbehind patterns use
            # group 1 for the actual entity text.  Use group(1) when it exists
            # and is non-None, otherwise fall back to group(0).
            if label == "QUOTED":
                matched = m.group(1) or m.group(2) or m.group(0)
            elif m.lastindex and m.group(1):
                matched = m.group(1)
            else:
                matched = m.group(0)

            matched = matched.strip()
            if not matched:
                continue

            # Skip stopwords for PROPER_NOUN to avoid "The", "A", etc.
            if label == "PROPER_NOUN" and matched.lower() in _STOPWORDS:
                continue

            key = (matched, label)
            if dedupe and key in seen:
                continue
            seen.add(key)

            # Compute start position: for capture-group patterns, offset by
            # the group start within the full match.
            if m.lastindex and m.group(1) and label != "QUOTED":
                start = m.start(1)
                end = m.end(1)
            else:
                start = m.start()
                end = m.end()

            entities.append(Entity(
                text=matched,
                label=label,
                start=start,
                end=end,
            ))

    # Sort by position in text
    entities.sort(key=lambda e: e.start)
    return entities


def extract_entities_batch(texts: list[str], *, dedupe: bool = True) -> dict[str, list[Entity]]:
    """Extract entities from multiple text chunks.

    Returns {chunk_text: [entities]} for non-empty results.
    """
    results = {}
    for text in texts:
        ents = extract_entities(text, dedupe=dedupe)
        if ents:
            results[text] = ents
    return results
