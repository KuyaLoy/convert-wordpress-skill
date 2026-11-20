#!/usr/bin/env python3
"""The go/no-go check of the developer's plugin folder: for each zip in the profile's plugin_zips, the plugin's
name, Version header and the zip's file date, so the developer can confirm each is the newest before go-live.

    python3 plugin-versions.py --profile <kit>/profile.local.json [--json out.json]

Read only. The developer replaces an old zip in their folder; this script never downloads or changes a zip.
Line 1: OK|FAIL plugin-versions: n zips (FAIL when a zip is missing or has no plugin header). Exit 0 or 1.
"""
import argparse
import datetime
import json
import os
import re
import sys
import zipfile

HEADER = re.compile(rb'^[ \t/*#@]*(Plugin Name|Version):\s*(.+?)\s*$', re.M | re.I)


def plugin_header(path):
    """(name, version) from the main plugin file: a top-level folder's .php file with a Plugin Name header."""
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.endswith('.php') and n.count('/') <= 1]
        for n in sorted(names, key=lambda x: (x.count('/'), len(x))):
            head = z.read(n)[:8192]
            found = {m.group(1).decode().lower(): m.group(2).decode('utf-8', 'replace') for m in HEADER.finditer(head)}
            if 'plugin name' in found:
                return found['plugin name'], found.get('version', '?')
    return None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--profile', required=True)
    ap.add_argument('--json')
    a = ap.parse_args()
    try:
        zips = json.load(open(a.profile, encoding='utf-8')).get('plugin_zips') or {}
    except (OSError, ValueError) as e:
        print(f'FAIL plugin-versions: cannot read {a.profile}: {e}')
        sys.exit(1)
    base = os.path.dirname(os.path.abspath(a.profile))
    rows, bad = [], 0
    for key, path in zips.items():
        if key.startswith('_') or not str(path).strip():
            continue
        full = path if os.path.isabs(path) else os.path.join(base, path)
        row = {'key': key, 'zip': full}
        if not os.path.isfile(full):
            row['problem'] = 'zip not found'
        else:
            row['date'] = datetime.date.fromtimestamp(os.path.getmtime(full)).isoformat()
            try:
                row['name'], row['version'] = plugin_header(full)
            except zipfile.BadZipFile:
                row['problem'] = 'not a zip'
            if not row.get('problem') and not row.get('name'):
                row['problem'] = 'no plugin header in the zip'
        bad += bool(row.get('problem'))
        rows.append(row)
    print(f"{'FAIL' if bad or not rows else 'OK'} plugin-versions: {len(rows)} zips"
          + (f', {bad} with a problem' if bad else '') + ('' if rows else ' (plugin_zips is empty)'))
    for r in rows:
        if r.get('problem'):
            print(f"- {r['key']}: {r['problem']} ({r['zip']})")
        else:
            print(f"- {r['key']}: {r['name']} {r['version']}, file date {r['date']}")
    if a.json:
        json.dump(rows, open(a.json, 'w', encoding='utf-8'), indent=2)
    sys.exit(1 if bad or not rows else 0)


if __name__ == '__main__':
    main()
