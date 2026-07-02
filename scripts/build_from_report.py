#!/usr/bin/env python3
"""
build_from_report.py

Parses the MVP markdown report (tables under #1/#2/#3) and emits 6 JSON
data files used by the static GitHub Pages site.

Input:  reports/seed/latest-report.md
Output: docs/data/{papers,systems,people,tech-stack,timeline,sources}.json
        docs/data/weekly/latest.json  (snapshot of the seed run)

Design choices:
- Pure stdlib. No third-party deps (works in hermes cron, GitHub Actions,
  bare python3 on any machine).
- Deterministic: same input -> same byte-identical JSON.
- Idempotent: re-running just overwrites the outputs.
- Defensive parsing: missing columns degrade gracefully to nulls.

Usage:
    python3 scripts/build_from_report.py \
        --input reports/seed/latest-report.md \
        --data-dir docs/data
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Table parser
# ---------------------------------------------------------------------------

def _split_md_row(line: str) -> list[str]:
    """Split a markdown table row into trimmed cells (handles leading/trailing pipes)."""
    line = line.strip()
    if not line.startswith("|"):
        return []
    parts = line.strip("|").split("|")
    return [p.strip() for p in parts]


def _is_separator(cells: list[str]) -> bool:
    """A markdown table separator row looks like ['---', '---', ...] or with :---: variants."""
    return all(re.fullmatch(r":?-{3,}:?", c) for c in cells) and len(cells) > 0


def extract_table(md: str, header_keyword: str) -> list[dict[str, str]]:
    """
    Find the first markdown table whose header row contains `header_keyword`
    in any cell. Return rows as dicts keyed by the header cells.

    Conservative: requires a 2-row header+separator pattern after the heading.
    """
    lines = md.splitlines()
    # Locate the heading line
    heading_idx = None
    for i, line in enumerate(lines):
        if re.match(rf"^##\s+.*\b{re.escape(header_keyword)}\b", line):
            heading_idx = i
            break
    if heading_idx is None:
        return []

    # Scan forward for the next table header
    i = heading_idx + 1
    while i < len(lines):
        candidate = _split_md_row(lines[i])
        if len(candidate) >= 2 and i + 1 < len(lines):
            sep = _split_md_row(lines[i + 1])
            if _is_separator(sep) and len(sep) == len(candidate):
                header = candidate
                rows: list[dict[str, str]] = []
                j = i + 2
                while j < len(lines):
                    row = _split_md_row(lines[j])
                    if not row or len(row) != len(header):
                        break
                    rows.append(dict(zip(header, row)))
                    j += 1
                return rows
        i += 1
    return []


# ---------------------------------------------------------------------------
# Field extractors
# ---------------------------------------------------------------------------

def _first_url(text: str) -> str | None:
    m = re.search(r"https?://[^\s)]+", text or "")
    return m.group(0) if m else None


def _clean(text: str) -> str:
    """Collapse multi-line summary cells, strip markdown bold/italic wrappers."""
    s = re.sub(r"\s+", " ", (text or "").strip())
    # Strip **bold** and *italic* wrappers that survive inside table cells.
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", s)
    return s


def build_papers(table: list[dict[str, str]]) -> list[dict[str, Any]]:
    out = []
    for row in table:
        # Headers from MVP: # | Title | Link | Institution | Summary (3 lines)
        title = _clean(row.get("Title", ""))
        if not title:
            continue
        link_field = _clean(row.get("Link", ""))
        institution = _clean(row.get("Institution", ""))
        summary = _clean(row.get("Summary (3 lines)", "") or row.get("Summary", ""))
        # Extract a stable id from URL or fall back to slug of title
        url = _first_url(link_field)
        pid = (url or title)[:240]
        out.append({
            "id": pid,
            "title": title,
            "url": url,
            "institution": institution,
            "summary": summary,
            "tags": [],
        })
    return out


def build_systems(table: list[dict[str, str]]) -> list[dict[str, Any]]:
    out = []
    for row in table:
        name = _clean(row.get("System", "") or row.get("Name", ""))
        if not name:
            continue
        out.append({
            "name": name,
            "type": _clean(row.get("Type", "")),
            "architecture": _clean(row.get("Architecture", "")),
            "relation": _clean(row.get("Relation to MAI / MIRACLE", "")
                                 or row.get("Relation", "")),
        })
    return out


def build_people(table: list[dict[str, str]]) -> list[dict[str, Any]]:
    out = []
    for row in table:
        name = _clean(row.get("Name", ""))
        if not name:
            continue
        out.append({
            "name": name,
            "institution": _clean(row.get("Institution", "")),
            "role": _clean(row.get("Role in AI Education", "")
                            or row.get("Role", "")),
        })
    return out


def build_tech_stack(systems: list[dict[str, Any]], papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Compose a tech-stack comparison table by attaching extra fields we can
    infer from the MVP report. We use light heuristics so the table stays
    editable later.

    For systems explicitly named, we attach canonical fields. For others we
    leave blanks.
    """
    canonical = {
        "MAI (Metacognitive AI agent)": {
            "type": "Proactive SRL agent",
            "agent_architecture": "Single agent, trigger-recognition",
            "data_inputs": "Group multimodal streams (talk, affect, log)",
            "regulation_mechanism": "HASRL trigger prompts",
            "multimodal_support": "Yes (Oulu pipeline)",
            "open_source": "Pending (paper-only)",
            "relation": "Reference implementation",
        },
        "Khanmigo": {
            "type": "LLM 1:1 tutor + teacher assistant",
            "agent_architecture": "Single-agent per student + admin agent",
            "data_inputs": "KA skill history, conversation log",
            "regulation_mechanism": "Socratic prompting + structured skill feedback",
            "multimodal_support": "Text-first",
            "open_source": "Closed",
            "relation": "Deployment-scale cousin of MAI",
        },
        "AutoGen v0.4 / Microsoft Agent Framework": {
            "type": "Multi-agent orchestration SDK",
            "agent_architecture": "Async, event-driven; group chat + manager",
            "data_inputs": "Tool calls, MCP servers, OpenAPI",
            "regulation_mechanism": "Human-in-the-loop + termination policy",
            "multimodal_support": "Pluggable via tools",
            "open_source": "Yes (MIT)",
            "relation": "Substrate for multi-agent classroom systems",
        },
        "MASS (Google)": {
            "type": "Automated MAS design framework",
            "agent_architecture": "Prompt + topology co-optimisation",
            "data_inputs": "Task benchmarks",
            "regulation_mechanism": "Search over agent prompts + topology",
            "multimodal_support": "N/A (design-time)",
            "open_source": "Paper-only",
            "relation": "Design optimiser for MIRACLE-class systems",
        },
        "SimClass (Tsinghua MAIC)": {
            "type": "Multi-agent classroom simulator",
            "agent_architecture": "Teacher + peers + manager + assistant",
            "data_inputs": "Course scripts, learner actions",
            "regulation_mechanism": "Manager agent speaker selection",
            "multimodal_support": "Text",
            "open_source": "Yes (GitHub THU-MAIC/SimClass)",
            "relation": "Simulator sibling of MIRACLE",
        },
        "CTAT / Cognitive Tutor (LearnLab)": {
            "type": "Intelligent Tutoring System author tools",
            "agent_architecture": "Example-tracing model-tracing tutors",
            "data_inputs": "Step-level student actions",
            "regulation_mechanism": "Step-by-step feedback hints",
            "multimodal_support": "Domain-specific",
            "open_source": "Yes (CTAT)",
            "relation": "Foundational ITS line; MAI adds metacognition on top",
        },
        "OLI / Torus + DataShop (CMU)": {
            "type": "Online course platform + LA warehouse",
            "agent_architecture": "Course delivery + analytics pipeline",
            "data_inputs": "Interaction logs, clickstreams",
            "regulation_mechanism": "Course-internal scaffolds",
            "multimodal_support": "Video/text/code",
            "open_source": "Mixed",
            "relation": "LA backbone MIRACLE/MAI plug into",
        },
        "CocoRobo SMART Suite": {
            "type": "AI-native classroom OS (commercial)",
            "agent_architecture": "Multi-product suite with embedded agents/workflows",
            "data_inputs": "PPT/HTML courseware, PIN co-screen, classroom streams",
            "regulation_mechanism": "Just-enough scaffolding at crucial points",
            "multimodal_support": "Yes (text, image, interactive H5)",
            "open_source": "Closed",
            "relation": "Closest Multi-Agent Classroom OS reference deployment",
        },
        "Coconote (Quizlet)": {
            "type": "AI study-tool (consumer)",
            "agent_architecture": "Single LLM pipeline",
            "data_inputs": "Audio lecture",
            "regulation_mechanism": "Generated quizzes + flashcards",
            "multimodal_support": "Audio -> text",
            "open_source": "Closed",
            "relation": "Consumer study baseline",
        },
        "MAST (Berkeley)": {
            "type": "Multi-agent failure taxonomy + traces",
            "agent_architecture": "Trace analysis benchmark",
            "data_inputs": "~200 execution traces",
            "regulation_mechanism": "Failure-mode classification",
            "multimodal_support": "N/A",
            "open_source": "Paper + dataset",
            "relation": "Failure diagnostic for multi-agent classroom systems",
        },
    }

    out = []
    for sys_row in systems:
        name = sys_row["name"]
        canon = canonical.get(name, {})
        out.append({
            "system": name,
            "institution": canon.get("institution", ""),
            "type": sys_row["type"] or canon.get("type", ""),
            "agent_architecture": canon.get("agent_architecture", ""),
            "data_inputs": canon.get("data_inputs", ""),
            "regulation_mechanism": canon.get("regulation_mechanism", ""),
            "multimodal_support": canon.get("multimodal_support", ""),
            "open_source_status": canon.get("open_source", ""),
            "relation_to_mai_miracle": sys_row["relation"] or canon.get("relation", ""),
        })
    return out


