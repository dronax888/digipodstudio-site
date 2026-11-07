"""Build the Digipod Studio website into ./site (production) or ./preview (relative links).

    python3 tools/build.py            # production build for digipodstudio.com
    python3 tools/build.py --preview  # same pages, relative links, for previewing anywhere

Sources: data/products.json (from tools/enrich.py), data/reviews.json, data/shop.json,
content/journal/*.md (articles, English and Spanish), tools/sitecopy.py (page copy).
"""
import json, os, re, sys, shutil, html, datetime
from collections import Counter, defaultdict
import markdown

sys.path.insert(0, os.path.dirname(__file__))
from sitecopy import OCCASION_COPY, TYPE_COPY, GENERAL_FAQ  # noqa: E402  (tools/sitecopy.py)
from enrich import COLOURS, THEMES  # noqa: E402

ROOTDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import hashlib
PRODUCTS_V = hashlib.md5(open(os.path.join(ROOTDIR, 'data', 'products.json'), 'rb').read()).hexdigest()[:10]
ASSET_V = hashlib.md5(open(os.path.join(ROOTDIR, 'assets', 'site.css'), 'rb').read() + open(os.path.join(ROOTDIR, 'assets', 'site.js'), 'rb').read()).hexdigest()[:10]
PREVIEW = '--preview' in sys.argv
OUT = os.path.join(ROOTDIR, 'preview' if PREVIEW else 'site')
SITE = 'https://digipodstudio.com'
BRAND = 'Digipod Studio'
ETSY_SHOP = 'https://www.etsy.com/shop/DigipodStudio'
SOCIAL = [  # official DigipodStudio social pages (shown in the footer and in Organization sameAs)
    ('Facebook · Celebrations', 'https://www.facebook.com/digipodstudiocelebrations'),
    ('Facebook · Quince & Sweet 16', 'https://www.facebook.com/digipodstudioquince'),
]
FB_ICON = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="currentColor"><path d="M13.5 22v-8h2.7l.4-3.2h-3.1V8.8c0-.9.3-1.6 1.6-1.6h1.7V4.4c-.3 0-1.3-.1-2.5-.1-2.4 0-4.1 1.5-4.1 4.2v2.3H7.5V14h2.7v8h3.3z"/></svg>'
TODAY = datetime.date.today()

load = lambda n: json.load(open(os.path.join(ROOTDIR, 'data', n)))
P = load('products.json')
REVIEWS = load('reviews.json')
SHOP = load('shop.json')
_VER = load('site_verification.json') if os.path.exists(os.path.join(ROOTDIR, 'data', 'site_verification.json')) else {}
VERIFY_META = ''.join(f'<meta name="{k}" content="{v}">\n' for k, v in _VER.get('meta', {}).items())
FEATURES = load('colour_features.json')['features'] if os.path.exists(os.path.join(ROOTDIR, 'data', 'colour_features.json')) else {}
BYID = {p['id']: p for p in P}
COL = {c[0]: {'slug': c[0], 'label': c[1], 'hex': c[2]} for c in COLOURS}
THM = {t[0]: t[1] for t in THEMES}
OCC_ORDER = ['quinceanera-sweet-16', 'birthday-baby', 'wedding-anniversary', 'bat-bar-mitzvah', 'graduation', 'party-extras']
OCC_NAME = {p['occasion']: p['occasion_name'] for p in P}
TYPE_ORDER = ['slideshows', 'video-invitations', 'save-the-dates', 'website-invitations', 'printable-invitations',
              'invitations-save-the-dates', 'save-the-date-teasers', 'screen-displays-banners', 'signs-boards-decor', 'custom-edit-services']
NEWEST_ID = max(int(p['id']) for p in P)

e = html.escape


def rank(p):
    """Default order: best sellers first, then most units sold this year, then newest listings."""
    return (p['best'] or 999, -p.get('sold', 0), -int(p['id']))


RANKPOS = {p['id']: i for i, p in enumerate(sorted(P, key=rank))}


def money(x):
    return f'${x:,.2f}'


# ---------------------------------------------------------------- icons
ICON = {
    'heart': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M12 20.5s-7.5-4.6-9.3-9.1C1.4 8 3.5 4.5 7 4.5c2 0 3.6 1.1 5 2.9 1.4-1.8 3-2.9 5-2.9 3.5 0 5.6 3.5 4.3 6.9-1.8 4.5-9.3 9.1-9.3 9.1z"/></svg>',
    'search': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>',
    'menu': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
    'check': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M5 12.5l4.2 4.2L19 7"/></svg>',
    'bag': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M5 8h14l-1 12H6L5 8z"/><path d="M9 8V6a3 3 0 016 0v2"/></svg>',
    'cal': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M9 3v4M15 3v4"/></svg>',
}
LOGO = ('<svg viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="19" fill="#2B0B25"/>'
        '<circle cx="20" cy="20" r="15.5" fill="none" stroke="#B08A4F" stroke-width=".8"/>'
        '<text x="20.5" y="27.5" text-anchor="middle" font-family="Bodoni Moda,Didot,Georgia,serif" font-style="italic" font-size="21" fill="#FCF7F9">d</text>'
        '<circle cx="29" cy="12" r="1.6" fill="#E0559A"/></svg>')


# ---------------------------------------------------------------- links
def write(path, content):
    """path like 'shop/index.html'. Resolves @/ links for production or preview."""
    depth = path.count('/')
    # relative links work on the custom domain, on a GitHub Pages sub-path and from disk
    root = ('../' * depth or './') if path != '404.html' else '/'
    ext = '' if not PREVIEW else 'index.html'

    def fix(m):
        attr, target = m.group(1), m.group(2)
        frag = ''
        if '#' in target:
            target, frag = target.split('#', 1)
            frag = '#' + frag
        q = ''
        if '?' in target:
            target, q = target.split('?', 1)
            q = '?' + q
        if target == '' or target.endswith('/'):
            target = target + ext
        return f'{attr}="{root}{target}{q}{frag}"'
    content = re.sub(r'(href|src)="@/([^"]*)"', fix, content)
    content = content.replace('data-root="@/"', f'data-root="{root}"').replace('data-ext="@"', f'data-ext="{ext}"')
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w').write(content)


SITEMAP = []


def page(path, title, desc, body, *, schema=None, og_image=None, lang='en', alternates=None, body_page='', canonical=None,
         noindex=False, priority='0.6', og_type='website'):
    url = canonical or (SITE + '/' + path.replace('index.html', ''))
    if len(title) > 68 and title.endswith(' | Digipod Studio'):
        title = title[:-len(' | Digipod Studio')]
    if len(desc) > 160:
        desc = desc[:157].rsplit(' ', 1)[0] + '…'
    if not noindex:
        SITEMAP.append((url, priority))
    og_image = og_image or (P[0]['img_lg'])
    sch = ''
    if schema:
        for s in (schema if isinstance(schema, list) else [schema]):
            sch += '<script type="application/ld+json">' + json.dumps(s, ensure_ascii=False) + '</script>\n'
    alt = ''
    if alternates:
        for hl, u in alternates.items():
            alt += f'<link rel="alternate" hreflang="{hl}" href="{u}">\n'
    es = lang == 'es'
    nav_items = [
        ('quinceanera-sweet-16/', 'Quinceañera'), ('birthday-baby/', 'Cumpleaños' if es else 'Birthdays'),
        ('wedding-anniversary/', 'Bodas' if es else 'Weddings'), ('bat-bar-mitzvah/', 'Mitzvah'),
        ('shop/', 'Ver todo' if es else 'Shop all'), ('planner/', 'Planificador' if es else 'Planner'),
        ('es/blog/' if es else 'journal/', 'Blog' if es else 'Journal'),
    ]
    cur = path.replace('index.html', '')
    nav = ''.join(f'<a href="@/{h}"{" aria-current=page" if cur.startswith(h) else ""}>{t}</a>' for h, t in nav_items)
    nav += ('<a class="nav-lang" href="@/" lang="en">English</a>' if es else '<a class="nav-lang" href="@/es/" lang="es">Español</a>')
    lang_link = ('<a class="lang" href="@/" hreflang="en" lang="en">English</a>' if es
                 else '<a class="lang" href="@/es/" hreflang="es" lang="es">Español</a>')
    doc = f'''<!doctype html>
<html lang="{lang}" data-root="@/" data-ext="@" data-pv="{PRODUCTS_V}"{' data-signup="' + e(json.dumps(SIGNUP)) + '"' if SIGNUP.get('action') else ''}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
{'<meta name="robots" content="noindex, follow">' if noindex else '<meta name="robots" content="index, follow, max-image-preview:large">'}
{alt}{VERIFY_META if path in ('index.html',) else ''}<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og_image}">
<meta property="og:locale" content="{'es_US' if es else 'en_US'}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#2B0B25">
<link rel="icon" href="@/assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="@/assets/favicon.svg">
<link rel="manifest" href="@/site.webmanifest">
<link rel="alternate" type="application/rss+xml" title="{BRAND} Journal" href="{SITE}/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://i.etsystatic.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,400..700;1,6..96,400..700&family=Instrument+Sans:wght@400..700&display=swap">
<link rel="stylesheet" href="@/assets/site.css?v={ASSET_V}">
{sch}</head>
<body data-page="{body_page}">
<a class="skip" href="#main">{'Ir al contenido' if es else 'Skip to content'}</a>
<header class="top"><div class="wrap">
<a class="logo" href="@/{'es/' if es else ''}" aria-label="{BRAND} home">{LOGO}<span>Digipod Studio</span></a>
<nav class="nav" id="nav" aria-label="Main">{nav}</nav>
<div class="top-actions">
{lang_link}
<button class="icon-btn" type="button" data-open-search aria-label="{'Buscar plantillas' if es else 'Search templates'}">{ICON['search']}</button>
<a class="icon-btn" href="@/party-list/" aria-label="{'Mi lista' if es else 'Your party list'}">{ICON['heart']}<span class="count" hidden>0</span></a>
<button class="icon-btn menu-btn" type="button" aria-controls="nav" aria-expanded="false" aria-label="Menu">{ICON['menu']}</button>
</div></div></header>
<main id="main">
{body}
</main>
{footer(es)}
<div class="search" id="search" role="dialog" aria-modal="true" aria-label="Search templates"><div class="search-box">
<label class="sr" for="search-q">Search templates</label>
<input id="search-q" type="search" placeholder="{'Busca por color, evento o estilo' if es else 'Try “pink quinceañera slideshow” or “sage wedding”'}" autocomplete="off">
<div class="search-results" id="search-results"></div></div></div>
<script src="@/assets/site.js?v={ASSET_V}" defer></script>
</body></html>'''
    write(path, doc)


