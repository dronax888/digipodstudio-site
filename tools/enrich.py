"""Turn the DIGIPOD product registry + Etsy image data into site-ready product records.

Input:  data/registry.json (from the Google Sheet REGISTRY tab)
        data/images.json   (listing id -> main photo + alt text, from the Etsy shop pages)
        data/bestsellers.json (ordered listing ids shown first on the home page)
Output: data/products.json
"""
import json, re, unicodedata, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ROOT, 'data', *p)

UNAVAILABLE = {'4532807831'}  # Etsy shows "item unavailable" (checked 6 Nov 2026)

OCCASIONS = {
    '1': ('quinceanera-sweet-16', 'Quinceañera & Sweet 16', 'Quinceañera'),
    '2': ('birthday-baby', 'Birthday & Baby', 'Birthday'),
    '3': ('wedding-anniversary', 'Wedding & Anniversary', 'Wedding'),
    '4': ('bat-bar-mitzvah', 'Bat & Bar Mitzvah', 'Mitzvah'),
    '5': ('graduation', 'Graduation', 'Graduation'),
    '6': ('party-extras', 'Party Extras', 'Party'),
}

TYPE_SLUG = {
    'Slideshows': 'slideshows', 'Video Invitations': 'video-invitations', 'Save the Dates': 'save-the-dates',
    'Website Invitations': 'website-invitations', 'Printable Invitations': 'printable-invitations',
    'Invitations & Save the Dates': 'invitations-save-the-dates', 'Save the Date Teasers': 'save-the-date-teasers',
    'Screen Displays & Banners': 'screen-displays-banners', 'Signs, Boards & Table Decor': 'signs-boards-decor',
    'Custom Edit Services': 'custom-edit-services',
}

# colour families: (slug, label, swatch hex, keyword patterns)
COLOURS = [
    ('pink', 'Pink & blush', '#F2A7BF', r'\b(pink|blush|coquette|peony|cherry blossom)\b'),
    ('rose-gold', 'Rose gold', '#D8A39A', r'rose ?gold'),
    ('red', 'Red & burgundy', '#B3203A', r'\b(red|burgundy|wine|maroon|crimson)\b'),
    ('fuchsia', 'Fuchsia & magenta', '#D0157A', r'\b(fuchsia|magenta|hot pink|neon pink)\b'),
    ('champagne', 'Champagne & gold', '#D9BC86', r'\b(champagne|gold|golden)\b'),
    ('blue', 'Blue', '#8DB3DA', r'\b(blue|navy|dusty blue|light blue|royal blue|baby blue|midnight)\b'),
    ('green', 'Green & sage', '#7FA287', r'\b(green|sage|emerald|olive|mint)\b'),
    ('purple', 'Lavender & purple', '#A98BC9', r'\b(lavender|lilac|purple|violet|plum)\b'),
    ('black', 'Black', '#2C2730', r'\b(black|noir)\b'),
    ('white', 'White, ivory & silver', '#EEE6DC', r'\b(white|ivory|cream|snow|silver)\b'),
]

THEMES = [
    ('princess', 'Princess & fairytale', r'\b(princess|tiara|crown|royal|fairytale|fairy ?tale|carriage|cinderella)\b'),
    ('floral', 'Floral', r'\b(floral|flower|roses?|peony|blossom|garden)\b'),
    ('winter', 'Winter wonderland', r'\b(winter|snow|snowflake|onederland|wonderland)\b'),
    ('enchanted', 'Enchanted forest', r'\b(enchanted|forest|butterfl\w+)\b'),
    ('bows', 'Bows & coquette', r'\b(bows?|coquette)\b'),
    ('neon', 'Neon & party', r'\b(neon|disco|glow|haze)\b'),
    ('glam', 'Modern glam', r'\b(glam|glitter|sparkle|luxury|elegant)\b'),
    ('musical', 'With music', r'\b(music|musical|song)\b'),
]

