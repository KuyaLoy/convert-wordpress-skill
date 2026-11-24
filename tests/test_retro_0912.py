"""0.9.12: the leads portal in Theme Settings, packages without agent files, staging that survives a Duplicator
import, ACF tabs across the top, Duplicator Pro from the profile."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
import zipfile

from helpers import load, path, run
from test_theme_kit import PORTAL, PORTAL_STUBS, php

pkg = load('scripts/launch/package.py', 'launch_package_0912')
leads = load('scripts/report/leads-check.py', 'leads_check_0912')


def write(p, text):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def read(p):
    with open(p, encoding='utf-8') as fh:
        return fh.read()


def site_json(root, **extra):
    site = json.loads(read(path('assets', 'site.example.json')))
    site.update(site_name='Corner Shop', domain='cornershop.example.org', wp_root=root, local_host='shop.test',
                site_dir='shop', theme='shop', prefix='shop', key='cs', starter='barebones', **extra)
    write(os.path.join(root, '_plan', 'site.json'), json.dumps(site))
    return os.path.join(root, '_plan', 'site.json')


# The portal with no wp-config constants: only Theme Settings.
NO_CONSTANTS = PORTAL_STUBS.replace("const KITWP_LEADS_PREFIX = 'TEST_LEADS';", "const KITWP_LEADS_PREFIX = '';") \
    .replace("define( 'TEST_LEADS_ENDPOINT', 'https://portal.example.org/ingest/demo' );\n", '') \
    .replace("define( 'TEST_LEADS_KEY', 'lk_test_dummy_key' );\n", '')
POST_STUB = "function wp_remote_post( $url, $args ) { $GLOBALS['posts'][] = json_decode( $args['body'], true ); return []; }"
SEND = '$GLOBALS["posted"] = [ "your-name" => "Sam" ];\n$_SERVER = [ "REMOTE_ADDR" => "8.8.4.4" ];\n'


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class LeadsInThemeSettings(unittest.TestCase):
    """The portal's values come from Theme Settings > Leads portal; wp-config constants win when defined."""

    FUNCS = [(PORTAL, 'kitwp_leads_settings'), (PORTAL, 'kitwp_leads_tracking'),
             (PORTAL, 'kitwp_leads_allowed_fields'), (PORTAL, 'kitwp_leads_send'),
             ('assets/theme/includes/forms.php', 'kitwp_lead_fields')] + [
        ('assets/theme/includes/forms-attribution.php', n) for n in
        ('kitwp_attribution_fields', 'kitwp_attribution_url', 'kitwp_attribution_touch', 'kitwp_attribution_clean')]

    def stubs(self, constants):
        base = PORTAL_STUBS if constants else NO_CONSTANTS
        return base.replace(POST_STUB, "function wp_remote_post( $url, $args ) { $GLOBALS['posts'][] = [ $url, "
                                       "$args['headers']['Authorization'] ]; return []; }")

    def send(self, settings, constants=False):
        body = (f'$GLOBALS["settings"] = {php_array(settings)};\n' + SEND
                + 'kitwp_leads_send( new Kit_Form() );\n'
                + 'echo json_encode( [ "posts" => $GLOBALS["posts"], "from" => kitwp_leads_settings()["from"] ] );')
        return php(self.FUNCS, body, self.stubs(constants))

    def test_theme_settings_values_are_used(self):
        got = self.send({'leads_endpoint': 'https://portal.example.org/ingest/shop', 'leads_key': 'lk_ts_dummy'})
        self.assertEqual(got['posts'], [['https://portal.example.org/ingest/shop', 'Bearer lk_ts_dummy']])
        self.assertEqual(got['from'], 'Theme Settings')

    def test_wp_config_constants_win(self):
        got = self.send({'leads_endpoint': 'https://other.example.org/x', 'leads_key': 'lk_other'}, constants=True)
        self.assertEqual(got['posts'], [['https://portal.example.org/ingest/demo', 'Bearer lk_test_dummy_key']])
        self.assertEqual(got['from'], 'wp-config')

    def test_empty_settings_send_nothing(self):
        self.assertEqual(self.send({})['posts'], [])
        self.assertEqual(self.send({'leads_endpoint': 'https://portal.example.org/x', 'leads_key': ''})['posts'], [])
        self.assertEqual(self.send({'leads_endpoint': 'http://portal.example.org/x', 'leads_key': 'k'})['posts'], [])

    def test_staging_never_sends(self):
        stubs = self.stubs(False).replace("function wp_get_environment_type() { return 'production'; }",
                                          "function wp_get_environment_type() { return 'staging'; }")
        body = ('$GLOBALS["settings"] = ["leads_endpoint" => "https://p.example.org/x", "leads_key" => "k"];\n' + SEND
                + 'kitwp_leads_send( new Kit_Form() ); echo json_encode( $GLOBALS["posts"] );')
        self.assertEqual(php(self.FUNCS, body, stubs), [])

    def test_only_administrators_change_them(self):
        stubs = textwrap.dedent('''
            function current_user_can( $c ) { return $GLOBALS['admin']; }
            function get_field( $key, $post_id, $format ) { return 'stored-' . $key; }
        ''')
        body = textwrap.dedent('''
            $f = [ 'key' => 'field_kitk_ts_leads_key' ];
            $out = [];
            foreach ( [ true, false ] as $admin ) {
                $GLOBALS['admin'] = $admin;
                $out[] = kitwp_leads_settings_guard( 'posted', 'options', $f );
            }
            define( 'WP_CLI', true );
            $out[] = kitwp_leads_settings_guard( 'from-cli', 'options', $f );
            echo json_encode( $out );
        ''')
        got = php([(PORTAL, 'kitwp_leads_settings_guard')], body, stubs)
        self.assertEqual(got, ['posted', 'stored-field_kitk_ts_leads_key', 'from-cli'])
        src = read(path(PORTAL))
        for key in ('field_kitk_ts_leads_endpoint', 'field_kitk_ts_leads_key'):
            self.assertIn(f"add_filter( 'acf/update_value/key={key}', 'kitwp_leads_settings_guard', 10, 3 );", src)


