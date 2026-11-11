import os
import tempfile
import unittest
import zipfile

from helpers import load, run

pkg = load('scripts/launch/package.py', 'launch_package')

GOOD = [
    'index.php',
    'wp-config.php',
    'wp-content/themes/shop/style.css',
    'wp-content/themes/shop/functions.php',
    'wp-content/uploads/2026/01/photo.jpg',
    'dup-installer/dup_descriptors_abc123/db_dumps/database.sql',
    'dup-installer/dup_descriptors_abc123/orig_files/source_site_wpconfig',
]


def make_zip(names):
    fd, p = tempfile.mkstemp(suffix='_archive.zip')
    os.close(fd)
    with zipfile.ZipFile(p, 'w') as z:
        for n in names:
            z.writestr(n, 'x')
    return p


class ArchiveCheck(unittest.TestCase):
    def test_good_archive(self):
        c = pkg.check_archive(make_zip(GOOD), 'shop')
        self.assertEqual(c['entries'], len(GOOD))
        self.assertEqual(c['hits'], [])
        self.assertTrue(c['db'])
        self.assertTrue(c['wpconfig'])

    def test_private_entries_are_found(self):
        bad = [
            '_plan/site.json', '_setup/launch/RUNBOOK.md', '.claude/settings.json', 'tasks/one.md', 'handoff.md',
            'ai-handoff-summary.md', 'BUILD-MAP.md', 'wp-content/debug.log', 'wp-content/uploads/wpcf7_uploads/a.pdf',
            'wp-content/themes/shop/tests/shot.png', 'wp-content/themes/shop/node_modules/x/index.js',
            'wp-content/themes/shop/.git/HEAD',
        ]
        c = pkg.check_archive(make_zip(GOOD + bad), 'shop')
        self.assertEqual(sorted(c['hits']), sorted(bad))

    def test_other_themes_tests_are_not_flagged(self):
        c = pkg.check_archive(make_zip(GOOD + ['wp-content/plugins/x/tests/a.php']), 'shop')
        self.assertEqual(c['hits'], [])

    def test_missing_database_and_wpconfig(self):
        c = pkg.check_archive(make_zip(GOOD[:5]), 'shop')
        self.assertFalse(c['db'])
        self.assertFalse(c['wpconfig'])


class Filters(unittest.TestCase):
    def test_filter_paths_reuse_duplicator_filters(self):
        paths = pkg.filter_paths('C:/sites/shop', 'shop', 'tw')
        self.assertIn('C:/sites/shop/_plan', paths)
        self.assertIn('C:/sites/shop/wp-content/themes/shop/tests', paths)
        self.assertIn('C:/sites/shop/wp-content/themes/shop/tailwind', paths)
        self.assertIn('C:/sites/shop/.claude', paths)
        self.assertFalse(any(p.endswith(';') for p in paths))

    def test_password_file_must_be_outside_the_project(self):
        tmp = tempfile.mkdtemp()
        self.assertFalse(pkg.outside(os.path.join(tmp, 'x.txt'), tmp))
        self.assertTrue(pkg.outside(os.path.join(os.path.dirname(tmp), 'x.txt'), tmp))


class Cli(unittest.TestCase):
    def test_usage_exit_code(self):
        r = run('scripts/launch/package.py', tempfile.mkdtemp(), 'shop')
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertTrue(r.stdout.startswith('FAIL package:'), r.stdout)

    def test_dry_run_without_wordpress_build(self):
        root = tempfile.mkdtemp()
        os.makedirs(os.path.join(root, 'wp-content', 'themes', 'shop', 'tests'))
        os.makedirs(os.path.join(root, '_plan'))
        open(os.path.join(root, 'wp-load.php'), 'w').close()
        open(os.path.join(root, 'handoff.md'), 'w').close()
        r = run('scripts/launch/package.py', root, 'shop', '--dry-run', '--wp', 'missing-wp-command-for-test')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('WP-CLI did not start', r.stdout)
        r = run('scripts/launch/package.py', root, 'shop', '--dry-run', env={'PATH': ''})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        first = r.stdout.splitlines()[0]
        self.assertTrue(first.startswith('OK package: dry run, 2 folders and 1 files'), first)
        self.assertFalse(os.path.exists(os.path.join(root, '_setup')))


if __name__ == '__main__':
    unittest.main()
