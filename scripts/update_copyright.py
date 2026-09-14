#!/usr/bin/env python3
"""Refresh attribution in WebP containers without recompressing image pixels."""
import json
from pathlib import Path
import struct

from PIL import Image
from process_images import ROOT, COPYRIGHT, EXIF_COPYRIGHT, XMP, atomic_json, digest, processing_lock


def update(path: Path) -> None:
    original = path.read_bytes()
    if original[:4] != b'RIFF' or original[8:12] != b'WEBP':
        raise ValueError(f'Not WebP: {path}')
    exif = Image.Exif()
    exif[315] = 'Arjun Sarkar'
    exif[33432] = EXIF_COPYRIGHT
    replacements = {b'EXIF': exif.tobytes(), b'XMP ': XMP}
    chunks = []
    offset = 12
    present = set()
    while offset < len(original):
        tag = original[offset:offset + 4]
        size = struct.unpack('<I', original[offset + 4:offset + 8])[0]
        payload = original[offset + 8:offset + 8 + size]
        if tag in replacements:
            payload = replacements[tag]
            present.add(tag)
        chunks.append(tag + struct.pack('<I', len(payload)) + payload + (b'\0' if len(payload) % 2 else b''))
        offset += 8 + size + size % 2
    if present != set(replacements):
        raise ValueError(f'Expected existing attribution chunks: {path}')
    body = b'WEBP' + b''.join(chunks)
    result = b'RIFF' + struct.pack('<I', len(body)) + body
    if result == original:
        return
    temporary = path.with_suffix('.metadata.tmp')
    temporary.write_bytes(result)
    with Image.open(temporary) as image:
        assert image.getexif()[33432] == EXIF_COPYRIGHT
    temporary.replace(path)


if __name__ == '__main__':
    with processing_lock(ROOT):
        registry_path = ROOT / 'data/image-registry.json'
        registry = json.loads(registry_path.read_text())
        count = 0
        for entry in registry.values():
            for relative in [entry['src'], *(v['src'] for v in entry['variants'])]:
                path = ROOT / relative
                if path.exists():
                    update(path)
                    count += 1
            if (ROOT / entry['src']).exists():
                entry['sha256'] = digest(ROOT / entry['src'])
        atomic_json(registry_path, registry)
        catalogue_path = ROOT / 'data/photos.json'
        catalogue = json.loads(catalogue_path.read_text())
        catalogue['copyright'] = COPYRIGHT
        atomic_json(catalogue_path, catalogue)
        print(f'Updated attribution on {count} WebP files without image recompression.')