def php_array(d):
    return '[' + ', '.join(f'{json.dumps(k)} => {json.dumps(v)}' for k, v in d.items()) + ']'


class FieldGroups(unittest.TestCase):
    """The builder: the Leads portal group always, administrators only; tabs across the top by default."""

    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp()
        tool = os.path.join(cls.root, '_plan', 'tools', 'acf', 'build_field_groups.py')
        write(tool, read(path('scripts', 'acf', 'build_field_groups.py')).replace('{{THEME}}', 'shop'))
        os.makedirs(os.path.join(cls.root, 'wp-content', 'themes', 'shop'))
        cls.out = subprocess.run([sys.executable, tool], capture_output=True, text=True)
        cls.json = os.path.join(cls.root, 'wp-content', 'themes', 'shop', 'acf-json')

    def group(self, name):
        return json.loads(read(os.path.join(self.json, f'group_kitk_{name}.json')))

    def test_built(self):
        self.assertEqual(self.out.returncode, 0, self.out.stdout + self.out.stderr)
        self.assertIn('group_kitk_leads_portal', self.out.stdout)

    def test_leads_portal_group(self):
        g = self.group('leads_portal')
        fields = {f['name']: f for f in g['fields']}
        self.assertEqual(fields['leads_endpoint']['type'], 'url')
        self.assertEqual(fields['leads_endpoint']['key'], 'field_kitk_ts_leads_endpoint')
        self.assertEqual(fields['leads_key']['type'], 'password')
        self.assertEqual(fields['leads_key']['key'], 'field_kitk_ts_leads_key')
        self.assertEqual(fields['leads_endpoint']['default_value'], '')  # seeded empty
        self.assertNotIn('default_value', fields['leads_key'])
        rules = g['location'][0]
        self.assertIn({'param': 'options_page', 'operator': '==', 'value': 'kitk-theme-settings'}, rules)
        self.assertIn({'param': 'current_user_role', 'operator': '==', 'value': 'administrator'}, rules)

    def test_tabs_on_top(self):
        for name in ('theme_settings', 'tpl_service'):
            tabs = [f for f in self.group(name)['fields'] if f['type'] == 'tab']
            self.assertTrue(tabs, name)
            self.assertEqual({t['placement'] for t in tabs}, {'top'}, name)

    def test_left_only_when_asked(self):
        mod = load('scripts/acf/build_field_groups.py', 'bfg_0912')
        self.assertEqual(mod.G('x').tab('Hero')['placement'], 'top')
        self.assertEqual(mod.G('x').tab('Hero', placement='left')['placement'], 'left')


