"""The 0.8 phase board: gate.py rules, render.py, and install-wp.py's local-only guard."""
import json
import os
import re
import tempfile
import unittest

from helpers import path, run

FINDINGS_HEAD = '| ID | Phase | Where | Finding | Severity | Status |\n|---|---|---|---|---|---|\n'


def board(tmp, edit=None):
    with open(path('assets', 'build-map', 'BUILD-MAP.template.md'), encoding='utf-8') as fh:
        text = fh.read().replace('{{SITE_NAME}}', 'Corner Shop').replace('{{DATE}}', '18 Nov 2026')
    if edit:
        text = edit(text)
    p = os.path.join(tmp, 'BUILD-MAP.md')
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    return p


def rewrite(p, edit):
    with open(p, encoding='utf-8') as fh:
        text = edit(fh.read())
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def done_steps(text, phase):
    return re.sub(rf'(\| P{phase}-0\d \| [^|]+\| )(IN PROGRESS|TODO)', r'\1DONE', text)


def close_p0(text):
    return done_steps(text, 0).replace('| Plan OK | |', '| Plan OK | ok 18 Nov 2026 |')


def finding(text, row):
    return text.replace(FINDINGS_HEAD, FINDINGS_HEAD + row + '\n')


def set_phase(text, num, name, status):
    text = re.sub(rf'(## Phase {num}: {re.escape(name)}) \((IN PROGRESS|TODO|DONE)\)', rf'\1 ({status})', text)
    return re.sub(rf'(\| P{num} {re.escape(name)} \|[^|]+\| )(IN PROGRESS|TODO|DONE)( \| )', rf'\g<1>{status}\3', text)


class Gate(unittest.TestCase):
    def gate(self, p, *args):
        return run('scripts/build-map/gate.py', p, *args)

    def test_new_board_is_open_at_p0(self):
        r = self.gate(board(tempfile.mkdtemp()))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertTrue(r.stdout.startswith('WARN gate: P0 Plan'), r.stdout)
        self.assertIn('Plan OK', r.stdout)

    def test_plan_ok_closes_p0_and_opens_p1(self):
        p = board(tempfile.mkdtemp(), close_p0)
        self.assertEqual(self.gate(p).returncode, 0)
        r = self.gate(p, '--close')
        self.assertEqual(r.returncode, 0, r.stdout)
        with open(p, encoding='utf-8') as fh:
            text = fh.read()
        self.assertIn('## Phase 0: Plan (DONE)', text)
        self.assertIn('## Phase 1: Setup (IN PROGRESS)', text)
        self.assertIn('| Phase: **P1 Setup** | Next: **P2 Pages**', text)
        self.assertIn('P0 Plan closed', text)

    def test_work_ahead_breaks_the_rules(self):
        r = self.gate(board(tempfile.mkdtemp(), lambda t: done_steps(t, 2)))
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn('no work ahead', r.stdout)

    def test_bad_values_break_the_rules(self):
        def bad(t):
            t = t.replace('| Home | `/` | Hero | todo |', '| Home | `/` | Hero | done |')
            return finding(t, '| F-001 | P1 | Global / Header | logo blurry | high | open |')
        r = self.gate(board(tempfile.mkdtemp(), bad))
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("status 'done'", r.stdout)
        self.assertIn("severity 'high'", r.stdout)

    def test_phase_needs_its_qa_run_and_no_open_blocker(self):
        def p1_ready(t):
            t = set_phase(close_p0(t), 0, 'Plan', 'DONE')
            t = set_phase(t, 1, 'Setup', 'IN PROGRESS')
            return finding(done_steps(t, 1), '| F-001 | P1 | wp-admin | white screen | blocker | open |')
        p = board(tempfile.mkdtemp(), p1_ready)
        r = self.gate(p)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn('blocker F-001', r.stdout)
        self.assertIn('the phase QA run', r.stdout)

        def fixed(t):
            t = t.replace('| blocker | open |', '| blocker | fixed |')
            return re.sub(r'(\| P1 Setup \|[^|]+\| IN PROGRESS \| )', r'\g<1>18 Nov 2026: 1 found', t)
        rewrite(p, fixed)
        r = self.gate(p)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_fix_loop_needs_zero_found_and_go_live(self):
        def p5(t):
            for n, name in enumerate(('Plan', 'Setup', 'Pages', 'Forms and email', 'SEO, security, speed')):
                t = set_phase(done_steps(t, n), n, name, 'DONE')
            t = set_phase(t, 5, 'Fix and QA loop', 'IN PROGRESS')
            t = done_steps(t, 5).replace('| Plan OK | |', '| Plan OK | ok 1 Nov 2026 |')
            t = t.replace('| todo |', '| checked |')
            return finding(t, '| F-001 | P2 | Home / Hero | 2 px shift | minor | open |')
        p = board(tempfile.mkdtemp(), p5)
        r = self.gate(p)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn('finding F-001 is open', r.stdout)
        self.assertIn('0 found', r.stdout)
        self.assertIn('Go-live', r.stdout)

        def done(t):
            t = t.replace('| minor | open |', '| minor | fixed |')
            t = t.replace('| Go-live | |', '| Go-live | ok 18 Nov 2026 |')
            return re.sub(r'(\| P5 Fix and QA loop \|[^|]+\| IN PROGRESS \| )', r'\g<1>18 Nov 2026: 0 found', t)
        rewrite(p, done)
        r = self.gate(p)
        self.assertEqual(r.returncode, 0, r.stdout)


