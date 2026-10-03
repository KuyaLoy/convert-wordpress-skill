#!/usr/bin/env python3
"""Check this computer before a conversion: the tools, the local WordPress tools, and where the new site can run.

    python3 doctor.py [--name <site>] [--json <file>]

Only looks: it never installs, downloads or changes anything and needs no network. It prints at most 15 lines:
  OK|WARN doctor ...   the verdict and the Python command to use for every kit script on this computer
  Ready / Missing      tools with versions; anything missing comes with the install line for this system
  Found                local WordPress tools: web folder, address pattern, database defaults
  Suggested            where to build, the address, how WordPress and the database are made
  Warnings             synced folders (OneDrive, Dropbox...), spaces or long paths, ports in use, low disk space
--json writes the same as data, so the agent can fill site.json and the profile instead of asking.

Knows Laragon, XAMPP, MAMP, WampServer, Local, Laravel Herd, DDEV, wp-env, WordPress Studio and a native
Apache/Nginx + PHP + MySQL setup. Tools that give every site its own address (Laragon, Herd, Local, DDEV) are
used as they are; for the others the site runs on its own port with serve-wp.py (http://localhost:8081), so every
page stays at the root and the 1:1 comparison works.

Exit 0: there is a way to run WordPress here. Exit 3: not yet (the report says what to install).
Tests: --root <dir> treats <dir> as the file system (C:/x becomes <dir>/C/x), --home and --os fake the rest.
"""
import argparse
import glob
import json
import os
import re
import shutil
import socket
import subprocess
import sys

ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
ap.add_argument('--name', default='my-site', help='the site name, for the suggested folder and address')
ap.add_argument('--json', help='also write the report as JSON to this file')
ap.add_argument('--root', help=argparse.SUPPRESS)
ap.add_argument('--home', help=argparse.SUPPRESS)
ap.add_argument('--os', choices=['windows', 'mac', 'linux'], help=argparse.SUPPRESS)
a = ap.parse_args()

OSN = a.os or {'win32': 'windows', 'darwin': 'mac'}.get(sys.platform, 'linux')
ROOT = a.root
HOME = (a.home or os.path.expanduser('~')).replace('\\', '/')
TEST = bool(ROOT)
NAME = re.sub(r'[^a-z0-9]+', '-', a.name.lower()).strip('-') or 'my-site'


def real(p):
    """The path to look at: the real one, or the same path inside --root for tests."""
    p = p.replace('\\', '/')
    if not ROOT or p.startswith(ROOT.replace('\\', '/')):
        return p
    m = re.match(r'^([A-Za-z]):/(.*)', p)
    return os.path.join(ROOT, m.group(1).upper(), m.group(2)) if m else os.path.join(ROOT, p.lstrip('/'))


def exists(p):
    return os.path.exists(real(p))


def shown(p):
    """A path as the developer sees it (inside --root for tests: without the fake root)."""
    p = p.replace('\\', '/')
    if ROOT:
        r = ROOT.replace('\\', '/').rstrip('/')
        if p.startswith(r + '/'):
            rest = p[len(r) + 1:]
            m = re.match(r'^([A-Z])/(.*)', rest) if OSN == 'windows' else None
            p = f'{m.group(1)}:/{m.group(2)}' if m else '/' + rest
    return p


def newest(pattern):
    hits = sorted(glob.glob(real(pattern)))
    return shown(hits[-1]) if hits else None


def version(cmd):
    try:
        out = subprocess.run(cmd + ['--version'], capture_output=True, text=True, timeout=5)
        line = (out.stdout or out.stderr).strip().splitlines()[0]
    except Exception:
        return None
    m = re.search(r'Distrib (\d+\.\d+\.\d+)', line) or re.search(r'(\d+\.\d+(\.\d+)?)', line)
    return m.group(1) if m else line[:40]


def which(name):
    return shutil.which(name)


def port_open(port):
    if TEST:
        return False
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=0.25):
            return True
    except OSError:
        return False


def python_cmd():
    if OSN == 'windows':
        if which('py'):
            return 'py -3'
        for n in ('python', 'python3'):
            p = which(n)
            if p and 'WindowsApps' not in p:  # the Microsoft Store alias opens the Store instead of Python
                return n
        return f'"{sys.executable}"'
    return 'python3' if which('python3') else f'"{sys.executable}"'


INSTALL = {
    'windows': {'node': 'winget install -e --id OpenJS.NodeJS.LTS', 'git': 'winget install -e --id Git.Git',
                'python': 'winget install -e --id Python.Python.3.12', 'composer': 'getcomposer.org/download'},
    'mac': {'node': 'brew install node (or nodejs.org)', 'git': 'xcode-select --install',
            'python': 'brew install python (or python.org)', 'composer': 'brew install composer'},
    'linux': {'node': 'sudo apt install nodejs npm (or nodejs.org)', 'git': 'sudo apt install git',
              'python': 'sudo apt install python3', 'composer': 'sudo apt install composer'},
}[OSN]

