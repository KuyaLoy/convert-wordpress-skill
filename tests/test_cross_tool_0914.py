"""0.9.14: the skill outside Claude Code (Codex, Antigravity, T3 Code). The docs' grep checks have a Python twin
that gives the same hits, the progress page works as a local file, and SKILL.md points every other tool to its
fallbacks."""
import io
import os
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
import webbrowser
from contextlib import redirect_stdout
from unittest import mock

from helpers import path, run
from test_phases import board

TC = 'scripts/report/text-check.py'
BASH = shutil.which('bash')
GREP_OK = bool(BASH) and subprocess.run([BASH, '-c', 'command -v grep sed sort uniq'], capture_output=True).returncode == 0


def write(p, text, mode='w'):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if mode == 'wb':
        with open(p, 'wb') as fh:
            fh.write(text)
    else:
        with open(p, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)


def read(p):
    with open(p, encoding='utf-8') as fh:
        return fh.read()


def bash(cmd, cwd):
    return subprocess.run([BASH, '-c', cmd], capture_output=True, text=True, cwd=cwd).stdout


def theme():
    t = tempfile.mkdtemp()
    write(os.path.join(t, 'includes', 'a.php'), '<?php\nfunction kitwp_one() {}\nfunction kitwp_two( $x ) {}\n')
    write(os.path.join(t, 'includes', 'b.php'), '<?php\nfunction kitwp_two() {}\n  function kitwp_inner() {}\n')
    write(os.path.join(t, 'template-parts', 'hero.php'),
          '<div class="mt-[13px] w-[#fff]">\n<?php // phpcs:ignore WordPress.X -- reason ?>\n<p>Node 12:34</p>\n'
          '<p>ABC-T5 tag</p>\n<p class="plain">ok</p>\n')
    write(os.path.join(t, 'assets', 'site.css'), '.a{color:#ff0000}\n.b{color:#00ff00} /* tokens */\n.c{color:red}\n')
    write(os.path.join(t, 'assets', 'app.js'), 'const t = "10:30";\n')
    write(os.path.join(t, 'node_modules', 'x', 'i.js'), 'const z = "mt-[1px] 9:9";\n')
    write(os.path.join(t, 'vendor', 'v.php'), '<?php // phpcs:ignore all\n')
    write(os.path.join(t, 'src', 'Hero.tsx'), 'export const H = () => <div className="pt-[22px]" />;\n')
    write(os.path.join(t, 'src', 'Card.jsx'), 'const id = "PRJ-T12";\n')
    write(os.path.join(t, '.next', 'server', 'page.js'), 'const z = "mt-[1px] 9:9";\n')
    return t


