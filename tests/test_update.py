import functools
import http.server
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import zipfile

from helpers import load, path

up = load('scripts/update.py', 'update')

OLD_LOG = """# Changelog

## [Unreleased]

## [0.4.0] - 2026-10-03

Any local setup, plain words for newcomers.

### Added

- doctor.py
"""
NEW_LOG = OLD_LOG.replace('## [Unreleased]\n', """## [Unreleased]

## [0.5.0] - 2026-10-10

### Added

- Sections copied by script, not typed by the agent.
""")
SKILL = '---\nname: convert-to-wordpress\ndescription: test\n---\n\n# Skill\n'


def put(p, text):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as fh:
        fh.write(text)


def read(p):
    with open(p, encoding='utf-8') as fh:
        return fh.read()


def skill_files(log):
    return {
        'SKILL.md': SKILL,
        'CHANGELOG.md': log,
        'scripts/update.py': read(path('scripts', 'update.py')),
        'assets/update-command/update-convert-wordpress-skill.md': read(
            path('assets', 'update-command', 'update-convert-wordpress-skill.md')),
    }


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class Update(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='upd-')
        self.skills = os.path.join(self.tmp, 'skills')
        self.skill = os.path.join(self.skills, 'convert-to-wordpress')
        files = skill_files(OLD_LOG)
        files.update({'references/old.md': 'old guide', 'profile.local.json': '{"developer": "me"}'})
        for rel, text in files.items():
            put(os.path.join(self.skill, rel), text)
        self.www = os.path.join(self.tmp, 'www')
        put(os.path.join(self.www, 'raw', 'CHANGELOG.md'), NEW_LOG)
        os.makedirs(os.path.join(self.www, 'zips', 'tags'))
        self.release({**skill_files(NEW_LOG), 'references/new.md': 'new guide'})
        handler = functools.partial(Quiet, directory=self.www)
        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        base = f'http://127.0.0.1:{self.server.server_port}'
        self.env = dict(os.environ, UPDATE_RAW_BASE=base + '/raw', UPDATE_ZIP_BASE=base + '/zips')

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def release(self, files, top='convert-wordpress-skill-0.5.0'):
        with zipfile.ZipFile(os.path.join(self.www, 'zips', 'tags', 'v0.5.0.zip'), 'w') as z:
            for rel, text in files.items():
                z.writestr(rel if rel.startswith('..') else f'{top}/{rel}', text)

    def run_update(self, *args, folder=None):
        script = os.path.join(folder or self.skill, 'scripts', 'update.py')
        return subprocess.run([sys.executable, script, *args], capture_output=True, text=True, env=self.env,
                              timeout=120)

    def test_versions_and_summary(self):
        v = up.versions(NEW_LOG)
        self.assertEqual([x[1] for x in v], ['0.5.0', '0.4.0'])
        self.assertEqual(v[0][3], 'Sections copied by script, not typed by the agent.')
        self.assertEqual(v[1][3], 'Any local setup, plain words for newcomers.')
        wrapped = '## [0.3.0] - 2026-10-03\n\n### Added\n\n- One-command start: a long first item that goes on\n  to the next line.\n- Second.\n'
        self.assertEqual(up.versions(wrapped)[0][3], 'One-command start: a long first item that goes on to the next line.')

    def test_check_finds_a_newer_version_and_changes_nothing(self):
        r = self.run_update('--check')
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertTrue(r.stdout.startswith('WARN update: 0.5.0 is out (installed: 0.4.0)'), r.stdout)
        self.assertIn('- 0.5.0 (2026-10-10): Sections copied by script', r.stdout)
        self.assertNotIn('[0.5.0]', read(os.path.join(self.skill, 'CHANGELOG.md')))
        self.assertFalse(os.path.exists(os.path.join(self.skill, '_backups')))

    def test_up_to_date(self):
        put(os.path.join(self.www, 'raw', 'CHANGELOG.md'), OLD_LOG)
        r = self.run_update('--check')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.startswith('OK update: convert-to-wordpress 0.4.0 is the newest'), r.stdout)

    def test_zip_update_keeps_private_files_and_backs_up(self):
        r = self.run_update()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.startswith('OK update: 0.4.0 -> 0.5.0 (zip from GitHub; backup _backups'), r.stdout)
        self.assertTrue(os.path.exists(os.path.join(self.skill, 'references', 'new.md')))
        self.assertFalse(os.path.exists(os.path.join(self.skill, 'references', 'old.md')))
        self.assertEqual(read(os.path.join(self.skill, 'profile.local.json')), '{"developer": "me"}')
        self.assertIn('## [0.5.0]', read(os.path.join(self.skill, 'CHANGELOG.md')))
        backups = os.listdir(os.path.join(self.skill, '_backups'))
        self.assertEqual(len(backups), 1)
        with zipfile.ZipFile(os.path.join(self.skill, '_backups', backups[0])) as z:
            self.assertIn('references/old.md', z.namelist())
            self.assertIn('profile.local.json', z.namelist())

    def test_unsafe_download_changes_nothing(self):
        self.release({**skill_files(NEW_LOG), '../evil.txt': 'x'})
        r = self.run_update()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn('unsafe path', r.stdout)
        self.assertTrue(os.path.exists(os.path.join(self.skill, 'references', 'old.md')))
        self.assertFalse(os.path.exists(os.path.join(self.tmp, 'evil.txt')))

    def test_wrong_download_changes_nothing(self):
        self.release({'SKILL.md': '---\nname: something-else\n---\n', 'CHANGELOG.md': NEW_LOG})
        r = self.run_update()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn('does not look like this skill', r.stdout)
        self.assertNotIn('[0.5.0]', read(os.path.join(self.skill, 'CHANGELOG.md')))

    def test_project_copy_refused(self):
        project = os.path.join(self.tmp, 'site', '_plan')
        put(os.path.join(project, 'scripts', 'update.py'), read(path('scripts', 'update.py')))
        r = self.run_update(folder=project)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn('run it from the skill folder', r.stdout)

    def test_add_command_next_to_the_skill(self):
        put(os.path.join(self.www, 'raw', 'CHANGELOG.md'), OLD_LOG)
        r = self.run_update('--add-command')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        cmd = os.path.join(self.skills, 'update-convert-wordpress-skill', 'SKILL.md')
        self.assertIn('name: update-convert-wordpress-skill', read(cmd))
        self.assertIn('Command added', r.stdout)

    def test_add_command_needs_a_skills_folder(self):
        other = os.path.join(self.tmp, 'projects', 'convert-to-wordpress')
        shutil.copytree(self.skill, other)
        put(os.path.join(self.www, 'raw', 'CHANGELOG.md'), OLD_LOG)
        r = self.run_update('--add-command', folder=other)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('Command not added', r.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, 'projects', 'update-convert-wordpress-skill')))