GOOD = ['index.php', 'wp-content/themes/shop/style.css', 'wp-content/plugins/x/AGENTS.md',
        'dup-installer/dup_descriptors_a1/db_dumps/database.sql',
        'dup-installer/dup_descriptors_a1/orig_files/source_site_wpconfig']


def make_zip(names):
    fd, p = tempfile.mkstemp(suffix='_archive.zip')
    os.close(fd)
    with zipfile.ZipFile(p, 'w') as z:
        for n in names:
            z.writestr(n, 'x')
    return p


class Packaging(unittest.TestCase):
    """Agent folders and files stay out of the package, and the check refuses them."""

    def test_filters_leave_them_out(self):
        r = run('scripts/launch/duplicator-filters.py', 'C:/sites/shop', 'shop')
        self.assertEqual(r.returncode, 0, r.stderr)
        for p in ('eod', 'tasks', '.agents', '.claude', 'AGENTS.md', 'handoff-archive.md', 'handoff.md',
                  'wp-content/themes/shop/AGENTS.md'):
            self.assertIn(f'C:/sites/shop/{p};', r.stdout.splitlines(), p)

    def test_private_entries_refused(self):
        bad = ['eod/2026-11-24.md', 'tasks/aba/notes.md', '.agents/rules.md', 'AGENTS.md', 'handoff-archive.md',
               'handoff.md', 'ai-handoff-summary.md', 'BUILD-MAP.md', '_plan/site.json', '_setup/seed/x.json',
               'wp-content/debug.log', 'wp-content/themes/shop/AGENTS.md']
        c = pkg.check_archive(make_zip(GOOD + bad), 'shop')
        self.assertEqual(sorted(c['hits']), sorted(bad))

    def test_check_zip_lists_the_top_level(self):
        z = make_zip(GOOD)
        r = run('scripts/launch/package.py', '--check-zip', z, 'shop')
        self.assertEqual(r.returncode, 0, r.stdout)
        lines = r.stdout.splitlines()
        self.assertTrue(lines[0].startswith('OK package: '), r.stdout)
        self.assertIn('5 entries, 0 private', lines[0])
        self.assertIn('Top level of the archive (entries, name):', lines)
        self.assertIn('      2  dup-installer/', lines)
        self.assertIn('      1  index.php', lines)
        self.assertIn('      2  wp-content/', lines)

    def test_check_zip_fails_on_private(self):
        r = run('scripts/launch/package.py', '--check-zip', make_zip(GOOD + ['eod/today.md', 'AGENTS.md']), 'shop')
        self.assertEqual(r.returncode, 4, r.stdout)
        self.assertTrue(r.stdout.startswith('FAIL package: 2 private entries'), r.stdout)
        self.assertIn('eod/today.md', r.stdout)

    def test_figma_folder_left_out_and_refused(self):  # 0.9.13: a Figma build's private root folder
        r = run('scripts/launch/duplicator-filters.py', 'C:/sites/shop', 'shop')
        self.assertIn('C:/sites/shop/_figma;', r.stdout.splitlines())
        bad = ['_figma/inventory.json', '_figma/frames/home.png']
        self.assertEqual(sorted(pkg.check_archive(make_zip(GOOD + bad), 'shop')['hits']), sorted(bad))
        r = run('scripts/launch/package.py', '--check-zip', make_zip(GOOD + bad), 'shop')
        self.assertEqual(r.returncode, 4, r.stdout)
        self.assertIn('_figma/inventory.json', r.stdout)

    def test_check_zip_usage(self):
        r = run('scripts/launch/package.py', '--check-zip', 'missing.zip', 'shop')
        self.assertEqual(r.returncode, 1)
        self.assertTrue(r.stdout.startswith('FAIL package: --check-zip needs'), r.stdout)


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class StagingEnvironment(unittest.TestCase):
    """new-site.py writes the must-use environment file and acf-json/.htaccess; the host decides the environment."""

    @classmethod
    def setUpClass(cls):
        cls.root = os.path.join(tempfile.mkdtemp(), 'shop')
        theme = os.path.join(cls.root, 'wp-content', 'themes', 'shop')
        write(os.path.join(cls.root, 'wp-includes', 'version.php'), "<?php $wp_version = '7.1';\n")
        write(os.path.join(theme, 'style.css'), '/*\nTheme Name: Barebones\nText Domain: barebones\n*/\n')
        cls.r = run('scripts/new-site.py', site_json(cls.root))
        cls.mu = os.path.join(cls.root, 'wp-content', 'mu-plugins', 'shop-environment.php')
        cls.ht = os.path.join(theme, 'acf-json', '.htaccess')

    def test_files_written(self):
        self.assertEqual(self.r.returncode, 0, self.r.stdout + self.r.stderr)
        self.assertTrue(os.path.isfile(self.mu))
        self.assertIn('Require all denied', read(self.ht))
        src = read(self.mu)
        self.assertNotIn('{{', src)
        self.assertNotIn('kitwp', src)
        self.assertIn("array( 'cornershop.example.org', 'www.cornershop.example.org' )", src)
        self.assertEqual(subprocess.run(['php', '-l', self.mu], capture_output=True).returncode, 0)

    def env(self, home, defined=''):
        stubs = textwrap.dedent(f'''<?php
            define( 'ABSPATH', '/' );
            {defined}
            $GLOBALS['filters'] = [];
            function get_option( $n ) {{ return {json.dumps(home)}; }}
            function wp_parse_url( $u, $c ) {{ return parse_url( $u, $c ); }}
            function add_filter( $h, $f ) {{ $GLOBALS['filters'][] = $h; }}
            function add_action( $h, $f ) {{ $GLOBALS['filters'][] = $h; }}
        ''')
        code = stubs + read(self.mu).split('<?php', 1)[1] + '\necho json_encode( [ WP_ENVIRONMENT_TYPE, $GLOBALS["filters"] ] );'
        with tempfile.NamedTemporaryFile('w', suffix='.php', delete=False, encoding='utf-8') as fh:
            fh.write(code)
        try:
            out = subprocess.run(['php', fh.name], capture_output=True, text=True)
        finally:
            os.unlink(fh.name)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        return json.loads(out.stdout)

    def test_environment_by_host(self):
        self.assertEqual(self.env('https://cornershop.example.org')[0], 'production')
        self.assertEqual(self.env('https://www.cornershop.example.org/')[0], 'production')
        self.assertEqual(self.env('http://shop.test')[0], 'local')
        self.assertEqual(self.env('http://localhost:8080')[0], 'local')
        env, hooks = self.env('https://staging.agency.example.net/cornershop')
        self.assertEqual(env, 'staging')
        self.assertEqual(hooks, ['pre_option_blog_public', 'wp_robots', 'send_headers'])  # never indexed

    def test_wp_config_wins(self):
        env, hooks = self.env('https://staging.agency.example.net', "define( 'WP_ENVIRONMENT_TYPE', 'production' );")
        self.assertEqual(env, 'production')
        self.assertEqual(hooks, [])
        self.assertEqual(self.env('https://cornershop.example.org', "define( 'WP_ENVIRONMENT_TYPE', 'staging' );")[0],
                         'staging')

    def test_runbook_names_the_check(self):
        rb = read(os.path.join(self.root, '_setup', 'launch', 'RUNBOOK.md'))
        self.assertIn('`wp-content/mu-plugins/shop-environment.php`', rb)
        self.assertIn("`wp eval 'echo wp_get_environment_type();'` on staging says `staging`", rb)


