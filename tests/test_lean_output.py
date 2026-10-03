import json
import os
import tempfile
import unittest

from helpers import path, run

PAGE = '<html><body><header><nav class="n"><a>Home</a></nav></header><main><h1>x</h1></main>{footer}</body></html>'


def write(p, text):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as fh:
        fh.write(text)


class LeanOutput(unittest.TestCase):
    def test_domdiff_same_is_one_line(self):
        tmp = tempfile.mkdtemp()
        a = os.path.join(tmp, 'a.html')
        write(a, PAGE.format(footer='<footer><p>c</p></footer>'))
        r = run('scripts/parity/domdiff.py', a, a)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(r.stdout.strip().splitlines(), ['OK domdiff: 2 same, 0 differ'])

    def test_domdiff_diff_is_short(self):
        tmp = tempfile.mkdtemp()
        a, b = os.path.join(tmp, 'a.html'), os.path.join(tmp, 'b.html')
        write(a, PAGE.format(footer='<footer>' + '<p class="x">c</p>' * 60 + '</footer>'))
        write(b, PAGE.format(footer='<footer>' + '<span>c</span>' * 60 + '</footer>'))
        r = run('scripts/parity/domdiff.py', a, b)
        lines = r.stdout.strip().splitlines()
        self.assertEqual(r.returncode, 1)
        self.assertTrue(lines[0].startswith('FAIL domdiff: 1 same, 1 differ'), lines[0])
        self.assertLessEqual(len(lines), 25)
        self.assertIn('-v shows them', r.stdout)

    def test_gate_first_line(self):
        tmp = tempfile.mkdtemp()
        root = os.path.join(tmp, 'shop')
        with open(path('assets', 'site.example.json'), encoding='utf-8') as fh:
            site = json.load(fh)
        site.update(site_name='Corner Shop', domain='cornershop.example.org', wp_root=root, local_host='shop.test',
                    site_dir='shop', theme='shop', prefix='shop', key='cs')
        sj = os.path.join(root, '_plan', 'site.json')
        write(sj, json.dumps(site))
        self.assertEqual(run('scripts/new-site.py', sj, '--plan-only').returncode, 0)
        r = run('scripts/build-map/gate.py', os.path.join(root, 'BUILD-MAP.md'))
        lines = r.stdout.strip().splitlines()
        self.assertTrue(lines[0].startswith('WARN gate: S0'), lines[0])
        self.assertLessEqual(len(lines), 20)


if __name__ == '__main__':
    unittest.main()
