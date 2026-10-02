#!/usr/bin/env python3
"""Get the site to convert into a working copy, from whatever the developer gave: a git URL, a zip, or a folder.

    python3 get-source.py <git URL | file.zip | folder> [<dest>] [--branch <name>] [--dry-run]

<dest> defaults to <www>/<name>-source next to the WordPress folders, where <name> comes from the source (the repo,
zip or folder name) and <www> is the current folder. The original is never changed: builds and npm install happen
in the copy only (the copy is still not the golden master; that is the built site, served unchanged).

- git URL (https://..., git@..., ...git): a shallow clone (--depth 1, optional --branch). Asks nothing itself: the
  agent asks the developer before running it (a download). Private repos use the developer's own git login.
- zip: extracted safely (no absolute paths, no "..", no links); a single top folder is unwrapped.
- folder: copied without node_modules, .git, .next, .cache, dist caches of tools (out/ and build/ are kept: they
  may be the built site).

Writes <dest>/.source.json (what it came from, the commit or the zip's SHA-256, when) and prints the next command:
analyze-source.py on the copy. Lists files that look like secrets or personal data (.env, env.php, lead files):
never read them aloud, copy them anywhere else, or put them in the seed. Refuses a <dest> that exists and is not
empty. Exit 0 ok, 1 failed, 2 wrong usage.
"""
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

SKIP = {'node_modules', '.git', '.next', '.cache', '.turbo', '.vercel', '.parcel-cache', '.svelte-kit', '.nuxt'}
SECRET = re.compile(r'(^|/)(\.env(\..*)?|env\.php|wp-config\.php|secrets?\.\w+|leads?\.(json|csv)|'
                    r'submissions?\.(json|csv)|.*\.pem|.*\.key|id_rsa)$', re.I)

args = [x for x in sys.argv[1:] if not x.startswith('--')]
branch = sys.argv[sys.argv.index('--branch') + 1] if '--branch' in sys.argv else None
if branch in args:
    args.remove(branch)
dry = '--dry-run' in sys.argv
if not args:
    print(__doc__)
    sys.exit(2)
src = args[0]


def slug(s):
    s = re.sub(r'\.git$|\.zip$', '', os.path.basename(s.rstrip('/\\')), flags=re.I)
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-') or 'site'


is_git = bool(re.match(r'^(https?://|git@|ssh://)', src)) or src.endswith('.git')
is_zip = not is_git and src.lower().endswith('.zip') and os.path.isfile(src)
is_dir = not is_git and os.path.isdir(src)
if not (is_git or is_zip or is_dir):
    sys.exit(f'not a git URL, a zip file or a folder: {src}')
dest = os.path.abspath(args[1] if len(args) > 1 else os.path.join(os.getcwd(), slug(src) + '-source'))
if os.path.isdir(dest) and os.listdir(dest):
    sys.exit(f'{dest} exists and is not empty: give another folder, or remove it after asking the developer')
kind = 'git' if is_git else 'zip' if is_zip else 'folder'
print(f'source: {src} ({kind})\ncopy:   {dest}')
if dry:
    print('dry run: nothing written')
    sys.exit(0)

info = {'source': src if is_git else os.path.abspath(src), 'kind': kind,
        'copied': datetime.datetime.now().astimezone().isoformat(timespec='seconds')}
if is_git:
    cmd = ['git', 'clone', '--depth', '1'] + (['--branch', branch] if branch else []) + [src, dest]
    r = subprocess.run(cmd)
    if r.returncode:
        sys.exit('git clone failed (a private repo needs the developer\'s own git login)')
    info['commit'] = subprocess.run(['git', '-C', dest, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    info['branch'] = branch or subprocess.run(['git', '-C', dest, 'rev-parse', '--abbrev-ref', 'HEAD'],
                                              capture_output=True, text=True).stdout.strip()
elif is_zip:
    h = hashlib.sha256()
    with open(src, 'rb') as fh:
        for block in iter(lambda: fh.read(1 << 20), b''):
            h.update(block)
    info['sha256'] = h.hexdigest()
    with zipfile.ZipFile(src) as z:
        names = [n for n in z.namelist() if not n.startswith('__MACOSX/')]
        for zi in z.infolist():
            n = zi.filename
            if n.startswith('__MACOSX/'):
                continue
            mode = (zi.external_attr >> 16) & 0o170000
            if n.startswith(('/', '\\')) or re.match(r'^[A-Za-z]:', n) or '..' in re.split(r'[/\\]', n) or mode == 0o120000:
                sys.exit(f'unsafe path in the zip, nothing more extracted: {n}')
        os.makedirs(dest, exist_ok=True)
        for n in names:
            z.extract(n, dest)
    tops = {re.split(r'[/\\]', n)[0] for n in names if n.strip('/')}
    if len(tops) == 1 and os.path.isdir(os.path.join(dest, next(iter(tops)))):
        inner = os.path.join(dest, next(iter(tops)))
        for item in os.listdir(inner):
            shutil.move(os.path.join(inner, item), os.path.join(dest, item))
        os.rmdir(inner)
        info['unwrapped'] = next(iter(tops))
else:
    base = os.path.abspath(src)
    if os.path.commonpath([base, dest]) == base:
        sys.exit('the copy cannot go inside the source folder')
    shutil.copytree(base, dest, ignore=lambda d, files: [f for f in files if f in SKIP])

files = []
for d, dirs, fs in os.walk(dest):
    dirs[:] = [x for x in dirs if x not in SKIP]
    files += [os.path.relpath(os.path.join(d, f), dest).replace('\\', '/') for f in fs]
secrets = sorted(f for f in files if SECRET.search(f) and not f.endswith(('.example', '.sample', '.dist')))
info['files'] = len(files)
info['secret_files'] = secrets
json.dump(info, open(os.path.join(dest, '.source.json'), 'w', encoding='utf-8'), indent=2)
print(f'{len(files)} files' + (f", commit {info['commit'][:12]}" if info.get('commit') else '')
      + (f", sha256 {info['sha256'][:12]}" if info.get('sha256') else ''))
if secrets:
    print('secret or personal files (never read, copy or seed them): ' + ', '.join(secrets))
here = os.path.dirname(os.path.abspath(__file__))
print(f'next: python3 {os.path.join(here, "analyze-source.py")} "{dest}" --json <wp_root>/_plan/analyze.json '
      f'--site-draft <wp_root>/_plan/site.json')
