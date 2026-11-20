#!/usr/bin/env python3
"""Which routes' rendering changed since the last full QA run: after a fix pass, re-run pixel only on those.

    python3 changed-routes.py save <wordpress base> [route ...] [--dir DIR]   after a full run: the baseline
    python3 changed-routes.py diff <wordpress base> [route ...] [--dir DIR]   after a fix pass: what changed

Routes default to routes.json next to this file; DIR defaults to report/rendered/ next to this file. Each route's
HTML is fetched (redirects not followed: a changed status or target counts) and normalised: nonces, CF7's hidden
_wpcf7 values and the admin bar are left out, nothing else. A stylesheet or script whose ?ver= changed (the kit
versions them by file time) changes every page that loads it, so a CSS change marks every route: that is right.
Line 1 of diff: "OK changed-routes: N of M routes changed: re-run pixel on <routes>"; then a CHANGED line per
route (at most 20) with the first differing line. Exit 0;
2 when there is no baseline. --ignore REGEX (repeatable) drops site-specific moving parts (an "open now" badge).
"""
import difflib
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
VOLATILE = [
    r'(name="_wpnonce"|name="_wpcf7[a-z_]*"|name="_wp_http_referer")\s+value="[^"]*"',
    r'"nonce"\s*:\s*"[a-f0-9]+"', r'nonce="[^"]*"', r'<div id="wpadminbar".*?</div>\s*</div>',
    r'<!--.*?-->',
]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


OPEN = urllib.request.build_opener(NoRedirect).open


def fetch(url):
    try:
        with OPEN(url, timeout=30) as r:
            return r.status, r.read().decode('utf-8', 'replace'), r.headers.get('Location', '')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace'), e.headers.get('Location', '')


def rendered(url, ignore):
    status, body, location = fetch(url)
    for rx in VOLATILE + ignore:
        body = re.sub(rx, '', body, flags=re.S)
    body = re.sub(r'>\s+<', '>\n<', body)
    return f'HTTP {status} {location}'.strip() + '\n' + body


def name(route):
    return hashlib.sha1(route.encode()).hexdigest()[:10] + '-' + (re.sub(r'[^a-z0-9]+', '-', route.lower()).strip('-')
                                                                 or 'home') + '.html'


def main(argv):
    args, ignore, folder = list(argv), [], os.path.join(HERE, 'report', 'rendered')
    while '--ignore' in args:
        i = args.index('--ignore')
        ignore.append(args[i + 1])
        del args[i:i + 2]
    if '--dir' in args:
        i = args.index('--dir')
        folder = args[i + 1]
        del args[i:i + 2]
    if len(args) < 2 or args[0] not in ('save', 'diff'):
        print(__doc__)
        return 2
    mode, base, routes = args[0], args[1].rstrip('/'), args[2:]
    if not routes:
        with open(os.path.join(HERE, 'routes.json'), encoding='utf-8') as fh:
            routes = json.load(fh)
    if mode == 'save':
        os.makedirs(folder, exist_ok=True)
        for r in routes:
            with open(os.path.join(folder, name(r)), 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(rendered(base + r, ignore))
        print(f'OK changed-routes: baseline of {len(routes)} routes saved in {folder}')
        return 0
    changed, lines = [], []
    for r in routes:
        p = os.path.join(folder, name(r))
        if not os.path.isfile(p):
            print(f'FAIL changed-routes: no baseline for {r}: run "save" right after the full QA run')
            return 2
        with open(p, encoding='utf-8') as fh:
            old = fh.read().splitlines()
        new = rendered(base + r, ignore).splitlines()
        if old != new:
            changed.append(r)
            first = next((ln for ln in difflib.unified_diff(old, new, lineterm='', n=0)
                          if ln[:1] in '+-' and not ln.startswith(('+++', '---'))), '')
            lines.append(f'CHANGED {r}: {first[:160]}')
    print(f'OK changed-routes: {len(changed)} of {len(routes)} routes changed'
          + (': re-run pixel on ' + ','.join(changed) if changed else ': no pixel re-run needed'))
    for ln in lines[:20]:
        print(ln)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
