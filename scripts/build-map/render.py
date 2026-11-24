"""Render BUILD-MAP.md into the private progress page, the same page figma-to-wordpress shows.

    python3 render.py <BUILD-MAP.md> <out.html> [--json <progress.json>]
    python3 render.py <BUILD-MAP.md> <out.html> --pushed     after the database writes went through
    python3 render.py <BUILD-MAP.md> <out.html> --refresh 30 --open    the local page (tools without Artifacts)

--refresh N adds a reload every N seconds to out.html, so a tab showing the local file picks up each new render;
--open opens out.html in the default browser (once is enough: the reload keeps the tab current).

It also writes the live page (progress-live.html) and the database writes since the last push (progress-rows.json):
see live.py.

BUILD-MAP.md is the source of truth (gate.py checks it). This script reads it, writes progress.json in the shared
progress shape (the keys figma-to-wordpress's references/progress.md defines: site, target, figma, url, updated,
phases, pages with sections, findings, log; 0.9.5 adds now, next, waiting, blocked; updated is the render time;
default: next to out.html) and renders out.html from that JSON: the Now/Next line and the update time at the top,
phases, pages x sections x status, every QA finding with its status (counts per status and per QA run), the log.
Self-contained (no requests; one tiny inline script turns the time into "n min ago"). Publish it as a private page
and republish to the same link at every unit end and every stop (references/phases-and-qa.md > The progress page).

The page layout and CSS follow figma-to-wordpress's scripts/progress.py (MIT licence), so both skills show the
same page.
"""
import datetime
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import live  # noqa: E402  (next to this file)

if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(2)
SRC, OUT = sys.argv[1], sys.argv[2]
i = sys.argv.index('--json') if '--json' in sys.argv else -1
if i != -1 and i + 1 >= len(sys.argv):
    print('FAIL render: --json needs a file path')
    sys.exit(2)
REFRESH = 0
if '--refresh' in sys.argv:
    j = sys.argv.index('--refresh')
    try:
        REFRESH = int(sys.argv[j + 1])
    except (IndexError, ValueError):
        REFRESH = -1
    if REFRESH < 5:
        print('FAIL render: --refresh needs seconds (5 or more)')
        sys.exit(2)
JSON_OUT = sys.argv[i + 1] if i != -1 else os.path.join(os.path.dirname(os.path.abspath(OUT)), 'progress.json')
md = open(SRC, encoding='utf-8').read()

STATUSES = ['todo', 'building', 'built', 'checked', 'fixed']
# The shared phase ids, and which board phase each one follows.
PHASES = [('plan', 'Plan', 'P0'), ('setup', '1 Setup', 'P1'), ('pages', '2 Pages', 'P2'),
          ('forms', '3 Forms and email', 'P3'), ('seo', '4 SEO, security, speed', 'P4'), ('fix', 'Fix list', 'P5'),
          ('qa', 'QA until 0', 'P5'), ('golive', 'Go-live gate', 'gate'), ('live', 'Live and report', 'P6')]
MONTHS = {m: i for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov',
                                      'dec'], 1)}


def cells(line):
    """A table row's cells; an escaped pipe (backslash, pipe) stays inside its cell as |."""
    parts = re.split(r'(?<!\\)\|', line.strip().strip('|'))
    return [p.replace('\\|', '|').strip() for p in parts]


def rows_of(lines):
    for i, line in enumerate(lines):
        if line.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[-:| ]+\|$', lines[i + 1].strip()):
            out = []
            for row in lines[i + 2:]:
                if not row.startswith('|'):
                    break
                out.append(cells(row))
            return out
    return []


def plain(s):
    return re.sub(r'[`*]', '', s or '').strip()


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', plain(s).lower()).strip('-') or 'page'


def iso(day):
    """'18 Nov 2026' -> '2026-11-18' (anything else stays as written)."""
    m = re.match(r'^(\d{1,2}) ([A-Za-z]{3})\w* (\d{4})', day.strip())
    if m and m.group(2).lower() in MONTHS:
        return f'{m.group(3)}-{MONTHS[m.group(2).lower()]:02d}-{int(m.group(1)):02d}'
    return day.strip()


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
    return next((sections[n] for n in order if n == name or n.startswith(name + ' ')), [])


