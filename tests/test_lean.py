"""0.9: the intake in one call (start.py), setup in one call (setup.py), one PLAN.md, one check per section."""
import json
import os
import shutil
import tempfile
import unittest

from helpers import path, run


def read(p):
    with open(p, encoding='utf-8') as fh:
        return fh.read()


def write(p, text):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as fh:
        fh.write(text)


def static_site(folder):
    write(os.path.join(folder, 'index.html'), '<!doctype html><html lang="en"><head><title>Home</title></head><body>'
          '<header><a href="/">Home</a></header><main><section class="hero"><h1>Hi</h1></section></main>'
          '<footer>f</footer></body></html>')
    write(os.path.join(folder, 'about', 'index.html'), '<!doctype html><html><head><title>About</title></head>'
          '<body><main><h1>About</h1></main></body></html>')
    write(os.path.join(folder, '.env'), 'SECRET=1\n')


class StartPy(unittest.TestCase):
    def test_intake_in_one_call(self):
        tmp = tempfile.mkdtemp()
        src = os.path.join(tmp, 'given')
        static_site(src)
        www = os.path.join(tmp, 'www')
        root = os.path.join(www, 'shop')
        r = run('scripts/start.py', src, '--root', root, '--name', 'Corner Shop')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        lines = r.stdout.strip().splitlines()
        self.assertTrue(lines[0].startswith('OK start:'), r.stdout)
        self.assertLessEqual(len(lines), 8, r.stdout)
        for f in ('handoff.md', 'ai-handoff-summary.md', '_plan/analyze.json', '_plan/site.json', '_plan/analyze.txt'):
            self.assertTrue(os.path.exists(os.path.join(root, f)), f)
        self.assertTrue(os.path.exists(os.path.join(www, 'given-source', '.source.json')))
        self.assertIn('.env', r.stdout)  # the secret file is named, never read
        self.assertIn('stack ', r.stdout)
        # Again with the copy as the source: the copy is kept, the study runs again.
        r = run('scripts/start.py', os.path.join(www, 'given-source'), '--root', root)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('kept', r.stdout)

    def test_dry_run_writes_nothing(self):
        tmp = tempfile.mkdtemp()
        src = os.path.join(tmp, 'given')
        static_site(src)
        root = os.path.join(tmp, 'www', 'shop')
        r = run('scripts/start.py', src, '--root', root, '--dry-run')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(os.path.exists(root))
        self.assertTrue(r.stdout.startswith('OK start: dry run'))

    def test_missing_doctor_json(self):
        r = run('scripts/start.py', '.', '--root', tempfile.mkdtemp(), '--env', 'nope.json')
        self.assertEqual(r.returncode, 2)
        self.assertIn('FAIL start', r.stdout)


class SetupPy(unittest.TestCase):
    def site(self, **kw):
        tmp = tempfile.mkdtemp()
        site = {'wp_root': os.path.join(tmp, 'shop'), 'local_host': 'shop.test', 'site_name': 'Corner Shop',
                'site_dir': 'shop', 'wordpress': 'download', 'serve': 'vhost'}
        site.update(kw)
        p = os.path.join(tmp, 'site.json')
        write(p, json.dumps(site))
        return p

    def test_dry_run_lists_the_steps(self):
        r = run('scripts/setup/setup.py', self.site(), '--dry-run')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('OK setup: dry run', r.stdout)
        for step in ('database: db_shop', 'wordpress: download', 'wp-config: new, database db_shop', 'install: install-wp.py http://shop.test'):
            self.assertIn(step, r.stdout)
        self.assertNotIn('server:', r.stdout)

    def test_serve_wp_and_existing(self):
        sj = self.site(local_host='localhost:8099', serve='serve-wp', wordpress='existing')
        root = json.loads(read(sj))['wp_root']
        write(os.path.join(root, 'wp-config.php'), "<?php\ndefine( 'DB_HOST', 'db' );\n")  # the local app's own
        r = run('scripts/setup/setup.py', sj, '--dry-run')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('server: serve-wp.py on port 8099', r.stdout)
        self.assertNotIn('database:', r.stdout)  # that wp-config already has its database
        self.assertIn('wp-config: --existing, --no-cron', r.stdout)

    def test_new_config_creates_the_database(self):
        r = run('scripts/setup/setup.py', self.site(wordpress='existing'), '--dry-run')
        self.assertIn('database: db_shop', r.stdout)

    def test_refuses_a_live_address(self):
        r = run('scripts/setup/setup.py', self.site(local_host='www.cornershop.example.org'), '--dry-run')
        self.assertEqual(r.returncode, 2)
        self.assertIn('not a local address', r.stdout)


class OnePlan(unittest.TestCase):
    def test_plan_md_replaces_three_documents(self):
        tmp = tempfile.mkdtemp()
        root = os.path.join(tmp, 'shop')
        site = json.loads(read(path('assets', 'site.example.json')))
        site.update(site_name='Corner Shop', domain='cornershop.example.org', wp_root=root, local_host='shop.test',
                    site_dir='shop', theme='shop', prefix='shop', key='cs', starter='tw')
        write(os.path.join(root, '_plan', 'site.json'), json.dumps(site))
        write(os.path.join(root, '_plan', 'analyze.json'), json.dumps(
            {'stack': 'static-html', 'routes': ['/', '/about/'], 'private_files': ['.env'],
             'golden_master': 'serve the folder unchanged'}))
        r = run('scripts/new-site.py', os.path.join(root, '_plan', 'site.json'), '--plan-only')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        plan = os.path.join(root, '_plan')
        names = os.listdir(plan)
        self.assertIn('PLAN.md', names)
        for gone in ('BUILD-PLAN.md', 'ARCHITECTURE.md', 'SOURCE-NOTES.md'):
            self.assertNotIn(gone, names)
        for kept in ('CONTENT-MODEL.md', 'OLD-SITE-URLS.md'):
            self.assertIn(kept, names)
        text = read(os.path.join(plan, 'PLAN.md'))
        self.assertIn('| Stack | static-html |', text)
        self.assertIn('| Routes | 2: /, /about/ |', text)
        self.assertIn('From analyze-source.py: serve the folder unchanged', text)
        self.assertIn('`.env`', text)
        self.assertNotIn('kit:secrets', text)
        self.assertNotIn('{{', text)
        self.assertNotIn('starter:', text)
        self.assertIn('the _tw project', text)
        self.assertIn('tools', os.listdir(plan))
        self.assertTrue(os.path.exists(os.path.join(plan, 'tools', 'setup', 'setup.py')))


