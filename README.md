# AI Education Atlas｜全球 AI 教育研究图谱

**从学习调节到教育智能体：把论文、系统、研究者与证据放在同一张可追溯的地图上。**

AI Education Atlas is a curated research atlas for AI-supported learning, self-regulated learning and multi-agent education systems.

**[在线浏览研究图谱](https://conanxin.github.io/ai-education-system-map/)** · [最新周报索引](https://conanxin.github.io/ai-education-system-map/data/weekly/manifest.json) · [公开数据](docs/data/) · [维护手册](RUNBOOK.md) · [更新记录](CHANGELOG.md)

> **使用边界：**这是持续更新的研究索引，不是文献穷尽性检索、系统性能排行榜，也不代表对论文结论或产品效果的独立复现。请依据每条记录的原始来源核查。

## 从哪里开始阅读

| 阅读路线 | 适合的问题 | 入口 |
| --- | --- | --- |
| 研究脉络 | SRL、SSRL、HASRL 如何连接到 AI 智能体？ | [理论与演化](https://conanxin.github.io/ai-education-system-map/#research-lineage) |
| 系统地图 | MAI、MIRACLE、SimClass、Khanmigo 等系统有何不同？ | [系统比较](https://conanxin.github.io/ai-education-system-map/#system-cards) |
| 论文与证据 | 哪些主张有论文、原文与定位依据？ | [论文索引](https://conanxin.github.io/ai-education-system-map/#paper-groups) · [证据工作台](https://conanxin.github.io/ai-education-system-map/#evidence-lab) |
| 每周变化 | 最近收录了什么？数据源是否正常？ | [本周研究观察](https://conanxin.github.io/ai-education-system-map/#this-week) · [来源状态](https://conanxin.github.io/ai-education-system-map/#source-health) |

**核心研究线索：**自我调节学习（SRL）→ 社会共享调节学习（SSRL）→ 人机共享调节（HASRL）→ 元认知 AI 智能体（MAI）→ MIRACLE / 多智能体课堂。这是本项目组织研究的**阅读路径**，不意味着相关系统彼此具有直接继承关系或教育效果已获验证。

## 数据、来源与更新状态

图谱的论文、研究资料、系统、人物和时间线来自版本化 JSON。**当前数量请以 [dashboard-summary.json](docs/data/dashboard-summary.json) 为准**；[papers.json](docs/data/papers.json) 和 [review-queue.json](docs/data/review-queue.json) 提供可检查的原始记录与人工判定状态。

**P51 快照（2026-11-13；不是实时计数）：**24 篇论文、33 条非论文研究资料、10 个系统、16 位人物。原 W45 隔离队列 21 条已逐条审定：恢复 3 条、驳回 18 条、待处理 0 条。[查看逐篇审查依据](reports/review-queue-p51-2026-11-13.md)。

- **截至 P51 阶段（2026-11-13）的运行记录：**当时最近一次正式周任务为 2026-W46（2026-11-09）；P51 代码虽已上线，但当时尚未经历下一次正式周任务。请从 [manifest.json](docs/data/weekly/manifest.json) 查看**最新实际运行状态**。P51 影子运行只验证独立副本，模拟新增论文未发布到正式站点。
- **采集：**维护的官方来源与论文入口、arXiv 官方 API、OpenAlex 搜索补充。单个来源不可用时在运行诊断中留下错误，不等同于“没有新论文”。
- **相关性：**自动发现的论文须满足研究主题门禁；机器学习的 student/teacher/learner、蒸馏等技术术语不能仅凭字面被认定为真实教育研究。
- **准入：**每次周任务最多自动新增 **15 篇**；超额与不通过门禁的候选进入可追溯的人工队列。曾被驳回的条目不会自行重新收录；人工恢复标记为 `manual-review`。
- **身份与去重：**论文保留原始 `id`，并使用规范化 `key`（arXiv、DOI 或 URL）识别同一作品的不同链接形式。

网站支持页面内阅读历史周报、查看来源诊断与原始论文链接。**收录**意味着满足项目的整理标准，不等于全文已逐字审读或独立复现实验。

## 本地使用

不需要后台服务、数据库或前端打包工具；静态网站使用 HTML、CSS、JavaScript，数据处理使用 Python 标准库。

```bash
git clone https://github.com/conanxin/ai-education-system-map.git
cd ai-education-system-map
python3 -m http.server 8765 --directory docs --bind 127.0.0.1
```

打开 http://127.0.0.1:8765/ 即可浏览。运行现有自动化测试：

```bash
python3 -m unittest discover -s tests
```

以上命令**不会采集新论文或推送仓库**。更新数据、人工审查和发布命令在 [RUNBOOK.md](RUNBOOK.md)，不要对现有正式数据执行旧版种子初始化。

## 更新机制与责任边界

- **采集任务：**本机 Hermes `ai-education-weekly-watch`（ID `452055bd607a`），每周一 09:00（`Asia/Shanghai`）；按配置执行研究采集与数据发布。
- **网站部署：**推送 `main` 后，由 [`pages.yml`](.github/workflows/pages.yml) 中的 **GitHub Actions** 执行 Python 测试、检查站点数据、上传 `docs/` 产物并部署 GitHub Pages。**不是**旧版“从 `main/docs` 分支直接构建”模式。
- **调度原则：**目前由 Hermes 执行每周写入，GitHub Actions 只负责测试和网站部署。未启用第二套 Actions 周采集计划，避免重复写入。
- **状态核查：**[Actions 工作流](https://github.com/conanxin/ai-education-system-map/actions/workflows/pages.yml) · [最新运行清单](docs/data/weekly/manifest.json) · [运行维护手册](RUNBOOK.md)。

## 仓库导航

```text
docs/
  index.html                 静态研究图谱
  assets/                    页面 CSS / JavaScript
  data/                      公开的结构化研究数据
    dashboard-summary.json   网页展示用摘要与计数
    papers.json              论文记录
    research-entities.json   非论文研究资料
    review-queue.json        待审、恢复和驳回的历史记录
    source-registry.json     采集来源与查询配置
    weekly/                  最新周度数据与运行清单
  reports/weekly/            GitHub Pages 可访问的周报副本
reports/weekly/              周报的源文件
reports/review-queue-p51-2026-11-13.md  P51 审查台账
scripts/                     采集、索引、队列与迁移脚本
tests/                       标准库 unittest 自动测试
RUNBOOK.md                   操作说明与故障排查
CHANGELOG.md                 各阶段改动记录
```

## 语言与研究原则

界面以中文为主；论文标题、机构名、系统名和数据字段保持原始英文，避免翻译后难以追溯。每条研究主张尽量连接一手来源，区分原始文献、供应商报告、人工整理与推测，保留历史更新而不把旧结论默认为当前状态。

**已知边界：**部分外部来源（如 `google-mass`）偶有访问失败；相关性过滤仍可能误收或漏收；真正的周任务质量需要继续按周核查。详见 [数据方法](https://conanxin.github.io/ai-education-system-map/#methodology)、[P51 审查记录](reports/review-queue-p51-2026-11-13.md) 和 [更新历史](CHANGELOG.md)。
