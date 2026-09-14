# Image workflow

## Adding photographs

Put original photos in `poy/` for selected work, `poy/countries/<country>/` for country collections, or `images/` for site-only photos such as the portrait. Country folder names become display names. Empty folders remain available and show a “coming soon” state. Add a `.gitkeep` file if an empty folder should survive Git checkout.

Then run:

```sh
python3 scripts/process_images.py
python3 scripts/build.py
```

No HTML editing is needed when adding photographs. The old `python3 diff_images.py` command now invokes the same processor instead of printing snippets to paste into HTML.

Supported input: `.jpg`, `.jpeg`, `.png`, `.webp`, `.tif`, and `.tiff`, case-insensitively. Export HEIC/RAW files as JPEG or TIFF first. Animated images are rejected. The workflow is for photographs; transparent graphics should live outside the scanned photo directories.

## What happens, in order

1. Compare each photograph against the registry's SHA-256 fingerprint. Skip unchanged files whose derivatives exist.
2. Copy the original to `.photo-originals/<sha256>/<original filename>` and verify the backup byte-for-byte.
3. Correct EXIF orientation and inspect the image at its original resolution.
4. Detect connected white or near-white rectangular edge strips. Allow small compression artifacts and gray shading in an already detected frame. Require multiple matching sides; do not automatically trim isolated bright skies or snow. Stop at the photo content. Never crop more than 20% from one edge.
5. Crop only a detected frame. Preserve the remaining aspect ratio; resize only when the longest edge exceeds 2560 pixels.
6. Assign a globally collision-checked random integer filename between 1000 and 1000000, inclusive. Existing processed filenames remain stable.
7. Save WebP at quality 90 with responsive 480px and 960px width variants when the source is large enough. All image files use numeric names; sizes are separate directories.
8. Write EXIF Artist and Copyright, plus XMP creator, rights, and `Marked=true`, to every generated WebP, including thumbnails. Retain embedded ICC color profiles. Do not copy source GPS, serial numbers, or other camera EXIF.
9. Verify the output, update the registry, remove the input from the public photo folder, and regenerate the catalogue from files that actually exist.

The originals are **local backups, not stored in Git**. Back up `.photo-originals/` to your normal external backup storage. Do not publish this directory. A numeric filename is organization, not access control. Copyright metadata records attribution; it does not prevent downloading or guarantee that other software will preserve it.

## Preview and review crops

Before importing new photos:

```sh
python3 scripts/process_images.py --dry-run
```

This reports `[left, top, right, bottom]` crop coordinates (right/bottom are exclusive) and makes no changes to photographs. `[0, 0, original width, original height]` means no crop. The temporary processing lock is released afterward.

After processing:

```sh
python3 scripts/crop_report.py
```

Open `output/crop-review.html` locally to compare original and processed images. The report is not published. Crop coordinates, original dimensions, and backup locations are recorded in `data/image-registry.json`.

Automatic detection cannot distinguish every white scene from an added frame. Inspect unusual borders or white backgrounds in the report. One-sided, patterned, signed, and very large borders are intentionally conservative cases. Never repeatedly crop a processed file to “try harder.” Restore the original for manual correction instead.

## Captions, covers, and composition

The viewer and main gallery show the complete processed image. The full-screen hero and destination previews use `object-fit: cover` for their layouts; the underlying photograph remains unchanged.

Add real descriptions to `data/photo-details.json`, keyed by the stable numeric ID:

```json
{
  "123456": {
    "title": "An evening by the lake",
    "alt": "A wooden boathouse beside a turquoise lake beneath steep mountains"
  }
}
```

Use an ID that exists in `data/image-registry.json`, then rerun processing and build. The default alt text identifies the country and photographer without inventing subject details. Hero, portrait, selected order, and covers are configured in `data/site.json` using an ID, current relative path, or the original path recorded in the registry.

## Recovery and removal

- To remove a photo from the website, delete its processed file from `poy/` or `images/`, then process and build again. Its original backup stays safe. Unreferenced thumbnails are excluded from the build.
- To replace a photo while retaining its ID, place the corrected image at the same numeric `.webp` path (actually export it as WebP), then process and build. The previous backup stays intact.
- To undo a crop, locate the entry's `backup` path in `data/image-registry.json`. Copy that original back into the appropriate input folder, correct the crop manually if needed, and remove the unwanted processed version before rerunning. A reimport receives a new ID; update any cover/hero configuration referring to the old ID.
- Keep `data/image-registry.json` alongside processed photos. Deleting it causes the processor to treat those files as new imports, renaming and re-encoding them.
- The lock prevents simultaneous imports. If a process is killed forcibly, confirm it is no longer running before removing `.photo-processing.lock` and retrying.
- A failed import may have completed earlier photos. Their originals remain backed up; a rerun skips completed work. Read the error before retrying. Do not remove backups to resolve errors.

The favicon master is WebP too. The builder also generates small PNG browser and Apple touch icons for device compatibility; these are the only format exceptions in the published site, carry the same attribution, and are not photographs.

Transparent PNG and WebP artwork keeps its alpha channel in the processed master and every responsive variant. Border cropping is skipped for these assets so intentional transparent padding remains intact. Use a genuinely transparent export for logos: changing a file extension to SVG or matching a background color cannot remove a baked-in glow.

For a frame that needs visual review, `python3 scripts/crop_photo.py PHOTO_ID LEFT TOP RIGHT BOTTOM` crops directly from the preserved original, keeps its numeric ID, refreshes responsive variants and metadata, and records the crop in the registry. Coordinates are in original-image pixels, with the right and bottom edges excluded. The Germany image `525804` was reviewed and cropped to `(26, 26, 1900, 1900)` to remove its light grey frame. Rebuild after a reviewed crop.