def footer(es=False):
    occ = ''.join(f'<li><a href="@/{o}/">{OCC_NAME[o]}</a></li>' for o in OCC_ORDER)
    social = ''.join(f'<a href="{u}" rel="noopener" target="_blank">{FB_ICON}<span>{n.split(" · ")[1]}</span></a>' for n, u in SOCIAL)
    cols = ''.join(f'<li><a href="@/colors/{c}/">{COL[c]["label"]}</a></li>' for c in ['pink', 'champagne', 'blue', 'red', 'green', 'purple'])
    return f'''<footer class="foot"><div class="wrap">
<div class="foot-grid">
<div><a class="logo" href="@/">{LOGO}<span>Digipod Studio</span></a>
<p style="margin-top:16px;max-width:30em;color:#D9C3D1">{'Plantillas editables en Canva para quinceañeras, bodas y cumpleaños. Compra segura en Etsy.' if es else 'Editable Canva templates for quinceañeras, sweet 16s, weddings and birthdays. Designed by Digipod Studio, sold securely on Etsy.'}</p>
<p><a class="btn btn-light" href="{ETSY_SHOP}" rel="noopener">{ICON['bag']}{'Tienda en Etsy' if es else 'Visit our Etsy shop'}</a></p>
<p class="foot-social"><span>{'Síguenos' if es else 'Follow us'}</span>{social}</p></div>
<div><h4>Occasions</h4><ul>{occ}</ul></div>
<div><h4>Shop by color</h4><ul>{cols}<li><a href="@/matching-sets/">Matching sets</a></li></ul></div>
<div><h4>Help</h4><ul><li><a href="@/how-it-works/">How it works</a></li><li><a href="@/planner/">Party planner</a></li><li><a href="@/journal/">Journal</a></li><li><a href="@/es/">En español</a></li><li><a href="@/about/">About us</a></li><li><a href="@/contact/">Contact</a></li><li><a href="@/privacy/">Privacy</a></li></ul></div>
</div>
<div class="foot-base"><span>© {TODAY.year} Digipod Studio. Templates are digital downloads, edited in Canva. Canva is a trademark of Canva Pty Ltd; Etsy is a trademark of Etsy, Inc.</span><span>Payments and downloads are handled by Etsy.</span></div>
</div></footer>'''


SIGNUP = SHOP.get('signup', {})


def signup_box(es=False, compact=False):
    """Email sign-up with the free checklist as the reward. Hidden until a form endpoint is configured in data/shop.json."""
    if not SIGNUP.get('action'):
        return ''
    t = (dict(h='Lista gratis para planear su quinceañera', p='Una lista imprimible, mes a mes, desde el save the date hasta el último baile. Además, ideas y diseños nuevos en tu correo, como máximo una vez por semana.',
              email='Tu correo electrónico', occ='Celebración', date='Fecha de la fiesta (opcional)', btn='Enviarme la lista',
              legal='Puedes darte de baja cuando quieras. No compartimos tu correo.', ok='¡Listo! Aquí está tu lista', okp='Guárdala o imprímela. Te escribiremos con ideas para tu fiesta.')
         if es else
         dict(h='Free quinceañera planning checklist', p='A printable, month-by-month checklist from the save the date to the last dance. Plus new designs and planning ideas by email, at most once a week.',
              email='Your email', occ='Celebration', date='Party date (optional)', btn='Send me the checklist',
              legal='Unsubscribe any time. We never share your email.', ok='You are in. Here is your checklist', okp='Save it or print it. We will email you ideas for your celebration.'))
    opts = ''.join(f'<option value="{v}">{l}</option>' for v, l in
                   [('quince', 'Quinceañera'), ('wedding', 'Boda' if es else 'Wedding'), ('birthday', 'Cumpleaños' if es else 'Birthday'),
                    ('mitzvah', 'Bat / Bar Mitzvah'), ('graduation', 'Graduación' if es else 'Graduation'), ('other', 'Otra' if es else 'Other')])
    return f'''<section class="sec signup{' signup-compact' if compact else ''}" aria-labelledby="su-h"><div class="wrap signup-grid">
<div><h2 id="su-h">{t['h']}</h2><p class="lede">{t['p']}</p></div>
<form class="datebox su-form" data-signup method="post" action="{SIGNUP['action']}" target="_blank" novalidate>
<div class="su-fields"><label for="su-email">{t['email']}</label><input id="su-email" name="{SIGNUP['fields']['email']}" data-k="email" type="email" autocomplete="email" required placeholder="name@example.com">
<div class="row" style="margin-top:14px"><div><label for="su-occ">{t['occ']}</label><select id="su-occ" name="{SIGNUP['fields']['celebration']}" data-k="celebration">{opts}</select></div>
<div><label for="su-date">{t['date']}</label><input id="su-date" name="{SIGNUP['fields']['date']}" data-k="date" type="date"></div></div>
<input type="text" data-k="company" tabindex="-1" autocomplete="off" class="sr" aria-hidden="true">
<button class="btn btn-primary" type="submit">{t['btn']}</button>
<p class="su-legal">{t['legal']} <a href="@/privacy/">{'Privacidad' if es else 'Privacy'}</a></p>
<p class="su-error" role="alert" hidden></p></div>
<div class="su-done" hidden><h3>{t['ok']}</h3><p>{t['okp']}</p><p><a class="btn btn-primary" href="@/checklist/">{'Abrir la lista' if es else 'Open the checklist'}</a> <a class="btn btn-ghost su-plan" href="@/planner/">{'Ver mis fechas' if es else 'See my dates'}</a></p></div>
</form></div></section>'''


def card(p, tag='li', lazy=True, extra_attrs=''):
    data = (f' data-occasion="{p["occasion"]}" data-type="{p["type"]}" data-colours="{" ".join(p["colours"])}" '
            f'data-themes="{" ".join(p["themes"])}" data-price="{p["price"]}" data-rank="{RANKPOS[p["id"]]}" '
            f'data-newness="{int(p["id"])}" data-search="{e(search_text(p))}"') if extra_attrs == 'shop' else ''
    return (f'<{tag} class="card"{data}>'
            f'<button class="fav" type="button" data-id="{p["id"]}" aria-pressed="false" aria-label="Save to party list">{ICON["heart"]}</button>'
            f'<a class="cover" href="@/templates/{p["slug"]}/" tabindex="-1" aria-hidden="true"><img {"loading=lazy " if lazy else ""}src="{p["img"]}" '
            f'srcset="{p["img"]} 340w, {p["img_lg"]} 794w" sizes="(max-width:540px) 92vw, 300px" alt="{e(p["name"])}" width="340" height="270"></a>'
            f'<h3><a href="@/templates/{p["slug"]}/">{e(p["name"])}</a></h3>'
            f'<div class="meta"><span>{e(p["type_name"])}</span><span class="price">{money(p["price"])}</span></div></{tag}>')


def search_text(p):
    words = [p['name'], p['etsy_title'], p['occasion_name'], p['type_name'], ' '.join(COL[c]['label'] for c in p['colours']),
             ' '.join(THM[t] for t in p['themes']), 'quince xv anos sweet 16' if p['occasion'] == 'quinceanera-sweet-16' else '']
    s = ' '.join(words).lower()
    return s + (' ' + s.replace('ñ', 'n') if 'ñ' in s else '')


def crumbs(items):
    lis = ''.join(f'<li><a href="@/{h}">{e(t)}</a></li>' if h is not None else f'<li aria-current="page">{e(t)}</li>' for h, t in items)
    schema = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': t, **({'item': SITE + '/' + h} if h is not None else {})} for i, (h, t) in enumerate(items)]}
    return f'<nav class="crumbs wrap" aria-label="Breadcrumb"><ol>{lis}</ol></nav>', schema


