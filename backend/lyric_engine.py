"""Deterministic, original-first Nepali lyric helper.

This module does not call a paid AI service. It turns a user's story into a
structured songwriting brief and lyric scaffold. The user should review and
rewrite the generated text before publishing.
"""

from dataclasses import dataclass
import re


@dataclass
class LyricRequest:
    idea: str
    mood: str = "emotional"
    language: str = "Nepali"
    perspective: str = "first-person"


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def build_lyric_draft(req: LyricRequest) -> dict:
    idea = _clean(req.idea)
    if not idea:
        raise ValueError("A song idea is required.")
    if len(idea) > 500:
        raise ValueError("Song idea must be 500 characters or fewer.")

    # This is intentionally a scaffold rather than pretending to be an LLM.
    # It gives the eventual LLM a clean, reproducible songwriting structure.
    theme = idea.rstrip("।.!?")
    if req.language.lower() == "nepali":
        sections = {
            "verse_1": f"{theme} — दृश्य र पहिलो भावना लेख्नुहोस्।",
            "pre_chorus": "मनभित्र दबिएको कुरा विस्तारै बाहिर ल्याउनुहोस्।",
            "chorus": "मुख्य भावनालाई छोटो, सम्झन मिल्ने र मौलिक हुकमा बदल्नुहोस्।",
            "verse_2": "उही कथालाई अर्को दृश्य वा सम्झनाबाट अगाडि बढाउनुहोस्।",
            "bridge": "कथामा सानो मोड, स्वीकारोक्ति वा आशाको क्षण थप्नुहोस्।",
            "final_chorus": "मुख्य हुकलाई भावनात्मक निष्कर्षसहित पुनः लेख्नुहोस्।",
        }
    else:
        sections = {
            "verse_1": f"{theme} — describe the opening scene and feeling.",
            "pre_chorus": "Build the emotion toward the central idea.",
            "chorus": "Write a short, memorable and original hook around the core feeling.",
            "verse_2": "Move the story forward with a second scene or memory.",
            "bridge": "Add a small emotional turn, realization or moment of hope.",
            "final_chorus": "Repeat the central hook with an emotional resolution.",
        }

    return {
        "status": "draft",
        "originality_note": "Draft scaffold only. Review and rewrite before publication.",
        "request": req.__dict__,
        "sections": sections,
    }