def now_lines():
    """The board's "## Now" block: Doing (started HH:MM), Next, Waiting on the developer, Blocked."""
    got = {}
    for line in section('Now'):
        m = re.match(r'^- \*\*(Doing|Next|Waiting[^:*]*|Blocked):\*\*\s*(.*)$', line.strip())
        if m:
            got[m.group(1).split(' ')[0].lower()] = plain(m.group(2)).rstrip('.')
    return got


def started_at(text):
    """'P5 QA run 2 (started 14:05)' -> ('P5 QA run 2', '<today>T14:05'); a date before the time is kept."""
    m = re.search(r'\s*\(started (?:(.+?) )?(\d{1,2}:\d{2})\)\s*$', text)
    if not m:
        return text, ''
    day = iso(m.group(1)) if m.group(1) else RENDERED[:10]
    return text[:m.start()].strip(), f'{day}T{int(m.group(2).split(":")[0]):02d}:{m.group(2).split(":")[1]}'


RENDERED = datetime.datetime.now().astimezone().isoformat(timespec='minutes')
hm = re.search(r'^# BUILD-MAP:\s*(.+?)\s+(?:WordPress\s+)?build\s*$', md, re.M)
um = re.search(r'Updated: \*\*(.+?)\*\*', md)

board_phase = {}
for r in rows_of(section('Phases')):
    if len(r) >= 3:
        board_phase[r[0].split(' ')[0]] = {'status': plain(r[2]).upper(), 'qa': r[3] if len(r) > 3 else ''}
go_live = next((r[1] for r in rows_of(section('Developer gates')) if len(r) > 1 and r[0].lower() == 'go-live'), '')


def phase_status(ref, pid):
    if ref == 'gate':
        return 'done' if go_live.lower().startswith('ok') else 'todo'
    st = board_phase.get(ref, {}).get('status', 'TODO')
    if pid == 'qa' and st != 'DONE':
        return 'doing' if re.search(r'\d+ found', board_phase.get(ref, {}).get('qa', '')) else 'todo'
    return {'DONE': 'done', 'IN PROGRESS': 'doing', 'BLOCKED': 'doing'}.get(st, 'todo')


pages, index = [], {}
for r in rows_of(section('Pages')):
    if len(r) < 4:
        continue
    key = slug(r[0])
    if key not in index:
        index[key] = {'slug': key, 'name': plain(r[0]), 'route': plain(r[1]), 'desktop': '', 'mobile': '',
                      'sections': []}
        pages.append(index[key])
    st = plain(r[3]).lower()
    index[key]['sections'].append({'slug': slug(r[2]), 'status': st if st in STATUSES else 'todo'})

findings = []
for r in rows_of(section('QA findings')):
    if len(r) < 6 or not any(r):
        continue
    # "Page / Section" (spaces around the slash) or "Page > Section" points at the Pages table; anything else (a
    # file such as assets/x.css, wp-admin) stays as written, with no section.
    where = [plain(x) for x in re.split(r'\s+/\s+|\s*>\s*', r[2], maxsplit=1)]
    known = slug(where[0]) in index
    findings.append({'id': plain(r[0]), 'severity': plain(r[4]).lower(),
                     'page': slug(where[0]) if known else plain(r[2]),
                     'section': slug(where[1]) if known and len(where) > 1 and where[1] else '', 'what': plain(r[3]),
                     'expected': '', 'measured': '', 'phase': plain(r[1]), 'status': plain(r[5]).lower(),
                     'note': '', 'added': '', 'closed': ''})

log = []
for line in section('Log'):
    m = re.match(r'^- (.+?):\s+(.*)$', line.strip())
    if m:
        log.append({'at': iso(m.group(1)), 'text': plain(m.group(2))})
log.reverse()  # the board lists newest first; the shared shape appends

nl = now_lines()
doing, started = started_at(nl.get('doing', ''))
hn = re.search(r'\| Next: \*\*(.+?)\*\*', md)  # old boards: no Next line in "## Now", the header has one