# ---- tools ---------------------------------------------------------------------------------------------------
tools = {'python': {'version': '.'.join(map(str, sys.version_info[:3])), 'command': python_cmd()}}
for key, cmds in (('node', ['node']), ('npm', ['npm']), ('git', ['git']), ('php', ['php']),
                  ('composer', ['composer']), ('wp', ['wp']), ('mysql', ['mysql', 'mariadb']), ('docker', ['docker'])):
    for c in cmds:
        p = which(c)
        if p:
            tools[key] = {'path': shown(p), 'version': version([p])}
            break



def playwright_ready():
    """Playwright and a downloaded Chromium, found the way scripts/report/pw.mjs finds them."""
    kit = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    roots = [os.path.join(kit, *parts, 'node_modules') for parts in ((), ('scripts',), ('scripts', 'report'))]
    roots += [x for x in os.environ.get('NODE_PATH', '').split(os.pathsep) if x]
    if 'npm' in tools:
        try:
            roots.append(subprocess.run([which('npm'), 'root', '-g'], capture_output=True, text=True,
                                        timeout=10).stdout.strip())
        except Exception:
            pass
    package = any(r and os.path.isfile(os.path.join(r, 'playwright', 'package.json')) for r in roots)
    cache = os.environ.get('PLAYWRIGHT_BROWSERS_PATH') or {
        'windows': os.path.join(os.environ.get('LOCALAPPDATA', HOME + '/AppData/Local'), 'ms-playwright'),
        'mac': HOME + '/Library/Caches/ms-playwright', 'linux': HOME + '/.cache/ms-playwright'}[OSN]
    browser = bool(glob.glob(os.path.join(real(cache), 'chromium*'))) or os.path.isfile(os.environ.get('CHROME_PATH', '-'))
    return package and browser


if 'node' in tools and not playwright_ready():
    tools['playwright'] = None

# ---- local WordPress tools -----------------------------------------------------------------------------------
stacks = []


def add(name, base, www, url, serve, db, php=None, **extra):
    stacks.append({'name': name, 'base': base, 'www': www, 'url': url, 'serve': serve, 'db': db, 'php': php,
                   'running': port_open(db.get('port', 3306)) if db.get('port') else None, **extra})


root_db = {'host': '127.0.0.1', 'port': 3306, 'user': 'root', 'password': 'empty'}
if OSN == 'windows':
    for d in 'CDEF':
        base = f'{d}:/laragon'
        if exists(base + '/www') or exists(base + '/laragon.exe'):
            www = base + '/www'
            ini = real(base + '/usr/laragon.ini')
            if os.path.exists(ini):
                m = re.search(r'(?im)^\s*(?:wwwdir|documentroot)\s*=\s*(.+)$', open(ini, encoding='utf-8', errors='ignore').read())
                if m:
                    www = m.group(1).strip().replace('\\', '/')
            add('Laragon', base, www, 'http://{name}.test', 'vhost', dict(root_db),
                php=newest(base + '/bin/php/php-*/php.exe'), note='free; shows a reminder until you buy a licence')
            break
    if exists('C:/xampp/htdocs'):
        add('XAMPP', 'C:/xampp', 'C:/xampp/htdocs', 'http://localhost:8081', 'serve-wp', dict(root_db),
            php='C:/xampp/php/php.exe' if exists('C:/xampp/php/php.exe') else None)
    if exists('C:/MAMP/htdocs'):
        add('MAMP', 'C:/MAMP', 'C:/MAMP/htdocs', 'http://localhost:8081', 'serve-wp',
            dict(root_db, password='root'), php=newest('C:/MAMP/bin/php/php*/php.exe'))
    for base in ('C:/wamp64', 'C:/wamp'):
        if exists(base + '/www'):
            add('WampServer', base, base + '/www', 'http://localhost:8081', 'serve-wp', dict(root_db),
                php=newest(base + '/bin/php/php*/php.exe'))
            break
elif OSN == 'mac':
    if exists('/Applications/MAMP/htdocs'):
        add('MAMP', '/Applications/MAMP', '/Applications/MAMP/htdocs', 'http://localhost:8081', 'serve-wp',
            dict(root_db, port=8889, password='root'), php=newest('/Applications/MAMP/bin/php/php*/bin/php'))
    if exists('/Applications/XAMPP/xamppfiles/htdocs'):
        add('XAMPP', '/Applications/XAMPP', '/Applications/XAMPP/xamppfiles/htdocs', 'http://localhost:8081',
            'serve-wp', dict(root_db), php='/Applications/XAMPP/xamppfiles/bin/php')
