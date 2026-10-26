// app.js — renders the AI Education System Map static page (v1.3.3, zh-CN UI).
// Pure ES2017+, no build step. Fetches ONE aggregated summary file
// (dashboard-summary.json) and renders 7 modules.
// JSON schema stays English (matches the watcher / builder output). Display
// labels, group titles, badges and filter chips are localised to zh-CN via
// lookup tables below.

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
        else if (k.startsWith("data-") || k.startsWith("aria-")) node.setAttribute(k, v);
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

function safeExternalHref(value) {
    try {
        const url = new URL(value, window.location.href);
        return ["https:", "http:"].includes(url.protocol) ? url.href : "";
    } catch (_) {
        return "";
    }
}

function renderHero(s) {
    const totals = s.totals || {};
    for (const key of ["papers", "systems", "people", "references"]) {
        setText('[data-hero="' + key + '"]', totals[key] ?? "—");
    }
    const latest = s.source_health?.last_run || s.last_updated;
    setText("#hero-last-updated", latest ? fmtDate(latest) : "尚无归档时间");
}

function renderFeaturedReading(s) {
    const target = $("#featured-reads");
    if (!target) return;
    target.innerHTML = "";
    const papers = Object.values(s.paper_groups || {}).flat();
    const selections = [
        {
            name: "01 / HUMAN–AI CO-REGULATION",
            pattern: /Human and artificial intelligence collaboration/i,
            question: "人机可以怎样共同参与合作学习的调节？"
        },
        {
            name: "02 / CLASSROOM SIMULATION",
            pattern: /Simulating Classroom Education/i,
            question: "多智能体模拟能为课堂研究提供什么实验入口？"
        },
        {
            name: "03 / AGENT SYSTEM DESIGN",
            pattern: /Multi-Agent Design: Optimizing/i,
            question: "提示与协作拓扑应如何共同设计？"
        }
    ];
    for (const item of selections) {
        const match = papers.find(paper => item.pattern.test(paper.title || ""));
        if (!match) continue;
        const card = el("article", {class: "featured-card"});
        card.appendChild(el("span", {class:"featured-tag"},item.name));
        card.appendChild(el("h4",{},item.question));
        const href = safeExternalHref(match.url);
        if (href) {
            card.appendChild(el("a", {
                href, target:"_blank",rel:"noopener noreferrer"
            },match.title + " ↗"));
        } else {
            card.appendChild(el("p",{},match.title));
        }
        target.appendChild(card);
    }
}

function renderTimeline(s) {
    const host = $("#timeline-grid");
    if (!host) return;
    host.innerHTML = "";
    const events = Array.isArray(s.timeline) ? s.timeline : [];
    setText("#timeline-count", String(events.length) + " 个记录");
    const ordered = [...events].sort((a, b) => Number(a.year) - Number(b.year));
    for (const event of ordered) {
        const node = el("article", {class: "timeline-entry",
            "data-layer": String(event.layer || "other")});
        node.appendChild(el("span", {class: "timeline-year"}, String(event.year ?? "—")));
        node.appendChild(el("h4", {}, String(event.label || "未命名节点")));
        if (event.note) node.appendChild(el("p", {}, String(event.note)));
        host.appendChild(node);
    }
}

function enableSectionNavigation() {
    const nav = $(".nav-inner");
    if (!nav || !("IntersectionObserver" in window)) return;
    const links = [...nav.querySelectorAll('a[href^="#"]')];
    const targets = links.map(link => document.querySelector(link.getAttribute("href")))
                         .filter(Boolean);
    const observer = new IntersectionObserver(entries => {
        const visible = entries.filter(entry => entry.isIntersecting)
                               .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (!visible.length) return;
        const id = visible[0].target.id;
        for (const link of links) {
            if (link.getAttribute("href") === "#" + id) {
                link.setAttribute("aria-current", "location");
            } else {
                link.removeAttribute("aria-current");
            }
        }
    }, {rootMargin: "-90px 0px -65% 0px", threshold: 0});
    for (const target of targets) observer.observe(target);
}

