"""P49: the site can read weekly reports in-page from a generated archive index."""
from __future__ import annotations

import json
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class WeeklyReader(unittest.TestCase):
    def setUp(self):
        self.summary = json.loads(
            (DOCS / "data" / "dashboard-summary.json").read_text(encoding="utf-8"))

    def test_archive_lists_every_published_report_newest_first(self):
        archive = self.summary["weekly_archive"]
        files = sorted((p.name for p in (DOCS / "reports" / "weekly").glob("20??-W??.md")),
                       reverse=True)
        self.assertEqual([Path(w["report_path"]).name for w in archive], files)
        self.assertEqual(archive[0]["week_tag"], self.summary["latest_week_tag"])
        for w in archive:
            with self.subTest(week=w["week_tag"]):
                self.assertTrue((DOCS / w["report_path"]).is_file())
                self.assertFalse(w["report_path"].startswith("/"))
                text = (DOCS / w["report_path"]).read_text(encoding="utf-8")
                self.assertIn(f"New papers added this run: **{w['new_papers']}**", text)

    def test_review_queue_counts_match_queue_file(self):
        queue = json.loads((DOCS / "data" / "review-queue.json").read_text(encoding="utf-8"))
        open_items = [x for x in queue["items"] if x["status"] in
                      ("rejected_by_filter", "quarantined_from_papers")]
        self.assertEqual(self.summary["review_queue"],
                         {"open": len(open_items), "total": len(queue["items"])})

    def test_page_has_reader_markup_and_script_hooks(self):
        html = (DOCS / "index.html").read_text(encoding="utf-8")
        for element_id in ("weekly-reader", "weekly-week-select", "weekly-report-view",
                           "weekly-reader-meta", "review-queue-note"):
            with self.subTest(id=element_id):
                self.assertEqual(html.count(f'id="{element_id}"'), 1)
        js = (DOCS / "assets" / "app.js").read_text(encoding="utf-8")
        self.assertIn("renderWeeklyReader(summary)", js)
        # Report text must be escaped before any markup is added.
        body = js[js.index("function reportInline"):js.index("function renderReportMarkdown")]
        self.assertIn("escapeHtml(plain)", body)
        self.assertNotRegex(body, r"javascript:")
        self.assertRegex(body, re.escape("(https?:"))


if __name__ == "__main__":
    unittest.main()
