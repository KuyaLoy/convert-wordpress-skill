"""Render BUILD-MAP.md into the private Build Map page (one self-contained HTML file).

    python3 render.py <BUILD-MAP.md> <out.html> [project folder shown in the footer]

BUILD-MAP.md in the project is the source of truth. This script only reads it and writes a
self-contained page (HTML rendered here, JavaScript only for the tracker filter), so the page can be
regenerated and republished to the same artifact URL whenever the file changes.
"""
import html
import re
import sys

SRC, OUT = sys.argv[1], sys.argv[2]
FOLDER = sys.argv[3] if len(sys.argv) > 3 else ''
md = open(SRC, encoding='utf-8').read()


def E(s):
    return html.escape(str(s), quote=True)


def inline(s):
    s = html.escape(s.strip(), quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![*\w])\*([^*\n]+)\*(?![*\w])', r'<em>\1</em>', s)
    return s


def cells(line):
    return [p.strip() for p in line.strip().strip('|').split('|')]


def tables(lines):
    out, i = [], 0
    while i < len(lines):
        if lines[i].startswith('|') and i + 1 < len(lines) and re.match(r'^\|[-:| ]+\|$', lines[i + 1].strip()):
            hdr, rows, i = cells(lines[i]), [], i + 2
            while i < len(lines) and lines[i].startswith('|'):
                rows.append(cells(lines[i]))
                i += 1
            out.append((hdr, rows))
        else:
            i += 1
    return out


def bullets(lines):
    items = []
    for line in lines:
        if line.startswith('- '):
            items.append(line[2:].strip())
        elif items and line.startswith('  ') and line.strip():
            items[-1] += ' ' + line.strip()
    return items


def status(s):
    return s.strip().strip('`').strip()


# ---- read the markdown ----------------------------------------------------------
preamble, sections, order, cur = [], {}, [], None
for line in md.splitlines():
    m = re.match(r'^## (.+)$', line)
    if m:
        cur = m.group(1).strip()
        sections[cur] = []
        order.append(cur)
    elif cur is None:
        preamble.append(line)
    else:
        sections[cur].append(line)


def section(prefix):
    for name in order:
        if name.startswith(prefix):
            return sections[name]
    raise SystemExit(f'section not found: {prefix}')


pre = ' '.join(l.strip() for l in preamble if l.strip())
m = re.search(r'Updated: \*\*(.+?)\*\* \| Current sprint: \*\*(.+?)\*\* \| Next: \*\*(.+?)\*\*,? ?(.*?)(?= Status key:|$)', pre)
updated, current, nxt, next_note = (m.group(1), m.group(2), m.group(3), m.group(4).strip().lstrip('.,; ').strip()) if m else ('', '', '', '')
pm = re.search(r'\*\*Private[^*]*\*\*\s*(.+?)(?= Updated:)', pre)
hm = re.search(r'^# BUILD-MAP:\s*(.+?)\s+WordPress build\s*$', md, re.M)
SITE = hm.group(1).strip() if hm else 'Site'
OWNER = (re.search(r'Waiting on ([^:*]+):', md) or [None, 'the developer'])[1].strip()
private_note = inline(pm.group(1)) if pm else ''

glance = []
for row in tables(section('At a glance'))[0][1]:
    code, _, name = row[0].partition(' ')
    done, _, total = row[3].partition('/')
    glance.append({'code': code, 'name': name, 'goal': inline(row[1]), 'status': status(row[2]),
                   'done': int(done.strip() or 0), 'total': int(total.strip() or 0)})

now = []
for b in bullets(section('Now')):
    mm = re.match(r'^\*\*(.+?):\*\*\s*(.*)$', b)
    now.append((mm.group(1), mm.group(2)) if mm else ('', b))

decisions = [{'id': r[0], 'title': inline(r[1]), 'status': status(r[2]), 'rec': inline(r[3])}
             for r in tables(section('Decisions'))[0][1]]

