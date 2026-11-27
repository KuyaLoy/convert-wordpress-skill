"""0.10.0: a slimmer SKILL.md. The phase steps moved unchanged to references/phase-steps.md; SKILL.md keeps the
rules, the phase list and what each phase must prove. Nothing is lost: every heading and every line of the 0.9.16
SKILL.md is still in SKILL.md or a reference."""
import os
import re
import shutil
import subprocess
import unittest

from helpers import KIT, path

# Lines later releases changed on purpose: the old wording -> (its new wording, or None when rewritten, and why).
CHANGED = {
    '**Open first:** an existing project: `ai-handoff-summary.md`, then gate.py (Start: intake, step 1). A new one: Start:':
        (None, '0.10.0: Start: intake is now a short list with a pointer'),
    'leads portal; a skill update during a task applies at the next site or phase boundary, never inside a QA run.':
        ('leads portal (only when the profile names one); a skill update during a task applies at the next site or '
         'phase boundary, never inside a QA run.', '0.10.2: the leads portal is optional'),
    'built; every form and where its leads go (CF7 for each, the leads portal or "none: <reason>"), missing content as':
        ('built; every form and where its leads go (CF7 for each; the leads portal only when the profile names one), '
         'missing content as', '0.10.2: the leads portal is optional'),
    "Every lead also goes to the profile's leads portal (`leads_portal`), server to server, whether the email went out":
        ('Only when the profile names a leads portal (`leads_portal.constant_prefix`; optional, none by default) does '
         'every lead', '0.10.2: the leads portal is optional'),
    'or failed: mandatory on live for a site with a lead form (no portal in the profile is a go-live blocker; a site':
        (None, '0.10.2: no portal is no longer a blocker (the paragraph above, rewritten)'),
    'without forms says so in site.json). Its address and password always live in Theme Settings > Leads portal':
        (None, '0.10.2: the paragraph above, rewritten'),
    'Every lead form also says where the lead came from (form attribution, built in: UTM tags, ad click ids, landing':
        ("Every lead form also says where the lead came from (form attribution, built in: the company standard's "
         'eleven', '0.12.0: the company attribution standard'),
    'page, referrer, first visit), in the lead email, CFDB7, the portal and `generate_lead`.':
        ("fields, Lead Source to First Touch Referrer), in the lead email, CFDB7's columns, the portal, the CRM "
         'mapping and', '0.12.0: the company attribution standard'),
    'Every script, with what it does: `references/scripts.md`. Run them with the `python3` (or `node`)':
        ('Every script and how to run it: `references/scripts.md`.', '0.13.0: how to run them is in scripts.md'),
    'command doctor.py printed, from any shell.':
        (None, '0.13.0: the line above; scripts.md says which python3 command and that any shell works'),
}


def read(p):
    with open(p, encoding='utf-8') as fh:
        return fh.read()


def section(text, heading):
    m = re.search(rf'(?ms)^## {re.escape(heading)}\n(.*?)(?=^## |\Z)', text)
    return m.group(1) if m else None


def old_skill():
    if not shutil.which('git'):
        return None
    r = subprocess.run(['git', 'show', 'v0.9.16:SKILL.md'], cwd=KIT, capture_output=True, text=True, encoding='utf-8')
    return r.stdout if r.returncode == 0 else None


class Slim(unittest.TestCase):
    skill = read(path('SKILL.md'))
    steps = read(path('references', 'phase-steps.md'))

    def test_size(self):
        self.assertLessEqual(len(self.skill), 20000, 'SKILL.md over about 5,000 tokens (4 characters a token)')
        self.assertLess(len(self.skill.splitlines()), 500)

    @unittest.skipIf(old_skill() is None, 'no git or no v0.9.16 tag here')
    def test_nothing_lost(self):
        have = {line.strip() for f in [path('SKILL.md')] + [path('references', x) for x in os.listdir(path('references'))
                                                             if x.endswith('.md')]
                for line in read(f).splitlines()}
        old = old_skill()
        for line in old.splitlines():
            t = line.strip()
            if t in CHANGED:
                new = CHANGED[t][0]
                self.assertTrue(new is None or new in have, f'changed line missing: {new}')
            elif t:
                self.assertIn(t, have, f'lost from 0.9.16 SKILL.md: {t}')
        for h in re.findall(r'(?m)^##? .+$', old):
            self.assertTrue(h in self.skill or h in self.steps, f'heading lost: {h}')

    def test_rules_and_phase_list_stay(self):
        rules = section(self.skill, 'Rules (always)')
        nums = re.findall(r'(?m)^(\d+)\. \*\*', rules)
        self.assertEqual(nums, [str(n) for n in range(1, len(nums) + 1)])
        self.assertGreaterEqual(len(nums), 17)  # 0.10.1 added 17, leads stored by CFDB7 only
        phases = section(self.skill, 'The phases')
        for p in ('P0 Plan', 'P1 Setup', 'P2 Pages', 'P3 Forms and email', 'P4 SEO, security, speed',
                  'P5 Fix and QA loop', 'P6 Launch and live QA'):
            self.assertIn(f'| {p} |', phases)
        old = old_skill()
        if old:
            # The 0.9.16 hard rules word for word; later releases only add rules after them.
            self.assertTrue(rules.startswith(section(old, 'Rules (always)').rstrip('\n') + '\n'))
            was = section(old, 'The phases')
            for a, (b, _) in CHANGED.items():
                if b:
                    was = was.replace(a, b)
            self.assertEqual(phases, was)  # word for word, apart from the listed changes

    def test_every_phase_proves_and_points(self):
        prove = section(self.skill, 'What each phase must prove')
        self.assertIn('`references/phase-steps.md` > the phase\'s heading', prove)
        names = re.findall(r'(?m)^- \*\*(.+?):\*\*', prove)
        self.assertEqual(names, ['P0 Plan (no code)', 'P1 Setup', 'P2 Pages', 'P3 Forms and email',
                                 'P4 SEO, security, speed', 'P5 Fix and QA loop', 'P6 Launch',
                                 'P6 Live QA and the report'])
        heads = re.findall(r'(?m)^## (.+)$', self.steps)
        for n in names:
            self.assertTrue(any(h.startswith(n) for h in heads), f'no section for {n} in phase-steps.md')
        self.assertIn('`references/phase-steps.md` > Start: intake', section(self.skill, 'Start: intake'))
        self.assertIn('Start: intake', heads)

    def test_phase_steps_contents_and_read_table(self):
        heads = re.findall(r'(?m)^## (.+)$', self.steps)
        listed = re.findall(r'(?m)^- (.+)$', section(self.steps, 'Contents'))
        self.assertEqual(listed, [h for h in heads if h != 'Contents'])
        self.assertIn('| `references/phase-steps.md` |', self.skill)


if __name__ == '__main__':
    unittest.main()
