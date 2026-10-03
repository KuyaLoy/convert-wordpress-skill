import json
import unittest

from helpers import path


class ExampleFiles(unittest.TestCase):
    def test_profile_is_neutral(self):
        p = json.load(open(path('profile.example.json'), encoding='utf-8'))
        local = p['local']
        for k in ('stack', 'www', 'url'):
            self.assertEqual(local.get(k, ''), '', f'local.{k} must be empty: doctor.py fills it')
        text = json.dumps(p).lower()
        self.assertNotIn('d:/laragon', text)
        self.assertIn(p.get('level'), ('new', 'developer'))
        self.assertIn(p.get('oks'), ('group', 'each'))

    def test_site_example_has_no_machine_paths(self):
        s = json.load(open(path('assets', 'site.example.json'), encoding='utf-8'))
        self.assertEqual(s['wp_root'], '', 'wp_root comes from the intake (doctor.py suggests it)')
        self.assertEqual(s['local_host'], '', 'local_host comes from the intake (doctor.py suggests it)')


if __name__ == '__main__':
    unittest.main()
