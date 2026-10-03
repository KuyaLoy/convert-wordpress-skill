import json
import os
import tempfile
import unittest

from helpers import path, run


def read(p):
    with open(p, encoding='utf-8') as fh:
        return fh.read()


class Start(unittest.TestCase):
    def test_start_writes_and_keeps_intake_handoff(self):
        root = os.path.join(tempfile.mkdtemp(), 'shop')
        r = run('scripts/new-site.py', '--start', root, '--name', 'Corner Shop')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for f in ('handoff.md', 'ai-handoff-summary.md'):
            self.assertIn('kit:intake', read(os.path.join(root, f)))
        self.assertIn('Corner Shop', read(os.path.join(root, 'ai-handoff-summary.md')))
        with open(os.path.join(root, 'handoff.md'), 'a', encoding='utf-8') as fh:
            fh.write('\n- the developer chose Laragon\n')
        r = run('scripts/new-site.py', '--start', root)
        self.assertEqual(r.returncode, 0)
        self.assertIn('the developer chose Laragon', read(os.path.join(root, 'handoff.md')))

    def test_plan_only_replaces_intake_files_and_keeps_notes(self):
        tmp = tempfile.mkdtemp()
        root = os.path.join(tmp, 'shop')
        run('scripts/new-site.py', '--start', root, '--name', 'Corner Shop')
        with open(os.path.join(root, 'handoff.md'), 'a', encoding='utf-8') as fh:
            fh.write('\n- answer: lead emails go to the owner\n')
        site = json.loads(read(path('assets', 'site.example.json')))
        site.update(site_name='Corner Shop', legal_name='Corner Shop LLC', domain='cornershop.example.org',
                    wp_root=root, local_host='shop.test', site_dir='shop', theme='shop', prefix='shop', key='cs')
        os.makedirs(os.path.join(root, '_plan'), exist_ok=True)
        sj = os.path.join(root, '_plan', 'site.json')
        with open(sj, 'w', encoding='utf-8') as fh:
            json.dump(site, fh)
        r = run('scripts/new-site.py', sj, '--plan-only')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        h = read(os.path.join(root, 'handoff.md'))
        self.assertNotIn('kit:intake', h)
        self.assertIn('answer: lead emails go to the owner', h)
        self.assertNotIn('kit:intake', read(os.path.join(root, 'ai-handoff-summary.md')))

    def test_force_keeps_the_content_model(self):
        tmp = tempfile.mkdtemp()
        root = os.path.join(tmp, 'shop')
        os.makedirs(os.path.join(root, '_plan'))
        site = json.loads(read(path('assets', 'site.example.json')))
        site.update(site_name='Corner Shop', legal_name='Corner Shop LLC', domain='cornershop.example.org',
                    wp_root=root, local_host='shop.test', site_dir='shop', theme='shop', prefix='shop', key='cs')
        sj = os.path.join(root, '_plan', 'site.json')
        with open(sj, 'w', encoding='utf-8') as fh:
            json.dump(site, fh)
        self.assertEqual(run('scripts/new-site.py', sj, '--plan-only').returncode, 0)
        spec = os.path.join(root, '_plan', 'tools', 'acf', 'build_field_groups.py')
        with open(spec, 'a', encoding='utf-8') as fh:
            fh.write('\n# THE SHOP CONTENT MODEL\n')
        r = run('scripts/new-site.py', sj, '--plan-only', '--force')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('THE SHOP CONTENT MODEL', read(spec))

    def test_example_values_refused(self):
        tmp = tempfile.mkdtemp()
        site = json.loads(read(path('assets', 'site.example.json')))
        site['wp_root'] = os.path.join(tmp, 'x')
        site['local_host'] = 'x.test'
        sj = os.path.join(tmp, 'site.json')
        with open(sj, 'w', encoding='utf-8') as fh:
            json.dump(site, fh)
        r = run('scripts/new-site.py', sj, '--plan-only')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('example', (r.stdout + r.stderr).lower())


class AnalyzeEnv(unittest.TestCase):
    def test_env_fills_the_draft(self):
        tmp = tempfile.mkdtemp()
        src = os.path.join(tmp, 'shop-source')
        os.makedirs(src)
        with open(os.path.join(src, 'index.html'), 'w') as fh:
            fh.write('<!doctype html><html lang="en"><body><h1>Hi</h1></body></html>')
        doc = os.path.join(tmp, 'doctor.json')
        with open(doc, 'w') as fh:
            json.dump({'suggestion': {'stack': 'Local', 'wp_root': '/u/Local Sites/shop/app/public',
                                      'url': 'http://shop.local', 'serve': 'local-app', 'wordpress': 'existing'}}, fh)
        draft = os.path.join(tmp, 'plan', 'site.json')
        r = run('scripts/analyze-source.py', src, '--env', doc, '--site-draft', draft)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        d = json.loads(read(draft))
        self.assertEqual(d['wp_root'], '/u/Local Sites/shop/app/public')
        self.assertEqual(d['local_host'], 'shop.local')
        self.assertEqual(d['site_dir'], 'shop')
        self.assertEqual(d['wordpress'], 'existing')


if __name__ == '__main__':
    unittest.main()