else:
    if exists('/opt/lampp/htdocs'):
        add('XAMPP', '/opt/lampp', '/opt/lampp/htdocs', 'http://localhost:8081', 'serve-wp', dict(root_db),
            php='/opt/lampp/bin/php')

# Local (localwp.com): its sites are listed in sites.json.
local_json = {'windows': HOME + '/AppData/Roaming/Local/sites.json',
              'mac': HOME + '/Library/Application Support/Local/sites.json',
              'linux': HOME + '/.config/Local/sites.json'}[OSN]
if exists(local_json):
    try:
        data = json.load(open(real(local_json), encoding='utf-8'))
    except Exception:
        data = {}
    sites = [{'name': v.get('name', ''), 'path': v.get('path', '').replace('~', HOME, 1) + '/app/public',
              'domain': v.get('domain', '')} for v in (data.values() if isinstance(data, dict) else [])]
    add('Local', shown(os.path.dirname(real(local_json))), HOME + '/Local Sites/{name}/app/public',
        'http://{name}.local', 'local-app', {'host': 'the site in Local', 'user': 'root', 'password': 'root',
                                               'name': 'local'}, sites=sites,
        note='make the site in Local (+, Create a new site), then the skill keeps its WordPress')

if exists(HOME + '/Herd') or which('herd'):
    add('Herd', HOME + '/Herd', HOME + '/Herd', 'http://{name}.test', 'vhost',
        {'host': '127.0.0.1', 'port': 3306, 'user': 'root', 'password': 'empty',
         'note': 'MySQL comes with Herd Pro, or use DBngin'}, php=shown(which('php')) if which('php') else None)
if which('ddev'):
    add('DDEV', '', '<your projects folder>/{name}', 'https://{name}.ddev.site', 'ddev',
        {'host': 'db', 'user': 'db', 'password': 'db', 'name': 'db'}, note='needs Docker running')
if which('wp-env'):
    add('wp-env', '', '<your projects folder>/{name}', 'http://localhost:8888', 'wp-env',
        {'host': 'in Docker', 'user': 'root', 'password': 'password'}, note='needs Docker running')
if exists(HOME + '/Studio'):
    add('WordPress Studio', HOME + '/Studio', HOME + '/Studio/{name}', 'http://localhost:8881', 'studio',
        {'host': 'SQLite'}, note='uses SQLite: fine for trying, not for the Duplicator move to a normal host')

native_www = {'linux': '/var/www/html', 'mac': '/opt/homebrew/var/www', 'windows': ''}[OSN]
if native_www and exists(native_www) and 'php' in tools and 'mysql' in tools and any(
        which(s) for s in ('apache2', 'httpd', 'nginx')):
    add('Native', native_www, native_www, 'http://localhost:8081', 'serve-wp', dict(root_db), php=tools['php']['path'])

# ---- suggestion ----------------------------------------------------------------------------------------------
ORDER = ['Laragon', 'Herd', 'Local', 'DDEV', 'MAMP', 'XAMPP', 'WampServer', 'Native', 'wp-env']
pick = next((s for n in ORDER for s in stacks if s['name'] == n), None)
suggestion = None
if pick:
    root = pick['www'].replace('{name}', NAME)
    if '{name}' not in pick['www'] and not pick['www'].startswith('<'):
        root = pick['www'].rstrip('/') + '/' + NAME
    suggestion = {
        'stack': pick['name'], 'wp_root': shown(root), 'url': pick['url'].replace('{name}', NAME), 'serve': pick['serve'],
        'wordpress': 'existing' if pick['serve'] in ('local-app', 'ddev', 'wp-env') else 'download',
        'db': pick['db'], 'php': pick.get('php'),
    }
elif 'php' in tools and 'mysql' in tools:
    suggestion = {'stack': 'PHP and MySQL on this computer', 'wp_root': shown(f'{HOME}/Sites/{NAME}'),
                  'url': 'http://localhost:8081', 'serve': 'serve-wp', 'wordpress': 'download', 'db': dict(root_db),
                  'php': tools['php']['path']}

# ---- warnings ------------------------------------------------------------------------------------------------
warnings = []
cwd = shown(os.getcwd())
places = [('this folder', cwd)] + ([('the suggested folder', suggestion['wp_root'])] if suggestion else [])
for label, p in places:
    if re.search(r'(?i)onedrive|dropbox|icloud|google drive|googledrive|box sync', p):
        warnings.append({'kind': 'synced', 'text': f'{label} is in a synced folder ({p}): builds and node_modules there '
                                                    'are slow and can clash; use a folder outside it'})
    # Local's own "Local Sites" folder has a space by design and Local copes with it.
    if ' ' in p and not (label == 'the suggested folder' and pick and pick['name'] == 'Local'):
        warnings.append({'kind': 'spaces', 'text': f'{label} has spaces in its path ({p}): some tools break on them'})
    if len(p) > 100:
        warnings.append({'kind': 'long', 'text': f'{label} has a long path: keep projects near the top of a drive'})
