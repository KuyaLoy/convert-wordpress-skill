#!/usr/bin/env python3
"""Get the site to convert into a working copy, from whatever the developer gave: a GitHub or other git link, a
zip (a file or a link), a folder, or only the live web address.

    python3 get-source.py <link | file.zip | folder> [<dest>] [--into <folder>] [--branch <name>] [--dry-run]

<dest> defaults to <folder>/<name>-source with --into (use the folder where the WordPress site will live, from
doctor.py), else to <current folder>/<name>-source. The original is never changed: builds and npm install happen in
the copy only (the golden master is the built site, served unchanged).

- GitHub link (also /tree/<branch>/<folder> links): a shallow git clone; without git, the branch zip is downloaded
  (public repositories). Other git hosts: a shallow clone. A private repository uses the developer's own login.
- zip file or zip link: extracted safely (no absolute paths, no "..", no links); a single top folder is unwrapped.
  A zip with a password or a broken zip stops with a plain message.
- folder: copied without node_modules, .git and tool caches (out/ and build/ are kept: they may be the built site).
- live web address (no files at all): capture-site.mjs saves the pages and their files as the golden master. Only
  for a site the developer owns or may rebuild.
The agent asks the developer before any download (this script asks nothing itself).

Writes <dest>/.source.json (what it came from, the commit or the zip's SHA-256, when). Lists files that look like
secrets or personal data (.env, config.php, database dumps, keys, lead files): never read them aloud, copy them
anywhere else or seed them. Tokens in links are never printed or saved.
Exit 0 ok, 1 failed, 2 wrong usage, 4 the source is already a WordPress site (this skill rebuilds other sites).
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile

SKIP = {'node_modules', '.git', '.next', '.cache', '.turbo', '.vercel', '.parcel-cache', '.svelte-kit', '.nuxt'}
SECRET = re.compile(
    r'(^|/)(\.env(\..*)?|env\.php|wp-config\.php|config\.php|secrets?\.\w+|credentials?[\w.-]*\.json|'
    r'service[-_]?account[\w.-]*\.json|\.npmrc|\.htpasswd|auth\.json|[\w.-]*\.(sql|sql\.gz|pem|key|p12|pfx)|'
    r'id_rsa|leads?\.(json|csv)|submissions?\.(json|csv))$', re.I)
GIT_HOSTS = {'github.com', 'gitlab.com', 'bitbucket.org', 'codeberg.org', 'dev.azure.com', 'git.sr.ht'}
HERE = os.path.dirname(os.path.abspath(__file__))


def redact(url):
    """The link without a login or a token in it."""
    p = urllib.parse.urlsplit(url)
    if not p.scheme:
        return url
    host = p.netloc.rsplit('@', 1)[-1]
    query = '' if re.search(r'(?i)token|key|sig|secret|pass', p.query) else p.query
    return urllib.parse.urlunsplit((p.scheme, host, p.path, query, ''))


def classify(src):
    """('github'|'git'|'zip-url'|'website'|'zip'|'folder'|None, details)."""
    if re.match(r'^(git@|ssh://)', src):
        return 'git', {'url': src}
    if re.match(r'^https?://', src, re.I):
        p = urllib.parse.urlsplit(src)
        host = p.netloc.rsplit('@', 1)[-1].lower().split(':')[0]
        parts = [x for x in p.path.split('/') if x]
        if host in ('github.com', 'www.github.com') and len(parts) >= 2:
            name = re.sub(r'\.git$', '', parts[1])
            info = {'owner': parts[0], 'name': name, 'repo': f'https://github.com/{parts[0]}/{name}', 'branch': None,
                    'subdir': None, 'url': src}
            if len(parts) >= 4 and parts[2] in ('tree', 'blob'):
                info['branch'] = parts[3]
                info['subdir'] = '/'.join(parts[4:]) or None
            return 'github', info
        if host in GIT_HOSTS or p.path.endswith('.git'):
            return 'git', {'url': src}
        if p.path.lower().endswith('.zip'):
            return 'zip-url', {'url': src}
        return 'website', {'url': src}
    if os.path.isfile(src) and src.lower().endswith('.zip'):
        return 'zip', {}
    if os.path.isdir(src):
        return 'folder', {}
    return None, {}


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-') or 'site'


def slug_for(kind, src, info=None):
    info = info or classify(src)[1]
    if kind == 'github':
        return slug(info['name'])
    if kind == 'website':
        host = urllib.parse.urlsplit(src).netloc.rsplit('@', 1)[-1].split(':')[0].lower()
        host = re.sub(r'^www\.', '', host)
        return slug(host.rsplit('.', 1)[0] if '.' in host else host)
    base = os.path.basename(urllib.parse.urlsplit(src).path.rstrip('/') if '://' in src else src.rstrip('/\\'))
    return slug(re.sub(r'\.git$|\.zip$', '', base, flags=re.I))


def inside(base, dest):
    """True when dest is inside base. Paths on two different drives are never inside each other."""
    try:
        return os.path.commonpath([os.path.abspath(base), os.path.abspath(dest)]) == os.path.abspath(base)
    except ValueError:
        return False


def is_wordpress(names):
    names = [n.replace('\\', '/').lstrip('./') for n in names]
    top = {re.sub(r'^[^/]+/(?=wp-)', '', n) for n in names}  # also inside a single top folder
    return any(re.search(r'(^|/)wp-includes/version\.php$', n) for n in top) or (
        any(re.search(r'(^|/)wp-config\.php$', n) for n in top) and any('wp-content/' in n for n in top))


def human(n):
    for unit in ('bytes', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            return f'{n:.0f} {unit}' if unit == 'bytes' else f'{n:.1f} {unit}'
        n /= 1024


def folder_size(base):
    total = 0
    for d, dirs, fs in os.walk(base):
        dirs[:] = [x for x in dirs if x not in SKIP]
        total += sum(os.path.getsize(os.path.join(d, f)) for f in fs if os.path.isfile(os.path.join(d, f)))
    return total


def stop(msg, code=1):
    print(f'FAIL get-source: {msg}')
    sys.exit(code)


def wordpress_stop():
    stop('this is already a WordPress site (wp-config.php, wp-includes). This skill rebuilds sites made without '
         'WordPress. For a WordPress redesign or a theme rebuild, say so and the plan is made differently.', 4)


def download(url, target):
    req = urllib.request.Request(url, headers={'User-Agent': 'convert-to-wordpress get-source'})
    try:
        with urllib.request.urlopen(req, timeout=120) as r, open(target, 'wb') as fh:
            shutil.copyfileobj(r, fh)
    except Exception as e:  # noqa: BLE001 (a plain message for every network problem)
        stop(f'download failed ({redact(url)}): {getattr(e, "reason", e)}')


def extract_zip(path, dest):
    """Safe extraction; returns the unwrapped top folder name or None."""
    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        stop('not a valid zip file (it may be cut short or not a zip): download it again')
    with z:
        infos = [zi for zi in z.infolist() if not zi.filename.startswith('__MACOSX/')]
        for zi in infos:
            n = zi.filename
            mode = (zi.external_attr >> 16) & 0o170000
            if n.startswith(('/', '\\')) or re.match(r'^[A-Za-z]:', n) or '..' in re.split(r'[/\\]', n) or mode == 0o120000:
                stop(f'unsafe path in the zip, nothing extracted: {n}')
            if zi.flag_bits & 0x1:
                stop('the zip has a password: unzip it yourself (your zip app asks for the password), then give the '
                     'folder instead')
        if is_wordpress([zi.filename for zi in infos]):
            wordpress_stop()
        os.makedirs(dest, exist_ok=True)
        for zi in infos:
            z.extract(zi, dest)
    names = [zi.filename for zi in infos]
    tops = {re.split(r'[/\\]', n)[0] for n in names if n.strip('/')}
    if len(tops) == 1 and os.path.isdir(os.path.join(dest, next(iter(tops)))):
        inner = os.path.join(dest, next(iter(tops)))
        for item in os.listdir(inner):
            shutil.move(os.path.join(inner, item), os.path.join(dest, item))
        os.rmdir(inner)
        return next(iter(tops))
    return None


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for block in iter(lambda: fh.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def keep_subdir(dest, subdir):
    """Keep only <subdir> of a copied repository, at the top of dest."""
    sub = os.path.join(dest, *subdir.split('/'))
    if not os.path.isdir(sub):
        stop(f'the folder {subdir} is not in the repository')
    tmp = dest + '.part'
    shutil.move(sub, tmp)
    shutil.rmtree(dest)
    shutil.move(tmp, dest)


def git_clone(url, dest, branch):
    if not shutil.which('git'):
        return False
    cmd = ['git', 'clone', '--depth', '1'] + (['--branch', branch] if branch else []) + [url, dest]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        stop("git clone failed (a private repository needs the developer's own git login): "
             + redact((r.stderr or '').strip().splitlines()[-1] if r.stderr else ''))
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('source')
    ap.add_argument('dest', nargs='?')
    ap.add_argument('--into', help='put the copy in this folder as <name>-source')
    ap.add_argument('--branch')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    src = a.source
    kind, info = classify(src)
    if not kind:
        stop(f'not a link, a zip file or a folder: {src}', 2)
    if a.dest and a.into:
        stop('give either a destination or --into, not both', 2)
    name = slug_for(kind, src, info)
    dest = os.path.abspath(a.dest or os.path.join(a.into or os.getcwd(), name + '-source'))
    if os.path.isdir(dest) and os.listdir(dest):
        stop(f'{dest} exists and is not empty: give another folder, or remove it after asking the developer')
    if kind == 'folder' and inside(src, dest):
        stop('the copy cannot go inside the source folder', 2)
    shown_src = redact(src) if '://' in src or src.startswith('git@') else os.path.abspath(src)
    size = (human(os.path.getsize(src)) if kind == 'zip' else human(folder_size(src)) if kind == 'folder'
            else 'size known after the download')
    if a.dry_run:
        print(f'OK get-source: dry run, nothing written\nsource: {shown_src} ({kind}, {size})\ncopy:   {dest}')
        return
    if kind == 'folder':
        names = []
        for d, dirs, fs in os.walk(src):
            dirs[:] = [x for x in dirs if x not in SKIP]
            names += [os.path.relpath(os.path.join(d, f), src) for f in fs]
        if is_wordpress(names):
            wordpress_stop()

    record = {'source': shown_src, 'kind': kind,
              'copied': datetime.datetime.now().astimezone().isoformat(timespec='seconds')}
    if kind in ('git', 'github'):
        branch = a.branch or info.get('branch')
        url = info.get('repo') or info['url']
        if git_clone(url, dest, branch):
            record['commit'] = subprocess.run(['git', '-C', dest, 'rev-parse', 'HEAD'], capture_output=True,
                                              text=True).stdout.strip()
            record['branch'] = branch or subprocess.run(['git', '-C', dest, 'rev-parse', '--abbrev-ref', 'HEAD'],
                                                        capture_output=True, text=True).stdout.strip()
        elif kind == 'github':
            base = os.environ.get('GET_SOURCE_ZIP_BASE', 'https://github.com').rstrip('/')
            ref = branch or 'HEAD'
            zurl = f"{base}/{info['owner']}/{info['name']}/archive/{ref}.zip"
            tmpzip = os.path.join(tempfile.mkdtemp(prefix='get-source-'), 'repo.zip')
            download(zurl, tmpzip)
            record.update(kind='github-zip', branch=ref, sha256=sha256(tmpzip))
            extract_zip(tmpzip, dest)
        else:
            stop('git is not installed: ' + {'win32': 'winget install -e --id Git.Git'}.get(
                sys.platform, 'install git from git-scm.com') + ', or give a zip of the site instead')
        if info.get('subdir'):
            keep_subdir(dest, info['subdir'])
            record['subdir'] = info['subdir']
    elif kind in ('zip', 'zip-url'):
        path = src
        if kind == 'zip-url':
            path = os.path.join(tempfile.mkdtemp(prefix='get-source-'), 'site.zip')
            download(src, path)
        record['sha256'] = sha256(path)
        top = extract_zip(path, dest)
        if top:
            record['unwrapped'] = top
    elif kind == 'folder':
        shutil.copytree(os.path.abspath(src), dest, ignore=lambda d, files: [f for f in files if f in SKIP],
                        dirs_exist_ok=True)
    elif kind == 'website':
        if not shutil.which('node'):
            stop('Node.js is needed to capture a live site: ' + {'win32': 'winget install -e --id OpenJS.NodeJS.LTS'}
                 .get(sys.platform, 'install it from nodejs.org') + ', then run this again')
        r = subprocess.run(['node', os.path.join(HERE, 'capture-site.mjs'), src, dest])
        if r.returncode:
            stop('the capture did not finish (see above)')
        record['kind'] = 'live'

    files = []
    for d, dirs, fs in os.walk(dest):
        dirs[:] = [x for x in dirs if x not in SKIP]
        files += [os.path.relpath(os.path.join(d, f), dest).replace('\\', '/') for f in fs]
    if kind != 'folder' and is_wordpress(files):
        wordpress_stop()
    secrets = sorted(f for f in files if SECRET.search(f) and not f.endswith(('.example', '.sample', '.dist')))
    record['files'] = len(files)
    record['secret_files'] = secrets
    with open(os.path.join(dest, '.source.json'), 'w', encoding='utf-8') as fh:
        json.dump(record, fh, indent=2)
    extra = (f", commit {record['commit'][:12]}" if record.get('commit') else '') + (
        f", sha256 {record['sha256'][:12]}" if record.get('sha256') else '')
    print(f"OK get-source: {record['kind']} -> {dest} ({len(files)} files{extra})")
    if secrets:
        print('Secret or personal files (never read, copy or seed them): ' + ', '.join(secrets[:12])
              + (f' and {len(secrets) - 12} more' if len(secrets) > 12 else ''))
    print(f'Next: python3 {os.path.join(HERE, "analyze-source.py")} "{dest}" --json <wp_root>/_plan/analyze.json '
          f'--site-draft <wp_root>/_plan/site.json')


if __name__ == '__main__':
    main()
