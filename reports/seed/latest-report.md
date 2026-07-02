# AI Education MVP Research — Latest Report

**Scope:** 7 institutions (Oulu, Stanford HAI, CMU LearnLab, Microsoft Research, Google Research, Khan Academy, CocoRobo/MIRACLE)
**Keywords tracked:** SSRL / HASRL · metacognitive AI agent · multi-agent learning system · AI classroom system · learning analytics
**Compiled:** 2026-07-02 · MVP pass (depth over breadth, not exhaustive)

---

## 1. New Papers

| # | Title | Link | Institution | Summary (3 lines) |
|---|---|---|---|---|
| 1 | **Hybrid Intelligence Research at the University of Oulu — Position Paper 2025** | https://oulurepo.oulu.fi/handle/10024/59855 | University of Oulu (HI Programme) | Position paper formalising HI as co-evolution paradigm; four research themes include "Understanding humans in AI interaction." Anchors Oulu's 2023–2028 flagship. Directly feeds HASRL + MAI research streams. |
| 2 | **Human and artificial intelligence collaboration for socially shared regulation in learning** (Järvelä, Nguyen, Hadwin, 2023, BJET) | https://bera-journals.onlinelibrary.wiley.com/doi/10.1111/bjet.13325 | University of Oulu | **Introduces HASRL model + "trigger" concept.** The seminal citation for hybrid human-AI regulation of learning — explicitly cited as foundation of MAI agent design. |
| 3 | **Deliberative Interactions for Socially Shared Regulation in Collaborative Learning: An AI-Driven Learning Analytics Study** (Dang, Nguyen, Järvelä, 2024, JLA 11(3)) | https://learning-analytics.info/index.php/JLA/article/view/8393 | University of Oulu | Three-layer human-AI collaborative analysis on 2,125 utterances → identifies Plan-and-Implementation (adaptive) vs Trials-and-Failure (maladaptive) deliberation patterns. Empirical proof point that LA+AI can detect regulatory failure. |
| 4 | **MAI: Supporting Regulation of Learning with a Proactive AI Agent in Collaborative Learning Contexts** (Edwards et al., 2025) | https://oulurepo.oulu.fi/bitstream/handle/10024/58874/nbnfioulu-202510216402.pdf | University of Oulu | **System paper for MAI itself.** Proactive agent recognises trigger contexts and prompts metacognitive awareness — agent does not regulate *for* the group, but raises awareness so they self-regulate. Direct implementation of HASRL. |
| 5 | **RFI: Advancing AI in Education — Stanford HAI + Accelerator for Learning Response** (Aug 2025) | https://hai.stanford.edu/assets/files/hai-stanford-accelerator-for-learning-rfi-response-advancing-ai-in-education.pdf | Stanford HAI / Accelerator for Learning | Federal policy response noting only 35 RCTs on GenAI-in-education exist worldwide. Calls for "research-practice ecosystem" and broadening vision beyond individualised remediation — policy framing, not technical contribution, but signals US Department of Education priorities. |
| 6 | **A Data-Centered Approach to Education AI** (Subramonyam, Tan, Lee, Wang, 2024) | https://hai.stanford.edu/news/data-centered-approach-education-ai | Stanford HAI / GSE | Participatory-AI framework with 10 stakeholder meetings; "Is a Seat at the Table Enough?" (arXiv 2311.05792) shows ML-for-ed tools need teacher/student co-design from data spec stage. |
| 7 | **Simulating Classroom Education with LLM-Empowered Agents (SimClass)** (Zhang et al., NAACL 2025) | https://aclanthology.org/2025.naacl-long.520.pdf | Tsinghua University (MAIC) | Multi-agent classroom: teacher / classmate / manager / assistant agents. Demonstrates emergent group behaviours and Flanders Interaction Analysis fit. Tsinghua MAIC, but matches "AI classroom system" keyword directly. |
| 8 | **Agentic Orchestration for Adaptive Educational Recommendations** (Chaturvedi & Gunawardena, WSDM 2026) | https://genai-personalization.github.io/assets/papers/GenAIRecP2026/NainaChaturvedi_AgenticOrchestration.pdf | Rutgers University | 18+ coordinated agents in 4-tier hierarchy (perception / domain / coordination / strategy). Deployed on 6,000-user platform. Closest published blueprint to a "multi-agent classroom OS." |
| 9 | **AI Agent for Education: Von Neumann Multi-Agent System Framework** (Jiang et al., GCCCE 2024) | https://arxiv.org/html/2501.00083 | East China Normal University | Architectural framework decomposing each education agent into control / logic / storage / I/O units; distinguishes outer human-knowledge circulation vs inner agent-swarm intelligence circulation. |
| 10 | **Leveraging a Multi-Agent LLM-Based System to Educate Teachers in Hate Incidents Management (ARISE)** (Gajewska et al., 2025) | https://arxiv.org/html/2506.23774v1 | Warsaw University of Technology | Multi-agent system for teacher training: persona-modelled students, retrieval-augmented prompting. Application example of multi-agent architecture for teacher PD rather than K-12 student learning. |
| 11 | **Multi-Agent Design: Optimizing Agents with Better Prompts and Topologies (MASS)** (ICLR 2026, arXiv 2502.02533) | https://arxiv.org/abs/2502.02533 | Google Research | Three-stage prompt+topology optimisation. Key finding: "optimise individual agents before composition"; an optimised single agent with Self-Consistency beats a 9-agent SC with default prompts. Direct evidence that naive agent-counting hurts. |

