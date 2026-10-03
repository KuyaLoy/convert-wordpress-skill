#!/usr/bin/env python3
"""Update this skill (convert-to-wordpress) to its newest version on GitHub and show what changed.

    python3 update.py --check          only look: the installed version, the newest one and what is new
    python3 update.py                  update now (the agent asks the developer first: it downloads)
    python3 update.py --add-command    also add /update-convert-wordpress-skill next to this skill (once)

How it updates:
- A git clone (this folder has .git): `git pull --ff-only`. Local edits to the skill's own files stop it and are
  listed (commit or stash them first); nothing is overwritten. profile.local.json and the handoff files are
  git-ignored, so they stay.
- Any other install (a zip, a copy): downloads the release zip from GitHub, first saves a zip of this folder in
  _backups/, then writes the new files. Kept: profile.local.json, handoff.md, ai-handoff-summary.md, PLAN.md,
  _backups/ and any file of your own. Kit files in references/, scripts/ and assets/ that the new version no longer
  has are removed (they are in the backup).
A copy saved inside a Claude app (only SKILL.md) updates by uploading the new version there instead.
Projects keep their own copy of the tools (_plan/tools/ and the theme's kit files). To bring one up to date:
`python3 <this folder>/scripts/new-site.py <wp_root>/_plan/site.json --force` (kit code only, backup first).

The command: --add-command copies assets/update-command/ to <skills folder>/update-convert-wordpress-skill/SKILL.md
(only when this skill sits in a folder named "skills"); later updates keep that copy in step.

Prints one line first: OK|WARN|FAIL update: ...; then at most a few lines of what is new.
Exit 0: up to date or updated. Exit 3 (--check): a newer version exists. Exit 1: failed (nothing changed).
Tests: UPDATE_RAW_BASE and UPDATE_ZIP_BASE point at a local server instead of GitHub.
"""
import argparse
import datetime
import io
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile

REPO = 'KuyaLoy/convert-wordpress-skill'
NAME = 'convert-to-wordpress'
COMMAND = 'update-convert-wordpress-skill'
RAW = os.environ.get('UPDATE_RAW_BASE', f'https://raw.githubusercontent.com/{REPO}/main')
ZIPS = os.environ.get('UPDATE_ZIP_BASE', f'https://github.com/{REPO}/archive/refs')
NOTES = f'https://github.com/{REPO}/blob/main/CHANGELOG.md'
KEEP = {'profile.local.json', 'handoff.md', 'ai-handoff-summary.md', 'PLAN.md'}
KIT_DIRS = ('references/', 'scripts/', 'assets/')
SKIP = {'_backups', '.git', 'node_modules', '__pycache__'}

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def stop(msg):
    print(f'FAIL update: {msg}')
    sys.exit(1)


