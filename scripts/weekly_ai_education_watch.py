#!/usr/bin/env python3
"""
weekly_ai_education_watch.py (v1.2)

Weekly incremental update for the AI Education System Map.

What changed in v1.2 (vs v1.1):
  - Reads docs/data/source-registry.json for stable sources (arxiv abs /
    official pages / people / conferences / fallback queries).
  - Fetches strategies in priority order; each strategy's failure is soft
    and recorded in source_errors so the manifest tells the truth.
  - Tracks per-source candidate counts (candidates_by_source) and a
    fallback_status flag so zero-item weeks are diagnosable, not mysterious.
  - Adds entity extraction: dedup and incremental updates to
    systems.json / people.json / tech-stack.json / timeline.json (in
    addition to papers.json).
  - Adds first_seen / last_seen / source fields to every tracked entity.
  - Tightens the noise filter to explicitly drop coconote.app consumer hits
    and unrelated AI-ed news.
  - Mirrors the per-week markdown digest into docs/reports/weekly/ so the
    file is served by GitHub Pages alongside the site itself.

Usage:
    python3 scripts/weekly_ai_education_watch.py \
        --data-dir docs/data \
        --reports-dir reports/weekly \
        [--dry-run] [--max-results 5]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PAGES_BASE = "/ai-education-system-map"

# Keywords that, if present in a candidate's text, mark it as in-scope for
# the AI-ed system map. Used as a soft pre-filter before noise rules.
IN_SCOPE_TERMS = (
    "SSRL", "HASRL", "MAI", "MIRACLE", "Khanmigo", "CocoRobo", "SMART",
    "multi-agent", "metacognitive agent", "AI classroom", "learning analytics",
    "AutoGen", "Agent Framework", "MASS", "Cognitive Tutor", "LearnLab",
    "Khan Academy", "AI education", "collaborative learning agent",
    "proactive speech agent", "teacher-created agent", "shared regulation",
)

# CocoNote disambiguation: only include "coconote" hits that ALSO mention
# CocoRobo / MIRACLE / SMART / multi-agent classroom. Pure consumer
# coconote.app notes-tool hits are filtered out.
COCONOTE_RELEVANT_TERMS = (
    "CocoRobo", "MIRACLE", "SMART", "multi-agent classroom",
    "AI-native classroom", "CocoClass",
)

# Marketing / listicle / generic-news patterns that should never enter the
# core graph.
NOISE_PATTERNS = (
    "top 10", "best ai", "ai tools for teachers", "review of", "comparison of",
    "buying guide", "ai for education news", "best of 20", "top 20",
    "newsletter", "weekly roundup", "promo code",
)

# CocoNote consumer-app host patterns.
COCONOTE_CONSUMER_HOSTS = (
    "coconote.app", "apps.apple.com/app/id6479320349", "quizlet.com/coconote",
)


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_json(p: Path) -> Any:
    if not p.exists():
        return [] if p.suffix == ".json" else {}
    return json.loads(p.read_text(encoding="utf-8"))


def save_json(p: Path, data: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def iso_week_tag(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    y, w, _ = now.isocalendar()
    return f"{y}-W{w:02d}"


# ---------------------------------------------------------------------------
# HTTP / parsing helpers
# ---------------------------------------------------------------------------

def http_get(url: str, timeout: float = 5.0) -> str | None:
    """Plain stdlib GET. Returns body string or None on transport error.
    Default timeout is intentionally tight (5s) so the registry's 50+ sources
    don't blow past cron's 5-minute ceiling."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HermesBot/1.2 (+ai-education-system-map)"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ct = r.headers.get("content-type", "")
            raw = r.read()
            # Don't try to parse binary responses.
            if "html" not in ct and "xml" not in ct and "json" not in ct and "text" not in ct and "atom" not in ct:
                return None
            return raw.decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None


def url_canon(u: str) -> str:
    if not u:
        return ""
    u = u.strip()
    u = re.sub(r"^http://", "https://", u)
    return u.split("#")[0].rstrip("/")


