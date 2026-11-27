"""0.12.0: the agency badge in every footer and the branded emails: the theme keeps the badge unless the build
recorded that the client asked, and self-check.py and live-qa.py fail without the badge, its link or the branded
CF7 email and auto-reply."""
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

from helpers import load, path, run

BC = load('scripts/report/branding_check.py', 'branding_check_0120')
GUARD = "<?php\n/**\n * File.\n */\n\ndefined( 'ABSPATH' ) || exit;\n"
LEAD = open(path('assets', 'seed', 'lead-email.html'), encoding='utf-8').read().replace('kitk', 'shop')
AUTO = open(path('assets', 'seed', 'autoreply-email.html'), encoding='utf-8').read().replace('kitk', 'shop')
BRANDED = [{'form': 'Quote Form', 'mail': 'mail', 'active': True, 'html': True, 'body': LEAD},
           {'form': 'Quote Form', 'mail': 'mail_2', 'active': True, 'html': True, 'body': AUTO}]
FOOTER = ('<footer><div class="bar">(c) Shop <a href="https://agency.example/" target="_blank" '
          'data-shop-badge="agency" aria-label="Agency"><img src="https://shop.test/badge.svg" alt="Agency"></a></div>'
          '</footer>')


def fake_wp(tmp, mails):
    """A stand-in for WP-CLI that answers the branding eval with these mails, as a --wp value."""
    script = os.path.join(tmp, 'fake-wp.py')
    with open(script, 'w', encoding='utf-8') as fh:
        fh.write('import json\nprint(json.dumps({"mails": json.loads(%r)}))\n' % json.dumps(mails))
    return f'"{sys.executable.replace(os.sep, "/")}" "{script.replace(os.sep, "/")}"'


class Shared(unittest.TestCase):
    def test_badge(self):
        self.assertEqual(BC.badge_problem(FOOTER), '')
        self.assertIn('no agency badge', BC.badge_problem('<footer>(c) Shop</footer>'))
        self.assertIn('no link', BC.badge_problem(FOOTER.replace('href="https://agency.example/" ', '')))
        self.assertIn('no image', BC.badge_problem(FOOTER.replace('src="https://shop.test/badge.svg"', 'src=""')))

    def test_mails(self):
        self.assertEqual(BC.mail_problems(BRANDED), [])
        plain = [dict(BRANDED[0], body='Name: [name]'), dict(BRANDED[1], html=False),
                 {'form': 'Other', 'mail': 'mail_2', 'active': False, 'html': False, 'body': ''}]
        got = BC.mail_problems(plain)
        self.assertEqual(got[0], ('Quote Form', 'email: not the branded template (no logo and no badge mail-tag)'))
        self.assertEqual(got[1], ('Quote Form', 'auto-reply: not HTML (Mail tab: "Use HTML content type")'))
        self.assertEqual(got[2], ('Other', 'no auto-reply (Mail (2) is off)'))
        for name in ('lead-email.html', 'autoreply-email.html'):  # the kit's own templates are branded
            with open(path('assets', 'seed', name), encoding='utf-8') as fh:
                self.assertEqual(BC.template_problem(fh.read()), '', name)


def kit_site(footer_call=True, config_filled=True, hide_note='', autoreply='autoreply-email.html'):
    root = tempfile.mkdtemp()
    theme = os.path.join(root, 'wp-content', 'themes', 'shop')
    value = (lambda v: v if config_filled else '')
    files = {
        'includes/helpers.php': GUARD + 'function shop_agency_badge() {\n\treturn;\n}\n',
        'includes/config.php': GUARD + (
            f"const SHOP_SITE_BADGE = '{value('assets/brand/badge.svg')}';\n"
            f"const SHOP_SITE_BADGE_LINK = '{value('https://agency.example/')}';\n"
            f"const SHOP_EMAIL_BADGE = '{value('assets/email/badge.png')}';\n"
            f"const SHOP_EMAIL_BADGE_LINK = '{value('https://agency.example/')}';\n"
            f"const SHOP_BADGE_HIDE_NOTE = '{hide_note}';\n"
            "// shop_agency_badge() in a comment is not a call.\n"),
        'footer.php': GUARD + ('<footer><?php shop_agency_badge(); ?></footer>\n' if footer_call else '<footer></footer>\n'),
    }
    for rel, text in files.items():
        os.makedirs(os.path.dirname(os.path.join(theme, rel)), exist_ok=True)
        with open(os.path.join(theme, rel), 'w', encoding='utf-8') as fh:
            fh.write(text)
    seed = os.path.join(root, '_setup', 'seed')
    os.makedirs(seed)
    with open(os.path.join(seed, 'forms.json'), 'w', encoding='utf-8') as fh:
        json.dump({'quote': {'body_file': 'lead-email.html', 'autoreply_file': autoreply}}, fh)
    for name, text in (('lead-email.html', LEAD), ('autoreply-email.html', AUTO), ('plain.html', 'Name: [name]')):
        with open(os.path.join(seed, name), 'w', encoding='utf-8') as fh:
            fh.write(text)
    return root


