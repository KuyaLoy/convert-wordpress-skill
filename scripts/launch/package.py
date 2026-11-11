#!/usr/bin/env python3
"""Build the launch package with Duplicator Pro in one command, with no wp-admin login.

    python3 package.py <WordPress root> <theme folder> [--starter tw|barebones] [--dry-run] [--wp "<command>"]
                       [--password-file <path>] [-v]

It sets the Duplicator Pro template "launch" (the file filters from duplicator-filters.py, installer password on,
installer name with hash), builds the backup with WP-CLI, checks the archive for private files, and copies the
archive and installer to <root>/_setup/launch/upload/. A new installer password goes to a file OUTSIDE the project
(default: the system temp folder). The developer pastes it into the installer, then deletes the file.

--dry-run  shows the filter counts and the steps, builds nothing.
--wp       the WP-CLI command when `wp` is not on PATH, for example --wp "php C:/tools/wp-cli.phar".
-v         lists every filtered path.
Exit codes: 0 ok, 1 usage, 2 Duplicator Pro not active, 3 build failed, 4 private files in the archive.
"""
import argparse
import datetime
import os
import re
import secrets
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
FILTERS = os.path.join(HERE, 'duplicator-filters.py')
HELPER = os.path.join(HERE, 'duplicator-template.php')
PASS_ENV = 'DUP_LAUNCH_INSTALLER_PASS'
# Left out on top of duplicator-filters.py: agent folders and Contact Form 7's temporary uploads.
EXTRA = ['.claude', 'tasks', 'wp-content/uploads/wpcf7_uploads']
PRIVATE_ROOT = {'.claude', 'tasks', '_plan', '_setup', '.git'}
PRIVATE_THEME = {'tests', 'node_modules', '.git'}
PRIVATE_NAMES = {'debug.log', 'handoff.md', 'ai-handoff-summary.md', 'build-map.md'}
DB_DUMP = re.compile(r'^dup-installer/dup_descriptors_[^/]+/db_dumps/[^/]+\.sql$')
WPCONFIG = re.compile(r'^dup-installer/dup_descriptors_[^/]+/orig_files/source_site_wpconfig')
OK, USAGE, NO_DUP, BUILD_FAILED, PRIVATE = 0, 1, 2, 3, 4