def build_timeline() -> list[dict[str, Any]]:
    """
    Hard-coded canonical evolution timeline. The MVP report's System Map
    section defined this lineage; we encode it explicitly so it survives
    markdown-format drift.
    """
    return [
        {"year": 1989, "label": "Self-Regulated Learning (Zimmerman)",
         "layer": "theory", "note": "Origin of cyclical SRL model."},
        {"year": 2018, "label": "SSRL formalised (Järvelä et al.)",
         "layer": "theory", "note": "Socially Shared Regulation of Learning framework."},
        {"year": 2023, "label": "HASRL model (Järvelä, Nguyen, Hadwin, BJET)",
         "layer": "theory",
         "note": "Hybrid human-AI shared regulation + 'trigger' concept introduced."},
        {"year": 2024, "label": "MAI proactive agent (Edwards et al., demo paper)",
         "layer": "agent",
         "note": "Oulu demo: agent raises metacognitive awareness, does not regulate FOR group."},
        {"year": 2024, "label": "CocoNote (Quizlet consumer)",
         "layer": "ecosystem",
         "note": "Consumer AI study tool baseline (1M+ downloads)."},
        {"year": 2024, "label": "SimClass (Tsinghua MAIC, NAACL 2025)",
         "layer": "ecosystem",
         "note": "Multi-agent classroom simulator with emergent group behaviours."},
        {"year": 2025, "label": "Khanmigo at scale (~700K K-12 students)",
         "layer": "deployment",
         "note": "Commercial 1:1 LLM tutor; 40K -> 700K in one school year."},
        {"year": 2025, "label": "Microsoft Agent Framework (Oct 2025)",
         "layer": "substrate",
         "note": "AutoGen + Semantic Kernel unified; MCP + A2A protocol support."},
        {"year": 2026, "label": "MASS (Google, ICLR 2026)",
         "layer": "design",
         "note": "Prompt + topology co-optimisation; debunking naive agent-counting."},
        {"year": 2026, "label": "MIRACLE multi-agent classroom system",
         "layer": "ecosystem",
         "note": "Multi-agent orchestration layer on top of MAI; simulator-validated."},
        {"year": 2026, "label": "Multi-Agent Classroom OS (live deployments)",
         "layer": "deployment",
         "note": "CocoRobo SMART (1,400+ schools), Khanmigo (>700K), OLI Torus."},
    ]


