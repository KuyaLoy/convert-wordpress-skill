import os
import shutil
import signal
import socket
import tempfile
import time
import unittest
import urllib.error
import urllib.request

from helpers import run


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class ServeWP(unittest.TestCase):
    def test_router(self):
        root = tempfile.mkdtemp(prefix='wp-')
        files = {
            'index.php': '<?php echo "WP " . $_SERVER["REQUEST_URI"] . " " . $_SERVER["SCRIPT_NAME"];',
            'wp-admin/index.php': '<?php echo "ADMIN";',
            'wp-content/themes/t/style.css': 'body{color:red}',
            '_plan/SPRINT-PLAN.md': 'private',
            '_setup/.keep': '',
            'handoff.md': 'private',
        }
        for rel, text in files.items():
            os.makedirs(os.path.dirname(os.path.join(root, rel)), exist_ok=True)
            with open(os.path.join(root, rel), 'w') as fh:
                fh.write(text)
        port = free_port()
        r = run('scripts/setup/serve-wp.py', root, '--port', port, '--background')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(os.path.join(root, '_setup', 'serve-wp.pid')) as fh:
            pid = int(fh.read())
        try:
            base = f'http://127.0.0.1:{port}'
            for _ in range(50):
                try:
                    socket.create_connection(('127.0.0.1', port), timeout=0.2).close()
                    break
                except OSError:
                    time.sleep(0.1)
            self.assertEqual(get(base + '/about/team/'), (200, 'WP /about/team/ /index.php'))
            self.assertEqual(get(base + '/'), (200, 'WP / /index.php'))
            self.assertEqual(get(base + '/wp-admin/'), (200, 'ADMIN'))
            self.assertEqual(get(base + '/wp-content/themes/t/style.css'), (200, 'body{color:red}'))
            self.assertEqual(get(base + '/_plan/SPRINT-PLAN.md')[0], 403)
            self.assertEqual(get(base + '/handoff.md')[0], 403)
            self.assertEqual(get(base + '/wp-config.php')[0], 403)
        finally:
            os.kill(pid, signal.SIGTERM)

    def test_pid_never_in_web_root(self):
        root = tempfile.mkdtemp(prefix='wp-')
        with open(os.path.join(root, 'index.php'), 'w') as fh:
            fh.write('<?php echo 1;')
        r = run('scripts/setup/serve-wp.py', root, '--port', free_port(), '--background')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(os.path.exists(os.path.join(root, 'serve-wp.pid')))
        with open(os.path.join(root, '_setup', 'serve-wp.pid')) as fh:
            os.kill(int(fh.read()), signal.SIGTERM)
        self.assertTrue(os.path.exists(os.path.join(root, '_setup', 'serve-wp.log')))

    def test_port_in_use(self):
        root = tempfile.mkdtemp(prefix='wp-')
        with open(os.path.join(root, 'index.php'), 'w') as fh:
            fh.write('<?php echo 1;')
        with socket.socket() as s:
            s.bind(('127.0.0.1', 0))
            s.listen()
            r = run('scripts/setup/serve-wp.py', root, '--port', s.getsockname()[1])
        self.assertEqual(r.returncode, 1)
        self.assertIn('in use', r.stdout + r.stderr)


if __name__ == '__main__':
    unittest.main()
