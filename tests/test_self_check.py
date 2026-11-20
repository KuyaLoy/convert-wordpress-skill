"""0.9.6: the pre-QA self-check finds each kit-caused class on a small fake site, and nothing on a clean one."""
import json
import os
import tempfile
import unittest

from helpers import run

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


if __name__ == '__main__':
    unittest.main()