class Render(unittest.TestCase):
    def test_progress_page_and_shared_json(self):
        tmp = tempfile.mkdtemp()
        p = board(tmp, lambda t: finding(t, '| F-001 | P1 | Global / Header | logo <b>blurry</b> | major | open |'))
        out = os.path.join(tmp, 'progress.html')
        r = run('scripts/build-map/render.py', p, out)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith('ok: 9 phases, 5 sections'), r.stdout)
        with open(os.path.join(tmp, 'progress.json'), encoding='utf-8') as fh:
            data = json.load(fh)
        self.assertEqual(sorted(data), ['blocked', 'figma', 'findings', 'log', 'next', 'now', 'pages', 'phases', 'site',
                                        'target', 'updated', 'url', 'waiting'])
        self.assertEqual([x['id'] for x in data['phases']],
                         ['plan', 'setup', 'pages', 'forms', 'seo', 'fix', 'qa', 'golive', 'live'])
        self.assertEqual(data['phases'][0]['status'], 'doing')
        home = next(x for x in data['pages'] if x['slug'] == 'home')
        self.assertEqual((home['route'], home['sections']), ('/', [{'slug': 'hero', 'status': 'todo'}]))
        self.assertEqual(len(next(x for x in data['pages'] if x['slug'] == 'global')['sections']), 2)
        f = data['findings'][0]
        self.assertEqual((f['id'], f['page'], f['section'], f['severity'], f['status']),
                         ('F-001', 'global', 'header', 'major', 'open'))
        self.assertRegex(data['updated'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}')  # 0.9.5: the render time
        self.assertEqual((data['now']['step'], data['next']), ('P0 planning', 'the plan OK, then P1 Setup'))
        with open(out, encoding='utf-8') as fh:
            html = fh.read()
        for part in ('Corner Shop build progress', 'QA findings (1): 1 open', 'header (1 open)', 'Go-live gate'):
            self.assertIn(part, html)
        self.assertIn('logo &lt;b&gt;blurry&lt;/b&gt;', html)
        self.assertNotIn('<b>blurry', html)

    def test_now_line_and_every_finding_with_status(self):
        """0.9.5: Now/Next at the top with the start time; open, fixed and decided findings, counted per run."""
        tmp = tempfile.mkdtemp()

        def edit(t):
            t = t.replace('- **Doing:** P0 planning.', '- **Doing:** P5 full QA run 2 (started 14:05).')
            t = t.replace('- **Next:** the plan OK, then P1 Setup.', '- **Next:** P5-01 fix batch 3.')
            t = t.replace('- **Waiting on the developer:** the plan OK (with the decisions below).',
                          '- **Waiting on the developer:** nothing.')
            for row in ('| F-001 | P2 | Home / Hero | gap 24, expected 32 | major | fixed |',
                        '| F-002 | P2 | Global / Footer | icon colour: kept, the brand file says so | minor '
                        '| decided |',
                        '| F-003 | P5 run 2 | Home / Hero | button hover missing | major | open |',
                        '| F-004 | P5 run 2 | assets/css/main.css | unused rule | minor | fixed |'):
                t = finding(t, row)
            return t

        p = board(tmp, edit)
        out = os.path.join(tmp, 'progress.html')
        r = run('scripts/build-map/render.py', p, out)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(tmp, 'progress.json'), encoding='utf-8') as fh:
            data = json.load(fh)
        self.assertEqual(data['now']['step'], 'P5 full QA run 2')
        self.assertRegex(data['now']['started'], r'^\d{4}-\d{2}-\d{2}T14:05$')
        self.assertEqual((data['next'], data['waiting'], data['blocked']), ('P5-01 fix batch 3', 'nothing', 'nothing'))
        self.assertEqual(sorted(f['status'] for f in data['findings']), ['decided', 'fixed', 'fixed', 'open'])
        with open(out, encoding='utf-8') as fh:
            html = fh.read()
        top = html.index('class="card now"')
        self.assertLess(top, html.index('<h2>Phases'))
        for part in ('<b>P5 full QA run 2</b>', 'started 14:05', 'P5-01 fix batch 3', 'id="ago" data-at=',
                     'QA findings (4): 1 open', '1 open</span>', '2 fixed</span>', '1 decided</span>',
                     '<td>P2</td><td>2</td><td>0</td><td>1</td><td>1</td>',
                     '<td>P5 run 2</td><td>2</td><td>1</td><td>1</td><td>0</td>',
                     'Fixed and decided (3)', 'icon colour: kept', 'button hover missing'):
            self.assertIn(part, html)
        self.assertLess(html.index('button hover missing'), html.index('Fixed and decided'))
        self.assertNotIn('Waiting</span>', html)  # "nothing" is not shown

    def test_old_board_still_renders(self):
        """A board made before 0.9.5: no Next line in "## Now"; Next comes from the header line."""
        tmp = tempfile.mkdtemp()
        p = board(tmp, lambda t: t.replace('- **Next:** the plan OK, then P1 Setup.\n', ''))
        r = run('scripts/build-map/render.py', p, os.path.join(tmp, 'progress.html'))
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(tmp, 'progress.json'), encoding='utf-8') as fh:
            data = json.load(fh)
        self.assertEqual((data['now']['step'], data['now']['started'], data['next']), ('P0 planning', '', 'P1 Setup'))


