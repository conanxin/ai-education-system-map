# Changelog

Newest first. Counts quoted in older sections are snapshots from that phase.

## P50 live-tuned gate and weekly cap (2026-11-12)

First live run of the P47 collectors (two passes, about 135 s each): all five
arXiv API queries returned 15 results, OpenAlex answered 12 of 12 queries
with no rate limiting, and the only source error was the `google-mass` page.

- The live sample showed machine-learning jargon passing as education
  ("teacher/student" distillation, federated "collaborative learning").
  Education terms are now split into HARD and SOFT; SOFT terms do not count
  when the text carries an ML-jargon marker, and an abstract needs at least
  one HARD term. Bare "agentic" no longer counts as an AI context.
  On the 111 new candidates of that sample: 46 pass, 65 go to the queue.
- `--max-new-papers` (default 15) caps how many new papers one run may add;
  the overflow goes to the review queue with reason `weekly_cap`.
- A paper waiting in, or dismissed from, the review queue is never
  auto-added; `scripts/review_queue.py restore` is the only way in.

## P49 in-page weekly reports (2026-11-12)

- `build_dashboard_summary.py` writes `weekly_archive` (every report under
  `docs/reports/weekly/`, newest first, with its new-paper count) and
  `review_queue` (open / total) into `dashboard-summary.json`.
- The "本周研究观察" section has a collapsed reader: pick a week, read the
  report in the page. Source diagnostics and methodology are folded by
  default. Report text is escaped before formatting; only http(s) links are
  turned into anchors.
- The section shows how many candidates are waiting in the review queue.
- Verified in headless Chrome at 1440 px, 390 px and light theme: 16 weeks
  listed, W45's 30 entries render, no horizontal overflow, an injected
  `<img onerror>` / `javascript:` link stays inert text.

## P48 data model and review workflow (2026-11-12)

- Every record in `docs/data/papers.json` carries a canonical `key`; original
  `id` values are unchanged. DOIs inside publisher URLs (`/doi/10.x/...`) are
  recognised.
- `scripts/review_queue.py` lists, restores and dismisses review-queue
  entries. Restored papers are tagged `manual-review`, which the relevance
  gate treats as curated. Published, restored and dismissed papers are never
  queued again.
- `tests/test_data_schema.py` checks required fields and types for all six
  data collections, timestamp/year/URL formats, key uniqueness, the review
  queue shape, and that dashboard totals equal the data files.
- Weekly reports list authors for new papers and the number of candidates the
  gate rejected.
- README trimmed to current state; phase history moved to this file.

## P47 relevance gate and source reliability (2026-11-12)

Current counts: **21 papers** in `docs/data/papers.json` (12 reviewed core
records + 9 search-discovered papers that pass the gate), 33 other research
sources, 10 systems, 16 people. The counts quoted in the P42–P45 sections
below are historical snapshots.

- **Relevance gate.** Search-discovered papers (arXiv search, OpenAlex) no
  longer bypass filtering. A candidate needs a strong tracked term (SSRL,
  HASRL, MIRACLE, "self-regulated learning", "learning analytics", ...) or an
  education context *and* an AI/agent context. Acronyms are matched as whole,
  case-sensitive words, so "MAI" no longer hits "main". See `scope_decision()`
  in `scripts/weekly_ai_education_watch.py`.
- **Review queue.** `docs/data/review-queue.json` holds candidates the gate
  rejected, plus 21 records moved out of `papers.json` (added in W45, off
  topic). Each quarantined entry keeps its full original `record`; move it
  back into `papers.json` to restore it.
- **arXiv API.** `arxiv_search` registry items with an `api_query` are fetched
  from `export.arxiv.org/api/query` (Atom, newest first, abstracts and authors
  included) with a 3 s pause between calls. The HTML search URL remains as a
  fallback. Registry version 1.3.0.
- **OpenAlex.** Retries 429/5xx with backoff, paces queries, and stores the
  abstract. Optional identification comes from the environment, never from
  the repo: `OPENALEX_API_KEY` and/or `OPENALEX_MAILTO`.
- **Dedupe.** `paper_key()` treats `arxiv.org/abs|html|pdf/<id>` and
  `doi.org/10.48550/arxiv.<id>` as the same paper.
- **Dashboard labels.** "新增系统 / 新增人物" are now "复核系统 / 复核人物": the
  numbers count records whose `last_seen` was refreshed, not new records.
- **CI.** The Pages workflow runs the unittest suite before deploying and
  checks the report named in `weekly/manifest.json` instead of a fixed week.

Tuning knobs (environment): `AI_EDUCATION_ARXIV_API_DELAY` (default 3),
`AI_EDUCATION_OPENALEX_ATTEMPTS` (3), `AI_EDUCATION_OPENALEX_BACKOFF` (2),
`AI_EDUCATION_OPENALEX_PACING` (1). Set the last three to 0 for fast tests.

## Dashboard module history (P42 snapshot; see P43 section above)

The single-page site now has nine anchored reading sections, all driven by one
aggregated JSON file (`docs/data/dashboard-summary.json`):