---

## 2. New Systems

| System | Type | Architecture | Relation to MAI / MIRACLE |
|---|---|---|---|
| **MAI (Metacognitive AI agent)** | Proactive single-agent SRL scaffold | Trigger-recognition engine → prompts group to self-regulate; does NOT act on group's behalf. Built on HASRL model. | **This IS the MAI reference system.** Co-evolutionary partner, not controller. |
| **Khanmigo** | LLM tutor + teacher-assistant + district analytics | Single-conversation LLM (GPT-4 class) with structured access to student skill history; Go services; Langfuse for observability; ~100 internal users across 7 product teams. | Closest deployed commercial cousin of MAI at scale; differs in being one-to-one tutor rather than group-regulation agent. ~700K K-12 students in 2024–25. |
| **AutoGen v0.4 / Microsoft Agent Framework** | Multi-agent orchestration SDK | Asynchronous, event-driven; Studio (no-code) + AgentChat (Python) + Core runtime; unified with Semantic Kernel Oct 2025. MCP + A2A protocol support. | Generic substrate — not education-specific, but the orchestration layer a MAI-class system would run on. |
| **MASS (Google)** | Automated MAS design framework | Three-stage interleaved optimisation: local prompt → topology → global prompt. Meta-heuristic search over agent designs. | Indirect: validates that prompt-then-topology optimisation matters; informs how a multi-agent classroom should be designed before deployment. |
| **SimClass (Tsinghua MAIC)** | Multi-agent classroom simulator | Teacher + classmates + manager + assistant agents; emergent group behaviours; validated against Flanders Interactive Analysis. | Direct conceptual sibling of MIRACLE — multi-agent classroom simulation with student peers as agents. |
| **CTAT / Cognitive Tutor (LearnLab)** | Authoring tools for Intelligent Tutoring Systems | Example-tracing tutors; non-programmer authoring. | Oldest line (since 1990s) — what MAI's "proactive" model adds is metacognitive trigger recognition on top of step-level ITS feedback. |
| **OLI / Torus + DataShop (CMU)** | Online course platform + learning analytics warehouse | OLI courses + EDM via DataShop; ~1-week Summer School trains next-gen practitioners. | LA infrastructure layer MAI/MIRACLE-style systems plug into. |
| **CocoRobo SMART Suite** | AI-native classroom OS (commercial) | 5-product suite anchored on SMART principles (Share / Measure / Adaptive / Reconstructive / Team); CocoClass orchestrator with PPT→HTML, PIN co-screen, real-time whole-class diagnosis, embedded agents/workflows (CocoFlow). | **Closest "Multi-Agent Classroom OS" reference deployment.** Explicitly positions AI as team-partner for student thinking, not answer-vendor. MAI could be the metacognition layer on top of CocoClass; MIRACLE the simulator. |
| **Coconote (Quizlet)** | AI note-taker / study-tool consumer app | Audio→notes→study-guide/quiz/flashcards pipeline. | Consumer-side AI study tool; not multi-agent, but defines student expectation baseline. |
| **MAST (Berkeley, Multi-Agent System Traces)** | Benchmark + failure taxonomy | ~200 traces analysed → taxonomy of failure modes: system design, task verification, inter-agent misalignment. | Diagnostic tool — tells you *why* a MAI/MIRACLE multi-agent system might fail in classroom deployment. |

