#!/usr/bin/env python3
"""Final live QA for a static-to-WordPress conversion: one run checks what a launch needs. Read-only: GET only.

    python3 live-qa.py https://example.com GTM-XXXXXXX [redirects.json] [local-host.test] [options]
    python3 live-qa.py https://example.com - _setup/seed/redirects.json example.test     (no GTM check)
    python3 live-qa.py https://www.example.com - --redirects _setup/seed/redirects.json --routes /,/about/ \\
        --leftovers 20261111_site_archive.zip,20261111_installer.php --image /wp-content/uploads/hero.jpg

The site URL you give is the canonical host (with or without www). Each check prints PASS or FAIL, then the run
ends with ALL PASS or N FAIL.
1. Pages: every route answers 200 with no redirect. Routes come from --routes (a comma list or a file), else from
   <theme>/tests/parity/routes.json when found (--theme), plus every sitemap URL, / and the thank-you page.
   A made-up path answers 404, twice (LiteSpeed can serve a soft 404 on a repeat request).
2. Old links: every rule in redirects.json answers one 301 to its target, also with ?utm_source=qa kept, and the
   target answers 200. Regex rules are listed for a check by hand.
3. Host rules: http://domain, http://www.domain and https:// on the other host each answer one 301 straight to
   the canonical https host.
4. Private files: planning, handoff, installer, Duplicator, log and config files answer 403 or 404, never 200.
   --leftovers adds names such as *_archive.zip and *_installer.php.
5. Certificate: the certificate on the apex and on www covers both names and runs more than 14 days.
6. Search engines: robots meta index on every page except the thank-you page (noindex), a canonical link on the
   canonical host, robots.txt has a Sitemap line and the sitemap answers 200, the thank-you page is not in the
   sitemap. --hidden (before launch) expects noindex everywhere and a robots.txt that blocks everything.
7. Local leftovers: no .test or localhost URL (or the local host you give) in any page.
8. Page content: one H1 and a meta description. With a GTM ID: the container in the head, the noscript right
   after <body>, no other container id.
9. WebP: with --image, a request that accepts WebP gets image/webp.
Host rules and the certificate are skipped for an IP address or localhost, or with --skip hosts,tls.
Exit 0 when all pass, 1 on any FAIL, 2 on a usage error, 3 when the host's bot filter blocked the run (then use
live-qa-console.js in a real browser). Standard library only.
"""
import argparse
import glob
import html
import ipaddress
import json
import os
import random
import re
import socket
import ssl
import string
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/130.0.0.0 Safari/537.36')
ACCEPT_HTML = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
ACCEPT_WEBP = 'image/webp,*/*;q=0.8'
PRIVATE = ['/_plan/', '/_setup/', '/tasks/', '/.claude/', '/.git/', '/.git/HEAD', '/handoff.md',
           '/ai-handoff-summary.md', '/BUILD-MAP.md', '/wp-content/debug.log', '/php.ini', '/.user.ini',
           '/installer.php', '/installer-backup.php', '/dup-installer/', '/dup-installer/main.installer.php',
           '/wp-content/backups-dup-pro/', '/wp-content/backups-dup-lite/', '/wp-content/duplicator-backups/',
           '/readme.html', '/.htaccess', '/wp-config.php']
LOCAL_RE = re.compile(r'(?:https?:)?\\?/\\?/(?:[a-z0-9-]+\.)*(?:[a-z0-9-]+\.test|localhost)(?![a-z0-9.-])', re.I)
ATTR_RE = re.compile(r'([\w:-]+)\s*=\s*("[^"]*"|\'[^\']*\'|[^\s>]+)')
GROUPS = ('pages', 'missing', 'seo', 'content', 'local', 'redirects', 'hosts', 'private', 'tls', 'webp')
CERT_DAYS = 14
MAX_FAIL_LINES = 20


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Resp:
    def __init__(self, status, url, body=b'', headers=None, error=''):
        self.status, self.url, self.body, self.error = status, url, body, error
        self.headers = {k.lower(): v for k, v in (headers.items() if headers else [])}

    @property
    def text(self):
        return self.body.decode('utf-8', 'replace')

    def location(self):
        loc = self.headers.get('location', '')
        return urllib.parse.urljoin(self.url, loc) if loc else ''


