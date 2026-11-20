#!/usr/bin/env python3
"""Head tags and JSON-LD of each route, the reference site against WordPress: one fetch per route, no browser.

    python3 seodiff.py <reference base> <wordpress base> [route ...] [--map <ref>=<wp>]... [--dump DIR] [-v]

Routes default to routes.json next to this file. Line 1: OK or FAIL and how many routes are the same; then each
differing route with the keys that differ (-v: every route); exit 1 when any route differs. Compared: the HTTP status (redirects are reported, never followed), title,
description, robots, canonical, og:*, twitter:*, theme-color, viewport, the icon links (file name only), the order
of those tags, and every JSON-LD block after json.loads (so escaping differences do not count, values do).
Attributes are read with html.parser: quotes and apostrophes inside a value are safe. --map swaps the reference's
own origin (its live domain in canonical, og:url and JSON-LD @id) for WordPress's address before comparing.
parity.mjs still does the pixels and the visible text; this is the head, value by value.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser

ICON_RELS = ('icon', 'shortcut icon', 'apple-touch-icon', 'mask-icon')
META_NAMES = ('description', 'robots', 'theme-color', 'viewport')


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags, self.order, self.ld = {}, [], []
        self.title, self._in_title, self._in_ld, self._buf, self._head_done = None, False, False, '', False

    def _add(self, key, value):
        if self._head_done:
            return
        self.tags.setdefault(key, []).append(value)
        if not self.order or self.order[-1] != key:
            self.order.append(key)

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or '') for k, v in attrs}
        if tag == 'script' and a.get('type', '').lower() == 'application/ld+json':
            self._in_ld, self._buf = True, ''
        elif tag == 'title' and not self._head_done and self.title is None:
            self._in_title, self.title = True, ''
        elif tag == 'meta':
            key = (a.get('name') or a.get('property') or '').lower()
            if key in META_NAMES or key.startswith(('og:', 'twitter:')):
                self._add(key, a.get('content', ''))
        elif tag == 'link':
            rel = a.get('rel', '').lower()
            if rel == 'canonical':
                self._add('canonical', a.get('href', ''))
            elif rel in ICON_RELS:
                name = a.get('href', '').split('?')[0].rsplit('/', 1)[-1]
                self._add('link:' + rel, ' '.join(f'{k}={v}' for k, v in (('href', name), ('type', a.get('type')),
                                                                            ('sizes', a.get('sizes'))) if v))

    def handle_endtag(self, tag):
        if tag == 'title':
            self._in_title = False
        elif tag == 'head':
            self._head_done = True
        elif tag == 'script' and self._in_ld:
            self._in_ld = False
            try:
                self.ld.append(json.loads(self._buf))
            except ValueError as err:
                self.ld.append({'<invalid JSON-LD>': str(err)})

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif self._in_ld:
            self._buf += data


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # a redirect is its own status (301, 307), never followed


OPEN = urllib.request.build_opener(NoRedirect).open


def fetch(url):
    try:
        with OPEN(url, timeout=30) as r:
            return r.status, r.read().decode('utf-8', 'replace'), r.headers.get('Location', '')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace'), e.headers.get('Location', '')


def read(url, swap=()):
    status, body, location = fetch(url)
    for a, b in swap:
        body, location = body.replace(a, b), location.replace(a, b)
    p = Page()
    p.feed(body)
    out = dict(p.tags)
    out.update({'status': status, 'title': (p.title or '').strip() if p.title is not None else None,
                'order': p.order, 'json-ld': p.ld})
    if location:
        out['location'] = location
    return out


def norm(v, base):
    """WordPress's and the reference's own address both read {base}, so only paths are compared."""
    if isinstance(v, (list, dict)):
        return json.loads(json.dumps(v).replace(json.dumps(base)[1:-1], '{base}'))
    return v.replace(base, '{base}') if isinstance(v, str) else v


def first_diffs(a, w, path, out):
    if len(out) >= 6:
        return
    if type(a) is not type(w):
        out.append(f'{path}: {json.dumps(a)[:120]} | {json.dumps(w)[:120]}')
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(w)):
            first_diffs(a.get(k, '<missing>'), w.get(k, '<missing>'), f'{path}.{k}', out)
    elif isinstance(a, list) and len(a) != len(w):
        out.append(f'{path}: {len(a)} items | {len(w)} items')
    elif isinstance(a, list):
        for i, (x, y) in enumerate(zip(a, w)):
            first_diffs(x, y, f'{path}[{i}]', out)
    elif a != w:
        out.append(f'{path}: {json.dumps(a)[:120]} | {json.dumps(w)[:120]}')


def main(argv):
    verbose = '-v' in argv
    args, swap, dump = [a for a in argv if a != '-v'], [], None
    while '--map' in args:
        i = args.index('--map')
        swap.append(tuple(args[i + 1].split('=', 1)))
        del args[i:i + 2]
    if '--dump' in args:
        i = args.index('--dump')
        dump = args[i + 1]
        del args[i:i + 2]
        os.makedirs(dump, exist_ok=True)
    if len(args) < 2:
        print(__doc__)
        return 2
    ref, wp, routes = args[0].rstrip('/'), args[1].rstrip('/'), args[2:]
    if not routes:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'routes.json'), encoding='utf-8') as fh:
            routes = json.load(fh)
    fails, lines = 0, []
    for r in routes:
        a = {k: norm(v, ref) for k, v in read(ref + r, swap).items()}
        w = {k: norm(v, wp) for k, v in read(wp + r).items()}
        if dump:
            name = r.strip('/').replace('/', '_') or 'home'
            with open(os.path.join(dump, name + '.json'), 'w', encoding='utf-8', newline='\n') as fh:
                json.dump({'reference': a, 'wordpress': w}, fh, indent=1, ensure_ascii=False)
        keys = [k for k in sorted(set(a) | set(w)) if a.get(k) != w.get(k)]
        fails += bool(keys)
        if keys or verbose:
            lines.append(f'{r}: {"SAME" if not keys else "DIFF " + ", ".join(keys)} '
                         f'(status {a["status"]}/{w["status"]})')
        for k in keys:
            out = []
            first_diffs(a.get(k), w.get(k), k, out)
            lines.extend('   ' + line for line in out)
    print(f'{"OK" if not fails else "FAIL"} seodiff: {len(routes) - fails} of {len(routes)} routes SAME')
    for line in lines if verbose else lines[:20]:
        print(line)
    if not verbose and len(lines) > 20:
        print(f'... {len(lines) - 20} more lines (-v, or --dump DIR for the full head of each route)')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
