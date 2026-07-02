// app.js — renders the AI Education System Map static page (v1.3).
// Pure ES2017+, no build step. Fetches ONE aggregated summary file
// (dashboard-summary.json) and renders 6 modules.

const DATA = {
    summary: "data/dashboard-summary.json",
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
        if (v == null) continue;
        if (k === "class") node.className = v;
        else if (k === "html") node.innerHTML = v;
        else if (k === "text") node.textContent = v;
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
        if (isNaN(d.getTime())) return iso;
        return d.toISOString().replace("T", " ").replace(/\..+$/, " UTC");
    } catch (_) { return iso; }
}

function setText(sel, value) {
    const node = $(sel);
    if (node) node.textContent = value == null ? "—" : String(value);
}

function showModuleError(sel, message) {
    const node = $(sel);
    if (!node) return;
    const orig = node.querySelector("h2");
    node.innerHTML = "";
    if (orig) node.appendChild(orig);
    node.appendChild(el("div", { class: "module-error", html: escapeHtml(message) }));
}

// ---------------------------------------------------------------------------
// Badge mapping (system -> category badge labels)
// ---------------------------------------------------------------------------
const SYSTEM_BADGES = {
    "MAI (Metacognitive AI agent)": ["SSRL / HASRL", "Research Prototype"],
    "Khanmigo": ["Tutor", "Product"],
    "AutoGen v0.4 / Microsoft Agent Framework": ["Infrastructure", "Multi-Agent"],
    "MASS (Google)": ["Infrastructure"],
    "SimClass (Tsinghua MAIC)": ["Multi-Agent", "Research Prototype"],
    "CTAT / Cognitive Tutor (LearnLab)": ["Tutor", "Infrastructure"],
    "OLI / Torus + DataShop (CMU)": ["Infrastructure"],
    "CocoRobo SMART Suite": ["Multi-Agent", "Classroom OS", "Product"],
    "Coconote (Quizlet)": ["Product"],
    "MAST (Berkeley, Multi-Agent System Traces)": ["Research Prototype"],
};

function badgeNode(label) {
    return el("span", { class: `badge badge-${label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}` }, label);
}

// ---------------------------------------------------------------------------
// Module 1: This Week
// ---------------------------------------------------------------------------
function renderThisWeek(s) {
    setText("#this-week-tag", s.latest_week_tag || "—");
    setText('[data-stat="new_papers"]', s.this_week.new_papers ?? "—");
    setText('[data-stat="new_systems"]', s.this_week.new_systems ?? "—");
    setText('[data-stat="new_people"]', s.this_week.new_people ?? "—");
    setText('[data-stat="active_sources"]', s.totals.active_sources ?? "—");
    setText('[data-stat="stable_sources"]', s.totals.stable_sources ?? "—");

    // Fallback status
    const fb = s.this_week.fallback_status || {};
    const fbText = fb && Object.keys(fb).length
        ? `ran=${fb.ran ?? "?"} · queries=${fb.queries ?? "?"} · hits=${fb.hits ?? "?"}` +
          (Array.isArray(fb.errors) && fb.errors.length ? ` · errors=${fb.errors.length}` : "")
        : "—";
    setText("#this-week-fallback [data-fb]", fbText);

    // Links
    const links = $("#this-week-links");
    links.innerHTML = "";
    if (s.latest_report_url) {
        links.appendChild(el("a", {
            href: s.latest_report_url, target: "_blank", rel: "noopener noreferrer",
            class: "weekly-link",
        }, "View weekly report →"));
    }
    if (s.github_report_path) {
        links.appendChild(el("a", {
            href: s.github_report_path, target: "_blank", rel: "noopener noreferrer",
            class: "weekly-link",
        }, "View on GitHub →"));
    }
}

// ---------------------------------------------------------------------------
// Module 2: Research Lineage — Mermaid handled by initMermaid; nothing here.
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Module 3: System Cards with filter chips
// ---------------------------------------------------------------------------
const SYSTEM_FILTERS = [
    "All",
    "Research Prototype",
    "Product",
    "Infrastructure",
    "Tutor",
    "Classroom OS",
    "Multi-Agent",
    "SSRL / HASRL",
];

function renderSystemCards(s) {
    const cards = s.system_cards || [];
    setText("#sys-count", `${cards.length} systems`);

    const chipsHost = $("#system-filter-chips");
    chipsHost.innerHTML = "";
    for (const f of SYSTEM_FILTERS) {
        chipsHost.appendChild(el("button", {
            class: "chip" + (f === "All" ? " chip-active" : ""),
            "data-filter": f,
            type: "button",
        }, f));
    }
    chipsHost.addEventListener("click", (ev) => {
        const target = ev.target;
        if (!target.classList || !target.classList.contains("chip")) return;
        $$(".chip").forEach(c => c.classList.remove("chip-active"));
        target.classList.add("chip-active");
        const f = target.getAttribute("data-filter");
        applySystemFilter(f);
    });

    const grid = $("#system-cards-grid");
    grid.innerHTML = "";
    for (const c of cards) {
        grid.appendChild(buildSystemCard(c));
    }
}

