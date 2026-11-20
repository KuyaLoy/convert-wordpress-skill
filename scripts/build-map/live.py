"""The live progress page: the same page as progress.html, but it reads its data from the artifact's database, so an
open page updates itself when the chat writes rows; no republish.

render.py calls write(): it writes next to progress.json
  progress-live.html  the page (publish it once, privately, with capabilities {"db": {"rules": [{"path": "",
                      "read": "view", "write": "admin"}]}}); it carries the data of the moment it was rendered and
                      shows that when the database cannot be reached (another tool, a local preview)
  progress-rows.json  the database writes since the last push: {"url", "count", "batches": [[{op, collection,
                      doc_id, data}]], "existing": ["collection/doc_id"]}; each batch goes to ArtifactData "batch"
                      as it is, and a write to a document in "existing" needs that document's version
                      (if_version, from one ArtifactData "list" of its collection)
`render.py ... --pushed` records the rows as pushed (progress-pushed.json) after the writes went through.

Collections (the same names as figma-to-wordpress's live page and the tracker pages):
  meta/now     site, target, now, nowStarted, next, waiting, blocked, updated, static (the static page link)
  phases/<id>  id, name, status (todo, doing, done), order
  items/<page>--<section>  group (page name), page (slug), route, name (section slug), status (todo, building,
               built, checked, fixed), order
  findings/<id>  ref, text, where, run (the QA run: P2, P5 run 2), severity, status (open, fixed, decided)
  log/<id>     at, text (only added, never rewritten; the page shows the newest 30)
"""
import hashlib
import json
import os

BATCH = 50  # the most writes one ArtifactData batch takes


def docs(data):
    """progress.json -> {"collection/doc_id": fields}."""
    out = {'meta/now': {'site': data.get('site', ''), 'target': data.get('target', ''),
                        'now': (data.get('now') or {}).get('step', ''),
                        'nowStarted': (data.get('now') or {}).get('started', ''), 'next': data.get('next', ''),
                        'waiting': data.get('waiting', ''), 'blocked': data.get('blocked', ''),
                        'updated': data.get('updated', ''), 'static': data.get('url', '')}}
    for i, p in enumerate(data.get('phases', [])):
        out[f'phases/{p["id"]}'] = {'id': p['id'], 'name': p['name'], 'status': p['status'], 'order': i}
    n = 0
    for p in data.get('pages', []):
        for s in p['sections']:
            out[f'items/{p["slug"]}--{s["slug"]}'] = {'group': p['name'], 'page': p['slug'], 'route': p['route'],
                                                       'name': s['slug'], 'status': s['status'], 'order': n}
            n += 1
    for f in data.get('findings', []):
        where = f['page'] + ('/' + f['section'] if f.get('section') else '')
        out[f'findings/{f["id"]}'] = {'ref': f['id'], 'text': f['what'], 'where': where, 'run': f.get('phase', ''),
                                      'severity': f['severity'], 'status': f['status']}
    for x in data.get('log', []):
        key = hashlib.sha1(f'{x["at"]}|{x["text"]}'.encode()).hexdigest()[:12]
        out[f'log/L{key}'] = {'at': x['at'], 'text': x['text']}
    return out


def writes(now, pushed):
    """The writes that bring the database from `pushed` to `now`; log rows are only ever added."""
    out = []
    for path, fields in now.items():
        if pushed.get(path) != fields:
            col, _, doc = path.rpartition('/')
            out.append({'op': 'set', 'collection': col, 'doc_id': doc, 'data': fields, 'new': path not in pushed})
    for path in pushed:
        if path not in now and not path.startswith('log/'):
            col, _, doc = path.rpartition('/')
            out.append({'op': 'delete', 'collection': col, 'doc_id': doc, 'new': False})
    # meta/now last, so the page's "Updated" moves only once the rest is in.
    out.sort(key=lambda w: (w['collection'] == 'meta', w['collection'], w['doc_id']))
    return out


