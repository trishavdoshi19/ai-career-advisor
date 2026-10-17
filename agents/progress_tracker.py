"""Agent 6 - Progress Tracker: stores the plan and completed topics in SQLite."""
import json
import sqlite3
from datetime import datetime

from agents.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS learners (
    name TEXT PRIMARY KEY, career TEXT, skills TEXT, hours_per_week REAL, level TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS plan_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT, learner TEXT, week INTEGER, skill TEXT,
    course_id TEXT, course TEXT, url TEXT, hours REAL, status TEXT DEFAULT 'pending',
    completed_at TEXT);
"""


class ProgressTracker:
    name = "Progress Tracker"

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        with self._conn() as c:
            c.executescript(SCHEMA)

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save_plan(self, learner: str, career: str, skills: list, hours: float, level: str, weeks: list,
                  keep_done: bool = False):
        """Save learner profile + plan.
        keep_done=False -> brand-new plan, old progress is cleared.
        keep_done=True  -> reassessment, completed courses are kept."""
        now = datetime.now().isoformat(timespec="seconds")
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO learners VALUES (?,?,?,?,?,?)",
                      (learner, career, json.dumps(sorted(skills)), hours, level, now))
            if keep_done:
                c.execute("DELETE FROM plan_items WHERE learner=? AND status!='done'", (learner,))
            else:
                c.execute("DELETE FROM plan_items WHERE learner=?", (learner,))
            for w in weeks:
                for it in w["items"]:
                    c.execute("INSERT INTO plan_items (learner, week, skill, course_id, course, url, hours)"
                              " VALUES (?,?,?,?,?,?,?)",
                              (learner, w["week"], it["skill"], it["course_id"], it["course"],
                               it["url"], it["hours"]))

    def reset(self, learner: str):
        """Delete a learner's plan and progress."""
        with self._conn() as c:
            c.execute("DELETE FROM plan_items WHERE learner=?", (learner,))
            c.execute("DELETE FROM learners WHERE name=?", (learner,))

    def get_learner(self, learner: str):
        with self._conn() as c:
            row = c.execute("SELECT * FROM learners WHERE name=?", (learner,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["skills"] = json.loads(d["skills"])
        return d

    def get_items(self, learner: str) -> list:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM plan_items WHERE learner=? ORDER BY status='done' DESC, week, id",
                             (learner,)).fetchall()
        return [dict(r) for r in rows]

    def set_status(self, item_id: int, done: bool):
        with self._conn() as c:
            c.execute("UPDATE plan_items SET status=?, completed_at=? WHERE id=?",
                      ("done" if done else "pending",
                       datetime.now().isoformat(timespec="seconds") if done else None, item_id))

    def progress(self, learner: str) -> dict:
        items = self.get_items(learner)
        total = sum(i["hours"] for i in items)
        done = sum(i["hours"] for i in items if i["status"] == "done")
        done_skills = set()
        for label in {i["skill"] for i in items}:
            parts = [i for i in items if i["skill"] == label]
            if all(p["status"] == "done" for p in parts):
                done_skills.update(label.split(" + "))
        return {"total_hours": round(total, 1), "done_hours": round(done, 1),
                "percent": round(100 * done / total, 1) if total else 0.0,
                "completed_skills": sorted(done_skills),
                "done_items": sum(1 for i in items if i["status"] == "done"), "items": len(items)}
