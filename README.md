# 🎓 AI Course & Career Advisor

A **multi-agent AI system with RAG** that reads a student's CV, compares it with a target career, finds skill gaps, recommends **real free courses**, builds a **weekly study plan**, and **tracks progress**. It is built entirely with free tools.

> M.Tech (Data Science) project by **Trisha V Doshi**, in collaboration with LTIMindtree.

---

## ✨ What it does

| Step | Output |
|---|---|
| Upload CV (PDF / DOCX / TXT) + choose a career | Skills, education, projects extracted |
| Skill-gap analysis | Missing core / nice-to-have skills + **career readiness %** |
| Course recommendation (RAG) | Free courses for every gap, from a catalogue of 60 real courses |
| Study planning | Week-by-week plan that fits your available hours |
| Progress tracking | Tick off courses → **reassess** → updated plan |

**Example:** a sample B.E. CV targeting *Business Analyst* is **50% ready**. Its gaps are Power BI, requirements gathering and process modelling, which become a 7-week plan. After Power BI is completed, readiness rises to **59%**.

---

## 🤖 The 7 agents

| Agent | Job | How |
|---|---|---|
| **CV Analyst** | Extract skills, education, projects | LLM + keyword rules; every skill is verified in the CV text |
| **Career Analyst** | Skills needed for the career | 10 skill frameworks; LLM for careers not in the list |
| **Skill-Gap Analyst** | Missing skills + readiness % | Set difference; core skills weighted ×2 |
| **Course Recommender** | Courses for each gap | RAG: embeddings + ChromaDB vector search |
| **Study Planner** | Weekly plan | Core skills and basics first, packed into weekly hours |
| **Progress Tracker** | Save plan + completed courses | SQLite |
| **Orchestrator** | Runs the pipeline | Fixed agent sequence, LLM advice summary, reassessment loop |

```
CV + Career Goal → CV & Career Analysis (LLM) → Skill Gap + Readiness %
→ RAG Retrieval → Course Recommendation → Weekly Study Plan
→ Progress Tracking → Reassess & Re-plan
```

---

## 🛠️ Tech stack (100% free)

| Area | Technology |
|---|---|
| Language | Python |
| Web app | Streamlit |
| LLM | Groq API — GPT-OSS 20B (via the OpenAI-compatible Python SDK); Google Gemini also supported |
| Vector database | ChromaDB |
| Embeddings | all-MiniLM-L6-v2 |
| Database | SQLite |
| CV parsing | pypdf, python-docx |
| Fallback search | scikit-learn TF-IDF |
| Data handling | pandas |

## 🛡️ Reliability by design
- **Grounding:** skills suggested by the LLM are kept only if they appear in the CV.
- **No hallucinated courses:** only catalogue courses tagged with the gap skill are recommended.
- **Hybrid AI:** the LLM handles language tasks; exact rule-based logic handles scores and plans.
- **Graceful fallback:** runs without an LLM key (rule mode) and without ChromaDB (TF-IDF).

---

## 📁 Project structure
```
app.py                     Streamlit UI (5 tabs)
START.bat                  One-click setup & launch (Windows)
agents/
  cv_analyst.py            CV Analyst
  career_analyst.py        Career Analyst
  skill_gap.py             Skill-Gap Analyst
  course_recommender.py    Course Recommender (RAG)
  study_planner.py         Study Planner
  progress_tracker.py      Progress Tracker (SQLite)
  orchestrator.py          Orchestrator
  llm.py, skills.py, config.py
rag/vector_store.py        Ingestion: documents → chunks → embeddings → ChromaDB
data/
  courses.csv              60 free courses
  careers.json             10 career skill frameworks
  skills.json              45 skills + aliases
  sample_cv.txt            Demo CV
```

---

## 🚀 Run it

**Windows (easiest):** install Python 3.11 (tick *Add python.exe to PATH*) and double-click **`START.bat`**.

**Any OS:**
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install chromadb             # optional (vector search)
streamlit run app.py
```

**Optional LLM:** get a free key at [console.groq.com](https://console.groq.com) and paste it in the app sidebar under **🤖 Connect free AI**. The key is never saved to a file.

---

## 🔮 Future scope
- Larger course catalogue and more careers from live data
- Cloud deployment with user login and PostgreSQL
- Conversational advisor agent using LLM tool-calling