---

## 3. Key Researchers

| Name | Institution | Role in AI Education |
|---|---|---|
| **Sanna Järvelä** | University of Oulu (LET / HI Programme) | PI of Hybrid Intelligence 2023–2028; HASRL originator; co-PI CELLA; PISA 2025 Learning in Digital World expert. |
| **Andy Nguyen** | University of Oulu | Co-author HASRL paper + SSRL learning-analytics follow-ups; bridges LA methodology with regulation theory. |
| **Allyson Hadwin** | University of Oulu (formerly Victoria) | Co-author of HASRL; originator of SRL trigger framework underpinning MAI's design. |
| **Belle Dang** | University of Oulu | First author on AI-Driven LA SSRL study (JLA 2024); emerging in regulation-of-learning analytics. |
| **Justin Edwards** | University of Oulu | Lead developer of MAI proactive agent system. |
| **Marta Sobocinski** | University of Oulu | NRI 2025 grant for "Metacognitive Agent in VR" (Healthcare Education); connects MAI line to extended realities. |
| **Hariharan Subramonyam** | Stanford GSE / HAI Faculty Fellow | Participatory-AI for education; "Is a Seat at the Table Enough?" dataset-spec framework. |
| **Candace Thille** | Stanford Accelerator for Learning | Faculty director, Adult & Workforce Learning; OLI lineage (formerly CMU OLI). |
| **Kenneth Koedinger** | CMU HCII / LearnLab | LearnLab co-founder; Cognitive Tutor / CTAT lineage; ITS-as-research-platform tradition. |
| **John Stamper** | CMU HCII / LearnLab | DataShop / OLI Torus; LearnLab Summer School lead; AI-in-Education seminar series organiser. |
| **Chi Wang** | Microsoft Research AI Frontiers | AutoGen lead; multi-agent-as-conversation paradigm. |
| **Sal Khan** | Khan Academy | Founder; Khanmigo public evangelist; "5 graduate students per teacher" framing. |
| **Walt Wells** | Khan Academy | Staff engineer; built Go-based Langfuse integration for Khanmigo observability. |
| **Zheyuan Zhang / Jifan Yu / Juanzi Li** | Tsinghua MAIC | SimClass authors — multi-agent classroom simulation. |
| **Naina Chaturvedi** | Rutgers University | Agentic Orchestration for Adaptive Educational Recommendations (WSDM 2026). |
| **Bill Faruki** | MindHYVE.ai | Connected Miracle University (US, dropout-prevention nonprofit) to AI literacy work; adjacent ecosystem, not core research. |

---

