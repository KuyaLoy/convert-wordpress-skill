#!/usr/bin/env python3
"""Sprint gate: the build moves one sprint at a time, and a sprint closes only when all of it is done.

    python3 gate.py BUILD-MAP.md           check the board (exit 0: the current sprint may close, 1: not yet,
                                           2: the board breaks a rule and must be fixed first)
    python3 gate.py BUILD-MAP.md --close   close the current sprint and open the next one (only when the check passes)

Rules (the skill's sprint SDLC):
  - one sprint at a time: the first sprint that is not DONE is the current one (IN PROGRESS or BLOCKED), every later
    sprint is TODO with no story IN PROGRESS or DONE (no work ahead);
  - every earlier sprint is DONE: all its stories DONE, its gate row PASS (or n/a) and signed off ("go <date>");
  - the "At a glance" row of each sprint matches its story table (status, and done / total);
  - to close the current sprint: every story DONE, every page tracker row of that sprint "ok" in all five steps,
    every gate cell PASS or n/a, and the developer's sign-off. The agent writes "go <date>" in the Sign-off cell
    only after the developer said go in the chat, never on its own.
"""
import datetime
import re
import sys

if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(2)
SRC = sys.argv[1]
CLOSE = '--close' in sys.argv[2:]
md = open(SRC, encoding='utf-8').read()


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
    return s.strip().strip('`').strip().upper()


sections, order, cur = {}, [], None
for line in md.splitlines():
    m = re.match(r'^## (.+)$', line)
    if m:
        cur = m.group(1).strip()
        sections[cur] = []
        order.append(cur)
    elif cur:
        sections[cur].append(line)


def section(prefix):
    return next((sections[n] for n in order if n.startswith(prefix)), None)


broken, open_items = [], []

sprints = []
for name in order:
    m = re.match(r'^Sprint (\d+): (.+?) \((DONE|IN PROGRESS|TODO|BLOCKED)\)$', name)
    if m:
        _, rows = first_table(sections[name])
        sprints.append({'num': int(m.group(1)), 'code': 'S' + m.group(1), 'name': m.group(2), 'status': m.group(3),
                        'heading': name, 'stories': [(r[0], r[1], word(r[2])) for r in rows if len(r) >= 3]})
if not sprints:
    sys.exit('No "## Sprint N: Name (STATUS)" sections found: is this a BUILD-MAP.md?')

glance = {}
g_lines = section('At a glance')
if g_lines is None:
    broken.append('the "At a glance" section is missing')
else:
    for r in first_table(g_lines)[1]:
        code = r[0].split(' ')[0]
        done, _, total = r[3].partition('/') if len(r) > 3 else ('', '', '')
        glance[code] = {'status': word(r[2]) if len(r) > 2 else '', 'done': done.strip(), 'total': total.strip()}

gates = {}
gate_lines = section('Sprint gates')
gate_hdr = []
if gate_lines is None:
    broken.append('the "Sprint gates" section is missing (copy it from the BUILD-MAP template)')
else:
    gate_hdr, rows = first_table(gate_lines)
    for r in rows:
        gates[r[0].split(' ')[0]] = dict(zip(gate_hdr[1:], r[1:]))

tracker = []
t_lines = section('Page tracker')
if t_lines is not None:
    for r in first_table(t_lines)[1]:
        if len(r) >= 8:
            tracker.append({'route': re.sub(r'[`*]', '', r[0]), 'sprint': r[1].split(' ')[0],
                            'steps': [c.strip().lower() == 'ok' for c in r[2:7]]})

# The board must be true before anything else.
for s in sprints:
    g = glance.get(s['code'])
    done = sum(1 for _, _, st in s['stories'] if st == 'DONE')
    if g is None:
        broken.append(f"{s['code']}: no row in At a glance")
        continue
    if g['status'] != s['status']:
        broken.append(f"{s['code']}: At a glance says {g['status']}, the sprint heading says {s['status']}")
    if g['done'] != str(done) or g['total'] != str(len(s['stories'])):
        broken.append(f"{s['code']}: At a glance says {g['done']} / {g['total']}, the story table has "
                      f"{done} / {len(s['stories'])}")

current = next((s for s in sprints if s['status'] != 'DONE'), None)
for s in sprints:
    if current and s['num'] < current['num']:
        for sid, story, st in s['stories']:
            if st != 'DONE':
                broken.append(f"{s['code']} is DONE but {sid} is {st}: finish it or move it, with the developer's OK")
        row = gates.get(s['code'], {})
        for col in gate_hdr[1:]:
            v = row.get(col, '').strip()
            if col.lower().startswith('sign'):
                if not v.lower().startswith('go'):
                    broken.append(f"{s['code']} is DONE without the developer's sign-off")
            elif v.upper() not in ('PASS', 'N/A'):
                broken.append(f"{s['code']} is DONE but its {col} gate is '{v or 'empty'}'")
    if current and s['num'] > current['num']:
        if s['status'] != 'TODO':
            broken.append(f"{s['code']} is {s['status']} while {current['code']} is not done: one sprint at a time")
        for sid, story, st in s['stories']:
            if st in ('IN PROGRESS', 'DONE'):
                broken.append(f"{sid} ({s['code']}) is {st} while {current['code']} is open: no work ahead")
