#!/usr/bin/env python3
"""The plugin check: the site's plugins against the kit's list for its environment (local, staging or live).

    python3 plugin-check.py <wp_root>/_plan/site.json --env live --list plugins.json
                            [--profile <kit>/profile.local.json] [--files files.txt] [--done] [-v]
    python3 plugin-check.py <wp_root>/_plan/site.json --env live --profile <kit>/profile.local.json --expected

--list: what the site has, from `wp plugin list --format=json --fields=name,status,title` (or --format=csv, or one
plugin per line: its slug or its name as the Plugins screen shows it, optionally followed by its status). "-" reads
the paste from stdin. Must-use plugins and drop-ins are not counted.
--files (live): a listing of public_html and wp-content (`ls -a ~/public_html ~/public_html/wp-content`); flags the
migration leftovers (installer.php, installer-backup.php, *_installer.php, dup-installer*, *_archive.zip|.daf).
--done (live, after live QA reaches 0 and the report is done): Duplicator (Pro) must be deleted, not only
deactivated, and its backups folder (backups-dup-pro, backups-dup-lite, duplicator-backups) gone.
--expected: print the planned list for the environment and exit.

The list (the task wins: site.json "task_plugins" adds what the task asks for; site.json "cache_plugin": "none" when
the host caches by itself):
  every environment   ACF PRO (or Secure Custom Fields), Contact Form 7, Yoast SEO
  if redirects        Redirection (site.json "redirects" true or a 301 row in _plan/OLD-SITE-URLS.md): required on
                      live, allowed on local and staging; without redirects it is not on the list
  live only           Contact Form CFDB7, Converter for Media, the cache plugin (LiteSpeed Cache unless the profile or
                      site.json "cache_plugin" names another), the profile's extra_plugins with "where": "live"
  per profile entry   extra_plugins "where": "all" (or "required" without "where"): every environment
  the move            Duplicator or Duplicator Pro: allowed until --done on live
Each FAIL line: missing, inactive, not on the list, live only (on staging or local), or a leftover. Line 1 is
"OK|FAIL plugin-check: ..."; exit 0 when the site matches, 1 when it does not, 2 on a usage error.
"""
import argparse
import csv
import io
import json
import os
import re
import sys

CORE = [('ACF PRO', ['advanced-custom-fields-pro', 'secure-custom-fields']),
        ('Contact Form 7', ['contact-form-7']), ('Yoast SEO', ['wordpress-seo'])]
LIVE_ONLY = [('Contact Form CFDB7', ['contact-form-cfdb7']), ('Converter for Media', ['webp-converter-for-media'])]
CACHE_SLUGS = {'litespeed cache': 'litespeed-cache', 'wp rocket': 'wp-rocket', 'w3 total cache': 'w3-total-cache',
               'wp super cache': 'wp-super-cache', 'wp fastest cache': 'wp-fastest-cache',
               'breeze': 'breeze', 'sg optimizer': 'sg-cachepress', 'speed optimizer': 'sg-cachepress'}
DUPLICATOR = ['duplicator-pro', 'duplicator']
LEFTOVER = re.compile(r'^(installer(-backup)?\.php|.+_installer\.php(\.bak)?|dup-installer.*|'
                      r'.+_archive\.(zip|daf))$', re.I)
BACKUPS = re.compile(r'^(backups-dup-(pro|lite)|duplicator-backups)$', re.I)
SKIP_STATUS = ('must-use', 'dropin')


def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', str(text).lower()).strip('-')


def where(entry):
    """Where a profile plugin goes: 'all', 'live' or '' (only when the task asks)."""
    w = str(entry.get('where') or '').lower()
    if w in ('all', 'live'):
        return w
    return 'all' if entry.get('required') else 'live' if entry.get('live') else ''


def must(entry):
    """A profile plugin that has to be there (installed and active) wherever it goes."""
    return bool(entry.get('required') or entry.get('live'))


