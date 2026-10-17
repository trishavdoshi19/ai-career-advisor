"""Agent 2 - Career Analyst: identifies the skills required for a target career."""
import difflib

from agents.config import load_careers
from agents.skills import all_skills, normalize_skill


class CareerAnalyst:
    name = "Career Analyst"

    def __init__(self, kb=None, llm=None):
        self.kb, self.llm = kb, llm

    def match_career(self, goal: str):
        """Exact name or a typo of a known career (e.g. 'buisness analyst')."""
        lower = {c.lower(): c for c in load_careers()}
        g = " ".join(goal.strip().lower().split())
        if g in lower:
            return lower[g], 1.0
        close = difflib.get_close_matches(g, list(lower), n=1, cutoff=0.85)
        if close:
            return lower[close[0]], 0.9
        return None, 0.0

    def required_skills(self, goal: str) -> dict:
        career, conf = self.match_career(goal)
        if career:
            info = load_careers()[career]
            return {"career": career, "core": info["core"], "nice": info["nice"],
                    "description": info["description"], "source": "skill framework",
                    "confidence": conf}
        # Unknown career: ask LLM, but restrict answer to our skill vocabulary
        if self.llm and self.llm.available:
            data = self.llm.chat_json(
                "You are a career analyst.",
                f"List the skills needed for the career '{goal}'. Choose ONLY from this list: "
                f"{', '.join(all_skills())}. Return JSON: {{\"core\": [...], \"nice\": [...], "
                f"\"description\": \"one sentence\"}}",
            )
            core = [s for s in (normalize_skill(x) for x in data.get("core", [])) if s]
            nice = [s for s in (normalize_skill(x) for x in data.get("nice", [])) if s and s not in core]
            if core:
                return {"career": goal.title(), "core": core, "nice": nice,
                        "description": data.get("description", ""), "source": "AI-generated (verify)",
                        "confidence": 0.5}
        # No LLM: use RAG to suggest the closest known career, clearly labelled
        if self.kb:
            hits = self.kb.search(goal, k=1, doc_type="career")
            if hits and hits[0]["score"] > 0.35:
                info = load_careers()[hits[0]["meta"]["career"]]
                return {"career": hits[0]["meta"]["career"], "core": info["core"], "nice": info["nice"],
                        "description": info["description"],
                        "source": f"closest match to '{goal}' (connect the AI for exact skills)",
                        "confidence": hits[0]["score"]}
        return {"career": goal, "core": [], "nice": [], "description": "",
                "source": "not found", "confidence": 0.0}
