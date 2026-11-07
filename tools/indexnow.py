"""Tell search engines (via IndexNow: Bing, Yandex, Seznam, Naver) which pages changed.

Runs in GitHub Actions after each deploy.
    python3 tools/indexnow.py changed   # pages whose files changed in the last commit
    python3 tools/indexnow.py all       # every URL in the sitemap
"""
import json, os, re, subprocess, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://digipodstudio.com'
key = json.load(open(os.path.join(ROOT, 'data', 'shop.json'))).get('indexnow_key')
if not key:
    sys.exit('no indexnow_key in data/shop.json')
sitemap = open(os.path.join(ROOT, 'site', 'sitemap.xml')).read()
indexed = set(re.findall(r'<loc>(.*?)</loc>', sitemap))

mode = sys.argv[1] if len(sys.argv) > 1 else 'changed'
if mode == 'all':
    urls = sorted(indexed)
else:
    try:
        out = subprocess.run(['git', 'diff', '--name-only', 'HEAD~1', 'HEAD', '--', 'site/'], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.split()
    except subprocess.CalledProcessError:
        out = []
    urls = []
    for f in out:
        if f.endswith('index.html'):
            u = SITE + '/' + f[len('site/'):-len('index.html')]
            if u in indexed:
                urls.append(u)
    # a site-wide change (design, products) touches every page: send them all, capped by IndexNow's limit
urls = urls[:10000]
if not urls:
    print('IndexNow: nothing changed')
    sys.exit(0)
body = json.dumps({'host': 'digipodstudio.com', 'key': key, 'keyLocation': f'{SITE}/{key}.txt', 'urlList': urls}).encode()
import time
for attempt in range(3):  # the key file can take a minute to appear after a deploy
    req = urllib.request.Request('https://api.indexnow.org/indexnow', data=body, headers={'Content-Type': 'application/json; charset=utf-8'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f'IndexNow: sent {len(urls)} URLs, response {r.status} (200/202 = accepted)')
            break
    except urllib.error.HTTPError as e:
        print(f'IndexNow: attempt {attempt + 1}, response {e.code} {e.reason}')
        if e.code not in (403, 429) or attempt == 2:
            break
        time.sleep(90)
