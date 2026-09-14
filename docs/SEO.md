# Search visibility and AI search discoverability

## Implemented

- The homepage highlights, destination cards, and each country gallery are rendered into HTML at build time. Visitors and crawlers can follow real links and see photographs without JavaScript. JavaScript adds the viewer and existing mobile batches of 40.
- Each country has a stable page such as `france-photography.html` with a unique heading, title, description, canonical URL, and cover-based social preview. Existing `destinations.html#country=France` links move to the new page in the browser. Fragments are not sent to servers, so this compatibility transition is client-side.
- `sitemap.xml` lists the homepage, destination index, and populated country pages, with public image URLs. `robots.txt` permits crawling and points to that sitemap. Neither includes private originals or registry paths. Empty future countries remain available to visitors with `noindex, follow` until populated.
- JSON-LD identifies Arjun Sarkar, Our Travel Photobook, the website, country collections, breadcrumbs, and image authorship. Structured data reflects the visible collection; it does not invent ratings, awards, opening hours, or licensing offers.
- Inline structured data is safely serialized and authorized with exact CSP hashes. The page and HTTP security policies retain their restrictions on executable scripts.
- Both hosted copies identify the configured primary site as canonical. The primary is `https://www.ourtravelphotobook.com/`. If it changes, update both `data/site.json` and `netlify.toml` as described in `DOMAIN.md`.
- Netlify's automatic Pretty URL rewriting is disabled in configuration so generated links and canonical `.html` URLs stay consistent. Existing extensionless aliases can still be served by Netlify; the canonical tag identifies the preferred URL.

`build.py` calls `seo.py`; adding or removing photos and running the normal import/build commands refreshes page counts, galleries, metadata, and the sitemap together. Country slug collisions fail the build instead of overwriting a page. Do not manually edit `dist/`.

## What improves the content next

Many photographs still have generic alt text. Add accurate landmarks, city names, and meaningful visual descriptions through `data/photo-details.json`, keyed by the existing numeric photo ID, then rerun processing and building. Describe what is actually in the photograph; do not repeat keyword lists or infer places that have not been identified.

Short first-person accounts of real trips, dates, locations, and photography choices would give readers and search engines more useful context. Add these only when Arjun supplies or confirms the facts. Keep the photographer's name, brand, and social profile links consistent.

After publication, submit the sitemap in Google Search Console and Bing Webmaster Tools. Check indexing, image search impressions, search terms, mobile page experience, and broken links over time. A property verification token must come from the relevant account; it is not invented or included here.

## GEO scope

Here, GEO means discoverability in generative/AI search. The improvements make source content accessible and attribution unambiguous. There is no ranking or AI-citation guarantee. Google says its AI search features use the existing SEO foundations and require no special AI files or schema. No speculative `llms.txt`, hidden keyword blocks, or fabricated FAQs were added.

## Sources

- [Google: JavaScript SEO](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)
- [Google: crawlable URLs and fragments](https://developers.google.com/search/docs/crawling-indexing/url-structure)
- [Google: AI features and your website](https://developers.google.com/search/docs/appearance/ai-features)
- [Google: image credit metadata](https://developers.google.com/search/docs/appearance/structured-data/image-license-metadata)
- [Netlify: file-based Pretty URL configuration](https://docs.netlify.com/build/configure-builds/file-based-configuration/)