def read(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return fh.read()
    except OSError:
        return ''


def is_this_skill(skill_md):
    return bool(re.search(rf'^name:\s*"?{NAME}"?\s*$', skill_md, re.M))


def versions(changelog):
    """[(version tuple, 'x.y.z', date, summary)] for every dated release, newest first ("Unreleased" is skipped)."""
    out = []
    for block in re.split(r'^## ', changelog.replace('\r\n', '\n'), flags=re.M)[1:]:
        head, _, body = block.partition('\n')
        m = re.match(r'\[(\d+)\.(\d+)\.(\d+)\]\s*-\s*(\d{4}-\d{2}-\d{2})', head)
        if not m:
            continue
        summary = intro(body.splitlines())
        summary = re.sub(r'\s+', ' ', summary)
        out.append((tuple(int(x) for x in m.groups()[:3]), '.'.join(m.groups()[:3]), m.group(4),
                    summary[:110] + ('...' if len(summary) > 110 else '')))
    return out


def intro(lines):
    """The release's own summary paragraph, else its first item (with the lines that continue it)."""
    text = []
    for line in lines:
        s = line.strip()
        if s.startswith(('#', '- ')) or (not s and text):
            break
        if s:
            text.append(s)
    if text:
        return ' '.join(text)
    for line in lines:
        s = line.strip()
        if s.startswith('- '):
            if text:
                break
            text.append(s[2:])
        elif text and s and line.startswith('  '):
            text.append(s)
        elif text:
            break
    return ' '.join(text)


def installed():
    v = versions(read(os.path.join(HERE, 'CHANGELOG.md')))
    return v[0] if v else None


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={'User-Agent': 'convert-to-wordpress-update'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def whats_new(newest, current):
    newer = [v for v in newest if not current or v[0] > current[0]]
    lines = [f'- {v[1]} ({v[2]}): {v[3]}' for v in newer[:5]]
    if len(newer) > 5:
        lines.append(f'- and {len(newer) - 5} older versions')
    return "What's new:\n" + '\n'.join(lines + [f'Full notes: {NOTES}'])


def add_command(quiet=False):
    """Copy the companion skill /update-convert-wordpress-skill next to this skill. Returns a line to print."""
    src = os.path.join(HERE, 'assets', 'update-command', f'{COMMAND}.md')
    parent = os.path.dirname(HERE)
    if not os.path.isfile(src):
        return 'Command not added: assets/update-command/ is missing in this version'
    if os.path.basename(parent).lower() != 'skills':
        return (f'Command not added: this skill is not inside a skills folder ({parent}). Copy {src} to '
                f'<your skills folder>/{COMMAND}/SKILL.md yourself')
    dest = os.path.join(parent, COMMAND)
    os.makedirs(dest, exist_ok=True)
    shutil.copyfile(src, os.path.join(dest, 'SKILL.md'))
    return None if quiet else f'Command added: {dest} (start a new chat, then type /{COMMAND})'


def git(*args):
    return subprocess.run(['git', '-C', HERE, *args], capture_output=True, text=True)


def update_git():
    if not shutil.which('git'):
        stop('this skill is a git clone and git is not installed here: install git, then run this again')
    dirty = [l[3:] for l in git('status', '--porcelain', '--untracked-files=no').stdout.splitlines() if l.strip()]
    if dirty:
        stop("local edits in the skill's own files, nothing changed: " + ', '.join(dirty[:10]) +
             (' ...' if len(dirty) > 10 else '') + '. Commit or stash them (or copy them aside), then run this again')
    r = git('pull', '--ff-only')
    if r.returncode:
        err = (r.stderr or r.stdout).strip().splitlines()
        stop('git pull did not finish, nothing changed: ' + (err[-1] if err else 'unknown error'))
    return 'git pull'


def check_names(z):
    for zi in z.infolist():
        n = zi.filename
        mode = (zi.external_attr >> 16) & 0o170000
        if n.startswith(('/', '\\')) or re.match(r'^[A-Za-z]:', n) or '..' in re.split(r'[/\\]', n) or mode == 0o120000:
            stop(f'unsafe path in the download, nothing changed: {n}')


def backup(old):
    folder = os.path.join(HERE, '_backups')
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{NAME}-{old}-{datetime.datetime.now():%Y%m%d-%H%M%S}.zip")
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for d, dirs, files in os.walk(HERE):
            dirs[:] = [x for x in dirs if x not in SKIP]
            for f in files:
                full = os.path.join(d, f)
                z.write(full, os.path.relpath(full, HERE))
    return path


def update_zip(version, old):
    data = None
    for ref in (f'tags/v{version}.zip', 'heads/main.zip'):
        try:
            data = fetch(f'{ZIPS}/{ref}', timeout=180)
            break
        except Exception:  # noqa: BLE001 - try the next one
            continue
    if data is None:
        stop('the release zip could not be downloaded from GitHub here; nothing changed')
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        stop('the download is not a valid zip (cut short?); nothing changed')
    with z:
        check_names(z)
        names = [n for n in z.namelist() if not n.endswith('/')]
        tops = {n.split('/')[0] for n in names}
        if len(tops) != 1:
            stop('the download does not look like this skill (no single top folder); nothing changed')
        top = tops.pop() + '/'
        files = {n[len(top):]: n for n in names if n[len(top):]}
        if 'SKILL.md' not in files or not is_this_skill(z.read(files['SKILL.md']).decode('utf-8', 'replace')):
            stop('the download does not look like this skill (no SKILL.md named convert-to-wordpress); nothing changed')
        saved = backup(old)
        for rel, name in files.items():
            if rel in KEEP:
                continue
            dest = os.path.join(HERE, *rel.split('/'))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, 'wb') as fh:
                fh.write(z.read(name))
    removed = 0
    for d, dirs, fs in os.walk(HERE):
        dirs[:] = [x for x in dirs if x not in SKIP]
        for f in fs:
            rel = os.path.relpath(os.path.join(d, f), HERE).replace('\\', '/')
            if rel.startswith(KIT_DIRS) and rel not in files:
                os.remove(os.path.join(d, f))
                removed += 1
    how = f'zip from GitHub; backup {os.path.relpath(saved, HERE)}'
    return how + (f'; {removed} old kit files removed' if removed else '')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true', help='only look, change nothing')
    ap.add_argument('--add-command', action='store_true', help=f'add /{COMMAND} next to this skill')
    a = ap.parse_args()

    if not is_this_skill(read(os.path.join(HERE, 'SKILL.md'))):
        stop(f'run it from the skill folder (scripts/update.py next to the {NAME} SKILL.md), not from a project copy')
    current = installed()
    old = current[1] if current else 'unknown'
    try:
        newest = versions(fetch(f'{RAW}/CHANGELOG.md').decode('utf-8', 'replace'))
    except Exception as e:  # noqa: BLE001 - report and stop
        stop(f'GitHub could not be reached here ({str(e).splitlines()[0][:80]}); nothing changed')
    if not newest:
        stop('the newest version could not be read from GitHub; nothing changed')
    latest = newest[0]
    note = add_command() if a.add_command else None
    has_command = os.path.isdir(os.path.join(os.path.dirname(HERE), COMMAND))

    if current and current[0] >= latest[0]:
        if has_command and not a.check and not a.add_command:
            add_command(quiet=True)  # keep the command in step with this version
        print(f'OK update: {NAME} {old} is the newest version')
    elif a.check:
        print(f'WARN update: {latest[1]} is out (installed: {old}). Run update.py without --check to update.')
        print(whats_new(newest, current))
    else:
        how = update_git() if os.path.exists(os.path.join(HERE, '.git')) else update_zip(latest[1], old)
        if has_command:
            add_command(quiet=True)
        now = installed()
        print(f'OK update: {old} -> {now[1] if now else latest[1]} ({how})')
        print(whats_new(newest, current))
        print('Start a new chat so the agent reads the new version. Projects already started keep their own tools: '
              'new-site.py <wp_root>/_plan/site.json --force refreshes them (kit code only, backup first).')
    if note:
        print(note)
    return 3 if a.check and not (current and current[0] >= latest[0]) else 0


if __name__ == '__main__':
    sys.exit(main())
