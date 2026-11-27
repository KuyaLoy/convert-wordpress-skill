"""0.13.0: long tool output goes to a log in _plan/logs/, the chat gets the result line and the failures; the kit's
own commands are written with compact flags. SKILL.md does not grow."""
import re
import unittest

from helpers import path


def read(*p):
    with open(path(*p), encoding='utf-8') as fh:
        return fh.read()


def section(text, heading):
    m = re.search(rf'(?ms)^## {re.escape(heading)}\n(.*?)(?=^## |\Z)', text)
    return m.group(1) if m else ''


class LeanLog(unittest.TestCase):
    skill = read('SKILL.md')

    def test_rule_18(self):
        rules = section(self.skill, 'Rules (always)')
        self.assertIn('18. **Long output to a log.**', rules)
        rule = rules[rules.index('18. **'):]
        for p in ('about 50 lines', '`_plan/logs/`', 'result line', 'failures', 'log path',
                  '`references/agents.md` > Spend fewer tokens'):
            self.assertIn(p, rule)

    def test_skill_not_larger_than_0120(self):
        self.assertLessEqual(len(self.skill.encode('utf-8')), 16849)

    def test_agents_spend_fewer_tokens(self):
        s = re.sub(r'\s+', ' ', section(read('references', 'agents.md'), 'Spend fewer tokens'))
        for p in ('(rule 18)', '_plan/logs/<step>.log', 'mkdir _plan/logs', 'Out-File -Encoding utf8',
                  'keeps the command, the result line and the log path', '--format=count', '--fields=',
                  '--report-changed-only', 'git status --porcelain', 'vendor/bin/phpcs -q --report=summary',
                  '--no-progress', '--no-audit --no-fund', '--quiet'):
            self.assertIn(p, s)

    def test_compact_flags_where_commands_are_written(self):
        rb = read('assets', 'launch', 'RUNBOOK.template.md')
        self.assertEqual(rb.count('--report-changed-only'), 2)
        self.assertIn('--report-changed-only', read('references', 'launch.md'))
        self.assertIn('vendor/bin/phpcs -q', read('references', 'setup.md'))
        self.assertIn('vendor/bin/phpcs -q --report=summary', read('assets', 'theme', 'AGENTS.md'))
        self.assertIn('`git status --porcelain`', read('references', 'phases-and-qa.md'))
        lh = read('scripts', 'report', 'README.md')
        self.assertIn('--output-path=_plan/logs/lighthouse.json', lh)
        self.assertIn('read only the scores', lh)

    def test_logs_stay_private(self):
        for f in (('assets', 'launch', 'htaccess-live.txt'), ('assets', 'launch', 'htaccess-local.txt')):
            self.assertRegex(read(*f), r'RedirectMatch 403 \^/\(_plan\|')
        self.assertIn("'_plan'", read('scripts', 'launch', 'package.py'))


if __name__ == '__main__':
    unittest.main()
