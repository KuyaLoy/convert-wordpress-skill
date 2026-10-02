#!/usr/bin/env python3
"""Download WordPress, verify it, and unpack it into the site folder. Ask the developer before running it
(source wordpress.org, file latest.zip, about 30 MB).

    python3 get-wordpress.py <site folder> [--version 6.9.1] [--locale en_US] [--zip wordpress.zip]

- Downloads https://wordpress.org/latest.zip (or wordpress-<version>.zip) and its .sha1, and checks the SHA-1.
  With --zip it uses a zip you already have (when this shell cannot reach wordpress.org).
- Unpacks into <site folder> without overwriting anything that is already there (planning files stay).
- Checks every core file against the official MD5 list (api.wordpress.org/core/checksums) and reports the counts.
- Sets 0644 on files and 0755 on folders (copies from some mounts keep 0700, which LiteSpeed serves as 403).
Prints no secrets; writes no wp-config.php (make-wp-config.py does that).
"""
import argparse
import hashlib
import io
import json
import os
import sys
import urllib.request
import zipfile

ap = argparse.ArgumentParser()
ap.add_argument('site')
ap.add_argument('--version', default='latest')
ap.add_argument('--locale', default='en_US')
ap.add_argument('--zip')
a = ap.parse_args()

UA = {'User-Agent': 'get-wordpress/1.0'}


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()


name = 'latest.zip' if a.version == 'latest' else f'wordpress-{a.version}.zip'
if a.zip:
    data = open(a.zip, 'rb').read()
    print(f'using {a.zip} ({len(data) / 1e6:.1f} MB); SHA-1 not checked against wordpress.org')
else:
    try:
        data = fetch('https://wordpress.org/' + name)
        sha1 = fetch('https://wordpress.org/' + name + '.sha1').decode().strip().split()[0]
    except Exception as e:  # noqa: BLE001 - report and stop
        print(f'cannot download from wordpress.org here ({e}). Download {name} elsewhere and pass --zip <file>.')
        sys.exit(2)
    got = hashlib.sha1(data).hexdigest()
    print(f'{name}: {len(data) / 1e6:.1f} MB, SHA-1 {"OK" if got == sha1 else "MISMATCH " + got + " != " + sha1}')
    if got != sha1:
        sys.exit(1)

z = zipfile.ZipFile(io.BytesIO(data))
os.makedirs(a.site, exist_ok=True)
written = kept = 0
for info in z.infolist():
    if not info.filename.startswith('wordpress/'):
        continue
    rel = info.filename[len('wordpress/'):]
    if not rel:
        continue
    dest = os.path.join(a.site, *rel.split('/'))
    if info.is_dir():
        os.makedirs(dest, exist_ok=True)
        os.chmod(dest, 0o755)
        continue
    if os.path.exists(dest):
        kept += 1
        continue
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'wb') as fh:
        fh.write(z.read(info))
    os.chmod(dest, 0o644)
    written += 1
print(f'unpacked: {written} files written, {kept} already there (left as they were)')

# Core version and the official checksums.
ver = a.version
vf = os.path.join(a.site, 'wp-includes', 'version.php')
if os.path.exists(vf):
    for line in open(vf, encoding='utf-8'):
        if line.startswith('$wp_version'):
            ver = line.split("'")[1]
try:
    sums = json.loads(fetch(f'https://api.wordpress.org/core/checksums/1.0/?version={ver}&locale={a.locale}'))['checksums']
except Exception as e:  # noqa: BLE001
    print(f'WordPress {ver}: official checksums not reachable here ({e}); check later with wp core verify-checksums')
    sys.exit(0)
bad = [f for f, md5 in sums.items() if not os.path.exists(os.path.join(a.site, f))
       or hashlib.md5(open(os.path.join(a.site, f), 'rb').read()).hexdigest() != md5]
print(f'WordPress {ver}: {len(sums) - len(bad)} of {len(sums)} core files match the official MD5 list'
      + (f'; different or missing: {bad[:10]}' if bad else ''))
sys.exit(1 if bad else 0)
