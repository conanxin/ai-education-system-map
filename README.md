# Global AI Education System Map

A static GitHub Pages site that maps the global AI-education research landscape:
papers, systems, key researchers, tech stack comparison, evolution timeline,
and a weekly auto-updated research snapshot.

**Main lineage:** SSRL → HASRL → MAI → MIRACLE → Multi-Agent Classroom OS

## Dashboard modules (v1.3)

The single-page site is organised into six modules, all driven by one
aggregated JSON file (`docs/data/dashboard-summary.json`):

1. **This Week** — week tag, new paper/system/people counts, fallback
   status, View weekly report / View on GitHub buttons.
2. **Research Lineage** — horizontal Mermaid flowchart
   (ITS → SRL/SSRL → HASRL → MAI → CocoNote → MIRACLE → Multi-Agent Classroom OS)
   with side branches (Khanmigo, AutoGen, MASS, CocoRobo SMART).
3. **System Cards** — all tracked systems as cards with badges
   (SSRL/HASRL, Multi-Agent, Classroom OS, Tutor, Product, Research
   Prototype, Infrastructure). Filter chips narrow the view client-side.
4. **Paper Network Summary** — papers grouped by lineage role
   (Theory / MAI / MIRACLE·CocoNote / Agent infrastructure /
   Evidence·policy). Click a title to open the source URL.
5. **People & Institutions** — researchers grouped by institution
   (Oulu, Stanford, CMU LearnLab, Microsoft/Google, Khan Academy,
   CocoRobo/MIRACLE, Other).
6. **Source Health** — stable sources count, sources active this run,
   source errors, fallback status, candidates-by-source dump, links to
   the registry, manifest and summary JSON.

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
  build_from_report.py         Seed parser: MVP markdown -> 6 JSON files
  build_dashboard_summary.py   Aggregator: 6 JSON files -> dashboard-summary.json
  weekly_ai_education_watch.py Weekly incremental fetcher
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

---

## Runbook

### Schedule

- Hermes cron job: **`ai-education-weekly-watch`** (job id `452055bd607a`)
- Schedule: `0 9 * * 1` (every Monday 09:00 Asia/Shanghai)
- Next run: `hermes cron list 2>&1 | grep -A 6 452055bd607a`
- Deliver: telegram (summary goes to home chat)

The cron subprocess is clean — only `HOME`, `PATH`, `TERM` are inherited.
That is by design: it matches what `env -i bash -lc` produces.

### Manual commands

Preview only (no files written):

```
python3 scripts/weekly_ai_education_watch.py \
    --data-dir docs/data \
    --reports-dir reports/weekly \
    --dry-run
```

Light-touch real run (caps per-query results, recommended for spot-checks):

```
python3 scripts/weekly_ai_education_watch.py \
    --data-dir docs/data \
    --reports-dir reports/weekly \
    --max-results 3
```

Full real run (matches cron defaults):

```
python3 scripts/weekly_ai_education_watch.py \
    --data-dir docs/data \
    --reports-dir reports/weekly
```

### Rebuild data from MVP report

When you have a fresh `reports/seed/latest-report.md`:

```
python3 scripts/build_from_report.py \
    --input reports/seed/latest-report.md \
    --data-dir docs/data \
    --weekly-dir
```

This re-parses the seed markdown tables into the 6 JSON files. It does NOT
merge with existing weekly additions — it overwrites papers/systems/people.
Re-run the weekly watcher afterwards to fold in any new items.

### Outputs after a run

| Path | What |
|---|---|
| `reports/weekly/YYYY-WW.md` | Per-week human-readable digest (append-only) |
| `docs/data/weekly/latest.json` | Snapshot for the static site ("Weekly Watch" panel) |
| `docs/data/weekly/manifest.json` | Run record: queries, candidates, after-dedup count |
| `docs/data/papers.json` | Merged (deduped) paper list |

`docs/data/systems.json` and `docs/data/people.json` are NOT mutated by the
weekly watcher yet — systems/people updates need a fresh seed (TODO v1.2).

### Logs

| Path | Source |
|---|---|
| `logs/v1_1_cron_preflight_dry_run.log` | V1.1 preflight dry-run audit |
| `logs/v1_1_manual_run.log`             | V1.1 preflight real-run audit |
| `~/.hermes/cron/output/`               | Hermes cron delivery + agent stdout (managed by Hermes) |

Local logs are gitignored. Hermes-managed cron logs persist on disk for ~30 days.

