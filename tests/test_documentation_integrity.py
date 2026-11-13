"""P52: keep visitor-facing README and operator runbook navigable and accurate."""
from __future__ import annotations

import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = (ROOT / "README.md", ROOT / "RUNBOOK.md")
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\s]+)\)")


class DocumentationIntegrity(unittest.TestCase):
    def test_markdown_code_fences_are_balanced(self):
        for doc in DOCUMENTS:
            with self.subTest(document=doc.name):
                opening = None
                for lineno, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
                    marker = re.match(r"^\s*(`{3,})([^`]*)$", line)
                    if not marker:
                        continue
                    fence, rest = marker.groups()
                    if opening is None:
                        self.assertTrue(rest.strip() == "" or re.fullmatch(r"[\w-]+", rest.strip()),
                                        f"{doc.name}:{lineno}: malformed fence info string")
                        opening = lineno
                    else:
                        self.assertEqual(rest.strip(), "", f"{doc.name}:{lineno}: closing fence has text")
                        opening = None
                self.assertIsNone(opening, f"{doc.name}:{opening}: unclosed Markdown code fence")

    def test_local_markdown_links_resolve(self):
        checked = 0
        for doc in DOCUMENTS:
            body = doc.read_text(encoding="utf-8")
            for href in MARKDOWN_LINK.findall(body):
                url = unquote(href.split("#", 1)[0])
                if not url or urlparse(url).scheme or url.startswith("//"):
                    continue
                with self.subTest(document=doc.name, href=href):
                    self.assertTrue((doc.parent / url).exists(),
                                    f"missing local document target: {doc.name} -> {href}")
                checked += 1
        self.assertGreaterEqual(checked, 10)

    def test_github_pages_deployment_description_matches_workflow(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        runbook = (ROOT / "RUNBOOK.md").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
        self.assertIn("actions/deploy-pages@v4", workflow)
        self.assertIn("actions/upload-pages-artifact@v3", workflow)
        self.assertIn("GitHub Actions", readme)
        self.assertIn("GitHub Actions", runbook)
        self.assertNotIn("legacy build mode", readme)
        self.assertNotIn("Deploy from a branch", readme)

    def test_linked_site_sections_exist(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        site = (ROOT / "docs/index.html").read_text(encoding="utf-8")
        fragments = re.findall(r"https://conanxin\.github\.io/ai-education-system-map/#([a-z0-9-]+)", readme)
        self.assertGreaterEqual(len(fragments), 5)
        for fragment in fragments:
            with self.subTest(section=fragment):
                self.assertIn(f'id="{fragment}"', site)

    def test_legacy_seed_import_is_not_advertised_as_live_rebuild(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        runbook = (ROOT / "RUNBOOK.md").read_text(encoding="utf-8")
        code = (ROOT / "scripts/build_from_report.py").read_text(encoding="utf-8")
        self.assertIn("research-migration.json", runbook)
        self.assertIn("Typed P42 live corpus exists", code)
        self.assertIn("--data-dir /tmp/atlas-seed-preview", runbook)
        self.assertIn("[RUNBOOK.md](RUNBOOK.md)", readme)
        self.assertIn("--dry-run", runbook)


if __name__ == "__main__":
    unittest.main()