1. **本周更新 (This Week)** — 周标签、本周新论文/系统/人物数量、备用搜索状态、查看每周报告 / 在 GitHub 查看 按钮。
2. **研究脉络 (Research Lineage)** — 水平 Mermaid 流程图
   (ITS → SRL/SSRL → HASRL → MAI → CocoNote → MIRACLE → Multi-Agent Classroom OS)
   含旁路说明(Khanmigo、AutoGen、MASS、CocoRobo SMART)。
3. **系统卡片 (System Cards)** — 所有追踪中的系统,以卡片形式展示徽章
   (SSRL/HASRL、多智能体、课堂 OS、AI 导师、产品、研究原型、基础设施)。筛选标签可客户端过滤。
4. **论文网络摘要 (Paper Network Summary)** — 论文按脉络角色分组
   (理论基础 / MAI 研究脉络 / MIRACLE·CocoNote / 多智能体基础设施 / 证据与政策)。点击标题打开来源链接。
5. **研究资料与来源 (Research References)** — 独立列出机构官网、人物资料、会议、政策与新闻，不计入论文总数。
6. **关键人物与机构 (People & Institutions)** — 研究者按机构分组
   (奥卢大学、Stanford、CMU LearnLab、Microsoft/Google、Khan Academy、CocoRobo/MIRACLE、其他)。
7. **信息源健康状态 (Source Health)** — 稳定来源数、本次活跃数、来源错误数、备用搜索状态、按来源的候选结果、registry/manifest/summary JSON 链接。

## P42 typed research sources

P42 separates the 41 legacy mixed records into 12 reviewed publications
stored in docs/data/papers.json and 29 non-paper references in
docs/data/research-entities.json. The provenance file
docs/data/research-migration.json documents original SHA256 and classification.
Private byte-preserving backup was made before migration.
Dashboard totals and reference_groups display each type without paper inflation.
Weekly monitoring routes official web pages, people and venues into references.
Seed bootstrap refuses overwriting a typed production collection.

## P43 editorial website redesign

The site remains a single GitHub Pages static HTML/CSS/JavaScript application,
with no added frontend framework, CDN runtime or backend service. A consistent
research-atlas visual language unifies the landing page, cards, navigation and
data-provenance notes.

- Editorial cover with live-from-archive totals for 12 papers, 29 references,
  10 systems and 16 people. The timestamp is the last archive, not live data.
- Four guided research routes, three directly linked primary reading examples,
  a six-stage interpretive framework and 11 data-derived timeline entries.
- Dedicated paper title/topic/year search and reference type filters/search,
  alongside the existing system categories and original source links.
- Source-transparency and research-method sections explain the separation of
  scholarly and non-scholarly records, and limits of weekly data.
- Four tested viewport widths (1440, 768, 390, 320), native light/dark themes,
  keyboard focus, skip links and reduced-motion handling.
- Replaces external Mermaid rendering with native, offline-capable semantic
  HTML/CSS for the research framework and timeline.

Existing deep link anchors are preserved. Run the repository Python unittest
suite for data and static markup guards. The P43 browser and interaction
smoke-test receipts are kept privately in the upgrade research work directory,
not in the published GitHub repository.

## P44 primary-source evidence and research relations

The evidence workbench is a curated static editorial dataset in
docs/data/research-deep-dives.json. It contains:

- **Three readings**: the 2023 HASRL/SSRL framework article (publisher
  full-text and abstract sections consulted), the 2025 SimClass NAACL paper
  (ACL Anthology metadata/abstract), and the 2025 MASS manuscript (arXiv
  abstract and Google Research publication record).
- **Six typed research-system links**: two verified direct paper/system
  identities and four clearly marked editorial comparisons. The latter
  must never be presented as actual project integrations or published
  experiments. All explanations, questions and boundaries link back
  to the original study URL.
- **Explicit review scope**: source_fulltext, source_abstract and
  editorial_comparison describe how statements were checked. They do not
  rate educational outcomes, paper quality or commercial product safety.
- **Five verified system-link corrections** in docs/data/systems.json
  (MAI, SimClass, MASS, CMU OLI/Torus and Coconote), replacing blank or
  unrelated destinations. The builder forwards provenance into system cards.

No weekly automation overwrites these authored research notes. The JSON
retains editorial_reviewed_at; subsequent revisions require independent
primary-source verification. The Python unittest suite checks paper IDs,
system names, evidence categories, and canonical data/dashboard consistency.

## P45 system provenance and software lifecycle review

All ten existing system cards now have official source URLs, provenance dates
and a distinct statement of what those URLs actually establish. P45 reviewed
Khanmigo, archived AutoGen, CTAT, CocoRobo SMART and UC Berkeley MAST.
AutoGen is **archived and not supported**; its official Microsoft Agent
Framework successor has its own separate link. CTAT's free academic/research
use must not be mistaken for proof of an open source code license. The MAST
record describes a general multi-agent failure taxonomy, not a deployed
education product. CocoRobo's platform capabilities remain vendor claims,
not independently replicated learning outcomes.

Cards expose audited primary-source links, available successor/research links,
and explicit caveats. The canonical sources remain docs/data/systems.json
and docs/data/tech-stack.json; the dashboard builder copies the provenance
fields. Updating a source URL never alters the counts for 12 scholarly papers,
29 other research sources, 10 system records or 16 people.
