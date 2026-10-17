"""Agent 3 - Skill-Gap Analyst: compares current skills with required skills."""

CORE_WEIGHT, NICE_WEIGHT = 2, 1


class SkillGapAnalyst:
    name = "Skill-Gap Analyst"

    def analyze(self, current: list, required: dict) -> dict:
        have = {s.lower() for s in current}
        core, nice = required.get("core", []), required.get("nice", [])
        missing_core = [s for s in core if s not in have]
        missing_nice = [s for s in nice if s not in have]
        total = CORE_WEIGHT * len(core) + NICE_WEIGHT * len(nice)
        got = CORE_WEIGHT * (len(core) - len(missing_core)) + NICE_WEIGHT * (len(nice) - len(missing_nice))
        return {
            "matched": [s for s in core + nice if s in have],
            "missing_core": missing_core,
            "missing_nice": missing_nice,
            "readiness": round(100 * got / total, 1) if total else 0.0,
        }