def faq_html(faqs):
    return '<div class="faq">' + ''.join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in faqs) + '</div>'


def faq_schema(faqs):
    return {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs]}


ORG = {'@context': 'https://schema.org', '@type': 'Organization', 'name': BRAND, 'url': SITE,
       'logo': SITE + '/assets/favicon.svg', 'sameAs': [ETSY_SHOP] + [u for _, u in SOCIAL]}


# ---------------------------------------------------------------- matching sets
def build_sets():
    """For each colour family, the best-ranked quinceañera piece of each type that shares it."""
    sets, used = [], set()
    quince = [p for p in P if p['occasion'] == 'quinceanera-sweet-16']
    for c in ['pink', 'blue', 'champagne', 'red', 'rose-gold', 'purple', 'green', 'black', 'fuchsia', 'white']:
        pieces = []
        for t in ['save-the-dates', 'website-invitations', 'video-invitations', 'slideshows']:
            # prefer designs whose main color is this one, and never reuse a piece from another set
            cand = sorted([p for p in quince if p['type'] == t and c in p['colours'] and p['id'] not in used],
                          key=lambda p: (p['colours'][0] != c, len(p['colours']), rank(p)))
            if cand:
                pieces.append(cand[0])
                used.add(cand[0]['id'])
        if len(pieces) >= 3:
            sets.append({'colour': c, 'pieces': pieces})
    return sets


SETS = build_sets()


def set_html(s):
    c = COL[s['colour']]
    imgs = ''.join(f'<a href="@/templates/{p["slug"]}/" tabindex="-1" aria-hidden="true"><img loading="lazy" src="{p["img"]}" alt=""></a>' for p in s['pieces'][:3])
    rows = ''.join(f'<li><a href="@/templates/{p["slug"]}/">{e(p["type_name"].rstrip("s") if p["type_name"].endswith("s") else p["type_name"])}</a><span>{money(p["price"])}</span></li>' for p in s['pieces'])
    total = sum(p['price'] for p in s['pieces'])
    return (f'<article class="set" data-reveal><div class="set-imgs">{imgs}</div><h3><span class="dot" style="background:{c["hex"]}"></span>{e(c["label"])}</h3>'
            f'<ul>{rows}</ul><p class="muted" style="font-size:.92rem;margin-bottom:12px">{len(s["pieces"])} pieces, {money(total)} together</p>'
            f'<a class="textlink" href="@/colors/{s["colour"]}/">All {e(c["label"].lower())} designs</a></article>')


# ---------------------------------------------------------------- articles
def load_articles():
    arts = []
    d = os.path.join(ROOTDIR, 'content', 'journal')
    for fn in sorted(os.listdir(d)):
        if not fn.endswith('.md'):
            continue
        raw = open(os.path.join(d, fn)).read()
        m = re.match(r'---\n(.*?)\n---\n(.*)', raw, re.S)
        meta = {}
        for line in m.group(1).splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip()] = v.strip().strip('"')
        meta['body'] = m.group(2)
        meta['date'] = datetime.date.fromisoformat(meta['date'])
        if meta['date'] > TODAY:
            continue  # scheduled for later
        meta['lang'] = meta.get('lang', 'en')
        meta['tags'] = [t.strip() for t in meta.get('tags', '').split(',') if t.strip()]
        meta['path'] = ('es/blog/' if meta['lang'] == 'es' else 'journal/') + meta['slug'] + '/'
        arts.append(meta)
    arts.sort(key=lambda a: a['date'], reverse=True)
    return arts


def pick_products(tags, n=3, exclude=()):
    """Products matching all given tags (occasion/type/colour/theme slugs), best-ranked first."""
    def ok(p):
        for t in tags:
            if t in (p['occasion'], p['type']) or t in p['colours'] or t in p['themes']:
                continue
            return False
        return True
    res = [p for p in sorted(P, key=rank) if ok(p) and p['id'] not in exclude]
    return res[:n]


def render_article_body(md_text):
    # shortcode: [[products: tag tag | 3]]
    def sc(m):
        tags, _, n = m.group(1).partition('|')
        items = pick_products(tags.split(), int(n.strip() or 3))
        return '\n<div class="inline-products">' + ''.join(card(p, 'div') for p in items) + '</div>\n'
    md_text = re.sub(r'\[\[products:\s*([^\]]+)\]\]', sc, md_text)
    md_text = re.sub(r'\]\(@/', '](@/', md_text)
    h = markdown.markdown(md_text, extensions=['tables', 'toc', 'sane_lists'])
    h = h.replace('href="@/', 'href="@/')
    return h


