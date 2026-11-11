import http.server
import json
import os
import tempfile
import threading
import unittest
import urllib.parse

from helpers import load, run

TOOL = 'scripts/report/live-qa.py'
PAGES = {'/': 'Home', '/about/': 'About', '/thank-you/': 'Thanks'}


class Site(http.server.BaseHTTPRequestHandler):
    """A tiny live site: pages, a sitemap, robots.txt, two old links and an image. server.leaky makes it fail."""

    def log_message(self, *args):
        pass

    def send(self, code, body='', ctype='text/html; charset=utf-8', headers=None):
        data = body.encode()
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        p, q = url.path, url.query
        base = f'http://127.0.0.1:{self.server.server_port}'
        leaky = self.server.leaky
        if p in PAGES:
            robots = 'noindex, follow' if p == '/thank-you/' else 'index, follow'
            local = '<a href="http://shop.test/old/">old</a>' if leaky else ''
            self.send(200, f'<!doctype html><html><head><meta name="description" content="{PAGES[p]} page">'
                           f'<meta name="robots" content="{robots}"><link rel="canonical" href="{base}{p}">'
                           f'</head><body><h1>{PAGES[p]}</h1>{local}</body></html>')
        elif p == '/old-page/':
            self.send(301, headers={'Location': base + '/about/' + ('?' + q if q else '')})
        elif p == '/old-drops-query/':
            self.send(301, headers={'Location': base + '/about/'})
        elif p == '/robots.txt':
            self.send(200, f'User-agent: *\nDisallow:\n\nSitemap: {base}/sitemap_index.xml\n', 'text/plain')
        elif p == '/sitemap_index.xml':
            self.send(200, f'<sitemapindex><sitemap><loc>{base}/page-sitemap.xml</loc></sitemap></sitemapindex>',
                      'application/xml')
        elif p == '/page-sitemap.xml':
            self.send(200, f'<urlset><url><loc>{base}/</loc></url><url><loc>{base}/about/</loc></url></urlset>',
                      'application/xml')
        elif p == '/hero.jpg':
            webp = 'image/webp' in self.headers.get('Accept', '')
            self.send(200, 'img', 'image/webp' if webp else 'image/jpeg', {'Vary': 'Accept'})
        elif p == '/handoff.md' and leaky:
            self.send(200, '# notes', 'text/markdown')
        elif p == '/_plan/':
            self.send(403, 'Forbidden')
        else:
            self.send(404, '<html><head><meta name="robots" content="noindex"></head><body>Not found</body></html>')


def serve(leaky):
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Site)
    server.leaky = leaky
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


class LiveQa(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clean, cls.leaky = serve(False), serve(True)
        cls.tmp = tempfile.mkdtemp(prefix='liveqa-')
        cls.redirects = os.path.join(cls.tmp, 'redirects.json')
        with open(cls.redirects, 'w', encoding='utf-8') as fh:
            json.dump([{'from': '/old-page/', 'to': '/about/'}, {'from': '^/old(/.*)?$', 'to': '/', 'regex': True}], fh)

    @classmethod
    def tearDownClass(cls):
        for s in (cls.clean, cls.leaky):
            s.shutdown()
            s.server_close()

    def qa(self, server, *args):
        site = f'http://127.0.0.1:{server.server_port}'
        r = run(TOOL, site, '-', *args, '--delay', '0', '--timeout', '5', timeout=120)
        return r, r.stdout

    def test_clean_site_all_pass(self):
        out_json = os.path.join(self.tmp, 'clean.json')
        r, out = self.qa(self.clean, '--redirects', self.redirects, '--routes', '/,/about/', '--image', '/hero.jpg',
                         '--json', out_json)
        self.assertEqual(r.returncode, 0, out + r.stderr)
        self.assertIn('PASS Pages: 3 pages checked, each answers 200', out)
        self.assertIn('PASS Missing page: a made-up path answers 404 twice', out)
        self.assertIn('PASS Old links: 1 old URLs checked, each one 301 to the right page, query kept', out)
        self.assertIn('NOTE Old links: regex rule', out)
        self.assertIn('PASS Private files: 22 private paths checked, none is public', out)
        self.assertIn('PASS WebP:', out)
        self.assertIn('SKIP Host rules', out)
        self.assertTrue(out.rstrip().splitlines()[-2].startswith('RESULT: ALL PASS'), out)
        with open(out_json, encoding='utf-8') as fh:
            data = json.load(fh)
        self.assertEqual(data['result'], 'ALL PASS')
        self.assertEqual(data['fail_count'], 0)

    def test_problems_fail(self):
        bad = os.path.join(self.tmp, 'bad.json')
        with open(bad, 'w', encoding='utf-8') as fh:
            json.dump([{'from': '/old-drops-query/', 'to': '/about/'}, {'from': '/never-set/', 'to': '/about/'}], fh)
        r, out = self.qa(self.leaky, '--redirects', bad, '--routes', '/,/about/,/gone/')
        self.assertEqual(r.returncode, 1, out)
        self.assertIn('FAIL Pages: /gone/ answers 404 (expected 200)', out)
        self.assertIn('FAIL Old links: /old-drops-query/?utm_source=qa goes to /about/: the query string is lost', out)
        self.assertIn('FAIL Old links: /never-set/ answers 404 (expected 301 to /about/)', out)
        self.assertIn('FAIL Private files: /handoff.md is public (200)', out)
        self.assertIn('FAIL Local leftovers: / still links to a local address: http://shop.test', out)
        self.assertRegex(out, r'RESULT: \d+ FAIL')

    def test_hidden_flips_robots(self):
        r, out = self.qa(self.clean, '--routes', '/', '--hidden', '-v')
        self.assertEqual(r.returncode, 1, out)
        self.assertIn('robots.txt does not block everything', out)
        self.assertIn('FAIL Search engines: / robots meta is index, expected noindex', out)
        self.assertIn('PASS Search engines: /thank-you/ noindex', out)
        self.assertIn('PASS Private files: /_plan/ answers 403', out)

    def test_helpers(self):
        m = load(TOOL)
        self.assertTrue(m.covers('www.example.com', ['example.com', '*.example.com']))
        self.assertFalse(m.covers('example.com', ['*.example.com']))
        self.assertTrue(m.LOCAL_RE.search('src="http://site.test/a.png"'))
        self.assertTrue(m.LOCAL_RE.search('"url":"https:\\/\\/localhost:8080\\/"'))
        self.assertFalse(m.LOCAL_RE.search('https://example.com/test/ and site.tester.com'))
        self.assertTrue(m.robots_meta('<meta content="noindex, follow" name="ROBOTS">', {}))
        self.assertEqual(m.canonical("<link href='https://a.com/x/' rel='canonical'>"), 'https://a.com/x/')


if __name__ == '__main__':
    unittest.main()
