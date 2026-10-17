"""RAG knowledge base: course catalogue + career skill frameworks.

Pipeline: documents -> chunks -> embeddings -> vector search.
Uses ChromaDB (free, local) with its built-in all-MiniLM-L6-v2 embedding model.
If ChromaDB is not installed, falls back to a TF-IDF index so the app still runs.
"""
import csv
import sys

from agents.config import CAREERS_JSON, CHROMA_DIR, COURSES_CSV, load_careers

# Streamlit Cloud ships an old sqlite3; chromadb needs a newer one.
try:
    __import__("pysqlite3")
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except ImportError:
    pass


def load_courses() -> list:
    """Load, clean and de-duplicate the course catalogue."""
    seen, rows = set(), []
    with open(COURSES_CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r.get("title") or not r.get("skills") or not r.get("description"):
                continue  # drop incomplete records
            key = (r["title"].strip().lower(), r["provider"].strip().lower())
            if key in seen:
                continue  # drop duplicates
            seen.add(key)
            r["skills"] = [s.strip().lower() for s in r["skills"].split("|") if s.strip()]
            r["hours"] = float(r.get("hours") or 5)
            rows.append(r)
    return rows


def chunk_text(text: str, size: int = 500, overlap: int = 50) -> list:
    """Split long text into overlapping chunks (course descriptions are usually 1 chunk)."""
    if len(text) <= size:
        return [text]
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks


def build_documents() -> list:
    docs = []
    for c in load_courses():
        body = f"{c['title']} by {c['provider']} ({c['level']}). Skills: {', '.join(c['skills'])}. {c['description']}"
        for i, ch in enumerate(chunk_text(body)):
            docs.append({"id": f"{c['id']}-{i}", "text": ch,
                         "meta": {"type": "course", "course_id": c["id"]}})
    for career, info in load_careers().items():
        body = f"Career: {career}. {info['description']} Core skills: {', '.join(info['core'])}. " \
               f"Nice to have: {', '.join(info['nice'])}."
        docs.append({"id": f"career-{career}", "text": body,
                     "meta": {"type": "career", "career": career}})
    return docs


class KnowledgeBase:
    def __init__(self, persist_dir: str = CHROMA_DIR, force_tfidf: bool = False):
        self.courses = {c["id"]: c for c in load_courses()}
        self.docs = build_documents()
        self.backend = None
        if not force_tfidf:
            try:
                import chromadb
                client = chromadb.PersistentClient(path=persist_dir)
                self.col = client.get_or_create_collection("advisor_kb")
                if self.col.count() != len(self.docs):  # (re)ingest when data changes
                    client.delete_collection("advisor_kb")
                    self.col = client.get_or_create_collection("advisor_kb")
                    self.col.add(ids=[d["id"] for d in self.docs],
                                 documents=[d["text"] for d in self.docs],
                                 metadatas=[d["meta"] for d in self.docs])
                self.backend = "chromadb"
            except Exception as e:  # noqa: BLE001
                print("ChromaDB unavailable, using TF-IDF fallback:", e)
        if self.backend is None:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
            self.matrix = self.vec.fit_transform([d["text"] for d in self.docs])
            self.backend = "tfidf"

    def search(self, query: str, k: int = 8, doc_type: str = None) -> list:
        """Return [{'text', 'meta', 'score'}] most similar to the query."""
        if self.backend == "chromadb":
            where = {"type": doc_type} if doc_type else None
            res = self.col.query(query_texts=[query], n_results=k, where=where)
            out = []
            for text, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
                out.append({"text": text, "meta": meta, "score": round(1 / (1 + dist), 4)})
            return out
        from sklearn.metrics.pairwise import cosine_similarity
        sims = cosine_similarity(self.vec.transform([query]), self.matrix)[0]
        order = sims.argsort()[::-1]
        out = []
        for i in order:
            d = self.docs[i]
            if doc_type and d["meta"]["type"] != doc_type:
                continue
            out.append({"text": d["text"], "meta": d["meta"], "score": round(float(sims[i]), 4)})
            if len(out) == k:
                break
        return out