data = {'site': hm.group(1).strip() if hm else 'Site', 'target': 'wordpress', 'figma': '', 'url': '',
        'updated': RENDERED,
        'now': {'step': doing, 'started': started}, 'next': nl.get('next') or (plain(hn.group(1)) if hn else ''),
        'waiting': nl.get('waiting', ''), 'blocked': nl.get('blocked', ''),
        'phases': [{'id': pid, 'name': name, 'status': phase_status(ref, pid)} for pid, name, ref in PHASES],
        'pages': pages, 'findings': findings, 'log': log}
if os.path.isfile(JSON_OUT):  # keep the published links saved earlier (the static page and the live page)
    try:
        old = json.load(open(JSON_OUT, encoding='utf-8'))
        data['url'], data['live_url'] = old.get('url', ''), old.get('live_url', '')
    except (OSError, ValueError):
        pass
if '--pushed' in sys.argv:  # the chat wrote progress-rows.json to the database: remember what it holds now
    n = live.mark_pushed(os.path.dirname(os.path.abspath(JSON_OUT)))
    print(f'ok: {n} database writes marked as pushed')
    sys.exit(0)
with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as fh:
    json.dump(data, fh, indent=1, ensure_ascii=False)

# ---------- the page (same layout as figma-to-wordpress's progress.py) ----------

CSS = """
:root{--bg:#f7f7f5;--card:#fff;--ink:#1c1c1a;--mute:#6b6b66;--line:#e4e3de;--todo:#d9d8d2;--building:#f2b84b;
--built:#5b8def;--checked:#3fa66b;--fixed:#2d8a8a;--open:#d9534f;--chipink:#fff}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#151514;--card:#1f1f1d;--ink:#ecebe6;
--mute:#a3a29b;--line:#34332f;--todo:#4a4944;--building:#c9962f;--built:#4a76c9;--checked:#2f8a56;--fixed:#2a7a7a;
--open:#c9473f}}
:root[data-theme="dark"]{--bg:#151514;--card:#1f1f1d;--ink:#ecebe6;--mute:#a3a29b;--line:#34332f;--todo:#4a4944;
--building:#c9962f;--built:#4a76c9;--checked:#2f8a56;--fixed:#2a7a7a;--open:#c9473f}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 48px}h1{font-size:26px;margin:0 0 4px}
h2{font-size:18px;margin:28px 0 10px}.mute{color:var(--mute)}.card{background:var(--card);border:1px solid var(--line);
border-radius:10px;padding:14px 16px}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));
gap:10px;margin-top:16px}.stat b{display:block;font-size:24px}.phases{display:flex;flex-wrap:wrap;gap:6px}
.ph{padding:5px 10px;border-radius:999px;border:1px solid var(--line);font-size:13px}.ph-doing{border-color:
var(--building);font-weight:600}.ph-done{background:var(--checked);border-color:var(--checked);color:var(--chipink)}
.bar{display:flex;height:10px;border-radius:999px;overflow:hidden;background:var(--todo);margin-top:12px}
table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:8px 6px;border-top:1px solid var(--line);
vertical-align:top}th{font-size:13px;color:var(--mute);font-weight:500}.chips{display:flex;flex-wrap:wrap;gap:4px}
.chip{font-size:12px;padding:2px 8px;border-radius:999px;color:var(--chipink);white-space:nowrap}
.todo{background:var(--todo);color:var(--ink)}.building{background:var(--building);color:#1c1c1a}
.built{background:var(--built)}.checked{background:var(--checked)}.fixed{background:var(--fixed)}
.chip.has-open{outline:2px solid var(--open);outline-offset:1px}.sev{font-weight:600}.sev.blocker,.sev.major{
color:var(--open)}.legend{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}.scroll{overflow-x:auto}
ul.log{list-style:none;padding:0;margin:0}ul.log li{padding:4px 0;border-top:1px solid var(--line)}
.now{margin-top:14px;border-left:6px solid var(--building)}.now .big{font-size:22px;line-height:1.35}
.now .lbl{display:inline-block;min-width:64px;font-size:13px;color:var(--mute);text-transform:uppercase;
letter-spacing:.04em}.now .upd{font-size:20px;font-weight:600;margin-top:8px}.st{font-size:12px;padding:2px 8px;
border-radius:999px;color:var(--chipink);white-space:nowrap}.st.open{background:var(--open)}.st.fixed{
background:var(--fixed)}.st.decided{background:var(--todo);color:var(--ink)}.counts{display:flex;flex-wrap:wrap;
gap:8px;margin:0 0 10px}details summary{cursor:pointer;padding:8px 0}
@media (max-width:640px){td,th{padding:6px 4px}.hide-sm{display:none}.now .big{font-size:18px}}
"""