def norm_title(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", "", (t or "").lower())).strip()


def norm_name(t: str) -> str:
    """Looser than norm_title: keeps spaces, strips punctuation, lowercases."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", "", (t or "").lower())).strip()


# ---------------------------------------------------------------------------
# arXiv abstract page parser (Strategy 1)
# ---------------------------------------------------------------------------

def parse_arxiv_abs(html: str) -> dict[str, Any] | None:
    """Extract title + authors + abstract from a single arXiv abs page."""
    if not html:
        return None
    # Title block: <h1 class="title mathjax">...</h1>
    m_title = re.search(r'<h1[^>]*class="title[^"]*"[^>]*>(.*?)</h1>', html, re.DOTALL)
    title = re.sub(r"<[^>]+>", "", m_title.group(1)).strip() if m_title else ""
    title = re.sub(r"^Title:\s*", "", title).strip()
    # Authors block: <div class="authors">...</div>
    m_auth = re.search(r'<div[^>]*class="authors"[^>]*>(.*?)</div>', html, re.DOTALL)
    authors = re.sub(r"<[^>]+>", " ", m_auth.group(1)).strip() if m_auth else ""
    authors = re.sub(r"\s+", " ", authors)
    # Abstract block: <blockquote class="abstract mathjax">...</blockquote>
    m_abs = re.search(r'<blockquote[^>]*class="abstract[^"]*"[^>]*>(.*?)</blockquote>', html, re.DOTALL)
    abstract = re.sub(r"<[^>]+>", "", m_abs.group(1)).strip() if m_abs else ""
    abstract = re.sub(r"\s+", " ", re.sub(r"^Abstract:\s*", "", abstract))
    return {"title": title, "authors": authors, "abstract": abstract} if title else None


def fetch_arxiv_source(item: dict[str, Any]) -> list[dict[str, Any]]:
    """For an arxiv_sources item, return parsed paper dicts."""
    out: list[dict[str, Any]] = []
    url = item.get("url", "")
    if "/abs/" in url:
        html = http_get(url)
        parsed = parse_arxiv_abs(html) if html else None
        if parsed and parsed.get("title"):
            out.append({
                "id": url,
                "title": parsed["title"],
                "url": url,
                "institution": "",
                "summary": (parsed.get("abstract", "") or "")[:600],
                "tags": ["arxiv", item.get("label", "")],
                "source_id": item.get("id", ""),
                "year": _guess_year(parsed.get("abstract", "") + " " + url + " " + parsed.get("title", "")),
            })
    elif "/search/" in url:
        # arXiv search results page — pick off titles + links.
        html = http_get(url)
        if not html:
            return out
        # Each result: <li class="arxiv-result"> ... <p class="title">...</p> <a href="/abs/...">arXiv:...</a>
        for m in re.finditer(r'<li[^>]*class="arxiv-result"[^>]*>(.*?)</li>', html, re.DOTALL):
            block = m.group(1)
            m_title = re.search(r'<p[^>]*class="title"[^>]*>(.*?)</p>', block, re.DOTALL)
            m_link = re.search(r'<a[^>]+href="(/abs/[^"]+)"', block)
            m_authors = re.search(r'<p[^>]*class="authors"[^>]*>(.*?)</p>', block, re.DOTALL)
            if not (m_title and m_link):
                continue
            title = re.sub(r"<[^>]+>", "", m_title.group(1)).strip()
            link = "https://arxiv.org" + m_link.group(1)
            authors = re.sub(r"<[^>]+>", " ", m_authors.group(1)).strip() if m_authors else ""
            authors = re.sub(r"\s+", " ", re.sub(r"^Authors:\s*", "", authors))
            if title:
                out.append({
                    "id": link,
                    "title": title,
                    "url": link,
                    "institution": "",
                    "summary": authors[:300],
                    "tags": ["arxiv-search", item.get("label", "")],
                    "source_id": item.get("id", ""),
                    "year": _guess_year(title + " " + link),
                })
    return out


# ---------------------------------------------------------------------------
# Official page parser (Strategy 2)
# ---------------------------------------------------------------------------

def fetch_official_source(item: dict[str, Any]) -> list[dict[str, Any]]:
    """Light title+description extraction from an official page."""
    html = http_get(item.get("url", ""))
    if not html:
        return []
    out: list[dict[str, Any]] = []
    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL)
    if m:
        title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()
    desc = ""
    m = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', html)
    if m:
        desc = m.group(1).strip()
    if not title:
        return []
    out.append({
        "id": item.get("url", ""),
        "title": title,
        "url": item.get("url", ""),
        "institution": item.get("label", ""),
        "summary": (desc or "")[:400],
        "tags": ["official-page"],
        "source_id": item.get("id", ""),
        "year": _guess_year(title + " " + desc),
    })
    return out


# ---------------------------------------------------------------------------
# People source (Strategy 3)
# ---------------------------------------------------------------------------

def fetch_people_source(item: dict[str, Any]) -> list[dict[str, Any]]:
    """For a person in the registry, we don't fetch papers here; we just
    produce a 'confidence touch' so the watcher can update last_seen."""
    return [{
        "id": item.get("id", ""),
        "title": item.get("name", ""),
        "url": item.get("url", ""),
        "institution": item.get("institution", ""),
        "summary": f"people_source: {item.get('label', item.get('name', ''))}",
        "tags": ["person-source"],
        "source_id": item.get("id", ""),
        "year": "",
    }]


# ---------------------------------------------------------------------------
# Conference source (Strategy 3, used to mark a venue as live)
# ---------------------------------------------------------------------------

def fetch_conference_source(item: dict[str, Any]) -> list[dict[str, Any]]:
    """For a conference URL we just record a 'venue touch' for context."""
    return [{
        "id": item.get("id", ""),
        "title": item.get("label", ""),
        "url": item.get("url", ""),
        "institution": "",
        "summary": f"conference_source: {item.get('label', '')}",
        "tags": ["conference-venue"],
        "source_id": item.get("id", ""),
        "year": "",
    }]


# ---------------------------------------------------------------------------
# Search fallback (Strategy 4) — DuckDuckGo HTML, hermes_tools if available
# ---------------------------------------------------------------------------

def search_duckduckgo(query: str, limit: int = 5) -> list[dict[str, str]]:
    try:
        url = "https://duckduckgo.com/html/?" + urllib.parse.urlencode({
            "q": query,
            "kl": "us-en",
        })
        req = urllib.request.Request(url, headers={"User-Agent": "HermesBot/1.2"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
    except Exception:
        return []
    out: list[dict[str, str]] = []
    titles = re.findall(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
    snippets = re.findall(r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
    for i, (u, t) in enumerate(titles[:limit]):
        clean_u = u
        m = re.search(r"uddg=([^&]+)", u)
        if m:
            clean_u = urllib.parse.unquote(m.group(1))
        clean_t = re.sub(r"<[^>]+>", "", t).strip()
        sn = re.sub(r"<[^>]+>", "", snippets[i]).strip() if i < len(snippets) else ""
        out.append({"title": clean_t, "url": clean_u, "snippet": sn})
    return out


def try_hermes_search(query: str, limit: int = 5) -> list[dict[str, str]]:
    try:
        from hermes_tools import web_search  # type: ignore
    except Exception:
        return []
    try:
        out = web_search(query=query, limit=limit)
        web = (out or {}).get("data", {}).get("web", []) or []
        return [{"title": w.get("title", ""), "url": w.get("url", ""),
                 "snippet": w.get("description", "")} for w in web if w.get("url")]
    except Exception:
        return []


def run_query(query: str, limit: int = 5) -> list[dict[str, str]]:
    hits = try_hermes_search(query, limit=limit)
    return hits if hits else search_duckduckgo(query, limit=limit)


# ---------------------------------------------------------------------------
# Year heuristic
# ---------------------------------------------------------------------------

def _guess_year(text: str) -> str:
    m = re.search(r"\b(20[2-3]\d)\b", text or "")
    return m.group(1) if m else ""


# ---------------------------------------------------------------------------
# Noise filter
# ---------------------------------------------------------------------------

COCONOTE_CONSUMER_HOST_RE = re.compile("|".join(re.escape(h) for h in COCONOTE_CONSUMER_HOSTS), re.IGNORECASE)
COCONOTE_RELEVANT_RE = re.compile("|".join(re.escape(t) for t in COCONOTE_RELEVANT_TERMS), re.IGNORECASE)
NOISE_PATTERNS_RE = re.compile("|".join(re.escape(p) for p in NOISE_PATTERNS), re.IGNORECASE)
IN_SCOPE_RE = re.compile("|".join(re.escape(t) for t in IN_SCOPE_TERMS), re.IGNORECASE)


def looks_like_consumer_coconote(item: dict[str, Any]) -> bool:
    """True if the item is the consumer coconote.ai notes tool, not CocoRobo."""
    text = " ".join([
        str(item.get("url", "") or ""),
        str(item.get("title", "") or ""),
        str(item.get("summary", "") or ""),
    ])
    if not COCONOTE_CONSUMER_HOST_RE.search(text):
        return False
    if COCONOTE_RELEVANT_RE.search(text):
        return False
    return True


def is_noise(item: dict[str, Any]) -> bool:
    text = (str(item.get("title", "") or "") + " " + str(item.get("summary", "") or "")).lower()
    if NOISE_PATTERNS_RE.search(text):
        return True
    if looks_like_consumer_coconote(item):
        return True
    return False


def is_in_scope(item: dict[str, Any]) -> bool:
    """An item is in scope if its text hits any tracked keyword. People /
    conference / arxiv tags bypass this (they're already trusted by their
    source)."""
    if any(t in (item.get("tags") or []) for t in ("arxiv", "arxiv-search",
                                                   "official-page", "person-source",
                                                   "conference-venue")):
        return True
    text = " ".join([str(item.get("title", "") or ""), str(item.get("summary", "") or "")])
    return bool(IN_SCOPE_RE.search(text))


def is_relevant(item: dict[str, Any]) -> bool:
    if not item.get("url"):
        return False
    if is_noise(item):
        return False
    if not is_in_scope(item):
        return False
    return True


# ---------------------------------------------------------------------------
# Source-driven fetch pipeline
# ---------------------------------------------------------------------------

def fetch_from_registry(reg: dict[str, Any], max_results: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run each strategy in priority order. Returns (candidates, diagnostics)."""
    candidates: list[dict[str, Any]] = []
    diag: dict[str, Any] = {
        "source_counts": {},
        "source_errors": {},
        "candidates_by_source": {},
    }

    # Strategy 1: arXiv
    for item in reg.get("arxiv_sources", {}).get("items", []):
        try:
            hits = fetch_arxiv_source(item)
            diag["source_counts"][item["id"]] = len(hits)
            if hits:
                diag["candidates_by_source"][item["id"]] = [h["url"] for h in hits]
                candidates.extend(hits)
        except Exception as e:
            diag["source_errors"][item["id"]] = str(e)

    # Strategy 2: Official project pages
    for item in reg.get("official_project_sources", {}).get("items", []):
        try:
            hits = fetch_official_source(item)
            diag["source_counts"][item["id"]] = len(hits)
            if hits:
                diag["candidates_by_source"][item["id"]] = [h["url"] for h in hits]
                candidates.extend(hits)
        except Exception as e:
            diag["source_errors"][item["id"]] = str(e)

    # Strategy 3a: People sources (produce 1 candidate per person for entity tracking)
    for item in reg.get("people_sources", {}).get("items", []):
        try:
            hits = fetch_people_source(item)
            diag["source_counts"][item["id"]] = len(hits)
            candidates.extend(hits)
        except Exception as e:
            diag["source_errors"][item["id"]] = str(e)

    # Strategy 3b: Conference sources
    for item in reg.get("conference_sources", {}).get("items", []):
        try:
            hits = fetch_conference_source(item)
            diag["source_counts"][item["id"]] = len(hits)
            candidates.extend(hits)
        except Exception as e:
            diag["source_errors"][item["id"]] = str(e)

    # Strategy 4: Search fallback. ALWAYS run last; never let it block the manifest.
    fb = reg.get("search_fallback", {})
    fb_queries = fb.get("queries", []) if isinstance(fb, dict) else []
    fb_hits: list[dict[str, Any]] = []
    fb_status = {"ran": False, "queries": len(fb_queries), "hits": 0, "errors": []}
    for q in fb_queries:
        try:
            fb_status["ran"] = True
            r = run_query(q, limit=max_results)
            for h in r:
                hb = {
                    "id": url_canon(h.get("url", "")),
                    "title": h.get("title", ""),
                    "url": url_canon(h.get("url", "")),
                    "institution": "",
                    "summary": h.get("snippet", ""),
                    "tags": ["fallback-search"],
                    "source_id": "search_fallback",
                    "year": _guess_year(h.get("title", "") + " " + h.get("snippet", "")),
                }
                fb_hits.append(hb)
        except Exception as e:
            fb_status["errors"].append(f"{q[:40]}: {e}")
    fb_status["hits"] = len(fb_hits)
    diag["fallback_status"] = fb_status
    diag["source_counts"]["search_fallback"] = len(fb_hits)
    if fb_hits:
        diag["candidates_by_source"]["search_fallback"] = [h["url"] for h in fb_hits][:10]
    candidates.extend(fb_hits)

    # Final relevance pass
    relevant = [c for c in candidates if is_relevant(c)]
    return relevant, diag


# ---------------------------------------------------------------------------
# Entity extraction & dedup
# ---------------------------------------------------------------------------

def merge_papers(existing: list[dict[str, Any]], new_items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Update papers.json with new items. Match by canonical URL or normalized title."""
    by_url = {url_canon(p.get("url", "")): p for p in existing if p.get("url")}
    by_title = {norm_title(p.get("title", "")): p for p in existing if p.get("title")}
    added = 0
    now = now_iso()
    for it in new_items:
        u = url_canon(it.get("url", ""))
        nt = norm_title(it.get("title", ""))
        if u and u in by_url:
            by_url[u]["last_seen"] = now
            by_url[u]["summary"] = by_url[u].get("summary") or it.get("summary", "")
            continue
        if nt and nt in by_title:
            by_title[nt]["last_seen"] = now
            continue
        merged = dict(it)
        merged["first_seen"] = now
        merged["last_seen"] = now
        existing.append(merged)
        if u:
            by_url[u] = merged
        if nt:
            by_title[nt] = merged
        added += 1
    return existing, added


SYSTEM_CANON = {
    # Seeded system name -> canonical lookup name (so new mentions can be merged)
    "mai (metacognitive ai agent)": "MAI (Metacognitive AI agent)",
    "khanmigo": "Khanmigo",
    "autogen v0.4 / microsoft agent framework": "AutoGen v0.4 / Microsoft Agent Framework",
    "autogen": "AutoGen v0.4 / Microsoft Agent Framework",
    "microsoft agent framework": "AutoGen v0.4 / Microsoft Agent Framework",
    "mass (google)": "MASS (Google)",
    "mass": "MASS (Google)",
    "simclass (tsinghua maic)": "SimClass (Tsinghua MAIC)",
    "simclass": "SimClass (Tsinghua MAIC)",
    "ctat / cognitive tutor (learnlab)": "CTAT / Cognitive Tutor (LearnLab)",
    "ctat": "CTAT / Cognitive Tutor (LearnLab)",
    "cognitive tutor": "CTAT / Cognitive Tutor (LearnLab)",
    "oli / torus + datashop (cmu)": "OLI / Torus + DataShop (CMU)",
    "oli": "OLI / Torus + DataShop (CMU)",
    "cocorobo smart suite": "CocoRobo SMART Suite",
    "cocorobo smart": "CocoRobo SMART Suite",
    "cocorobo": "CocoRobo SMART Suite",
    "coconote (quizlet)": "Coconote (Quizlet)",
    "coconote": "Coconote (Quizlet)",
    "mast (berkeley, multi-agent system traces)": "MAST (Berkeley, Multi-Agent System Traces)",
    "mast": "MAST (Berkeley, Multi-Agent System Traces)",
}

SYSTEM_SYSTEM_KEYWORDS = {
    "MAI (Metacognitive AI agent)": ("MAI", "Oulu"),
    "Khanmigo": ("Khanmigo", "Khan Academy"),
    "AutoGen v0.4 / Microsoft Agent Framework": ("AutoGen", "Microsoft"),
    "MASS (Google)": ("MASS", "Google"),
    "SimClass (Tsinghua MAIC)": ("SimClass", "Tsinghua"),
    "CTAT / Cognitive Tutor (LearnLab)": ("Cognitive Tutor", "CMU"),
    "OLI / Torus + DataShop (CMU)": ("OLI", "CMU"),
    "CocoRobo SMART Suite": ("CocoRobo", "CocoRobo"),
    "Coconote (Quizlet)": ("Coconote", "Quizlet"),
    "MAST (Berkeley, Multi-Agent System Traces)": ("MAST", "Berkeley"),
}


def find_existing_system(item: dict[str, Any], existing: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Match a candidate system mention to an existing seeded entry."""
    text = " ".join([
        str(item.get("title", "") or ""),
        str(item.get("summary", "") or ""),
        str(item.get("url", "") or ""),
    ]).lower()
    # Drop consumer coconote.app noise
    if looks_like_consumer_coconote(item):
        return None
    for sys_name, (needle, inst) in SYSTEM_SYSTEM_KEYWORDS.items():
        if needle.lower() in text:
            for ex in existing:
                if ex.get("name") == sys_name:
                    return ex
            return None
    return None


def merge_systems(existing: list[dict[str, Any]], new_items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Update existing system entries' last_seen + source_url. New systems only added
    when we have HIGH confidence (e.g. an arxiv-paper-style title or a clear
    institutional source); for the watcher pass we mostly touch existing."""
    now = now_iso()
    updated = 0
    for it in new_items:
        match = find_existing_system(it, existing)
        if not match:
            continue
        match["last_seen"] = now
        if it.get("url") and not match.get("source_url"):
            match["source_url"] = it["url"]
        match["first_seen"] = match.get("first_seen") or now
        updated += 1
    return existing, updated


def find_existing_person(item: dict[str, Any], existing: list[dict[str, Any]]) -> dict[str, Any] | None:
    name_norm = norm_name(item.get("title", ""))
    if not name_norm:
        return None
    for ex in existing:
        if norm_name(ex.get("name", "")) == name_norm:
            return ex
    # fuzzy: try the people_sources seed
    return None


def merge_people(existing: list[dict[str, Any]], new_items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    now = now_iso()
    updated = 0
    for it in new_items:
        m = find_existing_person(it, existing)
        if not m:
            continue
        m["last_seen"] = now
        if it.get("url") and not m.get("source_url"):
            m["source_url"] = it["url"]
        m["first_seen"] = m.get("first_seen") or now
        updated += 1
    return existing, updated


def merge_tech_stack(existing: list[dict[str, Any]], new_items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Touch last_updated for tech-stack rows whose system was confirmed in
    the same run."""
    now = now_iso()
    updated = 0
    matched_systems = set()
    for it in new_items:
        m = find_existing_system(it, existing)
        if m and m.get("system"):
            matched_systems.add(m["system"])
    for row in existing:
        if row.get("system") in matched_systems:
            row["last_updated"] = now
            updated += 1
    return existing, updated


def maybe_extend_timeline(existing: list[dict[str, Any]], new_items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Only extend timeline when a candidate is unambiguously a *new* evolution
    node (e.g. arxiv abs with explicit year >= 2026 AND a clear lineage label).
    The watcher pass is conservative: we mark the highest year we saw this run
    but do not invent events."""
    years = set()
    for it in new_items:
        y = it.get("year") or ""
        if y.isdigit() and 2024 <= int(y) <= 2030:
            years.add(int(y))
    if not years:
        return existing, 0
    # No-op: a timeline extension requires a manual review (v1.3).
    # Return the existing list unchanged so the contract is honest.
    return existing, 0


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_weekly_report(path: Path, items_added: list[dict[str, Any]], week_tag: str,
                        totals: dict[str, int], diag: dict[str, Any]) -> None:
    lines = [
        f"# AI Education Weekly Watch — {week_tag}",
        "",
        f"_Generated: {now_iso()}_",
        "",
        "## Snapshot",
        "",
        f"- New papers added this run: **{len(items_added)}**",
        f"- Total papers tracked: **{totals['papers']}**",
        f"- Total systems tracked: **{totals['systems']}**",
        f"- Total people tracked: **{totals['people']}**",
        "",
        "## New items",
        "",
    ]
    if not items_added:
        lines.append("_No new items found this run._")
    else:
        for it in items_added[:50]:
            t = it.get("title", "(untitled)")
            u = it.get("url", "")
            src = it.get("source_id", "")
            lines.append(f"### [{t}]({u})" if u else f"### {t}")
            if src:
                lines.append(f"_Source:_ `{src}`")
            if it.get("institution"):
                lines.append(f"_Institution:_ {it['institution']}")
            if it.get("summary"):
                lines.append("")
                lines.append(f"> {it['summary'][:400]}")
            lines.append("")
    lines.append("## Source diagnostics")
    lines.append("")
    sc = diag.get("source_counts", {})
    lines.append(f"- Total source hits: **{sum(sc.values())}**")
    if sc:
        for k, v in list(sc.items())[:30]:
            lines.append(f"  - `{k}`: {v}")
    fb = diag.get("fallback_status", {})
    if fb:
        lines.append("")
        lines.append(f"- Fallback ran: **{fb.get('ran')}** · queries: {fb.get('queries')} · hits: {fb.get('hits')}")
        if fb.get("errors"):
            lines.append(f"- Fallback errors: {len(fb['errors'])}")
    se = diag.get("source_errors", {})
    if se:
        lines.append("")
        lines.append(f"- Source errors: {len(se)}")
        for k, v in list(se.items())[:10]:
            lines.append(f"  - `{k}`: {v}")
    lines.extend([
        "",
        "## Methodology",
        "",
        "- Source registry at `docs/data/source-registry.json` is read first;",
        "  strategies run in priority order (arxiv > official > people/conference",
        "  > search fallback). Each source failure is soft-logged.",
        "- Candidate filter: drops coconote.app consumer hits, marketing listicles,",
        "  and items lacking any tracked keyword (SSRL / MAI / MIRACLE / etc.).",
        "- Dedup: papers by URL or normalised title; systems and people by",
        "  canonical name. Existing entries get `last_seen` refreshed.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def update_latest_snapshot(weekly_path: Path, items_added: list[dict[str, Any]],
                            totals: dict[str, int], week_tag: str,
                            diag: dict[str, Any]) -> None:
    snapshot = {
        "updated_at": now_iso(),
        "week_tag": week_tag,
        "source_report": f"reports/weekly/{week_tag}.md",
        "github_report_path": f"reports/weekly/{week_tag}.md",
        "page_report_url": f"{PAGES_BASE}/reports/weekly/{week_tag}.md",
        "new_papers": len(items_added),
        "new_systems": totals.get("systems_updated", 0),
        "new_people": totals.get("people_updated", 0),
        "tech_stack_updated": totals.get("tech_stack_updated", 0),
        "fallback_status": diag.get("fallback_status", {}),
        "source_counts": diag.get("source_counts", {}),
        "candidates_by_source": diag.get("candidates_by_source", {}),
        "entity_changes": {
            "papers_added": len(items_added),
            "systems_updated": totals.get("systems_updated", 0),
            "people_updated": totals.get("people_updated", 0),
            "tech_stack_updated": totals.get("tech_stack_updated", 0),
            "timeline_extended": totals.get("timeline_extended", 0),
        },
        "highlights": [it["title"] for it in items_added[:8]],
        "insights": [
            "Weekly run completed; only items passing relevance + dedup filters were appended.",
            "See the per-week markdown for the full per-item list.",
            f"Source registry used: v{doc_registry_version()}",
        ],
    }
    save_json(weekly_path, snapshot)


def doc_registry_version() -> str:
    try:
        reg = load_json(Path("docs/data/source-registry.json"))
        return str(reg.get("version", "?"))
    except Exception:
        return "?"


def write_manifest(manifest_path: Path, week_tag: str, items_added: list[dict[str, Any]],
                    diag: dict[str, Any], totals: dict[str, int]) -> None:
    manifest = {
        "ran_at": now_iso(),
        "week_tag": week_tag,
        "registry_version": doc_registry_version(),
        "source_counts": diag.get("source_counts", {}),
        "source_errors": diag.get("source_errors", {}),
        "fallback_status": diag.get("fallback_status", {}),
        "candidates_by_source": diag.get("candidates_by_source", {}),
        "entity_changes": {
            "papers_added": len(items_added),
            "systems_updated": totals.get("systems_updated", 0),
            "people_updated": totals.get("people_updated", 0),
            "tech_stack_updated": totals.get("tech_stack_updated", 0),
            "timeline_extended": totals.get("timeline_extended", 0),
        },
        "weekly_report": f"reports/weekly/{week_tag}.md",
        # Dashboard summary rebuild fields are filled in by main() AFTER the
        # rebuild runs. Initial values here are placeholders.
        "dashboard_summary_rebuilt": False,
        "dashboard_summary_path": "docs/data/dashboard-summary.json",
        "dashboard_summary_updated_at": "",
        "dashboard_summary_error": None,
        # Auto-publish fields are filled in by main() AFTER git_publish runs.
        # Initial values here are placeholders.
        "publish_requested": False,
        "publish_status": "skipped",
        "publish_commit": None,
        "publish_error": None,
        "pages_expected_to_rebuild": False,
    }
    save_json(manifest_path, manifest)


def rebuild_dashboard_summary(project_root: Path, data_dir: Path) -> tuple[bool, str, str | None]:
    """Run scripts/build_dashboard_summary.py against `data_dir` and capture
    the resulting dashboard-summary.json's updated_at.

    Returns: (rebuilt, updated_at_iso, error_message_or_None).

    Built as a subprocess so the watcher's stdout stays clean and the
    builder's CLI contract is unchanged.
    """
    import subprocess
    builder = project_root / "scripts" / "build_dashboard_summary.py"
    summary_path = data_dir / "dashboard-summary.json"
    if not builder.exists():
        return False, "", f"builder not found: {builder}"
    try:
        result = subprocess.run(
            ["python3", str(builder), "--data-dir", str(data_dir)],
            capture_output=True, text=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        return False, "", "build_dashboard_summary timed out after 60s"
    except Exception as e:
        return False, "", f"subprocess failed: {e}"
    if result.returncode != 0:
        return False, "", f"exit {result.returncode}: {result.stderr.strip()[:400] or result.stdout.strip()[:400]}"
    # Pull updated_at out of the freshly-written summary.
    try:
        s = json.loads(summary_path.read_text(encoding="utf-8"))
        return True, str(s.get("generated_at", "")), None
    except Exception as e:
        return True, "", f"summary written but could not parse generated_at: {e}"


def patch_manifest_with_summary_result(manifest_path: Path, rebuilt: bool,
                                        updated_at: str, error: str | None) -> None:
    """Update the manifest in place with the dashboard-summary rebuild outcome."""
    if not manifest_path.exists():
        return
    try:
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return
    m["dashboard_summary_rebuilt"] = rebuilt
    m["dashboard_summary_updated_at"] = updated_at
    m["dashboard_summary_error"] = error
    save_json(manifest_path, m)


def _patch_manifest_with_publish_result(manifest_path: Path, publish_requested: bool,
                                        status: str, commit_sha: str | None,
                                        error: str | None,
                                        pages_expected: bool) -> None:
    """Update the manifest in place with the auto-publish outcome."""
    if not manifest_path.exists():
        return
    try:
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return
    m["publish_requested"] = publish_requested
    m["publish_status"] = status
    m["publish_commit"] = commit_sha
    m["publish_error"] = error
    m["pages_expected_to_rebuild"] = pages_expected
    save_json(manifest_path, m)


def mirror_report_into_pages(src: Path, docs_reports_dir: Path) -> Path | None:
    """Copy the weekly markdown into docs/reports/weekly/ so it's served
    by GitHub Pages alongside the rest of the site."""
    if not src.exists():
        return None
    docs_reports_dir.mkdir(parents=True, exist_ok=True)
    dest = docs_reports_dir / src.name
    shutil.copyfile(src, dest)
    return dest


# ---------------------------------------------------------------------------
# Auto-publish helper (V1.3.2)
# ---------------------------------------------------------------------------

_PUBLISH_PATHS = [
    "docs/data",
    "docs/reports",
    "reports/weekly",
    "README.md",
]


def git_publish(project_root: Path, week_tag: str) -> tuple[str, str | None, str | None]:
    """Stage a curated set of paths, commit if anything changed, push to origin/main.

    Returns a tuple of (status, commit_sha, error_message) where status is one of:
      - "no_changes" — working tree was already clean against HEAD
      - "committed"  — a new commit was created and pushed
      - "failed"     — git errored at any step; commit_sha is None
    """
    try:
        # Short-circuit: any tracked-or-untracked edits at all?
        porcelain = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root, capture_output=True, text=True, check=True,
        ).stdout.strip()
        if not porcelain:
            print("[publish] no changes to publish", flush=True)
            return ("no_changes", None, None)

        # Stage only the curated paths so logs/ and stray files never leak.
        for rel in _PUBLISH_PATHS:
            subprocess.run(
                ["git", "add", "--", rel],
                cwd=project_root, capture_output=True, text=True, check=True,
            )

        # If after staging the index is empty (e.g. edits were outside the
        # curated paths), treat as no_changes rather than an empty commit.
        staged = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=project_root, capture_output=True, text=True, check=True,
        ).stdout.strip()
        if not staged:
            print("[publish] no curated-path changes to publish", flush=True)
            return ("no_changes", None, None)

        commit_msg = f"Update AI education weekly watch {week_tag}"
        sha = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=project_root, capture_output=True, text=True, check=True,
        ).stdout.strip()
        # `git commit` doesn't print the SHA by default; derive from rev-parse.
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root, capture_output=True, text=True, check=True,
        ).stdout.strip()

        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=project_root, capture_output=True, text=True, check=True,
        )
        print(f"[publish] committed {sha[:7]}: {commit_msg}", flush=True)
        return ("committed", sha, None)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip() if hasattr(exc, "stderr") else ""
        return ("failed", None, stderr or str(exc))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--reports-dir", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-results", type=int, default=5)
    ap.add_argument("--publish", action="store_true",
                    help="Auto git add/commit/push changed docs/data and docs/reports "
                         "after the weekly watch. Dry-run ignores this flag.")
    args = ap.parse_args(argv)

    papers_path = args.data_dir / "papers.json"
    systems_path = args.data_dir / "systems.json"
    people_path = args.data_dir / "people.json"
    tech_path = args.data_dir / "tech-stack.json"
    timeline_path = args.data_dir / "timeline.json"
    latest_path = args.data_dir / "weekly" / "latest.json"
    manifest_path = args.data_dir / "weekly" / "manifest.json"
    registry_path = args.data_dir / "source-registry.json"

    papers = load_json(papers_path)
    systems = load_json(systems_path)
    people = load_json(people_path)
    tech_stack = load_json(tech_path)
    timeline = load_json(timeline_path)

    registry = load_json(registry_path)
    if not isinstance(registry, dict):
        print(f"ERROR: registry at {registry_path} not a dict; aborting.")
        return 1

    candidates, diag = fetch_from_registry(registry, args.max_results)

    week_tag = iso_week_tag()
    weekly_report_path = args.reports_dir / f"{week_tag}.md"

    papers, papers_added = merge_papers(papers, candidates)
    systems, systems_updated = merge_systems(systems, candidates)
    people, people_updated = merge_people(people, candidates)
    tech_stack, tech_updated = merge_tech_stack(tech_stack, candidates)
    timeline, timeline_extended = maybe_extend_timeline(timeline, candidates)

    totals = {
        "papers": len(papers),
        "systems": len(systems),
        "people": len(people),
        "systems_updated": systems_updated,
        "people_updated": people_updated,
        "tech_stack_updated": tech_updated,
        "timeline_extended": timeline_extended,
    }

    if args.dry_run:
        print(f"[dry-run] {papers_added} new papers; "
              f"{systems_updated} systems updated; "
              f"{people_updated} people updated; "
              f"{tech_updated} tech-stack rows touched.")
        print("[dry-run] (real run will rebuild dashboard-summary.json after this)")
        return 0

    # Persist
    save_json(papers_path, papers)
    save_json(systems_path, systems)
    save_json(people_path, people)
    save_json(tech_path, tech_stack)
    save_json(timeline_path, timeline)

    write_weekly_report(weekly_report_path, candidates, week_tag, totals, diag)
    update_latest_snapshot(latest_path, candidates, totals, week_tag, diag)
    write_manifest(manifest_path, week_tag, candidates, diag, totals)

    # Mirror the per-week MD into docs/reports/weekly/ so it's Pages-served.
    docs_reports_weekly = args.data_dir.parent / "reports" / "weekly"
    mirror_report_into_pages(weekly_report_path, docs_reports_weekly)

    # Auto-rebuild dashboard-summary.json so the static page sees fresh
    # numbers on the next deploy. Runs even when entity_changes are all 0
    # because latest.updated_at / source health can still shift.
    # data_dir is e.g. docs/data; project root is one more level up.
    project_root = args.data_dir.parent.parent
    rebuilt, summary_updated_at, summary_error = rebuild_dashboard_summary(
        project_root, args.data_dir
    )
    patch_manifest_with_summary_result(manifest_path, rebuilt, summary_updated_at, summary_error)

    # Auto-publish (V1.3.2): stage curated docs/data + reports paths, commit
    # only if there's something new, and push to origin/main. Dry-run never
    # publishes. Failure surfaces in the manifest and exits 1.
    publish_status = "skipped"
    publish_commit = None
    publish_error = None
    pages_expected = False
    if args.dry_run:
        print("[dry-run] real run with --publish will auto-commit and "
              "git push origin main when curated paths change", flush=True)
    elif args.publish:
        # Pre-write the manifest with a "pending" sentinel so the upcoming
        # commit carries it; we'll patch in the real SHA afterwards.
        _patch_manifest_with_publish_result(
            manifest_path, True, "pending", None, None, False,
        )
        publish_status, publish_commit, publish_error = git_publish(project_root, week_tag)
        pages_expected = publish_status == "committed"
        # Re-patch the manifest on disk with the actual outcome.
        _patch_manifest_with_publish_result(
            manifest_path, True, publish_status, publish_commit,
            publish_error, pages_expected,
        )
        # If we got a real commit SHA AND the manifest now differs from the
        # last-pushed version, do a tiny follow-up commit so the live record
        # carries the real SHA. Avoids --amend + force-with-lease.
        if publish_status == "committed" and publish_commit:
            try:
                subprocess.run(
                    ["git", "add", "--", "docs/data/weekly/manifest.json"],
                    cwd=project_root, capture_output=True, text=True, check=True,
                )
                staged_check = subprocess.run(
                    ["git", "diff", "--cached", "--name-only"],
                    cwd=project_root, capture_output=True, text=True, check=True,
                ).stdout.strip()
                if staged_check:
                    amend_msg = (
                        f"Record publish commit {publish_commit[:7]} in manifest "
                        f"({week_tag})"
                    )
                    subprocess.run(
                        ["git", "commit", "-m", amend_msg],
                        cwd=project_root, capture_output=True, text=True, check=True,
                    )
                    subprocess.run(
                        ["git", "push", "origin", "main"],
                        cwd=project_root, capture_output=True, text=True, check=True,
                    )
            except subprocess.CalledProcessError as exc:
                print(f"[publish] follow-up commit failed (non-fatal): {exc}", file=sys.stderr)

    print(f"weekly-watch complete: +{papers_added} papers, "
          f"~{systems_updated} systems, ~{people_updated} people, "
          f"~{tech_updated} tech-stack; "
          f"report={weekly_report_path}, manifest={manifest_path}, "
          f"dashboard_summary={'rebuilt' if rebuilt else 'FAILED'}, "
          f"publish={publish_status}")
    if not rebuilt:
        print(f"ERROR: dashboard summary build failed: {summary_error}", file=sys.stderr)
        return 1
    if publish_status == "failed":
        print(f"ERROR: auto-publish failed: {publish_error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))