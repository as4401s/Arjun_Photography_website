"""Build crawlable galleries and metadata from the same public photo catalogue."""
from __future__ import annotations

import base64
import hashlib
import html
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit, urljoin
from xml.etree import ElementTree as ET

BRAND = 'Our Travel Photobook'
AUTHOR = 'Arjun Sarkar'
SOCIAL = ['https://www.instagram.com/ourtravelphotobook/', 'https://www.youtube.com/@ourtravelphotobook']


def validate_site_url(value: str) -> str:
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or any(c.isspace() for c in value)
            or any(part in ('.', '..') for part in parsed.path.split('/'))):
        raise ValueError('SITE_URL must be an absolute HTTPS URL without credentials, query, or fragment.')
    return value.rstrip('/') + '/'


def country_page(country: str) -> str:
    ascii_name = unicodedata.normalize('NFKD', country).encode('ascii', 'ignore').decode().lower()
    slug = re.sub(r'[^a-z0-9]+', '-', ascii_name).strip('-')
    if not slug:
        raise ValueError(f'Country needs a usable URL name: {country!r}')
    return f'{slug}-photography.html'


def page_names(catalogue: dict) -> set[str]:
    pages = [country_page(c) for c in catalogue['countries']]
    if len(pages) != len(set(pages)):
        raise ValueError('Country names produce duplicate page URLs.')
    return {'index.html', 'destinations.html', '404.html', *pages}


def country_description(country: str, count: int, summary: str = '') -> str:
    if count and summary:
        return f'{summary} {count} photographs by {AUTHOR} for {BRAND}.'
    return (f'{count} travel photographs from {country} by {AUTHOR}, shared through {BRAND}.'
            if count else f'Photographs from {country} will be added to {BRAND} as the collection grows.')


def image_url(photo: dict, src: str | None = None) -> str:
    url = src or photo['src']
    return f'{url}?v={photo["revision"]}' if photo.get('revision') else url


def image_markup(photo: dict, sizes: str, alt: str | None = None) -> str:
    variants = [*photo['variants'], {'src': photo['src'], 'width': photo['width']}]
    srcset = ', '.join(f'{image_url(photo, v["src"])} {v["width"]}w' for v in variants)
    e = html.escape
    return (f'<img src="{e(image_url(photo))}" srcset="{e(srcset)}" sizes="{e(sizes)}" '
            f'width="{int(photo["width"])}" height="{int(photo["height"])}" '
            f'alt="{e(photo["alt"] if alt is None else alt)}" loading="lazy" decoding="async">')


def photo_markup(photos: list[dict]) -> str:
    return '\n'.join(f'<a class="photo-item" href="{html.escape(image_url(p))}" '
                     f'aria-label="{html.escape(p["alt"])}">'
                     f'{image_markup(p, "(max-width: 600px) 90vw, (max-width: 900px) 44vw, 29vw")}</a>'
                     for p in photos)


def cover_for(catalogue: dict, country: str, photos: list[dict]) -> dict | None:
    return (next((p for p in photos if p['src'].lower().endswith('/cover.webp')), None)
            or next((p for p in photos if p['id'] == catalogue['covers'].get(country)), None)
            or (photos[0] if photos else None))


def destination_markup(catalogue: dict) -> str:
    cards = []
    for country in catalogue['countries']:
        photos = [p for p in catalogue['photos'] if p['country'] == country]
        cover = cover_for(catalogue, country, photos)
        image = (f'<div class="destination-image">{image_markup(cover, "(max-width: 600px) 90vw, (max-width: 900px) 44vw, 29vw", "")}'
                 '<span class="destination-arrow" aria-hidden="true">↗</span></div>' if cover else
                 '<div class="destination-empty"><span>Coming soon</span></div>')
        count = f'{len(photos)} photographs' if photos else 'A story still to come'
        cards.append(f'<a class="destination" href="{country_page(country)}">{image}'
                     f'<div class="destination-meta"><h3>{html.escape(country)}</h3><span>{count}</span></div></a>')
    return '\n'.join(cards)


