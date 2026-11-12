"""P47: search-discovered papers must pass an education + AI relevance gate."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "weekly_watch_p47", ROOT / "scripts" / "weekly_ai_education_watch.py")
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)


def cand(title, summary="", tags=("arxiv-search",)):
    return {"title": title, "summary": summary, "tags": list(tags),
            "url": "https://arxiv.org/abs/2610.00001"}


class RelevanceGate(unittest.TestCase):
    def test_off_topic_search_hits_are_rejected(self):
        for title in (
            "ViFA-Council: Multi-Agent LLM Deliberation for Vietnamese Folk Art Generation",
            "Mining the Design Space of Multi-Agent Workflows",
            "Deep Research in Physical Sciences: A Multi-Agent Framework",
            "Maintaining domain consistency in massive smart grids",
        ):
            with self.subTest(title=title):
                self.assertFalse(watch.is_relevant(cand(title)))

    def test_education_plus_ai_is_accepted(self):
        for title in (
            "MAVE: A Multi-Agent Framework for Grounded Pedagogical Feedback",
            "Exploring AI Peer in Collaborative Mathematics Learning",
            "Voice-Based AI Feedback in Higher Education: A Field Study",
        ):
            with self.subTest(title=title):
                self.assertEqual(watch.scope_decision(cand(title)),
                                 (True, "education_and_ai"))

    def test_strong_terms_are_whole_word_and_case_sensitive(self):
        self.assertEqual(watch.scope_decision(cand("SSRL in small groups"))[1],
                         "strong_term")
        self.assertFalse(watch.is_in_scope(cand("A miracle of main memory design")))

    def test_education_without_ai_is_rejected_with_reason(self):
        self.assertEqual(
            watch.scope_decision(cand("Volunteer Moderation in a Higher Education Group")),
            (False, "no_ai_agent_context"))

    def test_abstract_needs_two_education_terms_when_title_has_none(self):
        one = cand("A benchmark for agents", "We test LLM agents on tasks used by students.")
        two = cand("A benchmark for agents",
                   "LLM agents support students and teachers in the classroom.")
        self.assertFalse(watch.is_in_scope(one))
        self.assertTrue(watch.is_in_scope(two))

    def test_machine_learning_jargon_is_not_education(self):
        # Titles from a live arXiv sample (2026-11-12) that an earlier gate let in.
        for title in (
            "SteerDistill: Quantizing LLM Agents via Closed-Loop Teacher Steering",
            "Teaching the Harness: Student-Aware Skill Transfer for LLM Agents",
            "CIDERS: Cloud-Edge LLM Collaborative Learning via Bilevel Optimization",
            "Decentralized collaborative continual learning for agents",
        ):
            with self.subTest(title=title):
                self.assertEqual(watch.scope_decision(cand(title)),
                                 (False, "ml_jargon_not_education"))
        distill = cand("A benchmark for agents",
                       "We distill a teacher model into student agents used in classrooms.")
        self.assertFalse(watch.is_in_scope(distill))
        # A hard education term in the title still wins.
        self.assertTrue(watch.is_in_scope(
            cand("Distilling an LLM tutor for classroom mathematics tutoring")))
        # "agentic engagement" is psychology, not an AI context.
        self.assertEqual(
            watch.scope_decision(cand("Student motivation and agentic engagement in schools")),
            (False, "no_ai_agent_context"))

    def test_weekly_cap_and_queue_aware_admission(self):
        def paper(n):
            return {"title": f"AI tutoring study {n}", "source_id": "s",
                    "url": f"https://arxiv.org/abs/2611.{n:05d}"}
        existing = [{"url": paper(1)["url"]}]
        queue = {"items": [
            {"url": paper(2)["url"], "status": "dismissed"},
            {"url": paper(3)["url"], "status": "rejected_by_filter"},
            {"url": paper(4)["url"], "status": "restored"},
        ]}
        candidates = [paper(n) for n in range(1, 9)]
        admitted, held = watch.limit_new_papers(candidates, existing, queue, 2)
        urls = [c["url"] for c in admitted]
        # known paper passes; queued/dismissed are skipped; 2 new admitted.
        self.assertEqual(urls, [paper(1)["url"], paper(4)["url"], paper(5)["url"]])
        self.assertEqual([h["url"] for h in held], [paper(n)["url"] for n in (6, 7, 8)])
        self.assertTrue(all(h["reason"] == "weekly_cap" for h in held))
        # A cap of zero admits nothing new and never crashes.
        admitted, held = watch.limit_new_papers(candidates, existing, None, 0)
        self.assertEqual([c["url"] for c in admitted], [paper(1)["url"]])
        self.assertEqual(len(held), 7)

    def test_curated_registry_sources_bypass_gate(self):
        self.assertTrue(watch.is_in_scope(cand("AutoGen", tags=("arxiv",))))

    def test_rejected_candidates_reach_review_queue(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review-queue.json"
            rejected = [{"title": "X", "url": "https://arxiv.org/abs/2610.00001",
                         "source_id": "s", "reason": "no_education_context"}]
            self.assertEqual(watch.update_review_queue(path, rejected, "2026-W47"), 1)
            # Same paper via its DOI form is not queued twice.
            again = [{"title": "X", "url": "https://doi.org/10.48550/arXiv.2610.00001",
                      "source_id": "s", "reason": "no_education_context"}]
            self.assertEqual(watch.update_review_queue(path, again, "2026-W48"), 0)
            self.assertEqual(len(json.loads(path.read_text())["items"]), 1)

    def test_published_papers_all_pass_gate_or_are_core(self):
        papers = json.loads((ROOT / "docs/data/papers.json").read_text(encoding="utf-8"))
        queue = json.loads((ROOT / "docs/data/review-queue.json").read_text(encoding="utf-8"))
        queued = {watch.paper_key(x["url"]) for x in queue["items"]}
        for p in papers:
            with self.subTest(title=p["title"]):
                self.assertNotIn(watch.paper_key(p["url"]), queued)
                core = not str(p.get("first_seen") or "").startswith("2026-11")
                self.assertTrue(core or watch.is_in_scope(p))


class PaperIdentity(unittest.TestCase):
    def test_arxiv_url_forms_share_one_key(self):
        keys = {watch.paper_key(u) for u in (
            "https://arxiv.org/abs/2501.00083", "https://arxiv.org/html/2501.00083v1",
            "https://arxiv.org/pdf/2501.00083", "https://doi.org/10.48550/arXiv.2501.00083")}
        self.assertEqual(keys, {"arxiv:2501.00083"})

    def test_merge_does_not_duplicate_other_url_form(self):
        existing = [{"id": "a", "title": "Old title", "record_type": "scholarly_paper",
                     "url": "https://arxiv.org/html/2501.00083"}]
        merged, added = watch.merge_papers(existing, [
            {"title": "Different title", "url": "https://arxiv.org/abs/2501.00083"}])
        self.assertEqual((len(merged), added), (1, 0))

    def test_year_comes_from_arxiv_identifier(self):
        self.assertEqual(watch._guess_year("https://arxiv.org/abs/2610.26943 since 2023"), "2026")


if __name__ == "__main__":
    unittest.main()
