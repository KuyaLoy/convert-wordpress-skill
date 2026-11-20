"""0.9.6: seodiff.py (head tags and JSON-LD values) and changed-routes.py (what a fix pass changed)."""
import http.server
import os
import tempfile
import threading
import unittest

from helpers import run


def page(desc, ld='{"@type":"Organization","name":"Acme","url":"BASE/"}', theme='#000', nonce='abc123'):
    return (f'<!doctype html><html><head><title>Home</title><meta name="description" content="{desc}">'
            f'<meta name="theme-color" content="{theme}"><link rel="canonical" href="BASE/">'
            f'<link rel="icon" href="/assets/icon.svg?v=1" type="image/svg+xml">'
            f'<script type="application/ld+json">{ld}</script></head><body>'
            f'<form><input type="hidden" name="_wpnonce" value="{nonce}"></form><main>Hi</main></body></html>')


def serve(pages):
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            p = self.server.pages.get(self.path)
            if p is None:
                self.send_response(404)
                self.end_headers()
                return
            if isinstance(p, tuple):  # a redirect
                self.send_response(p[0])
                self.send_header('Location', p[1])
                self.end_headers()
                return
            body = p.replace('BASE', f'http://127.0.0.1:{self.server.server_port}').encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    s = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H)
    s.pages = pages
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, f'http://127.0.0.1:{s.server_port}'


class SeoDiff(unittest.TestCase):
    def test_same_and_values_after_an_apostrophe(self):
        ref, rb = serve({'/': page("Acme's shop, open late"), '/old/': (301, '/new/')})
        wp, wb = serve({'/': page("Acme's shop, open early"), '/old/': (301, '/new/')})
        try:
            r = run('scripts/parity/seodiff.py', rb, rb, '/', '/old/')
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertTrue(r.stdout.startswith('OK seodiff: 2 of 2 routes SAME'), r.stdout)
            self.assertNotIn('DIFF', r.stdout)  # the redirect is compared, not followed
            r = run('scripts/parity/seodiff.py', rb, wb, '/')
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn('DIFF description', r.stdout)  # the old regex parser stopped at the apostrophe: SAME
            self.assertNotIn('canonical', r.stdout)  # each site's own address counts as the same
        finally:
            ref.shutdown()
            ref.server_close()
            wp.shutdown()
            wp.server_close()

    def test_json_ld_values_theme_color_and_status(self):
        ref, rb = serve({'/': page('d')})
        wp, wb = serve({'/': page('d', ld='{"@type":"Organization","name":"Acme Ltd","url":"BASE/"}',
                                   theme='#fff'), })
        try:
            r = run('scripts/parity/seodiff.py', rb, wb, '/', '/gone/')
        finally:
            ref.shutdown()
            ref.server_close()
            wp.shutdown()
            wp.server_close()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn('/: DIFF json-ld, theme-color (status 200/200)', r.stdout)
        self.assertIn('json-ld[0].name: "Acme" | "Acme Ltd"', r.stdout)
        self.assertIn('FAIL seodiff: 1 of 2 routes SAME', r.stdout)  # /gone/ is 404 on both: SAME


class ChangedRoutes(unittest.TestCase):
    def test_only_changed_routes_and_nonces_ignored(self):
        site, base = serve({'/': page('d'), '/about/': page('about')})
        tmp = tempfile.mkdtemp()
        try:
            r = run('scripts/parity/changed-routes.py', 'diff', base, '/', '--dir', tmp)
            self.assertEqual(r.returncode, 2, r.stdout)  # no baseline yet
            run('scripts/parity/changed-routes.py', 'save', base, '/', '/about/', '--dir', tmp)
            site.pages['/'] = page('d', nonce='zzz999')  # a new nonce is not a change
            site.pages['/about/'] = page('about', theme='#123456')
            r = run('scripts/parity/changed-routes.py', 'diff', base, '/', '/about/', '--dir', tmp)
            self.assertEqual(r.returncode, 0, r.stdout)
            first = r.stdout.splitlines()[0]
            self.assertEqual(first, 'OK changed-routes: 1 of 2 routes changed: re-run pixel on /about/')
            self.assertIn('CHANGED /about/', r.stdout)
            self.assertEqual(len(os.listdir(tmp)), 2)
        finally:
            site.shutdown()
            site.server_close()


if __name__ == '__main__':
    unittest.main()
