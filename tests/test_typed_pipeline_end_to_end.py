from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import contextlib,io

R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("p42_end_to_end_watcher",R/"scripts/weekly_ai_education_watch.py")
watch=importlib.util.module_from_spec(spec);sys.modules[spec.name]=watch;spec.loader.exec_module(watch)


class TypedPipelineE2ETests(unittest.TestCase):
    def test_dry_oneshot_weekly_job_updates_papers_and_references_independently(self):
        with tempfile.TemporaryDirectory(prefix="p42-e2e-",dir="/dev/shm") as t:
            root=Path(t)
            data=root/"docs/data"
            shutil.copytree(R/"docs/data",data)
            before_papers=json.loads((data/"papers.json").read_text())
            before_refs=json.loads((data/"research-entities.json").read_text())
            assert len(before_papers)==12 and len(before_refs)==29
            old=next(x for x in before_refs if x.get("source_id")=="cocorobo-research")
            prior_url=old["url"]
            new_source="https://cocorobo.hk/research-new-p42-test"
            candidates=[
                {"id":before_papers[0]["id"],"url":before_papers[0]["url"],
                 "title":before_papers[0]["title"],"tags":["arxiv"],"source_id":"same-paper"},
                {"id":"https://arxiv.org/abs/2601.99999","url":"https://arxiv.org/abs/2601.99999",
                 "title":"P42 Test: SSRL multi-agent AI learning study",
                 "tags":["arxiv"],"source_id":"fixture-new-paper","year":"2026"},
                {"id":"https://cocorobo.hk/research-new-p42-test","url":new_source,
                 "title":"CocoRobo Research","tags":["official-page"],"source_id":"cocorobo-research"},
                {"id":"https://www.oulu.fi/en/hybrid-intelligence",
                 "url":"https://www.oulu.fi/en/hybrid-intelligence",
                 "title":"Hybrid Intelligence | University of Oulu",
                 "tags":["official-page"],"source_id":"oulu-hi"},
            ]
            diag={"source_counts":{"fixture":len(candidates)},"source_errors":{},
                  "fallback_status":{"ran":False,"queries":0,"hits":0,"errors":[]}}
            with patch.object(watch,"fetch_from_registry",return_value=(candidates,diag)),\
                 patch.object(watch,"rebuild_dashboard_summary",
                              return_value=(True,"2026-10-26T08:00:00Z",None)),\
                 patch.object(watch,"iso_week_tag",return_value="2026-W44"),\
                 contextlib.redirect_stdout(io.StringIO()):
                exitcode=watch.main([
                    "--data-dir",str(data),"--reports-dir",str(root/"reports/weekly")])
            self.assertEqual(exitcode,0)
            after_papers=json.loads((data/"papers.json").read_text())
            after_refs=json.loads((data/"research-entities.json").read_text())
            self.assertEqual(len(after_papers),13)
            self.assertEqual(len(after_refs),30)
            self.assertEqual(after_papers[-1]["record_type"],"scholarly_paper")
            same=next(x for x in after_refs if x.get("source_id")=="cocorobo-research")
            self.assertEqual(same["url"],new_source)
            self.assertEqual(same["previous_urls"],[prior_url])
            self.assertEqual(len([x for x in after_refs if x.get("source_id")=="oulu-hi"]),1)
            manifest=json.loads((data/"weekly/manifest.json").read_text())
            latest=json.loads((data/"weekly/latest.json").read_text())
            self.assertEqual(manifest["entity_changes"]["papers_added"],1)
            self.assertEqual(manifest["entity_changes"]["references_added"],1)
            self.assertEqual(latest["new_papers"],1)
            self.assertEqual(latest["new_references"],1)
            self.assertIn("P42 Test: SSRL",
                          (root/"reports/weekly/2026-W44.md").read_text())


if __name__=="__main__":
    unittest.main()
