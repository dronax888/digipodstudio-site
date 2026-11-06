"""Check the built site: every internal link resolves, every JSON-LD block parses. Exit 1 on problems."""
import os, re, json, sys
root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'site')
bad, pages = [], 0
for dp, _, fs in os.walk(root):
    for f in fs:
        if not f.endswith('.html'):
            continue
        pages += 1
        p = os.path.join(dp, f); s = open(p).read()
        for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            try: json.loads(m)
            except Exception as e: bad.append((p, 'JSON-LD: ' + str(e)))
        if f == '404.html':
            continue
        for h in re.findall(r'(?:href|src)="([^"]+)"', s):
            if h.startswith(('http', 'mailto:', '#', 'data:')):
                continue
            t = os.path.normpath(os.path.join(dp, h.split('?')[0].split('#')[0]))
            if os.path.isdir(t): t = os.path.join(t, 'index.html')
            if not os.path.exists(t): bad.append((p, h))
print(f'{pages} pages checked, {len(bad)} problems')
for b in bad[:30]: print(' ', b)
sys.exit(1 if bad else 0)
