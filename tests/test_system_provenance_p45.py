"""P45 factual system-link and maintenance-boundary regression suite."""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"docs/data"


class RemainingSystemPrimarySources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.systems={x["name"]:x for x in json.loads((DATA/"systems.json").read_text())}
        cls.stack={x["system"]:x for x in json.loads((DATA/"tech-stack.json").read_text())}
        cls.cards={x["system"]:x for x in json.loads((DATA/"dashboard-summary.json").read_text())["system_cards"]}
        cls.html=(ROOT/"docs/index.html").read_text()
        cls.js=(ROOT/"docs/assets/app.js").read_text()

    def test_all_ten_systems_have_distinct_verified_primary_source_entries(self):
        self.assertEqual(len(self.systems),len(self.cards))
        self.assertEqual(len(self.systems),10)
        self.assertEqual(set(self.systems),set(self.cards))
        for name,item in self.systems.items():
            self.assertTrue(item["source_url"].startswith("https://"),name)
            self.assertEqual(item["source_verification"],"official_primary_source_page",name)
            self.assertEqual(item["source_verified_at"],"2026-10-26",name)
            self.assertEqual(item["source_url"],self.cards[name]["source_url"])
            self.assertEqual(item.get("lifecycle_status",""),self.cards[name].get("lifecycle_status",""))
            self.assertEqual(item.get("source_limit_note",""),self.cards[name].get("source_limit_note",""))

    def test_original_microsoft_autogen_archive_status_and_successor_are_explicit(self):
        name="AutoGen v0.4 / Microsoft Agent Framework"
        entry=self.systems[name]
        self.assertEqual(entry["lifecycle_status"],"archived_unmaintained")
        self.assertEqual(entry["source_url"],"https://github.com/microsoft/autogen")
        self.assertTrue(any("agent-framework" in p["url"] for p in entry["additional_source_links"]))
        self.assertIn("不再",entry["source_limit_note"])
        self.assertIn("archived_unmaintained",self.js)
        self.assertIn("sys-lifecycle-warning",self.js)
        self.assertNotIn("已证实用于 MAI",entry["relation"])

    def test_ctat_and_mast_correct_category_and_origin(self):
        ctat=self.systems["CTAT / Cognitive Tutor (LearnLab)"]
        self.assertIn("cdn.ctat.cs.cmu.edu",ctat["source_url"])
        self.assertIn("示例轨迹",ctat["architecture"])
        self.assertIn("不等于",ctat["source_limit_note"])
        self.assertIn("免费研究",self.stack[ctat["name"]]["open_source_status"])
        mast=self.systems["MAST (Berkeley, Multi-Agent System Traces)"]
        self.assertIn("sky.cs.berkeley.edu",mast["source_url"])
        self.assertEqual(mast["lifecycle_status"],"research_taxonomy")
        self.assertIn("14 类失败模式",mast["architecture"])
        self.assertIn("不是针对",mast["relation"])
        self.assertTrue(any("2503.13657" in x["url"] for x in mast["additional_source_links"]))

    def test_vendor_claims_not_confused_with_independent_learning_effect(self):
        khan=self.systems["Khanmigo"]
        ccr=self.systems["CocoRobo SMART Suite"]
        self.assertIn("不凭官网宣传",khan["source_limit_note"])
        self.assertNotIn("~700K",khan["relation"])
        self.assertNotIn("Langfuse",khan["architecture"])
        self.assertIn("厂商",ccr["architecture"])
        self.assertIn("官网自报",ccr["source_limit_note"])
        self.assertEqual(ccr["source_url"],"https://cocorobo.hk/smart")
        self.assertTrue(any("research" in x["url"] for x in ccr["additional_source_links"]))
        for name in (khan["name"],ccr["name"]):
            self.assertNotIn("已证明提高成绩",self.cards[name]["relation_to_mai_miracle"])


if __name__=="__main__":
    unittest.main()
