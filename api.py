from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import json
import re
import sqlite3
import time
import os
from datetime import datetime, timezone
from collections import deque
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from user_taste_profile import generate_llm_taste_profile, resolve_liked_movies
from admin_api import admin_router, load_hidden_movies

# Load environment variables from .env file if it exists
def load_env_file():
    """Load environment variables from .env file if it exists"""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Load .env file on startup
load_env_file()

ROOT = Path(__file__).parent

# Use only the merged dataset which contains all movie profiles
SOURCES = [
    ROOT / "movie_profiles_merged.json",
]


def _to_list(v):
    if not v:
        return []
    if isinstance(v, list):
        return [x for x in v if x]
    return [v]


def _merge_profiles(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    # Union arrays, prefer longer non-empty strings for text fields
    def union(x, y):
        sx = set([*(x or [])])
        for itm in (y or []):
            if itm:
                sx.add(itm)
        return list(sx)

    def pref(x, y):
        sx = (x or "").strip()
        sy = (y or "").strip()
        if not sx:
            return sy
        if not sy:
            return sx
        return sy if len(sy) > len(sx) else sx

    return {
        "title": pref(a.get("title"), b.get("title")),
        "emotional_tone": union(a.get("emotional_tone"), b.get("emotional_tone")),
        "themes": union(a.get("themes"), b.get("themes")),
        "pacing_style": pref(a.get("pacing_style"), b.get("pacing_style")),
        "visual_aesthetic": pref(a.get("visual_aesthetic"), b.get("visual_aesthetic")),
        "target_audience": pref(a.get("target_audience"), b.get("target_audience")),
        "similar_films": union(a.get("similar_films"), b.get("similar_films")),
        "cultural_context": union(a.get("cultural_context"), b.get("cultural_context")),
        "narrative_structure": pref(a.get("narrative_structure"), b.get("narrative_structure")),
        "energy_level": pref(a.get("energy_level"), b.get("energy_level")),
        "discussion_topics": union(a.get("discussion_topics"), b.get("discussion_topics")),
        "card_description": pref(a.get("card_description"), b.get("card_description")),
        "profile_text": pref(a.get("profile_text"), b.get("profile_text")),
        # New structure fields
        "primary_emotional_tone": pref(a.get("primary_emotional_tone"), b.get("primary_emotional_tone")),
        "secondary_emotional_tone": pref(a.get("secondary_emotional_tone"), b.get("secondary_emotional_tone")),
        "primary_theme": pref(a.get("primary_theme"), b.get("primary_theme")),
        "secondary_theme": pref(a.get("secondary_theme"), b.get("secondary_theme")),
        "intensity_level": pref(a.get("intensity_level"), b.get("intensity_level")),
        # Add metadata fields
        "imdb_id": pref(a.get("imdb_id"), b.get("imdb_id")),
        "tmdb_id": pref(a.get("tmdb_id"), b.get("tmdb_id")),
        "poster_url": pref(a.get("poster_url"), b.get("poster_url")),
        "year": pref(a.get("year"), b.get("year")),
        "director": pref(a.get("director"), b.get("director")),
        "genre_tags": union(a.get("genre_tags"), b.get("genre_tags")),
        "plot_summary": pref(a.get("plot_summary"), b.get("plot_summary")),
    }


def _normalize(obj: Dict[str, Any]) -> Dict[str, Any]:
    # Convert new structure to old structure for compatibility
    emotional_tone = []
    if obj.get("primary_emotional_tone"):
        emotional_tone.append(obj.get("primary_emotional_tone"))
    if obj.get("secondary_emotional_tone") and obj.get("secondary_emotional_tone") != "none":
        emotional_tone.append(obj.get("secondary_emotional_tone"))
    
    themes = []
    if obj.get("primary_theme"):
        themes.append(obj.get("primary_theme"))
    if obj.get("secondary_theme") and obj.get("secondary_theme") != "none":
        themes.append(obj.get("secondary_theme"))
    
    return {
        "title": obj.get("title") or obj.get("Title") or "Untitled",
        "emotional_tone": emotional_tone or _to_list(obj.get("emotional_tone")),
        "themes": themes or _to_list(obj.get("themes")),
        "pacing_style": obj.get("pacing_style") or "",
        "visual_aesthetic": obj.get("visual_aesthetic") or "",
        "target_audience": obj.get("target_audience") or "",
        "similar_films": _to_list(obj.get("similar_films")),
        "cultural_context": _to_list(obj.get("cultural_context")),
        "narrative_structure": obj.get("narrative_structure") or "",
        "energy_level": obj.get("energy_level") or "",
        "discussion_topics": _to_list(obj.get("discussion_topics")),
        "card_description": obj.get("card_description") or "",
        "profile_text": obj.get("profile_text") or "",
        # Keep new structure fields
        "primary_emotional_tone": obj.get("primary_emotional_tone"),
        "secondary_emotional_tone": obj.get("secondary_emotional_tone"),
        "primary_theme": obj.get("primary_theme"),
        "secondary_theme": obj.get("secondary_theme"),
        "intensity_level": obj.get("intensity_level"),
        # Add metadata fields
        "imdb_id": obj.get("imdb_id"),
        "tmdb_id": obj.get("tmdb_id"),
        "poster_url": obj.get("poster_url"),
        "year": obj.get("year"),
        "director": obj.get("director"),
        "genre_tags": _to_list(obj.get("genre_tags")),
        "plot_summary": obj.get("plot_summary") or "",
    }


def _load_all_profiles() -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for path in SOURCES:
        try:
            if not path.exists():
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            for obj in data.values():
                m = _normalize(obj)
                key = (m["title"] or "").strip().lower()
                if key in merged:
                    merged[key] = _merge_profiles(merged[key], m)
                else:
                    merged[key] = m
        except Exception:
            # skip bad source but continue others
            continue
    # Reindex as title->profile mapping to align with user_taste_profile expectations
    return {v["title"]: v for v in merged.values()}


# -----------------
# Stage 1 search (MVP): In-memory SQLite FTS5 over profile text
# -----------------
class SearchEngine:
    def __init__(self, profiles: Dict[str, Any]):
        self.conn = sqlite3.connect(":memory:")
        # Do not attempt to enable or load SQLite extensions; many Python builds (e.g., macOS system Python)
        # disable extension loading. FTS5 is available in standard builds and works without enabling extensions.
        self._init_schema()
        self._index_profiles(profiles)

    def _init_schema(self):
        c = self.conn.cursor()
        c.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS movies_fts USING fts5("
            "id, title, tags, text, tokenize='porter'"
            ")"
        )
        self.conn.commit()

    @staticmethod
    def _build_tags(p: Dict[str, Any]) -> str:
        parts: List[str] = []
        parts.extend(p.get("themes", []) or [])
        parts.extend(p.get("emotional_tone", []) or [])
        parts.extend(p.get("similar_films", []) or [])
        parts.extend(p.get("cultural_context", []) or [])
        ns = p.get("narrative_structure") or ""
        if isinstance(ns, list):
            parts.extend([str(x) for x in ns])
        else:
            parts.append(str(ns))
        return " ".join(str(x) for x in parts if x)

    def _index_profiles(self, profiles: Dict[str, Any]):
        c = self.conn.cursor()
        c.execute("DELETE FROM movies_fts")
        for title, p in profiles.items():
            pid = title.strip().lower()
            tags = self._build_tags(p)
            text = "\n".join([
                p.get("title") or "",
                tags,
                p.get("visual_aesthetic") or "",
                p.get("target_audience") or "",
                p.get("profile_text") or "",
            ])
            c.execute(
                "INSERT INTO movies_fts(id, title, tags, text) VALUES (?,?,?,?)",
                (pid, p.get("title") or title, tags, text),
            )
        self.conn.commit()

    def parse_intent(self, q: str) -> Dict[str, Any]:
        ql = (q or "").lower()
        # basic synonyms for vibes/genres
        synonyms = {
            "feel good": ["feelgood", "uplifting", "heartwarming", "comfort", "cozy", "wholesome"],
            "sci fi": ["sci-fi", "science fiction", "scifi"],
            "post apocalyptic": ["post-apocalyptic", "after the apocalypse", "wasteland"],
            "found family": ["chosen family", "makeshift family"],
            "rom com": ["rom-com", "romantic comedy"],
            # mood synonyms
            "sad": ["melancholic", "melancholy", "tragic", "heartbreaking", "tearjerker", "somber", "sombre", "poignant", "bleak", "bittersweet"],
            "scary": ["terrifying", "frightening", "creepy", "disturbing", "unsettling", "horror"],
        }
        # canonical genres we can try to match in tags/text
        genre_map = {
            "sci-fi": ["sci fi", "science fiction", "scifi"],
            "romance": ["romance", "romantic", "rom-com", "rom com"],
            "horror": ["horror", "scary", "gore"],
            "comedy": ["comedy", "funny"],
            "drama": ["drama", "melodrama"],
            "thriller": ["thriller", "suspense"],
            "animation": ["animated", "animation", "cartoon"],
        }
        intent: Dict[str, Any] = {
            "exclude_terms": [],
            "runtime_max": None,
            "genres": [],
            "years": None,  # (min_year, max_year)
            "expanded_query": q,
            "applied_filters": {},
        }
        # exclusions like "no horror", "not horror"
        m = re.search(r"(?:no|not)\s+(horror|gore|animation|animated)", ql)
        if m:
            intent["exclude_terms"].append(m.group(1))
        # runtime hints
        m = re.search(r"under\s+(\d{2,3})\s*(?:min|minutes)?", ql)
        if m:
            try:
                intent["runtime_max"] = int(m.group(1))
            except Exception:
                pass
        if "not too long" in ql:
            intent["runtime_max"] = intent.get("runtime_max") or 120
        # treat "for the night" / "tonight" as a hint for shorter runtime
        if "for the night" in ql or "tonight" in ql:
            intent["runtime_max"] = intent.get("runtime_max") or 120
        # decade/year like 90s, 2010s, after 2000, older than 1980
        m = re.search(r"(\d{4})s", ql)
        if m:
            y = int(m.group(1))
            intent["years"] = (y, y + 9)
        m = re.search(r"(\d{2})0s", ql)
        if not intent["years"] and m:
            # e.g., 90s -> 1990s heuristic
            decade = int(m.group(1))
            base = 1900 if decade >= 2 else 2000
            y = base + decade * 10
            intent["years"] = (y, y + 9)
        m = re.search(r"after\s+(\d{4})", ql)
        if m:
            y = int(m.group(1))
            intent["years"] = (y + 1, 9999)
        m = re.search(r"before\s+(\d{4})", ql)
        if m:
            y = int(m.group(1))
            intent["years"] = (0, y - 1)
        m = re.search(r"older than\s+(\d{4})", ql)
        if m:
            y = int(m.group(1))
            intent["years"] = (0, y - 1)
        # genre detection
        found_genres: List[str] = []
        for canon, alts in genre_map.items():
            for term in [canon, *alts]:
                if re.search(rf"\b{re.escape(term)}\b", ql):
                    found_genres.append(canon)
                    break
        intent["genres"] = sorted(list(set(found_genres)))
        # mood detection
        mood_map = {
            "sad": ["sad", "melancholic", "melancholy", "tragic", "heartbreaking", "tearjerker", "somber", "sombre", "poignant", "bleak", "bittersweet"],
            "feel-good": ["feel good", "feelgood", "uplifting", "heartwarming", "cozy", "comfort", "wholesome"],
            "scary": ["scary", "terrifying", "frightening", "creepy", "disturbing", "horrifying", "unsettling", "horror"],
        }
        mood_terms: List[str] = []
        for terms in mood_map.values():
            if any(re.search(rf"\b{re.escape(t)}\b", ql) for t in terms):
                mood_terms.extend(terms)
        if mood_terms:
            intent["mood_terms"] = sorted(list(set(mood_terms)))
        else:
            intent["mood_terms"] = []
        # query expansion with synonyms (lightweight)
        expansions: List[str] = []
        for key, alts in synonyms.items():
            if re.search(rf"\b{re.escape(key)}\b", ql) or any(re.search(rf"\b{re.escape(a)}\b", ql) for a in alts):
                expansions.extend(alts)
        # Build expanded query by appending synonyms (OR). Keep original first for BM25.
        if expansions:
            intent["expanded_query"] = f"{q} OR " + " OR ".join(sorted(set(expansions)))
        # Record applied filters for response transparency
        af = {}
        if intent["genres"]:
            af["genres"] = intent["genres"]
        if intent.get("mood_terms"):
            af["mood"] = intent["mood_terms"][:5]
        if intent["runtime_max"]:
            af["runtime_max"] = intent["runtime_max"]
        if intent["years"]:
            af["years"] = intent["years"]
        if intent["exclude_terms"]:
            af["exclude"] = intent["exclude_terms"]
        intent["applied_filters"] = af
        return intent

    def search(self, q: str, limit: int = 20) -> List[Dict[str, Any]]:
        intent = self.parse_intent(q)
        c = self.conn.cursor()
        query = intent.get("expanded_query") or q
        try:
            rows = c.execute(
                "SELECT id, title, tags, snippet(movies_fts, 'text', '[', ']', ' … ', 8) AS snip, bm25(movies_fts) AS score "
                "FROM movies_fts WHERE movies_fts MATCH ? ORDER BY score LIMIT ?",
                (query, int(limit * 3)),  # fetch more then post-filter
            ).fetchall()
        except Exception:
            rows = c.execute(
                "SELECT id, title, tags, substr(text,1,200) AS snip, 0 as score FROM movies_fts LIMIT ?",
                (int(limit * 3),),
            ).fetchall()
        results: List[Dict[str, Any]] = []
        for pid, title, tags, snip, score in rows:
            # basic exclusion filter by terms in tags/text
            if intent["exclude_terms"]:
                exq = " OR ".join(intent["exclude_terms"])  # simple OR
                try:
                    block = c.execute(
                        "SELECT 1 FROM movies_fts WHERE id=? AND movies_fts MATCH ?",
                        (pid, exq),
                    ).fetchone()
                    if block:
                        continue
                except Exception:
                    pass
            # genre filter (approximate): require that any of the genre terms appear in tags/text
            if intent["genres"]:
                gq = " OR ".join(intent["genres"])  # genres are canonical words that exist in tags/themes sometimes
                try:
                    ok = c.execute(
                        "SELECT 1 FROM movies_fts WHERE id=? AND movies_fts MATCH ?",
                        (pid, gq),
                    ).fetchone()
                    if not ok:
                        continue
                except Exception:
                    pass
            # mood requirement: if user asked for a mood, require at least one mood term match in this doc
            if intent.get("mood_terms"):
                mq = " OR ".join(intent["mood_terms"])  # simple OR requirement
                try:
                    ok = c.execute(
                        "SELECT 1 FROM movies_fts WHERE id=? AND movies_fts MATCH ?",
                        (pid, mq),
                    ).fetchone()
                    if not ok:
                        continue
                except Exception:
                    pass
            # runtime/year not present in current dataset; keep as hints only
            # badges: choose up to 3 tag tokens that intersect query terms
            q_terms = set([w for w in re.split(r"[^a-z0-9+]+", (q or "").lower()) if w])
            tag_tokens = [t.strip() for t in (tags or "").split()] if tags else []
            badges = []
            for t in tag_tokens:
                tl = t.lower()
                if tl in q_terms and tl not in badges:
                    badges.append(t)
                if len(badges) >= 3:
                    break
            results.append({
                "id": pid,
                "title": title,
                "score": float(score) if isinstance(score, (int, float)) else None,
                "snippet": snip,
                "badges": badges,
            })
            if len(results) >= limit:
                break
        return results


# Load profiles once
movie_profiles: Dict[str, Any] = _load_all_profiles()

def reload_movie_data():
    """Reload movie data from JSON files"""
    global movie_profiles, search_engine, semantic_index
    try:
        movie_profiles = _load_all_profiles()
        
        # Rebuild search engine with new data
        search_engine = SearchEngine(movie_profiles)
        
        # Rebuild semantic index with new data
        try:
            docs: List[VectorDoc] = []
            for title, p in (movie_profiles or {}).items():
                pid = (title or "").strip().lower()
                text = build_search_text(p)
                if text:
                    docs.append(VectorDoc(id=pid, title=title, text=text))
            if docs:
                semantic_index = EmbeddingIndex(docs)
                print(f"[semantic] rebuilt FAISS index for {len(docs)} docs")
            else:
                print("[semantic] no docs to index")
                semantic_index = None
        except Exception as e:
            print(f"[semantic] failed to rebuild index: {e}")
            semantic_index = None
            
        print(f"[api] reloaded {len(movie_profiles)} movie profiles")
        return True
    except Exception as e:
        print(f"[api] failed to reload movie data: {e}")
        return False

# -------------
# Semantic search (optional, Stage 2)
# -------------
import os
from dataclasses import dataclass
from typing import Callable

try:
    import faiss  # type: ignore
except Exception as _e:
    faiss = None  # graceful disable


def build_search_text(p: Dict[str, Any]) -> str:
    parts = [
        p.get("title") or "",
        " ".join((p.get("themes") or [])),
        " ".join((p.get("emotional_tone") or [])),
        " ".join((p.get("similar_films") or [])),
        " ".join((p.get("cultural_context") or [])),
        p.get("visual_aesthetic") or "",
        p.get("target_audience") or "",
        p.get("narrative_structure") or "",
        p.get("energy_level") or "",
        p.get("profile_text") or "",
    ]
    text = "\n".join([str(x) for x in parts if x])
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


@dataclass
class VectorDoc:
    id: str
    title: str
    text: str


class EmbeddingIndex:
    def __init__(self, docs: List[VectorDoc]):
        if faiss is None:
            raise RuntimeError("faiss not installed; pip install faiss-cpu")
        self.ids: List[str] = [d.id for d in docs]
        self.texts: List[str] = [d.text for d in docs]
        self.dim: Optional[int] = None
        self.index = None
        self.embed = self._init_embedder()
        self._build_index()

    def _init_embedder(self) -> Callable[[List[str]], List[List[float]]]:
        provider = (os.getenv("EMB_PROVIDER", "local").lower() or "local").strip()
        if provider == "openai":
            import openai  # type: ignore
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY not set for OpenAI embeddings")
            openai.api_key = api_key
            model = os.getenv("OPENAI_EMB_MODEL", "text-embedding-3-small")

            def _embed(batch: List[str]) -> List[List[float]]:
                resp = openai.embeddings.create(model=model, input=batch)
                return [d.embedding for d in resp.data]

            return _embed
        else:
            from sentence_transformers import SentenceTransformer  # type: ignore

            model_name = os.getenv("EMB_LOCAL_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            model = SentenceTransformer(model_name)

            def _embed(batch: List[str]) -> List[List[float]]:
                embs = model.encode(batch, normalize_embeddings=True, show_progress_bar=False)
                return [e.tolist() for e in embs]

            return _embed

    def _build_index(self):
        B = 256
        all_vecs: List[List[float]] = []
        for i in range(0, len(self.texts), B):
            all_vecs.extend(self.embed(self.texts[i : i + B]))
        import numpy as np  # type: ignore

        mat = np.array(all_vecs, dtype="float32")
        self.dim = int(mat.shape[1])
        self.index = faiss.IndexFlatIP(self.dim)
        self.index.add(mat)

    def search(self, query: str, k: int = 50) -> List[Tuple[str, float]]:
        if not query:
            return []
        import numpy as np  # type: ignore

        [qv] = self.embed([query])
        qv = np.array([qv], dtype="float32")
        D, I = self.index.search(qv, k)
        hits: List[Tuple[str, float]] = []
        for score, idx in zip(D[0].tolist(), I[0].tolist()):
            if idx == -1:
                continue
            hits.append((self.ids[idx], float(score)))
        return hits


semantic_index = None
try:
    docs: List[VectorDoc] = []
    for title, p in (movie_profiles or {}).items():
        pid = (title or "").strip().lower()
        text = build_search_text(p)
        if text:
            docs.append(VectorDoc(id=pid, title=title, text=text))
    if docs:
        semantic_index = EmbeddingIndex(docs)
        print(f"[semantic] built FAISS index for {len(docs)} docs")
    else:
        print("[semantic] no docs to index")
except Exception as _e:
    print(f"[semantic] disabled: {_e}")

# Create the keyword search engine from loaded profiles
search_engine = SearchEngine(movie_profiles)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=False,  # no cookies needed; using '*' is valid without credentials
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include admin router
app.include_router(admin_router)

@app.post("/reload")
async def reload_data():
    """Reload movie data from JSON files"""
    success = reload_movie_data()
    if success:
        return {"message": f"Successfully reloaded {len(movie_profiles)} movie profiles", "count": len(movie_profiles)}
    else:
        return {"error": "Failed to reload movie data"}

# Static files are served by a separate server on port 8002

# In-memory observability buffers (simple ring buffers)
RECENT_REQUESTS = deque(maxlen=500)
CLICK_EVENTS = deque(maxlen=1000)


@app.get("/health")
async def health():
    return {"status": "ok", "profiles": len(movie_profiles), "semantic_enabled": bool(semantic_index)}


def rrf_fuse(lists: List[List[Tuple[str, float]]], k: int = 60, K: float = 60.0) -> List[str]:
    from collections import defaultdict
    scores = defaultdict(float)
    for lst in lists:
        for rank, (pid, _s) in enumerate(lst, start=1):
            scores[pid] += 1.0 / (K + rank)
    return [pid for pid, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)][:k]


def keyword_retrieve(q: str, k: int) -> List[Tuple[str, float]]:
    rows = search_engine.search(q, limit=k)
    return [(r["id"], float(r.get("score") or 0.0)) for r in rows]


def vector_retrieve(q: str, k: int) -> List[Tuple[str, float]]:
    if semantic_index is None:
        return []
    return semantic_index.search(q, k=k)


@app.get("/search")
async def search(q: str, limit: int = 20, mode: str = "hybrid", k: int = 60):
    """Stage 2 search over movie profiles.
    - mode: 'keyword' | 'vector' | 'hybrid' (default)
    - k: candidate pool per retriever (hybrid)
    Returns: list of {id, title, score, snippet, badges, why, debug} and applied_filters.
    """
    intent = search_engine.parse_intent(q)
    expanded = intent.get("expanded_query") or q

    # Build a soft-expanded query for vectors (natural phrase + mood/genres, excluding overly generic 'drama')
    expanded_for_vectors = q
    if intent.get("mood_terms"):
        expanded_for_vectors = (expanded_for_vectors + " " + " ".join(intent["mood_terms"])) if expanded_for_vectors else " ".join(intent["mood_terms"])
    if intent.get("genres"):
        vg = [g for g in intent["genres"] if g != "drama"]
        if vg:
            expanded_for_vectors = (expanded_for_vectors + " " + " ".join(vg)) if expanded_for_vectors else " ".join(vg)

    # Retrieve candidates
    kw_hits = keyword_retrieve(expanded, k if mode != "vector" else limit) if mode != "vector" else []
    vec_hits = vector_retrieve(expanded_for_vectors, k if mode != "keyword" else 0) if mode != "keyword" else []

    # Precompute ranks/scores for provenance
    kw_rank = {pid: i + 1 for i, (pid, _s) in enumerate(kw_hits)}
    vec_rank = {pid: i + 1 for i, (pid, _s) in enumerate(vec_hits)}
    kw_score = {pid: float(s) for pid, s in kw_hits}
    vec_score = {pid: float(s) for pid, s in vec_hits}

    # Candidate IDs per mode
    if mode == "keyword":
        cands = [pid for pid, _ in kw_hits]
    elif mode == "vector":
        cands = [pid for pid, _ in vec_hits]
    else:
        fused = rrf_fuse([kw_hits, vec_hits], k=max(k, limit))
        cands = fused

    # Filter out hidden movies
    load_hidden_movies()
    from admin_api import admin_state
    hidden_titles = admin_state['hidden_movies']
    if hidden_titles:
        # Get movie titles for the candidate IDs and filter out hidden ones
        c = search_engine.conn.cursor()
        visible_cands = []
        for pid in cands:
            try:
                row = c.execute("SELECT title FROM movies_fts WHERE id = ?", (pid,)).fetchone()
                if row and row[0] not in hidden_titles:
                    visible_cands.append(pid)
            except Exception:
                # If we can't check the title, include it to be safe
                visible_cands.append(pid)
        cands = visible_cands

    # Build results applying filters/gates via FTS
    c = search_engine.conn.cursor()
    results: List[Dict[str, Any]] = []
    for pid in cands:
        # Exclusions
        if intent["exclude_terms"]:
            exq = " OR ".join(intent["exclude_terms"])  # simple OR
            try:
                if c.execute("SELECT 1 FROM movies_fts WHERE id=? AND movies_fts MATCH ?", (pid, exq)).fetchone():
                    continue
            except Exception:
                pass
        # Genres (ignore super-generic 'drama' for gating)
        genres_for_gate = [g for g in intent["genres"] if g != "drama"] if intent["genres"] else []
        if genres_for_gate:
            gq = " OR ".join(genres_for_gate)  # approximate
            try:
                if not c.execute("SELECT 1 FROM movies_fts WHERE id=? AND movies_fts MATCH ?", (pid, gq)).fetchone():
                    continue
            except Exception:
                pass
        # Mood gating
        if intent.get("mood_terms"):
            mq = " OR ".join(intent["mood_terms"])  # require at least one
            try:
                if not c.execute("SELECT 1 FROM movies_fts WHERE id=? AND movies_fts MATCH ?", (pid, mq)).fetchone():
                    continue
            except Exception:
                pass
        # Fetch presentation fields with MATCH so snippet highlights query terms
        try:
            row = c.execute(
                """
                SELECT title, tags,
                       snippet(movies_fts, 'text', '[', ']', ' … ', 8) AS snip_text,
                       snippet(movies_fts, 'tags', '[', ']', ' … ', 8) AS snip_tags,
                       bm25(movies_fts) AS score
                FROM movies_fts
                WHERE id = ? AND movies_fts MATCH ?
                """,
                (pid, expanded),
            ).fetchone()
        except Exception:
            row = c.execute(
                "SELECT title, tags, substr(text,1,200) AS snip_text, substr(tags,1,200) AS snip_tags, 0.0 as score FROM movies_fts WHERE id=\?",
                (pid,),
            ).fetchone()
        if not row:
            continue
        title, tags, snip_text, snip_tags, score = row
        # Prefer the snippet that actually contains a highlight; if none, do a tiny manual highlight over tags/text
        snip_source = "unknown"
        if snip_text and '[' in str(snip_text):
            snip = snip_text
            snip_source = "text"
        elif snip_tags and '[' in str(snip_tags):
            snip = snip_tags
            snip_source = "tags"
        else:
            snip = snip_text or snip_tags or ''
        if not snip or '[' not in str(snip):
            # manual fallback highlighter
            stop = {"the","a","an","for","and","or","of","movie","films","film"}
            terms = [w for w in re.findall(r"[a-z0-9]+", (q or "").lower()) if w and w not in stop]
            def _hl(s: str) -> str:
                out = s or ""
                hit = False
                for t in terms:
                    rx = re.compile(rf"\b{re.escape(t)}\b", re.IGNORECASE)
                    if rx.search(out):
                        out = rx.sub(lambda m: f"[{m.group(0)}]", out, count=1)
                        hit = True
                if not hit:
                    return ""
                return out[:220]
            # Try tags first, then text snippet
            manual_tag = _hl(tags or "")
            manual_text = _hl(snip_text or "")
            manual = manual_tag or manual_text
            if manual:
                snip = manual
                snip_source = "tags" if manual == manual_tag else "text"
        # badges from tag tokens intersecting query terms (filter stopwords/short tokens)
        stop = {
            "the","a","an","for","and","or","of","to","in","on","with","about","by","at","from","as","is","it","its","film","films","movie","movies"
        }
        q_terms_all = [w for w in re.split(r"[^a-z0-9+]+", (q or "").lower()) if w]
        q_terms = set([w for w in q_terms_all if len(w) >= 3 and w not in stop])
        # Extract alphanumeric-ish tokens from tags
        tag_tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-]+", tags or "") if tags else []
        badges: List[str] = []
        for t in tag_tokens:
            tl = t.lower()
            # also check common hyphenated forms against concatenated query tokens, e.g., coming-of-age
            hy_ok = False
            if "-" in tl:
                parts = [p for p in tl.split("-") if p]
                if all(len(p) >= 3 for p in parts) and any(p in q_terms for p in parts):
                    hy_ok = True
            if (tl in q_terms or hy_ok) and tl not in (b.lower() for b in badges) and tl not in stop and len(tl) >= 3:
                badges.append(t)
            if len(badges) >= 3:
                break
        # Build human-friendly why string with provenance
        # 1) Deduplicate badges case-insensitively and Title Case for readability
        seen_badges = set()
        pretty_badges: List[str] = []
        for b in badges:
            lb = str(b).lower()
            if lb not in seen_badges:
                seen_badges.add(lb)
                # normalize common phrases like coming-of-age
                pretty_badges.append(lb.replace("coming of age","coming-of-age").replace("coming-of-age","Coming-of-age").title().replace("-Of-","-of-").replace("-And-","-and-"))
        # 2) Clean up snippet spacing and brackets for display, collapse hyphenated highlights
        def _clean_snip(s: str) -> str:
            s = (s or "").strip()
            s = re.sub(r"\s+", " ", s)
            # collapse [coming]-of-[age] or [coming] of [age] => [coming-of-age]
            s = re.sub(r"\[([Cc]oming)\]\s*-?\s*of\s*-?\s*\[([Aa]ge)\]", r"[coming-of-age]", s)
            # remove brackets around stopwords
            s = re.sub(r"\[(?:the|a|an|of|and|or|for|to|in|on|with)\]", lambda m: m.group(0)[1:-1], s, flags=re.IGNORECASE)
            return s[:220]
        clean_snip = _clean_snip(str(snip or ""))
        # Build a prettier, more readable explanation snippet
        def _pretty_snip(s: str, source: str) -> str:
            if not s:
                return ""
            txt = s
            # remove all brackets for readability
            txt = re.sub(r"[\[\]]", "", txt)
            txt = re.sub(r"\s+", " ", txt).strip()
            if source == "tags":
                # tags are usually space-separated keywords; convert to comma-separated list
                toks = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-'&]+", txt)
                # de-duplicate preserving order
                seen = set()
                nice = []
                for t in toks:
                    tl = t.lower()
                    if tl in {"the","and","of","a","an"}:
                        continue
                    if tl not in seen:
                        seen.add(tl)
                        nice.append(t.capitalize() if t.islower() else t)
                    if len(nice) >= 12:
                        break
                txt = ", ".join(nice)
                if txt and not txt.endswith(('.', '!', '?')):
                    txt = txt + "."
                return txt
            # For text, ensure sentence case and end punctuation
            if txt and not re.search(r"[\.!?]$", txt):
                txt = txt[0:1].upper() + txt[1:]
                txt = txt + "."
            return txt
        pretty_snip = _pretty_snip(clean_snip, snip_source)
        # 3) Pull a couple of themes/moods from the underlying profile if available
        p = movie_profiles.get(title) or {}
        themes = p.get("themes") or []
        moods = p.get("emotional_tone") or []
        # prefer themes that match the query (case-insensitive, handle coming-of-age variants)
        ql = (q or "").lower()
        normalized_themes = [str(t) for t in themes]
        matched_themes = []
        for t in normalized_themes:
            tl = t.lower()
            tl = tl.replace("coming of age", "coming-of-age")
            if "coming of age" in ql or "coming-of-age" in ql:
                if "coming-of-age" in tl:
                    matched_themes.append("Coming-of-age")
                    continue
            # generic overlap by words excluding stopwords
            words = [w for w in re.findall(r"[a-z0-9]+", tl) if len(w) >= 3 and w not in stop]
            if any(w in q_terms for w in words):
                matched_themes.append(t)
        # tidy and dedupe matched themes
        mt_seen = set()
        matched_themes_clean = []
        for t in matched_themes:
            key = t.lower()
            if key not in mt_seen:
                mt_seen.add(key)
                # Title case but keep common hyphen/connectors lowercase
                tv = t.replace("coming of age","Coming-of-age").replace("coming-of-age","Coming-of-age")
                matched_themes_clean.append(tv)
        top_themes = ", ".join(matched_themes_clean[:2]) if matched_themes_clean else ", ".join(normalized_themes[:2])
        top_moods = ", ".join([str(x).capitalize() for x in moods[:2]])
        # 4) Compose explanation
        # Prefer matched themes, then badges, then moods for the topical focus
        focus = top_themes or ", ".join(pretty_badges[:3]) or top_moods
        # Build a single, natural sentence explaining why this fits the query
        base = f"{title} matches \"{q}\"" if q else f"{title} is a good fit"
        clauses = []
        if focus and top_moods:
            clauses.append(f"for its {focus.lower()} themes and {top_moods.lower()} mood")
        elif focus:
            clauses.append(f"for its {focus.lower()} themes")
        elif top_moods:
            clauses.append(f"for its {top_moods.lower()} mood")
        # Add a more specific clause naming exact matching themes/keywords when available
        def _fmt_list(xs: List[str]) -> str:
            xs = [x.strip() for x in xs if x and x.strip()]
            if not xs:
                return ""
            if len(xs) == 1:
                return f"‘{xs[0]}’"
            if len(xs) == 2:
                return f"‘{xs[0]}’ and ‘{xs[1]}’"
            return ", ".join([f"‘{x}’" for x in xs[:-1]]) + f", and ‘{xs[-1]}’"
        # Prefer themes that matched the query; otherwise fall back to badges already intersecting it
        exact_terms: List[str] = []
        if matched_themes_clean:
            exact_terms = matched_themes_clean[:2]
        elif pretty_badges:
            exact_terms = pretty_badges[:2]
        if exact_terms:
            clauses.append(f"specifically for themes like {_fmt_list(exact_terms)}")
        # Integrate snippet as an illustrative clause
        sn = (pretty_snip or "").strip().rstrip(".!? ")
        if sn:
            if snip_source == "tags":
                clauses.append(f"highlighting {sn.lower()}")
            else:
                # use as an example from text
                clauses.append(f"with moments like {sn}")
        why_sentence = base + (", " + ", ".join(clauses) if clauses else "") + "."
        # Also keep a detailed, multi-part variant for debugging/optional UI
        pieces: List[str] = []
        if focus:
            pieces.append(f"Focus: {focus}.")
        if top_moods:
            pieces.append(f"Mood: {top_moods}.")
        if pretty_snip:
            pieces.append(f"Why: {pretty_snip}")
        why_details = " ".join(pieces)
        # Present the single-sentence version as the primary pretty reason
        why_pretty = why_sentence
        # Legacy structured bits
        why_bits: List[str] = []
        if pretty_badges:
            why_bits.append(f"Badges: {', '.join(pretty_badges)}")
        if clean_snip:
            why_bits.append(f"Why: {clean_snip}")
        prov = []
        if pid in kw_rank:
            prov.append(f"kw#{kw_rank[pid]}")
        if pid in vec_rank:
            prov.append(f"vec#{vec_rank[pid]}")
        if prov:
            why_bits.append("Via: " + ", ".join(prov))

        results.append({
            "id": pid,
            "title": title,
            "score": float(score) if isinstance(score, (int, float)) else None,
            "snippet": clean_snip,
            "badges": pretty_badges,
            "why": " — ".join(why_bits),
            "why_pretty": why_pretty,
            "why_sentence": why_sentence,
            "why_details": why_details,
            "debug": {
                "via": (["keyword"] if pid in kw_rank else []) + (["vector"] if pid in vec_rank else []),
                "kw_rank": kw_rank.get(pid),
                "vec_rank": vec_rank.get(pid),
                "kw_score": kw_score.get(pid),
                "vec_score": vec_score.get(pid),
            },
        })
        if len(results) >= limit:
            break

    # Build response
    _dbg = {
        "semantic_enabled": bool(semantic_index),
        "kw_candidates": len(kw_hits) if isinstance(kw_hits, list) else 0,
        "vec_candidates": len(vec_hits) if isinstance(vec_hits, list) else 0,
    }
    # Attach a request id for observability linking
    request_id = uuid.uuid4().hex
    _dbg["request_id"] = request_id
    resp = {
        "query": q,
        "count": len(results),
        "mode": mode,
        "applied_filters": intent.get("applied_filters", {}),
        "results": results,
        "debug": _dbg,
    }
    # Record a compact event for the dashboard
    try:
        top = []
        for r in results[:3]:
            d = r.get("debug") or {}
            top.append({
                "id": r.get("id"),
                "title": r.get("title"),
                "kw_rank": d.get("kw_rank"),
                "vec_rank": d.get("vec_rank"),
                "kw_score": d.get("kw_score"),
                "vec_score": d.get("vec_score"),
                "why": r.get("why_pretty") or r.get("why") or r.get("why_sentence") or r.get("why_details"),
            })
        RECENT_REQUESTS.appendleft({
            "request_id": request_id,
            "ts": datetime.now(timezone.utc).isoformat(),
            "q": q,
            "mode": mode,
            "applied_filters": intent.get("applied_filters", {}),
            "kw_candidates": len(kw_hits) if isinstance(kw_hits, list) else 0,
            "vec_candidates": len(vec_hits) if isinstance(vec_hits, list) else 0,
            "fused_count": len(cands) if isinstance(cands, list) else None,
            "result_count": len(results),
            "top_results": top,
        })
    except Exception:
        # don't fail the request if observability buffer append fails
        pass
    return resp


