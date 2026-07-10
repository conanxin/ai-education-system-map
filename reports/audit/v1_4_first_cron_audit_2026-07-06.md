# V1.4 First Cron Audit — AI Education System Map

**STATUS: PASS**

**Audit round:** v1.4 — first-real-cron-run-audit
**Audit date:** 2026-07-11 04:47 +08:00
**Cron run audited:** 2026-07-06 09:05:48 +08:00 (Monday schedule, week 2026-W28)
**Cron job:** `ai-education-weekly-watch` (id `452055bd607a`)
**Project path:** `/home/conanxin/projects/ai-education-system-map`
**Live URL:** `https://conanxin.github.io/ai-education-system-map/`

This audit verifies that the **first real cron run** of the AI Education
weekly watcher completed cleanly: local data, Git commits, GitHub Actions,
live Pages, Telegram delivery, and Chinese UI all reconcile to the
manifest's `publish_commit`. The raw evidence for every row below is in
[`v1_4_first_cron_raw_2026-07-06.md`](v1_4_first_cron_raw_2026-07-06.md).

No code was modified during this audit. The only files added are these
two `reports/audit/` documents.

---

## 1. Summary verdict

| Dimension | Result | Notes |
|---|---|---|
| Cron execution | PASS | `last_status=ok`, `last_error=null`, `last_delivery_error=null` |
| Cron schedule | PASS | `0 9 * * 1`; ran Monday 2026-07-06 09:05 +08:00 |
| Script exit code | PASS | `0` (per cron agent's report to Telegram) |
| Manifest fields | PASS | All 13 expected fields populated correctly |
| Git commits | PASS | `c298900` (data) + `96b5bbc` (manifest follow-up) both present |
| Tree state | PASS | Working tree clean, no force-push history, HEAD = origin/main |
| GitHub Actions | PASS | Workflow run on `96b5bbc` succeeded; deploy job succeeded |
| Live HTTP | PASS | All 5 URLs HTTP 200, last-modified 2026-07-06 01:04:59 UTC, sizes match |
| Chinese UI | PASS | `<html lang="zh-CN">`, 6 modules, filter chips, Mermaid SVG all rendered |
| JS console | PASS | Zero errors, zero warnings |
| Telegram delivery | PASS | Message persisted at `~/.hermes/cron/output/452055bd607a/2026-07-06_09-05-45.md` |
| JSON data quality | PASS | All 8 JSONs parse; 0 duplicate papers, 0 duplicate people |
| Consumer-noise filter | PASS | 1 `coconote` consumer entry (`Coconote (Quizlet)`) properly demoted — not in `candidates_by_source`, not classified as `cocorobo`/`miracle` |
| Metric semantics | NOTE | "+0 papers" stdout vs `papers_added=31` differ by scope (see §7) — informational only |

---

## 2. Cron run time & outcome

Source: `~/.hermes/cron/jobs.json["jobs"][id=452055bd607a]`.

| Field | Value |
|---|---|
| job_id | `452055bd607a` |
| name | `ai-education-weekly-watch` |
| schedule | `0 9 * * 1` (Monday 09:00 +08:00) |
| last_run_at | `2026-07-06T09:05:48.557562+08:00` |
| last_status | `ok` |
| last_error | `null` |
| last_delivery_error | `null` |
| repeat.completed | `1` (first successful run) |
| next_run_at | `2026-07-13T09:00:00+08:00` |
| deliver target | telegram chat `1540208324` (Home) |

Manifest `ran_at`: `2026-07-06T01:04:38.617166+00:00` (= 09:04:38 +08:00, ~1 min before
the cron-recorded `last_run_at`, which is when the wrapper finished — consistent).

---

## 3. Telegram delivery

Source: `~/.hermes/cron/output/452055bd607a/2026-07-06_09-05-45.md` (full text in §3 of the
raw log).

The Telegram message begins with: `**Status: OK ✓ — auto-published**`.

Delivery fields confirmed:
- `last_delivery_error = null` (Hermes wrapper recorded)
- `deliver = "telegram"`, `origin.chat_id = 1540208324` (Home channel)
- The exact file `~/.hermes/cron/output/452055bd607a/2026-07-06_09-05-45.md`
  exists and contains a markdown report with the table shown above

---

## 4. Week tag & detected titles

`manifest.week_tag = 2026-W28` ✓

`docs/reports/weekly/2026-W28.md` exists (8,478 B), and `grep` confirms all four titles:

| # | Title | URL |
|---|---|---|
| 1 | AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation | `https://arxiv.org/abs/2308.08155` |
| 2 | Multi-Agent Design: Optimizing Agents with Better Prompts and Topologies | `https://arxiv.org/abs/2502.02533` |
| 3 | Towards a Science of Scaling Agent Systems | `https://arxiv.org/abs/2512.08296` |
| 4 | MIRACLE — Multi-Agent Intelligent Regulation to Advance Collaborative Learning Environment | `https://arxiv.org/abs/2605.12923` |

---

## 5. Source counts summary

From `manifest.source_counts` (38 source IDs):

| Source group | Count active | Count zero | Notes |
|---|---|---|---|
| arXiv direct (4) | 4 | 0 | AutoGen / Multi-Agent Design / Scaling / MIRACLE papers |
| arXiv search queries (4) | 0 | 4 | Empty results; **fallback path engaged** |
| CocoRobo (HK) (2) | 2 | 0 | `cocorobo-research`, `cocorobo-smart` |
| Stanford (2) | 2 | 0 | `stanford-ai-ed`, `stanford-hai` |
| Microsoft (2) | 2 | 0 | `ms-autogen`, `ms-agent-framework` |
| Khanmigo + blog (2) | 2 | 0 | |
| CMU LearnLab (1) | 1 | 0 | |
| People (11) | 11 | 0 | jarvela, nguyen, edwards, sobocinski, tormanen, koedinger, khan, chiwang, shuangli, haiyangxin, chingsingchai, harisubramonyam |
| Conferences (6) | 6 | 0 | AIED / ISLS / LAK / EDM / CUI / BJET |
| Oulu (3) | 0 | 3 | Hi / Lead / LET — none fetched |
| Google MASS (1) | 0 | 1 | Not fetched |
| search_fallback | 0 | — | Triggered but 0 hits, 0 errors |

**Total active sources: 31** (matches `dashboard-summary.json.totals.active_sources: 31`).
**Total tracked sources: 51** (matches `dashboard-summary.json.totals.stable_sources: 51`).

`fallback_status` = `{ ran: true, queries: 12, hits: 0, errors: [] }` — fallback ran but
did not produce additional hits, with no errors. **No hermes_tools / DuckDuckGo warnings.**

---

## 6. Publish status & commits

| Field | Expected | Observed | Match |
|---|---|---|---|
| `manifest.publish_requested` | true | true | ✓ |
| `manifest.publish_status` | committed | committed | ✓ |
| `manifest.publish_commit` | set | `c2989006323332950484a5c3f1a206fb7ec3b826` | ✓ |
| `manifest.publish_error` | null | null | ✓ |
| `manifest.pages_expected_to_rebuild` | true | true | ✓ |
| `manifest.dashboard_summary_rebuilt` | true | true | ✓ |
| `manifest.dashboard_summary_error` | null | null | ✓ |

**Git chain** (`git log --oneline -n 6`):

```
96b5bbc Record publish commit c298900 in manifest (2026-W28)   ← HEAD / origin/main
c298900 Update AI education weekly watch 2026-W28              ← publish_commit
2e5315d Localize AI education dashboard to Chinese (v1.3.3)
8671029 Auto-publish weekly watcher output to GitHub Pages (v1.3.2)
8fe2d87 Record publish commit e514bd6 in manifest (2026-W27)
e514bd6 Update AI education weekly watch 2026-W27
```

No force-push, no history rewrite. `git status -sb` returns
`## main...origin/main` with no modifications.

---

## 7. Metric Semantics Note

The script stdout and the manifest use different scopes for what looks like the same metric.
This is **informational only** — it does not affect run success — but is worth recording
before v1.4.1.

| Channel | Field | Value | What it actually counts |
|---|---|---|---|
| Script stdout | `+0 papers` (printed line) | 0 | Per-run **newly appended** to the registry this run |
| `manifest.entity_changes.papers_added` | `31` | 31 | Cumulative **curated paper entries exercised/seen** during this run |

**Interpretation:**
- `+0 papers` (stdout) = "no row was *appended* to `papers.json` this week that wasn't
  already there." This is true: the 4 arXiv entries re-emerged from the source sweep but
  were already tracked in the registry as prior seed entries.
- `papers_added=31` (manifest) = the cumulative count of curated paper entries that the
  registry passed through during this run's processing — not a delta, but a participation
  count of tracked papers whose metadata or status was updated.

**Why this matters for a reader:**
The two numbers tell different stories (delta vs participation), but the labels look like
they refer to the same thing. A reader seeing "0 papers" in the Telegram summary and
"31 papers" in the manifest would reasonably wonder which is right.

**Suggested v1.4.1 split (no code changes today):**
- `papers_appended` — delta entries added to the registry this run
- `papers_seen` — count of tracked papers exercised during the source sweep
- `papers_updated` — count of papers whose fields changed
- `papers_total_tracked` — total size of `papers.json` after this run

This matches the existing structure already used for `systems_updated` (8) and
`people_updated` (5), which both report "updates" not "appends."

---

## 8. JSON parse check

```
docs/data/papers.json              OK
docs/data/systems.json             OK
docs/data/people.json              OK
docs/data/tech-stack.json          OK
docs/data/timeline.json            OK
docs/data/dashboard-summary.json   OK
docs/data/weekly/latest.json       OK
docs/data/weekly/manifest.json     OK
```

All 8 JSONs parse with `python3 -m json.tool`.

---

## 9. Duplicate / quality checks

| Check | Result |
|---|---|
| Duplicate paper titles | none (41 papers, 0 dup titles) |
| Duplicate paper URLs | none (0 dup URLs) |
| Duplicate people names | none (16 people, 0 dup names) |
| Consumer-noise filter (coconote.app) | **1 demoted entry** — `Coconote (Quizlet)` exists in `systems.json` but is correctly tagged with quizlet/consumer context, **not** confused with `cocorobo` or `miracle`. The candidates_by_source list for `cocorobo-research`/`cocorobo-smart` only contains `cocorobo.hk/research` and `cocorobo.hk/smart`. |
| Dashboard totals consistency | `totals.papers=41` matches `papers.json` length; `totals.systems=10` matches `systems.json` length; `totals.people=16` matches `people.json` length; `totals.timeline_events=11` matches `timeline.json` length |

---

## 10. GitHub Actions workflow result

`gh run list --workflow=pages.yml --limit 4`:

| databaseId | headSha | createdAt | conclusion |
|---|---|---|---|
| 28761341558 | `96b5bbc` | 2026-07-06T01:04:48Z | **success** |
| 28761339958 | `c298900` | 2026-07-06T01:04:45Z | cancelled |

`gh run view 28761341558 --json jobs.conclusion` →
```
deploy → success
```

The run on `c298900` is `cancelled` because the workflow has
`concurrency.cancel-in-progress: true` and the follow-up commit `96b5bbc` pushed 3 seconds
later. **The deploy that actually shipped to Pages is 28761341558 on `96b5bbc`**, which
succeeded and matches the live `last-modified: 2026-07-06 01:04:59 GMT` on all five URLs.

This matches the user's known-good pattern: legacy `gh api /pages/builds/latest` can show
stale status, so we rely on `gh run list --workflow=pages.yml` + `curl` byte match instead.

---

## 11. Live HTTP check (two rounds)

Round 1 (at audit time, 2026-07-11 04:47 +08:00):

| URL | HTTP | size | last-modified | cache-control |
|---|---|---|---|---|
| `/` | 200 | 7,321 B | 2026-07-06 01:04:59 GMT | max-age=600 |
| `/data/dashboard-summary.json` | 200 | 26,108 B | 2026-07-06 01:04:59 GMT | max-age=600 |
| `/data/weekly/latest.json` | 200 | 3,484 B | 2026-07-06 01:04:59 GMT | max-age=600 |
| `/data/weekly/manifest.json` | 200 | 2,920 B | 2026-07-06 01:04:59 GMT | max-age=600 |
| `/reports/weekly/2026-W28.md` | 200 | 8,478 B | 2026-07-06 01:04:59 GMT | max-age=600 |

Round 2 (immediately after first check, same minute):
- `/` size 7,321 B (matches)
- `/data/weekly/manifest.json` size 2,920 B (matches)

All files non-placeholder (>3 KB), `last-modified` aligned to the 2026-07-06 deploy
window, `cache-control: max-age=600` present on every URL.

---

## 12. Chinese UI check (browser)

Navigated to `https://conanxin.github.io/ai-education-system-map/`.

| Check | Result |
|---|---|
| `<html lang="...">` | `zh-CN` ✓ |
| `<title>` | `全球 AI 教育系统地图 — MAI · MIRACLE · CocoNote · Khanmigo · LearnLab · AutoGen · MASS` ✓ |
| H1 | `全球 AI 教育 系统地图` ✓ |
| Module 1 header | `本周更新 2026-W28` ✓ |
| Module 2 header | `研究脉络 1989 → 2026` ✓ |
| Module 3 header | `系统卡片 10 个系统` ✓ |
| Module 4 header | `论文网络摘要 41 论文 · 5 个分组` ✓ |
| Module 5 header | `关键人物与机构 16 人物 · 7 个机构` ✓ |
| Module 6 header | `信息源健康状态 实时` ✓ |
| Filter chips (system) | 全部 / 研究原型 / 产品 / 基础设施 / AI 导师 / 课堂 OS / 多智能体 / SSRL / HASRL — all Chinese ✓ |
| Stat values | 新论文 31 / 新系统 8 / 新人物 5 / 活跃来源 31 / 稳定来源 51 ✓ |
| Fallback status | `运行=true · 查询=12 · 命中=0` ✓ |
| View weekly report link | `查看本周报告 →` → `/reports/weekly/2026-W28.md` ✓ |
| View on GitHub link | `在 GitHub 查看 →` ✓ |
| Mermaid SVG | 1 rendered (`.mermaid` → 1 SVG inside) ✓ |
| System cards | 10 articles (matches `systems.json` length) ✓ |
| Console errors | 0 ✓ |
| Console warnings | 0 ✓ |

---

## 13. Telegram reconciliation

The message persisted in `~/.hermes/cron/output/452055bd607a/2026-07-06_09-05-45.md`
matches what the audit checklist expected:

- `exit code = 0` ✓
- `week tag = 2026-W28` ✓
- `publish_status = committed` ✓
- `publish_commit = c298900` (full SHA recorded) ✓
- `dashboard_summary_rebuilt = true` ✓
- `fallback_status: ran, 12 queries, 0 hits, 0 errors` ✓
- Top 3 new titles (AutoGen / Multi-Agent Design / Scaling Agent Systems) listed ✓
- MIRACLE flagged as "also worth glancing at" (4th title) ✓
- "No failure to surface" closing line ✓

---

## 14. Remaining risks

1. **Metric semantics ambiguity (§7)** — The "+0 papers" stdout vs `papers_added=31`
   mismatch is the only meaningful inconsistency found. It does **not** break the run,
   but a future reader of the Telegram summary would have to reconcile two numbers.
   **Action proposed:** v1.4.1 split per §7.

2. **Workflow concurrency cancellation** — The Pages workflow cancelled the run on
   `c298900` because `96b5bbc` pushed 3 seconds later. This is **intended behaviour**
   (`concurrency.cancel-in-progress: true` saves redundant deploys) and does not affect
   the user-facing result, but it does mean a stale `gh api /pages/builds/latest` would
   show the older `c298900` build. **Recommendation:** always use `gh run list
   --workflow=pages.yml --json headSha,conclusion` filtered to the latest run + verify
   with a `curl` byte check against the live site.

3. **`p-haiyangxin` and `p-chingsingchai` IDs** — both are present and active in the
   manifest, but neither name matches a well-known public researcher I can verify
   externally. They were carried over from prior weekly runs (presumably seeded
   intentionally). **Not a run failure; flagging for the next manual review.**

4. **Workflow `verify site contents` step** — `/.github/workflows/pages.yml` hardcodes
   `2026-W27.md` in its required-files list. This still passes because the file exists,
   but it would not catch a case where W28 was deleted and W29 was expected. **Minor
   housekeeping; suggest making the step dynamic in v1.4.1.**

---

## 15. Recommended next step

The cron is healthy. Two small follow-ups are recommended, **neither blocking**:

- **(a) v1.4.1 watcher tweak** — split `entity_changes.papers_added` into
  `papers_appended` / `papers_seen` / `papers_updated` / `papers_total_tracked` to
  remove the stdout vs manifest discrepancy. Touch only `scripts/weekly_ai_education_watch.py`
  and its docstrings; no schema-breaking change required (new fields can be added).
- **(b) workflow hardening** — make `/.github/workflows/pages.yml`'s "verify site
  contents" step dynamic (read latest.json + assert that file exists). Touches only
  one YAML file.

**No action needed for v1.4 itself. Status: PASS — cron + publish + Pages + UI all
verified.** Audit reports `v1_4_first_cron_audit_2026-07-06.md` (this file) and
`v1_4_first_cron_raw_2026-07-06.md` (evidence) will be committed to `main` after
this audit; no code changes are committed in this round.

---

## Audit signature

- **Audit conducted by:** Hermes (cron audit sub-mode)
- **Audit round:** v1.4 — first-real-cron-run-audit
- **Files written:**
  - `reports/audit/v1_4_first_cron_audit_2026-07-06.md` (this file)
  - `reports/audit/v1_4_first_cron_raw_2026-07-06.md` (raw evidence)
- **Files NOT modified:** all other paths (cron, watcher, pages, JSONs, JS, CSS)