FEATURES = [
    (r'rsvp', 'Online RSVP'),
    (r'bilingual|english\s*&\s*spanish|spanish', 'English & Spanish'),
    (r'music|musical', 'Music included'),
    (r'countdown', 'Countdown'),
    (r'qr code', 'QR code to share'),
    (r'mp4', 'Download as MP4'),
    (r'with photo|photo', 'Add your photos'),
    (r'animated', 'Animated'),
]


def slugify(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s.lower()).strip('-')
    return re.sub(r'-+', '-', s)


def clean_title(t):
    t = t.replace(' l ', ' | ').replace(' I ', ' | ').replace('–', '|')
    parts = [p.strip(' ,') for p in re.split(r'\s*\|\s*', t) if p.strip()]
    name = parts[0] if parts else t
    i = 1
    TYPEWORD = re.compile(r'template|slideshow|invitation|save the date|montage|display|banner|sign|website', re.I)
    while (len(name.split()) < 3 or not TYPEWORD.search(name)) and i < len(parts) and len(name.split()) < 9:  # e.g. "Quinceanera | Sweet 16 | Slideshow Template"
        name = f'{name} {parts[i]}'
        i += 1
    name = re.sub(r'\s+', ' ', name)
    if len(name) > 64 and ',' in name:
        m = re.search(r'(template|slideshow|invitation|save the date|montage|website|display|banner|sign|video)', name, re.I)
        if m:
            cut = name.find(',', m.end())
            if cut > 0:
                name = name[:cut].strip()
    return name, parts


def big_image(url):
    # Etsy CDN sizes: il_340x270 (card) -> il_794xN (large)
    return re.sub(r'il_\d+x\d+\.', 'il_794xN.', url)