# ---------------------------------------------------------------- pages
def home(articles):
    best = sorted([p for p in P if p['best']], key=lambda p: p['best'])[:12]
    sw = ''.join(f'<li><button class="swatch" type="button" data-colour="{c}" aria-pressed="false" style="--c:{COL[c]["hex"]}"><i></i>{e(COL[c]["label"])}</button></li>'
                 for c in ['pink', 'champagne', 'blue', 'red', 'rose-gold', 'purple', 'green', 'black'])
    # cinematic "venue screen": the best sellers play like a slideshow
    playlist = best[:6]
    slides = ''.join(f'<a class="slide{" is-on" if i == 0 else ""}" href="@/templates/{p["slug"]}/" data-name="{e(p["name"])}" data-price="{money(p["price"])}" data-type="{e(p["type_name"])}"'
                     f'{"" if i == 0 else " tabindex=-1"}><img src="{p["img_lg"]}" alt="{e(p["name"])}"{" fetchpriority=high" if i == 0 else " loading=lazy"}></a>'
                     for i, p in enumerate(playlist))
    bars = ''.join(f'<button type="button" class="bar{" is-on" if i == 0 else ""}" aria-label="Show design {i + 1}"><i></i></button>' for i in range(len(playlist)))
    # two endless rows of designs
    pool = sorted(P, key=rank)
    row1 = [p for p in pool if p['occasion'] == 'quinceanera-sweet-16'][:16]
    row2 = [p for p in pool if p['occasion'] != 'quinceanera-sweet-16'][:8] + [p for p in pool if p['occasion'] == 'quinceanera-sweet-16'][16:24]

    def mq(items, rev=False):
        cells = ''.join(f'<a class="mq-item" href="@/templates/{p["slug"]}/"><img loading="lazy" src="{p["img"]}" srcset="{p["img"]} 340w, {p["img_lg"]} 794w" sizes="280px" alt="{e(p["name"])}" width="340" height="270"></a>' for p in items)
        dup = cells.replace('class="mq-item"', 'class="mq-item" tabindex="-1" aria-hidden="true"')
        return f'<div class="mq-row{" mq-rev" if rev else ""}"><div class="mq-track">{cells}{dup}</div></div>'
    marquee = mq(row1) + mq(row2, True)
    ranked = ''.join(f'<li class="slide-card"><span class="rank" aria-hidden="true">{i + 1}</span>{card(p, "div", lazy=False)}</li>' for i, p in enumerate(best[:12]))
    occ_tiles = ''
    for o in OCC_ORDER:
        ps = sorted([p for p in P if p['occasion'] == o], key=rank)
        occ_tiles += (f'<a class="occ" data-reveal href="@/{o}/"><img loading="lazy" src="{ps[0]["img_lg"]}" alt=""><div><h3>{OCC_NAME[o]}</h3>'
                      f'<p>{OCCASION_COPY[o]["blurb"]}, {len(ps)} design{"s" if len(ps) != 1 else ""}</p></div></a>')
    revs = ''.join(review_html(r) for r in REVIEWS[:10])
    posts = ''.join(post_card(a) for a in [a for a in articles if a['lang'] == 'en'][:3])
    body = f'''
<section class="hero hero-cine"><div class="glow g1" aria-hidden="true"></div><div class="glow g2" aria-hidden="true"></div><div class="wrap">
<div class="hero-copy">
<h1>Invitations and slideshows for the day she turns <em>quince</em></h1>
<p class="lede">Editable in Canva, in English or Spanish. Choose her colors, add your photos and share it with the whole family the same day.</p>
<div class="ribbon" id="ribbon" data-features='{json.dumps(FEATURES)}'><span class="ribbon-label" id="ribbon-l">What are her party colors?</span>
<ul class="swatches" aria-labelledby="ribbon-l">{sw}</ul></div>
<div class="hero-ctas"><a class="btn btn-primary" href="@/quinceanera-sweet-16/">Shop quinceañera</a><a class="btn btn-ghost btn-ghost-light" href="@/shop/">Browse all {len(P)} templates</a></div>
<div class="trust"><span><span class="stars" aria-hidden="true">★★★★★</span> <b>{SHOP["rating"]}</b> from {SHOP["reviews"]} Etsy reviews</span><span><b>{SHOP["sales"]}+</b> orders</span><span><b>Star Seller</b> on Etsy</span></div>
</div>
<figure class="screen" id="screen" aria-roledescription="carousel" aria-label="Best sellers playing on a venue screen">
<div class="screen-frame"><div class="slides" id="slides" aria-live="off">{slides}</div>
<div class="screen-ui"><div class="bars" id="bars">{bars}</div>
<figcaption class="now"><span class="now-l" id="now-l">Now playing, best seller no. 1</span><a id="now-link" href="@/templates/{playlist[0]["slug"]}/">{e(playlist[0]["name"])}</a><span class="now-meta" id="now-meta">{e(playlist[0]["type_name"])}, {money(playlist[0]["price"])}</span></figcaption>
<button class="screen-pause" id="screen-pause" type="button" aria-label="Pause slideshow"><svg viewBox="0 0 24 24" aria-hidden="true"><path class="i-pause" d="M8 5h3v14H8zM13 5h3v14h-3z"/><path class="i-play" d="M8 5l11 7-11 7z"/></svg></button></div></div>
<div class="stand" aria-hidden="true"></div>
</figure>
</div></section>

<section class="marquee" aria-label="More designs">{marquee}</section>

<section class="sec" aria-labelledby="best-h"><div class="wrap wrap-wide">
<div class="sec-head" data-reveal><div><h2 id="best-h">Best sellers</h2><p class="muted">Ranked by what families ordered most this year.</p></div>
<div class="car-nav"><button class="car-btn" type="button" data-car-prev aria-label="Previous best sellers"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg></button><button class="car-btn" type="button" data-car-next aria-label="Next best sellers"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg></button></div></div>
</div>
<ol class="ranked car-track" data-carousel tabindex="0" aria-label="Best sellers">{ranked}</ol>
<div class="wrap wrap-wide"><p style="margin-top:22px"><a class="textlink" href="@/shop/">See every template</a></p></div>
</section>

<section class="sec band" aria-labelledby="occ-h"><div class="wrap">
<div class="sec-head" data-reveal><h2 id="occ-h">Shop by celebration</h2></div>
<div class="occasions">{occ_tiles}</div>
</div></section>

<section class="sec" aria-labelledby="sets-h"><div class="wrap">
<div class="sec-head" data-reveal><div><h2 id="sets-h">Keep one palette from save the date to slideshow</h2><p class="muted">Pieces that share the same colors, so every message your guests get looks like it belongs together.</p></div><a class="textlink" href="@/matching-sets/">All matching sets</a></div>
<div class="sets">{''.join(set_html(s) for s in SETS[:3])}</div>
</div></section>

<section class="sec dark" aria-labelledby="how-h"><div class="wrap">
<div class="sec-head" data-reveal><h2 id="how-h" style="color:var(--pearl)">How it works</h2><a class="textlink" href="@/how-it-works/">More details and questions</a></div>
{steps_html()}
</div></section>

<section class="sec" aria-labelledby="plan-h"><div class="wrap planner-teaser">
<div><h2 id="plan-h">When should each piece go out?</h2><p class="lede">Enter the party date. We work backwards to when to send the save the date and the invitation, when the RSVP closes and when to finish the slideshow, and you can add every step to your calendar.</p></div>
<form class="datebox" id="planner-teaser">
<div class="row"><div><label for="t-event">Celebration</label><select id="t-event"><option value="quince">Quinceañera</option><option value="wedding">Wedding</option><option value="birthday">Birthday</option><option value="mitzvah">Bat or bar mitzvah</option><option value="graduation">Graduation</option></select></div>
<div><label for="t-date">Party date</label><input id="t-date" type="date" required></div></div>
<button class="btn btn-primary" type="submit">{ICON['cal']}Build my timeline</button>
</form></div></section>

<section class="sec band" aria-labelledby="rev-h"><div class="wrap">
<div class="sec-head" data-reveal><div><h2 id="rev-h">From families who celebrated with us</h2><p class="muted">Recent reviews from our Etsy shop.</p></div><a class="textlink" href="{ETSY_SHOP}#reviews" rel="noopener">Read all reviews on Etsy</a></div>
<div class="rev-rail"><div class="rev-track">{revs}{revs.replace('class="review"', 'class="review" aria-hidden="true"')}</div></div>
</div></section>

{signup_box()}
<section class="sec" aria-labelledby="j-h"><div class="wrap">
<div class="sec-head" data-reveal><div><h2 id="j-h">Planning ideas from the journal</h2><p class="muted">Timelines, color palettes and step-by-step Canva guides.</p></div><a class="textlink" href="@/journal/">All articles</a></div>
<div class="posts">{posts}</div>
</div></section>

<section class="sec band" aria-labelledby="faq-h"><div class="wrap">
<h2 id="faq-h">Questions before you order</h2>
{faq_html(GENERAL_FAQ)}
</div></section>'''
    website = {'@context': 'https://schema.org', '@type': 'WebSite', 'name': BRAND, 'url': SITE,
               'potentialAction': {'@type': 'SearchAction', 'target': SITE + '/shop/?q={search_term_string}', 'query-input': 'required name=search_term_string'}}
    best_list = {'@context': 'https://schema.org', '@type': 'ItemList', 'name': 'Best sellers', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'url': f'{SITE}/templates/{p["slug"]}/'} for i, p in enumerate(best)]}
    page('index.html', 'Quinceañera Invitations & Slideshows | Digipod Studio',
         'Editable quinceañera, sweet 16, wedding and birthday templates: slideshows, video invitations, save the dates and RSVP websites. Personalize in Canva, share the same day.',
         body, schema=[ORG, website, best_list, faq_schema(GENERAL_FAQ)], og_image=best[0]['img_lg'], body_page='home', priority='1.0',
         alternates={'en': SITE + '/', 'es': SITE + '/es/', 'x-default': SITE + '/'})


SAVE_SHARE = {
    'website-invitations': 'Publish your website and share the link with your guests.',
    'video-invitations': 'Download your finished video and share it with your guests.',
    'save-the-dates': 'Download your finished video and share it with your guests.',
    'save-the-date-teasers': 'Download your finished video and share it with your guests.',
    'slideshows': 'Download your finished video and play it at the party or share it with your guests.',
    'screen-displays-banners': 'Download your finished video and play it on the venue screen.',
    'default': 'Download your finished design and share or print it.',
}
HOW_STEPS = {
    'en': [('Purchase', 'cart', 'Choose your favorite design and complete your purchase.'),
           ('Download', 'pdf', 'Download the PDF file sent to your email.'),
           ('Personalize', 'canva', 'Click the Canva link in the PDF and customize your invitation with your details, photos, and more.'),
           ('Save & share', 'share', '<strong>Video invitation:</strong> download your finished video and share it with your guests.<br><strong>Website invitation:</strong> publish your website and share the link with your guests.')],
    'es': [('Compra', 'cart', 'Elige tu diseño favorito y completa tu compra.'),
           ('Descarga', 'pdf', 'Descarga el archivo PDF que llega a tu correo.'),
           ('Personaliza', 'canva', 'Haz clic en el enlace de Canva del PDF y personaliza tu invitación con tus datos, fotos y más.'),
           ('Guarda y comparte', 'share', '<strong>Invitación en video:</strong> descarga tu video terminado y compártelo con tus invitados.<br><strong>Invitación web:</strong> publica tu página y comparte el enlace con tus invitados.')],
}
STEP_ICON = {
    'cart': '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M6 9h6l4 22h22l4-15H15"/><circle cx="19" cy="38" r="3"/><circle cx="35" cy="38" r="3"/><path d="M27 25s-5-3-5-6.2c0-1.8 1.4-3 3-3 1 0 1.6.5 2 1.2.4-.7 1-1.2 2-1.2 1.6 0 3 1.2 3 3 0 3.2-5 6.2-5 6.2z" class="fill"/></svg>',
    'pdf': '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M7 19l17 12 17-12v20H7z"/><path d="M7 19l17-11 17 11"/><rect x="13" y="12" width="22" height="12" rx="2" class="paper"/><text x="24" y="21" text-anchor="middle" font-size="7" font-weight="700" font-family="Instrument Sans, sans-serif" class="txt">PDF</text></svg>',
    'canva': '<svg viewBox="0 0 48 48" aria-hidden="true"><rect x="6" y="9" width="36" height="24" rx="3"/><path d="M3 37h42"/><text x="24" y="25" text-anchor="middle" font-size="9" font-style="italic" font-family="Bodoni Moda, Georgia, serif" class="txt">Canva</text><path d="M33 27l7 7-3 1 2 4-2 1-2-4-2 2z" class="fill"/></svg>',
    'share': '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M17 20h-6v20h26V20h-6"/><path d="M24 30V6M17 13l7-7 7 7"/></svg>',
}


def steps_html(lang='en', light=False):
    items = ''.join(f'<li data-reveal><div class="step-ico">{STEP_ICON[ic]}</div><h3>{e(t)}</h3><p>{d}</p></li>' for t, ic, d in HOW_STEPS[lang])
    return f'<ol class="steps steps4{" steps-light" if light else ""}">{items}</ol>'


def review_html(r):
    p = BYID.get(r['listing'])
    on = f' on <a href="@/templates/{p["slug"]}/">{e(p["name"])}</a>' if p else ''
    name = r['name'] if r['name'].lower() not in ('family', 'etsy buyer') else 'Etsy buyer'
    name = name[:1].upper() + name[1:]
    return (f'<figure class="review"><span class="stars" aria-label="{r["stars"]} out of 5 stars">{"★" * r["stars"]}{"☆" * (5 - r["stars"])}</span>'
            f'<blockquote>{e(r["text"])}</blockquote><figcaption>{e(name)}, {e(r["date"])}{on}</figcaption></figure>')


