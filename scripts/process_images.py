#!/usr/bin/env python3
"""Prepare photographs safely; see docs/IMAGES.md for the publishing workflow."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import sys
from urllib.parse import quote

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff'}
COPYRIGHT = '© 2026 Arjun Sarkar. All rights reserved.'
EXIF_COPYRIGHT = 'Copyright 2026 Arjun Sarkar. All rights reserved.'
VERSION = 1
XMP = ('<x:xmpmeta xmlns:x="adobe:ns:meta/">'
       '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
       '<rdf:Description xmlns:dc="http://purl.org/dc/elements/1.1/" '
       'xmlns:xmpRights="http://ns.adobe.com/xap/1.0/rights/">'
       '<dc:creator><rdf:Seq><rdf:li>Arjun Sarkar</rdf:li></rdf:Seq></dc:creator>'
       '<dc:rights><rdf:Alt><rdf:li xml:lang="x-default">' + COPYRIGHT +
       '</rdf:li></rdf:Alt></dc:rights><xmpRights:Marked>True</xmpRights:Marked>'
       '</rdf:Description></rdf:RDF></x:xmpmeta>').encode('utf-8')


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def border_box(image: Image.Image) -> tuple[int, int, int, int]:
    """Find connected, flat white edge strips, without trimming bright subjects.

    Work at native resolution. Require neutral near-white lines spanning >=98%
    of an edge and at least two agreeing sides.
    Stop on the first content line; never seek white pixels within the image.
    Compression tolerance is 20 levels; the strip itself must average >=245.
    """
    rgb = np.asarray(image.convert('RGB'))
    h, w = rgb.shape[:2]
    low = np.minimum(np.minimum(rgb[:, :, 0], rgb[:, :, 1]), rgb[:, :, 2])
    high = np.maximum(np.maximum(rgb[:, :, 0], rgb[:, :, 1]), rgb[:, :, 2])
    white = (low >= 235) & ((high.astype(np.int16) - low) <= 20)

    def depth(mask: np.ndarray, brightness: np.ndarray) -> int:
        limit = max(1, int(len(mask) * .20))
        result = 0
        for count, light in zip(mask[:limit], brightness[:limit]):
            if count < .98 or light < 245:
                break
            result += 1
        # Do not accept an unbounded blank edge (e.g. an overexposed sky).
        return 0 if result == limit else result

    rows = white.mean(axis=1)
    cols = white.mean(axis=0)
    row_light = low.mean(axis=1)
    col_light = low.mean(axis=0)
    top = depth(rows, row_light)
    bottom = depth(rows[::-1], row_light[::-1])
    left = depth(cols, col_light)
    right = depth(cols[::-1], col_light[::-1])
    depths = (left, top, right, bottom)
    # A confirmed frame may have gray shading or compression ringing on one side.
    # Relax only for this connected frame, never for isolated bright scene edges.
    relaxed = (low >= 225) & ((high.astype(np.int16) - low) <= 22)

    def relaxed_depth(mask: np.ndarray, brightness: np.ndarray) -> int:
        limit = max(1, int(len(mask) * .20))
        result = 0
        for count, light in zip(mask[:limit], brightness[:limit]):
            if count < .98 or light < 232:
                break
            result += 1
        return 0 if result == limit else result

    rr, cc = relaxed.mean(axis=1), relaxed.mean(axis=0)
    refined = (
        relaxed_depth(cc, col_light), relaxed_depth(rr, row_light),
        relaxed_depth(cc[::-1], col_light[::-1]), relaxed_depth(rr[::-1], row_light[::-1]),
    )
    if sum(d > 0 for d in depths) >= 2 or all(d > 0 for d in refined):
        left, top, right, bottom = refined
        return (left, top, w - right, h - bottom)
    # One-sided white edges can be real sky/snow: leave them for review.
    return (0, 0, w, h)


def save_webp(image: Image.Image, path: Path, icc: bytes | None) -> None:
    exif = Image.Exif()
    exif[315] = 'Arjun Sarkar'  # Artist
    exif[33432] = EXIF_COPYRIGHT
    options = dict(format='WEBP', quality=90, method=6, exif=exif.tobytes(), xmp=XMP)
    if icc:
        options['icc_profile'] = icc
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    image.save(temporary, **options)
    with Image.open(temporary) as check:
        check.load()
        if check.getexif().get(33432) != EXIF_COPYRIGHT:
            raise RuntimeError(f'Copyright verification failed: {path}')
    temporary.replace(path)


def process(job: tuple[Path, int, dict | None], root: Path) -> dict:
    source, number, previous = job
    relative = source.relative_to(root).as_posix()
    source_hash = digest(source)
    backup = root / '.photo-originals' / source_hash / source.name
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not backup.exists():
        shutil.copy2(source, backup)
    if digest(backup) != source_hash:
        raise RuntimeError(f'Original backup verification failed: {relative}')
    destination = source.with_name(f'{number}.webp')
    stage = root / '.photo-originals' / '.staging' / str(number)
    staged_main = stage / 'main.webp'
    staged_files = []
    with Image.open(source) as opened:
        if getattr(opened, 'n_frames', 1) > 1:
            raise ValueError(f'Animated image is unsupported: {relative}')
        icc = opened.info.get('icc_profile')
        has_alpha = 'A' in opened.getbands() or 'transparency' in opened.info
        photo = ImageOps.exif_transpose(opened).convert('RGBA' if has_alpha else 'RGB')
        original_size = photo.size
        # Transparent artwork has intentional padding, not a photographic frame.
        box = (0, 0, *photo.size) if has_alpha else border_box(photo)
        photo = photo.crop(box)
        cropped_size = photo.size
        photo.thumbnail((2560, 2560), Image.Resampling.LANCZOS)
        save_webp(photo, staged_main, icc)
        staged_files.append({'temporary': staged_main.relative_to(root).as_posix(), 'destination': destination.relative_to(root).as_posix(), 'sha256': digest(staged_main)})
        variants = []
        for width in (480, 960):
            if photo.width <= width:
                continue
            thumb = photo.resize((width, round(photo.height * width / photo.width)), Image.Resampling.LANCZOS)
            target = root / 'assets' / 'photos' / str(width) / f'{number}.webp'
            staged_thumb = stage / f'{width}.webp'
            save_webp(thumb, staged_thumb, icc)
            staged_files.append({'temporary': staged_thumb.relative_to(root).as_posix(), 'destination': target.relative_to(root).as_posix(), 'sha256': digest(staged_thumb)})
            variants.append({'src': target.relative_to(root).as_posix(), 'width': thumb.width})
        width, height = photo.size
    entry = {
        'id': number, 'original': previous['original'] if previous else relative,
        'src': destination.relative_to(root).as_posix(),
        'sha256': digest(staged_main), 'version': VERSION,
        'width': width, 'height': height, 'variants': variants,
        'originalSize': original_size, 'crop': box, 'croppedSize': cropped_size,
        'backup': backup.relative_to(root).as_posix(),
    }
    # Keep the source until the registry has been saved by the caller.
    entry['_remove'] = relative if source != destination else None
    entry['_files'] = staged_files
    return entry


def finish_entry(root: Path, entry: dict) -> None:
    """Recoverable commit: journal first, then publish files, then remove input."""
    pending = entry.get('_remove')
    source = root / pending if pending else None
    if source and source.exists() and digest(source) != digest(root / entry['backup']):
        raise RuntimeError(f'Input changed during processing; inspect before retry: {pending}')
    for item in entry.get('_files', []):
        temporary, destination = root / item['temporary'], root / item['destination']
        if temporary.exists():
            if digest(temporary) != item['sha256']:
                raise RuntimeError(f'Staged image checksum mismatch: {temporary}')
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary.replace(destination)
        if not destination.exists() or digest(destination) != item['sha256']:
            raise RuntimeError(f'Published image checksum mismatch: {destination}')
    if source:
        source.unlink(missing_ok=True)
    entry.pop('_remove', None)
    entry.pop('_files', None)


def catalogue(root: Path, registry: dict) -> dict:
    config_path = root / 'data' / 'site.json'
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    overrides_path = root / 'data' / 'photo-details.json'
    overrides = json.loads(overrides_path.read_text()) if overrides_path.exists() else {}
    entries = [e for e in registry.values() if (root / e['src']).exists()]
    entries.sort(key=lambda e: (e['original'].casefold(), e['id']))
    photos = []
    for entry in entries:
        parts = Path(entry['src']).parts
        country = parts[2].title() if parts[:2] == ('poy', 'countries') else ''
        detail = overrides.get(str(entry['id']), {})
        photos.append({
            'id': entry['id'], 'src': quote(entry['src']), 'width': entry['width'], 'height': entry['height'],
            'revision': entry['sha256'][:12],
            'variants': [{**v, 'src': quote(v['src'])} for v in entry['variants']],
            'country': country, 'selected': parts[0] == 'poy' and not country,
            'title': detail.get('title', ''),
            'alt': detail.get('alt') or (f'{country} — photograph by Arjun Sarkar' if country else 'Travel photograph by Arjun Sarkar'),
        })
    country_root = root / 'poy' / 'countries'
    countries = sorted(p.name.title() for p in country_root.iterdir() if p.is_dir() and not p.is_symlink()) if country_root.exists() else []
    def resolve(value: str | int | None) -> int | None:
        return next((e['id'] for e in entries if value in (e['id'], e['original'], e['src'])), None)
    featured = [resolve(value) for value in config.get('featured', [])]
    ranks = {number: rank for rank, number in enumerate(featured) if number is not None}
    photos.sort(key=lambda p: ranks.get(p['id'], len(ranks)))
    return {'copyright': COPYRIGHT, 'photos': photos, 'countries': countries,
            'hero': resolve(config.get('hero')), 'portrait': resolve(config.get('portrait')), 'logo': resolve(config.get('logo')), 'favicon': resolve(config.get('favicon')),
            'covers': {country: resolve(value) for country, value in config.get('covers', {}).items()}}


@contextmanager
def processing_lock(root: Path):
    path = root / '.photo-processing.lock'
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, str(os.getpid()).encode())
        yield
    finally:
        os.close(descriptor)
        path.unlink(missing_ok=True)


def run(root: Path, workers: int, dry_run: bool) -> None:
    registry_path = root / 'data' / 'image-registry.json'
    registry = json.loads(registry_path.read_text()) if registry_path.exists() else {}
    # Finish journaled publication/removal from a previously interrupted import.
    pending_sources = {e.get('_remove') for e in registry.values()} - {None}
    if not dry_run:
        for entry in registry.values():
            finish_entry(root, entry)
    files = sorted(p for directory in ('images', 'poy') for p in (root / directory).rglob('*')
                   if p.is_file() and not p.is_symlink() and p.suffix.lower() in EXTENSIONS
                   and (not dry_run or p.relative_to(root).as_posix() not in pending_sources))
    by_path = {e['src']: e for e in registry.values()}
    used = {int(key) for key in registry}
    used.update(int(p.stem) for p in files if p.stem.isdigit())
    jobs = []
    unchanged = 0
    for path in files:
        previous = by_path.get(path.relative_to(root).as_posix())
        if previous and previous['version'] == VERSION and digest(path) == previous['sha256'] and all((root / v['src']).exists() for v in previous['variants']):
            unchanged += 1
            continue
        number = previous['id'] if previous else secrets.randbelow(999001) + 1000
        while not previous and number in used:
            number = secrets.randbelow(999001) + 1000
        used.add(number)
        jobs.append((path, number, previous))
    print(f'{len(files)} photos: {len(jobs)} to process; {unchanged} unchanged.', flush=True)
    if dry_run:
        for path, _, _ in jobs:
            with Image.open(path) as im:
                im = ImageOps.exif_transpose(im)
                box = border_box(im)
                print(json.dumps({'file': str(path.relative_to(root)), 'size': im.size, 'crop': box}))
        return
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = executor.map(lambda job: process(job, root), jobs)
        for index, entry in enumerate(results, 1):
            registry[str(entry['id'])] = entry
            atomic_json(registry_path, registry)
            finish_entry(root, entry)
            if index % 20 == 0 or index == len(jobs):
                print(f'Processed {index}/{len(jobs)}', flush=True)
    atomic_json(registry_path, registry)
    atomic_json(root / 'data' / 'photos.json', catalogue(root, registry))
    print('Catalogue updated. Originals preserved in .photo-originals/.', flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true', help='Inspect crops without modifying photos.')
    parser.add_argument('--workers', type=int, choices=range(1, 9), default=4)
    args = parser.parse_args()
    try:
        with processing_lock(ROOT):
            run(ROOT, args.workers, args.dry_run)
    except (OSError, ValueError, RuntimeError) as error:
        print(f'Image processing stopped: {error}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