class LeadsCheckSite(unittest.TestCase):
    """leads-check.py --site: the check runs inside WordPress; only facts come back, never the key."""

    def fake_wp(self, answer):
        d = tempfile.mkdtemp()
        script = os.path.join(d, 'fakewp.py')
        write(script, 'import sys\nassert sys.argv[1] == "--path=/srv/shop" and sys.argv[2] == "eval"\n'
                      f'print("Success: loaded")\nprint("KITWP_LEADS_CHECK " + {json.dumps(json.dumps(answer))})\n')
        return f'"{sys.executable}" "{script}"'

    def check(self, answer):
        return run('scripts/report/leads-check.py', '--site', '/srv/shop', '--wp', self.fake_wp(answer))

    def test_ok_says_where_from(self):
        r = self.check({'env': 'production', 'from': 'Theme Settings', 'endpoint': True, 'key': True, 'https': True,
                        'where': 'portal.example.org/ingest/shop', 'code': 200, 'transport': ''})
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(r.stdout.splitlines()[0], 'OK leads-check: portal.example.org/ingest/shop (from Theme '
                         'Settings; environment production) accepts this key (200; nothing stored)')

    def test_empty_and_wrong(self):
        r = self.check({'env': 'production', 'from': 'Theme Settings', 'endpoint': True, 'key': False,
                        'https': True, 'where': 'p.example.org/x'})
        self.assertEqual(r.returncode, 1)
        self.assertIn('FAIL leads-check: the password empty in Theme Settings > Leads portal', r.stdout)
        r = self.check({'env': 'production', 'from': 'wp-config', 'endpoint': True, 'key': True, 'https': True,
                        'where': 'p.example.org/x', 'code': 401, 'transport': ''})
        self.assertEqual(r.returncode, 1)
        self.assertIn('HTTP 401: the key is wrong', r.stdout)
        r = self.check({'env': 'staging', 'error': 'no kitwp_leads_settings() in the active theme'})
        self.assertEqual(r.returncode, 1)

    @unittest.skipUnless(shutil.which('php'), 'needs PHP')
    def test_site_php_is_valid_and_never_prints_the_key(self):
        with tempfile.NamedTemporaryFile('w', suffix='.php', delete=False, encoding='utf-8') as fh:
            fh.write('<?php\n' + leads.SITE_PHP)
        try:
            self.assertEqual(subprocess.run(['php', '-l', fh.name], capture_output=True).returncode, 0)
        finally:
            os.unlink(fh.name)
        self.assertNotIn("$s['key'] ]", leads.SITE_PHP)  # only whether it is set goes out
        self.assertIn("'key' => '' !== $s['key']", leads.SITE_PHP)


