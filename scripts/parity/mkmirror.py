#!/usr/bin/env python3
"""Build a static mirror of the WordPress pages from their snapshots, for parity runs in the cloud.

The cloud cannot reach Laragon's .test sites, so: open each route on local with ?kitwp_snapshot=1 (the theme saves
the HTML to _setup/snapshots/), stage the snapshots and the theme, then build the mirror here and serve it next to
the static build (serve.py).

    python3 mkmirror.py --snapshots <dir> --theme <theme dir> --theme-url /wp-content/themes/<theme> \
        --local-host <site>.test --out <mirror dir> [--uploads <uploads dir>] [--static-build <out dir> --media media.json]

- home.html becomes index.html, about.html about/index.html, a__b.html a/b/index.html, parity-missing-page.html
  the 404 page.
- http(s)://<local-host> becomes root-relative, so the mirror works on any port.
- The theme files are copied (not node_modules or tests).
- Uploads: copied from --uploads, or, with --static-build and --media, mapped back to the static build's own files
  (WordPress <name>-<key>-<width>.webp = static /_img<src>-<width>.webp; the original = static <src>), so nothing
  big has to be staged.
"""
import argparse
import json
import os
import re
import shutil

ap = argparse.ArgumentParser()
ap.add_argument('--snapshots', required=True)
ap.add_argument('--theme', required=True)
ap.add_argument('--theme-url', required=True)
ap.add_argument('--local-host', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--uploads')
ap.add_argument('--static-build')
ap.add_argument('--media')
ap.add_argument('--size-key', default='kitk')
a = ap.parse_args()

os.makedirs(a.out, exist_ok=True)
host = re.compile(r'https?://' + re.escape(a.local_host))
pages = 0
html_all = ''
for f in sorted(os.listdir(a.snapshots)):
    if not f.endswith('.html'):
        continue
    html = host.sub('', open(os.path.join(a.snapshots, f), encoding='utf-8').read())
    html_all += html
    stem = f[:-5]
    if stem == 'parity-missing-page':
        dest = os.path.join(a.out, '404.html')
    elif stem == 'home':
        dest = os.path.join(a.out, 'index.html')
    else:
        dest = os.path.join(a.out, *stem.split('__'), 'index.html')
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, 'w', encoding='utf-8').write(html)
    pages += 1

theme_dest = os.path.join(a.out, a.theme_url.strip('/'))
shutil.copytree(a.theme, theme_dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns('node_modules', 'tests', 'vendor', '.git'))

mapped = missing = 0
if a.uploads:
    shutil.copytree(a.uploads, os.path.join(a.out, 'wp-content', 'uploads'), dirs_exist_ok=True)
elif a.static_build and a.media:
    by_stem = {}
    for m in json.load(open(a.media, encoding='utf-8')):
        by_stem[os.path.splitext(os.path.basename(m['src']))[0]] = m
    for url in sorted(set(re.findall(r'/wp-content/uploads/[^"\'\s,)]+', html_all))):
        name = os.path.basename(url)
        stem, ext = os.path.splitext(name)
        w = re.match(r'^(.*)-' + re.escape(a.size_key) + r'-(\d+)$', stem)
        item = by_stem.get(w.group(1) if w else stem)
        if not item:
            missing += 1
            continue
        src = item['variants'].get(w.group(2)) if w else item['src']
        source = os.path.join(a.static_build, (src or '').lstrip('/'))
        if not src or not os.path.exists(source):
            missing += 1
            continue
        dest = os.path.join(a.out, url.lstrip('/'))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(source, dest)
        mapped += 1

print(f'mirror: {pages} pages, theme copied, uploads mapped {mapped}, missing {missing} -> {a.out}')
