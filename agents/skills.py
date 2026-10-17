"""Skill normalisation: maps free-text skill names to one canonical name."""
import re

from agents.config import load_skill_aliases


def _pattern(alias: str) -> re.Pattern:
    # word-boundary that also works for things like "c++", "a/b testing", "node.js"
    return re.compile(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])")


def normalize_skill(name: str):
    """Return canonical skill for a free-text name, or None if unknown."""
    n = name.strip().lower()
    for canon, aliases in load_skill_aliases().items():
        if n == canon or n in aliases:
            return canon
    return None


def find_skills_in_text(text: str) -> dict:
    """canonical skill -> the alias found in the text (evidence)."""
    low = " " + text.lower() + " "
    found = {}
    for canon, aliases in load_skill_aliases().items():
        for alias in sorted(set([canon] + aliases), key=len, reverse=True):
            if _pattern(alias).search(low):
                found[canon] = alias
                break
    return found


def all_skills() -> list:
    return sorted(load_skill_aliases().keys())