def e(s):
    return html.escape(str(s or ''))


def open_findings(page=None, sec=None):
    return [f for f in data['findings'] if f['status'] == 'open'
            and (page is None or f.get('page') == page) and (sec is None or f.get('section') == sec)]


c = {s: 0 for s in STATUSES}
for p in data['pages']:
    for s in p['sections']:
        c[s['status']] += 1
total = sum(c.values()) or 1
of = open_findings()
done = c['checked'] + c['fixed']
bar = ''.join(f'<span class="{s}" style="width:{c[s] * 100 / total:.2f}%"></span>'
              for s in ('fixed', 'checked', 'built', 'building'))
phases = ''.join(f'<span class="ph ph-{p["status"]}">{e(p["name"])}</span>' for p in data['phases'])
legend = ''.join(f'<span class="chip {s}">{s}</span>' for s in STATUSES)
rows = []
for p in data['pages']:
    chips = []
    for s in p['sections']:
        n = len(open_findings(p['slug'], s['slug']))
        mark = f' ({n} open)' if n else ''
        chips.append(f'<span class="chip {s["status"]}{" has-open" if n else ""}" '
                     f'title="{e(s["slug"])}: {s["status"]}{mark}">{e(s["slug"])}{mark}</span>')
    pdone = sum(1 for s in p['sections'] if s['status'] in ('checked', 'fixed'))
    rows.append(f'<tr><td><b>{e(p["name"])}</b><br><span class="mute">{e(p["route"])}</span></td>'
                f'<td><div class="chips">{"".join(chips)}</div></td>'
                f'<td class="hide-sm">{pdone}/{len(p["sections"])}</td></tr>')
FSTATES = ('open', 'fixed', 'decided')


def frow(f):
    st = f['status'] if f['status'] in FSTATES else 'open'
    return (f'<tr><td>{e(f["id"])}</td><td><span class="st {st}">{e(f["status"])}</span></td>'
            f'<td class="sev {e(f["severity"])}">{e(f["severity"])}</td><td class="hide-sm">{e(f["phase"])}</td>'
            f'<td>{e(f["page"])}{"/" + e(f["section"]) if f["section"] else ""}</td><td>{e(f["what"])}</td></tr>')


def by_sev(f):
    return ['blocker', 'major', 'minor'].index(f['severity']) if f['severity'] in ('blocker', 'major', 'minor') else 3


FHEAD = ('<tr><th>ID</th><th>Status</th><th>Severity</th><th class="hide-sm">QA run</th><th>Where</th>'
         '<th>What</th></tr>')
closed = [f for f in data['findings'] if f['status'] != 'open']
fcount = {s: sum(1 for f in data['findings'] if f['status'] == s) for s in FSTATES}
fcounts = ' &middot; '.join(f'<span class="st {s}">{fcount[s]} {s}</span>' for s in FSTATES)
runs = {}  # the Phase column names the QA run ("P2", "P5 run 2"); first seen first
for f in data['findings']:
    runs.setdefault(f['phase'] or '?', {s: 0 for s in FSTATES})[f['status'] if f['status'] in FSTATES else 'open'] += 1
run_rows = ''.join(f'<tr><td>{e(k)}</td><td>{sum(v.values())}</td><td>{v["open"]}</td><td>{v["fixed"]}</td>'
                   f'<td>{v["decided"]}</td></tr>' for k, v in runs.items())
frows = ''.join(frow(f) for f in sorted(of, key=by_sev))
crows = ''.join(frow(f) for f in closed)


def hm_time(stamp):
    """'2026-11-20T14:05+08:00' -> '20 Nov 2026 14:05'."""
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})T(\d{2}:\d{2})', stamp or '')
    if not m:
        return (stamp or '').replace('T', ' ')
    mon = [k for k, v in MONTHS.items() if v == int(m.group(2))][0].title()
    return f'{int(m.group(3))} {mon} {m.group(1)} {m.group(4)}'


