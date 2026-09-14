# Security review — 14 September 2026

The static website has no public backend, login, payment flow, file-upload endpoint, or third-party JavaScript. The review found a vulnerable image-processing dependency and several opportunities to harden build/browser boundaries. The fixes below are included in this release. See `DOMAIN.md` for the production domain configuration.

## SEC-01 — High upstream severity: affected Pillow dependency (fixed)

- **Rule:** dependency maintenance / image-decoder attack surface.
- **Location:** `requirements.txt:1`; image decoding in `scripts/process_images.py:144`.
- **Evidence:** the previous pin was `Pillow==12.2.0`. OSV returned advisories for that version, including [GHSA-6r8x-57c9-28j4](https://github.com/python-pillow/Pillow/security/advisories/GHSA-6r8x-57c9-28j4), a high-severity heap write issue in image coordinate operations. The maintainer lists 12.3.0 as the patched release. Other advisories cover format-specific decoder/encoder and font paths.
- **Impact and scope:** affected operations could crash or corrupt the local processing/build process under their documented conditions. The site does not accept visitor uploads; no remotely exploitable path from a website visitor to these Python operations was demonstrated. Several reported APIs/formats are not used by this project, and crop coordinates here are computed from the image rather than supplied by visitors.
- **Fix:** pinned Pillow 12.3.0, installed the requirements in the project `.venv`, and ran the image workflow/build regression checks with that environment. NumPy remains pinned to 2.5.0. A fresh OSV query for both updated pins returned no known advisories at review time.
- **Mitigation:** the importer now explicitly opens only JPEG, PNG, TIFF, and WebP data. A disguised unsupported format is rejected while its original source remains intact. Continue using the project environment for future imports.

## SEC-02 — Low: inconsistent build boundary checks (hardened)

- **Location:** `scripts/build.py:99`; `scripts/seo.py:19`.
- **Evidence:** image paths were already checked before publication, but fixed public assets were copied without the same resolved-path boundary check. The configured canonical URL was escaped but accepted without validating its scheme and credentials.
- **Impact and scope:** someone able to modify the local checkout could accidentally or deliberately point a public asset outside it, or supply invalid public metadata URLs. This is not an anonymous visitor attack and does not grant capabilities beyond existing write access to the checkout.
- **Fix:** fixed public assets must resolve within the repository. The primary site URL must be absolute HTTPS without credentials, query strings, fragments, whitespace, or literal dot-segment paths. Existing image-path checks and the strict publication allowlist remain in place.

## SEC-03 — Informational: browser and generated-markup hardening

- **Location:** `_headers:2`, `index.html:11`, `scripts/seo.py:142`.
- **Evidence:** the existing CSP restricted scripts to this origin, denied framing, and disabled forms/plugins. This already provided a useful baseline. Adding SEO structured data would otherwise introduce a new inline-script exception.
- **Fix:** generated JSON-LD escapes HTML delimiters and receives an exact SHA-256 CSP authorization in both the page and HTTP policy. No `unsafe-inline` or `unsafe-eval` permission was added. The policy now explicitly disables inline event attributes, frames, and workers. Browser code continues to use text/DOM APIs rather than parsing URL content into HTML.
- **Verification:** malicious caption text is included in a regression fixture and cannot terminate the JSON-LD script or inject a script element. Invalid URL and duplicate-country-slug fixtures fail safely.

## Existing protections verified

- A read-only request to the live Netlify homepage confirmed CSP, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, the referrer policy, and camera/microphone/geolocation restrictions. These were the prior deployed headers; the new directives will take effect after publication.
- Source review found no `eval`, HTML-injection sinks, local/session credential storage, or cross-window messaging in the website code. A targeted tracked-file secret-pattern scan found no matching private keys or token patterns; this is not a guarantee that every possible secret format is absent.
- Outbound new-tab links retain `noopener noreferrer`. The frontend has no external scripts or fonts.
- The builder publishes only generated pages, approved public files, and referenced images. Verification checks every WebP's metadata and rejects private or unexpected files in `dist/`.
- GitHub Actions use pinned action revisions and scoped deployment permissions. Netlify headers do not apply to the GitHub Pages mirror; its HTML CSP provides only the subset of protections supported through a meta tag.

## Account and operational scope

Account MFA, registrar locks, and billing permissions were not audited or changed. The user purchased the domain and edited Cloudflare DNS. The authorized release connects it to Netlify and uses its managed HTTPS certificate. The domain guide recommends MFA, email verification, auto-renew, and DNSSEC during setup.

Use `.venv/bin/python` or activate `.venv` for local imports and builds. Install `requirements.txt` after future dependency changes, then run the documented checks. Dependency advisory databases change over time; the successful check applies to this review date.
