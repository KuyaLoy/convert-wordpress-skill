import glob
import os
import shutil
import subprocess
import tempfile
import unittest

from helpers import run

SAMPLE = """<?php
define( 'DB_NAME', 'database_name_here' );
define( 'DB_USER', 'username_here' );
define( 'DB_PASSWORD', 'password_here' );
define( 'DB_HOST', 'localhost' );
define( 'AUTH_KEY',         'put your unique phrase here' );
$table_prefix = 'wp_';
define( 'WP_DEBUG', false );

/* That's all, stop editing! Happy publishing. */
if ( ! defined( 'ABSPATH' ) ) {
	define( 'ABSPATH', __DIR__ . '/' );
}
require_once ABSPATH . 'wp-settings.php';
"""

LOCAL_APP = """<?php
define( 'DB_NAME', 'local' );
define( 'DB_USER', 'root' );
define( 'DB_PASSWORD', 'root' );
define( 'DB_HOST', 'localhost' );
define( 'AUTH_KEY', 'kept-salt-123' );
$table_prefix = 'wp_';
define( 'WP_DEBUG', false );
define( 'WP_ENVIRONMENT_TYPE', 'local' );

/* That's all, stop editing! Happy publishing. */
if ( ! defined( 'ABSPATH' ) ) {
	define( 'ABSPATH', __DIR__ . '/' );
}
require_once ABSPATH . 'wp-settings.php';
"""


def read(p):
    with open(p, encoding='utf-8') as fh:
        return fh.read()


class WpConfig(unittest.TestCase):
    def setUp(self):
        self.site = tempfile.mkdtemp(prefix='wpc-')

    def write(self, name, text):
        with open(os.path.join(self.site, name), 'w', encoding='utf-8') as fh:
            fh.write(text)

    def test_existing_twice(self):
        self.write('wp-config.php', LOCAL_APP)
        for _ in range(2):
            r = run('scripts/setup/make-wp-config.py', self.site, '--existing')
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        s = read(os.path.join(self.site, 'wp-config.php'))
        self.assertEqual(s.count('/* kit:settings start */'), 1)
        self.assertEqual(s.count('/* kit:settings end */'), 1)
        for kept in ("define( 'DB_NAME', 'local' );", "define( 'DB_PASSWORD', 'root' );", 'kept-salt-123'):
            self.assertIn(kept, s)
        # the app's own WP_DEBUG and WP_ENVIRONMENT_TYPE are switched off, so each constant is defined once
        self.assertEqual(s.count("\ndefine( 'WP_DEBUG',"), 1)
        self.assertEqual(s.count("\ndefine( 'WP_ENVIRONMENT_TYPE',"), 1)
        self.assertIn("// kit (was): define( 'WP_DEBUG', false );", s)
        self.assertLess(s.index('kit:settings end'), s.index("That's all, stop editing"))
        self.assertGreaterEqual(len(glob.glob(os.path.join(self.site, '_setup', 'backups', 'wp-config.php.*'))), 1)
        if shutil.which('php'):
            self.assertEqual(subprocess.run(['php', '-l', os.path.join(self.site, 'wp-config.php')],
                                            capture_output=True).returncode, 0)

    def test_new_config_has_markers(self):
        self.write('wp-config-sample.php', SAMPLE)
        r = run('scripts/setup/make-wp-config.py', self.site, '--db', 'db_shop', '--no-cron')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        s = read(os.path.join(self.site, 'wp-config.php'))
        self.assertIn('/* kit:settings start */', s)
        self.assertIn("define( 'DISABLE_WP_CRON', true );", s)
        self.assertIn("define( 'DB_NAME', 'db_shop' );", s)
        self.assertNotIn('put your unique phrase here', s)

    def test_existing_needs_a_config(self):
        r = run('scripts/setup/make-wp-config.py', self.site, '--existing')
        self.assertNotEqual(r.returncode, 0)


if __name__ == '__main__':
    unittest.main()
