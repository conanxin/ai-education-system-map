#!/usr/bin/env python3
"""
weekly_ai_education_watch.py

Weekly incremental update for the AI Education System Map.

What it does:
  1. Reads the existing docs/data/{papers,systems,people}.json as the dedupe
     baseline.
  2. Runs a small set of tracked queries via the hermes_tools web_search
     helper when available, else via a duckduckgo-html fallback (no key).
  3. Adds only NEW items (URL / DOI / normalised title dedupe).
  4. Writes:
        reports/weekly/YYYY-WW.md          (human-readable digest)
        docs/data/weekly/latest.json        (snapshot for the site)
        docs/data/papers.json               (incremental update)
  5. Updates the run manifest so we can see what we did.

Usage:
    python3 scripts/weekly_ai_education_watch.py \
        --data-dir docs/data \
        --reports-dir reports/weekly \
        [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Tracked scope (matches the brief)
# ---------------------------------------------------------------------------

INSTITUTIONS = [
    "University of Oulu Hybrid Intelligence",
    "University of Oulu LEAD",
    "University of Oulu MAI",
    "Stanford HAI AI Education",
    "Stanford Accelerator for Learning",
    "CMU LearnLab Cognitive Tutor",
    "CMU LearnLab ITS",
    "Microsoft Research AutoGen",
    "Microsoft Research Agent Framework",
    "Google Research MASS",
    "Google Research multi-agent",
    "Khan Academy Khanmigo",
    "Khanmigo evidence",
    "CocoRobo SMART",
    "CocoRobo CocoNote",
    "MIRACLE multi-agent classroom",
]

KEYWORDS = [
    "socially shared regulation",
    "SSRL",
    "HASRL",
    "metacognitive AI agent",
    "proactive speech agent",
    "AI education agent",
    "multi-agent learning system",
    "collaborative learning environment",
    "AI classroom OS",
    "learning analytics",
    "teacher-created agents",
    "AutoGen education",
    "MASS multi-agent design",
]

# CocoNote disambiguation: only include results that mention CocoRobo / MIRACLE
# / SMART / multi-agent classroom. Pure "Coconote.ai the notes app" hits are
# filtered out at the result-cleaning step below.
COCONOTE_RELEVANT_TERMS = (
    "CocoRobo", "MIRACLE", "SMART", "multi-agent classroom",
    "AI-native classroom", "CocoClass",
)


# ---------------------------------------------------------------------------
# Web search backend (with graceful degradation)
# ---------------------------------------------------------------------------

def search_duckduckgo(query: str, limit: int = 5) -> list[dict[str, str]]:
    """DuckDuckGo HTML search. No API key, stdlib only.

    Returns a list of {"title", "url", "snippet"} dicts. Best-effort;
    gracefully returns empty list on any transport error.
    """
    try:
        url = "https://duckduckgo.com/html/?" + urllib.parse.urlencode({
            "q": query + " site:arxiv.org OR site:aclanthology.org OR site:openreview.net OR site:dl.acm.org OR site:ed.stanford.edu OR site:oulu.fi OR site:cmu.edu OR site:microsoft.com OR site:research.google OR site:khanacademy.org OR site:cocorobo",
            "kl": "us-en",
        })
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 HermesBot"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
    except Exception:
        return []

    results: list[dict[str, str]] = []
    # Result blocks: <a class="result__a" href="...">title</a>
    # snippet: <a class="result__snippet">...</a>
    titles = re.findall(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
    snippets = re.findall(r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
    for i, (u, t) in enumerate(titles[:limit]):
        clean_u = u
        # DuckDuckGo wraps real URLs in //duckduckgo.com/l/?...
        m = re.search(r"uddg=([^&]+)", u)
        if m:
            clean_u = urllib.parse.unquote(m.group(1))
        clean_t = re.sub(r"<[^>]+>", "", t).strip()
        sn = re.sub(r"<[^>]+>", "", snippets[i]).strip() if i < len(snippets) else ""
        results.append({"title": clean_t, "url": clean_u, "snippet": sn})
    return results


def try_hermes_search(query: str, limit: int = 5) -> list[dict[str, str]]:
    """Best-effort wrapper for hermes_tools.web_search if installed.

    hermes_tools exposes web_search(query, limit) returning a dict with
    {"data": {"web": [{"url","title","description"}, ...]}}. We don't hard-
    require it; if the import fails we just return [] and the caller will
    fall back to DuckDuckGo.
    """
    try:
        from hermes_tools import web_search  # type: ignore
    except Exception:
        return []
    try:
        out = web_search(query=query, limit=limit)
        web = (out or {}).get("data", {}).get("web", []) or []
        return [{
            "title": w.get("title", ""),
            "url": w.get("url", ""),
            "snippet": w.get("description", ""),
        } for w in web if w.get("url")]
    except Exception:
        return []


def run_query(query: str, limit: int = 5) -> list[dict[str, str]]:
    """Use hermes web_search if available, else DuckDuckGo fallback."""
    hits = try_hermes_search(query, limit=limit)
    if hits:
        return hits
    return search_duckduckgo(query, limit=limit)


# ---------------------------------------------------------------------------
# Dedup helpers
# ---------------------------------------------------------------------------

def norm_title(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", "", (t or "").lower())).strip()


def url_canon(u: str) -> str:
    if not u:
        return ""
    u = u.strip()
    # Strip trackers, force https
    u = re.sub(r"^http://", "https://", u)
    return u.split("#")[0].rstrip("/")


def load_json(p: Path) -> Any:
    if not p.exists():
        return [] if p.suffix == ".json" else {}
    return json.loads(p.read_text(encoding="utf-8"))


def save_json(p: Path, data: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

COCONOTE_RE = re.compile("|".join(re.escape(t) for t in COCONOTE_RELEVANT_TERMS), re.IGNORECASE)


def is_coconote_consumer_hit(item: dict[str, str]) -> bool:
    """Return True if this is the consumer Coconote (Quizlet) and NOT
    related to CocoRobo / MIRACLE / SMART / classroom research."""
    text = " ".join([item.get("title", ""), item.get("snippet", ""), item.get("url", "")])
    if "coconote" not in text.lower():
        return False
    # If CocoRobo / MIRACLE / SMART etc. is mentioned, keep it.
    if COCONOTE_RE.search(text):
        return False
    return True


def is_marketing_fluff(item: dict[str, str]) -> bool:
    """Heuristic: pure product / 'best of' / 'top 10' pages aren't evidence."""
    text = (item.get("title", "") + " " + item.get("snippet", "")).lower()
    fluff = [
        "top 10", "best ai", "ai tools for teachers", "review of", "comparison of",
        "buying guide", "ai for education news",
    ]
    return any(f in text for f in fluff)


