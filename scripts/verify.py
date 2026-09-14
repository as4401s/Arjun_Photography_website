#!/usr/bin/env python3
"""Validate the actual photo catalogue and the safe publication directory."""
import json
from pathlib import Path
import re
from urllib.parse import unquote

from PIL import Image
from process_images import ROOT, EXIF_COPYRIGHT


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
    public_files = {'index.html', 'destinations.html', 'assets/site.css', 'assets/site.js', 'data/photos.json', '_headers', '.nojekyll'}
    for photo in photos:
        assert str(photo['id']) in registry
        for src in [photo['src'], *(v['src'] for v in photo['variants'])]:
            relative = unquote(src)
            path = ROOT / relative
            assert re.fullmatch(r'\d+\.webp', path.name) and 1000 <= int(path.stem) <= 1000000, src
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
    for size in (32, 180):
        icon_path = f'assets/icons/{size}/{catalogue["favicon"]}.png'
        with Image.open(ROOT / 'dist' / icon_path) as icon:
            assert icon.size == (size, size) and '2026 Arjun Sarkar' in icon.info['Copyright']
        public_files.add(icon_path)
    actual = {p.relative_to(ROOT / 'dist').as_posix() for p in (ROOT / 'dist').rglob('*') if p.is_file()}
    assert actual == public_files, f'Unexpected or missing public files: {actual ^ public_files}'
    inputs = [p for directory in ('images', 'poy') for p in (ROOT / directory).rglob('*') if p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.tif', '.tiff')]
    assert not inputs, f'Unprocessed images: {inputs}'
    print(f'PASS: {len(photos)} photos, {count} WebP files with copyright metadata, {len(catalogue["countries"])} countries; publication allowlist verified.')


if __name__ == '__main__':
    verify()
