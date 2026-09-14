"""Regression checks for crawlability, metadata, and safe generated markup."""
import base64
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
import re
import tempfile
import unittest
from xml.etree import ElementTree as ET

from seo import enrich_pages, validate_site_url, country_page, page_names

ROOT = Path(__file__).resolve().parents[1]


class Document(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.tags = []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class SearchPagesTests(unittest.TestCase):
    def photo(self, number, country='', selected=False):
        return {'id': number, 'src': f'poy/countries/{country.lower()}/cover.webp' if country else f'poy/{number}.webp',
                'width': 1200, 'height': 800, 'variants': [{'src': f'assets/photos/480/{number}.webp', 'width': 480}],
                'revision': '0123456789ab', 'alt': '</script><script>alert("caption")</script>',
                'title': '', 'country': country, 'selected': selected}

    def test_crawlable_gallery_metadata_and_safe_serialization(self):
        catalogue = {'photos': [self.photo(1000, selected=True), self.photo(1001, 'France')],
                     'countries': ['France', 'Japan'], 'covers': {'France': 1001}, 'hero': 1000}
        with tempfile.TemporaryDirectory() as folder:
            stage = Path(folder)
            template = (ROOT / 'index.html').read_text()
            destination = template.replace('data-page="home"', 'data-page="destinations"').replace(
                '<h2 id="gallery-title">Highlights<span class="accent">.</span></h2>', '<h1 id="gallery-title">The destinations.</h1>')
            for section in ('home', 'about', 'travelbook'):
                destination = re.sub(r'<section\b[^>]*\bid="' + section + r'"[^>]*>.*?</section>', '', destination, flags=re.S)
            (stage / 'index.html').write_text(template)
            (stage / 'destinations.html').write_text(destination)
            (stage / '_headers').write_text((ROOT / '_headers').read_text())
            enrich_pages(stage, catalogue, 'https://example.com/portfolio/')
            self.assertEqual({p.name for p in stage.glob('*.html')}, page_names(catalogue))
            index = (stage / 'destinations.html').read_text()
            self.assertIn('href="france-photography.html"', index)
            france = (stage / 'france-photography.html').read_text()
            self.assertIn('1 travel photographs from France', france)
            self.assertIn('data-country="France"', france)
            self.assertIn('class="photo-item"', france)
            doc = Document(france)
            self.assertFalse(any(k.startswith('on') for _, attrs in doc.tags for k in attrs))
            self.assertEqual(sum(tag == 'h1' for tag, _ in doc.tags), 1)
            self.assertEqual(sum(tag == 'link' and attrs.get('rel') == 'canonical' for tag, attrs in doc.tags), 1)
            self.assertFalse(any(tag == 'script' and not attrs.get('src') and attrs.get('type') != 'application/ld+json' for tag, attrs in doc.tags))
            raw = re.search(r'<script type="application/ld\+json">(.*?)</script>', france).group(1)
            data = json.loads(raw)
            self.assertEqual(data['@graph'][4]['numberOfItems'], 1)
            token = "'sha256-" + base64.b64encode(hashlib.sha256(raw.encode()).digest()).decode() + "'"
            self.assertIn(token, france)
            self.assertIn(token, (stage / '_headers').read_text())
            self.assertNotIn('unsafe-inline', (stage / '_headers').read_text())
            tree = ET.parse(stage / 'sitemap.xml')
            ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9', 'i': 'http://www.google.com/schemas/sitemap-image/1.1'}
            urls = [e.text for e in tree.findall('s:url/s:loc', ns)]
            self.assertEqual(urls, ['https://example.com/portfolio/', 'https://example.com/portfolio/destinations.html', 'https://example.com/portfolio/france-photography.html'])
            self.assertEqual(len(tree.findall('s:url/i:image/i:loc', ns)), 3)
            self.assertIn('noindex, follow', (stage / 'japan-photography.html').read_text())
            self.assertIn('https://example.com/portfolio/sitemap.xml', (stage / 'robots.txt').read_text())

    def test_invalid_urls_and_duplicate_country_slugs_fail(self):
        for value in ['http://example.com', 'javascript:alert(1)', 'https://a:b@example.com', 'https://example.com/?x=1', 'https://example.com/#about', 'https://example.com/../', '']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_site_url(value)
        self.assertEqual(validate_site_url('https://example.com/portfolio'), 'https://example.com/portfolio/')
        self.assertEqual(country_page('Czech Republic'), 'czech-republic-photography.html')
        with self.assertRaises(ValueError):
            page_names({'countries': ['Côte', 'Cote']})


if __name__ == '__main__':
    unittest.main()
