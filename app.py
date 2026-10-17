"""AI Course & Career Advisor - Streamlit app.

Run locally:  streamlit run app.py
"""
import pandas as pd
import streamlit as st

from agents.config import load_careers
from agents.cv_analyst import read_cv
from agents.llm import LLM
from agents.orchestrator import Orchestrator
from agents.progress_tracker import ProgressTracker
from agents.skills import all_skills
from rag.vector_store import KnowledgeBase

st.set_page_config(page_title="AI Course & Career Advisor", page_icon="🎓", layout="wide")


@st.cache_resource(show_spinner="Building knowledge base (first run downloads a small embedding model)...")
def get_kb():
    return KnowledgeBase()


@st.cache_resource
def get_orchestrator():
    return Orchestrator(get_kb(), LLM(), ProgressTracker())


orch = get_orchestrator()
tracker = orch.tracker

# ---------------- Sidebar ----------------
with st.sidebar:
    st.title("🎓 Career Advisor")
    learner = st.text_input("Your name (used to save progress)", value=st.session_state.get("learner", ""))
    st.session_state["learner"] = learner.strip()
    st.divider()
    with st.expander("🤖 Connect free AI (LLM)", expanded=not orch.llm.available):
        provider = st.radio("Provider", ["Groq", "Google Gemini"], horizontal=True)
        default_model = "gemini-2.5-flash" if provider == "Google Gemini" else "openai/gpt-oss-20b"
        key = st.text_input("Paste your free API key", type="password")
        model = st.text_input("Model name", value=default_model)
        if st.button("Connect"):
            orch.llm.api_key = key.strip()
            orch.llm.model = model.strip()
            orch.llm.base_url = ("https://generativelanguage.googleapis.com/v1beta/openai/"
                                 if provider == "Google Gemini" else "https://api.groq.com/openai/v1")
            orch.llm._client = None
            try:
                orch.llm.chat("You are a test.", "Reply with the single word OK.")
                st.success("Connected! The AI is now used by the agents.")
            except Exception as e:  # noqa: BLE001
                orch.llm.api_key = ""
                st.error(f"Could not connect: {e}")
    st.caption("System status")
    st.write(("🟢 LLM connected: `" + orch.llm.model + "`") if orch.llm.available
             else "🟡 No LLM key - running in rule-based mode")
    st.write(f"🔎 Vector search: `{orch.recommender.kb.backend}`")
    st.write(f"📚 Courses in catalogue: {len(orch.recommender.kb.courses)}")

st.title("AI Course & Career Advisor")
st.caption("CV + career goal → skill gaps → courses → weekly plan → progress")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["1️⃣ Profile & CV", "2️⃣ Skill Gap", "3️⃣ Courses", "4️⃣ Study Plan", "5️⃣ Progress"])

# ---------------- 1. Input ----------------
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        up = st.file_uploader("Upload your CV", type=["pdf", "docx", "txt"])
        use_sample = st.checkbox("No CV handy? Use the sample CV")
        pasted = st.text_area("...or paste CV text", height=150)
    with c2:
        careers = list(load_careers()) + ["Other (type below)"]
        choice = st.selectbox("Target career", careers)
        goal = st.text_input("Other career") if choice.startswith("Other") else choice
        hours = st.slider("Hours you can study per week", 2, 30, 8)
        level = st.select_slider("Preferred course level", ["Beginner", "Intermediate", "Advanced"])
        extra = st.multiselect("Skills you have that may not be on your CV", all_skills())

    if st.button("Analyse my profile", type="primary"):
        cv_text = ""
        if up is not None:
            cv_text = read_cv(up.name, up.getvalue())
        elif pasted.strip():
            cv_text = pasted
        elif use_sample:
            with open("data/sample_cv.txt", encoding="utf-8") as f:
                cv_text = f.read()
        if not cv_text.strip() and not extra:
            st.error("Please upload/paste a CV or select some skills.")
        elif not goal.strip():
            st.error("Please enter a target career.")
        else:
            with st.spinner("Agents at work: CV → Career → Gap → Courses → Plan..."):
                st.session_state["result"] = orch.run(cv_text, goal, hours, level, extra)
                st.session_state["settings"] = {"hours": hours, "level": level}
            st.success("Done! Open the next tabs to see your results.")
            st.caption("Agents called: " + " → ".join(st.session_state["result"]["trace"]))

r = st.session_state.get("result")