function applySystemFilter(filter) {
    const cards = $$(".sys-card");
    for (const card of cards) {
        const cats = (card.getAttribute("data-cats") || "").split(",").filter(Boolean);
        if (filter === "All" || cats.includes(filter)) {
            card.style.display = "";
        } else {
            card.style.display = "none";
        }
    }
}

function buildSystemCard(c) {
    const badges = (c.categories || []).map(badgeNode);
    const card = el("article", {
        class: "sys-card",
        "data-cats": (c.categories || []).join(","),
    }, [
        el("header", { class: "sys-card-header" }, [
            el("h3", { class: "sys-name" }, c.system || "(unnamed)"),
            el("div", { class: "sys-badges" }, badges),
        ]),
        el("div", { class: "sys-row" }, [
            el("span", { class: "sys-key" }, "Institution"),
            el("span", { class: "sys-val" }, c.institution || "—"),
        ]),
        el("div", { class: "sys-row" }, [
            el("span", { class: "sys-key" }, "Type"),
            el("span", { class: "sys-val" }, c.type || "—"),
        ]),
        el("div", { class: "sys-row" }, [
            el("span", { class: "sys-key" }, "Agent architecture"),
            el("span", { class: "sys-val" }, c.agent_architecture || "—"),
        ]),
        el("div", { class: "sys-row" }, [
            el("span", { class: "sys-key" }, "Open source"),
            el("span", { class: "sys-val" }, c.open_source_status || "—"),
        ]),
        el("div", { class: "sys-row" }, [
            el("span", { class: "sys-key" }, "Relation to MAI / MIRACLE"),
            el("span", { class: "sys-val sys-rel" }, c.relation_to_mai_miracle || "—"),
        ]),
    ]);
    if (c.source_url) {
        card.appendChild(el("footer", { class: "sys-card-footer" }, [
            el("a", {
                href: c.source_url, target: "_blank", rel: "noopener noreferrer",
                class: "sys-source-link",
            }, "Source →"),
        ]));
    }
    return card;
}

// ---------------------------------------------------------------------------
// Module 4: Paper Network Summary
// ---------------------------------------------------------------------------
function renderPaperGroups(s) {
    const groups = s.paper_groups || {};
    const total = Object.values(groups).reduce((sum, arr) => sum + arr.length, 0);
    setText("#paper-count", `${total} papers · ${Object.keys(groups).length} groups`);

    const body = $("#paper-groups-body");
    body.innerHTML = "";

    // Stable display order
    const order = [
        "Theory papers",
        "MAI lineage papers",
        "MIRACLE / CocoNote papers",
        "Agent infrastructure papers",
        "Evidence / policy papers",
    ];
    const seen = new Set();
    for (const g of order) {
        if (groups[g]) {
            body.appendChild(buildPaperGroup(g, groups[g]));
            seen.add(g);
        }
    }
    // Anything not in the canonical order
    for (const g of Object.keys(groups)) {
        if (!seen.has(g)) {
            body.appendChild(buildPaperGroup(g, groups[g]));
        }
    }
}

function buildPaperGroup(groupName, papers) {
    const wrap = el("section", { class: "paper-group" });
    wrap.appendChild(el("h3", { class: "paper-group-title" }, `${groupName} (${papers.length})`));
    const list = el("ul", { class: "paper-list" });
    for (const p of papers) {
        const li = el("li", { class: "paper-item" });
        const titleNode = p.url
            ? el("a", { href: p.url, target: "_blank", rel: "noopener noreferrer" }, p.title || "(untitled)")
            : el("span", {}, p.title || "(untitled)");
        li.appendChild(titleNode);
        const meta = [];
        if (p.year) meta.push(String(p.year));
        if (p.related_system && p.related_system !== p.title) meta.push(p.related_system);
        if (meta.length) {
            li.appendChild(el("div", { class: "paper-meta", html: meta.map(escapeHtml).join(" · ") }));
        }
        list.appendChild(li);
    }
    wrap.appendChild(list);
    return wrap;
}

// ---------------------------------------------------------------------------
// Module 5: People & Institutions
// ---------------------------------------------------------------------------
function renderPeopleGroups(s) {
    const groups = s.people_groups || {};
    const total = Object.values(groups).reduce((sum, arr) => sum + arr.length, 0);
    setText("#people-count", `${total} people · ${Object.keys(groups).length} institutions`);

    const body = $("#people-groups-body");
    body.innerHTML = "";
    for (const [g, people] of Object.entries(groups)) {
        body.appendChild(buildPeopleGroup(g, people));
    }
}

