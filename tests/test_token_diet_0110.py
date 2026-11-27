"""0.11.0: the token diet. What each phase must prove is objective items with evidence (Pass|Fail), no line tells the
agent to check its own work, the read-only QA check is a reader that never saw the build, and script checks are
named instead of restated."""
import os
import re
import unittest

from helpers import path

SELF_CHECK = ('re-read the changed files', 'as if someone else wrote', 'checked by you afterwards',
              'double-check', 'check your own work', 'review your own')
SUBJECTIVE = ('raised', 'built in', 'honestly', 'looks right', 'as needed')


def read(*p):
    with open(path(*p), encoding='utf-8') as fh:
        return fh.read()


def section(text, heading):
    m = re.search(rf'(?ms)^## {re.escape(heading)}\n(.*?)(?=^## |\Z)', text)
    return m.group(1) if m else ''


DOCS = ['SKILL.md'] + [os.path.join('references', f) for f in os.listdir(path('references')) if f.endswith('.md')]


class TokenDiet(unittest.TestCase):
    skill = read('SKILL.md')

    def test_skill_smaller_than_0102(self):
        self.assertLess(len(self.skill.encode('utf-8')), 16969)

    def test_no_self_check_lines(self):
        for d in DOCS:
            text = read(d).lower()
            for phrase in SELF_CHECK:
                self.assertNotIn(phrase, text, f'{d}: "{phrase}"')

    def test_must_prove_is_pass_fail_with_evidence(self):
        prove = section(self.skill, 'What each phase must prove')
        self.assertIn('`Pass|Fail | item | evidence`', prove)
        self.assertIn('none is Fail', prove)
        bullets = re.findall(r'(?ms)^- \*\*.+?(?=^- \*\*|\Z)', prove)
        self.assertEqual(len(bullets), 8)
        evidence = [('gate.py', 'PLAN.md', '`ok <date>`'),
                    ('setup.py', 'PHPCS 0', 'swaptest.py', 'sync.php', 'region-check.mjs, domdiff.py'),
                    ('check-section.py', 'design-check.mjs', 'curl -I', 'text-check.py placeholders'),
                    ('(curl)', '`_setup/mail/`', 'Theme Settings group'),
                    ('seodiff.py 0', 'curl -I', '(check-section.py)', 'Lighthouse'),
                    ('(gate.py)', 'text-check.py oneoff', 'self-check.py 0', '`ok <date>`'),
                    ('"done"', 'package.py output', 'curl -I', 'wp-config', 'plugin-check.py --env live'),
                    ('`live-qa.py`', 'track.mjs', 'PageSpeed Insights', '`text-check.py fill` OK')]
        for b, ev in zip(bullets, evidence):
            for e in ev:
                self.assertIn(e, b, f'evidence "{e}" missing in {b[:40]}')
            for w in SUBJECTIVE:
                self.assertNotIn(w, b, f'subjective "{w}" in {b[:40]}')

    def test_fresh_reader(self):
        qa = section(read('references', 'phases-and-qa.md'), 'The read-only QA check')
        self.assertIn('never saw the build', qa)
        self.assertIn('in the background', qa)
        self.assertIn('The chat that built it never stands in', qa)
        self.assertIn('never saw the build', section(read('references', 'agents.md'), 'Subagents'))

    def test_script_checks_named_not_restated(self):
        sc = section(read('references', 'phases-and-qa.md'), 'The self-check before every QA run')
        self.assertIn("the script's own header", sc)
        self.assertLess(len(sc), 900)
        header = read('scripts', 'report', 'self-check.py').split('"""')[1]
        for cls in ('instructions', 'repeater', 'abspath', 'phpcs-ignore', 'unused', 'missing-file', 'size',
                    'leftover', 'launch', 'public', 'lead-storage', 'tracking'):
            self.assertIn(cls, header)  # the list the docs point to
        build = read('references', 'build.md')
        self.assertNotIn('grep -rnE $X', build)
        self.assertIn('text-check.py oneoff .', section(build, 'Code quality: tokens, only what is used, sizes, gates'))


if __name__ == '__main__':
    unittest.main()
