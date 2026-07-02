// app.js — renders the AI Education System Map static page.
// Pure ES2017+, no build step. Fetches 6 JSON files + 1 weekly snapshot.

const DATA = {
    papers: "data/papers.json",
    systems: "data/systems.json",
    people: "data/people.json",
    tech: "data/tech-stack.json",
    timeline: "data/timeline.json",
    sources: "data/sources.json",
    weekly: "data/weekly/latest.json",
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

async function loadJson(path) {
    const r = await fetch(path, { cache: "no-store" });
    if (!r.ok) throw new Error(`${path} -> ${r.status}`);
    return r.json();
}

function el(tag, attrs = {}, children = []) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
        if (k === "class") node.className = v;
        else if (k === "html") node.innerHTML = v;
        else if (k.startsWith("data-")) node.setAttribute(k, v);
        else node[k] = v;
    }
    for (const c of [].concat(children)) {
        if (c == null) continue;
        node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    }
    return node;
}

function escapeHtml(s) {
    return String(s ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function linkify(text) {
    return escapeHtml(text).replace(
        /(https?:\/\/[^\s)]+)/g,
        '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
    );
}

function fmtDate(iso) {
    if (!iso) return "—";
    try {
        const d = new Date(iso);
        return d.toISOString().replace("T", " ").replace(/\..+$/, " UTC");
    } catch (_) { return iso; }
}

// ---------------------------------------------------------------------------
// Overview cards
// ---------------------------------------------------------------------------
const OVERVIEW_CARDS = [
    { tag: "Theory", title: "HASRL → MAI is the theoretical main line",
      body: "Järvelä et al.'s HASRL model (2023) + trigger framework + MAI proactive agent (Edwards et al., 2025) form a coherent three-layer lineage from SSRL theory to deployed system." },
    { tag: "System", title: "MIRACLE is the multi-agent classroom regulator",
      body: "On top of MAI's single-agent regulation primitives, MIRACLE adds teacher / peer / manager agents for emergent classroom orchestration (SimClass-style validation)." },
    { tag: "Caution", title: "MASS: don't blindly add agents",
      body: "Google's MASS (ICLR 2026) shows an optimised single agent beats a 9-agent ensemble with default prompts. Optimise agents individually first, then compose." },
    { tag: "Substrate", title: "Microsoft Agent Framework is the substrate",
      body: "AutoGen + Semantic Kernel unified Oct 2025 with MCP + A2A support. A MAI-class agent built today should target this runtime." },
    { tag: "Evidence", title: "Khanmigo scale vs RCT gap",
      body: "Khanmigo: 40K → 700K K-12 students in one school year. Stanford's RFI notes only 35 GenAI-in-ed RCTs exist worldwide. Deployment is racing ahead of evidence." },
    { tag: "Deployment", title: "CocoRobo SMART = live Multi-Agent Classroom OS",
      body: "CocoRobo SMART Suite deployed in 1,400+ schools across HK / Macau / GBA; 5-product orchestration (Teach / Learn / Assess / Manage + Cloud) is the closest live reference for a multi-agent classroom OS." },
];

function renderOverview() {
    const host = $("#overview-cards");
    host.innerHTML = "";
    for (const c of OVERVIEW_CARDS) {
        host.appendChild(el("div", { class: "card" }, [
            el("span", { class: "tag" }, c.tag),
            el("h3", {}, c.title),
            el("p", {}, c.body),
        ]));
    }
}

// ---------------------------------------------------------------------------
// System Map (Mermaid)
// ---------------------------------------------------------------------------
function renderSystemMap() {
    const host = $("#system-map");
    host.innerHTML = "";
    const def = `flowchart LR
    classDef theory fill:#1d1147,stroke:#7c5cff,color:#e6edf7;
    classDef agent fill:#0e2a4d,stroke:#4ea1ff,color:#e6edf7;
    classDef eco fill:#0c3d2c,stroke:#4ade80,color:#e6edf7;
    classDef sub fill:#3d2c0a,stroke:#facc15,color:#e6edf7;
    classDef dep fill:#3a1a0a,stroke:#ff8c5a,color:#e6edf7;

    SSRL["SSRL<br/>Socially Shared Regulation"]:::theory
    HASRL["HASRL<br/>Hybrid Human-AI SRL<br/>+ trigger concept"]:::theory
    MAI["MAI<br/>Proactive Metacognitive Agent"]:::agent
    Coconote["CocoNote<br/>consumer study"]:::eco
    MIRACLE["MIRACLE<br/>Multi-Agent Classroom"]:::eco
    MACOS["Multi-Agent Classroom OS<br/>(deployed)"]:::dep

    SSRL --> HASRL --> MAI --> MIRACLE --> MACOS
    Coconote -. companion .-> MIRACLE

    CTAT["CMU LearnLab<br/>CTAT / Cognitive Tutor"]:::eco
    Tutor["Khanmigo<br/>AI Tutor"]:::dep
    AutoGen["AutoGen / MS<br/>Agent Framework"]:::sub
    MASS["MASS<br/>multi-agent design"]:::sub
    SimClass["SimClass<br/>multi-agent simulator"]:::eco
    CocoRobo["CocoRobo SMART<br/>classroom OS"]:::dep

    CTAT --> MACOS
    Tutor --> MACOS
    AutoGen --> MIRACLE
    MASS --> MIRACLE
    SimClass -. validates .-> MIRACLE
    CocoRobo --> MACOS
`;
    host.innerHTML = def;
    host.classList.add("mermaid");
}

async function initMermaid() {
    if (window.mermaid) return window.mermaid;
    await new Promise((res, rej) => {
        const s = document.createElement("script");
        s.src = "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js";
        s.onload = res;
        s.onerror = rej;
        document.head.appendChild(s);
    });
    window.mermaid.initialize({ startOnLoad: false, theme: "dark", securityLevel: "loose" });
    return window.mermaid;
}

// ---------------------------------------------------------------------------
// Paper network (textual graph + table)
// ---------------------------------------------------------------------------
function renderPapers(papers) {
    const list = $("#papers-list");
    list.innerHTML = "";
    for (const p of papers) {
        list.appendChild(el("div", { class: "paper" }, [
            el("div", { class: "title" }, [
                p.url
                    ? el("a", { href: p.url, target: "_blank", rel: "noopener noreferrer" }, p.title)
                    : document.createTextNode(p.title),
            ]),
            el("div", { class: "inst" }, p.institution || ""),
            el("div", { class: "sum", html: linkify(p.summary || "") }),
        ]));
    }
}

// ---------------------------------------------------------------------------
// People graph
// ---------------------------------------------------------------------------
function renderPeople(people) {
    const grid = $("#people-grid");
    grid.innerHTML = "";
    for (const person of people) {
        grid.appendChild(el("div", { class: "person" }, [
            el("div", { class: "name" }, person.name),
            el("div", { class: "inst" }, person.institution || ""),
            el("div", { class: "role" }, person.role || ""),
        ]));
    }
}

// ---------------------------------------------------------------------------
// Tech stack table
// ---------------------------------------------------------------------------
const TECH_COLS = [
    { key: "system", label: "System" },
    { key: "institution", label: "Institution" },
    { key: "type", label: "Type" },
    { key: "agent_architecture", label: "Agent architecture" },
    { key: "data_inputs", label: "Data inputs" },
    { key: "regulation_mechanism", label: "Regulation mechanism" },
    { key: "multimodal_support", label: "Multimodal" },
    { key: "open_source_status", label: "Open source" },
    { key: "relation_to_mai_miracle", label: "Relation to MAI / MIRACLE" },
];

function renderTechStack(rows) {
    const host = $("#tech-stack");
    host.innerHTML = "";
    const wrap = el("div", { class: "table-scroll" });
    const tbl = el("table", { class: "data" });
    const thead = el("thead");
    const trh = el("tr");
    for (const c of TECH_COLS) trh.appendChild(el("th", {}, c.label));
    thead.appendChild(trh);
    tbl.appendChild(thead);
    const tbody = el("tbody");
    for (const r of rows) {
        const tr = el("tr");
        for (const c of TECH_COLS) {
            tr.appendChild(el("td", { class: c.key === "system" ? "mono" : "" }, r[c.key] || "—"));
        }
        tbody.appendChild(tr);
    }
    tbl.appendChild(tbody);
    wrap.appendChild(tbl);
    host.appendChild(wrap);
}

// ---------------------------------------------------------------------------
// Timeline
// ---------------------------------------------------------------------------
function renderTimeline(items) {
    const host = $("#timeline");
    host.innerHTML = "";
    items.sort((a, b) => a.year - b.year);
    for (const it of items) {
        host.appendChild(el("div", { class: "tl-item", "data-layer": it.layer || "theory" }, [
            el("div", { class: "tl-year" }, String(it.year)),
            el("div", { class: "tl-dot" }),
            el("div", { class: "tl-label" }, it.label || ""),
            el("div", { class: "tl-note" }, it.note || ""),
        ]));
    }
}

// ---------------------------------------------------------------------------
// Weekly
// ---------------------------------------------------------------------------
function renderWeekly(weekly) {
    const host = $("#weekly");
    host.innerHTML = "";
    host.appendChild(el("div", { class: "stats" }, [
        el("div", { class: "stat" }, [el("strong", {}, "Updated:"), fmtDate(weekly.updated_at)]),
        el("div", { class: "stat" }, [el("strong", {}, "Papers:"), String(weekly.new_papers ?? "—")]),
        el("div", { class: "stat" }, [el("strong", {}, "Systems:"), String(weekly.new_systems ?? "—")]),
        el("div", { class: "stat" }, [el("strong", {}, "People:"), String(weekly.new_people ?? "—")]),
    ]));

    if (Array.isArray(weekly.highlights) && weekly.highlights.length) {
        const h = el("div", {}, [el("h3", { html: "Highlights" })]);
        const ul = el("ul");
        for (const line of weekly.highlights) ul.appendChild(el("li", {}, line));
        host.appendChild(h);
        host.appendChild(ul);
    }
    if (Array.isArray(weekly.insights) && weekly.insights.length) {
        const h = el("div", {}, [el("h3", { html: "Insights from seed report" })]);
        const ul = el("ul");
        for (const line of weekly.insights) ul.appendChild(el("li", {}, line));
        host.appendChild(h);
        host.appendChild(ul);
    }
}

// ---------------------------------------------------------------------------
// Source manifest footer
// ---------------------------------------------------------------------------
function renderFooterSources(sources, errors) {
    const host = $("#footer-sources");
    host.innerHTML = "";
    host.appendChild(el("div", { html: `<strong>Tracked keywords</strong>: ${sources.keywords.map(escapeHtml).join(" · ")}` }));
    host.appendChild(el("div", { html: `<strong>Institutions</strong>: ${sources.institutions.map(escapeHtml).join(" · ")}` }));
    if (errors.length) {
        host.appendChild(el("div", { html: `<strong style="color:var(--warn)">Data load warnings</strong>: ${errors.map(escapeHtml).join("; ")}` }));
    }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
    renderOverview();
    renderSystemMap();

    const results = await Promise.allSettled([
        loadJson(DATA.papers),
        loadJson(DATA.systems),
        loadJson(DATA.people),
        loadJson(DATA.tech),
        loadJson(DATA.timeline),
        loadJson(DATA.sources),
        loadJson(DATA.weekly),
    ]);
    const [papers, systems, people, tech, timeline, sources, weekly] = results.map(r =>
        r.status === "fulfilled" ? r.value : null
    );
    const errors = results.map((r, i) =>
        r.status === "rejected" ? `${Object.values(DATA)[i]} (${r.reason.message})` : null
    ).filter(Boolean);

    if (papers) renderPapers(papers);
    if (people) renderPeople(people);
    if (tech) renderTechStack(tech);
    if (timeline) renderTimeline(timeline);
    if (weekly) renderWeekly(weekly);
    if (sources) renderFooterSources(sources, errors);

    // Initialise Mermaid AFTER all data is on the page so theme is consistent.
    try {
        const m = await initMermaid();
        await m.run({ nodes: document.querySelectorAll(".mermaid") });
    } catch (e) {
        const host = $("#system-map");
        if (host) host.innerHTML = `<pre style="color:var(--warn)">Mermaid load failed: ${escapeHtml(e.message)}</pre>`;
    }
}

document.addEventListener("DOMContentLoaded", main);