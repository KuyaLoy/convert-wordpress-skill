"""0.9.6: the pre-QA self-check finds each kit-caused class on a small fake site, and nothing on a clean one."""
import glob
import json
import os
import shutil
import tempfile
import unittest

from helpers import load, path, run

GUARD = "<?php\n/**\n * File.\n */\n\ndefined( 'ABSPATH' ) || exit;\n"


def site(dirty):
    root = tempfile.mkdtemp()
    theme = os.path.join(root, 'wp-content', 'themes', 'acme')
    files = {
        'functions.php': GUARD + "require __DIR__ . '/includes/config.php';\nacme_used();\n"
                         "foreach ( [ 'a' ] as $s ) { call_user_func( 'acme_step_' . $s ); }\n",
        'includes/config.php': GUARD + "function acme_used() {\n\treturn get_theme_file_uri( 'assets/logo.png' );\n}\n"
                               "function acme_step_a() {\n\treturn 1;\n}\n",
        'assets/logo.png': 'png',
        'style.css': '/*\nTheme Name: Acme\nAuthor: Acme Ltd\nRequires PHP: 8.1\n\nBased on _tw https://underscoretw.com/\n*/',
        'acf-json/group_acme.json': json.dumps({'title': 'Home', 'fields': [
            {'label': 'Title', 'name': 'title', 'type': 'text', 'instructions': 'The big line at the top.'},
            {'label': 'Note', 'name': 'note', 'type': 'text', 'instructions': 'Write {phone} to show the number.'},
            {'label': 'Tabs', 'name': '', 'type': 'tab', 'instructions': ''}]}),
    }
    launch = {'RUNBOOK.md': '# Runbook\n', 'htaccess-live.txt': 'RewriteCond %{HTTP_HOST} ^example\\.com$\n'
              '<FilesMatch "readme">deny</FilesMatch>\nRedirectMatch 404 acf-json\n'}
    if dirty:
        files['includes/config.php'] += ("function acme_dead() {\n\treturn 2;\n}\n"
                                         "function acme_logo() {\n\treturn get_theme_file_uri( 'assets/email/logo.png' );\n}\n"
                                         "function acme_rows() {\n\treturn (array) get_field( 'faqs' );\n}\n"
                                         "function acme_head() {\n\t?>\n\t<?php\n\techo 1; // phpcs:ignore WordPress.Security\n}\n")
        files['includes/noguard.php'] = "<?php\necho acme_logo() . acme_rows() . acme_head();\n"
        files['includes/big.php'] = GUARD + '// line\n' * 320
        files['js/readme.txt'] = 'starter'
        files['style.css'] = files['style.css'].replace('Author: Acme Ltd', 'Author: Barebones')
        files['acf-json/group_acme.json'] = json.dumps({'title': 'Home', 'fields': [
            {'label': 'Title', 'name': 'title', 'type': 'text', 'instructions': ''},
            {'label': 'Slug', 'name': 'slug', 'type': 'text', 'instructions': 'The article slug.'},
            {'label': 'Number', 'name': 'n', 'type': 'text', 'instructions': 'Token {company_number}.'}]})
        launch['htaccess-live.txt'] = 'RewriteCond %{HTTP_HOST} ^www\\.www\\.example\\.com$ {{DOMAIN}}\n'
    for rel, text in files.items():
        p = os.path.join(theme, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8') as fh:
            fh.write(text)
    os.makedirs(os.path.join(root, '_setup', 'launch'))
    for rel, text in launch.items():
        with open(os.path.join(root, '_setup', 'launch', rel), 'w', encoding='utf-8') as fh:
            fh.write(text)
    return root


class SelfCheck(unittest.TestCase):
    def test_clean_site(self):
        r = run('scripts/report/self-check.py', site(False))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(r.stdout.splitlines()[0], 'OK self-check: 0 found')

    def test_every_class_found(self):
        r = run('scripts/report/self-check.py', site(True))
        self.assertEqual(r.returncode, 1, r.stdout)
        first = r.stdout.splitlines()[0]
        self.assertTrue(first.startswith('FAIL self-check:'), first)
        for cls in ('abspath', 'instructions', 'launch', 'leftover', 'missing-file', 'php-gap', 'phpcs-ignore',
                    'repeater', 'size', 'unused'):
            self.assertIn(cls, first, r.stdout)
        out = r.stdout
        self.assertIn('acme_dead() is never called', out)
        self.assertNotIn('acme_step_a', out)  # called by a built name
        self.assertIn('Home > Title: no instructions', out)
        self.assertIn('developer words ("slug")', out)
        self.assertIn('developer words ("Token")', out)
        self.assertIn('assets/email/logo.png does not exist', out)
        self.assertIn('the host rule reads www.www.', out)
        self.assertIn('{{DOMAIN}} is not filled', out)
        self.assertIn('js/readme.txt', out)


STORE = GUARD + """function acme_store_lead( $data ) {
	global $wpdb;
	$wpdb->query( "CREATE TABLE {$wpdb->prefix}acme_enquiries ( id INT )" );
	require_once ABSPATH . 'wp-admin/includes/upgrade.php';
	dbDelta( $sql );
	$wpdb->insert(
		$wpdb->prefix . 'acme_enquiries',
		$data
	);
	$wpdb->get_var( 'SELECT 1' );
}
add_action( 'init', function () {
	register_post_type( 'enquiry', [ 'public' => false ] );
	register_post_type( 'project', [ 'public' => true ] );
} );
add_action( 'admin_menu', function () {
	add_menu_page( 'Leads', 'Leads', 'manage_options', 'acme-leads', 'acme_store_lead' );
	add_submenu_page( 'tools.php', 'Form entries', 'Form entries', 'manage_options', 'acme-form-entries', '__return_null' );
	add_menu_page( 'Projects', 'Projects', 'edit_posts', 'acme-projects', '__return_null' );
} );
"""


class LeadStorage(unittest.TestCase):
    """0.10.1: leads are stored by Contact Form CFDB7 on live only; the build's own storage is a finding."""

    def lead_lines(self, root):
        r = run('scripts/report/self-check.py', root, '-v')
        return r, [l for l in r.stdout.splitlines() if l.startswith('lead-storage: ')]

    def test_every_pattern_caught(self):
        root = site(False)
        theme = os.path.join(root, 'wp-content', 'themes', 'acme')
        with open(os.path.join(theme, 'includes', 'enquiries.php'), 'w', encoding='utf-8') as fh:
            fh.write(STORE)
        mu = os.path.join(root, 'wp-content', 'mu-plugins')
        os.makedirs(mu)
        with open(os.path.join(mu, 'contact-store.php'), 'w', encoding='utf-8') as fh:
            fh.write(GUARD + '$wpdb->query( "INSERT INTO {$wpdb->prefix}contact_messages VALUES (1)" );\n')
        r, lines = self.lead_lines(root)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn('lead-storage', r.stdout.splitlines()[0])
        where = [l.split(': ')[1] for l in lines]
        self.assertEqual(where, ['includes/enquiries.php:9', 'includes/enquiries.php:11', 'includes/enquiries.php:12',
                                 'includes/enquiries.php:19', 'includes/enquiries.php:23',
                                 'includes/enquiries.php:24', 'mu-plugins/contact-store.php:7'], r.stdout)
        self.assertIn('includes/enquiries.php:9: creates a table', r.stdout)  # one finding for the line
        text = '\n'.join(lines)
        self.assertIn('creates a table', text)
        self.assertIn('writes with $wpdb', text)
        self.assertIn('register_post_type for enquiries', text)
        self.assertIn('add_menu_page for enquiries', text)
        self.assertIn('add_submenu_page for enquiries', text)
        self.assertIn('Contact Form CFDB7 on live only', text)
        self.assertNotIn(':16:', text)  # $wpdb->get_var reads, it does not store
        self.assertNotIn(':20:', text)  # the projects post type
        self.assertNotIn(':25:', text)  # the projects menu

    def test_kit_files_allow_listed_and_listed_whole(self):
        mod = load('scripts/report/self-check.py', 'self_check_0101')
        shipped = {os.path.relpath(p, path('assets', 'theme')).replace(os.sep, '/')
                   for p in glob.glob(path('assets', 'theme', '**', '*.php'), recursive=True)} - {'functions.php'}
        self.assertEqual(mod.KIT_FILES, shipped)
        self.assertEqual(sorted(f[len('kitwp'):] for f in os.listdir(path('assets', 'mu-plugin'))
                                if f.endswith('.php')), sorted(mod.KIT_MU))
        root = site(False)
        p = os.path.join(root, 'wp-content', 'themes', 'acme', 'includes', 'forms.php')
        with open(p, 'w', encoding='utf-8') as fh:
            fh.write(GUARD + "register_post_type( 'enquiry' );\n")
        self.assertEqual(self.lead_lines(root)[1], [])  # a kit file by its path

    def test_the_rule_word_for_word(self):
        rule = ("Leads are stored only by Contact Form CFDB7, installed on live (the kit's plugin list). Never create a "
                "database table, custom post type, option rows, files or an admin page of your own for enquiries or "
                "submissions; local mail capture (_setup/mail) is local only.")
        for doc in (('SKILL.md',), ('references', 'forms-email.md')):
            with open(path(*doc), encoding='utf-8') as fh:
                flat = ' '.join(fh.read().split())
            self.assertIn(rule, flat, doc)

    def test_kit_theme_is_clean_even_without_the_allow_list(self):
        mod = load('scripts/report/self-check.py', 'self_check_0101b')
        root = tempfile.mkdtemp()
        mu = os.path.join(root, 'wp-content', 'mu-plugins')
        shutil.copytree(path('assets', 'mu-plugin'), mu)
        for kit in (mod.KIT_FILES, set()):
            mod.KIT_FILES, out = kit, []
            mod.check_lead_storage(path('assets', 'theme'), root, out)
            self.assertEqual(out, [])


if __name__ == '__main__':
    unittest.main()
