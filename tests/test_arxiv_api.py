"""P47: arXiv search sources use the documented Atom API with HTML fallback."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "weekly_watch_p47_api", ROOT / "scripts" / "weekly_ai_education_watch.py")
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)
watch.ARXIV_API_DELAY = 0

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2610.24498v2</id>
    <published>2026-10-27T10:00:00Z</published>
    <title>MAVE: A Multi-Agent Framework for
      Grounded Pedagogical Feedback</title>
    <summary>  We support teachers with
      classroom video feedback. </summary>
    <author><name>Ada Example</name></author>
    <author><name>Bo Sample</name></author>
  </entry>
  <entry>
    <id>http://arxiv.org/api/errors#bad</id>
    <title>Error</title><summary>bad query</summary>
  </entry>
</feed>"""
ITEM = {"id": "arxiv-search-x", "label": "x", "api_query": 'all:"multi-agent"',
        "url": "https://arxiv.org/search/?query=x&searchtype=all"}


class ArxivApi(unittest.TestCase):
    def test_feed_is_parsed_with_abstract_authors_and_canonical_url(self):
        rows = watch.parse_arxiv_api_feed(FEED, ITEM)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["url"], "https://arxiv.org/abs/2610.24498")
        self.assertEqual(row["title"],
                         "MAVE: A Multi-Agent Framework for Grounded Pedagogical Feedback")
        self.assertEqual(row["authors"], ["Ada Example", "Bo Sample"])
        self.assertEqual(row["year"], "2026")
        self.assertIn("classroom video", row["summary"])
        self.assertTrue(watch.is_paper_candidate(row))

    def test_non_atom_payload_is_not_treated_as_empty_result(self):
        self.assertIsNone(watch.parse_arxiv_api_feed("<html>busy</html>", ITEM))
        self.assertIsNone(watch.parse_arxiv_api_feed("not xml", ITEM))

    def test_api_is_used_first_and_requests_newest(self):
        seen = []
        def fake(url, timeout=7.0, *, errors=None):
            seen.append(url)
            return FEED
        with patch.object(watch, "http_get", side_effect=fake):
            errors = []
            rows = watch.fetch_arxiv_source(ITEM, errors=errors)
        self.assertEqual(len(rows), 1)
        self.assertEqual(errors, [])
        self.assertEqual(len(seen), 1)
        self.assertTrue(seen[0].startswith("https://export.arxiv.org/api/query?"))
        self.assertIn("sortBy=submittedDate", seen[0])

    def test_api_failure_falls_back_to_html_and_reports_error(self):
        html = ("<li class='arxiv-result'><p class='list-title'>"
                "<a href='https://arxiv.org/abs/2610.24498'>arXiv:2610.24498</a></p>"
                "<p class='title is-5'>MAVE</p><p class='authors'>Authors: A</p></li>")
        def fake(url, timeout=7.0, *, errors=None):
            if "export.arxiv.org" in url:
                errors.append("fetch_TimeoutError")
                return None
            return html
        with patch.object(watch, "http_get", side_effect=fake):
            errors = []
            rows = watch.fetch_arxiv_source(ITEM, errors=errors)
        self.assertEqual([r["url"] for r in rows], ["https://arxiv.org/abs/2610.24498"])
        self.assertIn("arxiv_api_fetch_TimeoutError", errors)

    def test_registry_search_sources_all_have_api_query(self):
        import json
        reg = json.loads((ROOT / "docs/data/source-registry.json").read_text(encoding="utf-8"))
        searches = [i for i in reg["arxiv_sources"]["items"] if i["type"] == "arxiv_search"]
        self.assertGreaterEqual(len(searches), 5)
        self.assertTrue(all(i.get("api_query") for i in searches))


class OpenAlexAbstract(unittest.TestCase):
    def test_inverted_index_is_rebuilt_in_order(self):
        self.assertEqual(
            watch._openalex_abstract({"agents": [1], "Teaching": [0], "help": [2]}),
            "Teaching agents help")
        self.assertEqual(watch._openalex_abstract(None), "")


if __name__ == "__main__":
    unittest.main()
