#!/usr/bin/env python3
"""Apply a visually reviewed crop using original pixels and preserve the photo ID."""
import argparse
import json

from PIL import Image, ImageOps
from process_images import ROOT, atomic_json, catalogue, digest, finish_entry, processing_lock, save_webp


def crop_photo(number, box):
    registry_path = ROOT / 'data/image-registry.json'
    registry = json.loads(registry_path.read_text())
    entry = dict(registry[str(number)])
    if entry.get('_files'):
        raise ValueError('Finish the interrupted import before applying a reviewed crop.')
    with Image.open(ROOT / entry['backup']) as original:
        photo = ImageOps.exif_transpose(original)
        left, top, right, bottom = box
        if not (0 <= left < right <= photo.width and 0 <= top < bottom <= photo.height):
            raise ValueError('Crop must fit within the original image.')
        original_size = photo.size
        photo = photo.convert('RGBA' if 'A' in photo.getbands() else 'RGB').crop(box)
        cropped_size = photo.size
        photo.thumbnail((2560, 2560), Image.Resampling.LANCZOS)
        stage = ROOT / '.photo-originals/.staging' / str(number)
        files, variants = [], []
        for width in (None, 480, 960):
            if width and photo.width <= width:
                continue
            image = photo if width is None else photo.resize((width, round(photo.height * width / photo.width)), Image.Resampling.LANCZOS)
            destination = entry['src'] if width is None else f'assets/photos/{width}/{number}.webp'
            temporary = stage / f'{width or "main"}.webp'
            save_webp(image, temporary, original.info.get('icc_profile'))
            files.append({'temporary': temporary.relative_to(ROOT).as_posix(), 'destination': destination, 'sha256': digest(temporary)})
            if width:
                variants.append({'src': destination, 'width': width})
        entry.update(width=photo.width, height=photo.height, originalSize=original_size,
                     crop=box, croppedSize=cropped_size, variants=variants,
                     sha256=files[0]['sha256'], _files=files)
    registry[str(number)] = entry
    atomic_json(registry_path, registry)
    finish_entry(ROOT, entry)
    atomic_json(registry_path, registry)
    atomic_json(ROOT / 'data/photos.json', catalogue(ROOT, registry))
    print(f'Applied reviewed crop to {number}; original backup and ID preserved.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('photo_id', type=int)
    parser.add_argument('box', type=int, nargs=4, metavar=('LEFT', 'TOP', 'RIGHT', 'BOTTOM'))
    args = parser.parse_args()
    with processing_lock(ROOT):
        crop_photo(args.photo_id, args.box)
