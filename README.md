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
6. Spanish articles are written natively in Spanish (US Latino audience), not translated word for word.

## IndexNow (instant ping to Bing and others)

After every deploy, GitHub Actions runs `tools/indexnow.py`, which sends the pages that changed in that commit to IndexNow. Put `[indexnow all]` in a commit message to resend every page in the sitemap. The key file is `site/<indexnow_key>.txt` (key in `data/shop.json`).

## Links

All Buy buttons use Etsy's Share & Save format (`digipodstudio.etsy.com/listing/<ID>`).