now_d = data['now']
now_html = (f'<div class="big"><span class="lbl">Now</span> <b>{e(now_d["step"]) or "nothing written"}</b>'
            + (f' <span class="mute">started {e(now_d["started"][11:16])}</span>' if now_d['started'] else '')
            + '</div>'
            + (f'<div class="big"><span class="lbl">Next</span> {e(data["next"])}</div>' if data['next'] else '')
            + ''.join(f'<div><span class="lbl">{label}</span> {e(data[k])}</div>'
                      for k, label in (('waiting', 'Waiting'), ('blocked', 'Blocked'))
                      if data[k] and data[k].lower() not in ('nothing', 'none', 'no'))
            + f'<div class="upd">Updated {e(hm_time(data["updated"]))} '
              f'<span class="mute" id="ago" data-at="{e(data["updated"])}"></span></div>')
AGO = ("<script>(function(){var t=document.getElementById('ago'),d=new Date(t.getAttribute('data-at'));"
       "function f(){var m=Math.floor((Date.now()-d)/60000);if(isNaN(m)||m<0)return;t.textContent='('+(m<1?"
       "'just now':m<60?m+' min ago':Math.floor(m/60)+' h '+m%60+' min ago')+')'}f();setInterval(f,60000)})();"
       "</script>")
log_html = ''.join(f'<li><span class="mute">{e(x["at"][:16].replace("T", " "))}</span> {e(x["text"])}</li>'
                   for x in reversed(data['log'][-25:]))
title = f'{data["site"]} build progress'
page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
{f'<meta http-equiv="refresh" content="{REFRESH}">' if REFRESH else ''}<title>{e(title)}</title><style>{CSS}</style></head><body><main>
<h1>{e(title)}</h1>
<div class="mute">Target: {e(data["target"])}</div>
<div class="card now">{now_html}</div>
<div class="stats">
<div class="card stat"><b>{done}/{sum(c.values())}</b>sections done</div>
<div class="card stat"><b>{c["building"] + c["built"]}</b>building or built</div>
<div class="card stat"><b>{c["todo"]}</b>to do</div>
<div class="card stat"><b>{len(of)}</b>open findings</div>
</div>
<div class="bar">{bar}</div>
<h2>Phases</h2><div class="phases">{phases}</div>
<h2>Pages and sections</h2><div class="legend">{legend}</div>
<div class="card scroll"><table><tr><th>Page</th><th>Sections</th><th class="hide-sm">Done</th></tr>
{''.join(rows) or '<tr><td colspan="3" class="mute">No pages yet.</td></tr>'}</table></div>
<h2>QA findings ({len(data["findings"])}): {len(of)} open</h2>
<div class="card scroll"><div class="counts">{fcounts}</div>
{f'<table><tr><th>QA run</th><th>Found</th><th>Open</th><th>Fixed</th><th>Decided</th></tr>{run_rows}</table>'
 if run_rows else ''}
<h3>Open ({len(of)})</h3><table>{FHEAD}
{frows or '<tr><td colspan="6" class="mute">None open.</td></tr>'}</table>
{f'<details><summary>Fixed and decided ({len(closed)})</summary><table>{FHEAD}{crows}</table></details>'
 if closed else ''}</div>
<h2>Log</h2><div class="card"><ul class="log">{log_html}</ul></div>
</main>{AGO}</body></html>
"""
with open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
    fh.write(page)
n_rows = live.write(data, CSS, os.path.dirname(os.path.abspath(JSON_OUT)))
print(f'ok: {len(data["phases"])} phases, {sum(c.values())} sections ({done} done), {len(data["findings"])} findings '
      f'({len(of)} open), {len(log)} log lines; wrote {os.path.basename(OUT)} and {os.path.basename(JSON_OUT)}; '
      f'{n_rows} database writes in progress-rows.json')
if '--open' in sys.argv:  # tools without a published page: the local file in the default browser
    import pathlib
    import webbrowser
    uri = pathlib.Path(os.path.abspath(OUT)).as_uri()
    print(f'opened: {uri}' if webbrowser.open(uri) else f'open this in a browser: {uri}')