ART_IMG = {}
BY_ID_ALL = {p['id']: p for p in P}


def assign_article_images(articles):
    """Give every article its own cover: the best match for all its tags not already used by a newer article."""
    used = set()
    for a in sorted(articles, key=lambda x: x['date'], reverse=True):
        if a.get('image'):
            ART_IMG[a['slug']] = a['image']
            continue
        pick = None
        for tags in (a['tags'], a['tags'][:1], []):
            for p in pick_products(tags, 60):
                if p['id'] not in used:
                    pick = p
                    break
            if pick:
                break
        pick = pick or P[0]
        # a colour with a chosen lead design (data/colour_features.json) always shows that design
        for c in pick.get('colours') or []:
            fid = FEATURES.get(c)
            if fid and fid != pick['id'] and fid not in used and fid in BY_ID_ALL:
                pick = BY_ID_ALL[fid]
                break
        used.add(pick['id'])
        ART_IMG[a['slug']] = pick['img_lg']


def post_card(a):
    img = ART_IMG.get(a['slug']) or a.get('image') or (pick_products(a['tags'][:1], 1) or [P[0]])[0]['img_lg']
    return (f'<article class="post" data-reveal><a class="cover" href="@/{a["path"]}" tabindex="-1" aria-hidden="true"><img loading="lazy" src="{img}" alt=""></a>'
            f'<h3><a href="@/{a["path"]}">{e(a["title"])}</a></h3><p>{e(a["description"])}</p></article>')


def listing_page(path, title, desc, h1, intro, items, crumbs_items, chips='', extra='', schema_extra=None, priority='0.8'):
    nav, bc = crumbs(crumbs_items)
    grid = ''.join(card(p) for p in items)
    itemlist = {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': h1, 'description': desc, 'url': SITE + '/' + path.replace('index.html', ''),
                'mainEntity': {'@type': 'ItemList', 'numberOfItems': len(items), 'itemListElement': [
                    {'@type': 'ListItem', 'position': i + 1, 'url': f'{SITE}/templates/{p["slug"]}/'} for i, p in enumerate(items[:30])]}}
    body = f'''{nav}
<section class="page-head wrap"><h1>{e(h1)}</h1><p class="lede">{e(intro)}</p>{chips}</section>
<section class="wrap" aria-label="Templates"><p class="muted" style="margin-bottom:22px">{len(items)} designs, best sellers first</p>
<ul class="grid" style="list-style:none;margin:0;padding:0">{grid}</ul></section>
{extra}'''
    page(path, title, desc, body, schema=[bc, itemlist] + (schema_extra or []), og_image=items[0]['img_lg'], priority=priority)


def occasion_pages():
    for o in OCC_ORDER:
        c = OCCASION_COPY[o]
        items = sorted([p for p in P if p['occasion'] == o], key=rank)
        types = [t for t in TYPE_ORDER if any(p['type'] == t for p in items)]
        tn = {p['type']: p['type_name'] for p in items}
        chips = '<ul class="chips">' + ''.join(f'<li><a href="@/{o}/{t}/">{e(tn[t])} ({sum(1 for p in items if p["type"] == t)})</a></li>' for t in types) + '</ul>'
        faqs = [f for t in types[:3] for f in TYPE_COPY[t]['faq'][:1]] + GENERAL_FAQ[:2]
        extra = f'<section class="sec"><div class="wrap"><h2>Good to know</h2>{faq_html(faqs)}</div></section>'
        listing_page(f'{o}/index.html', c['title'] + ' | Digipod Studio', c['desc'], c['h1'], c['intro'], items,
                     [('', 'Home'), (None, OCC_NAME[o])], chips, extra, [faq_schema(faqs)], priority='0.9')
        for t in types:
            sub = [p for p in items if p['type'] == t]
            occ_short = items[0]['occasion_short']
            h1 = f'{occ_short} {tn[t].lower()}' if o != 'party-extras' else tn[t]
            h1 = h1[0].upper() + h1[1:]
            tc = TYPE_COPY[t]
            intro = f'{tc["what"]} {tc["use"]}'
            chips2 = '<ul class="chips">' + ''.join(f'<li><a href="@/{o}/{t2}/"{" aria-current=page" if t2 == t else ""}>{e(tn[t2])}</a></li>' for t2 in types) + '</ul>'
            extra = f'<section class="sec"><div class="wrap"><h2>Questions about {e(tn[t].lower())}</h2>{faq_html(tc["faq"])}</div></section>'
            listing_page(f'{o}/{t}/index.html', f'{h1} Templates, Editable in Canva | Digipod Studio',
                         f'{len(sub)} editable {h1.lower()} templates. {tc["what"]}'[:158], h1 + ' templates', intro, sub,
                         [('', 'Home'), (f'{o}/', OCC_NAME[o]), (None, tn[t])], chips2, extra, [faq_schema(tc['faq'])])


def colour_pages():
    allc = Counter(c for p in P for c in p['colours'])
    for c, n in allc.items():
        if n < 4:
            continue
        col = COL[c]
        items = sorted([p for p in P if c in p['colours']], key=rank)
        lab = col['label'].lower()
        chips = '<ul class="chips">' + ''.join(f'<li><a href="@/colors/{c2}/"{" aria-current=page" if c2 == c else ""}><span class="dot" style="background:{COL[c2]["hex"]}"></span>{e(COL[c2]["label"])}</a></li>'
                                               for c2, n2 in allc.most_common() if n2 >= 4) + '</ul>'
        listing_page(f'colors/{c}/index.html', f'{col["label"]} Quinceañera, Wedding & Party Templates | Digipod Studio',
                     f'{len(items)} {lab} invitations, save the dates, slideshows and RSVP websites. Editable in Canva so every piece matches your party colors.',
                     f'{col["label"]} templates', f'Every design in {lab}, across invitations, save the dates, slideshows and RSVP websites, so you can match one palette from the first announcement to the last song.',
                     items, [('', 'Home'), ('shop/', 'Shop'), (None, col['label'])], chips)


def matching_sets_page():
    nav, bc = crumbs([('', 'Home'), (None, 'Matching sets')])
    body = f'''{nav}<section class="page-head wrap"><h1>Matching sets by color</h1>
<p class="lede">Quinceañera pieces grouped by palette: a save the date, a website invitation, a video invitation and a slideshow that share the same colors. Mix and match within a color to keep everything consistent.</p></section>
<section class="wrap"><div class="sets">{''.join(set_html(s) for s in SETS)}</div></section>'''
    page('matching-sets/index.html', 'Matching Quinceañera Invitation Sets by Color | Digipod Studio',
         'Save the dates, website invitations, video invitations and slideshows grouped by color, so your quinceañera pieces match.', body, schema=[bc])


def shop_page():
    nav, bc = crumbs([('', 'Home'), (None, 'Shop all templates')])
    items = sorted(P, key=rank)

    def group(name, legend, opts):
        return f'<fieldset><legend>{legend}</legend>' + ''.join(
            f'<label class="opt"><input type="checkbox" name="{name}" value="{v}">{lab}<span class="n">{n}</span></label>' for v, lab, n in opts) + '</fieldset>'
    occ = [(o, OCC_NAME[o], sum(1 for p in P if p['occasion'] == o)) for o in OCC_ORDER]
    tcount = Counter(p['type'] for p in P)
    tname = {p['type']: p['type_name'] for p in P}
    typ = [(t, tname[t], tcount[t]) for t in TYPE_ORDER if t in tcount]
    cc = Counter(c for p in P for c in p['colours'])
    col = [(c, f'<span class="dot" style="background:{COL[c]["hex"]}"></span>{COL[c]["label"]}', n) for c, n in cc.most_common()]
    th = Counter(t for p in P for t in p['themes'])
    thm = [(t, THM[t], n) for t, n in th.most_common()]
    pr = [('0-10', 'Under $10', sum(1 for p in P if p['price'] <= 10)), ('10.01-20', '$10 to $20', sum(1 for p in P if 10 < p['price'] <= 20)),
          ('20.01-30', '$20 to $30', sum(1 for p in P if 20 < p['price'] <= 30)), ('30.01-9999', 'Over $30', sum(1 for p in P if p['price'] > 30))]
    body = f'''{nav}<section class="page-head wrap" style="padding-bottom:18px"><h1>All templates</h1></section>
<section class="wrap shop">
<form class="filters" id="filters" aria-label="Filters" onsubmit="return false">
{group('occasion', 'Celebration', occ)}{group('type', 'Type', typ)}{group('colour', 'Color', col)}{group('theme', 'Style', thm)}{group('price', 'Price', pr)}
<button class="btn btn-ghost" type="button" id="clear">Clear filters</button>
</form>
<div>
<div class="shop-bar"><label class="sr" for="q">Search</label><input id="q" type="search" placeholder="Search by name, color or style">
<button class="btn btn-ghost filters-toggle" type="button" aria-controls="filters" aria-expanded="false">Filters</button>
<span class="muted" id="shown" aria-live="polite"></span>
<label class="sr" for="sort">Sort</label><select id="sort"><option value="best">Best sellers</option><option value="new">Newest</option><option value="price-asc">Price, low to high</option><option value="price-desc">Price, high to low</option></select></div>
<ul class="grid" id="shop-grid" style="list-style:none;margin:0;padding:0">{''.join(card(p, extra_attrs='shop') for p in items)}</ul>
<div class="empty" id="shop-empty" hidden><p><strong>No templates match those filters.</strong></p><p>Remove a filter, or try a broader color like pink.</p></div>
</div></section>'''
    page('shop/index.html', 'Shop All Editable Party Templates | Digipod Studio',
         f'Browse {len(P)} editable Canva templates for quinceañeras, sweet 16s, weddings, birthdays and mitzvahs. Filter by color, style and price.',
         body, schema=[bc], body_page='shop', priority='0.9')