def redirects_planned(site, site_json):
    if site.get('redirects') is True:
        return True
    doc = os.path.join(os.path.dirname(os.path.abspath(site_json)), 'OLD-SITE-URLS.md')
    if site.get('redirects') is False or not os.path.exists(doc):
        return False
    with open(doc, encoding='utf-8') as fh:
        return bool(re.search(r'^\|\s*(?:/|https?://)[^|]*\|[^|]*\b301\b', fh.read(), re.M))


def expected(site, profile, env, site_json):
    """[{name, slugs, need}] for the environment; need is 'required', 'allowed' or 'elsewhere' (live only)."""
    out = [{'name': n, 'slugs': s, 'need': 'required'} for n, s in CORE]
    redirects = redirects_planned(site, site_json)
    if redirects:
        need = 'required' if env == 'live' else 'allowed'
        out.append({'name': 'Redirection', 'slugs': ['redirection'], 'need': need})
    live_need = 'required' if env == 'live' else 'elsewhere'
    out += [{'name': n, 'slugs': s, 'need': live_need} for n, s in LIVE_ONLY]
    cache = str(site.get('cache_plugin') or profile.get('cache_plugin') or 'LiteSpeed Cache').strip()
    if cache.lower() != 'none':
        out.append({'name': cache, 'slugs': [CACHE_SLUGS.get(cache.lower(), slug(cache))], 'need': live_need})
    for p in [x for x in profile.get('extra_plugins', []) if isinstance(x, dict) and x.get('name')]:
        w = where(p)
        slugs = [p['slug']] if p.get('slug') else [slug(p['name'])]
        if w == 'all' or (w == 'live' and env == 'live'):
            out.append({'name': p['name'], 'slugs': slugs, 'need': 'required' if must(p) else 'allowed'})
        elif w == 'live':
            out.append({'name': p['name'], 'slugs': slugs, 'need': 'elsewhere'})
        else:
            out.append({'name': p['name'], 'slugs': slugs, 'need': 'allowed'})
    for t in site.get('task_plugins') or []:
        t = {'name': t, 'slug': slug(t)} if isinstance(t, str) else t
        if isinstance(t, dict) and (t.get('slug') or t.get('name')):
            w = str(t.get('where') or 'all').lower()
            need = 'required' if w == 'all' or env == 'live' else 'elsewhere'
            out.append({'name': t.get('name') or t['slug'], 'slugs': [t.get('slug') or slug(t['name'])], 'need': need})
    out.append({'name': 'Duplicator (Pro)', 'slugs': DUPLICATOR, 'need': 'allowed'})
    return out


def read_list(text):
    """[{name, status, title}] from wp plugin list JSON or CSV, or one plugin per line."""
    text = text.strip()
    if text.startswith('['):
        rows = json.loads(text)
    elif re.match(r'^name\s*,', text):
        rows = list(csv.DictReader(io.StringIO(text)))
    else:
        rows = []
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            m = re.match(r'^(.*?)[\s,|]+(active-network|active|inactive|must-use|dropin)$', line, re.I)
            name, status = (m.group(1).strip(), m.group(2).lower()) if m else (line, 'active')
            rows.append({'name': name if re.fullmatch(r'[a-z0-9._-]+', name) else slug(name), 'status': status,
                         'title': name})
    return [{'name': str(r.get('name', '')).strip(), 'status': str(r.get('status', 'active')).strip().lower(),
             'title': str(r.get('title', '') or '').strip()} for r in rows if isinstance(r, dict) and r.get('name')]


def matches(item, row):
    return row['name'] in item['slugs'] or slug(row['name']) == slug(item['name']) or (
        row['title'] and slug(row['title']) == slug(item['name']))