class Usage(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Usage(message)


def norm_root(root):
    return os.path.realpath(root).replace('\\', '/').rstrip('/')


def filter_paths(root, theme, starter=None):
    """Full paths to leave out, from duplicator-filters.py plus EXTRA."""
    cmd = [sys.executable, FILTERS, root, theme] + (['--starter', starter] if starter else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise Usage('duplicator-filters.py failed: ' + (r.stderr or r.stdout).strip()[:300])
    paths = [line.strip().rstrip(';') for line in r.stdout.splitlines() if line.strip().endswith(';')]
    for x in EXTRA:
        p = f'{root}/{x}'
        if p not in paths:
            paths.append(p)
    return paths


def split_paths(paths):
    """(folders, files, missing) on this machine. Missing paths are left out of the template (they filter nothing)."""
    dirs, files, missing = [], [], []
    for p in paths:
        if os.path.isdir(p):
            dirs.append(p)
        elif os.path.exists(p):
            files.append(p)
        else:
            missing.append(p)
    return dirs, files, missing


def private_hit(name, theme):
    """True when an archive entry is a private path that must never go live."""
    parts = [x for x in name.replace('\\', '/').split('/') if x]
    if not parts:
        return False
    low = [x.lower() for x in parts]
    if low[0] in PRIVATE_ROOT or low[-1] in PRIVATE_NAMES or 'wpcf7_uploads' in low:
        return True
    return len(parts) > 3 and parts[:3] == ['wp-content', 'themes', theme] and low[3] in PRIVATE_THEME


def check_archive(path, theme):
    """Read the zip's entry list. Returns dict(entries, hits, db, wpconfig). Raises zipfile.BadZipFile."""
    with zipfile.ZipFile(path) as z:
        names = [n.replace('\\', '/').lstrip('/') for n in z.namelist()]
    return {
        'entries': len(names),
        'hits': [n for n in names if private_hit(n, theme)],
        'db': any(DB_DUMP.match(n) for n in names),
        'wpconfig': any(WPCONFIG.match(n) for n in names),
    }


def newest_package(backups, since):
    """(archive, installer) built after `since` in wp-content/duplicator-backups, or (None, None)."""
    if not os.path.isdir(backups):
        return None, None
    zips = [os.path.join(backups, f) for f in os.listdir(backups) if f.endswith('_archive.zip')]
    zips = [z for z in zips if os.path.getmtime(z) >= since]
    if not zips:
        return None, None
    archive = max(zips, key=os.path.getmtime)
    installer = archive[:-len('_archive.zip')] + '_installer.php.bak'
    return archive, (installer if os.path.isfile(installer) else None)


def outside(path, root):
    p = os.path.normcase(os.path.realpath(path))
    r = os.path.normcase(os.path.realpath(root))
    try:
        return os.path.commonpath([p, r]) != r
    except ValueError:  # another drive on Windows
        return True


def size_text(n):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            return f'{n:.0f} {unit}' if unit == 'B' else f'{n:.1f} {unit}'
        n /= 1024.0


def wp_command(arg):
    if arg:
        return shlex.split(arg)
    found = shutil.which('wp')
    return [found] if found else None


def run_wp(wp, root, args, env=None, timeout=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run(wp + [f'--path={root}'] + args, capture_output=True, text=True, env=e, timeout=timeout,
                          errors='replace')


def write_password(path, site, password):
    note = (f'Duplicator installer password for {site}, made {datetime.date.today().isoformat()}.\n'
            'Paste it into the installer when it asks, then delete this file.\n'
            'Never put it in chat, notes, tickets or the project.\n\n'
            f'{password}\n')
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as fh:
        fh.write(note)


def tail(text, n=20):
    return '\n'.join(text.strip().splitlines()[-n:])


def main(argv=None):
    ap = Parser(add_help=True, description='Build the launch package with Duplicator Pro.')
    ap.add_argument('root')
    ap.add_argument('theme')
    ap.add_argument('--starter', choices=('tw', 'barebones'))
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--wp')
    ap.add_argument('--password-file')
    ap.add_argument('-v', action='store_true')
    try:
        a = ap.parse_args(argv)
        if not os.path.isfile(os.path.join(a.root, 'wp-load.php')):
            raise Usage(f'{a.root} is not a WordPress root (no wp-load.php)')
        root = norm_root(a.root)
        if not os.path.isdir(os.path.join(root, 'wp-content', 'themes', a.theme)):
            raise Usage(f'no theme folder wp-content/themes/{a.theme}')
        site = os.path.basename(root)
        pass_file = a.password_file or os.path.join(os.path.realpath(tempfile.gettempdir()), f'{site}-installer-password.txt')
        if not outside(pass_file, root):
            raise Usage('the password file must be outside the project')
        paths = filter_paths(root, a.theme, a.starter)
    except Usage as e:
        print(f'FAIL package: {e}\n{ap.format_usage().strip()}')
        return USAGE
    dirs, files, missing = split_paths(paths)
    upload = f'{root}/_setup/launch/upload'
    wp = wp_command(a.wp)

    if a.dry_run:
        active = 'unknown (WP-CLI not found)'
        if wp:
            try:
                ok = run_wp(wp, root, ['plugin', 'is-active', 'duplicator-pro']).returncode == 0
                active = 'active' if ok else 'NOT active'
            except OSError:
                active = 'unknown (WP-CLI did not start)'
        print(f'OK package: dry run, {len(dirs)} folders and {len(files)} files to leave out '
              f'({len(missing)} listed paths not on this machine); Duplicator Pro {active}')
        print('Would: save the Duplicator Pro template "launch" (filters on, installer password on, '
              'installer name with hash)')
        print(f'Would: write a new installer password to {pass_file}')
        print('Would: run wp duplicator build --template=<id> --phpzip')
        print(f'Would: check the archive, then copy it and the installer to {upload}')
        if a.v:
            print('\n'.join([f'folder  {p}' for p in dirs] + [f'file    {p}' for p in files]
                            + [f'missing {p}' for p in missing]))
        return NO_DUP if active == 'NOT active' else OK

    if not wp:
        print('FAIL package: WP-CLI not found. Put `wp` on PATH or pass --wp "php <path>/wp-cli.phar".')
        return USAGE
    try:
        active = run_wp(wp, root, ['plugin', 'is-active', 'duplicator-pro']).returncode == 0
    except OSError as e:
        print(f'FAIL package: WP-CLI did not start ({e})')
        return USAGE
    if not active:
        print('FAIL package: Duplicator Pro is not active on this site (wp plugin is-active duplicator-pro).')
        return NO_DUP

    # 1. Template "launch" with a fresh installer password. The password never reaches the screen.
    password = secrets.token_urlsafe(18)
    write_password(pass_file, site, password)
    fd, list_file = tempfile.mkstemp(suffix='.txt', prefix='dup-filters-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(dirs + files) + '\n')
        r = run_wp(wp, root, ['eval-file', HELPER, root, list_file], env={PASS_ENV: password})
    finally:
        os.remove(list_file)
        password = None
    m = re.search(r'template=(\d+) dirs=(\d+) files=(\d+)', r.stdout)
    if r.returncode != 0 or not m:
        print(f'FAIL package: could not save the template "launch" (exit {r.returncode})')
        print(tail(r.stderr + '\n' + r.stdout))
        return NO_DUP if r.returncode == NO_DUP else BUILD_FAILED
    tid = m.group(1)

    # 2. Build.
    log = f'{root}/_setup/launch/package-build.log'
    os.makedirs(os.path.dirname(log), exist_ok=True)
    start = time.time() - 2
    r = run_wp(wp, root, ['duplicator', 'build', f'--template={tid}', '--phpzip'])
    with open(log, 'w', encoding='utf-8') as fh:
        fh.write(r.stdout + '\n' + r.stderr)
    archive, installer = newest_package(f'{root}/wp-content/duplicator-backups', start)
    if r.returncode != 0 or not archive or not installer:
        print(f'FAIL package: the build failed (exit {r.returncode}); log: {log}')
        print(tail(r.stderr + '\n' + r.stdout))
        return BUILD_FAILED

    # 3. Check before anything is copied.
    try:
        c = check_archive(archive, a.theme)
    except zipfile.BadZipFile:
        print(f'FAIL package: {os.path.basename(archive)} is not a readable zip')
        return BUILD_FAILED
    if c['hits']:
        print(f'FAIL package: {len(c["hits"])} private entries in {os.path.basename(archive)}; nothing copied')
        print('\n'.join(c['hits'][:20]))
        return PRIVATE
    if not c['db'] or not c['wpconfig']:
        lack = ' and '.join(x for x, ok in (('the database dump', c['db']), ('source_site_wpconfig', c['wpconfig']))
                            if not ok)
        print(f'FAIL package: {os.path.basename(archive)} has no {lack}')
        return BUILD_FAILED

    # 4. Copy to _setup/launch/upload/, the installer without .bak.
    os.makedirs(upload, exist_ok=True)
    inst_name = os.path.basename(installer)[:-len('.bak')]
    shutil.copy2(archive, os.path.join(upload, os.path.basename(archive)))
    shutil.copy2(installer, os.path.join(upload, inst_name))
    print(f'OK package: {os.path.basename(archive)} ({size_text(os.path.getsize(archive))}), installer {inst_name}, '
          f'{c["entries"]} entries, 0 private')
    print(f'Copied to: {upload}')
    print(f'Installer password: in {pass_file} (paste it into the installer, then delete the file)')
    print('Next: upload both files to the live docroot and run the installer (references/launch.md, The move).')
    return OK


if __name__ == '__main__':
    sys.exit(main())