## 4. System Map (text only)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LAYER 0 — THEORY                                                              │
│                                                                                │
│    Self-Regulated Learning (Zimmerman, 1989)                                   │
│         │                                                                      │
│         ▼                                                                      │
│    Socially Shared Regulation of Learning (SSRL)  ← Järvelä/Hadwin/Winne       │
│         │                                                                      │
│         ▼                                                                      │
│    Hybrid Human-AI Shared Regulation of Learning (HASRL)  ← Järvelä et al 2023 │
│         │   "trigger" concept: situations precipitating need for regulation    │
└─────────┼──────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1 — AGENT (MAI)                                                         │
│                                                                                │
│    MAI = proactive AI agent                                                    │
│      • recognises trigger contexts in collaborative learning                  │
│      • prompts group to raise metacognitive awareness                         │
│      • does NOT regulate FOR the group — raises awareness so THEY self-regulate│
│      • built on trigger framework (Järvelä & Hadwin, 2024)                    │
│                                                                                │
│    Cousin: Khanmigo (1:1 tutor, deployed to 700K K-12 students)               │
└─────────┼──────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  LAYER 2 — MULTI-AGENT ECOSYSTEM (MIRACLE)                                     │
│                                                                                │
│    MIRACLE = multi-agent classroom system (simulator / orchestration layer)    │
│      • teacher agent, peer/student agents, manager agent, domain agents        │
│      • emergent group behaviours among agents                                  │
│      • validated frameworks: Flanders Interaction Analysis, Community of Inquiry│
│                                                                                │
│    Reference implementations:                                                  │
│      SimClass (Tsinghua) — classroom simulator                                 │
│      Agentic Orchestration (Rutgers, 18+ agents, 4-tier) — deployed            │
│      CocoRobo SMART Suite — commercial classroom OS (closest live example)     │
│                                                                                │
│    Substrate: AutoGen v0.4 / Microsoft Agent Framework (orchestration runtime) │
│    Optimisation: MASS (Google) — prompt+topology auto-design                   │
│    Failure diagnosis: MAST (Berkeley) — trace taxonomy                         │
└─────────┼──────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  LAYER 3 — CLASSROOM OS                                                        │
│                                                                                │
│    Multi-Agent Classroom OS                                                    │
│      • in-class orchestration (content · interaction · analysis — CocoClass)   │
│      • learning analytics backbone (DataShop, OLI Torus)                       │
│      • teacher PD & co-pilot (Khanmigo Teachers, ARISE)                        │
│      • consumer study tools (Coconote, Quizlet)                                │
│      • infrastructure: CMU LearnLab, Khanmigo @ scale                         │
└──────────────────────────────────────────────────────────────────────────────┘

Reading direction (bottom-up to design):   SSRL theory → HASRL model → MAI agent
                                            → MIRACLE multi-agent classroom
                                            → deployed Classroom OS.

Reading direction (top-down to deploy):    Classroom OS that emits trace data
                                            → MIRACLE simulator validates new patterns
                                            → MAI agent tuned for regulation
                                            → HASRL framework explains why
                                            → SSRL theory grounds it all.
```

---

## 5. Insights

1. **SSRL → HASRL → MAI is now a coherent three-layer research lineage, not loose concepts.** Järvelä's HASRL model (2023) provided the theory, the trigger framework (Järvelä & Hadwin, 2024) operationalised *when* to intervene, and MAI (Edwards et al., 2025) is the first deployed agent following that specification. Anyone building in this space should cite all three.

2. **Multi-agent is winning the orchestration layer, but naive agent-counting is being actively debunked.** Google's MASS (ICLR 2026) shows an optimised single agent beats a 9-agent ensemble with default prompts. Berkeley's MAST shows ~200 real traces fail in three predictable ways (system design, task verification, inter-agent misalignment). The lesson for MIRACLE-class systems: **optimise agents individually first, then compose** — don't scale agent count.

3. **Microsoft consolidated the substrate (Oct 2025)**. AutoGen v0.4 and Microsoft Agent Framework now unify AutoGen + Semantic Kernel with MCP + A2A protocol support. A MAI-class agent built today should target this runtime rather than rolling custom orchestration.

4. **Commercial deployment is moving faster than RCT evidence.** Khanmigo went from 40K → 700K K-12 students in one school year; Stanford's RFI response notes only 35 GenAI-in-education RCTs exist worldwide. CocoRobo's SMART suite is already in 1,400+ schools across HK/Macau/GBA. The evidence-practice gap is the binding constraint on policy.

5. **CocoRobo's "SMART" framing is the most actionable architectural vocabulary for the Classroom OS layer.** Their decomposition (Share / Measure / Adaptive / Reconstructive / Team) explicitly rejects "AI-as-answer-vendor" in favour of "AI-as-thinking-partner" — which is precisely the philosophical stance MAI's trigger-prompting approach implies. MAI could plausibly be the metacognition layer sitting *on top of* a CocoClass-style orchestrator.

---

**Note on path:** Originally requested `/research-mvp/latest-report.md`; that path is root-owned and rejected with `Permission denied`. Delivered at `/home/conanxin/research-mvp/latest-report.md` instead. Move or symlink if root path is required.