def main():
    reg = json.load(open(D('registry.json')))
    imgs = json.load(open(D('images.json')))
    best = json.load(open(D('bestsellers.json')))['listing_ids']
    order = json.load(open(D('sales_rank.json')))['order'] if os.path.exists(D('sales_rank.json')) else []
    sold = {lid: len(order) - i for i, lid in enumerate(order)}  # higher = sold more
    used = {}
    out = []
    for r in reg:
        lid = r['LISTING ID'].strip()
        if lid in UNAVAILABLE:
            continue
        no = r['PRODUCT NO.']
        g, sg = no.split('.')[0], '.'.join(no.split('.')[:2])
        occ_slug, occ_name, occ_short = OCCASIONS[g]
        title = r['PRODUCT TITLE (ETSY)'].strip()
        name, parts = clean_title(title)
        im = imgs.get(lid, {})
        alt = re.sub(r'^May include:\s*', '', im.get('alt', '')).strip()
        hay = (title + ' ' + alt).lower()
        colours = [c[0] for c in COLOURS if re.search(c[3], hay)]
        # 'gold' inside 'rose gold' should not also count as champagne unless champagne named
        if 'rose-gold' in colours and 'champagne' in colours and not re.search(r'champagne|(?<!rose )gold', hay):
            colours.remove('champagne')
        themes = [t[0] for t in THEMES if re.search(t[2], hay)]
        feats = []
        for pat, lab in FEATURES:
            if re.search(pat, hay) and lab not in feats:
                feats.append(lab)
        m = re.search(r'(\d+)\s*slides', hay)
        slides = int(m.group(1)) if m else None
        # unique, readable slug: name + distinguishing colour/theme + short id
        base = slugify(name)
        if len(base) > 60:
            base = base[:60].rsplit('-', 1)[0]
        slug = base
        if slug in used:
            extra = '-'.join([c for c in colours[:2]] + [t for t in themes[:1]])
            slug = f"{base}-{extra}".strip('-') if extra else base
            if slug in used:
                slug = f"{base}-{lid[-5:]}"
        used[slug] = lid
        price = float(r['PRICE (USD)'].replace('$', '').replace(',', '') or 0)
        out.append({
            'no': no, 'id': lid, 'slug': slug, 'name': name, 'etsy_title': title,
            'subtitle_parts': parts[1:4],
            'occasion': occ_slug, 'occasion_name': occ_name, 'occasion_short': occ_short,
            'type': TYPE_SLUG[r['SUB-GROUP']], 'type_name': r['SUB-GROUP'], 'subgroup': sg,
            'price': price,
            'url': f'https://digipodstudio.etsy.com/listing/{lid}',  # Etsy Share & Save format
            'img': im.get('img', ''), 'img_lg': big_image(im.get('img', '')), 'alt': alt,
            'colours': colours, 'themes': themes, 'features': feats, 'slides': slides,
            'best': best.index(lid) + 1 if lid in best else None,
            'sold': sold.get(lid, 0),
            'order': int(no.split('.')[-1]),
        })
    # Give products that share a generic name a descriptive one (colour + theme first)
    from collections import Counter
    cnt = Counter(p['name'].lower() for p in out)
    CW = {'pink': 'Pink', 'rose-gold': 'Rose Gold', 'red': 'Red', 'fuchsia': 'Fuchsia', 'champagne': 'Champagne Gold',
          'blue': 'Blue', 'green': 'Sage Green', 'purple': 'Lavender', 'black': 'Black', 'white': 'Ivory'}
    TW = {'princess': 'Princess', 'floral': 'Floral', 'winter': 'Winter', 'enchanted': 'Enchanted', 'bows': 'Bow',
          'neon': 'Neon', 'glam': 'Glam', 'musical': ''}
    seen = Counter()
    PHRASE = re.compile(r'\b((?:light|dusty|royal|navy|baby|hot|rose|champagne|sage|emerald|blush|midnight|pastel)\s+)?'
                        r'(blue|pink|gold|red|green|lavender|purple|lilac|black|white|ivory|burgundy|fuchsia|blush|champagne|silver|rosegold|rose gold|sage|emerald|navy)'
                        r'(\s+(?:and|&)\s+(?:light |dusty |royal |rose )?(?:blue|pink|gold|red|green|lavender|purple|black|white|ivory|silver|champagne|sage))?\b', re.I)
    for p in out:
        if cnt[p['name'].lower()] > 1:
            low = p['name'].lower()
            m = None
            for part in p['subtitle_parts'] + [p['etsy_title']]:
                m = PHRASE.search(part)
                if m:
                    break
            if m and m.group(0).lower() not in low:
                phrase = ' '.join(w if w.lower() in ('and',) else w.capitalize() for w in m.group(0).replace('&', 'and').split())
                p['name'] = f"{phrase} {p['name']}"
                seen[p['name'].lower()] += 1
                if seen[p['name'].lower()] > 1:
                    p['name'] += f" (Design {seen[p['name'].lower()]})"
                continue
            words = [CW[c] for c in p['colours'][:2] if CW[c].lower().split()[0] not in low]
            words += [TW[t] for t in p['themes'][:1] if TW[t] and TW[t].lower() not in low]
            if words:
                p['name'] = ' '.join(words) + ' ' + p['name']
        seen[p['name'].lower()] += 1
        if seen[p['name'].lower()] > 1:
            p['name'] += f" (Design {seen[p['name'].lower()]})"
    ov = json.load(open(D('name_overrides.json')))['names'] if os.path.exists(D('name_overrides.json')) else {}
    for p in out:
        if p['id'] in ov:
            p['name'] = ov[p['id']]
    slugs = Counter()
    for p in out:
        b = slugify(p['name'].replace('(Design', ''))
        if len(b) > 64:
            b = b[:64].rsplit('-', 1)[0]
        cand, n = b, 1
        while cand in slugs:
            n += 1
            cand = f"{b}-{n}"
        slugs[cand] += 1
        p['slug'] = cand
    json.dump(out, open(D('products.json'), 'w'), indent=1, ensure_ascii=False)
    from collections import Counter
    print(len(out), 'products')
    print('colours', Counter(c for p in out for c in p['colours']).most_common())
    print('themes', Counter(c for p in out for c in p['themes']).most_common())
    print('no image', [p['no'] for p in out if not p['img']])


if __name__ == '__main__':
    main()