def build_sources(papers: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Aggregate sources + tracked keyword vocabulary. Sources are paper URLs.
    Keywords are the union of the brief's tracked terms plus a few we used.
    """
    keywords = [
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
        "Khanmigo evidence",
        "AutoGen education",
        "MASS multi-agent design",
    ]
    institutions = [
        "University of Oulu",
        "Stanford HAI",
        "Stanford Accelerator for Learning",
        "CMU LearnLab",
        "CMU HCII",
        "Microsoft Research",
        "Google Research",
        "Khan Academy",
        "CocoRobo",
        "Tsinghua MAIC",
        "Rutgers University",
        "East China Normal University",
        "Warsaw University of Technology",
        "Berkeley",
    ]
    return {
        "keywords": keywords,
        "institutions": institutions,
        "paper_count": len(papers),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--weekly-dir", action="store_true",
                    help="Also write docs/data/weekly/latest.json snapshot.")
    args = ap.parse_args(argv)

    md = args.input.read_text(encoding="utf-8")

    papers_table = extract_table(md, "New Papers")
    systems_table = extract_table(md, "New Systems")
    people_table = extract_table(md, "Key Researchers")

    papers = build_papers(papers_table)
    systems = build_systems(systems_table)
    people = build_people(people_table)
    tech_stack = build_tech_stack(systems, papers)
    timeline = build_timeline()
    sources = build_sources(papers)

    args.data_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "papers.json": papers,
        "systems.json": systems,
        "people.json": people,
        "tech-stack.json": tech_stack,
        "timeline.json": timeline,
        "sources.json": sources,
    }
    for name, payload in outputs.items():
        path = args.data_dir / name
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        print(f"wrote {path}  ({len(payload) if isinstance(payload, list) else 'dict'} entries)")

    # Weekly snapshot: a digest of the seed run.
    if args.weekly_dir:
        weekly_dir = args.data_dir / "weekly"
        weekly_dir.mkdir(parents=True, exist_ok=True)
        insights = []
        # Pull the insights bullets from the MVP report by section
        m = re.search(r"##\s+5\.\s+Insights(.+?)(?:\n##\s+|\Z)", md, re.DOTALL)
        if m:
            for line in m.group(1).splitlines():
                stripped = line.strip()
                if re.match(r"^\d+\.\s+", stripped):
                    insights.append(re.sub(r"^\d+\.\s+", "", stripped))
        latest = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "source_report": "reports/seed/latest-report.md",
            "new_papers": len(papers),
            "new_systems": len(systems),
            "new_people": len(people),
            "insights": insights,
            "highlights": [
                "HASRL -> MAI -> MIRACLE lineage is now self-contained",
                "MASS shows optimised single agent > naive multi-agent",
                "Microsoft Agent Framework (Oct 2025) is the orchestration substrate to target",
                "Khanmigo scale (700K) vs 35 GenAI-in-ed RCTs = deployment-evidence gap",
                "CocoRobo SMART suite is closest live Multi-Agent Classroom OS reference",
            ],
        }
        latest_path = weekly_dir / "latest.json"
        latest_path.write_text(json.dumps(latest, indent=2, ensure_ascii=False) + "\n",
                               encoding="utf-8")
        print(f"wrote {latest_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))