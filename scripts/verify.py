#!/usr/bin/env python3
"""Validate the actual photo catalogue and the safe publication directory."""
import json
import hashlib
import base64
from xml.etree import ElementTree as ET
from pathlib import Path
import re
from urllib.parse import unquote

from seo import page_names
from PIL import Image
from process_images import ROOT, EXIF_COPYRIGHT, is_country_cover


def verify():
    catalogue = json.loads((ROOT / 'data/photos.json').read_text())
    registry = json.loads((ROOT / 'data/image-registry.json').read_text())
    photos = catalogue['photos']
    ids = [p['id'] for p in photos]
    assert len(ids) == len(set(ids)), 'Duplicate photo IDs'
    assert catalogue['hero'] in ids and catalogue['portrait'] in ids, 'Missing site photos'
    actual_photos = {p.relative_to(ROOT).as_posix() for folder in ('images', 'poy') for p in (ROOT / folder).rglob('*.webp')}
    listed_photos = {unquote(photo['src']) for photo in photos}
    assert actual_photos == listed_photos, 'Uncatalogued photos: run scripts/process_images.py'
    actual_countries = sorted(p.name.title() for p in (ROOT / 'poy/countries').iterdir() if p.is_dir())
    assert actual_countries == catalogue['countries'], 'Country folders changed: run scripts/process_images.py'
    count = 0
    public_files = page_names(catalogue) | {'sitemap.xml', 'robots.txt', 'assets/site.css', 'assets/site.js', 'data/photos.json', '_headers', '.nojekyll'}
    for page in page_names(catalogue) - {'404.html'}:
        markup = (ROOT / 'dist' / page).read_text()
        assert 'data-photo=' not in markup and 'data-icon=' not in markup, f'Unbuilt template: {page}'
        assert len(re.findall(r'<h1\b', markup)) == 1, f'Expected one primary heading: {page}'
        assert len(re.findall(r'<link rel="canonical"', markup)) == 1, f'Canonical URL missing or duplicated: {page}'
        structured = re.search(r'<script type="application/ld\+json">(.*?)</script>', markup)
        assert structured, f'Missing structured data: {page}'
        json.loads(structured[1])
        token = "'sha256-" + base64.b64encode(hashlib.sha256(structured[1].encode()).digest()).decode() + "'"
        assert token in markup and token in (ROOT / 'dist/_headers').read_text(), f'Structured data blocked by CSP: {page}'
        assert 'class="photo-item"' in markup or 'class="destination"' in markup or 'id="empty-state"' in markup, f'No crawlable content: {page}'
        for size in (32, 96, 180):
            assert f'href="assets/icons/{size}/{catalogue["favicon"]}.png"' in markup, f'Missing icon link: {page}'
    homepage = (ROOT / 'dist/index.html').read_text()
    for role in ('hero', 'portrait', 'logo'):
        photo = next(p for p in photos if p['id'] == catalogue[role])
        assert f'src="{photo["src"]}"' in homepage, f'Missing {role} image in homepage'
    for photo in photos:
        assert str(photo['id']) in registry
        assert 1000 <= photo['id'] <= 1000000, photo['id']
        for src in [photo['src'], *(v['src'] for v in photo['variants'])]:
            relative = unquote(src)
            path = ROOT / relative
            named_cover = src == photo['src'] and is_country_cover(Path(relative)) and path.suffix == '.webp'
            assert named_cover or (re.fullmatch(r'\d+\.webp', path.name) and int(path.stem) == photo['id']), src
            if named_cover:
                assert catalogue['covers'].get(photo['country']) == photo['id'], f'Cover not selected: {src}'
            with Image.open(path) as image:
                assert image.format == 'WEBP', src
                assert image.getexif().get(315) == 'Arjun Sarkar', src
                assert image.getexif().get(33432) == EXIF_COPYRIGHT, src
                assert b'Arjun Sarkar' in image.info.get('xmp', b''), src
                assert 34853 not in image.getexif(), f'GPS metadata: {src}'
                if src == photo['src']:
                    assert image.size == (photo['width'], photo['height']), src
                    assert max(image.size) <= 2560, src
                else:
                    variant = next(v for v in photo['variants'] if v['src'] == src)
                    assert image.width == variant['width'], src
            assert (ROOT / 'dist' / relative).is_file(), f'Not published: {src}'
            public_files.add(relative)
            count += 1
    for size in (32, 96, 180):
        icon_path = f'assets/icons/{size}/{catalogue["favicon"]}.png'
        with Image.open(ROOT / 'dist' / icon_path) as icon:
            assert icon.size == (size, size) and '2026 Arjun Sarkar' in icon.info['Copyright']
        public_files.add(icon_path)
    sitemap = ET.parse(ROOT / 'dist/sitemap.xml')
    namespace = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    sitemap_urls = [entry.text for entry in sitemap.findall('s:url/s:loc', namespace)]
    populated = {p['country'] for p in photos if p['country']}
    assert len(sitemap_urls) == len(populated) + 2 and len(sitemap_urls) == len(set(sitemap_urls)), 'Missing or duplicate sitemap pages'
    actual = {p.relative_to(ROOT / 'dist').as_posix() for p in (ROOT / 'dist').rglob('*') if p.is_file()}
    assert actual == public_files, f'Unexpected or missing public files: {actual ^ public_files}'
    inputs = [p for directory in ('images', 'poy') for p in (ROOT / directory).rglob('*') if p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.tif', '.tiff')]
    assert not inputs, f'Unprocessed images: {inputs}'
    print(f'PASS: {len(photos)} photos, {count} WebP files with copyright metadata, {len(catalogue["countries"])} countries; publication allowlist verified.')


if __name__ == '__main__':
    verify()