class TextCheck(unittest.TestCase):
    def test_fill_finds_left_markers(self):
        t = tempfile.mkdtemp()
        report = os.path.join(t, 'report.html')
        write(report, '<p>Done</p>\n<p>[[SUMMARY]]</p>\n')
        r = run(TC, 'fill', report)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn(f'{report}:2:<p>[[SUMMARY]]</p>', r.stdout)
        self.assertTrue(r.stdout.strip().endswith('FAIL fill: 1 "[[" left to fill'), r.stdout)
        write(report, '<p>Done</p>\n')
        r = run(TC, 'fill', report)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, 'OK fill: nothing left to fill'))

    def test_plain_fails_on_markers_and_dashes_and_lists_jargon(self):
        t = tempfile.mkdtemp()
        msg = os.path.join(t, 'client-message.md')
        write(msg, 'Hi {{NAME}},\nYour site is live — enjoy.\nThe plugin is updated.\n')
        r = run(TC, 'plain', msg)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn(':1:Hi {{NAME}},', r.stdout)
        self.assertIn(':2:Your site is live', r.stdout)
        self.assertIn(':3:The plugin is updated.', r.stdout)
        self.assertIn('FAIL plain: 2 "[[", "{{" or em dash hits', r.stdout)
        write(msg, 'Hi Sam,\nThe plugin is updated.\n')
        r = run(TC, 'plain', msg)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn('OK plain: nothing to fill, no em dashes; 1 jargon hits to read', r.stdout)

    def test_dupes_finds_a_name_in_two_files(self):
        t = theme()
        r = run(TC, 'dupes', t)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn('duplicate function kitwp_two: includes/a.php:3 and includes/b.php:2', r.stdout)
        self.assertNotIn('kitwp_inner', r.stdout)  # indented: not a global function at line start
        os.remove(os.path.join(t, 'includes', 'b.php'))
        r = run(TC, 'dupes', t)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, 'OK dupes: 2 functions, no duplicates'))

    @unittest.skipUnless(GREP_OK, 'no bash with grep')
    def test_dupes_matches_the_grep_line(self):
        t = theme()
        grep = bash("grep -h \"^function\" includes/*.php | sed 's/(.*//' | sort | uniq -d", t).split()
        names = re.findall(r'duplicate function (\w+)', run(TC, 'dupes', t).stdout)
        self.assertEqual(sorted(names), sorted(x for x in grep if x != 'function'))

    def test_oneoff_hits_and_skips(self):
        t = theme()
        r = run(TC, 'oneoff', t)
        self.assertEqual(r.returncode, 0, r.stdout)
        out = r.stdout
        self.assertIn('template-parts/hero.php:1:[one-off value]', out)
        self.assertIn('assets/site.css:1:[raw hex]', out)
        self.assertNotIn('assets/site.css:2:', out)  # a tokens line is left out, as | grep -v tokens does
        self.assertIn('template-parts/hero.php:3:[node ID or ticket tag]', out)
        self.assertIn('template-parts/hero.php:4:[node ID or ticket tag]', out)
        self.assertIn('assets/app.js:1:[node ID or ticket tag]', out)
        self.assertIn('template-parts/hero.php:2:[phpcs ignore]', out)
        self.assertNotIn('node_modules', out)
        self.assertNotIn('vendor', out)
        self.assertIn('src/Hero.tsx:1:[one-off value]', out)  # 0.9.15: React files too
        self.assertIn('src/Card.jsx:1:[node ID or ticket tag]', out)
        self.assertNotIn('.next', out)  # a Next.js build folder is skipped like node_modules
        self.assertIn('OK oneoff: 8 hits', out)

    @unittest.skipUnless(GREP_OK, 'no bash with grep')
    def test_oneoff_matches_the_grep_lines(self):
        t = theme()
        x = ('--exclude-dir=node_modules --exclude-dir=vendor --exclude-dir=tests --exclude-dir=dist --exclude-dir=build'
             ' --exclude-dir=.next')
        r = "--include='*.php' --include='*.js' --include='*.jsx' --include='*.tsx'"
        cmds = [f"grep -rnE {x} {r} -e '[a-z]-\\[(#|[0-9])' .",
                f"grep -rnE {x} --include='*.css' --include='*.scss' -e '#[0-9a-fA-F]{{3,8}}\\b' . | grep -v tokens",
                f"grep -rnE {x} {r} -e '[0-9]+:[0-9]+|\\b[A-Z][A-Z0-9]+-T[0-9]+\\b' .",
                f"grep -rn {x} --include='*.php' -e 'phpcs:ignore' -e 'phpcs:disable' ."]
        want = set()
        for c in cmds:
            for line in bash(c, t).splitlines():
                f, n = line.split(':')[:2]
                want.add((f[2:] if f.startswith('./') else f, n))
        got = {tuple(m) for m in re.findall(r'^([^:\n]+):(\d+):\[', run(TC, 'oneoff', t).stdout, re.M)}
        self.assertEqual(got, want)

    def test_placeholders_reads_text_and_skips_binaries(self):
        t = tempfile.mkdtemp()
        seed = os.path.join(t, '_setup', 'seed')
        write(os.path.join(seed, 'pages.json'), '{"about": "[PLACEHOLDER: team photo]"}\n')
        write(os.path.join(seed, 'media', 'PLACEHOLDER.png'), b'\x89PNG\r\n\x00PLACEHOLDER', 'wb')
        r = run(TC, 'placeholders', cwd=t)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn('pages.json:1:', r.stdout)
        self.assertIn('OK placeholders: 1 ', r.stdout)

    def test_usage(self):
        self.assertEqual(run(TC).returncode, 2)
        self.assertEqual(run(TC, 'fill').returncode, 2)
        self.assertEqual(run(TC, 'dupes', os.path.join(tempfile.mkdtemp(), 'none')).returncode, 2)


