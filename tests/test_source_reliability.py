"""P41 offline regressions for real source HTML and diagnosed provider failures."""
from __future__ import annotations

import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"scripts/weekly_ai_education_watch.py"
spec=importlib.util.spec_from_file_location("p41_weekly_watch",SRC)
watch=importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name]=watch
spec.loader.exec_module(watch)


class ArxivHTMLCases(unittest.TestCase):
    def test_canonical_relative_absolute_and_untrusted_rejection(self):
        for candidate in ("/abs/2601.01234",
                          "https://arxiv.org/abs/2601.01234",
                          "https://www.arxiv.org/abs/2601.01234?ref=search",
                          "/abs/2601.01234/"):
            self.assertEqual(watch._canonical_arxiv_abs_url(candidate),
                             "https://arxiv.org/abs/2601.01234")
        for unsafe in ("https://example.org/abs/2601.01234",
                       "//evil.org/abs/2601.01234",
                       "https://arxiv.org/pdf/2601.01234",
                       "javascript:alert(1)"):
            self.assertIsNone(watch._canonical_arxiv_abs_url(unsafe))

    def test_search_absolute_and_relative_are_discovered(self):
        markup = """
        <ol>
          <li class="arxiv-result">
             <p class="title mathjax"> A &amp; B Agent </p>
             <p class="authors">Authors: <span>Mary</span> Li</p>
             <a href="https://arxiv.org/abs/2601.01234">arXiv:2601.01234</a>
          </li>
          <li class='arxiv-result'>
             <p class='title'>Learning Analytics &amp; AI</p>
             <a href='/abs/2502.02533?ref=search'>arXiv:2502.02533</a>
          </li>
          <li class="arxiv-result"><p class="title">Evil</p>
              <a href="https://malicious.example/abs/2601.01233">bad</a></li>
        </ol>"""
        rows=watch.parse_arxiv_search_results(markup,{"id":"arxiv-search-test"},max_items=10)
        self.assertEqual(len(rows),2)
        self.assertEqual([r["url"] for r in rows],
                         ["https://arxiv.org/abs/2601.01234",
                          "https://arxiv.org/abs/2502.02533"])
        self.assertEqual(rows[0]["title"],"A & B Agent")
        self.assertIn("Mary Li",rows[0]["summary"])
        self.assertEqual(rows[0]["source_id"],"arxiv-search-test")

    def test_search_results_not_duplicated_and_bounded(self):
        markup = "".join(
            f'<li class="arxiv-result"><p class="title">Paper {i}</p>'
            f'<a href="https://arxiv.org/abs/2601.{i:05d}">id</a></li>'
            for i in range(12))
        item={"id":"arxiv-search-limit"}
        self.assertEqual(len(watch.parse_arxiv_search_results(markup,item,max_items=5)),5)
        double=markup[:markup.index('</li>')+5]*3
        self.assertEqual(len(watch.parse_arxiv_search_results(double,item)),1)

    def test_arxiv_search_reports_parse_failure_for_present_results(self):
        errors=[]
        with patch.object(watch,"http_get",return_value="<li class='arxiv-result'>broken<li>"):
            rows=watch.fetch_arxiv_source(
                {"url":"https://arxiv.org/search/?query=SSRL","id":"arxiv-search-test"},
                errors=errors)
        self.assertEqual(rows,[])
        self.assertIn("arxiv_search_markup_unparseable",errors)

    def test_arxiv_challenge_and_unrecognized_empty_pages_are_reported(self):
        item={"url":"https://arxiv.org/search/?query=learning","id":"search"}
        for html,expected in [
            ("<html><body>Cloudflare CAPTCHA, verify you are human</body></html>",
             "arxiv_search_challenge_detected"),
            ("<html><body>Dynamic data is rendered by JavaScript</body></html>",
             "arxiv_search_unrecognized_empty_markup")
        ]:
            with self.subTest(expected=expected):
                errors=[]
                with patch.object(watch,"http_get",return_value=html):
                    self.assertEqual(watch.fetch_arxiv_source(item,errors=errors),[])
                self.assertIn(expected,errors)

    def test_http_error_is_recorded_not_silent_empty(self):
        errors=[]
        with patch.object(watch.urllib.request,"urlopen",
                          side_effect=HTTPError("https://example.org",404,"Not Found",{},None)):
            rows=watch.fetch_official_source(
                {"id":"source","url":"https://example.org"},errors=errors)
        self.assertEqual(rows,[])
        self.assertEqual(errors,["http_404"])
        errors=[]
        with patch.object(watch.urllib.request,"urlopen",
                          side_effect=HTTPError("https://arxiv.org",429,"Too Many",{},None)):
            rows=watch.fetch_arxiv_source(
                {"id":"s","url":"https://arxiv.org/search/?query=SSRL"},errors=errors)
        self.assertEqual(rows,[])
        self.assertEqual(errors,["http_429"])


