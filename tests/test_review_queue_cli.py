"""P48: the review-queue CLI restores and dismisses without re-queueing."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "review_queue_cli", ROOT / "scripts" / "review_queue.py")
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)
watch = cli.watch


class ReviewQueueCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        # Mirror <root>/docs/data and <root>/scripts so the summary rebuild works.
        root = Path(self.tmp.name)
        shutil.copytree(ROOT / "docs" / "data", root / "docs" / "data")
        shutil.copytree(ROOT / "scripts", root / "scripts",
                        ignore=shutil.ignore_patterns("__pycache__"))
        self.data = root / "docs" / "data"

    def run_cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = cli.main(["--data-dir", str(self.data), *argv])
        return code, out.getvalue()

    def read(self, name):
        return json.loads((self.data / name).read_text(encoding="utf-8"))

    def test_restore_moves_record_back_and_updates_summary(self):
        before = len(self.read("papers.json"))
        target = self.read("review-queue.json")["items"][0]
        code, _ = self.run_cli("restore", "0")
        self.assertEqual(code, 0)
        papers = self.read("papers.json")
        self.assertEqual(len(papers), before + 1)
        restored = papers[-1]
        self.assertEqual(restored["url"], target["url"])
        self.assertIn("manual-review", restored["tags"])
        self.assertTrue(watch.is_in_scope(restored))
        self.assertEqual(self.read("review-queue.json")["items"][0]["status"], "restored")
        self.assertEqual(self.read("dashboard-summary.json")["totals"]["papers"], before + 1)
        # A second restore is a no-op.
        self.run_cli("restore", "0")
        self.assertEqual(len(self.read("papers.json")), before + 1)

    def test_dismissed_and_published_items_are_not_requeued(self):
        # Build a pending fixture even if the live queue has been reviewed.
        queue = self.read("review-queue.json")
        queue["items"][1]["status"] = "quarantined_from_papers"
        (self.data / "review-queue.json").write_text(json.dumps(queue))
        summary = self.read("dashboard-summary.json")
        summary["review_queue"]["open"] = 1
        (self.data / "dashboard-summary.json").write_text(json.dumps(summary))
        entry = queue["items"][1]
        self.assertEqual(self.run_cli("dismiss", entry["url"])[0], 0)
        self.assertEqual(self.read("review-queue.json")["items"][1]["status"], "dismissed")
        self.assertEqual(self.read("dashboard-summary.json")["review_queue"]["open"], 0)
        size = len(self.read("review-queue.json")["items"])
        paper = self.read("papers.json")[-1]
        again = [{"title": entry["title"], "url": entry["url"], "source_id": "s",
                  "reason": "no_education_context"},
                 {"title": paper["title"], "url": paper["url"], "source_id": "s",
                  "reason": "no_education_context"}]
        added = watch.update_review_queue(
            self.data / "review-queue.json", again, "2026-W47",
            known_paper_keys={paper["key"]})
        self.assertEqual(added, 0)
        self.assertEqual(len(self.read("review-queue.json")["items"]), size)

    def test_unknown_selector_fails_without_writing(self):
        before = (self.data / "papers.json").read_bytes()
        self.assertEqual(self.run_cli("restore", "no-such-paper-xyz")[0], 1)
        self.assertEqual((self.data / "papers.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
