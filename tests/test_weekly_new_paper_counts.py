"""P40 regression: candidate matches are not necessarily newly inserted papers."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "weekly_ai_education_watch.py"
spec = importlib.util.spec_from_file_location("p40_weekly_watch", SOURCE)
watch = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = watch
spec.loader.exec_module(watch)


class WeeklyNewPapersTest(unittest.TestCase):
    def prepare(self, root: Path):
        data = root / "docs" / "data"
        data.mkdir(parents=True)
        for src in (ROOT / "docs" / "data").glob("*.json"):
            shutil.copy2(src, data / src.name)
        return data, root / "reports" / "weekly"

    def run_offline(self, candidates):
        with tempfile.TemporaryDirectory(prefix="p40-ai-weekly-", dir="/dev/shm") as td:
            root = Path(td)
            data, reports = self.prepare(root)
            before = json.loads((data / "papers.json").read_text())
            # Do not access the network or use Git publishing: only a sandboxed
            # main() invocation with a deterministic candidate list.
            with patch.object(watch, "fetch_from_registry",
                              return_value=(candidates, {
                                  "source_counts": {"fixture": len(candidates)},
                                  "source_errors": {},
                                  "fallback_status": {"ran": False, "queries": 0, "hits": 0, "errors": []},
                              })), patch.object(watch, "rebuild_dashboard_summary",
                                                  return_value=(True, "2026-10-26T00:00:00+00:00", None)), patch.object(
                       watch, "iso_week_tag", return_value="2026-W44"), contextlib.redirect_stdout(io.StringIO()):
                rc = watch.main(["--data-dir", str(data), "--reports-dir", str(reports)])
            self.assertEqual(rc, 0)
            new = json.loads((data / "papers.json").read_text())
            manifest = json.loads((data / "weekly" / "manifest.json").read_text())
            latest = json.loads((data / "weekly" / "latest.json").read_text())
            report = (reports / "2026-W44.md").read_text()
            return len(new) - len(before), manifest, latest, report

    def test_30_existing_candidates_produce_zero_new(self):
        entries = json.loads((ROOT / "docs" / "data" / "papers.json").read_text())
        self.assertGreaterEqual(len(entries), 3)
        repeated=[entries[i % len(entries)] for i in range(30)]
        difference, manifest, latest, report = self.run_offline(repeated)
        self.assertEqual(difference, 0)
        self.assertEqual(manifest["entity_changes"]["papers_added"], 0)
        self.assertEqual(latest["entity_changes"]["papers_added"], 0)
        self.assertEqual(latest["new_papers"], 0)
        self.assertEqual(latest["highlights"], [])
        self.assertIn("New papers added this run: **0**", report)
        self.assertIn("_No new items found this run._", report)

    def test_one_new_plus_repeated_candidate_counts_once(self):
        existing = json.loads((ROOT / "docs" / "data" / "papers.json").read_text())
        sample = {
            "title": "P40 Fixture: Unique SSRL Agent Study",
            "url": "https://arxiv.org/abs/2601.99999",
            "source_id": "p40-fixture",
            "tags": ["arxiv"],
            "summary": "A new SSRL study for testing only.",
            "year": "2026"
        }
        candidates = [existing[0], sample, dict(sample), existing[1]]
        diff, manifest, latest, report = self.run_offline(candidates)
        self.assertEqual(diff, 1)
        self.assertEqual(manifest["entity_changes"]["papers_added"], 1)
        self.assertEqual(latest["new_papers"], 1)
        self.assertEqual(len(latest["highlights"]), 1)
        self.assertIn(sample["title"], latest["highlights"])
        self.assertIn("New papers added this run: **1**", report)
        self.assertEqual(report.count("### [P40 Fixture:"), 1)

    def test_official_source_url_migration_does_not_create_fake_new_paper(self):
        official=[{
            "id":"https://www.oulu.fi/en/hybrid-intelligence",
            "title":"Hybrid Intelligence | University of Oulu",
            "url":"https://www.oulu.fi/en/hybrid-intelligence",
            "source_id":"oulu-hi",
            "tags":["official-page"],
            "summary":"Official institutional research programme",
            "institution":"University of Oulu",
            "year":"2026",
        }]
        diff,manifest,latest,report=self.run_offline(official)
        self.assertEqual(diff,0)
        self.assertEqual(manifest["entity_changes"]["papers_added"],0)
        self.assertEqual(latest["new_papers"],0)
        self.assertIn("New papers added this run: **0**",report)

    def test_merge_counts_reseen_url_and_normalized_title_correctly(self):
        start = [
            {"title": "MAI Research Notes", "url": "https://example.invalid/paper?id=1", "summary": ""}
        ]
        hits = [
            {"title": "MAI Research Notes", "url": "https://example.invalid/paper?id=1", "summary": "updated"},
            {"title": "  MAI   Research   Notes  ", "url": "https://example.invalid/different", "summary": "same title"},
        ]
        merged, count = watch.merge_papers(start, hits)
        self.assertEqual(count, 0)
        self.assertEqual(len(merged), 1)


if __name__ == "__main__":
    unittest.main()