# ---------------- 2. Skill gap ----------------
with tab2:
    if not r:
        st.info("Run the analysis in tab 1 first.")
    else:
        req, g = r["required"], r["gap"]
        if not req["core"]:
            st.error("Sorry, I couldn't find skill requirements for that career. "
                     "Pick one from the list, or add an LLM key to handle custom careers.")
        else:
            st.subheader(f"Target: {req['career']}")
            st.caption(f"{req['description']}  ·  Source: "
                       + ("🤖 " if req["source"].startswith("AI") else "") + req["source"])
            st.metric("Career readiness", f"{g['readiness']}%")
            st.progress(g["readiness"] / 100)
            a, b, c = st.columns(3)
            a.markdown("**✅ Skills you have**\n\n" + "\n".join(f"- {s}" for s in g["matched"]) or "-")
            b.markdown("**🔴 Core skills missing**\n\n" + "\n".join(f"- {s}" for s in g["missing_core"]))
            c.markdown("**🟡 Nice-to-have missing**\n\n" + "\n".join(f"- {s}" for s in g["missing_nice"]))
            st.subheader("Advisor summary")
            st.caption("🤖 Written by the LLM" if r.get("advice_source") == "llm"
                       else "📝 Template (connect the AI in the sidebar for a personalised summary)")
            st.write(r["advice"])
        with st.expander("What the CV Analyst extracted"):
            cv = r["cv"]
            st.caption("🤖 Extracted by the LLM, then every skill checked against your CV text"
                       if cv.get("source") == "llm+rules" else "📝 Extracted by keyword rules")
            st.write("**Skills (with evidence from your CV):**", cv.get("evidence", {}))
            for k in ("education", "experience", "projects"):
                if cv.get(k):
                    st.write(f"**{k.title()}:**")
                    st.write("\n".join(f"- {x}" for x in cv[k]))

# ---------------- 3. Courses ----------------
with tab3:
    if not r:
        st.info("Run the analysis in tab 1 first.")
    else:
        for skill, courses in r["recommendations"].items():
            tag = "🔴 core" if skill in r["gap"]["missing_core"] else "🟡 nice-to-have"
            st.markdown(f"#### {skill.title()}  ·  {tag}")
            if not courses:
                st.warning("No course for this skill in our catalogue (we don't invent courses).")
            for c in courses:
                st.markdown(f"- **[{c['title']}]({c['url']})** — {c['provider']} · {c['level']} · "
                            f"~{c['hours']:.0f} h  \n  {c['description']}")

# ---------------- 4. Plan ----------------
with tab4:
    if not r:
        st.info("Run the analysis in tab 1 first.")
    elif not r["plan"]:
        st.success("No gaps to plan for - you're ready! 🎉")
    else:
        total = sum(w["hours"] for w in r["plan"])
        st.subheader(f"{len(r['plan'])}-week plan · {total:.0f} hours total")
        for w in r["plan"]:
            with st.expander(f"Week {w['week']}  ({w['hours']} h)", expanded=w["week"] <= 2):
                st.dataframe(pd.DataFrame(w["items"])[["skill", "course", "hours", "url"]],
                             hide_index=True,
                             column_config={"url": st.column_config.LinkColumn("link")})
        if st.button("💾 Save this plan to my progress tracker"):
            if not st.session_state["learner"]:
                st.error("Enter your name in the sidebar first.")
            else:
                s = st.session_state["settings"]
                tracker.save_plan(st.session_state["learner"], r["required"]["career"],
                                  r["current_skills"], s["hours"], s["level"], r["plan"])
                for k in [k for k in st.session_state if str(k).startswith("done_")]:
                    del st.session_state[k]
                st.success("Saved as a fresh plan (old progress cleared). Track it in the Progress tab.")

# ---------------- 5. Progress ----------------
with tab5:
    name = st.session_state["learner"]
    if not name:
        st.info("Enter your name in the sidebar to see your saved plan.")
    else:
        items = tracker.get_items(name)
        if not items:
            st.info("No saved plan yet. Create one and click 'Save' in the Study Plan tab.")
        else:
            p = tracker.progress(name)
            m1, m2, m3 = st.columns(3)
            m1.metric("Completed", f"{p['percent']}%")
            m2.metric("Hours done", f"{p['done_hours']} / {p['total_hours']}")
            m3.metric("Skills completed", len(p["completed_skills"]))
            st.progress(p["percent"] / 100)

            def toggle(item_id, key):
                tracker.set_status(item_id, st.session_state[key])

            for week in sorted({i["week"] for i in items}):
                st.markdown(f"**Week {week}**")
                for it in [i for i in items if i["week"] == week]:
                    key = f"done_{it['id']}"
                    st.checkbox(f"{it['course']} — {it['skill']} ({it['hours']} h)",
                                value=it["status"] == "done", key=key,
                                on_change=toggle, args=(it["id"], key))

            st.caption(f"Plan for: {(tracker.get_learner(name) or {}).get('career', '-')}")
            st.divider()
            if st.button("🗑️ Reset my progress"):
                tracker.reset(name)
                for k in [k for k in st.session_state if str(k).startswith("done_")]:
                    del st.session_state[k]
                st.rerun()
            if st.button("🔄 Reassess & update my plan"):
                new = orch.reassess(name)
                st.success(f"Updated! Readiness is now {new['gap']['readiness']}%. "
                           f"{len(new['plan'])} week(s) of learning left.")
                st.rerun()
