#!/usr/bin/env python3
"""The swap test (S1-05): the golden master with the theme's CSS in place of its own must diff 0.000%.

    python3 swaptest.py --ref <golden master URL> --map swap.json [--routes routes.json] [--out swap] [--port 8772]
    python3 serve.py swap 8772 &
    REF=<golden master URL> WP=http://127.0.0.1:8772 node parity.mjs --widths=quick

For every route it saves the golden master's HTML with a <base> pointing at the golden master (images, scripts and
markup stay the golden master's), swaps the stylesheets for the theme's own files, and copies the theme's asset
folders next to the pages, so the theme's CSS and fonts load from the same origin as the page (as on WordPress;
fonts from another origin are blocked without CORS and would show as a false diff). swap.json:

    {
      "theme_dir": "../../theme",
      "copy": ["assets"],
      "css": {"/assets/css/min/style.min.css": "assets/css/style.min.css"},
      "inline": ["assets/css/critical.min.css"],
      "inline_replace": {"url(assets/fonts/": "url(/_theme/assets/fonts/"}
    }

"theme_dir": the folder WordPress loads (for _tw, `<theme>/theme`), relative to swap.json. "copy": its folders to
copy (default: assets). "css": each same-site stylesheet in the golden master (the path; ?v= queries ignored) and
the theme file that replaces it. Every one must be listed: one left out is reported, because the theme lacks it.
"inline" (optional): theme files whose contents replace the page's first inline <style> blocks, in order (a page's
own later blocks stay). "inline_replace" (optional): text swaps on that inline CSS, as the theme's PHP does when it
prints it; the copied theme lives under /_theme/. A diff above 0 is a CSS difference. Read only on both sites.
"""
import argparse
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request

ap = argparse.ArgumentParser()
ap.add_argument('--ref', required=True)
ap.add_argument('--map', required=True)
ap.add_argument('--routes', default='routes.json')
ap.add_argument('--out', default='swap')
ap.add_argument('--port', default='8772')
a = ap.parse_args()

ref = a.ref.rstrip('/')
here = os.path.dirname(os.path.abspath(a.map))
cfg = json.load(open(a.map, encoding='utf-8'))
theme_dir = os.path.normpath(os.path.join(here, cfg.get('theme_dir', '../../theme')))
serve = f'http://127.0.0.1:{a.port}/_theme/'
css_map = {urllib.parse.urlparse(k).path: v for k, v in cfg.get('css', {}).items()}
routes = json.load(open(a.routes, encoding='utf-8'))

missing = [v for v in list(css_map.values()) + cfg.get('inline', []) if not os.path.isfile(os.path.join(theme_dir, v))]
if missing:
    sys.exit('theme files not found under ' + theme_dir + ': ' + ', '.join(missing))
if os.path.isdir(a.out):
    shutil.rmtree(a.out)
os.makedirs(os.path.join(a.out, '_theme'))
for d in cfg.get('copy', ['assets']):
    src = os.path.join(theme_dir, d)
    if not os.path.isdir(src):
        sys.exit(f'theme folder {src} not found (theme_dir in swap.json)')
    shutil.copytree(src, os.path.join(a.out, '_theme', d))

inline_css = []
for v in cfg.get('inline', []):
    body = open(os.path.join(theme_dir, v), encoding='utf-8').read()
    for old, new in cfg.get('inline_replace', {}).items():
        body = body.replace(old, new.replace('/_theme/', serve))
    inline_css.append(body)


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'swaptest'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')


problems = []
for route in routes:
    status, html = get(ref + route)
    seen = set()

    def link(m):
        tag = m.group(0)
        if not re.search(r'rel=["\']?stylesheet', tag, re.I):
            return tag
        href = re.search(r'href=["\']([^"\']+)', tag)
        if not href:
            return tag
        p = urllib.parse.urlparse(urllib.parse.urljoin(ref + route, href.group(1)))
        if p.netloc != urllib.parse.urlparse(ref).netloc:
            return tag  # a third-party stylesheet (Google Fonts...): the theme prints the same link
        seen.add(p.path)
        if p.path not in css_map:
            problems.append(f'{route}: stylesheet {p.path} has no theme file in swap.json')
            return tag
        return tag.replace(href.group(1), serve + css_map[p.path])

    html = re.sub(r'<link\b[^>]*>', link, html, flags=re.I)
    if inline_css and status == 200:
        n = len(re.findall(r'<style\b[^>]*>', html, re.I))
        if n < len(inline_css):
            problems.append(f'{route}: {n} inline <style> blocks, swap.json gives {len(inline_css)}')
        blocks = iter(inline_css)

        def style(m):
            nxt = next(blocks, None)
            return m.group(0) if nxt is None else m.group(1) + nxt + '</style>'

        html = re.sub(r'(<style\b[^>]*>)[\s\S]*?</style>', style, html, flags=re.I)
    html = re.sub(r'(<head\b[^>]*>)', r'\1<base href="' + ref + route + '">', html, count=1, flags=re.I)
    dst = os.path.join(a.out, '404.html') if status == 404 else os.path.join(a.out, route.strip('/'), 'index.html')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'w', encoding='utf-8').write(html)
    print(f'{route}: HTTP {status}, {len(seen)} stylesheets swapped')

for p in sorted(set(problems)):
    print('PROBLEM', p)
print(f'next: python3 serve.py {a.out} {a.port} &  then  REF={ref} WP=http://127.0.0.1:{a.port} node parity.mjs --widths=quick')
sys.exit(1 if problems else 0)