sprints = []
for name in order:
    sm = re.match(r'^Sprint (\d+): (.+?) \((DONE|IN PROGRESS|TODO|BLOCKED)\)$', name)
    if not sm:
        continue
    rows = tables(sections[name])[0][1]
    sprints.append({'num': int(sm.group(1)), 'title': sm.group(2), 'status': sm.group(3), 'stories': [
        {'id': r[0], 'story': inline(r[1]), 'status': status(r[2]), 'notes': inline(r[3]) if len(r) > 3 else ''}
        for r in rows]})

pages = []
for r in tables(section('Page tracker'))[0][1]:
    pages.append({'route': inline(r[0]), 'text': re.sub(r'[`*]', '', r[0]), 'sprint': r[1].strip(),
                  'steps': [c.strip().lower() == 'ok' for c in r[2:7]], 'status': status(r[7]),
                  'global': '(global)' in r[0]})

shared = [{'piece': inline(r[0]), 'sprint': inline(r[1]), 'status': status(r[2])}
          for r in tables(section('Shared pieces'))[0][1]]
risks = [{'risk': inline(r[0]), 'where': inline(r[1]), 'plan': inline(r[2])} for r in tables(section('Risks'))[0][1]]
gate_src = next((sections[n] for n in order if n.startswith('Sprint gates')), None)
gate_hdr, gate_rows = (tables(gate_src)[0] if gate_src and tables(gate_src) else ([], []))
log = [inline(b) for b in bullets(section('Log'))]

# ---- building blocks ------------------------------------------------------------
KIND = {'DONE': 'done', 'IN PROGRESS': 'prog', 'TODO': 'todo', 'BLOCKED': 'block', 'DECISION': 'dec'}
LABEL = {'DONE': 'Done', 'IN PROGRESS': 'In progress', 'TODO': 'To do', 'BLOCKED': 'Blocked', 'DECISION': 'Decision'}


def chip(s):
    return f'<span class="chip chip-{KIND.get(s, "todo")}"><i aria-hidden="true"></i>{LABEL.get(s, E(s))}</span>'


def pct(a, b):
    return 0 if not b else round(100 * a / b)


ICON_LOCK = '<svg viewBox="0 0 24 24" aria-hidden="true" class="ico"><path d="M7 10V8a5 5 0 0 1 10 0v2h1a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-9a1 1 0 0 1 1-1h1Zm2 0h6V8a3 3 0 0 0-6 0v2Z" fill="currentColor"/></svg>'
ICON_TICK = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9.5 16.2 5.8 12.5l-1.4 1.4 5.1 5.1L20 8.5l-1.4-1.4z" fill="currentColor"/></svg>'

stories_done = sum(g['done'] for g in glance)
stories_total = sum(g['total'] for g in glance)
current_g = next((g for g in glance if g['status'] == 'IN PROGRESS'),
                 next((g for g in glance if g['status'] != 'DONE'), glance[-1]))
waiting = [d for d in decisions if d['status'] == 'DECISION']
route_rows = [p for p in pages if not p['global']]
parity_done = sum(1 for p in route_rows if p['steps'][3])
blocked = sum(1 for s in sprints for st in s['stories'] if st['status'] == 'BLOCKED')

# band
next_line = f'{E(nxt)} starts {E(next_note)}' if next_note else E(nxt)
band = f'''
<header class="band" id="overview">
  <p class="eyebrow">{E(SITE)} · WordPress build</p>
  <h1>Build Map</h1>
  <dl class="band-meta">
    <div><dt>Updated</dt><dd>{E(updated)}</dd></div>
    <div><dt>Current sprint</dt><dd>{E(current)}</dd></div>
    <div><dt>Next</dt><dd>{E(nxt)}</dd></div>
  </dl>
  <p class="band-note">{next_line}</p>
  <p class="private">{ICON_LOCK}<span><strong>Private.</strong> {private_note}</span></p>
</header>'''

