"""P48: published data files keep a stable, typed shape."""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data"
spec = importlib.util.spec_from_file_location(
    "weekly_watch_p48_schema", ROOT / "scripts" / "weekly_ai_education_watch.py")
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)

# file -> {field: type} that every record must carry
REQUIRED = {
    "papers.json": {"id": str, "key": str, "title": str, "url": str,
                    "institution": str, "summary": str, "tags": list,
                    "record_type": str},
    "research-entities.json": {"id": str, "title": str, "url": str,
                               "summary": str, "tags": list, "record_type": str},
    "systems.json": {"name": str, "type": str, "architecture": str,
                     "relation": str, "source_url": str,
                     "source_verified_at": str, "source_verification": str},
    "people.json": {"name": str, "institution": str, "role": str},
    "tech-stack.json": {"system": str, "institution": str, "type": str,
                        "agent_architecture": str, "open_source_status": str},
    "timeline.json": {"label": str, "layer": str, "note": str},
}
ISO_FIELDS = ("first_seen", "last_seen")


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class DataSchema(unittest.TestCase):
    def test_every_data_file_is_valid_json(self):
        for path in DATA.rglob("*.json"):
            with self.subTest(path=path.name):
                json.loads(path.read_text(encoding="utf-8"))

    def test_required_fields_and_types(self):
        for name, fields in REQUIRED.items():
            records = load(name)
            self.assertIsInstance(records, list)
            for i, record in enumerate(records):
                for field, kind in fields.items():
                    with self.subTest(file=name, index=i, field=field):
                        self.assertIsInstance(record.get(field), kind)

    def test_optional_timestamps_and_years_are_well_formed(self):
        for name in REQUIRED:
            for i, record in enumerate(load(name)):
                for field in ISO_FIELDS:
                    if record.get(field):
                        with self.subTest(file=name, index=i, field=field):
                            self.assertRegex(record[field], r"^\d{4}-\d{2}-\d{2}T")
                if name != "timeline.json" and record.get("year"):
                    with self.subTest(file=name, index=i, field="year"):
                        self.assertRegex(str(record["year"]), r"^(19|20)\d{2}$")

    def test_links_are_https(self):
        for name, field in (("papers.json", "url"), ("research-entities.json", "url"),
                            ("systems.json", "source_url")):
            for i, record in enumerate(load(name)):
                with self.subTest(file=name, index=i):
                    self.assertTrue(record[field].startswith("https://"))

    def test_paper_keys_are_canonical_and_unique(self):
        papers = load("papers.json")
        for p in papers:
            with self.subTest(title=p["title"][:60]):
                self.assertEqual(p["key"], watch.paper_key(p["url"]))
                self.assertEqual(p["record_type"], "scholarly_paper")
        self.assertEqual(len({p["key"] for p in papers}), len(papers))
        self.assertEqual(len({p["id"] for p in papers}), len(papers))

    def test_doi_inside_publisher_url_is_recognised(self):
        self.assertEqual(
            watch.paper_key("https://bera-journals.onlinelibrary.wiley.com/doi/10.1111/bjet.13325"),
            "doi:10.1111/bjet.13325")
        self.assertEqual(watch.paper_key("https://doi.org/10.1111/BJET.13325"),
                         "doi:10.1111/bjet.13325")

    def test_review_queue_shape(self):
        queue = load("review-queue.json")
        self.assertEqual(queue["schema_version"], 1)
        allowed = {"rejected_by_filter", "quarantined_from_papers", "restored", "dismissed"}
        for i, entry in enumerate(queue["items"]):
            with self.subTest(index=i):
                self.assertTrue(entry["title"] and entry["url"] and entry["reason"])
                self.assertIn(entry["status"], allowed)
                if entry["status"] == "quarantined_from_papers":
                    self.assertEqual(entry["record"]["url"], entry["url"])

    def test_dashboard_totals_match_source_files(self):
        totals = load("dashboard-summary.json")["totals"]
        self.assertEqual(totals["papers"], len(load("papers.json")))
        self.assertEqual(totals["references"], len(load("research-entities.json")))
        self.assertEqual(totals["systems"], len(load("systems.json")))
        self.assertEqual(totals["people"], len(load("people.json")))


if __name__ == "__main__":
    unittest.main()