class Client:
    """GET only, with a pause between requests and a browser User-Agent."""

    def __init__(self, delay, timeout):
        self.delay, self.timeout, self.last = delay, timeout, 0.0
        self.openers = {True: urllib.request.build_opener(), False: urllib.request.build_opener(NoRedirect)}

    def pause(self):
        wait = self.last + self.delay - time.time()
        if wait > 0:
            time.sleep(wait)

    def get(self, url, follow=False, accept=ACCEPT_HTML, tries=3):
        """A dropped connection is retried after a pause (hosts reset some requests in a long run). A certificate
        error is not retried. When nothing answers, the status is 0 and the error says why."""
        headers = {'User-Agent': UA, 'Accept': accept, 'Accept-Language': 'en'}
        try:
            for attempt in range(tries):
                self.pause()
                try:
                    with self.openers[follow].open(urllib.request.Request(url, headers=headers),
                                                   timeout=self.timeout) as r:
                        return Resp(r.status, r.geturl(), r.read(), r.headers)
                except urllib.error.HTTPError as e:
                    try:
                        body = e.read() or b''
                    except Exception:
                        body = b''
                    return Resp(e.code, url, body, e.headers)
                except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as e:
                    reason = getattr(e, 'reason', e)
                    if isinstance(reason, ssl.SSLError) or attempt + 1 == tries:
                        return Resp(0, url, error=str(reason))
                    time.sleep(2 * (attempt + 1))
                finally:
                    self.last = time.time()
        finally:
            self.last = time.time()


class Report:
    def __init__(self, verbose):
        self.verbose, self.checks, self.notes, self.printed, self.hidden_fails = verbose, [], [], 0, 0

    def group(self, name, items, all_pass=''):
        """items: (ok, text). A group with a summary prints it when all pass, else its FAIL lines. -v: every line."""
        for ok, text in items:
            self.checks.append({'group': name, 'ok': ok, 'text': text})
        if not items:
            return
        if not self.verbose and all_pass:
            if all(ok for ok, _ in items):
                print(f'PASS {name}: {all_pass}')
                return
            items = [i for i in items if not i[0]]
        for ok, text in items:
            if not ok and not self.verbose and self.printed >= MAX_FAIL_LINES:
                self.hidden_fails += 1
                continue
            print(f'{"PASS" if ok else "FAIL"} {name}: {text}')
            self.printed += 0 if ok else 1

    def note(self, name, text):
        self.notes.append(f'{name}: {text}')
        print(f'NOTE {name}: {text}')

    @staticmethod
    def skip(name, why):
        print(f'SKIP {name}: {why}')


def tags(head, tag):
    """Attribute dicts of every <tag ...> in the HTML (attribute names lower case)."""
    out = []
    for t in re.findall(r'<%s\b[^>]*>' % tag, head, re.I):
        out.append({k.lower(): html.unescape(v.strip('"\'')) for k, v in ATTR_RE.findall(t)})
    return out


def robots_meta(head, headers):
    words = [m.get('content', '').lower() for m in tags(head, 'meta') if m.get('name', '').lower() == 'robots']
    words.append(headers.get('x-robots-tag', '').lower())
    return 'noindex' in ' '.join(words)


def canonical(head):
    for link in tags(head, 'link'):
        if 'canonical' in link.get('rel', '').lower().split():
            return link.get('href', '')
    return ''


def covers(name, patterns):
    name = name.lower()
    for p in patterns:
        p = p.lower()
        if p == name or (p.startswith('*.') and '.' in name and name.split('.', 1)[1] == p[2:]):
            return True
    return False


def same_path(a, b):
    return a.rstrip('/') == b.rstrip('/')


def blocked(r):
    return r.status == 415 or 'One moment, please' in r.text[:4000]