def branding_lines(root, *args):
    r = run('scripts/report/self-check.py', root, '--theme', 'shop', '-v', *args)
    return [line for line in r.stdout.splitlines() if line.startswith('branding:')], r


class SelfCheck(unittest.TestCase):
    def test_badge_and_branded_seed_pass(self):
        lines, r = branding_lines(kit_site())
        self.assertEqual(lines, [], r.stdout)

    def test_missing_badge_link_and_template_fail(self):
        lines, r = branding_lines(kit_site(footer_call=False, config_filled=False, autoreply='plain.html'))
        self.assertEqual(r.returncode, 1)
        text = '\n'.join(lines)
        self.assertIn('branding: footer: no agency badge: call <prefix>_agency_badge()', text)
        for const in ('SITE_BADGE', 'SITE_BADGE_LINK', 'EMAIL_BADGE', 'EMAIL_BADGE_LINK'):
            self.assertIn(f'({const})', text)
        self.assertIn('branding: _setup/seed/forms.json quote: auto-reply: not the branded template', text)
        self.assertIn('(branding', r.stdout.splitlines()[0])

    def test_hide_only_with_the_recorded_note(self):
        lines, _ = branding_lines(kit_site(footer_call=False, hide_note='client asked, task ABC-12'))
        self.assertEqual(lines, [])
        lines, _ = branding_lines(kit_site(footer_call=False, hide_note='{{BADGE_HIDE_NOTE}}'))
        self.assertTrue(any('no agency badge' in line for line in lines))  # an unfilled token is no note

    def test_database_mails_with_wp(self):
        root = kit_site()
        lines, _ = branding_lines(root, '--wp', fake_wp(root, BRANDED))
        self.assertEqual(lines, [])
        lines, _ = branding_lines(root, '--wp', fake_wp(root, [dict(BRANDED[1], body='Thanks [name]')]))
        self.assertEqual(lines, ['branding: CF7 "Quote Form": auto-reply: not the branded template (no logo and no '
                                 'badge mail-tag)'])

    def test_not_a_kit_theme_is_left_alone(self):
        root = kit_site(footer_call=False, config_filled=False)
        os.remove(os.path.join(root, 'wp-content', 'themes', 'shop', 'includes', 'helpers.php'))
        lines, _ = branding_lines(root)
        self.assertEqual([x for x in lines if 'seed' not in x], [])


class Theme(unittest.TestCase):
    def test_hide_toggle_needs_the_note(self):
        for rel, fn in (('assets/theme/includes/helpers.php', 'kitwp_agency_badge'),
                        ('assets/theme/includes/forms-mail.php', 'kitwp_email_badge')):
            with open(path(rel), encoding='utf-8') as fh:
                body = fh.read().split(f'function {fn}()', 1)[1][:200]
            self.assertIn("kitwp_setting( 'agency_badge_hide' ) && '' !== KITWP_BADGE_HIDE_NOTE", body, rel)
        with open(path('assets', 'theme', 'includes', 'config.php'), encoding='utf-8') as fh:
            self.assertIn("const KITWP_BADGE_HIDE_NOTE = '{{BADGE_HIDE_NOTE}}';", fh.read())

    def test_seeder_prefills_branding(self):
        with open(path('assets', 'theme', 'includes', 'seed-settings.php'), encoding='utf-8') as fh:
            s = fh.read()
        self.assertIn('return kitwp_seed_agency_badge( $report );', s)
        for need in ("'agency_badge' => [ KITWP_SITE_BADGE", "'email_badge'  => [ KITWP_EMAIL_BADGE",
                     "field_kitk_ts_agency_link", "! kitwp_setting( 'agency_link' )"):
            self.assertIn(need, s)

    def test_new_site_takes_the_note(self):
        tmp = tempfile.mkdtemp()
        root = os.path.join(tmp, 'shop')
        with open(path('assets', 'site.example.json'), encoding='utf-8') as fh:
            site = json.load(fh)
        site.update(site_name='Corner Shop', domain='cornershop.example.org', wp_root=root, local_host='shop.test',
                    site_dir='shop', theme='shop', prefix='shop', key='cs', agency_badge_hide="client asked, task's ABC")
        os.makedirs(os.path.join(root, '_plan'))
        with open(os.path.join(root, '_plan', 'site.json'), 'w', encoding='utf-8') as fh:
            json.dump(site, fh)
        r = run('scripts/new-site.py', os.path.join(root, '_plan', 'site.json'), '--plan-only')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(path('scripts', 'new-site.py'), encoding='utf-8') as fh:
            self.assertIn("'BADGE_HIDE_NOTE': str(site.get('agency_badge_hide') or '')", fh.read())


class Docs(unittest.TestCase):
    def test_hard_rule_written(self):
        with open(path('references', 'build.md'), encoding='utf-8') as fh:
            build = ' '.join(fh.read().split())
        self.assertIn('every site, even when the design has none', build)
        self.assertTrue(re.search(r'agency_badge_hide', build))


if __name__ == '__main__':
    unittest.main()
