# Design direction

Visual thesis: a quiet travel journal, with expansive photography, a deep charcoal background, muted cream text, and generous editorial typography.

Content plan: an edge-to-edge ocean photograph introduces Our Travel Photobook; homepage highlights shows the photographs at their natural proportions; destinations organize the growing archive; a short personal introduction closes with contact links.

Interaction thesis: a restrained hero entrance, navigation that settles onto a solid surface as the visitor scrolls, and gentle photo hover transitions. Respect reduced motion. Use a native dialog for a focused, keyboard-accessible photo viewer.

## Engineering decisions

- Static HTML, CSS, and JavaScript. No client framework, runtime CDN, third-party fonts, trackers, or stock-photo fallbacks.
- Generate the catalogue from real files. Preserve empty country directories and show honest empty states.
- Desktop renders the full collection. Mobile begins with 40 photographs and adds batches of 40 through a Load more button. Thumbnails load lazily; the viewer preloads only adjacent full-size photos.
- Publish only `dist/`, built from an explicit allowlist. Keep originals, processing state, and tools out of the public site.
- Real photographs belong to Arjun Sarkar. Preserve composition except for detected added white borders; no generated imagery.

## Reference review

Reviewed the official sites of [Alex Strohl](https://www.alexstrohl.com/) and [Benjamin Hardman](https://benjaminhardman.com/). The useful principles were large image-led surfaces, simple navigation, and a clear separation between photography and supporting information. The design uses original layout, copy, and Arjun's own photographs; no reference-site assets are copied.

Final direction: Our Travel Photobook is the main brand; Arjun Photography appears in the header. The homepage contains highlights and compact channel/about sections. `destinations.html` is a separate catalogue page. The portrait is intentionally small.

The favicon was generated through Higgsfield (`gpt_image_2_5`, job `fc4ffee8-dcee-4907-8cbd-4d1106b76a10`), as a flat teal, cream, and gold mountain/camera emblem. The channel logo is a transparent cutout of the user's supplied Our Travel Photobook artwork, edited with the built-in image tool. The final WebP is `images/298472.webp`; its alpha channel is retained in both responsive variants. The edit requested removal of the rectangular background and outer glow while retaining the lettering, landmarks, and cream/gold/teal palette. Generated artwork is not mixed into the photography collections.

The user-supplied [Joe McNally portfolio](https://portfolio.joemcnally.com/index) and [Joey L quick portfolio](https://joeyl.com/overview/category/quick-portfolio) reinforced a near-black gallery background, restrained navigation, and a continuous photo collection. Desktop collections remain continuous with native lazy loading. Mobile uses 40-photo batches to keep the About and channel sections within reach, with a compact, two-row navigation header fixed at the top. The text links and Instagram icon have 44px touch targets and safe-area spacing; there is no bottom navigation bar.

Destination cards use each country’s `cover.webp` before any configured fallback. Responsive variants come from that same image, with revision URLs to refresh replaced covers. The catalogue revalidates on page load. Desktop uses three cover columns, tablet uses two, and phones show one generous landscape cover per row. Cream serif country names, small photo counts, and restrained arrow overlays keep the black layout focused on the photographs.