def is_ip_or_local(host):
    if host == 'localhost' or host.endswith('.localhost'):
        return True
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def as_path(origin, u):
    """A route as a path on the site: absolute URLs lose their origin, a missing leading slash is added."""
    u = u.strip()
    if re.match(r'https?://', u):
        s = urllib.parse.urlsplit(u)
        return (s.path or '/') + ('?' + s.query if s.query else '')
    return u if u.startswith('/') else '/' + u


def short(origin, u):
    return u[len(origin):] or '/' if u.startswith(origin) else u


def read_list(value):
    """--routes / --leftovers: a comma list, or a file (JSON list, or one item per line)."""
    if not value:
        return []
    if os.path.isfile(value):
        with open(value, encoding='utf-8') as fh:
            text = fh.read()
        if text.lstrip().startswith('['):
            return [str(x) for x in json.loads(text)]
        return [x.strip() for x in text.splitlines() if x.strip() and not x.strip().startswith('#')]
    return [x.strip() for x in value.split(',') if x.strip()]


def find_routes_json(theme):
    """The parity tool's routes.json: <theme>/tests/parity/routes.json, else the one theme under wp-content/themes
    (from the current folder, or the WordPress root above _plan/tools/report/)."""
    if theme:
        f = os.path.join(theme, 'tests', 'parity', 'routes.json')
        return f if os.path.isfile(f) else None
    roots = [os.getcwd(), os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))]
    found = []
    for root in roots:
        for f in glob.glob(os.path.join(root, 'wp-content', 'themes', '*', 'tests', 'parity', 'routes.json')):
            if os.path.realpath(f) not in [os.path.realpath(x) for x in found]:
                found.append(f)
    return found[0] if len(found) == 1 else None


def sitemap_urls(c, url, depth=0):
    """(status of the first sitemap, every page URL in it, following a sitemap index one or two levels)."""
    r = c.get(url)
    locs = [html.unescape(x) for x in re.findall(r'<loc>\s*([^<\s]+)\s*</loc>', r.text)]
    if r.status != 200:
        return r.status, []
    if '<sitemapindex' in r.text and depth < 2:
        pages = []
        for sm in locs:
            pages += sitemap_urls(c, sm, depth + 1)[1]
        return r.status, pages
    return r.status, locs


