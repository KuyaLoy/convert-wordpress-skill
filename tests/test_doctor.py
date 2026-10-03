import json
import os
import stat
import tempfile
import unittest

from helpers import run


def touch(path, text=''):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(text)


def fake_bin(folder, tools):
    """Executables that print a version line, so doctor.py can be tested on any machine."""
    os.makedirs(folder, exist_ok=True)
    for name, out in tools.items():
        p = os.path.join(folder, name)
        touch(p, f'#!/bin/sh\necho "{out}"\n')
        os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)
    return folder


class Doctor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='doctor-')
        self.root = os.path.join(self.tmp, 'fs')
        self.home = os.path.join(self.root, 'home')
        os.makedirs(self.home)

    def doctor(self, osname, bin_tools, *extra, cwd=None):
        b = fake_bin(os.path.join(self.tmp, 'bin'), bin_tools)
        out = os.path.join(self.tmp, 'doctor.json')
        r = run('scripts/doctor.py', '--root', self.root, '--home', self.home, '--os', osname, '--json', out, *extra,
                env={'PATH': b}, cwd=cwd or self.tmp)
        data = None
        if os.path.exists(out):
            with open(out, encoding='utf-8') as fh:
                data = json.load(fh)
        return r, data

    def test_windows_laragon_and_xampp(self):
        touch(os.path.join(self.root, 'D', 'laragon', 'www', '.keep'))
        touch(os.path.join(self.root, 'D', 'laragon', 'bin', 'php', 'php-8.3.12-Win32', 'php.exe'))
        touch(os.path.join(self.root, 'C', 'xampp', 'htdocs', '.keep'))
        touch(os.path.join(self.root, 'C', 'xampp', 'php', 'php.exe'))
        r, d = self.doctor('windows', {'py': 'Python 3.12.1', 'node': 'v22.11.0', 'git': 'git version 2.47.0'},
                           '--name', 'Shop Site')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertLessEqual(len(r.stdout.strip().splitlines()), 15, r.stdout)
        self.assertTrue(r.stdout.startswith('OK doctor'), r.stdout)
        names = [s['name'] for s in d['stacks']]
        self.assertIn('Laragon', names)
        self.assertIn('XAMPP', names)
        self.assertEqual(d['python'], 'py -3')
        sug = d['suggestion']
        self.assertEqual(sug['stack'], 'Laragon')
        self.assertEqual(sug['wp_root'], 'D:/laragon/www/shop-site')
        self.assertEqual(sug['url'], 'http://shop-site.test')
        self.assertEqual(sug['serve'], 'vhost')
        xampp = next(s for s in d['stacks'] if s['name'] == 'XAMPP')
        self.assertEqual(xampp['serve'], 'serve-wp')
        self.assertEqual(xampp['www'], 'C:/xampp/htdocs')

    def test_playwright_needed_after_node(self):
        tools = {'python3': 'Python 3.11.4', 'node': 'v20.18.0', 'git': 'git version 2.39.0'}
        mods, cache = os.path.join(self.tmp, 'mods'), os.path.join(self.root, 'pw-cache')
        os.makedirs(mods)
        os.makedirs(cache)
        env = {'NODE_PATH': mods, 'PLAYWRIGHT_BROWSERS_PATH': cache, 'CHROME_PATH': ''}
        b = fake_bin(os.path.join(self.tmp, 'bin'), tools)
        out = os.path.join(self.tmp, 'pw.json')
        args = ('--root', self.root, '--home', self.home, '--os', 'linux', '--json', out)
        r = run('scripts/doctor.py', *args, env={'PATH': b, **env}, cwd=self.tmp)
        self.assertIn('npm install -g playwright', r.stdout)
        with open(out, encoding='utf-8') as fh:
            self.assertIn('playwright', json.load(fh)['missing'])
        touch(os.path.join(mods, 'playwright', 'package.json'), '{}')
        os.makedirs(os.path.join(cache, 'chromium-1194'))
        r = run('scripts/doctor.py', *args, env={'PATH': b, **env}, cwd=self.tmp)
        self.assertNotIn('playwright', r.stdout.lower())

    def test_mac_local_and_mamp(self):
        sites = {'abc': {'name': 'old-shop', 'path': '~/Local Sites/old-shop', 'domain': 'old-shop.local'}}
        touch(os.path.join(self.home, 'Library', 'Application Support', 'Local', 'sites.json'), json.dumps(sites))
        touch(os.path.join(self.root, 'Applications', 'MAMP', 'htdocs', '.keep'))
        r, d = self.doctor('mac', {'python3': 'Python 3.11.4', 'node': 'v20.18.0', 'git': 'git version 2.39.0'},
                           '--name', 'cafe')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        local = next(s for s in d['stacks'] if s['name'] == 'Local')
        self.assertEqual(local['sites'][0]['domain'], 'old-shop.local')
        self.assertEqual(d['suggestion']['stack'], 'Local')
        self.assertEqual(d['suggestion']['wordpress'], 'existing')
        self.assertEqual(d['suggestion']['url'], 'http://cafe.local')
        self.assertTrue(d['suggestion']['wp_root'].endswith('/Local Sites/cafe/app/public'))
        mamp = next(s for s in d['stacks'] if s['name'] == 'MAMP')
        self.assertEqual(mamp['db']['port'], 8889)

    def test_nothing_installed(self):
        r, d = self.doctor('windows', {'python': 'Python 3.10.0'})
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertTrue(r.stdout.startswith('WARN doctor'), r.stdout)
        self.assertEqual(d['stacks'], [])
        self.assertIn('localwp.com', r.stdout)
        self.assertIn('winget install -e --id OpenJS.NodeJS.LTS', r.stdout)
        self.assertIn('winget install -e --id Git.Git', r.stdout)

    def test_synced_folder_and_spaces(self):
        cwd = os.path.join(self.home, 'OneDrive', 'My Projects')
        os.makedirs(cwd)
        touch(os.path.join(self.root, 'opt', 'lampp', 'htdocs', '.keep'))
        r, d = self.doctor('linux', {'python3': 'Python 3.12.0', 'node': 'v22.0.0', 'git': 'git version 2.40.0'},
                           cwd=cwd)
        self.assertEqual(r.returncode, 0, r.stdout)
        kinds = {w['kind'] for w in d['warnings']}
        self.assertIn('synced', kinds)
        self.assertIn('spaces', kinds)


if __name__ == '__main__':
    unittest.main()