def product_pages():
    for p in P:
        tc = TYPE_COPY[p['type']]
        o = p['occasion']
        nav, bc = crumbs([('', 'Home'), (f'{o}/', p['occasion_name']), (f'{o}/{p["type"]}/', p['type_name']), (None, p['name'])])
        facts = ['Editable in Canva', 'Instant digital download', 'Change every word, in English or Spanish'] + p['features']
        if p['slides']:
            facts.append(f'{p["slides"]} slides to start from')
        facts = list(dict.fromkeys(facts))[:8]
        facts_html = ''.join(f'<li>{ICON["check"]}<span>{e(f)}</span></li>' for f in facts)
        cols = ''.join(f'<li><a href="@/colors/{c}/"><span class="dot" style="background:{COL[c]["hex"]}"></span>{e(COL[c]["label"])}</a></li>' for c in p['colours'])
        # Etsy's photo description, minus its generic first sentence, as a note on what the preview shows
        sents = re.split(r'(?<=\.)\s+', p['alt']) if p['alt'] else []
        if sents and re.match(r'^(a|an)\s+(digital|animated|editable|quincea|rose|pink)', sents[0], re.I) and len(sents) > 1:
            sents = sents[1:]
        desc_alt = ' '.join(sents) if sents and not p['alt'].lower().startswith(p['name'].lower()[:20]) else ''
        if desc_alt:
            desc_alt = 'In the preview: ' + desc_alt[0].lower() + desc_alt[1:]
        look = ''
        if p['colours'] and o == 'quinceanera-sweet-16':
            same = []
            for t in ['save-the-dates', 'website-invitations', 'video-invitations', 'slideshows']:
                if t == p['type']:
                    continue
                cand = sorted([q for q in P if q['occasion'] == o and q['type'] == t and set(q['colours']) & set(p['colours'][:1])], key=rank)
                if cand:
                    same.append(cand[0])
            if same:
                look = (f'<section class="sec band"><div class="wrap"><div class="sec-head"><div><h2>Match it in {e(COL[p["colours"][0]]["label"].lower())}</h2>'
                        f'<p class="muted">Pieces in the same colors for the rest of the celebration.</p></div></div>'
                        f'<ul class="grid" style="list-style:none;margin:0;padding:0">{"".join(card(q) for q in same[:3])}</ul></div></section>')
        rel = [q for q in sorted(P, key=rank) if q['type'] == p['type'] and q['occasion'] == o and q['id'] != p['id']][:4]
        rel_html = (f'<section class="sec"><div class="wrap"><div class="sec-head"><h2>More {e(p["type_name"].lower())}</h2>'
                    f'<a class="textlink" href="@/{o}/{p["type"]}/">See all</a></div><ul class="grid" style="list-style:none;margin:0;padding:0">'
                    f'{"".join(card(q) for q in rel)}</ul></div></section>') if rel else ''
        faqs = tc['faq'] + GENERAL_FAQ[:1]
        video = ''
        if p.get('video'):
            video = f'<iframe src="https://www.youtube-nocookie.com/embed/{p["video"]}" title="{e(p["name"])} preview" loading="lazy" allowfullscreen></iframe>'
        best_line = f'<p class="note"><strong style="color:var(--rosa)">Best seller no. {p["best"]}</strong></p>' if p['best'] and p['best'] <= 8 else ''
        body = f'''{nav}
<div class="wrap pdp" style="padding-top:22px">
<div class="pdp-media"><div class="main"><img src="{p["img_lg"]}" alt="{e(p["alt"] or p["name"])}" width="794" height="630" fetchpriority="high"></div>{video}</div>
<div class="pdp-body">
<h1>{e(p["name"])}</h1>{best_line}
<p class="price-lg">{money(p["price"])}</p>
<p class="note">Digital template. Complete your purchase on Etsy and the PDF with your Canva link is sent to your email.</p>
<div class="buy"><a class="btn btn-primary" href="{p["url"]}" rel="noopener">{ICON["bag"]}Buy on Etsy</a>
<button class="fav" type="button" data-id="{p["id"]}" aria-pressed="false">{ICON["heart"]}<span>Save to party list</span></button></div>
<ul class="facts">{facts_html}</ul>
{f'<ul class="colors-line" aria-label="Colors">{cols}</ul>' if cols else ''}
<h2>About this design</h2>
<p>{e(tc["what"])}</p>
{f'<p>{e(desc_alt)}</p>' if desc_alt else ''}
<p>{e(tc["use"])}</p>
<h2>How it works</h2>
<ol><li><strong>Purchase.</strong> Complete your purchase on Etsy.</li><li><strong>Download.</strong> Download the PDF file sent to your email.</li><li><strong>Personalize.</strong> Click the Canva link in the PDF and add your details, photos and more.</li><li><strong>Save &amp; share.</strong> {SAVE_SHARE.get(p['type'], SAVE_SHARE['default'])}</li></ol>
<h2>Questions</h2>{faq_html(faqs)}
</div></div>
<div class="sticky-buy"><span><strong>{money(p["price"])}</strong></span><a class="btn btn-primary" href="{p["url"]}" rel="noopener">Buy on Etsy</a></div>
{look}{rel_html}'''
        schema = {'@context': 'https://schema.org', '@type': 'Product', 'name': p['name'], 'image': [p['img_lg']], 'sku': p['no'],
                  'description': f'{tc["what"]} {tc["use"]}', 'brand': {'@type': 'Brand', 'name': BRAND},
                  'category': f'{p["occasion_name"]} > {p["type_name"]}',
                  'offers': {'@type': 'Offer', 'price': f'{p["price"]:.2f}', 'priceCurrency': 'USD', 'availability': 'https://schema.org/InStock',
                             'url': p['url'], 'seller': {'@type': 'Organization', 'name': BRAND},
                             'shippingDetails': {'@type': 'OfferShippingDetails', 'shippingRate': {'@type': 'MonetaryAmount', 'value': '0', 'currency': 'USD'},
                                                 'shippingDestination': {'@type': 'DefinedRegion', 'addressCountry': 'US'},
                                                 'deliveryTime': {'@type': 'ShippingDeliveryTime', 'handlingTime': {'@type': 'QuantitativeValue', 'minValue': 0, 'maxValue': 0, 'unitCode': 'DAY'},
                                                                  'transitTime': {'@type': 'QuantitativeValue', 'minValue': 0, 'maxValue': 0, 'unitCode': 'DAY'}}}}}
        title = f'{p["name"]} | Editable Canva Template'
        if len(title) > 68:
            title = p['name'][:66].rsplit(' ', 1)[0]
        desc = f'{p["name"]}, {money(p["price"])}. {tc["what"]}'
        desc = desc[:157].rsplit(' ', 1)[0] + '…' if len(desc) > 158 else desc
        page(f'templates/{p["slug"]}/index.html', title, desc, body, schema=[bc, schema, faq_schema(faqs)], og_image=p['img_lg'],
             body_page='product" class="has-sticky', og_type='product', priority='0.7')


