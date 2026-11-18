#!/usr/bin/env python3
"""Phase gate: the build moves one phase at a time; QA after each phase only logs findings; one fix loop at the end.

    python3 gate.py BUILD-MAP.md           check the board (exit 0: the current phase may close, 1: not yet,
                                           2: the board breaks a rule and must be fixed first)
    python3 gate.py BUILD-MAP.md --close   close the current phase and open the next one (only when the check passes)

Rules (references/phases-and-qa.md):
  - one phase at a time: the first phase that is not DONE is the current one (IN PROGRESS or BLOCKED); every later
    phase is TODO with no step IN PROGRESS or DONE (no work ahead); every earlier phase has all its steps DONE;
  - the "Phases" table matches each phase heading; section, finding and gate values use the board's words;
  - to close the current phase: every step DONE, and
      P0 Plan: the developer's "Plan OK" gate (ok <date>);
      P1 to P4: the phase's QA run recorded ("<date>: <n> found"), no open blocker;
      P2 Pages: also every section row checked or fixed;
      P5 Fix and QA loop: no finding open (each fixed and checked again, or decided), the last full QA run
         "0 found", every section checked or fixed,
         and the developer's "Go-live" gate (ok <date>);
  - the agent writes "ok <date>" in a Developer gates cell only after the developer said it in the chat.
"""
import datetime
import re
import sys

if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(2)
SRC = sys.argv[1]
CLOSE = '--close' in sys.argv[2:]
try:
    md = open(SRC, encoding='utf-8').read()
except OSError as e:
    print(f'FAIL gate: cannot read {SRC}: {e.strerror}')
    sys.exit(2)

SECTION_STATES = ('todo', 'building', 'built', 'checked', 'fixed')
FINDING_STATES = ('open', 'fixed', 'decided')
SEVERITIES = ('blocker', 'major', 'minor')


def cells(line):
    return [p.strip() for p in line.strip().strip('|').split('|')]


def first_table(lines):
    for i, line in enumerate(lines):
        if line.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[-:| ]+\|$', lines[i + 1].strip()):
            hdr, rows = cells(line), []
            for row in lines[i + 2:]:
                if not row.startswith('|'):
                    break
                rows.append(cells(row))
            return hdr, rows
    return [], []


def word(s):
    return s.strip().strip('`').strip()


sections, order, cur = {}, [], None
for line in md.splitlines():
    m = re.match(r'^## (.+)$', line)
    if m:
        cur = m.group(1).strip()
        sections[cur] = []
        order.append(cur)
    elif cur:
        sections[cur].append(line)


def section(name):
    return next((sections[n] for n in order if n == name or n.startswith(name + ' ')), None)


broken, open_items = [], []

phases = []
for name in order:
    m = re.match(r'^Phase (\d+): (.+?) \((DONE|IN PROGRESS|TODO|BLOCKED)\)$', name)
    if m:
        _, rows = first_table(sections[name])
        phases.append({'num': int(m.group(1)), 'code': 'P' + m.group(1), 'name': m.group(2), 'status': m.group(3),
                       'heading': name, 'steps': [(r[0], r[1], word(r[2]).upper()) for r in rows if len(r) >= 3]})
if not phases:
    print('FAIL gate: no "## Phase N: Name (STATUS)" sections: is this a 0.8 BUILD-MAP.md? '
          '(A board from 0.7 or older has sprints: keep using the kit version it was made with.)')
    sys.exit(2)

table = {}
t_lines = section('Phases')
if t_lines is None:
    broken.append('the "Phases" section is missing')
else:
    for r in first_table(t_lines)[1]:
        if len(r) >= 3:
            table[r[0].split(' ')[0]] = {'status': word(r[2]).upper(), 'qa': r[3].strip() if len(r) > 3 else ''}

gates = {}
g_lines = section('Developer gates')
if g_lines is None:
    broken.append('the "Developer gates" section is missing (copy it from the BUILD-MAP template)')
else:
    for r in first_table(g_lines)[1]:
        if len(r) >= 2:
            gates[r[0].strip().lower()] = r[1].strip()


def gate_ok(name):
    return gates.get(name, '').lower().startswith('ok')


pages = []
p_lines = section('Pages')
if p_lines is None:
    broken.append('the "Pages" section is missing (copy it from the BUILD-MAP template)')
else:
    for r in first_table(p_lines)[1]:
        if len(r) >= 4:
            st = word(r[3]).lower()
            pages.append({'where': r[0] + ' / ' + r[2], 'status': st})
            if st not in SECTION_STATES:
                broken.append(f"Pages: '{r[0]} / {r[2]}' has status '{r[3]}' (use: {', '.join(SECTION_STATES)})")

findings = []
f_lines = section('QA findings')
if f_lines is None:
    broken.append('the "QA findings" section is missing')
else:
    for r in first_table(f_lines)[1]:
        if len(r) >= 6 and any(r):
            f = {'id': r[0], 'phase': r[1], 'where': r[2], 'text': r[3], 'sev': word(r[4]).lower(),
                 'status': word(r[5]).lower()}
            findings.append(f)
            if f['sev'] not in SEVERITIES:
                broken.append(f"finding {f['id']}: severity '{r[4]}' (use: blocker, major or minor)")
            if f['status'] not in FINDING_STATES:
                broken.append(f"finding {f['id']}: status '{r[5]}' (use: open, fixed or decided)")

