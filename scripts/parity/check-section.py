#!/usr/bin/env python3
"""One check per section (P2 step "check" and "clean"), in one call with one line back.

    python3 check-section.py <route> [--section <selector>] [--widths quick|390,1440] [--php php]
                             [--skip pixel,dom,php,phpcs,dup]

Run it in the theme's tests/parity/ (npm install done once). The hosts come from parity.config.json (REF=... and
WP=... override them). It runs:
  pixel and text: with --section, region-check.mjs on that element at the widths (nothing hidden); without it,
                  parity.mjs on the whole route (pixel, text and SEO);
  dom:            both pages fetched, domdiff.py on the section (or header, main and footer);
  php:            php -l on every PHP file of the theme (vendor, node_modules and tests left out);
  phpcs:          the theme's vendor/bin/phpcs with its phpcs.xml.dist (WARN when composer install was not run);
  dup:            the duplicate function check (two global functions with one name take the site down; php -l
                  cannot see it).
Line 1: OK|WARN|FAIL check-section <route> [<section>]: one number per part. Then the failing lines only (at most 20).
Everything else in report/check-section.log. Exit 0 OK, 1 FAIL or WARN.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
THEME_ROOT = os.path.dirname(os.path.dirname(HERE))  # <theme>/tests/parity -> <theme>
SKIP_DIRS = {'vendor', 'node_modules', 'tests', '.git', 'report'}


def run(cmd, cwd=HERE):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    except FileNotFoundError as e:
        return 127, str(e)
    return r.returncode, ((r.stdout or '') + (r.stderr or '')).strip()


def hosts():
    cfg = json.load(open(os.path.join(HERE, 'parity.config.json'), encoding='utf-8'))
    wp = (os.environ.get('WP') or cfg.get('wp') or '').rstrip('/')
    ref = (os.environ.get('REF') or cfg.get('ref') or '').rstrip('/')
    if not ref:
        for u in cfg.get('refCandidates') or []:
            try:
                urllib.request.urlopen(u + '/', timeout=3)
                ref = u.rstrip('/')
                break
            except Exception:  # noqa: BLE001 - try the next one
                continue
    return cfg, ref, wp


def fetch(url):
    """The page's HTML (a 404 page is still a page to compare), or None when the host does not answer."""
    req = urllib.request.Request(url, headers={'User-Agent': 'check-section/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.read().decode('utf-8', 'replace')
    except Exception:  # noqa: BLE001 - reported as a failure
        return None


def php_files():
    for d, dirs, files in os.walk(THEME_ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            if f.endswith('.php'):
                yield os.path.join(d, f)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('route')
    ap.add_argument('--section', help='CSS selector of the section (tag, .class, #id, tag.class)')
    ap.add_argument('--widths', default='quick')
    ap.add_argument('--php', default=os.environ.get('PHP', 'php'))
    ap.add_argument('--skip', default='')
    a = ap.parse_args()
    skip = set(x.strip() for x in a.skip.split(',') if x.strip())
    if re.match(r'^[A-Za-z]:[\\/]', a.route):
        print(f'FAIL check-section: the route arrived as a path ({a.route}): Git Bash rewrites /routes; run with '
              'MSYS_NO_PATHCONV=1, or give the route without its first slash (about/)')
        sys.exit(2)
    if a.section and ',' in a.section:
        print('FAIL check-section: --section takes one selector (no commas)')
        sys.exit(2)
    route = a.route if a.route.startswith('/') else '/' + a.route
    cfg, ref, wp = hosts()
    if not wp or '{{' in wp:
        print('FAIL check-section: parity.config.json "wp" is not set (the local WordPress address)')
        sys.exit(2)
    parts, fails, log = [], [], []
    warn = False

    def record(name, code, out, summary, bad_lines):
        log.append(f'## {name} (exit {code})\n{out}\n')
        parts.append(summary)
        if code:
            fails.extend(bad_lines or [f'{name}: exit {code}'])

    # Pixel and text (and SEO for a whole route).
    if 'pixel' not in skip:
        if not ref:
            record('pixel', 1, 'no reference host', 'pixel ?', ['pixel: no reference host answers (parity.config.json "ref")'])
        elif not shutil.which('node') or not os.path.isdir(os.path.join(HERE, 'node_modules')):
            record('pixel', 1, 'node or node_modules missing', 'pixel ?',
                   ['pixel: Node.js and npm install in tests/parity needed (or --skip pixel)'])
        else:
            widths = ','.join(map(str, cfg['widths'].get(a.widths, []))) or a.widths
            if a.section:
                code, out = run(['node', 'region-check.mjs', ref, wp, route, a.section, widths, ''])
            else:
                code, out = run(['node', 'parity.mjs', f'--routes={route}', f'--widths={widths}'])
            m = re.search(r'(\d+) of (\d+) pass', out)
            record('pixel', code, out, f"pixel+text {m.group(1)}/{m.group(2)}" if m else 'pixel+text ?',
                   [l for l in out.splitlines() if l.startswith(('FAIL', '  ref', '  wp', 'Error'))])
    # DOM.
    if 'dom' not in skip and ref:
        rep = os.path.join(HERE, 'report', 'check')
        os.makedirs(rep, exist_ok=True)
        files = []
        down = []
        for name, host in (('ref', ref), ('wp', wp)):
            html = fetch(host + route)
            if html is None:
                down.append(host)
                continue
            p = os.path.join(rep, f'{name}.html')
            with open(p, 'w', encoding='utf-8') as fh:
                fh.write(html)
            files.append(p)
        if down:
            record('dom', 1, 'not answering: ' + ', '.join(down), 'dom ?', ['dom: not answering: ' + ', '.join(down)])
        else:
            regions = [a.section] if a.section else ['header', 'main', 'footer']
            code, out = run([sys.executable, os.path.join(HERE, 'domdiff.py'), *files, *regions])
            m = re.search(r'(\d+) same, (\d+) differ', out)
            record('dom', code, out, f"dom {'same' if not code else (m.group(2) + ' differ' if m else 'differs')}",
                   [l for l in out.splitlines()[1:]])
    # PHP lint.
    files = list(php_files())
    if 'php' not in skip:
        bad = []
        for f in files:
            code, out = run([a.php, '-l', f])
            if code:
                bad.append(f'php -l: {os.path.relpath(f, THEME_ROOT)}: ' + (out.splitlines() or ['?'])[0][:200])
        record('php', 1 if bad else 0, '\n'.join(bad) or f'{len(files)} files OK', f'php -l {len(files) - len(bad)}/{len(files)}', bad)
    # PHPCS.
    if 'phpcs' not in skip:
        exe = os.path.join(THEME_ROOT, 'vendor', 'bin', 'phpcs' + ('.bat' if os.name == 'nt' else ''))
        if not os.path.exists(exe):
            warn = True
            parts.append('phpcs not installed')
            fails.append('phpcs: run composer install in the theme folder once')
        else:
            code, out = run([exe, '-q', '--report=summary'], cwd=THEME_ROOT)
            m = re.search(r'A TOTAL OF (\d+) ERRORS? AND (\d+) WARNINGS?', out)
            record('phpcs', code, out, 'phpcs clean' if not code else (f'phpcs {m.group(1)} errors {m.group(2)} warnings' if m else 'phpcs fails'),
                   [l.strip() for l in out.splitlines() if re.search(r'\s\d+\s+\d+\s*$|A TOTAL OF', l)][:8])
    # Duplicate global functions.
    if 'dup' not in skip:
        seen, dups = {}, []
        for f in files:
            for n in re.findall(r'(?m)^function\s+&?\s*(\w+)\s*\(', open(f, encoding='utf-8', errors='replace').read()):
                k = n.lower()
                if k in seen:
                    dups.append(f'duplicate function {n}: {os.path.relpath(seen[k], THEME_ROOT)} and {os.path.relpath(f, THEME_ROOT)}')
                seen.setdefault(k, f)
        record('dup', 1 if dups else 0, '\n'.join(dups) or 'none', f'duplicates {len(dups)}', dups)

    os.makedirs(os.path.join(HERE, 'report'), exist_ok=True)
    with open(os.path.join(HERE, 'report', 'check-section.log'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(log))
    status = 'FAIL' if any(not l.startswith('phpcs: run composer') for l in fails) else ('WARN' if warn else 'OK')
    print(f"{status} check-section {route}{' ' + a.section if a.section else ''}: " + ', '.join(parts))
    for l in fails[:20]:
        print('  ' + l[:240])
    if len(fails) > 20:
        print(f'  ... {len(fails) - 20} more in report/check-section.log')
    sys.exit(0 if status == 'OK' else 1)


if __name__ == '__main__':
    main()