def structured_data(base: str, path: str, title: str, description: str, photos: list[dict], country: str = '') -> dict:
    url = urljoin(base, path if path != 'index.html' else '')
    graph = [
        {'@type': 'Person', '@id': base + '#photographer', 'name': AUTHOR,
         'url': base + '#about', 'description': 'Travel and landscape photographer based in Germany.'},
        {'@type': 'Organization', '@id': base + '#publisher', 'name': BRAND,
         'alternateName': 'ourtravelphotobook', 'url': base,
         'founder': {'@id': base + '#photographer'}, 'sameAs': SOCIAL},
        {'@type': 'WebSite', '@id': base + '#website', 'url': base, 'name': BRAND,
         'alternateName': ['ourtravelphotobook', 'OurTravelPhotobook'],
         'publisher': {'@id': base + '#publisher'}, 'inLanguage': 'en'},
        {'@type': 'CollectionPage', '@id': url + '#page', 'url': url, 'name': title,
         'description': description, 'isPartOf': {'@id': base + '#website'},
         'author': {'@id': base + '#photographer'}, 'publisher': {'@id': base + '#publisher'},
         'inLanguage': 'en', 'mainEntity': {'@id': url + '#photographs'}},
        {'@type': 'ItemList', '@id': url + '#photographs', 'numberOfItems': len(photos),
         'itemListElement': [{'@type': 'ListItem', 'position': i, 'item': {
             '@type': 'ImageObject', 'contentUrl': urljoin(base, image_url(p)),
             'name': p.get('title') or p['alt'], 'caption': p['alt'],
             'width': p['width'], 'height': p['height'],
             'creator': {'@id': base + '#photographer'}, 'creditText': AUTHOR,
             'copyrightNotice': f'© 2026 {AUTHOR}. All rights reserved.'}}
             for i, p in enumerate(photos, 1)]},
    ]
    if country:
        graph[3]['about'] = {'@type': 'Country', 'name': country}
    if path != 'index.html':
        crumbs = [('', 'Home'), ('destinations.html', 'Destinations')]
        if country:
            crumbs.append((path, country))
        graph.append({'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i, 'name': name, 'item': urljoin(base, link)}
            for i, (link, name) in enumerate(crumbs, 1)]})
    return {'@context': 'https://schema.org', '@graph': graph}


def metadata(markup: str, base: str, path: str, title: str, description: str,
             photos: list[dict], social_photo: dict, country: str = '') -> tuple[str, str]:
    # Replace template metadata as one unit to prevent stale or duplicate canonicals.
    markup = re.sub(r'<title>.*?</title>|<link rel="canonical"[^>]*>|<meta (?:property="og:[^"]+"|name="(?:description|twitter:[^"]+)")[^>]*>', '', markup)
    url = urljoin(base, '' if path == 'index.html' else path)
    e = html.escape
    tags = (f'<title>{e(title)}</title>\n<meta name="description" content="{e(description)}">'
            '<meta name="robots" content="index, follow, max-image-preview:large">'
            f'<link rel="canonical" href="{e(url)}">'
            f'<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(description)}">'
            f'<meta property="og:url" content="{e(url)}"><meta property="og:site_name" content="{BRAND}">'
            '<meta property="og:type" content="website"><meta property="og:locale" content="en_US">'
            f'<meta property="og:image" content="{e(urljoin(base, image_url(social_photo)))}">'
            f'<meta property="og:image:alt" content="{e(social_photo["alt"])}">'
            f'<meta property="og:image:width" content="{social_photo["width"]}">'
            f'<meta property="og:image:height" content="{social_photo["height"]}">'
            '<meta name="twitter:card" content="summary_large_image">')
    data = json.dumps(structured_data(base, path, title, description, photos, country), ensure_ascii=False, separators=(',', ':'))
    # Prevent editorial text from closing a script tag; authorize only this exact JSON block in CSP.
    data = data.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    csp_hash = "'sha256-" + base64.b64encode(hashlib.sha256(data.encode()).digest()).decode() + "'"
    markup = markup.replace("script-src 'self';", f"script-src 'self' {csp_hash};")
    return markup.replace('</head>', tags + '\n<script type="application/ld+json">' + data + '</script>\n</head>'), csp_hash


