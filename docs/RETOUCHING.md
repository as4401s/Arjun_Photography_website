# Removing visible photographer signatures

Visible signatures are separate from the embedded copyright metadata. Remove an Arjun signature only after visually confirming it; keep the photograph's copyright metadata intact. Do not remove real signs, text on buildings, or other details in the scene.

Process borders and orientation first. Inspect the photograph, prepare a small patch around the signature, and use the built-in imagegen editor to reconstruct only the obscured background. Blend the reviewed patch into the processed master with a soft mask confined to that area. Regenerate both responsive sizes and update the registry checksum so browsers receive the correction.

Keep the original camera export, the previous processed master, the generated patch, and a lossless edited master in `.photo-originals/`. Retouch records in `data/image-registry.json` identify those files and the edited region. These backups and records are excluded from the published site.

For a later edit to a retouched photo, use its recorded `editedMaster` as the starting image. Do not reapply `crop_photo.py` to a retouched entry: it uses the original export and would restore the removed signature. Review and preserve earlier retouches when replacing an image.

## September 14, 2026 review

The new batch contained 63 photographs. A text-recognition scan of all 1,053 gallery photographs, followed by visual inspection of the new batch and matching results, identified five visible Arjun signatures. Text recognition is a review aid and may miss stylized lettering; future imports still need visual inspection.

All five signatures were in sky areas in the Belgium collection:

| Photo ID | Published master |
| --- | --- |
| 66204 | `poy/countries/belgium/66204.webp` |
| 58614 | `poy/countries/belgium/58614.webp` |
| 555467 | `poy/countries/belgium/555467.webp` |
| 790177 | `poy/countries/belgium/790177.webp` |
| 671349 | `poy/countries/belgium/671349.webp` |

Each received a separate built-in imagegen edit using this prompt:

> Use case: precise-object-edit. Edit this 512 by 384 pixel crop from the user's own travel photograph. Remove ONLY the black Arjun signature, its copyright symbol, winged camera emblem, and camera outline in the sky. Inpaint their pixels with the immediately surrounding sky/cloud texture. Keep the exact same 4:3 composition, colors, grain, clouds, trees, building edges, and all other image details. No crop, no zoom, no added detail, no color grading. Return one clean photographic patch in the same framing and aspect ratio; no text or watermark. Preserve the existing sky gradient and cloud boundaries so this patch fits seamlessly back into the original photograph.

Only a feathered area around each signature was composited from the generated patch. The rest of the photograph used the existing master. WebP encoding was then applied with the usual metadata and responsive-image settings.

## Named Belgium cover

The subsequent cover update added photo `70558` at `poy/countries/belgium/cover.webp`. Its top-left Arjun mark was also removed with a separate built-in imagegen sky patch. Harmonic boundary color matching blended this patch into the original blue sky without a visible rectangular edge. The reserved cover filename and internal ID were preserved, and the same original/patch/edited-master backups were recorded in the registry.

Prompt:

> Use case: precise-object-edit. This is a 512 by 384 pixel sky crop from the user's own travel photo. Remove only the black Arjun signature, copyright symbol, winged camera emblem and outlined camera. Inpaint those pixels with the surrounding blue sky gradient and subtle photographic texture. Preserve all surrounding clouds, original sky colors, exposure, grain, and exact 4:3 framing. No crop, zoom, text, watermark, color grading, or extra objects. The patch must fit seamlessly back into the existing photograph.
