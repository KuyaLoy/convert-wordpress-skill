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


class AcfLicenceFromProfile(unittest.TestCase):
    """0.9.2: the profile's acf_pro_license goes into LOCAL wp-config files only, active, and is never printed."""

    DUMMY = 'DUMMY-acf-key-0123456789'

    def site(self, profile_key=None):
        tmp = tempfile.mkdtemp()
        site = os.path.join(tmp, 'site')
        os.makedirs(site)
        with open(os.path.join(site, 'wp-config-sample.php'), 'w', encoding='utf-8') as fh:
            fh.write(SAMPLE)
        prof = os.path.join(tmp, 'profile.local.json')
        with open(prof, 'w', encoding='utf-8') as fh:
            fh.write('{"acf_pro_license": "%s"}' % (profile_key or ''))
        return site, prof

    def config(self, site):
        with open(os.path.join(site, 'wp-config.php'), encoding='utf-8') as fh:
            return fh.read()

    def test_key_written_active_and_never_printed(self):
        site, prof = self.site(self.DUMMY)
        r = run('scripts/setup/make-wp-config.py', site, '--db', 'db_test', '--profile', prof)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(f"\ndefine( 'ACF_PRO_LICENSE', '{self.DUMMY}' );", self.config(site))
        self.assertNotIn(self.DUMMY, r.stdout + r.stderr)
        self.assertIn('ACF PRO licence active (from the profile, not shown)', r.stdout)

    def test_no_key_keeps_the_commented_line(self):
        site, prof = self.site('')
        r = run('scripts/setup/make-wp-config.py', site, '--db', 'db_test', '--profile', prof)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        text = self.config(site)
        self.assertIn("// define( 'ACF_PRO_LICENSE', '' );", text)
        self.assertNotRegex(text, r"(?m)^define\( 'ACF_PRO_LICENSE'")

    def test_not_written_for_a_live_environment(self):
        site, prof = self.site(self.DUMMY)
        r = run('scripts/setup/make-wp-config.py', site, '--db', 'db_test', '--env', 'production', '--profile', prof)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn(self.DUMMY, self.config(site))

    def test_reruns_refresh_the_profile_key_and_keep_a_pasted_one(self):
        site, prof = self.site(self.DUMMY)
        run('scripts/setup/make-wp-config.py', site, '--db', 'db_test', '--profile', prof)
        with open(prof, 'w', encoding='utf-8') as fh:
            fh.write('{"acf_pro_license": "DUMMY-second-key-987654"}')
        r = run('scripts/setup/make-wp-config.py', site, '--existing', '--profile', prof)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        text = self.config(site)
        self.assertIn("'DUMMY-second-key-987654'", text)
        self.assertNotIn(self.DUMMY, text)
        self.assertNotIn('DUMMY-second', r.stdout + r.stderr)
        # A key the developer pasted into the block (the commented line made active) survives a rerun.
        site2, empty = self.site('')
        run('scripts/setup/make-wp-config.py', site2, '--db', 'db_test', '--profile', empty)
        cfg = os.path.join(site2, 'wp-config.php')
        text = self.config(site2).replace("// define( 'ACF_PRO_LICENSE', '' );", "define( 'ACF_PRO_LICENSE', 'PASTED-by-hand-555' );")
        with open(cfg, 'w', encoding='utf-8') as fh:
            fh.write(text)
        r = run('scripts/setup/make-wp-config.py', site2, '--existing', '--profile', empty)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("define( 'ACF_PRO_LICENSE', 'PASTED-by-hand-555' );", self.config(site2))
        self.assertEqual(self.config(site2).count('ACF_PRO_LICENSE'), 1)
        self.assertIn('kept as it was', r.stdout)
