"""Entity extraction from document text using regex patterns.

Extracts structured entities (people, organizations, dates, monetary values,
technical identifiers, regulations, etc.) from ingested chunks.  No external
NLP dependencies required — uses compiled regex patterns for portability.
"""

import re
from dataclasses import dataclass, field, asdict
from typing import Optional


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
        r"\b\d+(?:\.\d+)?\s*%\b"
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
    # Phone numbers: +1-555-123-4567, (555) 123-4567
    ("PHONE", re.compile(
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b",
    )),
    # Technical IDs: EQ-1001, PRM-2026-5000, WO-2026-1000
    ("TECHNICAL_ID", re.compile(
        r"\b[A-Z]{2,5}-\d{2,6}(?:-\d{2,6})?\b",
    )),
    # Version numbers: v2.1, version 3.0, API v1
    ("VERSION", re.compile(
        r"\bv?\d+\.\d+(?:\.\d+)?\b"
        r"|version\s+\d+\.\d+(?:\.\d+)?",
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
    # Capitalized words (potential proper nouns) — 2+ words
    ("PROPER_NOUN", re.compile(
        r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b",
    )),
    # Single capitalized words (likely proper nouns when standalone)
    ("PROPER_NOUN", re.compile(
        r"\b(?:^|\.\s+)([A-Z][a-z]{2,15})\b",
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
    ("REGULATION", re.compile(
        r"\b[A-Z]{2,10}\s+Circular\s+\d{4}-\d{1,3}\b"
        r"|\b[A-Z]{2,10}-\d{2,4}\b",
        re.IGNORECASE,
    )),
]

# Labels that are "named entities" (not just data patterns)
_NAMED_ENTITY_LABELS = {"PROPER_NOUN", "QUOTED", "REGULATION", "SECTION_REF", "ARTICLE_REF"}


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
            # Quoted strings capture group 1 or 2
            if label == "QUOTED":
                matched = m.group(1) or m.group(2) or m.group(0)
            else:
                matched = m.group(0)

            key = (matched.strip(), label)
            if dedupe and key in seen:
                continue
            seen.add(key)

            entities.append(Entity(
                text=matched.strip(),
                label=label,
                start=m.start(),
                end=m.end(),
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
