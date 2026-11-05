"""P46: precise source locations, not invented page numbers or unpinned PDFs."""
import json
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
import unittest

ROOT=Path(__file__).resolve().parents[1]

class EvidenceLocatorTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((ROOT/'docs/data/research-deep-dives.json').read_text())

    def test_three_studies_have_nine_unique_checked_locations(self):
        seen=set()
        for s in self.data['studies']:
            loc=s.get('evidence_locations',[])
            self.assertEqual(len(loc),3,s['id'])
            self.assertEqual(s['locator_reviewed_at'],'2026-11-05')
            for x in loc:
                self.assertNotIn(x['id'],seen);seen.add(x['id'])
                self.assertTrue(x['locator'])
                self.assertTrue(x['supports'])
                self.assertTrue(x['source_version'])
                self.assertTrue(x['url'].startswith('https://'))
        self.assertEqual(len(seen),9)

    def test_pdf_offsets_and_version_are_explicit(self):
        byid={x['id']:x for x in self.data['studies']}
        for s_id,expected in [('simclass-2025',[4,5,9]),('mass-2025',[5,7,20])]:
            loc=byid[s_id].get('evidence_locations',[])
            self.assertEqual([x['pdf_page'] for x in loc],expected)
            for x in loc:
                self.assertEqual(x['format'],'pdf')
                self.assertEqual(urlsplit(x['url']).fragment,'page='+str(x['pdf_page']))
                self.assertTrue(x['printed_page'])
                if s_id=='mass-2025': self.assertIn('2502.02533v2',x['url'])
        for x in byid['human-ai-ssrl-2023'].get('evidence_locations',[]):
            self.assertEqual(x['format'],'html_section')
            self.assertIsNone(x['pdf_page'])
            self.assertIn('#:~:text=',x['url'])

    def test_renderer_is_wired_and_defends_links(self):
        js=(ROOT/'docs/assets/app.js').read_text()
        css=(ROOT/'docs/assets/style.css').read_text()
        self.assertIn('function renderEvidenceLocations(study)',js)
        self.assertIn('host.appendChild(renderEvidenceLocations(study))',js)
        self.assertIn('safeExternalHref(location.url)',js)
        self.assertIn('.evidence-location-list',css)

if __name__=='__main__': unittest.main()
