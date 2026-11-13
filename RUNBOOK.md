# AI Education Atlas｜运行与维护手册

返回 [README](README.md) · [研究网站](https://conanxin.github.io/ai-education-system-map/) · [阶段更新](CHANGELOG.md)

本文件记录实际可用的**数据采集、人工审查、构建和部署**操作；README 只负责介绍项目。命令均在仓库根目录运行。

## 1. 当前架构

| 环节 | 执行者 | 触发条件 | 输出 |
| --- | --- | --- | --- |
| 论文/资料采集 | 本机 Hermes cron：`ai-education-weekly-watch` | 每周一 09:00（`Asia/Shanghai`） | 研究 JSON、周报、manifest |
| 数据写入与推送 | `scripts/weekly_ai_education_watch.py --publish` | Hermes 任务调用 | 提交到 `origin/main` |
| 站点测试与部署 | GitHub Actions：[`pages.yml`](.github/workflows/pages.yml) | `main` 分支提交或手动运行 workflow | `docs/` 静态产物部署 GitHub Pages |
| 人工审核 | `scripts/review_queue.py` | 人工判定 | `papers.json`、`review-queue.json`、仪表盘 |

- Hermes job ID：`452055bd607a`。可用 `hermes cron list` 查看任务，`hermes cron runs 452055bd607a` 查看历史运行。
- 当前**没有** GitHub Actions 定时采集任务；不要再增加并行写入者。
- 一轮 `--publish` 在当前实现中可能产生**数据提交和 manifest 补充提交**；这不是两个独立的采集任务。是否合并提交留到首次 P51 正式周任务验收之后。
- P51 更新于 2026-11-13；正式计划的首次 P51 周任务为 2026-11-16。历史周报的时间和内容不会因为后续人工审定而被追溯改写。

## 2. 本地预览与测试

```bash
python3 -m http.server 8765 --directory docs --bind 127.0.0.1
```

打开 http://127.0.0.1:8765/。测试不会联网采集论文：

```bash
python3 -m unittest discover -s tests
```

如需降低某些测试环境中的网络等待参数，可沿用 GitHub Actions 的测试环境设置（测试逻辑本身应使用 mock）：

```bash
AI_EDUCATION_OPENALEX_BACKOFF=0 \
AI_EDUCATION_OPENALEX_PACING=0 \
AI_EDUCATION_ARXIV_API_DELAY=0 \
python3 -m unittest discover -s tests
```

## 3. 采集命令：先区分是否写数据

**只读预览**：会调用联网采集来源，但**不写研究数据，也不推送**：

```bash
python3 scripts/weekly_ai_education_watch.py \
  --data-dir docs/data \
  --reports-dir reports/weekly \
  --dry-run
```

**真实写本地数据，但不推送**：将修改 `docs/data/`、`reports/weekly/` 与 `docs/reports/weekly/`；适合有意执行单次人工测试时使用，不要把它误当成 dry-run。

```bash
python3 scripts/weekly_ai_education_watch.py \
  --data-dir docs/data \
  --reports-dir reports/weekly \
  --max-results 3
```

`--max-results` 是部分来源的查询数量参数，**不保证所有来源总共只产生 3 条结果**；一次运行自动新增论文上限由 `--max-new-papers` 控制，默认 15。

**真实写入并自动提交、推送**：与现有 Hermes 调度任务的命令相同。此命令会修改远端 `main` 并触发 GitHub Pages 部署，通常应交给定时任务执行。

```bash
python3 scripts/weekly_ai_education_watch.py \
  --data-dir docs/data \
  --reports-dir reports/weekly \
  --publish
```

发布仅会暂存以下约定路径：`docs/data`、`docs/reports`、`reports/weekly` 和 `README.md`；不会自动发布其他目录中的修改。发布状态写入 `docs/data/weekly/manifest.json`。手动发布前请确认当前分支与 `origin/main` 对齐，避免另一个写入者同时推送。

**非生产集成检查**：需要验证真实写入逻辑但不改变仓库时，使用独立的数据副本和报告目录，**不要传入 `--publish`**；P51 的影子验收就是这样做的。

## 4. 人工审查与数据边界

自动发现的论文需经过 `scope_decision()` 相关性门禁；官方策展来源可以按其来源标记通过。技术论文中出现的 `teacher`、`student`、`learner`、`distillation` 等词，不足以证明其研究对象是教育。门禁不能替代人工判断。

```bash
python3 scripts/review_queue.py list
python3 scripts/review_queue.py list --all
```

- `list` 显示仍需裁决的条目；`--all` 显示所有历史记录和完整索引。
- 判断研究是否**直接**涉及 AI 辅助学习、教学内容、专业训练、学习评估或 AI 教育治理。只讨论通用 Agent 能力、模型蒸馏、工程控制或学校后台 IT 的论文通常不属于图谱核心资料。
- 确认索引后，使用 `python3 scripts/review_queue.py restore N` 或 `python3 scripts/review_queue.py dismiss N`（把 `N` 换为 `list --all` 中的实际整数）。
- `restore` 在论文库中加入 `manual-review` 标签，`dismiss` 保留被驳回的历史记录。两者都会更新队列状态；涉及变化时仪表盘摘要同步重建。
- P51 原有 21 条隔离论文审查结果为恢复 3、驳回 18，见 [逐条裁决台账](reports/review-queue-p51-2026-11-13.md)。后续新候选可能使待审数量重新增长。

规范化 `key` 用于识别相同论文的 arXiv/DOI/URL 变体；原始 `id` 不应随意改变。每次周任务最多自动新增 15 篇，超额部分以 `weekly_cap` 原因留在队列。

## 5. 采集来源与可选回退

- arXiv：优先使用官方 `export.arxiv.org/api/query`，失败时才尝试旧 HTML 路线，并记录错误。
- OpenAlex：接口有重试和限速；可按需要通过环境变量 `OPENALEX_API_KEY` 或 `OPENALEX_MAILTO` 配置身份，不写到仓库。
- Hermes 搜索回退：只有当 `AI_EDUCATION_ENABLE_HERMES_SEARCH_FALLBACK=1` 才启用。
- DuckDuckGo HTML 回退：只有当 `AI_EDUCATION_ALLOW_DDG_HTML=1` 才启用；不能假定现有 Hermes 工具或 DDG 会自动补足失败来源。
- `google-mass` 页面偶有 `fetch_URLError`，会出现在来源健康信息中；此错误不意味着所有 arXiv/OpenAlex 来源失败。

可调参数与代码默认值：

| 环境变量 | 默认值 | 用途 |
| --- | --- | --- |
| `AI_EDUCATION_ARXIV_API_DELAY` | `3` 秒 | arXiv 查询间隔 |
| `AI_EDUCATION_OPENALEX_ATTEMPTS` | `3` | OpenAlex 重试次数 |
| `AI_EDUCATION_OPENALEX_BACKOFF` | `2` 秒 | OpenAlex 退避基数 |
| `AI_EDUCATION_OPENALEX_PACING` | `1` 秒 | OpenAlex 查询间隔 |

## 6. 输出、状态与网页构建

| 文件 | 用途 |
| --- | --- |
| `docs/data/papers.json` | 正式论文 |
| `docs/data/research-entities.json` | 非论文研究参考 |
| `docs/data/review-queue.json` | 待审、已恢复、已驳回记录 |
| `docs/data/weekly/latest.json` | 最近一次周报数据 |
| `docs/data/weekly/manifest.json` | 来源诊断、更新计数、发布状态 |
| `docs/data/dashboard-summary.json` | 网站展示用总量、来源状态、周报归档索引 |
| `reports/weekly/YYYY-WW.md` | 仓库中的周报源文件 |
| `docs/reports/weekly/YYYY-WW.md` | GitHub Pages 对应周报的镜像文件 |

`reports/weekly` 与 `docs/reports/weekly` 当前确实有两个路径，用途不同；**未验证迁移方案前不删除任何一个**。周任务还会刷新既有的系统和人物记录（例如更新 `last_seen`）；这不等于本周新增了系统或人物。

手工更正研究数据后需要重建摘要时：

```bash
python3 scripts/build_dashboard_summary.py --data-dir docs/data
python3 -m unittest discover -s tests
```

检查本次运行的 `manifest.json` 中 `week_tag`、`source_errors`、`rejected_candidate_count`、`dashboard_summary_rebuilt`、`publish_status`、`publish_commit`。`publish_status=skipped` 表示本次没有请求推送；`failed` 则应核查详细错误，而不能把“脚本跑完”视为已上线。

## 7. GitHub Pages 发布验收

`.github/workflows/pages.yml` 在 `main` 上执行测试、验证公开 JSON 和最新周报、上传 `docs/` Artifact，最后通过 `actions/deploy-pages@v4` 部署。这不是旧的 `main/docs` 分支发布流程。

```bash
gh run list --workflow pages.yml --limit 3
gh run view --log
curl -fsSI https://conanxin.github.io/ai-education-system-map/
curl -fsSI https://conanxin.github.io/ai-education-system-map/data/dashboard-summary.json
```

HTTP 200 只能证明服务可访问；如需确认**内容确实是当前版本**，比较公开文件与仓库内的数据：

```bash
curl -fsSL https://conanxin.github.io/ai-education-system-map/data/dashboard-summary.json \
  -o /tmp/atlas-dashboard-live.json
cmp docs/data/dashboard-summary.json /tmp/atlas-dashboard-live.json
```

也应对 `data/papers.json`、`data/review-queue.json`、`assets/app.js` 与 `index.html` 做相同的文件比对。新报告的路径从 `docs/data/weekly/manifest.json` 的 `weekly_report` 字段读取，不要硬编码早期周次 `2026-W27`。

## 8. 旧版种子报告仅供隔离初始化

`scripts/build_from_report.py` 是最初 MVP 报告的**初始化工具**，**不是**现有 P42+ 类型化数据的全量刷新命令。对于存在 `docs/data/research-migration.json` 的正式目录，脚本会以 `Typed P42 live corpus exists` 拒绝覆盖。

如需检验早期格式，可在空白临时目录执行：

```bash
python3 scripts/build_from_report.py \
  --input reports/seed/latest-report.md \
  --data-dir /tmp/atlas-seed-preview \
  --weekly-dir
```

不要直接以 `docs/data` 为目标重跑旧种子：即使绕过保护也可能抹掉按周积累的论文和已裁定状态。

## 9. 首次 P51 正式周任务验收清单

在 2026-11-16 原计划运行**之后**，核查而不是提前触发第二次生产运行：

1. Hermes job ID `452055bd607a` 的运行状态、退出码及 Telegram 投递记录。
2. 周报、`manifest.json`、`papers.json` 和待审队列的差异；新增论文 ≤15，记录拒绝总数与 `weekly_cap` 数量。
3. 逐篇复核是否真正涉及教育，重点检查模型蒸馏用语误收和课程内容生成、AI 教育治理误拒。
4. 确认 GitHub `main`、Actions 测试部署，以及正式网页的内容一致；继续记录 `google-mass` 来源错误。
5. 本轮没有改变 Hermes 任务定义、Telegram 通道或任何 LICENSE 授权选择。

[返回项目概览](README.md)