class SearchFallbackCases(unittest.TestCase):
    def test_duckduckgo_challenge_circuit_breaks_after_first(self):
        html=b"<title>DuckDuckGo</title><div class='anomaly-modal'>Verify you are human</div>"
        fake=io.BytesIO(html)
        errors=[]
        with patch.object(watch.urllib.request,"urlopen",return_value=fake):
            self.assertEqual(watch.search_duckduckgo("AI education",errors=errors),[])
        self.assertIn("duckduckgo_challenge_detected",errors)

        def missing(q,limit=5,*,errors=None):
            errors.append("hermes_search_module_unavailable")
            return []

        def blocked(q,limit=5,*,errors=None):
            errors.append("duckduckgo_challenge_detected")
            return []

        registry={"search_fallback":{"queries":["one","two","three"]}}
        with patch.object(watch,"try_hermes_search",side_effect=missing),\
             patch.object(watch,"search_duckduckgo",side_effect=blocked):
            rows, diag=watch.fetch_from_registry(registry,5)
        self.assertEqual(rows,[])
        self.assertTrue(diag["fallback_status"]["circuit_open"])
        self.assertEqual(diag["fallback_status"]["attempted_queries"],1)
        self.assertEqual(diag["fallback_status"]["skipped_queries"],2)
        self.assertTrue(diag["fallback_status"]["errors"])

    def test_ddg_real_results_url_unwrapped(self):
        html=(
            "<a class='result__a' "
            "href='//duckduckgo.com/l/?uddg=https%3A%2F%2Farxiv.org%2Fabs%2F2601.01234'>"
            "Paper &amp; Education</a>"
            "<a class='result__snippet'>A &amp; B</a>"
        ).encode()
        with patch.object(watch.urllib.request,"urlopen",return_value=io.BytesIO(html)):
            errors=[]
            rows=watch.search_duckduckgo("learning",errors=errors)
        self.assertEqual(errors,[])
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["url"],"https://arxiv.org/abs/2601.01234")
        self.assertEqual(rows[0]["title"],"Paper & Education")
        self.assertEqual(rows[0]["snippet"],"A & B")

    def test_missing_hermes_provider_is_explicit(self):
        errors=[]
        # Site's dependency is not installed in this standalone test environment;
        # deliberately simulate the import failure rather than depend on site config.
        import builtins
        orig_import=builtins.__import__
        def mock_import(name,*args,**kwargs):
            if name=="hermes_tools":
                raise ModuleNotFoundError("No module named 'hermes_tools'")
            return orig_import(name,*args,**kwargs)
        with patch("builtins.__import__",side_effect=mock_import):
            rows=watch.try_hermes_search("test",errors=errors)
        self.assertEqual(rows,[])
        self.assertEqual(errors,["hermes_search_module_unavailable"])

    def test_official_sources_never_count_as_new_academic_papers(self):
        values=[
            {"tags":["official-page"],"title":"Oulu HI","url":"https://www.oulu.fi/en/hybrid-intelligence"},
            {"tags":["person-source"],"title":"Researcher","url":"https://example.org/person"},
            {"tags":["conference-venue"],"title":"Conference","url":"https://example.org/conf"},
            {"tags":["arxiv-search"],"title":"Paper","url":"https://arxiv.org/abs/2601.01234"},
        ]
        self.assertEqual([watch.is_paper_candidate(x) for x in values],
                         [False,False,False,True])
        self.assertTrue(watch.is_paper_candidate({
            "tags":["fallback-search"],"url":"https://doi.org/10.1234/paper"}))
        self.assertFalse(watch.is_paper_candidate({
            "tags":["fallback-search"],"url":"https://random-blog.example.com/ai"}))

    def test_source_register_four_official_urls_are_validated(self):
        data=json.loads((ROOT/"docs/data/source-registry.json").read_text())
        urls={x["id"]:x["url"] for x in data["official_project_sources"]["items"]}
        self.assertEqual(urls["oulu-hi"],"https://www.oulu.fi/en/hybrid-intelligence")
        self.assertIn("learning-regulation-ai-promoting-adaptive-k-12-learners",urls["oulu-lead"])
        self.assertIn("let-lab-learning-and-educational-technology-research-lab",urls["oulu-let"])
        self.assertIn("multi-agent-design-optimizing-agents",urls["google-mass"])


if __name__=="__main__":
    unittest.main()