def check(items, rows, env, done):
    problems, seen = [], set()
    rows = [r for r in rows if r['status'] not in SKIP_STATUS]
    for item in items:
        hits = [r for r in rows if matches(item, r)]
        seen.update(id(r) for r in hits)
        active = any(r['status'].startswith('active') for r in hits)
        if item['name'] == 'Duplicator (Pro)':
            if done and env == 'live' and hits:
                problems.append(f"Duplicator still installed ({', '.join(r['name'] for r in hits)}): live QA is at "
                                '0, so deactivate and delete it, its backups first (Duplicator > Backups)')
            continue
        if len({r['name'] for r in hits if r['name'] in item['slugs']}) > 1 and item['name'] == 'ACF PRO':
            problems.append('ACF PRO and Secure Custom Fields are both installed: keep one (ACF PRO)')
        if item['need'] == 'elsewhere' and hits:
            problems.append(f"live only: {item['name']} is on {env}: remove it (it goes on live at launch)")
        elif item['need'] == 'required' and not hits:
            problems.append(f"missing: {item['name']} ({item['slugs'][0]})")
        elif item['need'] == 'required' and not active:
            problems.append(f"inactive: {item['name']}: activate it")
    for r in rows:
        if id(r) not in seen:
            problems.append(f"not on the list: {r['name']} ({r['status']}): delete it, or add it to site.json "
                            '"task_plugins" when the task asks for it')
    return problems


def leftovers(text, done):
    out = []
    for line in text.splitlines():
        name = (line.split()[-1] if line.split() else '').rstrip('/').split('/')[-1]
        if LEFTOVER.match(name):
            out.append(f'leftover: {name}: delete it (anyone could download it)')
        elif done and BACKUPS.match(name):
            out.append(f'leftover: {name}: the Duplicator backups folder, delete it')
    return sorted(set(out))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('site_json')
    ap.add_argument('--env', choices=['local', 'staging', 'live'], required=True)
    ap.add_argument('--list', default='', help='wp plugin list output (JSON, CSV or lines), - for stdin')
    ap.add_argument('--profile', default='', help="the kit's profile.local.json (extra_plugins, cache_plugin)")
    ap.add_argument('--files', default='', help='live: a listing of public_html and wp-content')
    ap.add_argument('--done', action='store_true', help='live QA is at 0: Duplicator must be gone')
    ap.add_argument('--expected', action='store_true', help='print the planned list and exit')
    ap.add_argument('-v', '--verbose', action='store_true')
    a = ap.parse_args(argv)
    try:
        with open(a.site_json, encoding='utf-8') as fh:
            site = json.load(fh)
        profile = {}
        if a.profile:
            with open(a.profile, encoding='utf-8') as fh:
                profile = json.load(fh)
    except (OSError, ValueError) as e:
        print(f'FAIL plugin-check: cannot read {e}')
        return 2
    items = expected(site, profile, a.env, a.site_json)
    if a.expected:
        req = [i['name'] for i in items if i['need'] == 'required']
        print(f"OK plugin-check: {a.env} needs {len(req)}: {', '.join(req)}")
        for i in items:
            if i['need'] != 'required':
                print(f"  {i['need']}: {i['name']}" + (' (not here: live only)' if i['need'] == 'elsewhere' else ''))
        return 0
    if not a.list:
        print('FAIL plugin-check: --list is missing (wp plugin list --format=json --fields=name,status,title)')
        return 2
    try:
        if a.list == '-':
            text = sys.stdin.read()
        else:
            with open(a.list, encoding='utf-8-sig') as fh:
                text = fh.read()
        rows = read_list(text)
    except (OSError, ValueError, csv.Error) as e:
        print(f'FAIL plugin-check: cannot read the plugin list ({e})')
        return 2
    problems = check(items, rows, a.env, a.done)
    if a.files and a.env == 'live':
        try:
            with open(a.files, encoding='utf-8-sig') as fh:
                problems += leftovers(fh.read(), a.done)
        except OSError as e:
            print(f'FAIL plugin-check: cannot read {a.files} ({e})')
            return 2
    counted = len([r for r in rows if r['status'] not in SKIP_STATUS])
    if problems:
        print(f'FAIL plugin-check: {a.env}, {len(problems)} not as planned ({counted} plugins)')
        for p in problems[:20] if not a.verbose else problems:
            print('  ' + p)
        return 1
    tail = ', Duplicator gone' if a.done and a.env == 'live' else ''
    print(f'OK plugin-check: {a.env}, {counted} plugins as planned{tail}')
    if a.verbose:
        for r in rows:
            print(f"  {r['name']} ({r['status']})")
    return 0


if __name__ == '__main__':
    sys.exit(main())
