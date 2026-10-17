"""Agent 5 - Study Planner: turns recommended courses into a weekly plan."""
# Learn foundations first (lower number = earlier)
ORDER = {
    "python": 0, "excel": 0, "statistics": 0, "sql": 0, "git": 0, "communication": 0, "linux": 0,
    "html/css": 0, "java": 0, "probability": 1, "pandas": 1, "numpy": 1, "data cleaning": 1,
    "data visualization": 2, "power bi": 2, "tableau": 2, "dbms": 1, "javascript": 1, "docker": 1,
    "requirements gathering": 1, "stakeholder management": 1, "agile": 1,
    "business process modelling": 2, "jira": 2, "machine learning": 3, "a/b testing": 3,
    "deep learning": 4, "nlp": 5, "computer vision": 5, "llms": 5, "mlops": 5, "kubernetes": 2,
    "ci/cd": 2, "cloud": 2, "etl": 2, "spark": 3, "airflow": 3, "data warehousing": 3,
    "react": 2, "apis": 2, "dsa": 1, "system design": 4,
}


class StudyPlanner:
    name = "Study Planner"

    def plan(self, recommendations: dict, core_gaps: list, hours_per_week: float = 8,
             max_course_hours: float = 20) -> list:
        """Return list of weeks: [{'week': 1, 'items': [{skill, course, hours}], 'hours': x}]."""
        hours_per_week = max(1.0, float(hours_per_week))
        tasks, by_course = [], {}
        for skill, courses in recommendations.items():
            if not courses:
                continue
            # best course not already scheduled; if all are, that course covers this skill too
            c = next((c for c in courses if c["id"] not in by_course), None)
            if c is None:
                t = by_course[courses[0]["id"]]
                t["skill"] += f" + {skill}"
                t["priority"] = min(t["priority"], 0 if skill in core_gaps else 1)
                continue
            t = {"skill": skill, "course_id": c["id"], "course": c["title"],
                 "url": c["url"], "hours": min(c["hours"], max_course_hours),
                 "priority": 0 if skill in core_gaps else 1}
            by_course[c["id"]] = t
            tasks.append(t)
        tasks.sort(key=lambda t: (t["priority"], ORDER.get(t["skill"].split(" + ")[0], 3)))

        weeks, week, left = [], {"week": 1, "items": [], "hours": 0.0}, hours_per_week
        for t in tasks:
            # 1) cut the course into pieces that fit the remaining weekly time
            pieces, remaining, room = [], t["hours"], left
            while remaining > 1e-9:
                if room <= 1e-9:
                    room = hours_per_week
                piece = min(remaining, room)
                pieces.append(piece)
                remaining -= piece
                room -= piece
            # 2) place the pieces week by week
            for n, piece in enumerate(pieces, 1):
                if left <= 1e-9:
                    weeks.append(week)
                    week = {"week": week["week"] + 1, "items": [], "hours": 0.0}
                    left = hours_per_week
                label = t["course"] if len(pieces) == 1 else f"{t['course']} (part {n}/{len(pieces)})"
                week["items"].append({"skill": t["skill"], "course_id": t["course_id"],
                                      "course": label, "url": t["url"], "hours": round(piece, 1)})
                week["hours"] = round(week["hours"] + piece, 1)
                left -= piece
        if week["items"]:
            weeks.append(week)
        return weeks