# tiles
tiles = f'''
<section class="tiles" aria-label="Summary">
  <div class="tile">
    <p class="k">Stories done</p>
    <p class="v">{stories_done}<small> / {stories_total}</small></p>
    <div class="bar" role="img" aria-label="{pct(stories_done, stories_total)} percent of stories done"><i style="width:{pct(stories_done, stories_total)}%"></i></div>
    <p class="s">{pct(stories_done, stories_total)}% across {len(glance)} sprints</p>
  </div>
  <div class="tile">
    <p class="k">Current sprint</p>
    <p class="v">{E(current_g['code'])}</p>
    <p class="s"><strong>{E(current_g['name'])}</strong>, {current_g['done']} of {current_g['total']} stories done</p>
  </div>
  <div class="tile">
    <p class="k">Waiting on you</p>
    <p class="v">{len(waiting)}<small> decisions</small></p>
    <p class="s ids">{' '.join(f'<a href="#dec-{E(d["id"])}">{E(d["id"])}</a>' for d in waiting) or 'None'}</p>
  </div>
  <div class="tile">
    <p class="k">Pages at 1:1</p>
    <p class="v">{parity_done}<small> / {len(route_rows)}</small></p>
    <div class="bar" role="img" aria-label="{pct(parity_done, len(route_rows))} percent of pages verified 1:1"><i style="width:{pct(parity_done, len(route_rows))}%"></i></div>
    <p class="s">Visual, DOM and text diff clean</p>
  </div>
</section>
<p class="legend" aria-label="Status key">{''.join(chip(s) for s in KIND)}</p>'''

# pipeline
pipe_items = []
for g in glance:
    k = KIND.get(g['status'], 'todo')
    cls = [f'state-{k}']
    if g is current_g:
        cls.append('current')
    if g['status'] in ('DONE', 'IN PROGRESS'):
        cls.append('flowing')
    pipe_items.append(f'''
    <li class="{' '.join(cls)}">
      <span class="stage-dot" aria-hidden="true">{E(g['code'])}</span>
      <span class="name"><span class="sr">{E(g['code'])} </span>{E(g['name'])}</span>
      <span class="count">{g['done']} / {g['total']} stories</span>
      {chip(g['status'])}
      <span class="goal">{g['goal']}</span>
    </li>''')
pipeline = f'''
<section id="pipeline" aria-labelledby="h-pipeline">
  <div class="sec-head"><h2 id="h-pipeline">Sprint pipeline</h2><p class="meta">One stage per sprint. The lit line is work under way.</p></div>
  <ol class="pipeline" style="--n:{len(glance)}">{''.join(pipe_items)}
  </ol>
</section>'''

# now + decisions
NOW_KIND = {'Doing': 'prog', 'Waiting on ' + OWNER: 'dec', 'Blocked': 'block', 'Done': 'done'}
now_rows = []
for label, text in now:
    k = NOW_KIND.get(label, 'todo')
    if label == 'Blocked' and re.match(r'^\s*nothing', text, re.I):
        k = 'done'
    text = text[:1].upper() + text[1:]
    now_rows.append(f'<div class="now-row"><span class="chip chip-{k}"><i aria-hidden="true"></i>{E(label)}</span><p>{inline(text)}</p></div>')
dec_rows = ''.join(f'''
    <div class="dec" id="dec-{E(d['id'])}">
      <span class="id">{E(d['id'])}</span>
      <span class="t">{d['title']}</span>
      {chip(d['status'])}
      <p class="r">{d['rec']}</p>
    </div>''' for d in decisions)
now_dec = f'''
<div class="split">
  <section id="now" class="panel" aria-labelledby="h-now">
    <div class="sec-head"><h2 id="h-now">Now</h2></div>
    <div class="now">{''.join(now_rows)}</div>
  </section>
  <section id="decisions" class="panel" aria-labelledby="h-dec">
    <div class="sec-head"><h2 id="h-dec">Decisions</h2><p class="meta">{len(waiting)} waiting on {E(OWNER)}</p></div>
    <div class="decs">{dec_rows}
    </div>
  </section>
</div>'''

