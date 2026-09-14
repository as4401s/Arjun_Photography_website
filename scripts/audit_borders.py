#!/usr/bin/env python3
"""Check every published master for remaining light frames without changing it."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from urllib.parse import unquote

from PIL import Image

from process_images import ROOT, atomic_json, border_box


def inspect(photo):
    with Image.open(ROOT / unquote(photo['src'])) as image:
        if 'A' in image.getbands():
            return None
        box = border_box(image)
        if box != (0, 0, *image.size):
            return {'id': photo['id'], 'country': photo['country'],
                    'src': photo['src'], 'size': image.size, 'suggestedCrop': box}
    return None


def audit():
    photos = json.loads((ROOT / 'data/photos.json').read_text())['photos']
    with ThreadPoolExecutor(max_workers=3) as pool:
        candidates = [result for result in pool.map(inspect, photos) if result]
    report = ROOT / 'output/border-audit/report.json'
    atomic_json(report, {'checked': len(photos), 'candidates': candidates})
    print(f'Checked {len(photos)} masters: {len(candidates)} possible remaining frames. Report: {report}')
    for candidate in candidates:
        print(f'{candidate["country"] or "Site/highlights"}: {candidate["id"]} {candidate["suggestedCrop"]}')
    return candidates


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Exit nonzero if a possible frame needs review.')
    args = parser.parse_args()
    candidates = audit()
    raise SystemExit(1 if args.check and candidates else 0)