def journal_pages(articles):
    for lang in ['en', 'es']:
        arts = [a for a in articles if a['lang'] == lang]
        es = lang == 'es'
        base = 'es/blog/' if es else 'journal/'
        nav, bc = crumbs([('es/' if es else '', 'Inicio' if es else 'Home'), (None, 'Blog' if es else 'Journal')])
        h1 = 'Ideas para tu celebración' if es else 'The journal'
        intro = ('Cronogramas, paletas de colores y guías paso a paso para quinceañeras, bodas y cumpleaños.' if es
                 else 'Planning timelines, color palettes, traditions and step-by-step Canva guides for quinceañeras, weddings and birthdays. New articles every day.')
        body = f'''{nav}<section class="page-head wrap"><h1>{h1}</h1><p class="lede">{intro}</p></section>
<section class="wrap"><div class="posts">{''.join(post_card(a) for a in arts)}</div></section>'''
        page(base + 'index.html', ('Blog: ideas para quinceañeras y fiestas' if es else 'Journal: Quinceañera, Wedding & Party Planning Ideas') + ' | Digipod Studio',
             intro, body, schema=[bc], lang=lang, priority='0.8')
        for a in arts:
            nav, bc = crumbs([('es/' if es else '', 'Inicio' if es else 'Home'), (base, 'Blog' if es else 'Journal'), (None, a['title'])])
            content = render_article_body(a['body'])
            heads = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', content)
            toc = ''
            if len(heads) >= 3:
                toc = (f'<nav class="toc" aria-label="Contents"><strong>{"En este artículo" if es else "In this article"}</strong><ol>'
                       + ''.join(f'<li><a href="#{i}">{t}</a></li>' for i, t in heads) + '</ol></nav>')
            img = ART_IMG.get(a['slug']) or a.get('image') or (pick_products(a['tags'][:2], 1) or [P[0]])[0]['img_lg']
            more = pick_products(a['tags'][:1], 4)
            faqs = []
            fm = re.search(r'<h2[^>]*>(?:Frequently asked questions|Preguntas frecuentes)</h2>(.*)$', content, re.S)
            if fm:
                for q, ans in re.findall(r'<h3[^>]*>(.*?)</h3>\s*<p>(.*?)</p>', fm.group(1), re.S):
                    faqs.append((re.sub('<[^>]+>', '', q), re.sub('<[^>]+>', '', ans)))
            alt = None
            if a.get('translation'):
                other = next((x for x in articles if x['slug'] == a['translation']), None)
                if other:
                    alt = {a['lang']: SITE + '/' + a['path'], other['lang']: SITE + '/' + other['path']}
            dt = a['date'].strftime('%d de %B de %Y') if es else a['date'].strftime('%B %-d, %Y')
            body = f'''{nav}<article class="wrap"><div class="article">
<header><h1>{e(a["title"])}</h1><p class="byline">{'Por' if es else 'By'} Digipod Studio, <time datetime="{a["date"].isoformat()}">{dt}</time></p></header>
<div class="hero-img"><img src="{img}" alt="" fetchpriority="high"></div>
{toc}<div class="prose">{content}</div>
</div></article>
{signup_box(es)}
<section class="sec band"><div class="wrap"><div class="sec-head"><h2>{'Plantillas para tu fiesta' if es else 'Templates for your celebration'}</h2><a class="textlink" href="@/shop/">{'Ver todas' if es else 'See all templates'}</a></div>
<ul class="grid" style="list-style:none;margin:0;padding:0">{''.join(card(p) for p in more)}</ul></div></section>'''
            schema = [bc, {'@context': 'https://schema.org', '@type': 'BlogPosting', 'headline': a['title'], 'description': a['description'],
                           'datePublished': a['date'].isoformat(), 'dateModified': a['date'].isoformat(), 'inLanguage': 'es-US' if es else 'en-US',
                           'image': [img], 'author': {'@type': 'Organization', 'name': BRAND, 'url': SITE},
                           'publisher': {'@type': 'Organization', 'name': BRAND, 'logo': {'@type': 'ImageObject', 'url': SITE + '/assets/favicon.svg'}},
                           'mainEntityOfPage': SITE + '/' + a['path']}]
            if faqs:
                schema.append(faq_schema(faqs))
            page(a['path'] + 'index.html', a['title'] + ' | Digipod Studio', a['description'], body, schema=schema, og_image=img, lang=lang,
                 alternates=alt, og_type='article', priority='0.7')


def spanish_home(articles):
    best = sorted([p for p in P if p['best']], key=lambda p: p['best'])[:8]
    ranked = ''.join(f'<li><span class="rank" aria-hidden="true">{i + 1}</span>{card(p, "div")}</li>' for i, p in enumerate(best))
    posts = ''.join(post_card(a) for a in [a for a in articles if a['lang'] == 'es'][:3])
    cats = [('quinceanera-sweet-16/slideshows/', 'Slideshows y videos de fotos para quinceañera'), ('quinceanera-sweet-16/video-invitations/', 'Invitaciones en video para XV años'),
            ('quinceanera-sweet-16/save-the-dates/', 'Save the date para quinceañera'), ('quinceanera-sweet-16/website-invitations/', 'Invitaciones web con confirmación (RSVP)'),
            ('wedding-anniversary/', 'Bodas y aniversarios'), ('birthday-baby/', 'Cumpleaños y primer añito')]
    chips = '<ul class="chips">' + ''.join(f'<li><a href="@/{h}">{t}</a></li>' for h, t in cats) + '</ul>'
    faqs = [('¿Cómo recibo mi plantilla?', 'Completa tu compra en Etsy y descarga el archivo PDF que llega a tu correo. Haz clic en el enlace de Canva del PDF para abrir tu plantilla y personalizarla.'),
            ('¿Puedo escribirla en español?', 'Sí. Puedes cambiar cada palabra, así que puedes usar español, inglés o los dos. Varias plantillas ya vienen bilingües.'),
            ('¿Puedo editar desde mi celular?', 'Sí. Canva funciona en el navegador y en la app gratuita de Canva para iPhone y Android.'),
            ('¿Me envían algo por correo?', 'No. Son plantillas digitales, así que no hay envío ni espera.')]
    body = f'''<section class="hero"><div class="wrap" style="grid-template-columns:1fr">
<div><h1 style="max-width:13em">Invitaciones y videos para sus <em>XV años</em>, editables en Canva</h1>
<p class="lede">Slideshows, invitaciones en video, save the dates e invitaciones web con confirmación de asistencia. Cambia nombres, fotos y música tú misma y compártelo con toda la familia el mismo día.</p>
<div class="hero-ctas"><a class="btn btn-primary" href="@/quinceanera-sweet-16/">Ver plantillas de quinceañera</a><a class="btn btn-ghost" href="@/planner/">Planifica tus fechas</a></div>
<div class="trust"><span><span class="stars" aria-hidden="true">★★★★★</span> <b>{SHOP["rating"]}</b> en {SHOP["reviews"]} reseñas de Etsy</span><span><b>{SHOP["sales"]}+</b> pedidos</span><span><b>Star Seller</b> en Etsy</span></div>
{chips}</div></div></section>
<section class="sec" style="padding-top:20px"><div class="wrap"><div class="sec-head"><div><h2>Las más vendidas</h2><p class="muted">Los diseños que más eligen las familias.</p></div><a class="textlink" href="@/shop/">Ver todas</a></div><ol class="ranked">{ranked}</ol></div></section>
<section class="sec dark"><div class="wrap"><h2 style="color:var(--pearl)">Cómo funciona</h2>{steps_html('es')}</div></section>
{f'<section class="sec"><div class="wrap"><div class="sec-head"><h2>Del blog</h2><a class="textlink" href="@/es/blog/">Todos los artículos</a></div><div class="posts">{posts}</div></div></section>' if posts else ''}
{signup_box(True)}
<section class="sec band"><div class="wrap"><h2>Preguntas frecuentes</h2>{faq_html(faqs)}</div></section>'''
    page('es/index.html', 'Invitaciones de Quinceañera y Slideshows Editables en Canva | Digipod Studio',
         'Plantillas editables para quinceañera y XV años: slideshows, invitaciones en video, save the dates e invitaciones web con RSVP. Personaliza en Canva.',
         body, schema=[ORG, faq_schema(faqs)], lang='es', og_image=best[0]['img_lg'], priority='0.9',
         alternates={'en': SITE + '/', 'es': SITE + '/es/', 'x-default': SITE + '/'})


def planner_page():
    nav, bc = crumbs([('', 'Home'), (None, 'Party planner')])
    body = f'''{nav}<section class="page-head wrap"><h1>Party planner</h1>
<p class="lede">Tell us the celebration and the date. You get a timeline of when to send each piece, when the RSVP should close and when to finish the slideshow, with a link to the right templates at every step.</p></section>
<section class="wrap"><div style="max-width:820px"><div class="datebox" id="planner">
<div class="row"><div><label for="p-event">Celebration</label><select id="p-event"><option value="quince">Quinceañera or sweet 16</option><option value="wedding">Wedding</option><option value="birthday">Birthday or first birthday</option><option value="mitzvah">Bat or bar mitzvah</option><option value="graduation">Graduation</option></select></div>
<div><label for="p-date">Party date</label><input id="p-date" type="date"></div></div>
<div id="p-out" aria-live="polite"></div>
<a class="btn btn-primary" id="p-ics" href="#" download="digipod-party-timeline.ics" hidden>{ICON['cal']}Add all dates to my calendar</a>
</div>
<p class="muted" style="margin-top:18px;font-size:.92rem">Timings are common guidelines. Adjust them for your venue, your family and how far your guests travel.</p></div></section>''' + signup_box()
    app = {'@context': 'https://schema.org', '@type': 'WebApplication', 'name': 'Digipod Studio party planner', 'applicationCategory': 'LifestyleApplication',
           'operatingSystem': 'Any', 'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'}, 'url': SITE + '/planner/'}
    page('planner/index.html', 'Quinceañera & Party Planning Timeline Calculator | Digipod Studio',
         'Enter your party date to see when to send the save the date and invitations, when to close RSVPs and when to finish the slideshow. Add it all to your calendar.',
         body, schema=[bc, app], body_page='planner', priority='0.8')