if current and current['status'] not in ('IN PROGRESS', 'BLOCKED'):
    broken.append(f"{current['code']} is the current sprint: set it IN PROGRESS (sprint planning done)")

if broken:
    print('BOARD BREAKS THE SPRINT RULES (fix these first):')
    for b in broken:
        print('  - ' + b)
    sys.exit(2)
if current is None:
    print('All sprints are DONE. Next: launch, live QA and the report (no sprint gate left).')
    sys.exit(0)

for sid, story, st in current['stories']:
    if st != 'DONE':
        open_items.append(f'story {sid} is {st}: {story}')
STEPS = ['Build', 'ACF', 'Seed', '1:1', 'SEO/a11y']
for t in tracker:
    if t['sprint'] == current['code'] and not all(t['steps']):
        missing = [n for n, ok in zip(STEPS, t['steps']) if not ok]
        open_items.append(f"page {t['route']}: not ok yet in {', '.join(missing)}")
row = gates.get(current['code'])
if row is None:
    open_items.append(f"no gate row for {current['code']} in Sprint gates")
else:
    for col in gate_hdr[1:]:
        v = row.get(col, '').strip()
        if col.lower().startswith('sign'):
            if not v.lower().startswith('go'):
                open_items.append("the developer's sign-off (ask for it after the demo; write \"go <date>\" only "
                                  'when they say go)')
        elif v.upper() not in ('PASS', 'N/A'):
            open_items.append(f'{col} gate: {v or "not checked"}')

if open_items:
    print(f"{current['code']} {current['name']} cannot close yet ({len(open_items)} open):")
    for o in open_items:
        print('  - ' + o)
    print(f"Keep working on {current['code']} only. Nothing from a later sprint starts before this gate passes.")
    sys.exit(1)

nxt = next((s for s in sprints if s['num'] > current['num']), None)
if not CLOSE:
    print(f"{current['code']} {current['name']}: gate passed and signed off. Close it with --close"
          + (f", which opens {nxt['code']} {nxt['name']}." if nxt else '.'))
    sys.exit(0)

today = datetime.date.today()
date = f'{today.day} {today:%b %Y}'
text = md.replace(f"## {current['heading']}", f"## Sprint {current['num']}: {current['name']} (DONE)", 1)
if nxt:
    text = text.replace(f"## {nxt['heading']}", f"## Sprint {nxt['num']}: {nxt['name']} (IN PROGRESS)", 1)


def set_glance(t, code, status):
    return re.sub(rf'^(\| {re.escape(code)} [^|]*\|[^|]*\| )([A-Z ]+?)( \|)', lambda m: m.group(1) + status + m.group(3),
                  t, count=1, flags=re.M)


text = set_glance(text, current['code'], 'DONE')
if nxt:
    text = set_glance(text, nxt['code'], 'IN PROGRESS')
after = next((s for s in sprints if nxt and s['num'] > nxt['num']), None)
cur_label = f"{nxt['code']} {nxt['name']}" if nxt else 'Launch'
next_label = f"{after['code']} {after['name']}" if after else ('Launch' if nxt else 'Live QA and report')
text = re.sub(r'Updated: \*\*.+?\*\* \| Current sprint: \*\*.+?\*\* \| Next: \*\*.+?\*\*',
              f'Updated: **{date}** | Current sprint: **{cur_label}** | Next: **{next_label}**', text, count=1)
sign = gates[current['code']].get(gate_hdr[-1], '').strip()
log = (f"- {date}: {current['code']} {current['name']} closed: every story done, every gate passed, signed off "
       f"({sign}).{' ' + nxt['code'] + ' ' + nxt['name'] + ' started.' if nxt else ''}")
text = re.sub(r'(^## Log\s*\n\n?)', lambda m: m.group(1) + log + '\n', text, count=1, flags=re.M)
open(SRC, 'w', encoding='utf-8', newline='\n').write(text)
print(f"Closed {current['code']} {current['name']}." + (f" {nxt['code']} {nxt['name']} is IN PROGRESS." if nxt else ''))
print('Now: sprint planning for the new sprint (stories, acceptance, tasks), re-render the board page, and update '
      'handoff.md and ai-handoff-summary.md.')