if not TEST:
    for port in (80, 443, 8081):
        if port_open(port):
            warnings.append({'kind': 'port', 'text': f'port {port} is in use' +
                             (': serve-wp.py will need another port (--port)' if port == 8081 else '')})
    try:
        free = shutil.disk_usage(real(suggestion['wp_root'].split('{')[0]) if suggestion else os.getcwd()).free
    except OSError:
        free = shutil.disk_usage(os.getcwd()).free
    if free < 2 * 1024 ** 3:
        warnings.append({'kind': 'disk', 'text': f'only {free // 1024 ** 2} MB free: a conversion needs about 2 GB'})
    if OSN == 'windows':
        try:
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                warnings.append({'kind': 'admin', 'text': 'not an administrator: installers may ask for an admin'})
        except Exception:
            pass

# ---- report --------------------------------------------------------------------------------------------------
missing = [k for k in ('node', 'git') if k not in tools] + (['playwright'] if 'playwright' in tools else [])
tools.pop('playwright', None)
if sys.version_info < (3, 9):
    missing.insert(0, 'python')
needs = {'node': 'Node.js 18+ (the comparison and report tools)', 'git': 'git (GitHub links)',
         'python': 'Python 3.9+', 'playwright': 'Playwright with Chromium (live capture, comparisons, report)'}
INSTALL['playwright'] = 'npm install -g playwright, then npx playwright install chromium'
ok = suggestion is not None and 'python' not in missing
osname = {'windows': 'Windows', 'mac': 'macOS', 'linux': 'Linux'}[OSN]
log = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'CHANGELOG.md')
skill = re.search(r'^## \[(\d+\.\d+\.\d+)\] - \d{4}-\d{2}-\d{2}', open(log, encoding='utf-8').read() if os.path.isfile(log)
                  else '', re.M)
skill = skill.group(1) if skill else None
lines = [f"{'OK' if ok else 'WARN'} doctor: {osname}, Python {tools['python']['version']} "
         f"(run the kit's scripts with: {tools['python']['command']}), {len(stacks)} local WordPress tool(s) found"
         + (f", skill {skill} (newer? update.py --check)" if skill else '')]
ready = [f"{k} {v.get('version') or ''}".strip() for k, v in tools.items() if k not in ('python', 'npm')]
lines.append('Ready: ' + (', '.join(ready) if ready else 'Python only'))
if missing:
    lines.append('Missing: ' + '; '.join(f"{needs[k]}: {INSTALL[k]}" for k in missing))
for s in stacks[:4]:
    db = s['db']
    dbtxt = f"database {db.get('user', '')}/{'no password' if db.get('password') == 'empty' else db.get('password', '')}"
    where = s['www'].replace('{name}', '<name>')
    lines.append(f"Found: {s['name']} (web folder {where}, sites at {s['url'].replace('{name}', '<name>')}, {dbtxt})")
if suggestion:
    how = {'vhost': 'its own address', 'serve-wp': 'serve-wp.py on its own port', 'local-app':
           'make it in Local first, the skill keeps that WordPress', 'ddev': 'ddev start', 'wp-env': 'wp-env start'}
    lines.append(f"Suggested: build in {suggestion['wp_root']}, address {suggestion['url']} "
                 f"({how.get(suggestion['serve'], suggestion['serve'])})")
else:
    lines.append({'windows': 'Suggested: install one free local WordPress tool: Local (localwp.com, then Create a new '
                             'site) or Laragon (laragon.org), then run this again',
                  'mac': 'Suggested: install one free local WordPress tool: Local (localwp.com, then Create a new '
                         'site), then run this again',
                  'linux': 'Suggested: install Local (localwp.com), or PHP 8.1+ and MariaDB (then serve-wp.py), '
                           'then run this again'}[OSN])
for w in warnings[:3]:
    lines.append('Warning: ' + w['text'])
if not warnings:
    lines.append('Warnings: none')
if a.json:
    lines.append(f'Details: {a.json}')
print('\n'.join(lines[:15]))

if a.json:
    report = {'os': OSN, 'skill': skill, 'python': tools['python']['command'], 'tools': tools, 'stacks': stacks,
              'suggestion': suggestion, 'warnings': warnings, 'missing': missing, 'ok': ok}
    os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
    json.dump(report, open(a.json, 'w', encoding='utf-8'), indent=2)
sys.exit(0 if ok else 3)