def enrich_pages(stage: Path, catalogue: dict, base: str) -> None:
    page_names(catalogue)  # Reject colliding slugs before writing any output.
    home = (stage / 'index.html').read_text()
    destination = (stage / 'destinations.html').read_text()
    selected = [p for p in catalogue['photos'] if p['selected']]
    hero = next(p for p in catalogue['photos'] if p['id'] == catalogue['hero'])
    home = home.replace('<div class="photo-grid" id="photo-grid"></div>', f'<div class="photo-grid" id="photo-grid">{photo_markup(selected)}</div>')
    home = home.replace('Loading the photographs…', '')
    home = home.replace('Enable JavaScript to browse the photo collections. You can still get in touch using the links below.', 'Select a photograph to open the full image. Enable JavaScript for the slideshow viewer.')
    destination = destination.replace('Enable JavaScript to browse the photo collections. You can still get in touch using the links below.', 'Select a destination or photograph to explore the collection.')
    description = f'Explore travel photography from {len(catalogue["countries"])} countries by {AUTHOR}, the Germany-based photographer behind {BRAND}.'
    destination = destination.replace('A few moments I keep coming back to.', description)
    destination = destination.replace('Loading the photographs…', f'{len(catalogue["countries"])} destinations to explore.')
    index = destination.replace('<div class="photo-grid" id="photo-grid"></div>', '<div class="photo-grid" id="photo-grid" hidden></div>')
    index = index.replace('<div class="destinations-grid" id="destinations-grid" hidden></div>', f'<div class="destinations-grid" id="destinations-grid">{destination_markup(catalogue)}</div>')
    covers = [cover_for(catalogue, c, [p for p in catalogue['photos'] if p['country'] == c]) for c in catalogue['countries']]
    pages = [('', 'index.html', home, f'{BRAND} | Travel Photography by {AUTHOR}',
              f'{BRAND} is the travel photography portfolio of {AUTHOR}. Explore landscapes, city life and travel stories from Europe and Asia.', selected, hero),
             ('', 'destinations.html', index, f'Travel Photography Destinations | {BRAND}', description, [p for p in covers if p], hero)]
    for country in catalogue['countries']:
        photos = sorted([p for p in catalogue['photos'] if p['country'] == country], key=lambda p: p['id'])
        text = country_description(country, len(photos), catalogue.get('countrySummaries', {}).get(country, ''))
        markup = destination.replace('data-page="destinations"', f'data-page="destinations" data-country="{html.escape(country)}"')
        markup = markup.replace('<h1 id="gallery-title">The destinations.</h1>', f'<h1 id="gallery-title">{html.escape(country)} photography.</h1>')
        markup = markup.replace(html.escape(description), html.escape(text))
        markup = markup.replace(f'{len(catalogue["countries"])} destinations to explore.', '')
        markup = markup.replace('<div class="photo-grid" id="photo-grid"></div>', f'<div class="photo-grid" id="photo-grid">{photo_markup(photos)}</div>')
        markup = markup.replace('id="collection-toolbar" hidden', 'id="collection-toolbar"')
        markup = markup.replace('<button class="text-button" id="back-button" type="button">← All destinations</button>', '<a class="text-button" id="back-button" href="destinations.html">← All destinations</a>')
        markup = markup.replace('<span id="collection-count"></span>', f'<span id="collection-count">{len(photos)} photographs</span>')
        if not photos:
            markup = markup.replace('id="empty-state" hidden', 'id="empty-state"')
        pages.append((country, country_page(country), markup, f'{country} Travel Photography | {BRAND}', text, photos, cover_for(catalogue, country, photos) or hero))

    hashes = []
    sitemap = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9', attrib={'xmlns:image': 'http://www.google.com/schemas/sitemap-image/1.1'})
    for country, path, markup, title, desc, photos, cover in pages:
        markup, csp_hash = metadata(markup, base, path, title, desc, photos, cover, country)
        (stage / path).write_text(markup)
        hashes.append(csp_hash)
        # Empty future collections are linked for visitors but not submitted for indexing yet.
        if country and not photos:
            (stage / path).write_text(markup.replace('index, follow, max-image-preview:large', 'noindex, follow'))
            continue
        node = ET.SubElement(sitemap, 'url')
        ET.SubElement(node, 'loc').text = urljoin(base, '' if path == 'index.html' else path)
        for photo in photos:
            image = ET.SubElement(node, 'image:image')
            ET.SubElement(image, 'image:loc').text = urljoin(base, image_url(photo))
    ET.ElementTree(sitemap).write(stage / 'sitemap.xml', encoding='utf-8', xml_declaration=True)
    (stage / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {base}sitemap.xml\n')
    headers = (stage / '_headers').read_text().replace("script-src 'self';", "script-src 'self' " + ' '.join(sorted(set(hashes))) + ';')
    (stage / '_headers').write_text(headers)
    (stage / '404.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex">'
        '<title>Page not found | Our Travel Photobook</title></head><body><main><h1>Page not found</h1>'
        f'<p>This page may have moved. <a href="{html.escape(base)}">Return to Our Travel Photobook</a>.</p></main></body></html>')
