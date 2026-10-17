"""Shared paths and data loaders."""
import json
import os
from functools import lru_cache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
COURSES_CSV = os.path.join(DATA_DIR, "courses.csv")
CAREERS_JSON = os.path.join(DATA_DIR, "careers.json")
SKILLS_JSON = os.path.join(DATA_DIR, "skills.json")
DB_PATH = os.environ.get("ADVISOR_DB", os.path.join(ROOT, "advisor.db"))
CHROMA_DIR = os.path.join(ROOT, "chroma_db")


@lru_cache(maxsize=1)
def load_careers() -> dict:
    with open(CAREERS_JSON, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_skill_aliases() -> dict:
    """canonical skill -> list of aliases (all lowercase)."""
    with open(SKILLS_JSON, encoding="utf-8") as f:
        return json.load(f)