# sprints
cards = []
by_code = {g['code']: g for g in glance}
for s in sprints:
    code = 'S' + str(s['num'])
    g = by_code.get(code, {'done': 0, 'total': len(s['stories'])})
    rows = ''
    for st in s['stories']:
        notes_html = '<span class="notes">' + st['notes'] + '</span>' if st['notes'] else ''
        rows += f'''
        <li class="story">
          <span class="id">{E(st['id'])}</span>
          <span class="st">{st['story']}</span>
          {chip(st['status'])}
          {notes_html}
        </li>'''
    current_cls = ' is-current' if code == current_g['code'] else ''
    cards.append(f'''
    <article class="sprint{current_cls}" id="sprint-{s['num']}">
      <header>
        <span class="code">S{s['num']}</span>
        <h3>{E(s['title'])}</h3>
        {chip(s['status'])}
      </header>
      <div class="bar thin" role="img" aria-label="{g['done']} of {g['total']} stories done"><i style="width:{pct(g['done'], g['total'])}%"></i></div>
      <ul class="stories">{rows}
      </ul>
    </article>''')
sprints_html = f'''
<section id="sprints" aria-labelledby="h-sprints">
  <div class="sec-head"><h2 id="h-sprints">Sprints and stories</h2><p class="meta">{stories_done} of {stories_total} stories done</p></div>
  <div class="sprints">{''.join(cards)}
  </div>
</section>'''

# sprint gates (one row per sprint: every role's gate, then the developer's sign-off)
gates_html = ''
if gate_rows:
    def gate_cell(v, sign=False):
        v = v.strip()
        if v.upper() == 'PASS' or (sign and v.lower().startswith('go')):
            label = E(v) if sign else 'pass'
            return f'<td class="step"><span class="tick" role="img" aria-label="{label}">{ICON_TICK}</span></td>'
        if v.lower() == 'n/a':
            return '<td class="step"><span class="na">n/a</span></td>'
        if not v:
            return '<td class="step"><span class="dot" role="img" aria-label="not checked"></span></td>'
        return f'<td class="step open">{inline(v)}</td>'
    g_trs = ''.join(
        '<tr><td class="sp">' + E(r[0]) + '</td>'
        + ''.join(gate_cell(v, i == len(gate_hdr) - 2) for i, v in enumerate((r + [''] * len(gate_hdr))[1:len(gate_hdr)]))
        + '</tr>' for r in gate_rows)
    gates_html = f'''
<section id="gates" aria-labelledby="h-gates">
  <div class="sec-head"><h2 id="h-gates">Sprint gates</h2><p class="meta">One sprint at a time: the next starts only when every gate passes and the developer says go</p></div>
  <div class="table-wrap">
    <table>
      <caption class="sr">Each role's gate per sprint, and the sign-off</caption>
      <thead><tr>{''.join(f'<th scope="col"{"" if i == 0 else " class=step"}>{E(h)}</th>' for i, h in enumerate(gate_hdr))}</tr></thead>
      <tbody>{g_trs}</tbody>
    </table>
  </div>
</section>'''

# tracker
STEPS = ['Build', 'ACF', 'Seed', '1:1', 'SEO/a11y']
step_bars = []
for i, name in enumerate(STEPS):
    n = sum(1 for p in pages if p['steps'][i])
    step_bars.append(f'<div class="step-sum"><span class="k">{E(name)}</span><span class="n">{n} / {len(pages)}</span>'
                     f'<div class="bar thin"><i style="width:{pct(n, len(pages))}%"></i></div></div>')
sprint_values = sorted({p['sprint'] for p in pages}, key=lambda v: (len(v), v))
filters = ['<button type="button" class="seg" data-filter="all" aria-pressed="true">All</button>',
           '<button type="button" class="seg" data-filter="global" aria-pressed="false">Global</button>']
filters += [f'<button type="button" class="seg" data-filter="{E(v)}" aria-pressed="false">{E(v)}</button>' for v in sprint_values]
TICK_CELL = '<td class="step"><span class="tick" role="img" aria-label="done">' + ICON_TICK + '</span></td>'
DOT_CELL = '<td class="step"><span class="dot" role="img" aria-label="not yet"></span></td>'
trs = []
for p in pages:
    cellhtml = ''.join(TICK_CELL if ok else DOT_CELL for ok in p['steps'])
    trs.append(f'''
        <tr data-sprint="{E(p['sprint'])}" data-global="{'1' if p['global'] else '0'}" data-text="{E(p['text'].lower())}"{' class="global"' if p['global'] else ''}>
          <td class="route">{p['route']}</td><td class="sp">{E(p['sprint'])}</td>{cellhtml}<td>{chip(p['status'])}</td>
        </tr>''')