for p in phases:
    t = table.get(p['code'])
    if t is None:
        broken.append(f"{p['code']}: no row in the Phases table")
    elif t['status'] != p['status']:
        broken.append(f"{p['code']}: the Phases table says {t['status']}, the phase heading says {p['status']}")

current = next((p for p in phases if p['status'] != 'DONE'), None)
for p in phases:
    if current and p['num'] < current['num']:
        for sid, step, st in p['steps']:
            if st != 'DONE':
                broken.append(f"{p['code']} is DONE but {sid} is {st}")
    if current and p['num'] > current['num']:
        if p['status'] != 'TODO':
            broken.append(f"{p['code']} is {p['status']} while {current['code']} is not done: one phase at a time")
        for sid, step, st in p['steps']:
            if st in ('IN PROGRESS', 'DONE'):
                broken.append(f"{sid} ({p['code']}) is {st} while {current['code']} is open: no work ahead")
if current and current['status'] not in ('IN PROGRESS', 'BLOCKED'):
    broken.append(f"{current['code']} is the current phase: set it IN PROGRESS")

if broken:
    print('BOARD BREAKS THE PHASE RULES (fix these first):')
    for b in broken:
        print('  - ' + b)
    sys.exit(2)

open_f = [f for f in findings if f['status'] == 'open']
blockers = [f for f in open_f if f['sev'] == 'blocker']
if current is None:
    print(f'All phases are DONE. Findings: {len(findings)} logged, {len(open_f)} open.')
    sys.exit(0)

for sid, step, st in current['steps']:
    if st != 'DONE':
        open_items.append(f'step {sid} is {st}: {step}')
for f in blockers:
    open_items.append(f"blocker {f['id']} ({f['where']}): fix it now; mark it fixed once checked again")
num, qa = current['num'], table[current['code']]['qa']
if num == 0 and not gate_ok('plan ok'):
    open_items.append('the developer\'s "Plan OK" (write "ok <date>" only when they say it in the chat)')
if 1 <= num <= 4 and not re.search(r'\d+ found', qa):
    open_items.append(f'the phase QA run: record it in the Phases table as "<date>: <n> found"')
if num == 2 or num == 5:
    if not pages:
        open_items.append('no sections on the Pages table: list every page and its sections first')
    for p in pages:
        if p['status'] not in ('checked', 'fixed'):
            open_items.append(f"section {p['where']} is {p['status']}")
if num == 5:
    for f in open_f:
        open_items.append(f"finding {f['id']} is open: {f['text'][:70]}")
    if not re.search(r'(^|\D)0 found', qa):
        open_items.append('the last full QA run must find 0: record it as "<date>: 0 found"')
    if not gate_ok('go-live'):
        open_items.append('the developer\'s "Go-live" (write "ok <date>" only when they say it in the chat)')

summary = f"findings {len(findings)} logged, {len(open_f)} open, {len(blockers)} blocker"
if open_items:
    print(f"WARN gate: {current['code']} {current['name']} cannot close yet ({len(open_items)} open; {summary}):")
    for o in open_items[:15]:
        print('  - ' + o)
    if len(open_items) > 15:
        print(f'  - and {len(open_items) - 15} more (the board lists them)')
    print(f"Keep working on {current['code']} only. QA logs findings; only a blocker is fixed before P5.")
    sys.exit(1)

nxt = next((p for p in phases if p['num'] > current['num']), None)
if not CLOSE:
    print(f"OK gate: {current['code']} {current['name']} may close ({summary}). Close it with --close"
          + (f", which opens {nxt['code']} {nxt['name']}." if nxt else '.'))
    sys.exit(0)

today = datetime.date.today()
date = f'{today.day} {today:%b %Y}'
text = md.replace(f"## {current['heading']}", f"## Phase {current['num']}: {current['name']} (DONE)", 1)
if nxt:
    text = text.replace(f"## {nxt['heading']}", f"## Phase {nxt['num']}: {nxt['name']} (IN PROGRESS)", 1)


def set_row(t, code, status):
    return re.sub(rf'^(\| {re.escape(code)} [^|]*\|[^|]*\| )`?([A-Z ]+?)`?( \|)',
                  lambda m: m.group(1) + status + m.group(3), t, count=1, flags=re.M)


text = set_row(text, current['code'], 'DONE')
if nxt:
    text = set_row(text, nxt['code'], 'IN PROGRESS')
after = next((p for p in phases if nxt and p['num'] > nxt['num']), None)
cur_label = f"{nxt['code']} {nxt['name']}" if nxt else 'Done'
next_label = f"{after['code']} {after['name']}" if after else ('Done' if nxt else '-')
text = re.sub(r'Updated: \*\*.+?\*\* \| Phase: \*\*.+?\*\* \| Next: \*\*.+?\*\*',
              f'Updated: **{date}** | Phase: **{cur_label}** | Next: **{next_label}**', text, count=1)
log = (f"- {date}: {current['code']} {current['name']} closed ({summary})."
       f"{' ' + nxt['code'] + ' ' + nxt['name'] + ' started.' if nxt else ''}")
text = re.sub(r'(^## Log\s*\n\n?)', lambda m: m.group(1) + log + '\n', text, count=1, flags=re.M)
open(SRC, 'w', encoding='utf-8', newline='\n').write(text)
print(f"Closed {current['code']} {current['name']}." + (f" {nxt['code']} {nxt['name']} is IN PROGRESS." if nxt else ''))
print('Now: re-render the board page and update handoff.md and ai-handoff-summary.md.')