function containsSearch(haystack, query) {
    return String(haystack || "").toLocaleLowerCase()
                 .includes(String(query || "").trim().toLocaleLowerCase());
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
// Display-side translations (zh-CN). JSON data values remain untouched.
// ---------------------------------------------------------------------------
const T = {
    // System card field labels
    "Institution": "所属机构",
    "Type": "类型",
    "Agent architecture": "智能体架构",
    "Open source": "开源状态",
    "Relation to MAI / MIRACLE": "与 MAI / MIRACLE 的关系",

    // Links / actions
    "Source": "来源",
    "Source link": "来源链接",
    "View weekly report": "查看本周报告",
    "View on GitHub": "在 GitHub 查看",

    // Footer / meta
    "papers": "论文",
    "references": "研究资料",
    "systems": "系统",
    "people": "人物",
    "last update": "最后更新",
    "entries": "条记录",
    "Tracked keywords": "追踪关键词",
    "Last weekly run": "上次每周运行",

    // Source-health panels
    "No source returned candidates this run.": "本次运行中无来源返回候选。",
    "No source errors.": "无来源错误。",
    "No people tracked in this group yet.": "本组暂未追踪人物。",

    // System card count suffix
    "systems suffix": "个系统",
};

// Paper group titles — JSON keys are English, render Chinese
const PAPER_GROUP_TITLES = {
    "Theory papers": "理论基础",
    "MAI lineage papers": "MAI 研究脉络",
    "MIRACLE / CocoNote papers": "MIRACLE / CocoNote",
    "Agent infrastructure papers": "多智能体基础设施",
    "Evidence / policy papers": "证据与政策",
};

// People group titles — JSON keys are institution names, render Chinese where
// useful. Keep the English original name in parentheses when helpful.
const PEOPLE_GROUP_TITLES = {
    "Oulu": "奥卢大学 (Oulu) / LET / HI",
    "Stanford": "Stanford / HAI",
    "CMU": "CMU LearnLab",
    "Microsoft+Google": "Microsoft / Google",
    "Khan Academy": "Khan Academy",
    "CocoRobo·MIRACLE": "CocoRobo / MIRACLE",
    "Other": "其他",
    "Other research": "其他研究机构",
};

// Badge labels (JS literals used in SYSTEM_BADGES below) — these double as
// filter chip values, so both surfaces share this map.
const BADGE_LABELS = {
    "All": "全部",
    "Research Prototype": "研究原型",
    "Product": "产品",
    "Infrastructure": "基础设施",
    "Tutor": "AI 导师",
    "Classroom OS": "课堂 OS",
    "Multi-Agent": "多智能体",
    "SSRL / HASRL": "SSRL / HASRL",
};

// Localised filter chips (rendered order preserved)
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

// ---------------------------------------------------------------------------
// Badge mapping (system -> category badge labels)
// Badge values are JSON keys (must match system_cards[i].categories).
// Display label is looked up via BADGE_LABELS.
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
    const display = BADGE_LABELS[label] || label;
    return el("span", { class: `badge badge-${label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}` }, display);
}

// ---------------------------------------------------------------------------
// Module 1: 本周更新
// ---------------------------------------------------------------------------
function renderThisWeek(s) {
    setText("#this-week-tag", s.latest_week_tag || "—");
    setText('[data-stat="new_papers"]', s.this_week.new_papers ?? "—");
    setText('[data-stat="new_references"]', s.this_week.new_references ?? 0);
    setText('[data-stat="new_systems"]', s.this_week.new_systems ?? "—");
    setText('[data-stat="new_people"]', s.this_week.new_people ?? "—");
    setText('[data-stat="active_sources"]', s.totals.active_sources ?? "—");
    setText('[data-stat="stable_sources"]', s.totals.stable_sources ?? "—");

    // Fallback status
    const fb = s.this_week.fallback_status || {};
    const fbText = fb && Object.keys(fb).length
        ? `运行=${fb.ran ?? "?"} · 查询=${fb.queries ?? "?"} · 命中=${fb.hits ?? "?"}` +
          (Array.isArray(fb.errors) && fb.errors.length ? ` · 错误=${fb.errors.length}` : "")
        : "—";
    setText("#this-week-fallback [data-fb]", fbText);

    // Links
    const links = $("#this-week-links");
    links.innerHTML = "";
    if (s.latest_report_url) {
        links.appendChild(el("a", {
            href: s.latest_report_url, target: "_blank", rel: "noopener noreferrer",
            class: "weekly-link",
        }, `${T["View weekly report"]} →`));
    }
    if (s.github_report_path) {
        links.appendChild(el("a", {
            href: s.github_report_path, target: "_blank", rel: "noopener noreferrer",
            class: "weekly-link",
        }, `${T["View on GitHub"]} →`));
    }
}