def cert_check(c, host, names, timeout):
    """(ok, text) for the certificate one host serves."""
    c.pause()
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=timeout) as s:
            with ctx.wrap_socket(s, server_hostname=host) as t:
                cert = t.getpeercert()
    except ssl.SSLCertVerificationError as e:
        return False, f'{host} serves a certificate that does not pass ({e.verify_message or e})'
    except (OSError, ssl.SSLError) as e:
        return False, f'{host} does not answer on https ({e})'
    finally:
        c.last = time.time()
    dns = [v for k, v in cert.get('subjectAltName', ()) if k == 'DNS']
    end = ssl.cert_time_to_seconds(cert['notAfter'])
    days = int((end - time.time()) // 86400)
    date = time.strftime('%Y-%m-%d', time.gmtime(end))
    missing = [n for n in names if not covers(n, dns)]
    if missing:
        return False, f'{host} certificate does not cover {", ".join(missing)} (expires {date})'
    if days <= CERT_DAYS:
        return False, f'{host} certificate expires {date}, in {days} days (renew it)'
    return True, f'{host} certificate covers {" and ".join(names)}, expires {date} ({days} days)'


def parse(argv):
    p = argparse.ArgumentParser(description='Final live QA: read-only checks on the live site, PASS or FAIL each.',
                                usage='live-qa.py SITE [GTM-ID|-] [redirects.json] [local-host] [options]')
    p.add_argument('site', help='the live site on its canonical host, for example https://example.com')
    p.add_argument('gtm_pos', nargs='?', default='', metavar='GTM-ID', help='GTM container id, or - to skip')
    p.add_argument('redirects_pos', nargs='?', default='', metavar='redirects.json')
    p.add_argument('local_pos', nargs='?', default='', metavar='local-host')
    p.add_argument('--gtm', default='', help='GTM container id (same as the second argument)')
    p.add_argument('--redirects', default='', help='redirects.json: a list of {"from", "to"}')
    p.add_argument('--local', default='', help='the local host name to look for, for example example.test')
    p.add_argument('--routes', default='', help='routes to check: a comma list or a file (JSON list or lines)')
    p.add_argument('--theme', default='', help='theme folder: use <theme>/tests/parity/routes.json')
    p.add_argument('--thank-you', default='/thank-you/', help='the thank-you path (noindex), - when none')
    p.add_argument('--leftovers', default='', help='more private names, for example x_archive.zip,x_installer.php')
    p.add_argument('--hidden', action='store_true', help='before launch: expect noindex and a blocking robots.txt')
    p.add_argument('--image', default='', help='an image URL or path for the WebP check')
    p.add_argument('--skip', default='', help='checks to leave out, comma list: ' + ','.join(GROUPS))
    p.add_argument('--delay', type=float, default=0.5, help='seconds between requests (default 0.5)')
    p.add_argument('--timeout', type=float, default=30, help='seconds to wait for each answer (default 30)')
    p.add_argument('--json', default='', help='write every result to this JSON file')
    p.add_argument('-v', '--verbose', action='store_true', help='print every check, not only failures')
    return p.parse_args(argv)


def main(argv=None):
    try:
        sys.stdout.reconfigure(errors='replace')
    except (AttributeError, ValueError):
        pass
    a = parse(argv)
    site = a.site.rstrip('/')
    if not re.match(r'https?://', site):
        site = 'https://' + site
    parts = urllib.parse.urlsplit(site)
    origin, netloc, host = f'{parts.scheme}://{parts.netloc}', parts.netloc, parts.hostname or ''
    bare = host[4:] if host.startswith('www.') else host
    gtm = a.gtm or ('' if a.gtm_pos == '-' else a.gtm_pos)
    redirects = a.redirects or a.redirects_pos
    local = (a.local or a.local_pos or '').strip()
    thank = '' if a.thank_you == '-' else as_path(origin, a.thank_you)
    skip = {x.strip().lower() for x in a.skip.split(',') if x.strip()}
    unknown = skip - set(GROUPS)
    if unknown:
        print('Unknown --skip name: ' + ', '.join(sorted(unknown)) + '. Use: ' + ', '.join(GROUPS))
        return 2
    c, rep = Client(a.delay, a.timeout), Report(a.verbose)
    mode = 'hidden, expects noindex' if a.hidden else 'live, expects index'
    print(f'live-qa: {origin} (canonical host {netloc}, {mode})')

    home = c.get(origin + '/')
    if blocked(home):
        print('The host answered with its bot filter (415 or "One moment, please").')
        print('Run live-qa-console.js in a real browser on the live site instead.')
        return 3
    if home.status == 0:
        print(f'FAIL Site: {origin}/ does not answer ({home.error})')
        print('\nRESULT: 1 FAIL')
        return 1

    # Route list: --routes, else the parity routes.json; the parity tool's deliberate missing page is left out.
    routes = read_list(a.routes)
    source = 'the --routes list' if routes else ''
    if not routes:
        rj = find_routes_json(a.theme)
        if rj:
            routes, source = read_list(rj), rj
        elif a.theme:
            rep.note('Pages', f'no tests/parity/routes.json in {a.theme}')
    routes = [as_path(origin, r) for r in routes
              if 'missing-page' not in r and '[' not in r and (':' not in r or re.match(r'https?://', r))]

    # robots.txt and the sitemap (also a source of pages).
    seo = 'seo' not in skip
    seo_items = []
    robots = c.get(origin + '/robots.txt')
    maps = re.findall(r'(?im)^\s*sitemap:\s*(\S+)', robots.text) if robots.status == 200 else []
    blocks_all = bool(re.search(r'(?ims)user-agent:[ \t]*\*.*?^[ \t]*disallow:[ \t]*/[ \t]*$', robots.text))
    if a.hidden:
        seo_items.append((robots.status == 200 and blocks_all,
                          'robots.txt blocks everything (Disallow: /)' if blocks_all and robots.status == 200 else
                          f'robots.txt does not block everything (answers {robots.status}), expected Disallow: /'))
    else:
        seo_items.append((robots.status == 200 and bool(maps) and not blocks_all,
                          'robots.txt has a Sitemap line' if maps and not blocks_all else
                          'robots.txt blocks everything (Disallow: /): search engines are kept out' if blocks_all else
                          f'robots.txt has no Sitemap line (answers {robots.status})'))
    sm_url = maps[0] if maps else origin + '/sitemap_index.xml'
    sm_status, sm_pages = sitemap_urls(c, sm_url)
    if not a.hidden:
        seo_items.append((sm_status == 200 and bool(sm_pages),
                          f'the sitemap answers 200 and lists {len(sm_pages)} pages' if sm_status == 200 and sm_pages
                          else f'the sitemap {short(origin, sm_url)} answers {sm_status} with {len(sm_pages)} pages'))
        other = [u for u in sm_pages if not u.startswith(origin + '/') and u != origin]
        if other:
            seo_items.append((False, f'{len(other)} sitemap URLs are not on {origin}, for example {other[0]}'))
        if thank:
            in_map = [u for u in sm_pages if same_path(as_path(origin, u), thank)]
            seo_items.append((not in_map, 'the thank-you page is not in the sitemap' if not in_map
                              else 'the thank-you page is in the sitemap (it should stay out)'))

    if thank:  # use the form the site itself uses (with or without the trailing slash)
        thank = next((r for r in routes + [as_path(origin, u) for u in sm_pages] if same_path(r, thank)), thank)
    pages = []
    for r in ['/'] + routes + [as_path(origin, u) for u in sm_pages] + ([thank] if thank else []):
        if r not in pages:
            pages.append(r)
    note = f'routes from {source}, ' if source else ''
    print(f'Checking {len(pages)} pages ({note}plus the sitemap, / and the thank-you page).')

    # 1. Pages answer 200, with no redirect.
    got = {'/': home}
    for p in pages:
        if p not in got:
            got[p] = c.get(origin + p)
    items = []
    for p in pages:
        r = got[p]
        if r.status == 200:
            items.append((True, f'{p} answers 200'))
        elif 300 <= r.status < 400:
            items.append((False, f'{p} answers {r.status} to {short(origin, r.location())} (expected 200)'))
        elif r.status == 0:
            items.append((False, f'{p} does not answer ({r.error})'))
        else:
            items.append((False, f'{p} answers {r.status} (expected 200)'))
    if 'pages' not in skip:
        rep.group('Pages', items, f'{len(pages)} pages checked, each answers 200')
    ok_pages = [p for p in pages if got[p].status == 200]

    # A made-up path is a real 404, twice.
    if 'missing' not in skip:
        fake = '/live-qa-missing-' + ''.join(random.choice(string.ascii_lowercase) for _ in range(6)) + '/'
        codes = [c.get(origin + fake).status for _ in (1, 2)]
        rep.group('Missing page', [(codes == [404, 404], 'a made-up path answers 404 twice' if codes == [404, 404]
                                    else f'a made-up path answers {codes[0]} then {codes[1]} (expected 404 twice)')])

    # Search engines: robots meta and canonical on every page.
    if seo:
        for p in ok_pages:
            r = got[p]
            head = r.text.partition('</head>')[0]
            noindex = robots_meta(head, r.headers)
            want_noindex = a.hidden or bool(thank and same_path(p, thank))
            probs = []
            if noindex != want_noindex:
                probs.append('robots meta is ' + ('noindex, expected index' if noindex else 'index, expected noindex'))
            canon = canonical(head)
            if canon:
                cu = urllib.parse.urlsplit(urllib.parse.urljoin(origin + p, canon))
                if f'{cu.scheme}://{cu.netloc}' != origin:
                    probs.append(f'canonical is on {cu.scheme}://{cu.netloc}, expected {origin}')
            elif not want_noindex:
                probs.append('no canonical link')
            seo_items.append((not probs, f'{p} ' + ('; '.join(probs) if probs else
                              ('noindex' if noindex else 'index') + (', canonical on ' + netloc if canon else ''))))
        rep.group('Search engines', seo_items,
                  f'robots.txt, sitemap and {len(ok_pages)} pages checked, ' +
                  ('noindex everywhere' if a.hidden else 'index with a canonical on the canonical host'))

    # Page content and tracking.
    if 'content' not in skip:
        items, track = [], []
        for p in ok_pages:
            text = got[p].text
            head, _, body = text.partition('</head>')
            probs = []
            h1 = len(re.findall(r'<h1[\s>]', text, re.I))
            if h1 != 1:
                probs.append(f'{h1} H1 headings (expected 1)')
            if not any(m.get('name', '').lower() == 'description' and m.get('content', '').strip()
                       for m in tags(head, 'meta')):
                probs.append('no meta description')
            items.append((not probs, f'{p} ' + ('; '.join(probs) if probs else 'has one H1 and a description')))
            if gtm:
                tp = []
                if gtm not in head or 'ns.html?id=' + gtm not in body[:3000]:
                    tp.append(f'{gtm} missing in the head or the noscript after <body>')
                others = sorted(set(re.findall(r'GTM-[A-Z0-9]{5,}', text.replace(gtm, ''))))
                if others:
                    tp.append('another container id: ' + ', '.join(others))
                track.append((not tp, f'{p} ' + ('; '.join(tp) if tp else f'loads {gtm}')))
        rep.group('Page content', items, f'{len(ok_pages)} pages checked, each has one H1 and a description')
        if gtm:
            rep.group('Tracking', track, f'{len(ok_pages)} pages checked, {gtm} in the head and the noscript')

    # Local leftovers.
    if 'local' not in skip:
        items = []
        for p in ok_pages:
            text = got[p].text
            m = LOCAL_RE.search(text)
            hit = m.group(0) if m else (local if local and local != '.test' and local.lower() in text.lower() else '')
            items.append((not hit, f'{p} still links to a local address: {hit}' if hit else f'{p} has no local URL'))
        rep.group('Local leftovers', items, f'{len(ok_pages)} pages checked, no .test or localhost URL')

    # 2. Old links: one 301 to the target, the query string kept, the target answers 200.
    if redirects and 'redirects' not in skip:
        with open(redirects, encoding='utf-8') as fh:
            rules = json.load(fh)
        items, targets, checked = [], [], 0
        for rule in rules:
            frm, to = rule.get('from', ''), rule.get('to', '')
            if rule.get('regex') or frm.startswith('^'):
                rep.note('Old links', f'regex rule {frm} -> {to}: check it by hand')
                continue
            checked += 1
            frm = as_path(origin, frm)
            want = to if re.match(r'https?://', to) else origin + as_path(origin, to)
            r = c.get(origin + frm)
            loc = r.location()
            q = c.get(origin + frm + ('&' if '?' in frm else '?') + 'utm_source=qa')
            ql, wl = urllib.parse.urlsplit(q.location()), urllib.parse.urlsplit(want)
            kept = q.status == 301 and (ql.scheme, ql.netloc, ql.path) == (wl.scheme, wl.netloc, wl.path) \
                and 'utm_source=qa' in ql.query
            if r.status != 301 or loc != want:
                where = f' to {short(origin, loc)}' if loc else ''
                items.append((False, f'{frm} answers {r.status}{where} (expected 301 to {short(origin, want)})'))
            elif not kept:
                items.append((False, f'{frm}?utm_source=qa goes to {short(origin, q.location()) or q.status}: '
                                     'the query string is lost'))
            else:
                items.append((True, f'{frm} 301 to {short(origin, want)}, query kept'))
            if want not in targets:
                targets.append(want)
        for t in targets:
            p = short(origin, t)
            r = got.get(p) if t.startswith(origin) and p in got else c.get(t)
            if r.status != 200:
                items.append((False, f'target {p} answers {r.status} (expected 200)'))
        rep.group('Old links', items, f'{checked} old URLs checked, each one 301 to the right page, query kept')

    # 3. Host rules: one 301 straight to the canonical https host.
    if 'hosts' in skip:
        pass
    elif is_ip_or_local(host) or parts.port:
        rep.skip('Host rules', 'the site is an IP address, localhost or has a port')
    else:
        other = f'www.{bare}' if host == bare else bare
        items = []
        for start in [f'http://{bare}/', f'http://www.{bare}/', f'https://{other}/']:
            r = c.get(start)
            loc = r.headers.get('location', '')
            if r.status == 301 and loc.rstrip('/') == f'https://{host}':
                items.append((True, f'{start} answers one 301 to https://{host}/'))
            elif r.status == 0:
                items.append((False, f'{start} does not answer ({r.error})'))
            else:
                items.append((False, f'{start} answers {r.status} {loc or "(no Location)"}, '
                                     f'expected one 301 to https://{host}/'))
        rep.group('Host rules', items)

    # 4. Private files: 403 or 404, never 200.
    if 'private' not in skip:
        items = []
        extra = [as_path(origin, x) for x in read_list(a.leftovers)]
        for p in PRIVATE + [x for x in extra if x not in PRIVATE]:
            r = c.get(origin + p)
            if r.status in (401, 403, 404, 410):
                items.append((True, f'{p} answers {r.status}'))
            elif r.status == 200 and p.endswith('.php') and not r.body.strip():
                items.append((True, f'{p} runs and shows nothing'))
            elif r.status == 200:
                items.append((False, f'{p} is public (200): remove it or block it'))
            elif 300 <= r.status < 400 and not same_path(urllib.parse.urlsplit(r.location()).path, p):
                items.append((True, f'{p} redirects away ({r.status})'))
            elif r.status == 0:
                items.append((False, f'{p} does not answer ({r.error})'))
            else:
                items.append((False, f'{p} answers {r.status} (expected 403 or 404)'))
        rep.group('Private files', items, f'{len(items)} private paths checked, none is public')
        users = c.get(origin + '/wp-json/wp/v2/users')
        if users.status == 200 and users.text.strip().startswith('['):
            try:
                names = [u.get('slug') for u in json.loads(users.text)]
            except ValueError:
                names = []
            rep.note('Private files', 'the REST user list is public (usernames): ' + ', '.join(map(str, names)))

    # 5. Certificate on the apex and on www.
    if 'tls' in skip:
        pass
    elif is_ip_or_local(host) or parts.scheme != 'https':
        rep.skip('Certificate', 'the site is not https on a domain name')
    else:
        names = [bare, f'www.{bare}']
        rep.group('Certificate', [cert_check(c, h, names, a.timeout) for h in names])

    # 9. WebP.
    if a.image and 'webp' not in skip:
        url = a.image if re.match(r'https?://', a.image) else origin + as_path(origin, a.image)
        r = c.get(url, follow=True, accept=ACCEPT_WEBP)
        ctype = r.headers.get('content-type', '').split(';')[0].strip().lower()
        ok = r.status == 200 and ctype == 'image/webp'
        rep.group('WebP', [(ok, f'{short(origin, url)} sends image/webp to a browser that accepts it' if ok else
                            f'{short(origin, url)} answers {r.status} {ctype or "(no type)"}, expected image/webp')])

    fails = [x for x in rep.checks if not x['ok']]
    if rep.hidden_fails:
        print(f'... {rep.hidden_fails} more FAIL lines: run with -v' + (' or read ' + a.json if a.json else ''))
    total = len(rep.checks)
    result = 'ALL PASS' if not fails else f'{len(fails)} FAIL'
    print(f'\nRESULT: {result} ({total} checks)')
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as fh:
            json.dump({'tool': 'live-qa', 'site': origin, 'hidden': a.hidden,
                       'date': time.strftime('%Y-%m-%d %H:%M:%S'), 'result': result, 'checks_total': total,
                       'fail_count': len(fails), 'checks': rep.checks, 'notes': rep.notes}, fh, indent=2)
        print(f'Every result: {a.json}')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
