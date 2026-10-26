"""P43: statically guard the static research atlas' navigation and data claims.

No external browser dependency needed; dynamic filter behavior is also checked
in the isolated P43 JSDOM acceptance harness before production publish.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import json
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/"docs"


class Tags(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids=[]
        self.anchor_refs=[]
        self.external_scripts=[]
        self.links=[]
        self.stat_keys=[]
        self.tag_count={}
        self.scripts=[]
    def handle_starttag(self,tag,attrs):
        self.tag_count[tag]=self.tag_count.get(tag,0)+1
        d=dict(attrs)
        if "id" in d:
            self.ids.append(d["id"])
        if tag=="a" and "href" in d:
            href=d["href"];self.links.append(href)
            if href.startswith("#") and href!="#":
                self.anchor_refs.append(href[1:])
        if tag=="script" and d.get("src"):
            self.scripts.append(d["src"])
            if d["src"].startswith(("http://","https://")):
                self.external_scripts.append(d["src"])
        if d.get("data-stat"):
            self.stat_keys.append(d["data-stat"])


class ResearchAtlasStaticTests(unittest.TestCase):
    def setUp(self):
        self.html=(DOCS/"index.html").read_text()
        self.css=(DOCS/"assets/style.css").read_text()
        self.js=(DOCS/"assets/app.js").read_text()
        self.data=json.loads((DOCS/"data/dashboard-summary.json").read_text())
        self.tags=Tags()
        self.tags.feed(self.html)

    def test_all_navigation_and_interactive_dom_targets_exist(self):
        self.assertEqual(len(self.tags.ids),len(set(self.tags.ids)))
        self.assertEqual(len(set(self.tags.anchor_refs)-set(self.tags.ids)),0)
        for key in (
            "main","research-guide","this-week","research-lineage","evidence-lab","system-cards",
            "paper-groups","research-references","people-groups","source-health",
            "methodology","evidence-tabs","evidence-article","evidence-relations",
            "relation-filter-chips","paper-search","reference-search","timeline-grid",
            "system-filter-chips","reference-filter-chips","paper-groups-body",
            "reference-groups-body","paper-visible-count","reference-visible-count"
        ):
            self.assertIn(key,self.tags.ids)

    def test_no_remote_script_required_for_research_lineage(self):
        self.assertEqual(self.tags.external_scripts,[])
        self.assertEqual(self.tags.scripts,["assets/app.js"])
        self.assertNotIn("mermaid.min.js",self.js)
        self.assertIn("function renderTimeline(s)",self.js)
        self.assertIn("function renderHero(s)",self.js)
        self.assertIn("function renderResearchReferences(s)",self.js)

    def test_content_numbers_and_provenance_are_honest(self):
        totals=self.data["totals"]
        self.assertEqual((totals["papers"],totals["references"],
                          totals["systems"],totals["people"]),(12,29,10,16))
        self.assertEqual(len(self.data["timeline"]),11)
        self.assertIn("featured-reads",self.tags.ids)
        self.assertIn("function renderFeaturedReading(s)",self.js)
        self.assertEqual(sum(len(x) for x in self.data["paper_groups"].values()),12)
        self.assertEqual(sum(len(x) for x in self.data["reference_groups"].values()),29)
        self.assertIn("最近一次归档更新",self.html)
        self.assertIn("研究索引，而非完整文献数据库",self.html)
        self.assertNotIn("实时</span>",self.html)
        self.assertIn("data/research-migration.json",self.html)
        self.assertEqual(self.data["this_week"]["new_papers"],0)
        self.assertEqual(self.data["this_week"]["new_references"],0)

    def test_text_search_filter_and_source_accessibility(self):
        for marker in (
            "function filterPapers()", "function filterResearchReferences()",
            "function applySystemFilter(filter)", '"aria-pressed"',
            'rel:"noopener noreferrer"', "function safeExternalHref(value)"
        ):
            self.assertIn(marker,self.js)
        self.assertIn('aria-live="polite"',self.html)
        self.assertIn('class="skip-link"',self.html)
        self.assertIn("prefers-reduced-motion",self.css)
        self.assertIn("prefers-color-scheme: light",self.css)
        self.assertIn("max-width: 480px",self.css)

    def test_source_links_and_data_files_are_available(self):
        for relative in (
            "assets/style.css","assets/app.js","data/dashboard-summary.json",
            "data/research-migration.json","data/research-deep-dives.json","data/source-registry.json",
            "data/weekly/manifest.json"
        ):
            with self.subTest(path=relative):
                self.assertTrue((DOCS/relative).is_file())
        for url in self.tags.links:
            self.assertFalse(url.startswith("javascript:"))
            if url.startswith("data/") or url.startswith("assets/"):
                self.assertTrue((DOCS/url.split("?")[0]).is_file(),url)

if __name__=="__main__":
    unittest.main()