// ---------------------------------------------------------------------------
// Module 2: 研究脉络 — Mermaid handled by initMermaid; nothing here.
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Module 3: 系统卡片 with filter chips
// ---------------------------------------------------------------------------
function renderSystemCards(s) {
    const cards = s.system_cards || [];
    setText("#sys-count", `${cards.length} ${T["systems suffix"]}`);

    const chipsHost = $("#system-filter-chips");
    chipsHost.innerHTML = "";
    for (const f of SYSTEM_FILTERS) {
        chipsHost.appendChild(el("button", {
            class: "chip" + (f === "All" ? " chip-active" : ""),
            "data-filter": f,
            "aria-pressed": f === "All" ? "true" : "false",
            type: "button",
        }, BADGE_LABELS[f] || f));
    }
    chipsHost.addEventListener("click", (ev) => {
        const target = ev.target;
        if (!target.classList || !target.classList.contains("chip")) return;
        chipsHost.querySelectorAll(".chip").forEach(c => {
            c.classList.remove("chip-active");
            c.setAttribute("aria-pressed", "false");
        });
        target.classList.add("chip-active");
        target.setAttribute("aria-pressed", "true");
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
    const cards = $$("#system-cards-grid .sys-card");
    let visible = 0;
    for (const card of cards) {
        const cats = (card.getAttribute("data-cats") || "").split(",").filter(Boolean);
        const match = filter === "All" || cats.includes(filter);
        card.hidden = !match;
        if (match) visible++;
    }
    const empty = $("#system-empty");
    if (empty) empty.hidden = visible > 0;
}

function buildSystemCard(c) {
    const badges = (c.categories || []).map(badgeNode);
    const card = el("article", {class: "sys-card",
        "data-cats": (c.categories || []).join(",")});
    const header = el("header", {class: "sys-card-header"}, [
        el("h3", {class: "sys-name"}, c.system || "(未命名系统)"),
        el("div", {class: "sys-badges"}, badges)
    ]);
    card.appendChild(header);
    if (c.type) card.appendChild(el("p", {class:"sys-type"}, c.type));
    if (c.relation_to_mai_miracle) card.appendChild(
        el("p", {class: "sys-context"}, c.relation_to_mai_miracle));
    const detail = el("details", {class: "sys-details"});
    detail.appendChild(el("summary", {}, "架构与项目资料"));
    for (const [key, value] of [
        ["Institution", c.institution], ["Agent architecture", c.agent_architecture],
        ["Open source", c.open_source_status]
    ]) {
        detail.appendChild(el("div", {class:"sys-row"}, [
            el("span", {class:"sys-key"}, T[key]),
            el("span", {class:"sys-val"}, value || "未记录")
        ]));
    }
    card.appendChild(detail);
    const source = safeExternalHref(c.source_url);
    if (source) card.appendChild(el("footer", {class:"sys-card-footer"}, [
        el("a", {class:"sys-source-link",href:source,target:"_blank",
                 rel:"noopener noreferrer"}, "查看资料来源 ↗")
    ]));
    return card;
}


// ---------------------------------------------------------------------------
// Module 4: 论文网络摘要
// ---------------------------------------------------------------------------
function renderPaperGroups(s) {
    const groups = s.paper_groups || {};
    const total = Object.values(groups).reduce((sum, arr) => sum + arr.length, 0);
    setText("#paper-count", String(total) + " 条 · " +
            Object.keys(groups).length + " 组");
    const body = $("#paper-groups-body");
    body.innerHTML = "";
    const order = [
        "Theory papers", "MAI lineage papers",
        "MIRACLE / CocoNote papers",
        "Agent infrastructure papers", "Evidence / policy papers"
    ];
    const seen = new Set();
    for (const group of order) {
        if (!groups[group]) continue;
        body.appendChild(buildPaperGroup(group, groups[group]));
        seen.add(group);
    }
    for (const group of Object.keys(groups)) {
        if (!seen.has(group)) body.appendChild(buildPaperGroup(group, groups[group]));
    }
    const search = $("#paper-search");
    if (search) search.addEventListener("input", filterPapers);
    filterPapers();
}

function buildPaperGroup(groupName, papers) {
    const wrap = el("section", {class:"paper-group"});
    const display = PAPER_GROUP_TITLES[groupName] || groupName;
    wrap.appendChild(el("h3", {class:"paper-group-title"},
                        display + " · " + papers.length + " 条"));
    const list = el("ul", {class:"paper-list"});
    for (const p of papers) {
        const metadata = [
            String(p.year || ""), String(p.related_system || ""),
            ...(Array.isArray(p.tags) ? p.tags : [])
        ].filter(Boolean);
        const haystack = [p.title, groupName, ...metadata].join(" ");
        const li = el("li", {class:"paper-item","data-search":haystack});
        const url = safeExternalHref(p.url);
        li.appendChild(url
            ? el("a", {href:url,target:"_blank",rel:"noopener noreferrer"},
                 p.title || "(未命名论文)")
            : el("span", {}, p.title || "(未命名论文)"));
        if (metadata.length) li.appendChild(
            el("div", {class:"paper-meta"}, metadata.join(" · ")));
        list.appendChild(li);
    }
    wrap.appendChild(list);
    return wrap;
}

function filterPapers() {
    const query = $("#paper-search")?.value || "";
    let visible = 0;
    for (const group of $$("#paper-groups-body .paper-group")) {
        let shown = 0;
        for (const item of group.querySelectorAll(".paper-item")) {
            const match = containsSearch(item.getAttribute("data-search"), query);
            item.hidden = !match;
            if (match) { shown++; visible++; }
        }
        group.hidden = shown === 0;
    }
    setText("#paper-visible-count", visible + " 条匹配");
    const empty = $("#paper-empty");
    if (empty) empty.hidden = visible !== 0;
}

// ---------------------------------------------------------------------------
// Module 5: 独立的非论文研究资料
// ---------------------------------------------------------------------------
const REFERENCE_KIND_LABELS = {
    "official_page": "官方项目与机构网页",
    "person_profile": "研究者资料页",
    "venue_or_journal": "学术会议与期刊",
    "policy_document": "政策文件",
    "news_article": "新闻与研究报道",
};
let activeReferenceFilter = "all";
function renderResearchReferences(s) {
    const groups = s.reference_groups || {};
    const total = Object.values(groups).reduce((n,items)=>n+items.length,0);
    setText("#reference-count", String(total) + " 条 · " +
            Object.keys(groups).length + " 类");
    const chips = $("#reference-filter-chips");
    chips.innerHTML = "";
    const categories = ["all", "official_page", "person_profile",
                        "venue_or_journal", "policy_document", "news_article"];
    for (const kind of categories) {
        if (kind !== "all" && !groups[kind]?.length) continue;
        chips.appendChild(el("button", {
            class:"chip" + (kind==="all" ? " chip-active" : ""),
            type:"button", "data-kind":kind,
            "aria-pressed":kind==="all" ? "true" : "false"
        }, kind==="all" ? "全部资料" : REFERENCE_KIND_LABELS[kind]));
    }
    const host = $("#reference-groups-body");
    host.innerHTML = "";
    for (const kind of categories) {
        if (kind==="all") continue;
        const items = groups[kind] || [];
        if (!items.length) continue;
        const group = el("section", {class:"paper-group","data-kind":kind});
        group.appendChild(el("h3", {class:"paper-group-title"},
                             REFERENCE_KIND_LABELS[kind]+" · "+items.length+" 条"));
        const ul = el("ul", {class:"paper-list"});
        for (const ref of items) {
            const haystack = [ref.title, ref.institution, kind].join(" ");
            const li = el("li", {class:"paper-item","data-search":haystack});
            const url = safeExternalHref(ref.url);
            li.appendChild(url
                ? el("a",{href:url,target:"_blank",rel:"noopener noreferrer"},
                     ref.title || "(未命名资料)")
                : el("span",{},ref.title || "(未命名资料)"));
            if (ref.institution) li.appendChild(
                el("div",{class:"paper-meta"},ref.institution));
            ul.appendChild(li);
        }
        group.appendChild(ul);
        host.appendChild(group);
    }
    chips.addEventListener("click", event => {
        const btn = event.target.closest("button[data-kind]");
        if (!btn || !chips.contains(btn)) return;
        activeReferenceFilter = btn.getAttribute("data-kind");
        chips.querySelectorAll(".chip").forEach(elm => {
            const selected = elm === btn;
            elm.classList.toggle("chip-active", selected);
            elm.setAttribute("aria-pressed", String(selected));
        });
        filterResearchReferences();
    });
    const search = $("#reference-search");
    if (search) search.addEventListener("input", filterResearchReferences);
    filterResearchReferences();
}

function filterResearchReferences() {
    const query = $("#reference-search")?.value || "";
    let visible = 0;
    for (const group of $$("#reference-groups-body .paper-group")) {
        const includeKind = activeReferenceFilter === "all" ||
                            group.getAttribute("data-kind") === activeReferenceFilter;
        let shown = 0;
        for (const item of group.querySelectorAll(".paper-item")) {
            const match = includeKind &&
                containsSearch(item.getAttribute("data-search"),query);
            item.hidden = !match;
            if (match) { shown++; visible++; }
        }
        group.hidden = shown===0;
    }
    setText("#reference-visible-count", visible + " 条匹配");
    const empty = $("#reference-empty");
    if (empty) empty.hidden = visible!==0;
}
// ---------------------------------------------------------------------------
// Module 6: 关键人物与机构
// ---------------------------------------------------------------------------
function renderPeopleGroups(s) {
    const groups = s.people_groups || {};
    const total = Object.values(groups).reduce((sum, arr) => sum + arr.length, 0);
    setText("#people-count",
        `${total} ${T["people"]} · ${Object.keys(groups).length} 个机构`);

    const body = $("#people-groups-body");
    body.innerHTML = "";
    for (const [g, people] of Object.entries(groups)) {
        body.appendChild(buildPeopleGroup(g, people));
    }
}

function buildPeopleGroup(groupName, people) {
    const display = PEOPLE_GROUP_TITLES[groupName] || groupName;
    const wrap = el("section", { class: "people-group" });
    wrap.appendChild(el("h3", { class: "people-group-title" }, `${display} (${people.length})`));
    const grid = el("div", { class: "people-grid" });
    if (!people.length) {
        grid.appendChild(el("div", { class: "empty-note" }, T["No people tracked in this group yet."]));
    }
    for (const p of people) {
        const card = el("article", { class: "person-card" });
        const nameNode = p.source_url
            ? el("a", { href: p.source_url, target: "_blank", rel: "noopener noreferrer", class: "person-name" }, p.name || "(未命名)")
            : el("span", { class: "person-name" }, p.name || "(未命名)");
        card.appendChild(nameNode);
        if (p.institution) card.appendChild(el("div", { class: "person-inst" }, p.institution));
        if (p.role) card.appendChild(el("div", { class: "person-role" }, p.role));
        grid.appendChild(card);
    }
    wrap.appendChild(grid);
    return wrap;
}

// ---------------------------------------------------------------------------
// Module 7: 信息源健康状态
// ---------------------------------------------------------------------------
function renderSourceHealth(s) {
    const h = s.source_health || {};
    setText('[data-stat="sh_stable_sources"]', h.stable_sources ?? "—");
    setText('[data-stat="sh_active_sources"]', h.active_sources ?? "—");
    setText('[data-stat="sh_source_errors_count"]', h.source_errors_count ?? "—");

    const fb = h.fallback_status || {};
    const fbText = fb && Object.keys(fb).length
        ? `运行=${fb.ran ?? "?"} · 查询=${fb.queries ?? "?"} · 命中=${fb.hits ?? "?"}` +
          (Array.isArray(fb.errors) && fb.errors.length ? ` · 错误=${fb.errors.length}` : "")
        : "—";
    setText("#source-health-fallback [data-fb]", fbText);

    // Candidates by source (top 20)
    const cbs = h.candidates_by_source || {};
    const cbsEntries = Object.entries(cbs).slice(0, 20);
    const cbsText = cbsEntries.length
        ? cbsEntries.map(([k, urls]) => `${k} (${urls.length})\n  ${urls.slice(0, 3).join("\n  ")}`).join("\n\n")
        : T["No source returned candidates this run."];
    setText("#source-candidates-pre", cbsText);

    const errs = h.source_errors || {};
    const errsText = Object.keys(errs).length
        ? Object.entries(errs).map(([k, v]) => `${k}: ${v}`).join("\n")
        : T["No source errors."];
    setText("#source-errors-pre", errsText);
}

// ---------------------------------------------------------------------------
// Footer (totals + last updated)
// ---------------------------------------------------------------------------
function renderFooter(s) {
    setText("#meta-data-count",
        `${s.totals.papers} ${T["papers"]} · ${s.totals.references ?? 0} ${T["references"]} · ${s.totals.systems} ${T["systems"]} · ${s.totals.people} ${T["people"]} · ${T["last update"]} ${fmtDate(s.last_updated)}`);

    const footer = $("#footer-sources");
    if (footer) {
        footer.innerHTML = "";
        footer.appendChild(el("div", {
            html: `<strong>${T["Tracked keywords"]}</strong>:SSRL · HASRL · MAI · MIRACLE · 多智能体 · 学习分析 · Khanmigo · AutoGen · MASS · Cognitive Tutor · LearnLab · Khan Academy · CocoRobo · AI 课堂 OS`,
        }));
        footer.appendChild(el("div", {
            html: `<strong>${T["Last weekly run"]}</strong>:${escapeHtml(fmtDate(s.last_updated))}`,
        }));
    }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
    let summary;
    try {
        summary = await loadJson(DATA.summary);
    } catch (e) {
        showModuleError("#this-week", `加载仪表盘摘要失败:${e.message}。站点可能仍在重新构建中。`);
        return;
    }

    try { renderHero(summary); } catch (e) { /* editorial summary is supplementary */ }
    try { renderFeaturedReading(summary); } catch (e) { /* optional curated entry points */ }
    try { renderTimeline(summary); } catch (e) { showModuleError("#research-lineage", e.message); }
    try { renderThisWeek(summary); } catch (e) { showModuleError("#this-week", e.message); }
    try { renderSystemCards(summary); } catch (e) { showModuleError("#system-cards", e.message); }
    try { renderPaperGroups(summary); } catch (e) { showModuleError("#paper-groups", e.message); }
    try { renderResearchReferences(summary); } catch (e) { showModuleError("#research-references", e.message); }
    try { renderPeopleGroups(summary); } catch (e) { showModuleError("#people-groups", e.message); }
    try { renderSourceHealth(summary); } catch (e) { showModuleError("#source-health", e.message); }
    try { renderFooter(summary); } catch (_) { /* non-critical */ }

    enableSectionNavigation();
}

document.addEventListener("DOMContentLoaded", main);