class LocalProgressPage(unittest.TestCase):
    def test_refresh_adds_the_reload_and_default_has_none(self):
        tmp = tempfile.mkdtemp()
        p, out = board(tmp), os.path.join(tmp, 'progress.html')
        self.assertEqual(run('scripts/build-map/render.py', p, out).returncode, 0)
        self.assertNotIn('http-equiv="refresh"', read(out))  # Claude's published page is unchanged
        r = run('scripts/build-map/render.py', p, out, '--refresh', '30')
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn('<meta http-equiv="refresh" content="30">', read(out))
        for bad in ([], ['2'], ['soon']):
            r = run('scripts/build-map/render.py', p, out, '--refresh', *bad)
            self.assertEqual(r.returncode, 2, r.stdout)
            self.assertIn('FAIL render: --refresh needs seconds', r.stdout)

    def test_open_opens_the_local_file(self):
        tmp = tempfile.mkdtemp()
        p, out = board(tmp), os.path.join(tmp, 'progress.html')
        buf = io.StringIO()
        with mock.patch.object(webbrowser, 'open', return_value=True) as opened, \
                mock.patch.object(sys, 'argv', ['render.py', p, out, '--open']), redirect_stdout(buf):
            runpy.run_path(path('scripts', 'build-map', 'render.py'), run_name='__main__')
        uri = opened.call_args[0][0]
        self.assertTrue(uri.startswith('file:') and uri.endswith('/progress.html'), uri)
        self.assertIn(f'opened: {uri}', buf.getvalue())


class Docs(unittest.TestCase):
    skill = read(path('SKILL.md'))
    agents = read(path('references', 'agents.md'))

    def test_description_carries_trigger_words(self):
        desc = re.search(r'^description: (.*)$', self.skill, re.M).group(1)
        self.assertLessEqual(len(desc), 1024)
        for words in ('convert this site to WordPress', 'migrate my website to WordPress', 'rebuild it in WordPress',
                      'to WordPress', 'WordPress conversion'):
            self.assertIn(words, desc)

    def test_skill_size_and_open_first(self):
        lines = self.skill.splitlines()
        self.assertLess(len(lines), 500)
        top = '\n'.join(lines[:30])
        self.assertIn('**Open first:**', top)
        self.assertIn('`references/agents.md` > Per tool', top)

    def test_per_tool_section(self):
        self.assertIn('## Per tool: Claude Code, Codex, Antigravity, T3 Code', self.agents)
        sec = self.agents.split('## Per tool:')[1].split('\n## ')[0]
        self.assertIn('| Step | Claude Code (CLI, desktop app) | Codex | Antigravity | Any other agent |', sec)
        for row in ('Load the skill', 'Ask the developer', 'QA check', 'Browser steps', 'The progress page',
                    'Context used', 'title', 'Hooks'):
            self.assertRegex(sec, rf'\n\| [^|\n]*{row}')
        for word in ('request_user_input', 'spawn_agent', 'invoke_subagent', '$convert-to-wordpress', '/status',
                     '--refresh 30 --open', 'T3 Code'):
            self.assertIn(word, sec)

    def test_scripts_table_moved_whole(self):
        listed = read(path('references', 'scripts.md'))
        for f in ('doctor.py', 'start.py', 'new-site.py', 'setup/setup.py', 'leads-check.py', 'text-check.py',
                  'gate.py', 'self-check.py', 'check-section.py', 'update.py'):
            self.assertIn(f, listed)
            self.assertTrue(any(os.path.isfile(os.path.join(d, os.path.basename(f)))
                                for d, _, _ in os.walk(path('scripts'))), f)
        self.assertIn('`references/scripts.md`', self.skill)
        self.assertNotIn('## Scripts at a glance', self.skill)

    def test_every_shell_only_check_has_its_python_twin(self):
        docs = ['SKILL.md', 'assets/launch/RUNBOOK.template.md'] + [
            'references/' + f for f in os.listdir(path('references')) if f.endswith('.md')]
        for d in docs:
            lines = read(path(*d.split('/'))).splitlines()
            for i, line in enumerate(lines):
                if re.search(r'uniq -d|grep -n "\\\[\\\[|grep -rn "PLACEHOLDER"|grep -rnE \$X', line):
                    near = '\n'.join(lines[max(0, i - 8):i + 9])
                    self.assertIn('text-check.py', near, f'{d}:{i + 1}: {line}')
                if re.search(r'`curl -', line):
                    near = '\n'.join(lines[max(0, i - 2):i + 4])
                    self.assertIn('curl.exe', near, f'{d}:{i + 1}: {line}')


if __name__ == '__main__':
    unittest.main()