class InstallWp(unittest.TestCase):
    def site(self, env_type, extra="define( 'DB_HOST', 'localhost' );"):
        root = tempfile.mkdtemp()
        with open(os.path.join(root, 'wp-load.php'), 'w') as fh:
            fh.write('<?php\n')
        with open(os.path.join(root, 'wp-config.php'), 'w') as fh:
            fh.write(f"<?php\ndefine( 'WP_ENVIRONMENT_TYPE', '{env_type}' );\n{extra}\n")
        return root

    def test_refuses_a_remote_database(self):
        r = run('scripts/setup/install-wp.py', self.site('local', "define( 'DB_HOST', 'db.example.com' );"),
                '--url', 'http://shop.test')
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn('DB_HOST', r.stdout)

    def test_a_second_define_is_refused(self):
        extra = "/* x */ define( 'WP_ENVIRONMENT_TYPE', 'production' );\ndefine( 'DB_HOST', 'localhost' );"
        r = run('scripts/setup/install-wp.py', self.site('local', extra), '--url', 'http://shop.test')
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn('exactly once', r.stdout)

    def test_a_commented_define_does_not_count(self):
        extra = "// define( 'WP_ENVIRONMENT_TYPE', 'production' );\ndefine( 'DB_HOST', 'localhost:3306' );"
        r = run('scripts/setup/install-wp.py', self.site('local', extra), '--url', 'https://example.com')
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn('not a local address', r.stdout)

    def test_refuses_a_live_url(self):
        r = run('scripts/setup/install-wp.py', self.site('local'), '--url', 'https://example.com')
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertTrue(r.stdout.startswith('FAIL install-wp: refused'), r.stdout)

    def test_refuses_a_non_local_environment(self):
        r = run('scripts/setup/install-wp.py', self.site('production'), '--url', 'http://shop.test')
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("WP_ENVIRONMENT_TYPE 'local'", r.stdout)


if __name__ == '__main__':
    unittest.main()
