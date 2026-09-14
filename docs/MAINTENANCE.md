# Maintaining and hosting the portfolio

## Day-to-day changes

- **New country:** create `poy/countries/<country>/`, add images, process, build. An empty directory with `.gitkeep` appears as coming soon.
- **Ordering and site photos:** edit `data/site.json`. Existing original paths remain resolvable after random renaming. Prefer numeric IDs for new configuration.
- **Captions:** edit `data/photo-details.json`, then process and build.
- **Text or layout:** edit `index.html` or `assets/site.css`, then build.
- **Behaviour:** edit `assets/site.js`, check its syntax and browser interactions, then build.

The public catalogue excludes missing photos automatically and contains only current image URLs. `images/` photos are available for the hero/portrait but are not duplicated into the selected-work gallery. Every image directly under `poy/` belongs to selected work; feature ordering is optional.

Country galleries sort by each photo's randomly assigned numeric ID, so the photographs are shuffled rather than following their original camera filenames. The order stays consistent across visits, mobile Load more batches, and the full-screen viewer. New imports receive random IDs and join at random positions. Homepage highlight ordering and destination cover selections remain separately controlled.

## Hosting

**Publish only when Arjun explicitly requests it.** Keep routine edits and image imports local. Do not push or deploy automatically: pushes trigger Netlify and GitHub Pages builds and consume hosting limits.

Upload the **contents of `dist/`** to a static host. Do not deploy the repository root, `.photo-originals/`, `output/`, or internal registry. The builder copies only explicitly referenced photographs and a small allowlist of application files. All URLs are relative, so deployment in a subdirectory is supported.

The `_headers` file configures CSP, anti-framing, MIME sniffing protection, privacy permissions, and cache policy on hosts that support this format. On other hosts, configure equivalent HTTP response headers in the hosting settings. GitHub Pages does not apply `_headers`; the HTML CSP still applies, but HTTP-only protections such as `frame-ancestors` require host support.

The site has no forms, credentials, analytics, external fonts, third-party scripts, or API keys. Instagram and email are ordinary outbound links. The native photo dialog supports keyboard navigation, Escape, focus restoration, and mobile swipes. Reduced motion preferences are respected.

HTML and the catalogue should revalidate on each request. Image caching is bounded to one day, allowing corrected photos at stable filenames to update. CSS and JavaScript URLs include content hashes as query parameters. Serve over HTTPS in production.

Gallery image requests include a revision from the processed master checksum. Reviewed crops therefore refresh in returning visitors' browsers immediately, while keeping the numeric photo ID. Mobile collections initially show 40 photos; the Load more button adds up to 40 at a time. Desktop shows the full collection. All thumbnails remain lazy-loaded.

## Verification

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
node --check assets/site.js
python3 scripts/build.py
python3 scripts/verify.py
```

The image regression checks cover unbordered photos, asymmetric white frames, JPEG compression, bright skies, attribution metadata, backups, empty collections, and repeat imports. The verifier checks the actual catalogue, filenames, dimensions, file formats, metadata on every full-size image and thumbnail, and private-file exclusion from `dist/`.

After visual changes, check desktop and mobile widths, selected work, destinations, an empty country, viewer arrows/Escape, focus restoration, and browser back/forward navigation. Check the browser console and network panel for broken requests. Serve `dist/` through HTTP rather than opening the template as a `file://` URL; catalogue fetching requires a server.

## Known editorial tasks

- Add unique captions and descriptive alt text for individual photographs as time allows.
- Populate the empty country collections when the photographs are ready.
- Set absolute Open Graph image/canonical URLs when the final public domain is known.
- Keep an independent backup of the original photo library.

## Netlify publication

The root `netlify.toml` runs the builder and verifier, then publishes only `dist/`. Netlify installs `requirements.txt` with Python 3.14 before building. A push to the linked production branch publishes the generated pages, logo, responsive images, and browser/Apple icons together. Do not set the publish directory to the repository root: `index.html` is a source template, and `destinations.html` and PNG icons only exist after building.

`SITE_URL` in `netlify.toml` sets canonical and social preview URLs for Netlify. Update it if the public domain changes. Other hosts use the URL in `data/site.json` unless they also set `SITE_URL`. For a manual Netlify upload, build locally and upload `dist/`.

## GitHub publication

The repository includes `.github/workflows/deploy.yml`. After GitHub Pages is set to **GitHub Actions** in repository Settings → Pages, every push to `main` verifies and publishes the generated `dist/` directory. The workflow uses immutable action revisions and limits publication permissions to the deploy job. Process new images locally and commit the processed files, derivatives, and both generated JSON files before pushing. Original backups are never uploaded.

Homepage highlights live at `/`; destinations live at `destinations.html`, with shareable country URLs such as `destinations.html#country=Switzerland`. Both pages are generated from the shared HTML template.

For a year or attribution change, update the constants in `scripts/process_images.py` and run `python3 scripts/update_copyright.py`; this updates existing WebP metadata without recompressing photo pixels. Then rebuild.