function buildPeopleGroup(groupName, people) {
    const wrap = el("section", { class: "people-group" });
    wrap.appendChild(el("h3", { class: "people-group-title" }, `${groupName} (${people.length})`));
    const grid = el("div", { class: "people-grid" });
    if (!people.length) {
        grid.appendChild(el("div", { class: "empty-note" }, "No people tracked in this group yet."));
    }
    for (const p of people) {
        const card = el("article", { class: "person-card" });
        const nameNode = p.source_url
            ? el("a", { href: p.source_url, target: "_blank", rel: "noopener noreferrer", class: "person-name" }, p.name || "(unnamed)")
            : el("span", { class: "person-name" }, p.name || "(unnamed)");
        card.appendChild(nameNode);
        if (p.institution) card.appendChild(el("div", { class: "person-inst" }, p.institution));
        if (p.role) card.appendChild(el("div", { class: "person-role" }, p.role));
        grid.appendChild(card);
    }
    wrap.appendChild(grid);
    return wrap;
}

// ---------------------------------------------------------------------------
// Module 6: Source Health
// ---------------------------------------------------------------------------
function renderSourceHealth(s) {
    const h = s.source_health || {};
    setText('[data-stat="stable_sources"]', h.stable_sources ?? "—");
    setText('[data-stat="active_sources"]', h.active_sources ?? "—");
    setText('[data-stat="source_errors_count"]', h.source_errors_count ?? "—");

    const fb = h.fallback_status || {};
    const fbText = fb && Object.keys(fb).length
        ? `ran=${fb.ran ?? "?"} · queries=${fb.queries ?? "?"} · hits=${fb.hits ?? "?"}` +
          (Array.isArray(fb.errors) && fb.errors.length ? ` · errors=${fb.errors.length}` : "")
        : "—";
    setText("#source-health-fallback [data-fb]", fbText);

    // Candidates by source (top 20)
    const cbs = h.candidates_by_source || {};
    const cbsEntries = Object.entries(cbs).slice(0, 20);
    const cbsText = cbsEntries.length
        ? cbsEntries.map(([k, urls]) => `${k} (${urls.length})\n  ${urls.slice(0, 3).join("\n  ")}`).join("\n\n")
        : "No source returned candidates this run.";
    setText("#source-candidates-pre", cbsText);

    const errs = h.source_errors || {};
    const errsText = Object.keys(errs).length
        ? Object.entries(errs).map(([k, v]) => `${k}: ${v}`).join("\n")
        : "No source errors.";
    setText("#source-errors-pre", errsText);
}

// ---------------------------------------------------------------------------
// Footer (totals + last updated)
// ---------------------------------------------------------------------------
function renderFooter(s) {
    setText("#meta-data-count",
        `${s.totals.papers} papers · ${s.totals.systems} systems · ${s.totals.people} people · last update ${fmtDate(s.last_updated)}`);

    const footer = $("#footer-sources");
    if (footer) {
        footer.innerHTML = "";
        footer.appendChild(el("div", {
            html: `<strong>Tracked keywords</strong>: ${(s.system_cards ? "" : "")}SSRL · HASRL · MAI · MIRACLE · multi-agent · learning analytics · Khanmigo · AutoGen · MASS · Cognitive Tutor · LearnLab · Khan Academy · CocoRobo · AI classroom OS`,
        }));
        footer.appendChild(el("div", {
            html: `<strong>Last weekly run</strong>: ${escapeHtml(fmtDate(s.last_updated))}`,
        }));
    }
}

// ---------------------------------------------------------------------------
// Mermaid init
// ---------------------------------------------------------------------------
async function initMermaid() {
    if (window.mermaid) return window.mermaid;
    await new Promise((res, rej) => {
        const s = document.createElement("script");
        s.src = "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js";
        s.onload = res;
        s.onerror = rej;
        document.head.appendChild(s);
    });
    window.mermaid.initialize({
        startOnLoad: false,
        theme: "dark",
        securityLevel: "loose",
        flowchart: { htmlLabels: true, curve: "basis" },
    });
    return window.mermaid;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
    let summary;
    try {
        summary = await loadJson(DATA.summary);
    } catch (e) {
        showModuleError("#this-week", `Failed to load dashboard summary: ${e.message}. The site may still be rebuilding.`);
        return;
    }

    try { renderThisWeek(summary); } catch (e) { showModuleError("#this-week", e.message); }
    // Module 2 (lineage) is Mermaid-only — handled in main.
    try { renderSystemCards(summary); } catch (e) { showModuleError("#system-cards", e.message); }
    try { renderPaperGroups(summary); } catch (e) { showModuleError("#paper-groups", e.message); }
    try { renderPeopleGroups(summary); } catch (e) { showModuleError("#people-groups", e.message); }
    try { renderSourceHealth(summary); } catch (e) { showModuleError("#source-health", e.message); }
    try { renderFooter(summary); } catch (_) { /* non-critical */ }

    // Initialise Mermaid AFTER all data is on the page so theme is consistent.
    try {
        const m = await initMermaid();
        await m.run({ nodes: document.querySelectorAll(".mermaid") });
    } catch (e) {
        const host = $("#lineage-mermaid");
        if (host) host.innerHTML = `<pre class="module-error">Mermaid load failed: ${escapeHtml(e.message)}</pre>`;
    }
}

document.addEventListener("DOMContentLoaded", main);