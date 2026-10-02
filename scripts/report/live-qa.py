#!/usr/bin/env python3
"""Final live QA for a static-to-WordPress conversion: pages, tracking, redirects, host rules, leftovers.

    python3 live-qa.py https://example.com GTM-XXXXXXX [redirects.json] [local-host.test]
    python3 live-qa.py https://example.com - _setup/seed/redirects.json example.test     (no GTM check)

Checks, read-only (GET requests only):
- every URL in the Yoast sitemap index, plus the thank-you page: status 200 at the same URL, GTM in <head> and the
  noscript right after <body>, no other container id, exactly one H1, a meta description, a canonical (unless
  noindex), no local host string left in the HTML; the thank-you page not in the sitemap;
- every old URL in redirects.json lands on its target (regex rules are listed for a manual check);
- http://, http://www. and https://www. reach https://<domain>/ in ONE 301;
- a missing URL answers 404 twice in a row (LiteSpeed can serve a soft 404 on a repeat request);
- installer, Duplicator and planning files are not public; the REST user list and robots.txt are printed.
Exit code 0 when everything passes, 1 on problems, 3 when the host's bot filter blocked the run (then use
live-qa-console.js in a real browser). Standard library only.
"""
import json
import re
import sys
import time
import urllib.error
import urllib.request

if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(2)
SITE = sys.argv[1].rstrip('/')
GTM = '' if sys.argv[2] == '-' else sys.argv[2]
REDIRECTS = sys.argv[3] if len(sys.argv) > 3 else None
LOCAL = sys.argv[4] if len(sys.argv) > 4 else '.test'
THANK_YOU = '/thank-you/'
HOST = re.sub(r'^https?://', '', SITE)
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36 live-qa'}
fails = []


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def get(url, follow=True, tries=3):
    """(status, final url, body, headers) for a GET. A dropped connection is retried after a pause (hosts and
    proxies reset some requests in a long run); if it keeps failing the status is 0 and the check reports it."""
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    for attempt in range(tries):
        try:
            r = opener.open(urllib.request.Request(url, headers=UA), timeout=40)
            return r.status, r.geturl(), r.read().decode('utf-8', 'replace'), dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, url, (e.read() or b'').decode('utf-8', 'replace'), dict(e.headers or {})
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as e:
            if attempt + 1 == tries:
                return 0, url, f'connection failed: {getattr(e, "reason", e)}', {}
            time.sleep(3 * (attempt + 1))


def path(url):
    return re.sub(r'^https?://[^/]+', '', url) or '/'


def blocked(code, body):
    return code == 415 or 'One moment, please' in body[:4000]


# 0. Is the host's bot filter in the way?
code, _, body, _ = get(SITE + '/')
if blocked(code, body):
    print('The host answered with its bot filter (415 or "One moment, please").')
    print('Run live-qa-console.js in a real browser on the live site instead.')
    sys.exit(3)

# 1. Pages: every sitemap URL plus the thank-you page.
_, _, idx, _ = get(SITE + '/sitemap_index.xml')
urls = []
for sm in re.findall(r'<loc>([^<]+\.xml)</loc>', idx):
    urls += re.findall(r'<loc>([^<]+)</loc>', get(sm)[2])
if not urls:
    fails.append('sitemap_index.xml lists no URLs')
if any(THANK_YOU.rstrip('/') in u for u in urls):
    fails.append('the thank-you page is in the sitemap')
urls.append(SITE + THANK_YOU)
for u in urls:
    code, final, h, _ = get(u)
    head, _, body = h.partition('</head>')
    p = []
    if code != 200 or final.rstrip('/') != u.rstrip('/'):
        p.append(f'status {code} final {path(final)}')
    if GTM:
        if head.count(GTM) < 1 or 'ns.html?id=' + GTM not in body[:3000]:
            p.append('GTM head/noscript missing')
        if re.findall(r'GTM-[A-Z0-9]{5,}', h.replace(GTM, '')):
            p.append('another GTM id')
    h1 = len(re.findall(r'<h1[\s>]', h))
    if h1 != 1:
        p.append(f'h1 count {h1}')
    if LOCAL in h:
        p.append('local host string ' + LOCAL)
    if 'name="description"' not in head:
        p.append('no meta description')
    if 'noindex' not in head and 'rel="canonical"' not in head:
        p.append('no canonical')
    if p:
        fails.append(path(u) + ': ' + ', '.join(p))
print(f'pages: {len(urls)} checked')

# 2. Old URLs.
if REDIRECTS:
    rules = json.load(open(REDIRECTS, encoding='utf-8'))
    n = 0
    for r in rules:
        if r.get('regex') or r['from'].startswith('^'):
            print('regex rule, test by hand:', r['from'], '->', r['to'])
            continue
        n += 1
        code, final, _, _ = get(SITE + r['from'])
        if code != 200 or path(final) != r['to'] or path(final) == r['from']:
            fails.append(f"redirect {r['from']} -> {path(final)} ({code}), expected {r['to']}")
    print(f'redirects: {n} checked')

# 3. Host rules: one hop to https without www.
bare = HOST[4:] if HOST.startswith('www.') else HOST
for start in [f'http://{bare}/', f'http://www.{bare}/', f'https://www.{bare}/']:
    code, _, _, hdr = get(start, follow=False)
    loc = hdr.get('Location') or hdr.get('location') or ''
    if code != 301 or loc.rstrip('/') != f'https://{bare}':
        fails.append(f'{start} -> {code} {loc or "(no Location)"}, expected one 301 to https://{bare}/')
print('host rules: 3 checked')

# 4. A missing URL is a real 404, twice.
for attempt in (1, 2):
    code, _, _, _ = get(SITE + '/live-qa-missing-page-404/', follow=False)
    if code != 404:
        fails.append(f'missing URL answered {code} on request {attempt} (soft 404?)')

# 5. Things that must not be public.
for p in ['/installer.php', '/installer-backup.php', '/dup-installer/main.installer.php', '/wp-content/backups-dup-pro/',
          '/wp-content/backups-dup-lite/', '/wp-content/debug.log', '/readme.html', '/_plan/', '/_setup/', '/handoff.md',
          '/ai-handoff-summary.md', '/BUILD-MAP.md', '/.htaccess', '/wp-config.php']:
    code, _, body, _ = get(SITE + p, follow=False)
    if code == 200 and body.strip():
        fails.append(f'{p} is public ({code})')
code, _, body, _ = get(SITE + '/wp-json/wp/v2/users')
if code == 200 and body.strip().startswith('['):
    print('note: the REST user list is public (usernames):', [u.get('slug') for u in json.loads(body)])
print('robots.txt:\n' + get(SITE + '/robots.txt')[2].strip())

print('\nRESULT:', 'ALL PASS' if not fails else f'{len(fails)} problem(s)')
for f in fails:
    print(' -', f)
sys.exit(1 if fails else 0)
