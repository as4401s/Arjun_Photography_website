# Our Travel Photobook — Arjun Photography

A static travel and landscape photography portfolio. Photos are the source of truth: the gallery and country collections are generated from the folders on disk.

## Set up

Use Python 3.11 or newer, then install the two image-processing dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Add photos and preview

1. Put selected photographs directly in `poy/`.
2. Put destination photographs in `poy/countries/<country name>/` (create a folder for any new country).
3. Run:

```sh
python3 scripts/process_images.py
python3 scripts/build.py
python3 -m http.server 8000 --bind 127.0.0.1 --directory dist
```

Open [the local preview](http://localhost:8000). The processor finds new JPEG, PNG, TIFF, and WebP files; removes detected white frames; assigns collision-checked random numeric names from `1000.webp` to `1000000.webp`; produces responsive WebP versions; embeds Arjun Sarkar's copyright; and regenerates the catalogue. Re-running it skips unchanged images.

To choose a country cover, name its photo `cover` inside that country's folder. It keeps the master filename `cover.webp` and becomes the destination cover automatically. Other photos still receive random numeric filenames. See the image workflow for replacing a cover or selecting an existing photo without recompression.

**Publish only `dist/`.** It contains the site and processed photographs. Originals and internal files are deliberately excluded. The working directory is not a deployable folder.

- [Image workflow, crop review, metadata, and recovery](docs/IMAGES.md)
- [Site configuration and maintenance](docs/MAINTENANCE.md)
- [Design and engineering decisions](docs/DESIGN.md)
- [Search visibility and AI discoverability](docs/SEO.md)
- [Buy and connect a Cloudflare domain](docs/DOMAIN.md)
- [Security review](docs/SECURITY.md)

## Checks

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
node --check assets/site.js
python3 scripts/verify.py
```

Node is optional for development; the website has no JavaScript package dependencies or runtime CDN. Run the verifier after processing and building.

## Files

| Path | Purpose |
| --- | --- |
| `index.html` | HTML template; the builder inserts imagery and crawlable galleries |
| `scripts/seo.py` | Country pages, metadata, structured data, sitemap, and robots.txt |
| `assets/site.css`, `assets/site.js` | Styles and gallery interactions |
| `data/site.json` | Hero, portrait, featured order, and destination covers |
| `data/photo-details.json` | Optional captions and descriptive alt text by photo ID |
| `data/photos.json` | Generated public catalogue; do not edit by hand |
| `data/image-registry.json` | Generated filename mapping, checksums, and crop history; keep it |
| `.photo-originals/` | Verified original backups; local and ignored by Git |
| `dist/` | Generated site, ready for hosting |

All photographs © 2026 Arjun Sarkar. All rights reserved.
