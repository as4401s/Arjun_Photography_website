#!/usr/bin/env python3
"""Build a deployable allowlisted static site; never publish the working directory."""
from __future__ import annotations
import argparse
from seo import enrich_pages, validate_site_url
import hashlib
import html
import json
import os
import re
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]


def build(root: Path = ROOT) -> Path:
    catalogue_path = root / 'data/photos.json'
    if not catalogue_path.exists():
        raise ValueError('Run python3 scripts/process_images.py first.')
    catalogue = json.loads(catalogue_path.read_text())
    from urllib.parse import unquote
    allowed = set()
    by_id = {photo['id']: photo for photo in catalogue['photos']}
    for photo in catalogue['photos']:
        for url in [photo['src'], *(v['src'] for v in photo['variants'])]:
            path = Path(unquote(url))
            if path.is_absolute() or '..' in path.parts or path.suffix != '.webp' or path.parts[0] not in ('images', 'poy', 'assets'):
                raise ValueError(f'Unsafe image path: {url}')
            if not (root / path).is_file() or not (root / path).resolve().is_relative_to(root.resolve()):
                raise ValueError(f'Missing or external image: {url}')
            allowed.add(path)
    template = (root / 'index.html').read_text()
    for role in ('hero', 'portrait', 'logo'):
        photo = by_id.get(catalogue[role])
        if not photo:
            raise ValueError(f'Select an existing {role} photograph in data/site.json and rerun processing.')
        srcset = ', '.join(f'{v["src"]} {v["width"]}w' for v in [*photo['variants'], {'src': photo['src'], 'width': photo['width']}])
        attributes = f'src="{html.escape(photo["src"], quote=True)}" srcset="{html.escape(srcset, quote=True)}" sizes="{ "100vw" if role == "hero" else "(max-width: 600px) 60vw, 35vw" }" width="{photo["width"]}" height="{photo["height"]}"'
        template = template.replace(f'data-photo="{role}"', attributes)
    favicon = by_id.get(catalogue.get('favicon'))
    if not favicon:
        raise ValueError('Select an existing favicon in data/site.json.')
    template = template.replace('data-icon="favicon"', f'href="{html.escape(favicon["src"], quote=True)}"')
    icon_links = (f'<link rel="icon" type="image/png" sizes="32x32" href="assets/icons/32/{favicon["id"]}.png">'
                  f'<link rel="icon" type="image/png" sizes="96x96" href="assets/icons/96/{favicon["id"]}.png">'
                  f'<link rel="apple-touch-icon" sizes="180x180" href="assets/icons/180/{favicon["id"]}.png">')
    template = template.replace('</head>', icon_links + '\n</head>')
    config = json.loads((root / 'data/site.json').read_text())
    # Hosting-specific metadata without changing the GitHub Pages configuration.
    if os.environ.get('SITE_URL'):
        config['url'] = os.environ['SITE_URL'].rstrip('/') + '/'
    config['url'] = validate_site_url(config.get('url', ''))
    if config.get('url'):
        from urllib.parse import urljoin
        url = config['url']
        hero = by_id[catalogue['hero']]
        metadata = (f'<link rel="canonical" href="{html.escape(url, quote=True)}">'
                    f'<meta property="og:url" content="{html.escape(url, quote=True)}">'
                    f'<meta property="og:image" content="{html.escape(urljoin(url, hero["src"]), quote=True)}">'
                    '<meta name="twitter:card" content="summary_large_image">')
        template = template.replace('</head>', metadata + '\n</head>')
    # Cache-busted application assets can be cached independently from the catalogue.
    for asset in ('assets/site.css', 'assets/site.js'):
        revision = hashlib.sha256((root / asset).read_bytes()).hexdigest()[:12]
        template = template.replace(f'"{asset}"', f'"{asset}?v={revision}"')
    stage = root / 'dist.next'
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir()
    # Browser and iOS icon formats are generated from the WebP master at build time.
    from PIL import Image, PngImagePlugin
    from process_images import COPYRIGHT, XMP
    with Image.open(root / unquote(favicon['src'])) as icon:
        metadata = PngImagePlugin.PngInfo()
        metadata.add_itxt('Copyright', COPYRIGHT)
        metadata.add_itxt('Author', 'Arjun Sarkar')
        metadata.add_itxt('XML:com.adobe.xmp', XMP.decode('utf-8'))
        for size in (32, 96, 180):
            target = stage / 'assets/icons' / str(size) / f'{favicon["id"]}.png'
            target.parent.mkdir(parents=True, exist_ok=True)
            icon.resize((size, size), Image.Resampling.LANCZOS).save(target, pnginfo=metadata, optimize=True)
    (stage / 'index.html').write_text(template)
    destination_page = template.replace('data-page="home"', 'data-page="destinations"')
    for section in ('home', 'travelbook', 'about'):
        destination_page = re.sub(r'<section\b[^>]*\bid="' + section + r'"[^>]*>.*?</section>', '', destination_page, flags=re.DOTALL)
    destination_page = destination_page.replace('<title>Our Travel Photobook — Photography by Arjun Sarkar</title>', '<title>Destinations — Our Travel Photobook</title>')
    destination_page = destination_page.replace('href="#home"', 'href="./"')
    destination_page = destination_page.replace('<h2 id="gallery-title">Highlights<span class="accent">.</span></h2>', '<h1 id="gallery-title">The destinations.</h1>')
    destination_page = destination_page.replace('The photographs', 'Explore / The destinations')
    if config.get('url'):
        destination_page = destination_page.replace(f'href="{html.escape(config["url"], quote=True)}"', f'href="{html.escape(config["url"], quote=True)}destinations.html"')
        destination_page = destination_page.replace(f'property="og:url" content="{html.escape(config["url"], quote=True)}"', f'property="og:url" content="{html.escape(config["url"], quote=True)}destinations.html"')
    (stage / 'destinations.html').write_text(destination_page)
    for path in sorted(allowed | {Path('assets/site.css'), Path('assets/site.js'), Path('data/photos.json'), Path('_headers')}):
        destination = stage / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = root / path
        if not source.resolve().is_relative_to(root.resolve()):
            raise ValueError(f'External public asset: {path}')
        shutil.copy2(source, destination)
    enrich_pages(stage, catalogue, config['url'])
    (stage / '.nojekyll').touch()
    dist = root / 'dist'
    if dist.exists():
        shutil.rmtree(dist)
    stage.rename(dist)
    print(f'Built dist/: {len(catalogue["photos"])} photographs, {len(allowed)} image files.')
    return dist


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        build()
    except (OSError, ValueError, KeyError) as error:
        print(f'Build failed: {error}', file=sys.stderr)
        sys.exit(1)
