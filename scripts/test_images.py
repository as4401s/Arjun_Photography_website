"""Regression checks for crop detection, metadata, and repeatable imports."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image, ImageOps

from process_images import EXIF_COPYRIGHT, border_box, run


class ImageWorkflowTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(42)
        self.photo = Image.fromarray(rng.integers(15, 225, (180, 240, 3), dtype=np.uint8))

    def test_no_border_keeps_composition(self):
        self.assertEqual(border_box(self.photo), (0, 0, 240, 180))

    def test_exact_asymmetric_frame(self):
        framed = ImageOps.expand(self.photo, border=(13, 7, 18, 22), fill='white')
        self.assertEqual(border_box(framed), (13, 7, 253, 187))

    def test_jpeg_frame(self):
        framed = ImageOps.expand(self.photo, border=12, fill='white')
        encoded = io.BytesIO()
        framed.save(encoded, format='JPEG', quality=90)
        encoded.seek(0)
        crop = border_box(Image.open(encoded))
        self.assertTrue(all(abs(a-b) <= 1 for a, b in zip(crop, (12, 12, 252, 192))), crop)

    def test_bright_sky_is_not_a_frame(self):
        sky = self.photo.copy()
        sky.paste('white', (0, 0, 240, 25))
        self.assertEqual(border_box(sky), (0, 0, 240, 180))
        self.assertEqual(border_box(Image.new('RGB', (240, 180), 'white')), (0, 0, 240, 180))

    def test_import_metadata_backup_empty_country_and_idempotence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'images').mkdir()
            (root / 'poy/countries/empty').mkdir(parents=True)
            source = root / 'poy/countries/empty/old-name.jpg'
            ImageOps.expand(self.photo, border=12, fill='white').save(source, quality=95)
            with contextlib.redirect_stdout(io.StringIO()):
                run(root, 1, False)
            registry = json.loads((root / 'data/image-registry.json').read_text())
            entry = next(iter(registry.values()))
            output = root / entry['src']
            self.assertFalse(source.exists())
            self.assertTrue((root / entry['backup']).exists())
            self.assertTrue(1000 <= int(output.stem) <= 1000000)
            with Image.open(output) as photo:
                self.assertEqual(photo.getexif()[33432], EXIF_COPYRIGHT)
                self.assertIn(b'Arjun Sarkar', photo.info['xmp'])
                self.assertNotIn(34853, photo.getexif())  # GPS is not copied.
            original = output.read_bytes()
            state = (root / 'data/image-registry.json').read_bytes()
            with contextlib.redirect_stdout(io.StringIO()):
                run(root, 1, False)
            self.assertEqual(output.read_bytes(), original)
            self.assertEqual((root / 'data/image-registry.json').read_bytes(), state)
            output.unlink()
            with contextlib.redirect_stdout(io.StringIO()):
                run(root, 1, False)
            catalogue = json.loads((root / 'data/photos.json').read_text())
            self.assertEqual(catalogue['countries'], ['Empty'])
            self.assertEqual(catalogue['photos'], [])


if __name__ == '__main__':
    unittest.main()