def load(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def write(data, css, folder):
    now = docs(data)
    pushed = load(os.path.join(folder, 'progress-pushed.json'))
    todo = writes(now, pushed)
    existing = [f'{w["collection"]}/{w["doc_id"]}' for w in todo if not w.pop('new')]
    rows = {'url': data.get('live_url', ''), 'count': len(todo), 'existing': existing,
            'batches': [todo[i:i + BATCH] for i in range(0, len(todo), BATCH)]}
    with open(os.path.join(folder, 'progress-rows.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(rows, fh, indent=1, ensure_ascii=False)
    with open(os.path.join(folder, 'progress-live.html'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(page(data, css))
    return len(todo)


def mark_pushed(folder):
    """After the writes in progress-rows.json went through: apply exactly those to what the database holds."""
    pushed = load(os.path.join(folder, 'progress-pushed.json'))
    rows = load(os.path.join(folder, 'progress-rows.json'))
    n = 0
    for batch in rows.get('batches', []):
        for w in batch:
            path = f'{w["collection"]}/{w["doc_id"]}'
            if w['op'] == 'delete':
                pushed.pop(path, None)
            else:
                pushed[path] = w['data']
            n += 1
    with open(os.path.join(folder, 'progress-pushed.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(pushed, fh, indent=1, ensure_ascii=False)
    with open(os.path.join(folder, 'progress-rows.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump({'url': rows.get('url', ''), 'count': 0, 'existing': [], 'batches': []}, fh, indent=1)
    return n


def page(data, css):
    snap = json.dumps(docs(data), ensure_ascii=False).replace('</', '<\\/')
    title = f'{data.get("site", "Site")} build progress'.replace('&', '&amp;').replace('<', '&lt;')
    return PAGE.replace('{{TITLE}}', title).replace('{{CSS}}', css).replace('{{SNAPSHOT}}', snap)


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{TITLE}}</title><style>{{CSS}}
.live{font-size:13px}.live.on{color:var(--checked)}.live.off{color:var(--mute)}</style></head><body><main>
<h1 id="title">{{TITLE}}</h1>
<div class="mute">Target: <span id="target"></span> &middot; <span class="live off" id="live">snapshot</span></div>
<div class="card now" id="now" aria-live="polite"></div>
<div class="stats" id="stats"></div>
<div class="bar" id="bar"></div>
<h2>Phases</h2><div class="phases" id="phases"></div>
<h2>Pages and sections</h2><div class="legend" id="legend"></div>
<div class="card scroll"><table id="pages"></table></div>
<h2 id="fhead">QA findings</h2>
<div class="card scroll" id="findings"></div>
<h2>Log</h2><div class="card"><ul class="log" id="log"></ul></div>
</main>
<script type="application/json" id="snapshot">{{SNAPSHOT}}</script>
<script>
(function () {
  var STATUSES = ['todo', 'building', 'built', 'checked', 'fixed'], FST = ['open', 'fixed', 'decided'];
  var SEV = ['blocker', 'major', 'minor'];
  var rows = {}, snap = {};
  try { snap = JSON.parse(document.getElementById('snapshot').textContent); } catch (e) { snap = {}; }
  function put(col, id, d) { rows[col] = rows[col] || {}; rows[col][id] = d; }
  Object.keys(snap).forEach(function (k) { var i = k.lastIndexOf('/'); put(k.slice(0, i), k.slice(i + 1), snap[k]); });
  function list(col) {
    var o = rows[col] || {};
    return Object.keys(o).map(function (k) { return o[k]; });
  }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = String(text);
    return n;
  }
  function add(p) { for (var i = 1; i < arguments.length; i++) if (arguments[i]) p.appendChild(arguments[i]); return p; }
  function stamp(iso) {
    var m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}:\d{2})/.exec(iso || '');
    if (!m) return String(iso || '');
    var mon = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ')[+m[2] - 1];
    return (+m[3]) + ' ' + mon + ' ' + m[1] + ' ' + m[4];
  }
  function ago(iso) {
    var d = new Date(iso), m = Math.floor((Date.now() - d) / 60000);
    if (!iso || isNaN(m) || m < 0) return '';
    return '(' + (m < 1 ? 'just now' : m < 60 ? m + ' min ago' : Math.floor(m / 60) + ' h ' + (m % 60) + ' min ago') + ')';
  }
  function quiet(v) { return !v || /^(nothing|none|no)$/i.test(String(v).trim()); }
  function renderNow() {
    var n = (rows.meta || {}).now || {}, box = document.getElementById('now');
    box.textContent = '';
    var a = el('div', 'big'); add(a, el('span', 'lbl', 'Now'), document.createTextNode(' '), el('b', null, n.now || 'nothing written'));
    if (n.nowStarted) add(a, document.createTextNode(' '), el('span', 'mute', 'started ' + String(n.nowStarted).slice(11, 16)));
    add(box, a);
    if (n.next) { var b = el('div', 'big'); add(b, el('span', 'lbl', 'Next'), document.createTextNode(' ' + n.next)); add(box, b); }
    [['waiting', 'Waiting'], ['blocked', 'Blocked']].forEach(function (k) {
      if (!quiet(n[k[0]])) { var r = el('div'); add(r, el('span', 'lbl', k[1]), document.createTextNode(' ' + n[k[0]])); add(box, r); }
    });
    var u = el('div', 'upd', 'Updated ' + stamp(n.updated) + ' ');
    add(u, el('span', 'mute', ago(n.updated)));
    add(box, u);
    document.getElementById('target').textContent = n.target || '';
    if (n.site) { document.title = n.site + ' build progress'; document.getElementById('title').textContent = document.title; }
  }
  function render() {
    renderNow();
    var items = list('items').sort(function (a, b) { return (a.order || 0) - (b.order || 0); });
    var c = {}; STATUSES.forEach(function (s) { c[s] = 0; });
    items.forEach(function (i) { c[STATUSES.indexOf(i.status) < 0 ? 'todo' : i.status]++; });
    var total = items.length || 1, done = c.checked + c.fixed;
    var findings = list('findings'), open = findings.filter(function (f) { return f.status === 'open'; });
    var stats = document.getElementById('stats'); stats.textContent = '';
    [[done + '/' + items.length, 'sections done'], [c.building + c.built, 'building or built'], [c.todo, 'to do'],
     [open.length, 'open findings']].forEach(function (s) {
      var d = el('div', 'card stat'); add(d, el('b', null, s[0]), document.createTextNode(s[1])); add(stats, d);
    });
    var bar = document.getElementById('bar'); bar.textContent = '';
    ['fixed', 'checked', 'built', 'building'].forEach(function (s) {
      var x = el('span', s); x.style.width = (c[s] * 100 / total).toFixed(2) + '%'; add(bar, x);
    });
    var ph = document.getElementById('phases'); ph.textContent = '';
    list('phases').sort(function (a, b) { return a.order - b.order; }).forEach(function (p) {
      add(ph, el('span', 'ph ph-' + p.status, p.name));
    });
    var lg = document.getElementById('legend'); lg.textContent = '';
    STATUSES.forEach(function (s) { add(lg, el('span', 'chip ' + s, s)); });
    var t = document.getElementById('pages'); t.textContent = '';
    var hr = el('tr'); add(hr, el('th', null, 'Page'), el('th', null, 'Sections'), el('th', 'hide-sm', 'Done')); add(t, hr);
    var groups = [];
    items.forEach(function (i) {
      var g = groups.filter(function (x) { return x.page === i.page; })[0];
      if (!g) { g = { page: i.page, name: i.group, route: i.route, list: [] }; groups.push(g); }
      g.list.push(i);
    });
    if (!groups.length) { var e = el('tr'); var td = el('td', 'mute', 'No pages yet.'); td.colSpan = 3; add(e, td); add(t, e); }
    groups.forEach(function (g) {
      var tr = el('tr'), a = el('td'), chips = el('div', 'chips'), pd = 0;
      add(a, el('b', null, g.name), el('br'), el('span', 'mute', g.route));
      g.list.forEach(function (s) {
        var n = open.filter(function (f) { return f.where === g.page + '/' + s.name; }).length;
        add(chips, el('span', 'chip ' + s.status + (n ? ' has-open' : ''), s.name + (n ? ' (' + n + ' open)' : '')));
        if (s.status === 'checked' || s.status === 'fixed') pd++;
      });
      var b = el('td'); add(b, chips);
      add(tr, a, b, el('td', 'hide-sm', pd + '/' + g.list.length)); add(t, tr);
    });
    var cnt = {}, runs = [], byRun = {};
    FST.forEach(function (s) { cnt[s] = 0; });
    findings.sort(function (a, b) { return String(a.ref).localeCompare(String(b.ref)); }).forEach(function (f) {
      var s = FST.indexOf(f.status) < 0 ? 'open' : f.status, r = f.run || '?';
      cnt[s]++;
      if (!byRun[r]) { byRun[r] = { open: 0, fixed: 0, decided: 0 }; runs.push(r); }
      byRun[r][s]++;
    });
    document.getElementById('fhead').textContent = 'QA findings (' + findings.length + '): ' + open.length + ' open';
    var fb = document.getElementById('findings'); fb.textContent = '';
    var cs = el('div', 'counts');
    FST.forEach(function (s) { add(cs, el('span', 'st ' + s, cnt[s] + ' ' + s)); });
    add(fb, cs);
    if (runs.length) {
      var rt = el('table'), rh = el('tr');
      ['QA run', 'Found', 'Open', 'Fixed', 'Decided'].forEach(function (h) { add(rh, el('th', null, h)); });
      add(rt, rh);
      runs.forEach(function (r) {
        var v = byRun[r], tr = el('tr');
        [r, v.open + v.fixed + v.decided, v.open, v.fixed, v.decided].forEach(function (x) { add(tr, el('td', null, x)); });
        add(rt, tr);
      });
      add(fb, rt);
    }
    function ftable(fs) {
      var tb = el('table'), h = el('tr');
      ['ID', 'Status', 'Severity', 'QA run', 'Where', 'What'].forEach(function (x, i) { add(h, el('th', i === 3 ? 'hide-sm' : null, x)); });
      add(tb, h);
      fs.forEach(function (f) {
        var tr = el('tr'), st = el('td');
        add(st, el('span', 'st ' + (FST.indexOf(f.status) < 0 ? 'open' : f.status), f.status));
        add(tr, el('td', null, f.ref), st, el('td', 'sev ' + f.severity, f.severity), el('td', 'hide-sm', f.run),
            el('td', null, f.where), el('td', null, f.text));
        add(tb, tr);
      });
      return tb;
    }
    add(fb, el('h3', null, 'Open (' + open.length + ')'));
    var sev = function (f) { var i = SEV.indexOf(f.severity); return i < 0 ? 3 : i; };
    var ot = ftable(open.slice().sort(function (a, b) { return sev(a) - sev(b); }));
    if (!open.length) { var nr = el('tr'), nd = el('td', 'mute', 'None open.'); nd.colSpan = 6; add(nr, nd); add(ot, nr); }
    add(fb, ot);
    var shut = findings.filter(function (f) { return f.status !== 'open'; });
    if (shut.length) {
      var d = el('details'); add(d, el('summary', null, 'Fixed and decided (' + shut.length + ')'), ftable(shut)); add(fb, d);
    }
    var lu = document.getElementById('log'); lu.textContent = '';
    list('log').sort(function (a, b) { return String(b.at).localeCompare(String(a.at)); }).slice(0, 30).forEach(function (x) {
      var li = el('li'); add(li, el('span', 'mute', String(x.at || '').slice(0, 16).replace('T', ' ')), document.createTextNode(' ' + x.text));
      add(lu, li);
    });
  }
  render();
  setInterval(renderNow, 60000);
  function status(text, on) { var s = document.getElementById('live'); s.textContent = text; s.className = 'live ' + (on ? 'on' : 'off'); }
  if (!window.claude || !window.claude.use) { status('snapshot (no live data in this view)', false); return; }
  status('connecting', false);
  window.claude.use('db').then(function (db) {
    if (!db) { status('snapshot (no live data in this view)', false); return; }
    var timer = setTimeout(function () { status('snapshot (live data not reachable yet)', false); }, 10000);
    ['meta', 'phases', 'items', 'findings', 'log'].forEach(function (col) {
      db.collection(col).onSnapshot(function (s) {
        clearTimeout(timer);
        if (!s.docs.length) { if (col === 'meta') status('snapshot (the database is still empty)', false); return; }
        rows[col] = {};
        s.docs.forEach(function (d) { rows[col][d.id] = d.data(); });
        status('live', true);
        render();
      }, function () { status('snapshot (live updates stopped; reopen the page)', false); });
    });
  }, function () { status('snapshot (no live data in this view)', false); });
})();
</script>
</body></html>
"""
