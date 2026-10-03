import functools
import http.server
import json
import os
import struct
import tempfile
import threading
import unittest
import zipfile
from unittest import mock

from helpers import load, run

gs = load('scripts/get-source.py', 'get_source')


def make_zip(path, files):
    with zipfile.ZipFile(path, 'w') as z:
        for name, data in files.items():
            z.writestr(name, data)
    return path


def read(p):
    with open(p, encoding='utf-8') as fh:
        return fh.read()


def put(p, data):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb' if isinstance(data, bytes) else 'w') as fh:
        fh.write(data)


class Classify(unittest.TestCase):
    def test_kinds(self):
        tmp = tempfile.mkdtemp()
        z = make_zip(os.path.join(tmp, 'a.zip'), {'index.html': '<h1>x</h1>'})
        cases = {
            'https://github.com/acme/site': 'github',
            'https://github.com/acme/site.git': 'github',
            'https://github.com/acme/site/tree/dev/web': 'github',
            'git@github.com:acme/site.git': 'git',
            'https://gitlab.com/acme/site': 'git',
            'https://www.acme-shop.com/': 'website',
            'http://acme-shop.com/about/': 'website',
            'https://files.example.com/site.zip?dl=1': 'zip-url',
            z: 'zip',
            tmp: 'folder',
            '/no/such/thing': None,
        }
        for src, kind in cases.items():
            self.assertEqual(gs.classify(src)[0], kind, src)

    def test_github_tree_link(self):
        kind, info = gs.classify('https://github.com/acme/site/tree/dev/apps/web')
        self.assertEqual(info['repo'], 'https://github.com/acme/site')
        self.assertEqual(info['branch'], 'dev')
        self.assertEqual(info['subdir'], 'apps/web')

    def test_redact(self):
        self.assertEqual(gs.redact('https://bob:ghp_SECRET123@github.com/acme/site'), 'https://github.com/acme/site')
        self.assertEqual(gs.redact('https://x.com/s.zip?token=abc&a=1'), 'https://x.com/s.zip')
        self.assertEqual(gs.redact('https://github.com/acme/site'), 'https://github.com/acme/site')

    def test_cross_drive_is_not_inside(self):
        with mock.patch('os.path.commonpath', side_effect=ValueError('different drives')):
            self.assertFalse(gs.inside('C:/sites/src', 'D:/copies/src-source'))

    def test_slugs(self):
        self.assertEqual(gs.slug_for('website', 'https://www.acme-shop.com/about/'), 'acme-shop')
        self.assertEqual(gs.slug_for('github', 'https://github.com/acme/My_Site'), 'my-site')


class Copies(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='gs-')

    def test_folder_secrets_and_skips(self):
        src = os.path.join(self.tmp, 'shop')
        for rel, text in {'index.html': 'x', 'config.php': '<?php', 'db/backup.sql': 'x', '.env': 'A=1',
                          '.env.example': 'A=', 'node_modules/x/i.js': 'x', 'creds/credentials.json': '{}'}.items():
            put(os.path.join(src, rel), text)
        r = run('scripts/get-source.py', src, '--into', os.path.join(self.tmp, 'www'))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        dest = os.path.join(self.tmp, 'www', 'shop-source')
        info = json.loads(read(os.path.join(dest, '.source.json')))
        self.assertFalse(os.path.exists(os.path.join(dest, 'node_modules')))
        for secret in ('.env', 'config.php', 'db/backup.sql', 'creds/credentials.json'):
            self.assertIn(secret, info['secret_files'])
        self.assertNotIn('.env.example', info['secret_files'])
        self.assertTrue(r.stdout.startswith('OK get-source'), r.stdout)

    def test_zip_unwrapped(self):
        z = make_zip(os.path.join(self.tmp, 'site.zip'), {'site/index.html': 'x', 'site/css/a.css': 'b{}'})
        r = run('scripts/get-source.py', z, os.path.join(self.tmp, 'out'))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(os.path.exists(os.path.join(self.tmp, 'out', 'css', 'a.css')))

    def test_unsafe_zip(self):
        z = make_zip(os.path.join(self.tmp, 'bad.zip'), {'../evil.txt': 'x'})
        r = run('scripts/get-source.py', z, os.path.join(self.tmp, 'out'))
        self.assertEqual(r.returncode, 1)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, 'evil.txt')))

    def test_password_zip(self):
        z = make_zip(os.path.join(self.tmp, 'locked.zip'), {'index.html': 'x'})
        with open(z, 'rb') as fh:
            data = bytearray(fh.read())
        # set the "encrypted" flag in the local header and in the central directory entry
        data[6:8] = struct.pack('<H', struct.unpack('<H', data[6:8])[0] | 1)
        cd = data.find(b'PK\x01\x02')
        data[cd + 8:cd + 10] = struct.pack('<H', struct.unpack('<H', data[cd + 8:cd + 10])[0] | 1)
        put(z, bytes(data))
        r = run('scripts/get-source.py', z, os.path.join(self.tmp, 'out'))
        self.assertEqual(r.returncode, 1)
        self.assertIn('password', (r.stdout + r.stderr).lower())

    def test_broken_zip(self):
        z = os.path.join(self.tmp, 'broken.zip')
        put(z, b'not a zip at all')
        r = run('scripts/get-source.py', z, os.path.join(self.tmp, 'out'))
        self.assertEqual(r.returncode, 1)
        self.assertIn('not a valid zip', (r.stdout + r.stderr).lower())

    def test_wordpress_backup_stops(self):
        src = os.path.join(self.tmp, 'wpsite')
        for rel in ('wp-config.php', 'wp-includes/version.php', 'wp-content/themes/x/style.css'):
            put(os.path.join(src, rel), 'x')
        r = run('scripts/get-source.py', src, os.path.join(self.tmp, 'out'))
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        self.assertIn('already a WordPress site', r.stdout + r.stderr)

    def test_dry_run_hides_token_and_shows_size(self):
        z = make_zip(os.path.join(self.tmp, 'site.zip'), {'index.html': 'x' * 5000})
        r = run('scripts/get-source.py', z, os.path.join(self.tmp, 'out'), '--dry-run')
        self.assertEqual(r.returncode, 0)
        self.assertIn('KB', r.stdout)
        r = run('scripts/get-source.py', 'https://bob:ghp_SECRET123@github.com/acme/site', '--dry-run')
        self.assertNotIn('ghp_SECRET123', r.stdout + r.stderr)

    def test_github_without_git(self):
        srv = os.path.join(self.tmp, 'srv')
        os.makedirs(os.path.join(srv, 'acme', 'site', 'archive'))
        make_zip(os.path.join(srv, 'acme', 'site', 'archive', 'HEAD.zip'),
                 {'site-main/index.html': '<h1>hi</h1>', 'site-main/about/index.html': 'a'})
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass
        handler = functools.partial(Quiet, directory=srv)
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            empty = os.path.join(self.tmp, 'nobin')
            os.makedirs(empty)
            r = run('scripts/get-source.py', 'https://github.com/acme/site', os.path.join(self.tmp, 'out'),
                    env={'PATH': empty, 'GET_SOURCE_ZIP_BASE': f'http://127.0.0.1:{server.server_port}'})
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(os.path.exists(os.path.join(self.tmp, 'out', 'about', 'index.html')))
        info = json.loads(read(os.path.join(self.tmp, 'out', '.source.json')))
        self.assertEqual(info['kind'], 'github-zip')


if __name__ == '__main__':
    unittest.main()
