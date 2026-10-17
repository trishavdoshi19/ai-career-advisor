"""Agent 7 - Career Advisor Orchestrator: coordinates all agents and combines outputs."""
from agents.career_analyst import CareerAnalyst
from agents.course_recommender import CourseRecommender
from agents.cv_analyst import CVAnalyst
from agents.progress_tracker import ProgressTracker
from agents.skill_gap import SkillGapAnalyst
from agents.skills import normalize_skill
from agents.study_planner import StudyPlanner


class Orchestrator:
    def __init__(self, kb, llm=None, tracker=None):
        self.llm = llm
        self.cv = CVAnalyst(llm)
        self.career = CareerAnalyst(kb, llm)
        self.gap = SkillGapAnalyst()
        self.recommender = CourseRecommender(kb)
        self.planner = StudyPlanner()
        self.tracker = tracker or ProgressTracker()

    def run(self, cv_text: str, goal: str, hours_per_week: float = 8, level: str = "Beginner",
            extra_skills=None) -> dict:
        trace = []
        cv = self.cv.analyze(cv_text) if cv_text.strip() else {"skills": [], "evidence": {},
                                                                 "education": [], "projects": [],
                                                                 "experience": [], "source": "none"}
        trace.append(self.cv.name)
        current = set(cv["skills"])
        for s in extra_skills or []:
            canon = normalize_skill(s)
            if canon:
                current.add(canon)

        required = self.career.required_skills(goal)
        trace.append(self.career.name)

        gap = self.gap.analyze(sorted(current), required)
        trace.append(self.gap.name)

        gaps = gap["missing_core"] + gap["missing_nice"]
        recs = self.recommender.recommend(gaps, level)
        trace.append(self.recommender.name)

        weeks = self.planner.plan(recs, gap["missing_core"], hours_per_week)
        trace.append(self.planner.name)

        result = {"cv": cv, "current_skills": sorted(current), "required": required, "gap": gap,
                  "recommendations": recs, "plan": weeks, "trace": trace, "advice": ""}
        result["advice"], result["advice_source"] = self.advice(result)
        return result

    def reassess(self, learner: str) -> dict:
        """Progress loop: completed skills -> reassessment -> updated plan for remaining gaps."""
        profile = self.tracker.get_learner(learner)
        if not profile:
            return {}
        prog = self.tracker.progress(learner)
        current = sorted(set(profile["skills"]) | set(prog["completed_skills"]))
        required = self.career.required_skills(profile["career"])
        gap = self.gap.analyze(current, required)
        recs = self.recommender.recommend(gap["missing_core"] + gap["missing_nice"], profile["level"])
        weeks = self.planner.plan(recs, gap["missing_core"], profile["hours_per_week"])
        self.tracker.save_plan(learner, profile["career"], current, profile["hours_per_week"],
                               profile["level"], weeks, keep_done=True)
        return {"current_skills": current, "gap": gap, "plan": weeks}

    def advice(self, r: dict) -> str:
        """Short personalised summary. LLM if available, otherwise a template."""
        g, career = r["gap"], r["required"]["career"]
        weeks = len(r["plan"])
        base = (f"You are {g['readiness']}% ready for {career}. You already have "
                f"{', '.join(g['matched']) or 'no matching skills yet'}. Focus first on "
                f"{', '.join(g['missing_core'][:3]) or 'nice-to-have skills'}. "
                f"Your plan takes about {weeks} week(s).")
        if not (self.llm and self.llm.available):
            return base, "template"
        try:
            text = self.llm.chat(
                "You are a friendly career advisor. Use ONLY the facts given; do not invent "
                "courses, companies or numbers. 4-5 sentences.",
                f"Facts: {base} Core gaps: {g['missing_core']}. Nice-to-have gaps: {g['missing_nice']}. "
                f"CV projects: {r['cv'].get('projects', [])[:3]}. Give encouraging, practical advice.",
                temperature=0.4,
            )
            return (text, "llm") if text.strip() else (base, "template")
        except Exception:
            return base, "template"
