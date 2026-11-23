"""0.9.11: the default plugin stack per environment: plugin-check.py, the "where" key, tracking through the plugin
only, Duplicator deleted after live QA, and the RUNBOOK's live list."""
import json
import os
import tempfile
import unittest

from helpers import path, run

PROFILE = {
    'tracking': {'plugin': 'Example Tracker'},
    'extra_plugins': [
        {'name': 'Example Tracker', 'required': True, 'where': 'live', 'zip': 'tracker'},
        {'name': 'Example Bridge', 'slug': 'example-bridge-wp', 'required': True, 'where': 'live', 'zip': 'bridge'},
        {'name': 'Shared Helper', 'required': True, 'where': 'all'},
        {'name': 'Sometimes Plugin', 'optional': True},
    ],
}
LIVE = [('advanced-custom-fields-pro', 'active'), ('contact-form-7', 'active'), ('wordpress-seo', 'active'),
        ('redirection', 'active'), ('contact-form-cfdb7', 'active'), ('webp-converter-for-media', 'active'),
        ('litespeed-cache', 'active'), ('example-tracker', 'active'), ('example-bridge-wp', 'active'),
        ('shared-helper', 'active'), ('duplicator-pro', 'active'), ('example-core', 'must-use')]
STAGING = [('advanced-custom-fields-pro', 'active'), ('contact-form-7', 'active'), ('wordpress-seo', 'active'),
           ('shared-helper', 'active'), ('duplicator-pro', 'inactive')]


def write(p, text):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as fh:
        fh.write(text)


def project(site=None, profile=None):
    tmp = tempfile.mkdtemp()
    s = {'site_name': 'Corner Shop', 'redirects': True}
    s.update(site or {})
    write(os.path.join(tmp, '_plan', 'site.json'), json.dumps(s))
    write(os.path.join(tmp, 'profile.json'), json.dumps(PROFILE if profile is None else profile))
    return tmp


def plugins(tmp, rows, name='plugins.json', drop=(), add=()):
    data = [{'name': n, 'status': st} for n, st in rows if n not in drop] + [{'name': n, 'status': st} for n, st in add]
    p = os.path.join(tmp, name)
    write(p, json.dumps(data))
    return p


def check(tmp, env, lst, *more):
    return run('scripts/report/plugin-check.py', os.path.join(tmp, '_plan', 'site.json'), '--env', env,
               '--profile', os.path.join(tmp, 'profile.json'), '--list', lst, *more)


class LiveList(unittest.TestCase):
    def test_the_live_list_as_planned(self):
        tmp = project()
        r = check(tmp, 'live', plugins(tmp, LIVE))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(r.stdout.splitlines()[0], 'OK plugin-check: live, 11 plugins as planned')

    def test_missing_inactive_and_extra_are_each_a_fail(self):
        tmp = project()
        lst = plugins(tmp, LIVE, drop=('contact-form-cfdb7', 'litespeed-cache'),
                      add=(('hello-dolly', 'inactive'), ('litespeed-cache', 'inactive')))
        r = check(tmp, 'live', lst)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertTrue(r.stdout.startswith('FAIL plugin-check: live, 3 not as planned'), r.stdout)
        self.assertIn('missing: Contact Form CFDB7 (contact-form-cfdb7)', r.stdout)
        self.assertIn('inactive: LiteSpeed Cache: activate it', r.stdout)
        self.assertIn('not on the list: hello-dolly (inactive)', r.stdout)

    def test_a_live_only_profile_plugin_missing_on_live(self):
        tmp = project()
        r = check(tmp, 'live', plugins(tmp, LIVE, drop=('example-bridge-wp',)))
        self.assertIn('missing: Example Bridge (example-bridge-wp)', r.stdout)

    def test_redirection_only_with_redirects(self):
        tmp = project({'redirects': False})
        r = check(tmp, 'live', plugins(tmp, LIVE))
        self.assertIn('not on the list: redirection (active)', r.stdout)
        r = check(tmp, 'live', plugins(tmp, LIVE, drop=('redirection',)))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_redirects_planned_in_the_old_urls_file(self):
        tmp = project({'redirects': None})
        write(os.path.join(tmp, '_plan', 'OLD-SITE-URLS.md'), '| Old | Status | Target |\n|---|---|---|\n'
              '| /old-page/ | 301 | /new-page/ |\n')
        r = check(tmp, 'live', plugins(tmp, LIVE, drop=('redirection',)))
        self.assertIn('missing: Redirection (redirection)', r.stdout)

    def test_the_task_adds_a_plugin_and_another_cache(self):
        tmp = project({'task_plugins': ['WooCommerce'], 'cache_plugin': 'WP Rocket'})
        lst = plugins(tmp, LIVE, drop=('litespeed-cache',), add=(('woocommerce', 'active'), ('wp-rocket', 'active')))
        r = check(tmp, 'live', lst)
        self.assertEqual(r.returncode, 0, r.stdout)
        tmp = project({'cache_plugin': 'none'})
        r = check(tmp, 'live', plugins(tmp, LIVE, drop=('litespeed-cache',)))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_plugins_screen_lines_and_csv(self):
        tmp = project()
        lines = os.path.join(tmp, 'screen.txt')
        names = ['Advanced Custom Fields PRO', 'Contact Form 7', 'Yoast SEO', 'Redirection', 'Contact Form CFDB7',
                 'Converter for Media', 'LiteSpeed Cache', 'Example Tracker', 'Example Bridge', 'Shared Helper']
        write(lines, '\n'.join(names) + '\nDuplicator Pro inactive\n')
        r = check(tmp, 'live', lines)
        self.assertEqual(r.returncode, 0, r.stdout)  # names as the Plugins screen shows them
        write(lines, '\n'.join(names[1:]) + '\nHello Dolly\n')
        r = check(tmp, 'live', lines)
        self.assertIn('missing: ACF PRO (advanced-custom-fields-pro)', r.stdout)
        self.assertIn('not on the list: hello-dolly (active)', r.stdout)
        csv_list = os.path.join(tmp, 'plugins.csv')
        write(csv_list, 'name,status,update,version\n' + '\n'.join(f'{n},{s},none,1.0' for n, s in LIVE) + '\n')
        r = check(tmp, 'live', csv_list)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_expected_prints_the_plan(self):
        tmp = project()
        r = run('scripts/report/plugin-check.py', os.path.join(tmp, '_plan', 'site.json'), '--env', 'staging',
                '--profile', os.path.join(tmp, 'profile.json'), '--expected')
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(r.stdout.startswith('OK plugin-check: staging needs 4: ACF PRO, Contact Form 7, Yoast SEO, '
                                            'Shared Helper'), r.stdout)
        self.assertIn('elsewhere: Contact Form CFDB7 (not here: live only)', r.stdout)
        self.assertIn('elsewhere: Example Tracker (not here: live only)', r.stdout)