@unittest.skipUnless(shutil.which('git'), 'needs git')
class GitUpdate(Update):
    def setUp(self):
        super().setUp()
        shutil.rmtree(self.skill)
        g = ['git', '-c', 'user.name=t', '-c', 'user.email=t@example.org', '-c', 'init.defaultBranch=main']
        self.g = g
        work, bare = os.path.join(self.tmp, 'work'), os.path.join(self.tmp, 'remote.git')
        for rel, text in skill_files(OLD_LOG).items():
            put(os.path.join(work, rel), text)
        put(os.path.join(work, '.gitignore'), '/profile.local.json\n')
        for cmd in (['init', '-q'], ['add', '-A'], ['commit', '-qm', '0.4.0']):
            subprocess.run(g + cmd, cwd=work, check=True, capture_output=True)
        subprocess.run(g + ['clone', '-q', '--bare', work, bare], check=True, capture_output=True)
        subprocess.run(g + ['clone', '-q', bare, self.skill], check=True, capture_output=True)
        put(os.path.join(self.skill, 'profile.local.json'), '{"developer": "me"}')
        put(os.path.join(work, 'CHANGELOG.md'), NEW_LOG)
        put(os.path.join(work, 'references', 'new.md'), 'new guide')
        for cmd in (['add', '-A'], ['commit', '-qm', '0.5.0'], ['push', '-q', bare, 'HEAD:main']):
            subprocess.run(g + cmd, cwd=work, check=True, capture_output=True)

    def test_git_update_keeps_private_files(self):
        r = self.run_update()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.startswith('OK update: 0.4.0 -> 0.5.0 (git pull)'), r.stdout)
        self.assertTrue(os.path.exists(os.path.join(self.skill, 'references', 'new.md')))
        self.assertEqual(read(os.path.join(self.skill, 'profile.local.json')), '{"developer": "me"}')
        self.assertFalse(os.path.exists(os.path.join(self.skill, '_backups')))

    def test_local_edits_stop_the_update(self):
        put(os.path.join(self.skill, 'SKILL.md'), SKILL + '\nmy own rule\n')
        r = self.run_update()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn('local edits', r.stdout)
        self.assertIn('SKILL.md', r.stdout)
        self.assertIn('my own rule', read(os.path.join(self.skill, 'SKILL.md')))
        self.assertNotIn('[0.5.0]', read(os.path.join(self.skill, 'CHANGELOG.md')))

    # The zip-only cases do not apply to a git clone.
    test_zip_update_keeps_private_files_and_backs_up = None
    test_unsafe_download_changes_nothing = None
    test_wrong_download_changes_nothing = None
    test_project_copy_refused = None
    test_add_command_needs_a_skills_folder = None


if __name__ == '__main__':
    unittest.main()