tracker = f'''
<section id="pages" aria-labelledby="h-pages">
  <div class="sec-head"><h2 id="h-pages">Page tracker</h2><p class="meta"><span id="page-count">{len(pages)} rows</span></p></div>
  <div class="step-sums">{''.join(step_bars)}</div>
  <div class="toolbar">
    <div class="segs" role="group" aria-label="Filter by sprint">{''.join(filters)}</div>
    <label class="search" for="page-search"><span class="sr">Filter routes</span>
      <input id="page-search" type="search" placeholder="Filter routes, e.g. about" autocomplete="off">
    </label>
  </div>
  <div class="table-wrap">
    <table>
      <caption class="sr">Every route and where it is in the section workflow</caption>
      <thead><tr><th scope="col">Route</th><th scope="col">Sprint</th>{''.join(f'<th scope="col" class="step">{E(n)}</th>' for n in STEPS)}<th scope="col">Status</th></tr></thead>
      <tbody>{''.join(trs)}
      </tbody>
    </table>
    <p class="empty" id="page-empty" hidden>No routes match that filter.</p>
  </div>
</section>'''

# shared + risks
shared_rows = ''.join(f'<li class="row3"><span class="t">{s["piece"]}</span><span class="w">{s["sprint"]}</span>{chip(s["status"])}</li>' for s in shared)
risk_rows = ''.join(f'<li class="risk"><p class="t">{r["risk"]}</p><p class="w">{r["where"]}</p><p class="plan">{r["plan"]}</p></li>' for r in risks)
shared_risks = f'''
<div class="split">
  <section id="shared" class="panel" aria-labelledby="h-shared">
    <div class="sec-head"><h2 id="h-shared">Shared pieces</h2></div>
    <ul class="list">{shared_rows}</ul>
  </section>
  <section id="risks" class="panel" aria-labelledby="h-risks">
    <div class="sec-head"><h2 id="h-risks">Risks to watch</h2></div>
    <ul class="list">{risk_rows}</ul>
  </section>
</div>'''

# log + footer
log_html = f'''
<section id="log" class="panel" aria-labelledby="h-log">
  <div class="sec-head"><h2 id="h-log">Log</h2></div>
  <ul class="log">{''.join(f'<li>{l}</li>' for l in log)}</ul>
</section>
<footer class="foot">
  <p>Made from <code>BUILD-MAP.md</code>{(' in <code>' + E(FOLDER) + '</code>') if FOLDER else ''}. That file is the source of truth; this page is regenerated from it when it changes.</p>
</footer>'''

nav = '''
<nav class="nav" aria-label="Sections">
  <ul>
    <li><a href="#overview">Overview</a></li>
    <li><a href="#pipeline">Pipeline</a></li>
    <li><a href="#now">Now</a></li>
    <li><a href="#decisions">Decisions</a></li>
    <li><a href="#gates">Gates</a></li>
    <li><a href="#sprints">Sprints</a></li>
    <li><a href="#pages">Pages</a></li>
    <li><a href="#risks">Risks</a></li>
    <li><a href="#log">Log</a></li>
  </ul>
</nav>'''

body = band + nav + tiles + pipeline + now_dec + gates_html + sprints_html + tracker + shared_risks + log_html
template = open(__file__.replace('render.py', 'template.html'), encoding='utf-8').read()
open(OUT, 'w', encoding='utf-8').write(template.replace('<!--BODY-->', body).replace('{{SITE}}', E(SITE)))
print(f'ok: {len(glance)} sprints, {sum(len(s["stories"]) for s in sprints)} story rows, {len(decisions)} decisions, '
      f'{len(pages)} tracker rows, {len(risks)} risks, {len(log)} log lines, updated {updated}')