class Staging(unittest.TestCase):
    def test_staging_has_none_of_the_live_list(self):
        tmp = project()
        r = check(tmp, 'staging', plugins(tmp, STAGING))
        self.assertEqual(r.returncode, 0, r.stdout)
        lst = plugins(tmp, STAGING, add=(('contact-form-cfdb7', 'active'), ('example-tracker', 'inactive'),
                                         ('litespeed-cache', 'active')))
        r = check(tmp, 'staging', lst)
        self.assertEqual(r.returncode, 1, r.stdout)
        for name in ('Contact Form CFDB7', 'Example Tracker', 'LiteSpeed Cache'):
            self.assertIn(f'live only: {name} is on staging: remove it', r.stdout)

    def test_redirection_allowed_on_staging_when_needed(self):
        tmp = project()
        r = check(tmp, 'staging', plugins(tmp, STAGING, add=(('redirection', 'active'),)))
        self.assertEqual(r.returncode, 0, r.stdout)
        tmp = project({'redirects': False})
        r = check(tmp, 'staging', plugins(tmp, STAGING, add=(('redirection', 'active'),)))
        self.assertIn('not on the list: redirection', r.stdout)

    def test_acf_pro_and_scf_together(self):
        tmp = project()
        r = check(tmp, 'local', plugins(tmp, STAGING, add=(('secure-custom-fields', 'active'),)))
        self.assertIn('ACF PRO and Secure Custom Fields are both installed', r.stdout)


class DuplicatorCleanUp(unittest.TestCase):
    def test_duplicator_allowed_until_done(self):
        tmp = project()
        r = check(tmp, 'live', plugins(tmp, LIVE), '--done')
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn('Duplicator still installed (duplicator-pro)', r.stdout)
        inactive = plugins(tmp, LIVE, drop=('duplicator-pro',), add=(('duplicator-pro', 'inactive'),))
        self.assertIn('Duplicator still installed', check(tmp, 'live', inactive, '--done').stdout)
        r = check(tmp, 'live', plugins(tmp, LIVE, drop=('duplicator-pro',)), '--done')
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(r.stdout.splitlines()[0], 'OK plugin-check: live, 10 plugins as planned, Duplicator gone')

    def test_leftover_files(self):
        tmp = project()
        listing = os.path.join(tmp, 'files.txt')
        write(listing, '/home/x/public_html:\n.\n..\nindex.php\nwp-content\n20261123_site_installer.php\n'
              '/home/x/public_html/wp-content:\nplugins\nbackups-dup-pro\n')
        lst = plugins(tmp, LIVE, drop=('duplicator-pro',))
        r = check(tmp, 'live', lst, '--files', listing)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn('leftover: 20261123_site_installer.php', r.stdout)
        self.assertNotIn('backups-dup-pro', r.stdout)  # the backups folder may stay until the clean-up
        r = check(tmp, 'live', lst, '--files', listing, '--done')
        self.assertIn('leftover: backups-dup-pro: the Duplicator backups folder, delete it', r.stdout)
        write(listing, '/home/x/public_html:\nindex.php\nwp-content\n/home/x/public_html/wp-content:\nplugins\n')
        r = check(tmp, 'live', lst, '--files', listing, '--done')
        self.assertEqual(r.returncode, 0, r.stdout)


