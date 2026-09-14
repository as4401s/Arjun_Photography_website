"""Regression checks for crop detection, metadata, and repeatable imports."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from process_images import EXIF_COPYRIGHT, border_box, run
from crop_photo import crop_photo


class ImageWorkflowTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(42)
        self.photo = Image.fromarray(rng.integers(15, 225, (180, 240, 3), dtype=np.uint8))

    def test_disguised_unsupported_format_is_rejected_without_removing_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'images').mkdir()
            source = root / 'images/disguised.jpg'
            self.photo.save(source, format='BMP')
            before = source.read_bytes()
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(UnidentifiedImageError):
                run(root, 1, False)
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse((root / 'data/photos.json').exists())

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

    def test_tinted_and_shaded_frames_are_removed(self):
        for colour in ((246, 241, 220), (250, 232, 225), (220, 232, 240), (205, 205, 205)):
            with self.subTest(colour=colour):
                framed = ImageOps.expand(self.photo, border=(13, 7, 18, 22), fill=colour)
                self.assertEqual(border_box(framed), (13, 7, 253, 187))
        framed = np.asarray(ImageOps.expand(self.photo, border=12, fill=(239, 235, 232))).copy()
        # A graded frame like the Taiwan photograph: darker along the bottom.
        shade = np.linspace(0, 22, framed.shape[0]).astype(np.uint8)[:, None, None]
        framed = Image.fromarray(np.maximum(framed.astype(np.int16) - shade, 0).astype(np.uint8))
        stream = io.BytesIO()
        framed.save(stream, format='JPEG', quality=90)
        stream.seek(0)
        crop = border_box(Image.open(stream))
        self.assertTrue(all(abs(a-b) <= 1 for a, b in zip(crop, (12, 12, 252, 192))), crop)

    def test_tinted_sky_and_blank_artwork_keep_composition(self):
        for colour in ((246, 241, 220), (215, 225, 240)):
            sky = self.photo.copy()
            sky.paste(colour, (0, 0, 240, 25))
            self.assertEqual(border_box(sky), (0, 0, 240, 180))
            self.assertEqual(border_box(Image.new('RGB', (240, 180), colour)), (0, 0, 240, 180))

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

    def test_transparency_survives_master_and_responsive_images(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'images').mkdir()
            artwork = Image.new('RGBA', (1200, 800), (255, 255, 255, 0))
            artwork.paste((220, 175, 80, 255), (200, 200, 1000, 600))
            artwork.save(root / 'images/logo.png')
            with contextlib.redirect_stdout(io.StringIO()):
                run(root, 1, False)
            entry = next(iter(json.loads((root / 'data/image-registry.json').read_text()).values()))
            self.assertEqual(entry['crop'], [0, 0, 1200, 800])
            for src in [entry['src'], *(v['src'] for v in entry['variants'])]:
                with Image.open(root / src) as image:
                    self.assertEqual(image.mode, 'RGBA')
                    self.assertEqual(image.getpixel((0, 0))[3], 0)
                    self.assertEqual(image.getpixel((image.width // 2, image.height // 2))[3], 255)

    def test_reviewed_crop_uses_original_and_retains_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'images').mkdir()
            self.photo.save(root / 'images/source.png')
            with contextlib.redirect_stdout(io.StringIO()), patch('crop_photo.ROOT', root):
                run(root, 1, False)
                registry_path = root / 'data/image-registry.json'
                number, original = next(iter(json.loads(registry_path.read_text()).items()))
                backup = (root / original['backup']).read_bytes()
                crop_photo(int(number), [20, 20, 200, 160])
                crop_photo(int(number), [0, 0, 230, 170])
                updated = json.loads(registry_path.read_text())[number]
                self.assertEqual(updated['src'], original['src'])
                self.assertEqual(updated['originalSize'], [240, 180])
                self.assertEqual((updated['width'], updated['height']), (230, 170))
                self.assertEqual((root / updated['backup']).read_bytes(), backup)
                with self.assertRaises(ValueError):
                    crop_photo(int(number), [0, 0, 999, 999])

    def test_named_cover_import_and_replacement(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory)
            country = root / 'poy/countries/belgium'
            country.mkdir(parents=True)
            self.photo.save(country / 'cover.jpg')
            self.photo.save(country / 'ordinary.jpg')
            run(root, 1, False)
            registry_path = root / 'data/image-registry.json'
            registry = json.loads(registry_path.read_text())
            cover = next(e for e in registry.values() if Path(e['src']).stem == 'cover')
            ordinary = next(e for e in registry.values() if e['id'] != cover['id'])
            self.assertTrue(Path(ordinary['src']).stem.isdigit())
            self.assertFalse((country / 'cover.jpg').exists())
            self.assertEqual(json.loads((root / 'data/photos.json').read_text())['covers']['Belgium'], cover['id'])
            first_backup = (root / cover['backup']).read_bytes()
            first_state = registry_path.read_bytes()
            run(root, 1, False)
            self.assertEqual(registry_path.read_bytes(), first_state)
            Image.new('RGB', (300, 200), '#3270ab').save(country / 'cover.jpg')
            run(root, 1, False)
            updated = json.loads(registry_path.read_text())[str(cover['id'])]
            self.assertEqual(updated['src'], cover['src'])
            self.assertNotEqual(updated['sha256'], cover['sha256'])
            self.assertEqual((root / cover['backup']).read_bytes(), first_backup)
            self.assertEqual(len(json.loads((root / 'data/photos.json').read_text())['photos']), 2)

    def test_renamed_cover_preserves_pixels_identity_and_retouch_records(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory)
            country = root / 'poy/countries/france'
            country.mkdir(parents=True)
            self.photo.save(country / 'original.jpg')
            run(root, 1, False)
            registry_path = root / 'data/image-registry.json'
            registry = json.loads(registry_path.read_text())
            key, original = next(iter(registry.items()))
            original['retouches'] = [{'kind': 'reviewed signature removal'}]
            registry_path.write_text(json.dumps(registry))
            (root / 'data/site.json').write_text(json.dumps({'covers': {'France': 'missing.jpg'}}))
            renamed = country / 'cover.webp'
            (root / original['src']).rename(renamed)
            pixels = renamed.read_bytes()
            run(root, 1, True)
            self.assertEqual(json.loads(registry_path.read_text())[key]['src'], original['src'])
            run(root, 1, False)
            updated = json.loads(registry_path.read_text())[key]
            self.assertEqual(renamed.read_bytes(), pixels)
            self.assertEqual(updated['id'], original['id'])
            self.assertEqual(updated['backup'], original['backup'])
            self.assertEqual(updated['retouches'], original['retouches'])
            self.assertEqual(json.loads((root / 'data/photos.json').read_text())['covers']['France'], original['id'])

    def test_competing_cover_inputs_are_rejected_without_modification(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory)
            country = root / 'poy/countries/france'
            country.mkdir(parents=True)
            self.photo.save(country / 'cover.jpg')
            self.photo.save(country / 'cover.png')
            before = {p.name: p.read_bytes() for p in country.iterdir()}
            with self.assertRaisesRegex(ValueError, 'one cover image'):
                run(root, 2, False)
            self.assertEqual({p.name: p.read_bytes() for p in country.iterdir()}, before)
            self.assertFalse((root / 'data/image-registry.json').exists())


if __name__ == '__main__':
    unittest.main()