### Deploy / Pages verification

```
# Trigger GitHub Pages rebuild status read
gh api repos/conanxin/ai-education-system-map/pages

# Wait ~30-60s after push, then:
curl -sI https://conanxin.github.io/ai-education-system-map/
curl -sI https://conanxin.github.io/ai-education-system-map/data/weekly/latest.json
curl -sI https://conanxin.github.io/ai-education-system-map/data/papers.json
```

5-piece deployment check (HTTP 200 alone is not enough):
1. `HTTP/2 200`
2. `Cache-Control` header present
3. Real asset size (e.g. `papers.json` > 5 KB, `index.html` > 3 KB) — not the 4 KB placeholder
4. Second round T+~60s still 200
5. `gh api .../pages` returns `html_url` + `source: {branch: main, path: /docs}` (this can lag 10+ min — HTTP behaviour is the truth)

---

## FAQ

### 1. DDG rate-limit caused 0 new items — what now?

DuckDuckGo HTML has no API key but throttles aggressively. If a run
returns `0 candidates` even though nothing is broken, do this:

- Check `docs/data/weekly/manifest.json` — `candidates: 0` means DDG either
  blocked us or returned nothing in scope. Both are fine.
- Re-run later (`--max-results 3` is gentler).
- If you have a Parallel / Firecrawl / other search provider configured in
  Hermes, `weekly_ai_education_watch.try_hermes_search()` will pick it up
  automatically on the next run — no code change needed.

The seed is fine; 0-item weeks just produce empty audit reports and that's
correct behaviour.

### 2. How do I rebuild from a fresh `latest-report.md`?

```
cp /path/to/new/latest-report.md reports/seed/latest-report.md
python3 scripts/build_from_report.py \
    --input reports/seed/latest-report.md \
    --data-dir docs/data \
    --weekly-dir
git add docs/data reports/seed/latest-report.md
git commit -m "Rebuild from MVP report $(date -u +%FT%TZ)"
git push
```

After rebuild, re-run the weekly watcher to merge in any new items since the
last run.

### 3. How do I confirm GitHub Pages actually updated?

`gh api .../pages` has a 10+ min API cache lag — DO NOT trust it alone.
The 5-piece check above is the truth. The fastest signal is:

```
curl -sI https://conanxin.github.io/ai-education-system-map/data/weekly/latest.json | grep -i last-modified
```

If `Last-Modified` moved forward, Pages served your new content.

If HTTP returns 404 right after a push, wait 30-120 s and retry — Pages CDN
has a propagation window. If still 404 after 5 min, check `gh api .../pages`
for build errors.

### 4. How do I trigger the weekly watch manually?

```
cd /home/conanxin/projects/ai-education-system-map
python3 scripts/weekly_ai_education_watch.py \
    --data-dir docs/data \
    --reports-dir reports/weekly \
    --max-results 3
```

To commit + push the resulting JSON updates:

```
git add reports/weekly docs/data
git commit -m "manual weekly run $(date -u +%FT%TZ)"
git push
```

To trigger via Hermes scheduler with custom timing, use
`hermes cron run 452055bd607a` (runs the job once immediately). The default
schedule is preserved.

### 5. How do I refresh the dashboard summary?

`docs/data/dashboard-summary.json` is the single file the v1.3 page reads.
Refresh it whenever the underlying data changes:

```
python3 scripts/build_dashboard_summary.py --data-dir docs/data
```

The watcher does NOT regenerate it on every cron run (intentional — keeps
the cron run light). After a seed rebuild or after several weekly runs,
re-run the summary script, then commit + push:

```
git add docs/data/dashboard-summary.json
git commit -m "refresh dashboard summary"
git push
```

### 6. How do I confirm the weekly report link is reachable from the site?

The site links to `data/weekly/manifest.json` and to the latest weekly
report via `page_report_url`. After a deploy:

```
# Local
curl -sI http://127.0.0.1:8765/data/weekly/manifest.json
curl -sI http://127.0.0.1:8765/reports/weekly/2026-W27.md

# Live (replace week tag with the one from latest.json)
curl -sI https://conanxin.github.io/ai-education-system-map/data/weekly/manifest.json
curl -sI https://conanxin.github.io/ai-education-system-map/reports/weekly/2026-W27.md
```

If a new path 404s for >5 min after push, force a Pages rebuild:

```
gh api -X POST repos/conanxin/ai-education-system-map/pages/builds
```

Then wait ~90 s and re-check.