class TrackingPlugin(unittest.TestCase):
    def theme(self, gtm, field):
        root = tempfile.mkdtemp()
        theme = os.path.join(root, 'wp-content', 'themes', 'acme')
        guard = "<?php\n/**\n * File.\n */\n\ndefined( 'ABSPATH' ) || exit;\n"
        write(os.path.join(theme, 'functions.php'), guard + "require __DIR__ . '/includes/config.php';\n")
        write(os.path.join(theme, 'includes', 'config.php'), guard + (
            "function acme_gtm() {\n\techo '<script src=\"https://www.googletagmanager.com/gtm.js?id=GTM-AB12CD3\">"
            "</script>';\n}\nadd_action( 'wp_head', 'acme_gtm', 0 );\n" if gtm else '// GTM-XXXXXXX example\n'))
        fields = [{'label': 'Title', 'name': 'title', 'type': 'text', 'instructions': 'The big line at the top.'}]
        if field:
            fields.append({'label': 'Tag Manager', 'name': 'gtm_id', 'type': 'text', 'instructions': 'The code.'})
        write(os.path.join(theme, 'acf-json', 'group_acme.json'), json.dumps({'title': 'Settings', 'fields': fields}))
        os.makedirs(os.path.join(root, '_setup', 'launch'))
        return root

    def test_the_theme_has_no_tracking_of_its_own(self):
        prof = os.path.join(tempfile.mkdtemp(), 'profile.json')
        write(prof, json.dumps(PROFILE))
        root = self.theme(True, True)
        r = run('scripts/report/self-check.py', root, '--profile', prof)
        self.assertIn('tracking: includes/config.php:', r.stdout)
        self.assertIn('the theme loads GTM: tracking goes through Example Tracker only', r.stdout)
        self.assertIn('ACF tracking field "gtm_id"', r.stdout)
        r = run('scripts/report/self-check.py', root)  # no profile: the theme may load GTM itself
        self.assertNotIn('tracking:', r.stdout)
        r = run('scripts/report/self-check.py', self.theme(False, False), '--profile', prof)
        self.assertNotIn('tracking:', r.stdout)  # GTM-XXXXXXX is a placeholder


class Runbook(unittest.TestCase):
    def runbook(self, profile, gtm=''):
        tmp = tempfile.mkdtemp()
        root = os.path.join(tmp, 'shop')
        prof = os.path.join(tmp, 'profile.local.json')
        write(prof, json.dumps(profile))
        with open(path('assets', 'site.example.json'), encoding='utf-8') as fh:
            site = json.load(fh)
        site.update(site_name='Corner Shop', domain='cornershop.example.org', wp_root=root, local_host='shop.test',
                    site_dir='shop', theme='shop', prefix='shop', key='cs', gtm=gtm)
        write(os.path.join(root, '_plan', 'site.json'), json.dumps(site))
        r = run('scripts/new-site.py', os.path.join(root, '_plan', 'site.json'), '--plan-only', '--profile', prof)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(os.path.join(root, '_setup', 'launch', 'RUNBOOK.md'), encoding='utf-8') as fh:
            return fh.read()

    def test_live_only_plugins_and_the_clean_up(self):
        rb = self.runbook(PROFILE, 'GTM-AB12CD3')
        self.assertIn('   - [ ] Example Tracker: from your plugin folder (`plugin_zips.tracker`) (live only: never '
                      'local or staging).', rb)
        self.assertIn('   - [ ] Shared Helper: from your plugin folder.', rb)
        self.assertNotIn('Sometimes Plugin', rb)
        self.assertIn('Tracking goes through the Example Tracker plugin only', rb)
        self.assertIn('plugin-check.py _plan/site.json --env live', rb)
        self.assertIn('**Clean-up, after live QA is at 0 and the report is done**', rb)
        self.assertIn('--done', rb)
        self.assertNotIn('<!--', rb)
        self.assertNotIn('{{', rb)

    def test_no_tracking_plugin_keeps_the_theme_setting(self):
        rb = self.runbook({}, 'GTM-AB12CD3')
        self.assertIn('4. Tracking: the Google Tag Manager ID GTM-AB12CD3 goes where this build loads it', rb)
        self.assertNotIn('Tracking goes through', rb)
        rb = self.runbook(PROFILE)
        self.assertIn('stays empty until the tracking task brings the GTM ID', rb)


if __name__ == '__main__':
    unittest.main()
