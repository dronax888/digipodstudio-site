# digipodstudio.com

The website for DigipodStudio (Etsy shop). A fast static site: no database, no monthly platform fee, hosted free on GitHub Pages at https://digipodstudio.com.

## What is in here

| Folder | What it holds |
|---|---|
| `data/registry.json` | Copy of the DIGIPOD product registry (Google Sheet, REGISTRY tab) |
| `data/images.json` | Main Etsy photo + photo description for each listing |
| `data/bestsellers.json` | Listing IDs in Best Sellers order (home page, top) |
| `data/reviews.json`, `data/shop.json` | Real Etsy reviews and shop stats shown on the site |
| `data/content-calendar.json` | The daily article queue |
| `content/journal/*.md` | Articles (English in /journal/, Spanish in /es/blog/) |
| `tools/enrich.py` | Registry + images -> `data/products.json` (names, colors, styles, links) |
| `tools/build.py` | Builds every page into `site/` |
| `tools/sitecopy.py` | Page wording for occasions, template types and FAQs |
| `assets/` | Design: `site.css` (look) and `site.js` (search, filters, party list, planner) |
| `site/` | The built website that GitHub Pages serves (do not edit by hand) |

## Rebuild after any change

```
python3 tools/enrich.py
python3 tools/build.py
```

Then commit and push. GitHub Pages republishes in about a minute.

## Common updates

- **New Etsy listing:** add it to the registry Google Sheet, refresh `data/registry.json`, add its photo to `data/images.json` (from the Etsy shop page), rebuild.
- **Best sellers changed:** edit the order of IDs in `data/bestsellers.json`, rebuild. Use Etsy Shop Manager > Stats (orders per listing) as the source.
- **Product video ready:** add `"video": "<YouTube ID>"` for that listing in `data/products.json` via `tools/enrich.py` (videos map), rebuild. The video shows under the product photo.
- **Listing removed on Etsy:** add its ID to `UNAVAILABLE` in `tools/enrich.py`, rebuild.

## Daily article (SEO)

One article a day from `data/content-calendar.json`. Rules for every article:

1. Written for parents planning the event, plain and practical, 900 to 1,400 words.
2. Front matter: title (under 65 characters where possible), description (under 158), date, slug, lang, tags (occasion/type/color slugs used to pick products).
3. At least two `[[products: <tags> | 3]]` blocks, and 2 or more links to other pages on the site (planner, related articles, collections).
4. Ends with `## Frequently asked questions` (or `## Preguntas frecuentes`) with 2 to 4 `###` questions. These become FAQ rich results.
5. No invented statistics, prices or quotes. Never quote song lyrics. Only general, widely accepted advice.
6. English only. From 8 Nov 2026 every new article, title, caption and hashtag is in English (no Spanish articles, no ¿ or ¡ in captions). The Spanish pages already published stay online.
7. The first tag must be the occasion slug (e.g. `quinceanera-sweet-16`). It decides which occasion feed the article goes into.

## Sitemap dates and internal links (SEO, 11 Nov 2026)

- `data/page_dates.json` stores, for every page, a fingerprint of its HTML and the day it last really changed. The build uses it for `<lastmod>` in the sitemap, so Google sees true update dates instead of "today" on every page. Commit it with each build; never edit it by hand.
- Articles link to each other ("Keep reading"), occasion and type pages show the latest matching articles ("Planning guides"), and product pages show 2 matching articles chosen oldest-first so they stay stable as new articles are published.
- Product page titles keep "(Design N)" when shortened, so similar designs never share a title.

## RSS feeds (Pinterest auto-publish)

`site/feed.xml` lists every article; `site/feeds/<occasion>.xml` lists one occasion only. Every item carries its hero image so Pinterest can pin it. Pinterest (account digipodquenci, Settings > Bulk create Pins > Auto-publish) reads `https://digipodstudio.com/feeds/quinceanera-sweet-16.xml` and pins each new quinceañera article to the board "Quinceañera Planning Ideas" within about a day. Keep these URLs stable.

## IndexNow (instant ping to Bing and others)

After every deploy, GitHub Actions runs `tools/indexnow.py`, which sends the pages that changed in that commit to IndexNow. Put `[indexnow all]` in a commit message to resend every page in the sitemap. The key file is `site/<indexnow_key>.txt` (key in `data/shop.json`).

## Social accounts

`SOCIAL` in `tools/build.py` lists every official account (Instagram @digipodquenci and @digipodceleb, Facebook Quince and Celebrations Pages, Pinterest digipodquenci). It feeds the home page "Follow along" cards, the footer icons and the Organization `sameAs` schema. Add or remove an account there and rebuild. The Celebrations Pinterest account (digipodceleb) is left out while it is suspended.

Logo rules (Meta and Pinterest brand guidelines): use the official logo shapes in `NET_ICON` only. Facebook = full blue circle with white f (#0866FF), never the f alone, never recoloured or outlined. Pinterest = red badge (#E60023) with white P, never recoloured. Instagram = glyph in one solid colour (white on our dark backgrounds). No borders or frames around the logos, keep clear space around them, and always pair them with a call to action (Follow).

## Links

All Buy buttons use Etsy's Share & Save format (`digipodstudio.etsy.com/listing/<ID>`).

## Facebook daily product posts

`social/facebook-daily-posts.json` holds the ready-made Facebook posts (English) for both Pages, best sellers first: Quince Page (quinceañera & sweet 16 products) and Celebrations Page (all other occasions). Two posts per Page per day, early morning Manila time (Quince 06:00 and 07:30, Celebrations 06:15 and 07:45); the daily article share goes out between them (Quince 07:00, Celebrations 06:45). The daily scheduled task "DigipodStudio daily Facebook product posts" reads this file and schedules the next days in Metricool. Rebuild the file after product changes with `python3 social/make_fb_posts.py .` (keep the start date so the order does not jump).

