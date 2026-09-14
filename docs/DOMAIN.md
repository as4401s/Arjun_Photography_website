# Connecting the Cloudflare domain to Netlify

Checked against Cloudflare and Netlify documentation on 14 September 2026. The website remains hosted on Netlify; Cloudflare supplies the domain registration and DNS.

## Connected domain — 14 September 2026

The existing **ourtravelphotobook** Netlify project now has both custom hostnames attached. Its primary address is **https://www.ourtravelphotobook.com/**; the bare domain redirects to it. Netlify issued a Let’s Encrypt certificate covering both names, and normal HTTPS certificate validation and the bare-to-www redirect passed before publication.

Cloudflare remains authoritative for DNS. The user configured these DNS-only records, confirmed through Cloudflare and Google public resolvers:

| Type | Name | Target |
| --- | --- | --- |
| A | `@` | `75.2.60.5` |
| CNAME | `www` | `ourtravelphotobook.netlify.app` |

This A record is Netlify's standard fallback; the flattened CNAME alternative below is also supported. No change to nameservers is needed. Netlify manages the website certificate and its automatic renewal.

`data/site.json` and `netlify.toml` both use the primary www URL. There are no Netlify UI environment overrides. The release generates canonical URLs, structured data, robots directives, and all 17 sitemap entries using this address. A host-specific permanent redirect in `netlify.toml` preserves old Netlify paths while moving visitors to www.

For subsequent releases, publish only when Arjun explicitly requests it. Verify valid HTTPS on both custom names, path-preserving redirects from the bare and Netlify hostnames, canonical URLs, sitemap, security headers, and representative image/navigation requests after publication.

The Google Search Console Domain property was verified on 14 September 2026 under Arjun's requested primary account, and the second requested account was granted Full access. The canonical sitemap has been submitted. Google's live URL test successfully fetched the sitemap with crawling allowed; initial reporting is still processing. See `SEO.md` for the indexing diagnosis. Bing verification remains a separate account setup task. Preserve the Cloudflare verification TXT record.

## Registration reference (purchase completed)

1. **ourtravelphotobook.com** is the purchased domain. The following registration steps are retained for reference; no additional purchase is needed.
2. Create or sign in to your [Cloudflare account](https://dash.cloudflare.com/), verify your email, and enable two-factor authentication.
3. Open **Domain Registration → Register Domains**, search the name, and select **Purchase**. Review the registration term, first-year total, renewal price, and any tax/currency charges before completing checkout. Cloudflare charges registry/ICANN cost without registrar markup; the current checkout quote is the price to use.
4. Enter accurate registration contact details, pay, and complete the registrant-email verification. Enable auto-renew and keep payment details current.
5. In the domain's configuration, enable **DNSSEC**. Keep the Cloudflare nameservers: domains registered through Cloudflare must use its DNS service. Netlify hosting works with these nameservers.

Sources: [Cloudflare registration instructions](https://developers.cloudflare.com/registrar/get-started/register-domain/), [Registrar pricing policy](https://developers.cloudflare.com/registrar/faq/), [DNSSEC instructions](https://developers.cloudflare.com/registrar/get-started/enable-dnssec/).

## Connect your existing site

6. In Netlify, open **ourtravelphotobook → Domain management → Add a domain**. Enter your purchased domain and add both the bare domain and `www` if Netlify has not added the second automatically. Keep external DNS; do not switch nameservers to Netlify.
7. In Cloudflare, open the domain's **DNS → Records**. For Netlify's standard network, use:

| Type | Name | Target | Proxy status |
| --- | --- | --- | --- |
| CNAME | `@` | `apex-loadbalancer.netlify.com` | **DNS only** (grey cloud) |
| CNAME | `www` | `ourtravelphotobook.netlify.app` | **DNS only** (grey cloud) |

Cloudflare flattens the apex CNAME automatically. Use TTL **Auto**. If Netlify's DNS-verification screen supplies a different target for your project, follow that project-specific target. Replace conflicting website A/AAAA/CNAME records for the same names; preserve email MX and verification TXT records.

8. In Netlify, verify DNS and wait for the HTTPS certificate. DNS can take up to a day to propagate. Choose **www.ourtravelphotobook.com** as the primary domain, as Netlify recommends a subdomain when using external DNS. Check that both names open the same site and the secondary redirects to the primary. With DNS-only records, Netlify provides the website HTTPS connection.

Sources: [Netlify external DNS](https://docs.netlify.com/manage/domains/configure-domains/configure-external-dns/), [Cloudflare CNAME flattening](https://developers.cloudflare.com/dns/cname-flattening/), [Cloudflare proxy status](https://developers.cloudflare.com/dns/proxy-status/).

## Update search references after the domain works

9. Update the `url` in `data/site.json` and `SITE_URL` in `netlify.toml` to the **same primary HTTPS address**, ending with `/`. A Netlify UI environment override, if configured, must match too. Rebuild to regenerate canonical URLs, structured data, `robots.txt`, and the sitemap. Publish only when explicitly authorized.
10. Verify the old Netlify address redirects to the primary custom domain while retaining paths. Configure a host-specific permanent redirect if it does not; do not add a catch-all redirect that sends the new domain back to itself. Keep country-page paths stable.
11. Google setup is complete as recorded above. For a future domain, add it as a **Domain property** in [Google Search Console](https://search.google.com/search-console/), copy its verification TXT record into Cloudflare DNS, and submit its sitemap after publication. Add the site to [Bing Webmaster Tools](https://www.bing.com/webmasters/) too; Bing setup has not been completed.
12. Update Instagram and YouTube profile links to the new primary address.

See [Google's sitemap submission guide](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap) and [site-move guidance](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes). Buying a domain does not automatically improve rankings; content, crawlability, relevance, and reputation still matter.
