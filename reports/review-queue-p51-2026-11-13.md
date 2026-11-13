# P51: Review of 21 quarantined papers (2026-11-13)

Core scope: AI-supported education or training, educational content generation, AI effects on students/teachers, learning assessment and AI-in-education governance. Generic agent capability research and educational-institution back-office technology are adjacent but are not automatically part of the core corpus.

Method: resolve each queue entry by its stable index with the repository CLI; keep original rejected records and original gate reasons. SOURCE-CHECKED = checked the source abstract or publisher description; TITLE-REVIEWED = decision from the recorded title and available project context, not a full-text evaluation. A future reviewer may override an earlier dismissal.

| Index | Decision | Paper | Reason | Basis |
| --- | --- | --- | --- | --- |
| 00 | dismissed | [MAMath-Bench: Process-Aware and Robust Evaluation of Multimodal Multi-Agent Mathematical Reasoning](https://arxiv.org/abs/2610.26943) | Math-reasoning benchmark, not a study of learners, tutors, or educational outcomes | SOURCE-CHECKED [source](https://arxiv.org/abs/2610.26943) |
| 01 | dismissed | [Integrating Fairness and Explainability in a Multiple Instance Reinforcement Learning System](https://arxiv.org/abs/2610.00035) | Fairness and explainability in reinforcement learning; no education objective | TITLE-REVIEWED |
| 02 | dismissed | [ViFA-Council: Multi-Agent LLM Deliberation for Vietnamese Folk Art Generation](https://arxiv.org/abs/2609.13348) | Agent-driven Vietnamese folk-art generation; no learning intervention | TITLE-REVIEWED |
| 03 | dismissed | [MedRoundsQA: A Persona and Difficulty Aware Evaluation for Multi-Turn Medical Consultations](https://arxiv.org/abs/2609.12851) | Medical consultation QA benchmark, not clinician training | TITLE-REVIEWED |
| 04 | dismissed | [Exposing Weaknesses in Emotion Recognition in Conversations](https://arxiv.org/abs/2609.05806) | Emotion recognition in conversations; no educational evaluation | TITLE-REVIEWED |
| 05 | restored | [CogEvol: Towards Efficient and Reliable Learning Environment Generation](https://arxiv.org/abs/2608.30968) | Generates educational slides and interactive learning pages from a course brief | SOURCE-CHECKED [source](https://arxiv.org/abs/2608.30968) |
| 06 | restored | [SIC-Agents: Benchmarking and Building an Adaptive Simulator for Pediatric Serious Illness Communication Training](https://arxiv.org/abs/2608.29481) | Adaptive simulation of clinician communication training | SOURCE-CHECKED [source](https://arxiv.org/abs/2608.29481) |
| 07 | dismissed | [Artificial Intelligence in Mechanical Engineering: Foundations, Opportunities, Challenges, and Responsibilities](https://arxiv.org/abs/2610.33105) | General AI in mechanical engineering, with curriculum discussion only peripheral | SOURCE-CHECKED [source](https://arxiv.org/abs/2610.33105) |
| 08 | dismissed | [When Statisticians Can Also Be AI Engineers, What Could We Build?](https://arxiv.org/abs/2610.32105) | Statistical-analysis agents, not teaching or learning | SOURCE-CHECKED [source](https://arxiv.org/abs/2610.32105) |
| 09 | restored | [When Does It Become Cheating? Exploring the Roles of Self-Efficacy and the Impostor Phenomenon in Computing Students' Perceptions of Academic Dishonesty](https://arxiv.org/abs/2610.05579) | Computer-science students' academic integrity and AI-related cheating perceptions | SOURCE-CHECKED [source](https://arxiv.org/abs/2610.05579) |
| 10 | dismissed | [Altruism as Infrastructure: Volunteer Moderation in a Bangladeshi Higher Education Facebook Group](https://arxiv.org/abs/2610.05470) | Study-abroad information volunteer moderation; AI only future context | SOURCE-CHECKED [source](https://arxiv.org/abs/2610.05470) |
| 11 | dismissed | [Agentic AI Modernization: Transforming Institutional Infrastructure Through Orchestrated Multi-Agent LLM Framework](https://doi.org/10.32996/jcsts.2026.8.4.1) | Higher-education back-office IT modernization; learning effects not studied | SOURCE-CHECKED [source](https://al-kindipublishers.org/index.php/jcsts/article/view/12077) |
| 12 | dismissed | [An empirical study of testing practices in open source AI agent frameworks and agentic applications](https://doi.org/10.1007/s10664-026-10857-9) | Software testing practices in AI agent frameworks; no education context | TITLE-REVIEWED |
| 13 | dismissed | [Agentic artificial intelligence: Architectures, planning mechanisms, multi-agent collaboration, applications, challenges, and future research directions-A comprehensive review](https://doi.org/10.33545/27076571.2026.v7.i7a.358) | Generic review of agent architectures; not education-specific | TITLE-REVIEWED |
| 14 | dismissed | [Mining the Design Space of Multi-Agent Workflows](https://doi.org/10.48550/arxiv.2610.31709) | Workflow optimization of agents; educational outcomes not evaluated | SOURCE-CHECKED [source](https://arxiv.org/abs/2610.31709) |
| 15 | dismissed | [Multi-Agent Social Simulation: Protocolizing LLM-Driven Agent-Based Modeling as a Quantitative Research Method](https://doi.org/10.3390/ai7080279) | Social simulation methods; not education-specific | TITLE-REVIEWED |
| 16 | dismissed | [Design and Tuning of Multi-Agent Systems Using Bayesian Evolutionary Optimization](https://doi.org/10.48550/arxiv.2610.29276) | Multi-agent Bayesian optimization; no educational setting | TITLE-REVIEWED |
| 17 | dismissed | [Deep Research in Physical Sciences: A Multi-Agent Framework and Comprehensive Benchmark](https://doi.org/10.48550/arxiv.2606.18648) | Deep research for physical sciences, not teaching or training | TITLE-REVIEWED |
| 18 | dismissed | [Collaborative Memory for Multi-Agent VLM Systems](https://doi.org/10.48550/arxiv.2609.17921) | Collaborative memory for vision-language agents, generic mechanism | TITLE-REVIEWED |
| 19 | dismissed | [Symbolic Machine Learning for Quasi-Optimal Control of a Collaborative Multi-Agent Robotic System](https://doi.org/10.15622/ia.25.4.5) | Multi-agent robotic control, not learning or education | TITLE-REVIEWED |
| 20 | dismissed | [Learning to Steer LLM Agents and Multi-Agent Systems](https://doi.org/10.48550/arxiv.2610.22316) | Steering LLM agents, generic agent capability | TITLE-REVIEWED |

## Follow-up

Original W45 historical weekly reports are not retrospectively rewritten; database totals change from 21 to 24 papers. All 21 queue rows remain for provenance: 3 restored and 18 dismissed; open count zero.
The three restorations show that automatic filtering can reject relevant course-content generation, professional simulation training and AI academic integrity. Keep a review queue rather than broadly whitelisting machine-learning jargon like student-teacher distillation.
The restored AI academic-integrity title had an HTML apostrophe entity; it was decoded for display without changing its ID or canonical key.
P51 also makes the dismiss CLI refresh the public dashboard review count. The independent seed-import subprocess test timeout was increased to 45 seconds to reduce WSL startup-load flakiness.
The current Hermes Monday writer is retained; migration to GitHub Actions and choice of LICENSE are governance decisions still reserved for the owner.

## Shadow weekly-write verification (non-publishing)

- The isolated copy at ~/.cache/atlas-p51-shadow was used with the production watcher, without the publish flag. This is a data-write integration test on a copy, not a live scheduled run or a GitHub deployment.
- Original production corpus at shadow start: 24 papers, 21 closed queue items. Shadow result: +15 papers (39 total), 88 new rejected candidates (queue 109), including 32 held by weekly_cap. Source health: five arXiv API queries and 12/12 OpenAlex fallback queries, with google-mass fetch_URLError remaining.
- An additional false admission was found on reviewing the shadow's 15 new papers: arXiv 2610.16543 is about model distillation despite its learner-centered and teaching metaphors. P51 moved learner(s) from a hard to a soft education indicator and added a regression test. The shadow result predates that code adjustment and is not a prediction of the revised exact list.
- The next actual Hermes scheduled publish remains 2026-11-16 09:00 Asia/Shanghai. This run did not update its definition or trigger an actual publish.
