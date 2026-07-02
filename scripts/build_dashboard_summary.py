#!/usr/bin/env python3
"""
build_dashboard_summary.py

Reads the existing JSON data files and emits docs/data/dashboard-summary.json
— a single aggregated object the static dashboard consumes so it doesn't have
to fan out 7 fetches + compute totals itself.

Inputs (all under --data-dir):
  papers.json, systems.json, people.json,
  source-registry.json, weekly/latest.json, weekly/manifest.json

Output:
  dashboard-summary.json

Usage:
    python3 scripts/build_dashboard_summary.py --data-dir docs/data
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(p: Path, default: Any = None) -> Any:
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def safe_get(d: dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def extract_year(s: str) -> str:
    m = re.search(r"\b(20[2-3]\d)\b", s or "")
    return m.group(1) if m else ""


def classify_paper(p: dict[str, Any]) -> str:
    """Coarse paper-group classifier — used for the Paper Network Summary."""
    text = " ".join([
        str(p.get("title", "") or ""),
        str(p.get("summary", "") or ""),
        str(p.get("institution", "") or ""),
    ]).lower()
    tags = " ".join(p.get("tags") or []).lower()
    src_id = str(p.get("source_id", "") or "").lower()
    blob = text + " " + tags + " " + src_id
    # Order matters — first match wins.
    if any(k in blob for k in ("jarvel", "hasrl", "ssrl", "trigger", "metacognitive")):
        return "MAI lineage papers"
    if any(k in blob for k in ("miracle", "cocorobo", "smart", "coconote")):
        return "MIRACLE / CocoNote papers"
    if any(k in blob for k in ("autogen", "mass", "agent framework", "simclass", "agentic orchestration")):
        return "Agent infrastructure papers"
    if any(k in blob for k in ("rfi", "rct", "policy", "evidence", "stanford hai", "khanmigo")):
        return "Evidence / policy papers"
    return "Theory papers"


def classify_person_group(p: dict[str, Any]) -> str:
    inst = (p.get("institution", "") or "").lower()
    role = (p.get("role", "") or "").lower()
    blob = inst + " " + role
    if "oulu" in blob or "let" in blob or "hybrid intelligence" in blob or "cella" in blob:
        return "Oulu / LET / HI"
    if "cocorobo" in blob or "miracle" in blob or "smart" in blob:
        return "CocoRobo / MIRACLE"
    if "stanford" in blob or "hai" in blob:
        return "Stanford"
    if "cmu" in blob or "carnegie" in blob or "learnlab" in blob:
        return "CMU LearnLab"
    if "khan" in blob:
        return "Khan Academy"
    if "microsoft" in blob or "google" in blob:
        return "Microsoft / Google"
    if "tsinghua" in blob or "rutgers" in blob or "ecnu" in blob or "warsaw" in blob:
        return "Other research"
    return "Other research"


def classify_system_card(s: dict[str, Any]) -> list[str]:
    """Return list of category tags for the System Cards filter.

    Naming overrides come first (so e.g. Coconote doesn't get tagged
    Multi-Agent by accident).
    """
    name = (s.get("name", "") or "").lower()
    typ = (s.get("type", "") or "").lower()
    rel = (s.get("relation", "") or "").lower()
    arch = (s.get("agent_architecture", "") or "").lower()
    out: list[str] = []

    # --- Name overrides first ---
    if "coconote" in name and "quizlet" in name:
        return ["Product"]  # consumer study baseline; never classify as classroom
    if name == "olli / torus + datashop (cmu)" or "oli / torus" in name or name.startswith("oli"):
        return ["Infrastructure"]
    if name.startswith("mai"):
        return ["SSRL / HASRL", "Research Prototype"]
    if name.startswith("khanmigo"):
        return ["Tutor", "Product"]
    if "cocorobo" in name:
        return ["Multi-Agent", "Classroom OS", "Product"]
    if "autogen" in name or "agent framework" in name:
        return ["Infrastructure", "Multi-Agent"]
    if name.startswith("mass"):
        return ["Infrastructure"]
    if "simclass" in name:
        return ["Multi-Agent", "Research Prototype"]
    if "ctat" in name or "cognitive tutor" in name:
        return ["Tutor", "Infrastructure"]
    if "mast" in name:
        return ["Research Prototype"]

    # --- Fallback heuristic for new systems the override doesn't know ---
    blob = name + " " + typ + " " + rel + " " + arch
    if "tutor" in typ or "ai tutor" in blob:
        out.append("Tutor")
    if "autogen" in blob or "agent framework" in blob or "datashop" in blob:
        out.append("Infrastructure")
    if "multi-agent" in blob:
        out.append("Multi-Agent")
    if "classroom os" in blob:
        out.append("Classroom OS")
    if "research prototype" in typ:
        out.append("Research Prototype")
    if "product" in typ or "consumer" in typ:
        out.append("Product")
    if "hasrl" in blob or "metacognitive" in blob:
        out.append("SSRL / HASRL")
    return out or ["Other"]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    args = ap.parse_args(argv)

    dd = args.data_dir
    papers = load_json(dd / "papers.json", default=[])
    systems = load_json(dd / "systems.json", default=[])
    people = load_json(dd / "people.json", default=[])
    registry = load_json(dd / "source-registry.json", default={})
    latest = load_json(dd / "weekly" / "latest.json", default={})
    manifest = load_json(dd / "weekly" / "manifest.json", default={})

    # Source counts
    stable_count = 0
    for k, v in (registry or {}).items():
        if isinstance(v, dict) and "items" in v:
            stable_count += len(v["items"])
        elif isinstance(v, dict) and "queries" in v:
            stable_count += len(v["queries"])

    source_counts = safe_get(manifest, "source_counts", default={}) or {}
    active_sources = sum(1 for v in source_counts.values() if isinstance(v, int) and v > 0)
    source_errors = safe_get(manifest, "source_errors", default={}) or {}
    candidates_by_source = safe_get(manifest, "candidates_by_source", default={}) or {}
    fallback_status = safe_get(manifest, "fallback_status", default={}) or {}

    # Paper groups
    paper_groups: dict[str, list[dict[str, Any]]] = {}
    for p in papers:
        if not isinstance(p, dict):
            continue
        g = classify_paper(p)
        paper_groups.setdefault(g, []).append({
            "title": p.get("title", ""),
            "year": p.get("year", "") or extract_year(p.get("summary", "") + " " + p.get("url", "")),
            "url": p.get("url", ""),
            "related_system": (p.get("tags") or [""])[0] if p.get("tags") else "",
            "tags": p.get("tags") or [],
        })

    # People groups
    people_groups: dict[str, list[dict[str, Any]]] = {}
    for person in people:
        if not isinstance(person, dict):
            continue
        g = classify_person_group(person)
        people_groups.setdefault(g, []).append({
            "name": person.get("name", ""),
            "institution": person.get("institution", ""),
            "role": person.get("role", ""),
            "related_projects": [],
            "source_url": person.get("source_url", ""),
        })

    # System cards (flatten tech-stack + systems rows so the dashboard has a
    # single normalized view)
    sys_cards: list[dict[str, Any]] = []
    for s in systems:
        if not isinstance(s, dict):
            continue
        # Enrich from tech-stack.json where fields are richer
        sys_name = s.get("name", "")
        ts_row = next((t for t in (load_json(dd / "tech-stack.json", default=[]) or [])
                       if isinstance(t, dict) and t.get("system") == sys_name), None)
        sys_cards.append({
            "system": sys_name,
            "institution": (ts_row or {}).get("institution", ""),
            "type": s.get("type", (ts_row or {}).get("type", "")),
            "relation_to_mai_miracle": s.get("relation", (ts_row or {}).get("relation_to_mai_miracle", "")),
            "agent_architecture": (ts_row or {}).get("agent_architecture", ""),
            "open_source_status": (ts_row or {}).get("open_source_status", ""),
            "source_url": s.get("source_url", ""),
            "categories": classify_system_card(s),
        })

    # Timeline (pass through)
    timeline = load_json(dd / "timeline.json", default=[]) or []

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "last_updated": safe_get(latest, "updated_at", default=""),
        "latest_week_tag": safe_get(latest, "week_tag", default=""),
        "latest_report_url": safe_get(latest, "page_report_url", default=""),
        "github_report_path": safe_get(latest, "github_report_path", default=""),
        "totals": {
            "papers": len(papers),
            "systems": len(systems),
            "people": len(people),
            "timeline_events": len(timeline),
            "stable_sources": stable_count,
            "active_sources": active_sources,
        },
        "this_week": {
            "new_papers": safe_get(latest, "new_papers", default=0),
            "new_systems": safe_get(latest, "new_systems", default=0),
            "new_people": safe_get(latest, "new_people", default=0),
            "fallback_status": fallback_status,
        },
        "source_health": {
            "stable_sources": stable_count,
            "active_sources": active_sources,
            "source_errors_count": len(source_errors),
            "source_errors": source_errors,
            "fallback_status": fallback_status,
            "candidates_by_source": candidates_by_source,
            "source_counts": source_counts,
            "last_run": safe_get(manifest, "ran_at", default=""),
            "registry_version": safe_get(manifest, "registry_version", default=""),
        },
        "system_cards": sys_cards,
        "paper_groups": paper_groups,
        "people_groups": people_groups,
        "timeline": timeline,
    }

    out = dd / "dashboard-summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out}  (papers={len(papers)} systems={len(systems)} people={len(people)} "
          f"stable_sources={stable_count} active={active_sources} "
          f"paper_groups={len(paper_groups)} people_groups={len(people_groups)})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))