def is_relevant(item: dict[str, str]) -> bool:
    if not item.get("url"):
        return False
    if is_coconote_consumer_hit(item):
        return False
    if is_marketing_fluff(item):
        return False
    return True


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def fetch_new_hits() -> list[dict[str, Any]]:
    """Run the curated set of queries, return deduplicated candidate papers."""
    seen_url: dict[str, dict[str, Any]] = {}
    queries: list[str] = []
    for inst in INSTITUTIONS:
        queries.append(f"{inst} 2025 2026")
    for kw in KEYWORDS:
        queries.append(f"{kw} 2026 paper")

    for q in queries:
        for hit in run_query(q, limit=5):
            if not is_relevant(hit):
                continue
            u = url_canon(hit["url"])
            if not u or u in seen_url:
                continue
            seen_url[u] = {
                "id": u,
                "title": hit["title"],
                "url": u,
                "institution": "",
                "summary": hit.get("snippet", ""),
                "tags": ["weekly"],
            }
    return list(seen_url.values())


def dedupe_against_existing(new_items: list[dict[str, Any]], existing: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop items whose URL or normalised title already exists."""
    existing_urls = {url_canon(it.get("url", "")) for it in existing}
    existing_titles = {norm_title(it.get("title", "")) for it in existing if it.get("title")}
    out = []
    for it in new_items:
        if it["url"] in existing_urls:
            continue
        if norm_title(it["title"]) in existing_titles:
            continue
        out.append(it)
    return out


def iso_week_tag(now: datetime) -> str:
    y, w, _ = now.isocalendar()
    return f"{y}-W{w:02d}"


def write_weekly_report(path: Path, items_added: list[dict[str, Any]], week_tag: str,
                         totals: dict[str, int]) -> None:
    lines = [
        f"# AI Education Weekly Watch — {week_tag}",
        "",
        f"_Generated: {datetime.now(timezone.utc).isoformat()}_",
        "",
        f"## Snapshot",
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
            inst = it.get("institution", "")
            snip = it.get("summary", "")
            lines.append(f"### [{t}]({u})" if u else f"### {t}")
            if inst:
                lines.append(f"_Institution:_ {inst}")
            if snip:
                lines.append("")
                lines.append(f"> {snip}")
            lines.append("")
    lines.extend([
        "## Methodology",
        "",
        "- Queries combine each tracked institution with the year (2025/2026) and",
        "  each keyword with `paper 2026` to bias toward primary sources.",
        "- Results filtered through `is_relevant()`:",
        "  - drops consumer Coconote (Quizlet) unless it references CocoRobo /",
        "    MIRACLE / SMART / multi-agent classroom / CocoClass",
        "  - drops marketing listicles (\"top 10 AI tools\", \"best of\", etc.)",
        "- Dedup against existing papers.json by canonical URL and normalised",
        "  title.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def update_latest_snapshot(weekly_path: Path, items_added: list[dict[str, Any]],
                            totals: dict[str, int], week_tag: str) -> None:
    snapshot = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "week_tag": week_tag,
        "source_report": f"reports/weekly/{week_tag}.md",
        "new_papers": len(items_added),
        "new_systems": totals.get("systems_delta", 0),
        "new_people": totals.get("people_delta", 0),
        "highlights": [it["title"] for it in items_added[:8]],
        "insights": [
            "Weekly run completed; only items passing relevance + dedup filters were appended.",
            "See the per-week markdown for the full per-item list.",
        ],
    }
    save_json(weekly_path, snapshot)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--reports-dir", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    papers_path = args.data_dir / "papers.json"
    systems_path = args.data_dir / "systems.json"
    people_path = args.data_dir / "people.json"
    latest_path = args.data_dir / "weekly" / "latest.json"

    existing_papers = load_json(papers_path)
    existing_systems = load_json(systems_path)
    existing_people = load_json(people_path)

    candidates = fetch_new_hits()
    new_items = dedupe_against_existing(candidates, existing_papers)

    week_tag = iso_week_tag(datetime.now(timezone.utc))
    weekly_report_path = args.reports_dir / f"{week_tag}.md"

    totals = {
        "papers": len(existing_papers) + len(new_items),
        "systems": len(existing_systems),
        "people": len(existing_people),
        "systems_delta": 0,
        "people_delta": 0,
    }

    if args.dry_run:
        print(f"[dry-run] {len(new_items)} new papers would be added.")
        for it in new_items[:10]:
            print(f"  + {it['title'][:80]}  ({it['url']})")
        return 0

    # Persist
    merged_papers = list(existing_papers) + new_items
    save_json(papers_path, merged_papers)
    write_weekly_report(weekly_report_path, new_items, week_tag, totals)
    update_latest_snapshot(latest_path, new_items, totals, week_tag)

    # Manifest for the cron log
    manifest = {
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "week_tag": week_tag,
        "queries_run": len(INSTITUTIONS) + len(KEYWORDS),
        "candidates": len(candidates),
        "after_dedup": len(new_items),
        "weekly_report": str(weekly_report_path),
    }
    manifest_path = args.data_dir / "weekly" / "manifest.json"
    save_json(manifest_path, manifest)

    print(f"weekly-watch complete: +{len(new_items)} papers, "
          f"report={weekly_report_path}, manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))