class SectionCheck(unittest.TestCase):
    def test_domdiff_takes_a_selector(self):
        tmp = tempfile.mkdtemp()
        a, b = os.path.join(tmp, 'a.html'), os.path.join(tmp, 'b.html')
        write(a, '<main><section class="hero"><h1>Hi</h1></section><section class="cta"><p>x</p></section></main>')
        write(b, '<main><section class="hero"><h1>Hi</h1></section><section class="cta"><p>y</p></section></main>')
        r = run('scripts/parity/domdiff.py', a, b, 'section.hero')
        self.assertEqual(r.returncode, 0, r.stdout)
        r = run('scripts/parity/domdiff.py', a, b, '.cta')
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn('DIFF  .cta', r.stdout)

    @unittest.skipUnless(shutil.which('php'), 'php not on PATH')
    def test_check_section_php_and_duplicates(self):
        theme = os.path.join(tempfile.mkdtemp(), 'shop')
        parity = os.path.join(theme, 'tests', 'parity')
        shutil.copytree(path('scripts', 'parity'), parity, ignore=shutil.ignore_patterns('__pycache__', 'node_modules', 'report'))
        write(os.path.join(theme, 'includes', 'a.php'), "<?php\nfunction shop_one() {}\n")
        write(os.path.join(theme, 'includes', 'b.php'), "<?php\nfunction shop_one() {}\n")
        write(os.path.join(theme, 'includes', 'c.php'), "<?php\nfunction shop_two( {\n")
        cfg = json.loads(read(os.path.join(parity, 'parity.config.json')))
        cfg['wp'] = 'http://shop.test'
        write(os.path.join(parity, 'parity.config.json'), json.dumps(cfg))
        import subprocess
        import sys
        r = subprocess.run([sys.executable, os.path.join(parity, 'check-section.py'), '/', '--skip', 'pixel,dom,phpcs'],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout)
        first = r.stdout.splitlines()[0]
        self.assertTrue(first.startswith('FAIL check-section /:'), first)
        self.assertIn('php -l 2/3', first)
        self.assertIn('duplicates 1', first)
        self.assertIn('duplicate function shop_one', r.stdout)
        self.assertTrue(os.path.exists(os.path.join(parity, 'report', 'check-section.log')))
        r = subprocess.run([sys.executable, os.path.join(parity, 'check-section.py'), 'C:/Program Files/Git/about/'],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn('MSYS_NO_PATHCONV', r.stdout)


if __name__ == '__main__':
    unittest.main()


class Quality091(unittest.TestCase):
    """0.9.1: Barebones gets lint scripts and configs, its jQuery sample goes aside, the build keeps blocks/."""

    def test_barebones_lint_and_escaping_helpers(self):
        root = os.path.join(tempfile.mkdtemp(), 'shop')
        theme = os.path.join(root, 'wp-content', 'themes', 'shop')
        write(os.path.join(root, 'wp-includes', 'version.php'), "<?php $wp_version = '7.1';\n")
        write(os.path.join(theme, 'style.css'), '/*\nTheme Name: Barebones\nText Domain: barebones\n*/\n')
        write(os.path.join(theme, 'includes', 'shortcodes.php'), '<?php\n')
        write(os.path.join(theme, 'blocks', 'demo', 'block.json'), '{}')
        write(os.path.join(theme, 'assets', 'scripts', 'scripts.js'), '$ = jQuery;\n')
        write(os.path.join(theme, 'package.json'), json.dumps({'type': 'module', 'scripts': {'build': 'vite build'}}))
        site = json.loads(read(path('assets', 'site.example.json')))
        site.update(site_name='Corner Shop', domain='cornershop.example.org', wp_root=root, local_host='shop.test',
                    site_dir='shop', theme='shop', prefix='shop', key='cs', starter='barebones')
        write(os.path.join(root, '_plan', 'site.json'), json.dumps(site))
        r = run('scripts/new-site.py', os.path.join(root, '_plan', 'site.json'))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        pkg = json.loads(read(os.path.join(theme, 'package.json')))
        self.assertIn('lint', pkg['scripts'])
        self.assertIn('eslint', pkg['devDependencies'])
        for f in ('eslint.config.js', 'prettier.config.js', '.prettierignore', os.path.join('blocks', '.gitkeep')):
            self.assertTrue(os.path.exists(os.path.join(theme, f)), f)
        self.assertNotIn('jQuery', read(os.path.join(theme, 'assets', 'scripts', 'scripts.js')))
        self.assertIn('*.css', read(os.path.join(theme, '.prettierignore')))  # copied static CSS stays byte for byte
        pcs = read(os.path.join(theme, 'phpcs.xml.dist'))
        self.assertIn('customAutoEscapedFunctions', pcs)
        self.assertIn('<element value="shop_img"/>', pcs)
