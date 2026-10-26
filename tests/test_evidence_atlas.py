"""P44: provenance and editorial boundaries for the published research workbench."""
from __future__ import annotations
from pathlib import Path
from urllib.parse import urlsplit
from html.parser import HTMLParser
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"docs/data"


class StudyEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence=json.loads((DATA/"research-deep-dives.json").read_text())
        cls.papers=json.loads((DATA/"papers.json").read_text())
        cls.systems=json.loads((DATA/"systems.json").read_text())
        cls.summary=json.loads((DATA/"dashboard-summary.json").read_text())
        cls.source_audit=json.loads((Path.home()/".local/state/hermes-upgrade-preflight"/
            "v0.22.5-P44_SYSTEM_SOURCE_AUDIT_20261026.json").read_text())

    def test_three_primary_studies_directly_identify_existing_library_records(self):
        studies=self.evidence["studies"]
        self.assertEqual(self.evidence["schema_version"],1)
        self.assertEqual(len(studies),3)
        self.assertEqual(len({s["id"] for s in studies}),3)
        paper_ids={p["id"] for p in self.papers}
        self.assertTrue(all(s["paper_id"] in paper_ids for s in studies))
        for study in studies:
            self.assertTrue(study["primary_url"].startswith("https://"))
            self.assertIn("原始资料",self.evidence["review_notice"])
            self.assertTrue(study["not_established"])
            self.assertGreaterEqual(len(study["verified_points"]),3)
            self.assertGreaterEqual(len(study["reading_questions"]),3)
            self.assertNotIn("我已独立复现实验",study["editorial_interpretation"])
        self.assertEqual({s["evidence_level"] for s in studies},
                         {"source_fulltext","source_abstract"})

    def test_citation_destinations_are_original_research_providers(self):
        sources={s["id"]:urlsplit(s["primary_url"]).hostname for s in self.evidence["studies"]}
        self.assertEqual(sources,{
            "human-ai-ssrl-2023":"bera-journals.onlinelibrary.wiley.com",
            "simclass-2025":"aclanthology.org",
            "mass-2025":"arxiv.org"
        })
        for study in self.evidence["studies"]:
            self.assertTrue(study["verification_scope"],study["id"])
            self.assertIn(study["evidence_level"],
                          {x["code"] for x in self.evidence["evidence_levels"]})

    def test_six_links_have_explicit_directness_and_no_unverified_projects(self):
        links=self.evidence["relations"]
        self.assertEqual(len(links),6)
        study_ids={x["id"] for x in self.evidence["studies"]}
        system_names={s["name"] for s in self.systems}
        self.assertEqual(len({x["id"] for x in links}),6)
        for link in links:
            self.assertIn(link["study_id"],study_ids)
            self.assertIn(link["system_name"],system_names)
            self.assertIn(link["relation_kind"],
                          ("direct_subject","editorial_comparison"))
            self.assertGreater(len(link["scope_note"]),10)
            self.assertGreater(len(link["rationale"]),12)
        self.assertEqual(sum(x["relation_kind"]=="direct_subject" for x in links),2)
        self.assertEqual(sum(x["relation_kind"]=="editorial_comparison" for x in links),4)

    def test_five_wrong_system_sources_corrected_in_canonical_data_and_dashboard(self):
        self.assertEqual(self.source_audit["status"],"5_PRIMARY_SOURCE_LINK_MISMATCHES_CORRECTED")
        changed=self.source_audit["changes"]
        self.assertEqual(len(changed),5)
        canonical={s["name"]:s for s in self.systems}
        summary={s["system"]:s for s in self.summary["system_cards"]}
        for row in changed:
            name=row["system"]
            self.assertEqual(canonical[name]["source_url"],row["new_url"])
            self.assertEqual(summary[name]["source_url"],row["new_url"])
            self.assertEqual(summary[name]["source_verification"],"official_primary_source_page")
            self.assertEqual(summary[name]["source_verified_at"],"2026-10-26")
            self.assertNotEqual(row["old_url"],row["new_url"])
        self.assertEqual(len(self.summary["system_cards"]),10)
        sources={
            name:summary[name]["additional_source_links"]
            for name in ("SimClass (Tsinghua MAIC)","MASS (Google)",
                         "OLI / Torus + DataShop (CMU)")
        }
        self.assertEqual(len(sources),3)
        self.assertEqual(sources["OLI / Torus + DataShop (CMU)"][0]["url"],
                         "https://hcii.cmu.edu/project/datashop")
        for urls in sources.values():
            self.assertEqual(len(urls),1)
            self.assertTrue(urls[0]["url"].startswith("https://"))

    def test_workbench_navigation_and_evidence_ui_present_in_site(self):
        html=(ROOT/"docs/index.html").read_text()
        script=(ROOT/"docs/assets/app.js").read_text()
        css=(ROOT/"docs/assets/style.css").read_text()
        self.assertIn('href="#evidence-lab"',html)
        for id_ in ("evidence-lab","evidence-tabs","evidence-article",
                    "evidence-relations","relation-filter-chips","evidence-scale"):
            self.assertIn(f'id="{id_}"',html)
        self.assertIn('"data/research-deep-dives.json"',script)
        for name in ("renderEvidenceAtlas","selectEvidenceStudy",
                     "filterEvidenceRelations","focusRelatedSystem"):
            self.assertIn("function "+name,script)
        self.assertIn(".evidence-workbench",css)
        self.assertIn(".evidence-related-highlight",css)
        self.assertIn("aria-live=\"polite\"",html)


if __name__=="__main__":
    unittest.main()