@app.post("/taste-profile")
async def taste_profile(payload: Dict[str, Any]):
    """
    Expected payload:
    {
      "liked": ["Movie A", "Movie B"],
      "provider": "openai" | "anthropic" | "ollama",   # optional, default openai
      "model": "gpt-4o-mini" | "claude-3-sonnet-20240229" | ...  # optional
    }
    """
    liked = payload.get("liked") or []
    provider: str = (payload.get("provider") or "openai").strip()
    model: Optional[str] = payload.get("model")

    used, skipped = resolve_liked_movies(movie_profiles, liked)
    if not used:
        return {
            "error": "No liked titles found in dataset.",
            "used": used,
            "skipped": skipped or liked,
        }

    profile = generate_llm_taste_profile(
        movie_profiles=movie_profiles,
        liked_movies=used,
        provider=provider,
        model=model,
    )

    # Retrieve metadata for verification (falls back to request values)
    meta = {}
    if isinstance(profile, dict) and profile.get("_meta"):
        meta = profile["_meta"]
    used_provider = meta.get("provider", provider)
    used_model = meta.get("model", model)
    print(f"[taste-profile] provider={used_provider} model={used_model} liked={len(used)}")

    return {
        "used": used,
        "skipped": skipped,
        "provider": used_provider,
        "model": used_model,
        "profile": profile,
    }


# -----------------
# Observability endpoints
# -----------------
@app.get("/observability/recent")
async def observability_recent(limit: int = 100) -> Dict[str, Any]:
    """Return recent search requests and click events for the dashboard."""
    # Requests are stored newest-first in deque (left appends)
    reqs = list(RECENT_REQUESTS)[:max(1, min(1000, limit))]
    clks = list(CLICK_EVENTS)[-max(1, min(1000, limit)) :]
    return {"requests": reqs, "clicks": clks}


@app.post("/observability/click")
async def observability_click(payload: Dict[str, Any]) -> Dict[str, Any]:
    rid = (payload or {}).get("request_id")
    movie_id = (payload or {}).get("movie_id")
    position = (payload or {}).get("position")
    dwell_ms = (payload or {}).get("dwell_ms")
    CLICK_EVENTS.append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "request_id": rid,
        "movie_id": movie_id,
        "position": position,
        "dwell_ms": dwell_ms,
    })
    return {"ok": True}
