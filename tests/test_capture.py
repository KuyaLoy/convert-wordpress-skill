import base64
import functools
import http.server
import json
import os
import shutil
import tempfile
import threading
import unittest

from helpers import run

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=')
PW = os.environ.get('KIT_PLAYWRIGHT', '/tmp/claude-0/pw/node_modules')
CHROME = os.environ.get('CHROME_PATH', '/opt/pw-browsers/chromium')


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@unittest.skipUnless(shutil.which('node') and os.path.isdir(os.path.join(PW, 'playwright')), 'needs Node and Playwright')
class Capture(unittest.TestCase):
    def test_capture_fixture(self):
        tmp = tempfile.mkdtemp(prefix='cap-')
        site = os.path.join(tmp, 'site')
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=site))
        base = f'http://127.0.0.1:{server.server_port}'
        files = {
            'index.html': f'''<!doctype html><html lang="en"><head><link rel="stylesheet" href="/css/site.css?v=3">
<link rel="icon" href="/favicon.png"></head><body><a href="{base}/about/">About</a>
<img src="/img/a-400.png" srcset="/img/a-400.png 400w, /img/a-800.png 800w" sizes="100vw" alt="">
<div style="height:3000px"></div><img src="/img/lazy.png" loading="lazy" alt=""></body></html>''',
            'about/index.html': '<!doctype html><html><head><link rel="stylesheet" href="/css/site.css"></head><body>'
                                '<a href="/">Home</a><img src="/img/b.png" alt=""></body></html>',
            'css/site.css': '@font-face{font-family:F;src:url(../fonts/f.woff2) format("woff2")}'
                            'body{font-family:F;background:url(/img/bg.png)}',
        }
        for rel, text in files.items():
            os.makedirs(os.path.dirname(os.path.join(site, rel)) or site, exist_ok=True)
            with open(os.path.join(site, rel), 'w') as fh:
                fh.write(text)
        for rel in ('img/a-400.png', 'img/a-800.png', 'img/lazy.png', 'img/b.png', 'img/bg.png', 'favicon.png'):
            os.makedirs(os.path.dirname(os.path.join(site, rel)), exist_ok=True)
            with open(os.path.join(site, rel), 'wb') as fh:
                fh.write(PNG)
        os.makedirs(os.path.join(site, 'fonts'), exist_ok=True)
        with open(os.path.join(site, 'fonts', 'f.woff2'), 'wb') as fh:
            fh.write(b'wOF2fake')
        threading.Thread(target=server.serve_forever, daemon=True).start()
        dest = os.path.join(tmp, 'copy')
        try:
            r = run('scripts/capture-site.mjs', base + '/', dest, '--delay', '0',
                    env={'NODE_PATH': PW, 'CHROME_PATH': CHROME}, timeout=300)
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.startswith('OK capture-site: 2 pages'), r.stdout)
        for rel in ('index.html', 'about/index.html', 'css/site.css', 'fonts/f.woff2', 'img/a-400.png',
                    'img/a-800.png', 'img/lazy.png', 'img/b.png', 'img/bg.png', 'favicon.png'):
            self.assertTrue(os.path.exists(os.path.join(dest, rel)), rel)
        with open(os.path.join(dest, 'index.html')) as fh:
            html = fh.read()
        self.assertNotIn(base, html)
        self.assertIn('href="/about/"', html)
        with open(os.path.join(dest, 'routes.json')) as fh:
            self.assertEqual(sorted(json.load(fh)), ['/', '/about/'])


if __name__ == '__main__':
    unittest.main()
