"""Agent 1 - CV Analyst: extracts skills, education, projects and experience."""
import io
import re

from agents.skills import find_skills_in_text, normalize_skill

SECTION_HEADINGS = {
    "education": ["education", "academic", "qualifications"],
    "experience": ["experience", "work experience", "internship", "internships", "employment"],
    "projects": ["projects", "academic projects", "personal projects"],
}
ALL_HEADINGS = ["skills", "technical skills", "certifications", "achievements", "summary",
                "objective", "profile", "languages", "hobbies", "interests", "publications",
                "extracurricular", "positions of responsibility", "contact"] + \
               [h for hs in SECTION_HEADINGS.values() for h in hs]


def read_cv(file_name: str, data: bytes) -> str:
    """Extract plain text from a PDF, DOCX or TXT upload."""
    name = file_name.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if name.endswith(".docx"):
        import docx
        d = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in d.paragraphs)
    return data.decode("utf-8", errors="ignore")


def clean_text(text: str) -> str:
    text = text.replace("\r", "\n").replace("•", "\n").replace("\t", " ")
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_sections(text: str) -> dict:
    """Very simple heading-based section splitter (fallback when no LLM)."""
    sections = {k: [] for k in SECTION_HEADINGS}
    current = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        key = line.lower().rstrip(":").strip()
        if key in ALL_HEADINGS and len(line) < 40:
            current = next((s for s, hs in SECTION_HEADINGS.items() if key in hs), None)
            continue
        if current:
            sections[current].append(line)
    return {k: v[:10] for k, v in sections.items()}


class CVAnalyst:
    name = "CV Analyst"

    def __init__(self, llm=None):
        self.llm = llm

    def analyze(self, cv_text: str) -> dict:
        text = clean_text(cv_text)
        evidence = find_skills_in_text(text)          # grounded keyword extraction
        result = {"skills": sorted(evidence), "evidence": evidence,
                  **_split_sections(text), "source": "rules"}

        if self.llm and self.llm.available:
            data = self.llm.chat_json(
                "You are a CV analyst. Extract information ONLY if it is written in the CV.",
                "Return JSON with keys: skills (list of strings), education (list), "
                "projects (list), experience (list). Keep each item short.\n\nCV:\n" + text[:8000],
            )
            if data:
                low = text.lower()
                for s in data.get("skills", []):
                    canon = normalize_skill(str(s))
                    # Grounding check: only accept skills that are really in the CV
                    if canon and canon not in evidence and str(s).lower() in low:
                        evidence[canon] = str(s).lower()
                result["skills"] = sorted(evidence)
                for k in ("education", "projects", "experience"):
                    if data.get(k):
                        result[k] = [str(x) for x in data[k]][:10]
                result["source"] = "llm+rules"
        return result
