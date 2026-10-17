"""Agent 4 - Course Recommender: RAG retrieval of catalogue courses for each gap."""

LEVELS = {"Beginner": 0, "Intermediate": 1, "Advanced": 2}


class CourseRecommender:
    name = "Course Recommender"

    def __init__(self, kb):
        self.kb = kb

    def for_skill(self, skill: str, level: str = "Beginner", k: int = 2) -> list:
        hits = self.kb.search(f"course to learn {skill}", k=10, doc_type="course")
        picked, seen = [], set()
        for h in hits:
            cid = h["meta"]["course_id"]
            course = self.kb.courses.get(cid)
            # Grounding: only recommend catalogue courses actually tagged with this skill
            if not course or skill not in course["skills"] or cid in seen:
                continue
            seen.add(cid)
            level_gap = abs(LEVELS.get(course["level"], 0) - LEVELS.get(level, 0))
            picked.append({**course, "score": h["score"], "_rank": (level_gap, -h["score"])})
        # also catch tagged courses the semantic search missed
        for cid, course in self.kb.courses.items():
            if skill in course["skills"] and cid not in seen:
                level_gap = abs(LEVELS.get(course["level"], 0) - LEVELS.get(level, 0))
                picked.append({**course, "score": 0.0, "_rank": (level_gap, 1)})
        picked.sort(key=lambda c: c["_rank"])
        return [{k: v for k, v in c.items() if k != "_rank"} for c in picked[:k]]

    def recommend(self, gaps: list, level: str = "Beginner") -> dict:
        """skill -> list of courses ([] means no grounded course: we never invent one)."""
        return {skill: self.for_skill(skill, level) for skill in gaps}