def simple_pages():
    nav, bc = crumbs([('', 'Home'), (None, 'Your party list')])
    page('party-list/index.html', 'Your party list | Digipod Studio', 'Templates you saved for your celebration.',
         f'''{nav}<section class="page-head wrap"><h1 id="party-title">Your party list</h1><p class="lede" id="party-sum">Templates you save appear here, on this device.</p>
<div class="share-row" id="party-share" hidden><button class="btn btn-primary" id="party-copy" type="button">Share this list</button><button class="btn btn-ghost" id="party-keep" type="button" hidden>Save these to my list</button></div></section>
<section class="wrap" id="party"></section>''', body_page='party-list', noindex=True)

    nav, bc = crumbs([('', 'Home'), (None, 'How it works')])
    howto = {'@context': 'https://schema.org', '@type': 'HowTo', 'name': 'How to order and personalize a Digipod Studio template',
             'step': [{'@type': 'HowToStep', 'position': i + 1, 'name': t, 'text': re.sub('<[^>]+>', ' ', d)} for i, (t, ic, d) in enumerate(HOW_STEPS['en'])]}
    page('how-it-works/index.html', 'How It Works: Purchase, Download, Personalize, Share | Digipod Studio',
         'Purchase your design, download the PDF sent to your email, personalize it in Canva from the link inside, then save and share your video or website invitation.',
         f'{nav}<section class="page-head wrap"><h1>How it works</h1><p class="lede">Four steps from choosing a design to sharing it with your guests.</p></section>'
         f'<section class="wrap">{steps_html("en", True)}</section>'
         f'<section class="sec"><div class="wrap"><h2>Questions</h2>{faq_html(GENERAL_FAQ)}</div></section>', schema=[bc, howto, faq_schema(GENERAL_FAQ)])

    nav, bc = crumbs([('', 'Home'), (None, 'About')])
    page('about/index.html', 'About Digipod Studio', 'Digipod Studio designs editable Canva templates for quinceañeras, weddings, birthdays and mitzvahs, sold on Etsy.',
         f'''{nav}<section class="page-head wrap"><h1>About Digipod Studio</h1><p class="lede">We design the pieces families share before and during a celebration: the save the date in the group chat, the invitation website with the RSVP, the slideshow that plays while everyone is at the tables.</p></section>
<section class="wrap prose prose-narrow"><p>Digipod Studio started on Etsy and has grown to {len(P)} designs, most of them for quinceañeras and sweet 16s. Every template is made to be edited by you in Canva, so you stay in control of every name, photo, date and song, in English, Spanish or both.</p>
<p>We are a {SHOP["badge"]} on Etsy with a {SHOP["rating"]} rating from {SHOP["reviews"]} reviews. If you have a question before or after you order, <a href="@/contact/">message us</a> and we will help.</p></section>''', schema=[bc, ORG])

    nav, bc = crumbs([('', 'Home'), (None, 'Contact')])
    page('contact/index.html', 'Contact Digipod Studio', 'Questions about a template or an order? Message Digipod Studio on Etsy or by email.',
         f'''{nav}<section class="page-head wrap"><h1>Contact us</h1><p class="lede">The fastest way to reach us about an order is an Etsy message, because we can see your purchase there.</p>
<div class="hero-ctas" style="margin-top:20px"><a class="btn btn-primary" href="{SHOP["contact_url"]}" rel="noopener">Message us on Etsy</a></div></section>
<section class="wrap prose prose-narrow"><p>For anything else, email us at <a href="mailto:{SHOP["email"]}">{SHOP["email"]}</a>.</p></section>''', schema=[bc])

    nav, bc = crumbs([('', 'Home'), (None, 'Privacy')])
    page('privacy/index.html', 'Privacy | Digipod Studio', 'How digipodstudio.com handles your information.',
         f'''{nav}<section class="page-head wrap"><h1>Privacy</h1></section><section class="wrap prose prose-narrow">
<p>This website does not ask you to create an account and does not collect payment details. Purchases happen on Etsy, under <a href="https://www.etsy.com/legal/privacy">Etsy's privacy policy</a>.</p>
<p>If you sign up for our checklist and emails, we keep your email address, the celebration you chose and the party date (if you gave one) in a private Google Sheet that only Digipod Studio can see. We use it only to send you planning ideas and new designs, at most once a week. To unsubscribe or have your details deleted, reply to any email or write to the address below.</p>
<p>Your party list is stored only in your own browser on your device. Sharing a list creates a link containing the template numbers you chose and nothing else.</p>
<p>Product photos load from Etsy's image servers and fonts load from Google Fonts. Those services receive standard technical information such as your IP address when your browser requests them.</p>
<p>Questions: <a href="mailto:{SHOP["email"]}">{SHOP["email"]}</a>. Last updated {TODAY:%B %-d, %Y}.</p></section>''', schema=[bc], priority='0.2')

    page('404.html', 'Page not found | Digipod Studio', 'This page does not exist.',
         '<section class="page-head wrap"><h1>We could not find that page</h1><p class="lede">The link may be old or mistyped. Search for a template or start from the shop.</p>'
         '<div class="hero-ctas"><a class="btn btn-primary" href="@/shop/">Go to the shop</a><button class="btn btn-ghost" type="button" data-open-search>Search templates</button></div></section>',
         noindex=True)


def checklist_page():
    md = open(os.path.join(ROOTDIR, 'content', 'checklist.md')).read()
    h = markdown.markdown(md, extensions=['sane_lists'])
    h = h.replace('<li>[ ] ', '<li><span class="box" aria-hidden="true"></span>')
    body = f'''<section class="page-head wrap"><h1>Quinceañera planning checklist</h1>
<p class="lede">Print it, stick it on the fridge and tick it off as a family. Pair it with the <a class="textlink" href="@/planner/">party planner</a> to get the exact dates for your celebration.</p>
<p class="no-print"><button class="btn btn-primary" type="button" onclick="window.print()">Print or save as PDF</button></p></section>
<section class="wrap checklist">{h}</section>
<section class="wrap no-print" style="margin-top:30px"><p class="muted">Find templates for every step in the <a class="textlink" href="@/quinceanera-sweet-16/">quinceañera collection</a>.</p></section>'''
    page('checklist/index.html', 'Quinceañera Planning Checklist (Printable) | Digipod Studio',
         'A printable month-by-month quinceañera planning checklist, from the save the date to the thank-you messages.', body, noindex=True, body_page='checklist')


def static_files(articles):
    os.makedirs(os.path.join(OUT, 'assets'), exist_ok=True)
    for f in ['site.css', 'site.js']:
        shutil.copy(os.path.join(ROOTDIR, 'assets', f), os.path.join(OUT, 'assets', f))
    open(os.path.join(OUT, 'assets', 'favicon.svg'), 'w').write(LOGO.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ').replace(' aria-hidden="true"', ''))
    slim = [{k: p[k] for k in ['id', 'slug', 'name', 'price', 'img', 'img_lg', 'occasion', 'occasion_name', 'type', 'type_name', 'colours', 'themes', 'best']} | {'search': search_text(p)}
            for p in sorted(P, key=rank)]
    json.dump(slim, open(os.path.join(OUT, 'assets', 'products.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    json.dump({'name': BRAND, 'short_name': 'Digipod', 'start_url': '/', 'display': 'browser', 'background_color': '#FCF7F9', 'theme_color': '#2B0B25',
               'icons': [{'src': '/assets/favicon.svg', 'sizes': 'any', 'type': 'image/svg+xml'}]}, open(os.path.join(OUT, 'site.webmanifest'), 'w'))
    if PREVIEW:
        return
    ver = load('site_verification.json') if os.path.exists(os.path.join(ROOTDIR, 'data', 'site_verification.json')) else {}
    for fn, body in ver.get('files', {}).items():
        open(os.path.join(OUT, fn), 'w').write(body)
    if SHOP.get('indexnow_key'):  # IndexNow ownership file (Bing, Yandex, Seznam, Naver)
        open(os.path.join(OUT, SHOP['indexnow_key'] + '.txt'), 'w').write(SHOP['indexnow_key'])
    open(os.path.join(OUT, 'CNAME'), 'w').write('digipodstudio.com\n')
    open(os.path.join(OUT, '.nojekyll'), 'w').write('')
    open(os.path.join(OUT, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\nDisallow: /party-list/\n\nSitemap: {SITE}/sitemap.xml\n')
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, pr in SITEMAP:
        sm.append(f'<url><loc>{u}</loc><lastmod>{TODAY.isoformat()}</lastmod><priority>{pr}</priority></url>')
    sm.append('</urlset>')
    open(os.path.join(OUT, 'sitemap.xml'), 'w').write('\n'.join(sm))
    items = ''.join(f'<item><title>{e(a["title"])}</title><link>{SITE}/{a["path"]}</link><guid>{SITE}/{a["path"]}</guid>'
                    f'<pubDate>{a["date"].strftime("%a, %d %b %Y")} 08:00:00 +0000</pubDate><description>{e(a["description"])}</description></item>' for a in articles[:30])
    open(os.path.join(OUT, 'feed.xml'), 'w').write(f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{BRAND} Journal</title>'
                                                   f'<link>{SITE}/journal/</link><description>Planning ideas for quinceañeras, weddings and birthdays.</description>{items}</channel></rss>')


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    articles = load_articles()
    assign_article_images(articles)
    home(articles)
    spanish_home(articles)
    shop_page()
    occasion_pages()
    colour_pages()
    matching_sets_page()
    product_pages()
    journal_pages(articles)
    planner_page()
    checklist_page()
    simple_pages()
    static_files(articles)
    n = sum(len(f) for _, _, f in os.walk(OUT))
    print(f'built {"preview" if PREVIEW else "site"}: {n} files, {len(SITEMAP)} indexed pages, {len(articles)} articles')


if __name__ == '__main__':
    main()
