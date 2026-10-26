from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


def module_from(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    result=importlib.util.module_from_spec(spec)
    sys.modules[name]=result
    spec.loader.exec_module(result)
    return result


migration=module_from("p42_legacy_entity_classifier","scripts/migrate_research_entities.py")
watch=module_from("p42_reference_weekly_update","scripts/weekly_ai_education_watch.py")


class TypedRecordMigrationTests(unittest.TestCase):
    def test_p42_corpus_is_fully_classified(self):
        d=ROOT/"docs/data"
        papers=json.loads((d/"papers.json").read_text())
        refs=json.loads((d/"research-entities.json").read_text())
        audit=json.loads((d/"research-migration.json").read_text())
        self.assertEqual(len(papers),12)
        self.assertEqual(len(refs),29)
        self.assertEqual(len({x["id"] for x in papers+refs}),41)
        self.assertTrue(all(x["record_type"]=="scholarly_paper" for x in papers))
        self.assertEqual(audit["input_record_count"],41)
        self.assertEqual(audit["typed_papers"],12)
        self.assertEqual(audit["typed_references"],29)
        self.assertEqual({k:sum(r["record_type"]==k for r in refs)
                          for k in migration.ALLOWED_REFERENCE_KINDS},
                         {"official_page":9,"person_profile":12,
                          "venue_or_journal":6,"policy_document":1,"news_article":1})
        self.assertEqual(migration.run(d)["status"],"ALREADY_MIGRATED")

    def test_no_unreviewed_legacy_classification(self):
        entries=[
            {"id":"https://arxiv.org/abs/2601.01234",
             "url":"https://arxiv.org/abs/2601.01234","title":"Study"},
            {"id":"official-1","url":"https://lab.example","title":"Lab",
             "tags":["official-page"]},
            {"id":"conference-1","url":"https://conf.example","title":"Conference",
             "tags":["conference-venue"]},
        ]
        papers,refs=migration.partition(entries)
        self.assertEqual(len(papers),1)
        self.assertEqual(len(refs),2)
        self.assertEqual({x["record_type"] for x in refs},
                         {"official_page","venue_or_journal"})
        with self.assertRaisesRegex(ValueError,"Unreviewed ambiguous"):
            migration.partition([{"id":"orphan","title":"Mystery",
                                  "url":"https://unknown.example/page"}])
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            migration.partition([entries[0],entries[0]])

    def test_future_openalex_doi_paper_stays_idempotent(self):
        doi={"id":"https://doi.org/10.1234/p42paper",
             "url":"https://doi.org/10.1234/p42paper",
             "title":"New SSRL Evidence",
             "record_type":"scholarly_paper",
             "source_id":"search_fallback:openalex",
             "tags":["fallback-search","openalex-search"],
             "openalex_id":"https://openalex.org/W123456"}
        papers,refs=migration.partition([doi])
        self.assertEqual(len(papers),1)
        self.assertEqual(refs,[])
        self.assertEqual(migration.record_kind(doi),"scholarly_paper")
        unsafe=dict(doi,url="https://untrusted.example/p42")
        with self.assertRaises(ValueError):
            migration.partition([unsafe])

    def test_reference_refresh_reuses_source_id_and_remembers_old_url(self):
        rows=[{"id":"https://lab.example/old","url":"https://lab.example/old",
               "title":"Lab","record_type":"official_page",
               "source_id":"oulu-hi"}]
        candidate={"id":"https://lab.example/new","url":"https://lab.example/new",
                   "title":"Lab","source_id":"oulu-hi",
                   "tags":["official-page"]}
        rows,added=watch.merge_references(rows,[candidate,dict(candidate)])
        self.assertEqual(added,0)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["url"],"https://lab.example/new")
        self.assertEqual(rows[0]["previous_urls"],["https://lab.example/old"])

    def test_reference_new_created_without_inflating_paper_count(self):
        with tempfile.TemporaryDirectory(prefix="p42-ref-tmp-") as td:
            ref={"id":"p-new","url":"https://www.oulu.fi/en/hybrid-intelligence",
                 "title":"Oulu HI","source_id":"oulu-hi",
                 "tags":["official-page"],"summary":"Research programme"}
            rows,added=watch.merge_references([], [ref])
            self.assertEqual(added,1)
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]["record_type"],"official_page")
            self.assertFalse(watch.is_paper_candidate(ref))
            paper={"id":"https://arxiv.org/abs/2601.01234",
                   "url":"https://arxiv.org/abs/2601.01234",
                   "title":"A real paper","tags":["arxiv"]}
            papers,count=watch.merge_papers([], [paper])
            self.assertEqual(count,1)
            self.assertEqual(papers[0]["record_type"],"scholarly_paper")

    def test_legacy_seed_import_refuses_overwrite_of_typed_data(self):
        with tempfile.TemporaryDirectory(prefix="p42-seedguard-") as td:
            base=Path(td)
            (base/"research-migration.json").write_text("{}")
            cmd=[sys.executable,str(ROOT/"scripts/build_from_report.py"),
                 "--input",str(ROOT/"reports/seed/latest-report.md"),
                 "--data-dir",str(base)]
            result=subprocess.run(cmd,capture_output=True,text=True,timeout=15)
            self.assertNotEqual(result.returncode,0)
            self.assertIn("Typed P42 live corpus exists",result.stderr)


if __name__=="__main__":
    unittest.main()
