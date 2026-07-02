# Global AI Education System Map

A static GitHub Pages site that maps the global AI-education research landscape:
papers, systems, key researchers, tech stack comparison, evolution timeline,
and a weekly auto-updated research snapshot.

**Main lineage:** SSRL → HASRL → MAI → MIRACLE → Multi-Agent Classroom OS

## Structure

```
docs/
  index.html              Single-page site (Overview / Map / Papers / People / Tech / Weekly)
  assets/style.css
  assets/app.js
  data/
    papers.json           Structured paper list
    systems.json          Structured system list
    people.json           Researchers
    tech-stack.json       Comparison table
    timeline.json         Evolution timeline
    sources.json          Tracked keywords + institutions
    weekly/latest.json    Latest weekly snapshot
reports/
  seed/latest-report.md   The MVP report this site is bootstrapped from
  weekly/YYYY-WW.md       Per-week digests (append-only)
scripts/
  build_from_report.py    Seed parser: MVP markdown -> 6 JSON files
  weekly_ai_education_watch.py  Weekly incremental fetcher
logs/                     Cron output (gitignored)
```

## Quick start (local preview)

```
cd docs
python3 -m http.server 8765 --bind 127.0.0.1
# open http://127.0.0.1:8765/
```

## Rebuild from MVP report

```
python3 scripts/build_from_report.py \
    --input reports/seed/latest-report.md \
    --data-dir docs/data \
    --weekly-dir
```

## Weekly update (auto)

Runs every Monday 09:00 Asia/Shanghai via the Hermes scheduler
(`ai-education-weekly-watch`, job id stored in this repo's Hermes config).
Reads existing `docs/data/*.json`, fetches new items, dedupes by URL / title,
appends, writes `reports/weekly/YYYY-WW.md` + `docs/data/weekly/latest.json`.

Manual run:
```
python3 scripts/weekly_ai_education_watch.py \
    --data-dir docs/data \
    --reports-dir reports/weekly
```

Dry-run preview (no files written):
```
python3 scripts/weekly_ai_education_watch.py \
    --data-dir docs/data \
    --reports-dir reports/weekly \
    --dry-run
```

## Tracked scope

**Institutions** (16 query seeds):
University of Oulu Hybrid Intelligence / LEAD / MAI; Stanford HAI / Accelerator
for Learning; CMU LearnLab / Cognitive Tutor / ITS; Microsoft Research AutoGen
/ Agent Framework; Google Research MASS / multi-agent; Khan Academy Khanmigo;
CocoRobo SMART / CocoNote; MIRACLE.

**Keywords** (13): SSRL, HASRL, metacognitive AI agent, proactive speech agent,
AI education agent, multi-agent learning system, collaborative learning
environment, AI classroom OS, learning analytics, teacher-created agents,
Khanmigo evidence, AutoGen education, MASS multi-agent design.

**Filters**:
- Consumer `coconote.app` (Quizlet) is filtered out unless the result references
  CocoRobo, MIRACLE, SMART, CocoClass or multi-agent classroom research.
- Marketing listicles ("top 10 AI tools", "best of", etc.) are filtered out.

## GitHub Pages deployment

This repo publishes from `docs/` on the `main` branch. If Pages isn't enabled
yet, go to **Settings → Pages → Build and deployment → Source: Deploy from a
branch → Branch: `main` / `docs`**.

Expected URL once enabled:
`https://conanxin.github.io/ai-education-system-map/`

## Constraints honoured

- No force-push, no overwriting of remote history.
- No sudo / root writes.
- No backend, no database, no login.
- No build chain — vanilla HTML + CSS + JS, Mermaid loaded from CDN at runtime.
- Stdlib-only Python scripts (works in any Python 3.10+).