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

All 82 homepage highlights, all 15 destination covers and the 10 corrected Poland/Taiwan photos have visually reviewed titles and descriptive alt text (107 photos in total). These descriptions appear in image alternatives, the accessible viewer, social previews and image structured data. Many other country photographs still have generic alt text. Add accurate landmarks, city names, and meaningful visual descriptions through `data/photo-details.json`, keyed by the existing numeric photo ID, then rerun processing and building. Describe what is actually in the photograph; do not repeat keyword lists or infer places that have not been identified.

`data/country-summaries.json` supplies distinct, visible summaries of the subjects represented in each collection. The catalogue passes the same text to static pages and the JavaScript gallery so metadata and visible content stay consistent. Keep summaries accurate when the library changes.

The homepage title starts with Our Travel Photobook. The existing WebSite and Organization structured data also identify the established `ourtravelphotobook` handle as an alternate name. A 96px PNG favicon complements the browser and Apple icons for search display.

Short first-person accounts of real trips, dates, locations, and photography choices would give readers and search engines more useful context. Add these only when Arjun supplies or confirms the facts. Keep the photographer's name, brand, and social profile links consistent.

The Google Search Console Domain property is verified and the canonical sitemap has been submitted. Bing Webmaster Tools setup remains separate. Check indexing, image search impressions, search terms, mobile page experience, and broken links over time. Preserve the domain verification TXT record in Cloudflare; it is not part of the public site build.

## New-domain indexing

The custom domain first went live on 14 September 2026. Availability at the URL does not mean Google has already discovered, crawled and indexed it. The established Instagram account may appear first while the new website is still being discovered. A public search alone cannot conclusively establish index status; use Search Console URL Inspection.

Search Console inspection on 14 September 2026 reported the homepage as **URL is unknown to Google**, with no recorded crawl. The sitemap was submitted to the verified Domain property. Its first report said **Couldn't fetch**, but Google's subsequent live test fetched that exact sitemap successfully with crawling allowed. The XML is valid and publicly returns HTTP 200; initial report data is still processing. Google reported no manual actions or security issues. If the sitemap error persists, inspect the exact sitemap URL again with a live test and review the report's detailed error before changing DNS or resubmitting.

Request homepage indexing once after the release, and use the sitemap for the remaining galleries. Repeated requests do not accelerate crawling. Update the Instagram and YouTube profile website fields to the canonical domain when signed into those accounts; this code release does not edit social profiles.

Google says crawling can take days to weeks, and indexing or ranking is not guaranteed. No code change can force an immediate first-place brand result. Keep redirects stable, add accurate photographic context, and check Search Console for actual crawl or canonical errors.

## GEO scope

Here, GEO means discoverability in generative/AI search. The improvements make source content accessible and attribution unambiguous. There is no ranking or AI-citation guarantee. Google says its AI search features use the existing SEO foundations and require no special AI files or schema. No speculative `llms.txt`, hidden keyword blocks, or fabricated FAQs were added.

## Sources

- [Google: JavaScript SEO](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)
- [Google: crawlable URLs and fragments](https://developers.google.com/search/docs/crawling-indexing/url-structure)
- [Google: AI features and your website](https://developers.google.com/search/docs/appearance/ai-features)
- [Google: image credit metadata](https://developers.google.com/search/docs/appearance/structured-data/image-license-metadata)
- [Google: request crawling and submit a sitemap](https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl)
- [Google: site names and alternate names](https://developers.google.com/search/docs/appearance/site-names)
- [Netlify: file-based Pretty URL configuration](https://docs.netlify.com/build/configure-builds/file-based-configuration/)