class RunbookLeadsItem(unittest.TestCase):
    """A portal without a constant prefix is a portal: Theme Settings holds its values."""

    def test_portal_without_prefix(self):
        tmp = tempfile.mkdtemp()
        root = os.path.join(tmp, 'shop')
        prof = os.path.join(tmp, 'profile.local.json')
        write(prof, json.dumps({'leads_portal': {'_about': 'x', 'constant_prefix': '', 'admin': 'https://admin.example'}}))
        r = run('scripts/new-site.py', site_json(root), '--plan-only', '--profile', prof)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rb = read(os.path.join(root, '_setup', 'launch', 'RUNBOOK.md'))
        self.assertIn('its address and password pasted into Theme Settings > Leads portal on live (the developer, '
                      'logged in as an administrator); `python3 _plan/tools/report/leads-check.py --site` on live', rb)
        self.assertNotIn('win when defined', rb)
        self.assertNotIn('BLOCKER: no leads portal', rb)


class DuplicatorProZip(unittest.TestCase):
    """install-wp.py takes Duplicator Pro from plugin_zips.duplicator_pro when the profile names it."""

    def test_profile_example_has_the_path(self):
        prof = json.loads(read(path('profile.example.json')))
        self.assertEqual(prof['plugin_zips']['duplicator_pro'], '')
        src = read(path('scripts', 'setup', 'install-wp.py'))
        self.assertIn("dup_zip = profile_zip('duplicator_pro')", src)
        self.assertIn("safe_extract(data, PLUGINS, 'duplicator-pro')", src)


if __name__ == '__main__':
    unittest.main()
