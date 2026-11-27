"""0.10.2: the leads portal is optional (none by default), and self-check.py --theme takes a name or a relative path."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

from helpers import path, run
from test_retro_0912 import site_json
from test_self_check import site as fake_site


def write(p, text):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def read(p):
    with open(p, encoding='utf-8') as fh:
        return fh.read()


def plan(profile):
    """new-site.py --plan-only with this profile: the runbook, the builder copy and the output."""
    tmp = tempfile.mkdtemp()
    root = os.path.join(tmp, 'shop')
    prof = os.path.join(tmp, 'profile.local.json')
    write(prof, json.dumps(profile))
    r = run('scripts/new-site.py', site_json(root), '--plan-only', '--profile', prof)
    return (r, read(os.path.join(root, '_setup', 'launch', 'RUNBOOK.md')),
            read(os.path.join(root, '_plan', 'tools', 'acf', 'build_field_groups.py')))


def build(portal):
    """Run the builder with LEADS_PORTAL filled (or left as the raw token) and list the groups it wrote."""
    root = tempfile.mkdtemp()
    text = read(path('scripts', 'acf', 'build_field_groups.py')).replace('{{THEME}}', 'shop')
    if portal is not None:
        text = text.replace('{{LEADS_PORTAL}}', portal)
    tool = os.path.join(root, '_plan', 'tools', 'acf', 'build_field_groups.py')
    write(tool, text)
    os.makedirs(os.path.join(root, 'wp-content', 'themes', 'shop'))
    r = subprocess.run([sys.executable, tool], capture_output=True, text=True)
    return r, sorted(os.listdir(os.path.join(root, 'wp-content', 'themes', 'shop', 'acf-json')))


class OptionalPortal(unittest.TestCase):
    def test_no_portal_is_fine(self):
        for profile in ({}, {'leads_portal': {'_about': 'x', 'constant_prefix': '', 'admin': 'https://admin.example'}}):
            r, rb, tool = plan(profile)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertNotIn('BLOCKER', rb)
            self.assertNotIn('eads portal', rb)  # no go/no-go item, no live checklist item, no portal counts
            self.assertNotIn('leads-check.py', rb)
            self.assertNotIn('- [ ] \n', rb)  # no empty checklist line left behind
            self.assertNotIn('leads portal', r.stdout)
            self.assertIn("LEADS_PORTAL = 'no' == 'yes'", tool)

    def test_a_profile_with_a_prefix_keeps_the_portal(self):
        r, rb, tool = plan({'leads_portal': {'constant_prefix': 'acme_leads'}})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('Leads portal ready', rb)
        self.assertIn('leads-check.py', rb)
        self.assertIn('pasted into Theme Settings > Leads portal on live', rb)
        self.assertIn("Each test lead also shows in the leads portal's form counts.", rb)
        self.assertIn("LEADS_PORTAL = 'yes' == 'yes'", tool)

    def test_builder_writes_the_group_only_with_a_portal(self):
        r, files = build('yes')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('group_kitk_leads_portal.json', files)
        for portal in ('no', None):  # None: the raw kit file, token unfilled
            r, files = build(portal)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertNotIn('group_kitk_leads_portal.json', files)
            self.assertIn('group_kitk_theme_settings.json', files)

    def test_docs_say_optional(self):
        forms = ' '.join(read(path('references', 'forms-email.md')).split())
        self.assertIn('**Optional, none by default.**', forms)
        self.assertNotIn('Mandatory on live', forms)
        for doc in (('SKILL.md',), ('references', 'phase-steps.md'), ('references', 'launch.md'),
                    ('references', 'phases-and-qa.md'), ('profile.example.json',)):
            text = ' '.join(read(path(*doc)).split()).lower()
            self.assertNotIn('go-live blocker', text, doc)
            self.assertNotIn('mandatory for a site with a lead form', text, doc)


class ThemeArgument(unittest.TestCase):
    def check(self, root, theme, cwd=None):
        return run('scripts/report/self-check.py', root, '--theme', theme, cwd=cwd)

    def test_name_relative_and_full_path(self):
        root = fake_site(False)
        full = os.path.join(root, 'wp-content', 'themes', 'acme')
        for theme, cwd in (('acme', None), ('wp-content/themes/acme', None), (full, None),
                           (os.path.join('wp-content', 'themes', 'acme'), root)):
            r = self.check(root, theme, cwd)
            self.assertEqual(r.stdout.splitlines()[0], 'OK self-check: 0 found', (theme, r.stdout))

    def test_tw_outer_folder_gives_its_theme_folder(self):
        root = fake_site(False)
        themes = os.path.join(root, 'wp-content', 'themes')
        os.rename(os.path.join(themes, 'acme'), os.path.join(themes, 'tmp'))
        os.makedirs(os.path.join(themes, 'acme'))
        os.rename(os.path.join(themes, 'tmp'), os.path.join(themes, 'acme', 'theme'))
        r = self.check(root, 'acme')
        self.assertEqual(r.stdout.splitlines()[0], 'OK self-check: 0 found', r.stdout)

    def test_missing_theme(self):
        r = self.check(fake_site(False), 'nope')
        self.assertEqual(r.returncode, 2)
        self.assertIn('FAIL self-check: no theme folder "nope"', r.stdout)


if __name__ == '__main__':
    unittest.main()
