#!/usr/bin/env python3
"""The kit's text checks in Python, so they run in any shell (PowerShell, cmd, Git Bash, a Mac or Linux terminal).
Each one runs the same check as the grep line in the docs, prints its hits as file:line:text and ends with one OK or FAIL line.

    python3 text-check.py fill <files>          "[[" left to fill (report.html; the grep -n "\\[\\[" check)
    python3 text-check.py plain <files>         the client pack's plain-English check: "[[", "{{" and em dashes
                                                must be 0 (FAIL); jargon words are listed to read (not a FAIL)
    python3 text-check.py dupes [theme]         duplicate global function names in <theme>/includes/*.php
    python3 text-check.py oneoff [theme]        the self-check searches: one-off values, raw hex, node IDs and
                                                ticket tags, phpcs ignores (each hit fixed or given a reason)
    python3 text-check.py placeholders [dir]    every PLACEHOLDER in the seed (default _setup/seed): client to-dos

Exit 0 OK (or hits to read), 1 hits that must be 0, 2 usage.
"""
import glob
import os
import re
import sys

SKIP_DIRS = {'node_modules', 'vendor', 'tests', 'dist', 'build'}
JARGON = re.compile(r'\bACF\b|\bSCF\b|\bCF7\b|contact form 7|\bDNS\b|cache|plugin|\bPHP\b|database|repeater|'
                    r'field group|_setup|_plan|\.html|password:', re.I)
ONEOFF = [  # (label, extensions, pattern, drop lines containing) as in references/build.md > Self-check
    ('one-off value', ('.php', '.js'), re.compile(r'[a-z]-\[(#|[0-9])'), None),
    ('raw hex', ('.css', '.scss'), re.compile(r'#[0-9a-fA-F]{3,8}\b'), 'tokens'),
    ('node ID or ticket tag', ('.php', '.js'), re.compile(r'[0-9]+:[0-9]+|\b[A-Z][A-Z0-9]+-T[0-9]+\b'), None),
    ('phpcs ignore', ('.php',), re.compile(r'phpcs:ignore|phpcs:disable'), None),
]


def lines(path):
    try:
        with open(path, encoding='utf-8', errors='replace') as fh:
            for n, line in enumerate(fh, 1):
                yield n, line.rstrip('\r\n')
    except OSError as err:
        print(f'FAIL text-check: cannot read {path}: {err.strerror}')
        sys.exit(2)


def walk(root, exts=None):
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        for f in sorted(files):
            if exts is None or f.endswith(exts):
                yield os.path.join(d, f)


def is_text(path):
    try:
        with open(path, 'rb') as fh:
            return b'\0' not in fh.read(4096)
    except OSError:
        return False


def show(path, n, text, base=None):
    rel = os.path.relpath(path, base).replace('\\', '/') if base else path
    print(f'{rel}:{n}:{text}')


def search(files, pattern):
    hits = 0
    for f in files:
        for n, line in lines(f):
            if pattern.search(line):
                show(f, n, line)
                hits += 1
    return hits


def need_files(rest):
    if not rest:
        print(__doc__)
        sys.exit(2)
    return rest


def main(argv):
    if not argv or argv[0] not in ('fill', 'plain', 'dupes', 'oneoff', 'placeholders'):
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == 'fill':
        n = search(need_files(rest), re.compile(r'\[\['))
        print(f'FAIL fill: {n} "[[" left to fill' if n else 'OK fill: nothing left to fill')
        return 1 if n else 0
    if cmd == 'plain':
        files = need_files(rest)
        must = search(files, re.compile(r'\[\[|\{\{|—'))
        print('-- jargon to read (a word stays only if the client sees it on screen or it is explained):')
        words = search(files, JARGON)
        print(f'FAIL plain: {must} "[[", "{{{{" or em dash hits' if must
              else f'OK plain: nothing to fill, no em dashes; {words} jargon hits to read')
        return 1 if must else 0
    root = rest[0] if rest else ('_setup/seed' if cmd == 'placeholders' else '.')
    if not os.path.isdir(root):
        print(f'FAIL text-check: no folder {root}')
        return 2
    if cmd == 'dupes':
        seen, dups = {}, []
        for f in sorted(glob.glob(os.path.join(root, 'includes', '*.php'))):
            for n, line in lines(f):
                m = re.match(r'function\s+&?\s*(\w+)\s*\(', line)
                if m:
                    k = m.group(1).lower()
                    if k in seen:
                        dups.append(f'duplicate function {m.group(1)}: {seen[k]} and '
                                    f'{os.path.relpath(f, root).replace(os.sep, "/")}:{n}')
                    seen.setdefault(k, f'{os.path.relpath(f, root).replace(os.sep, "/")}:{n}')
        print('\n'.join(dups + [f'FAIL dupes: {len(dups)} duplicate functions' if dups
                                else f'OK dupes: {len(seen)} functions, no duplicates']))
        return 1 if dups else 0
    if cmd == 'oneoff':
        total = 0
        for label, exts, pat, drop in ONEOFF:
            for f in walk(root, exts):
                for n, line in lines(f):
                    if pat.search(line) and not (drop and drop in line):
                        show(f, n, f'[{label}] {line.strip()}', root)
                        total += 1
        print(f'OK oneoff: {total} hits; each one fixed or given a one-line reason')
        return 0
    total = 0
    for f in filter(is_text, walk(root)):  # grep -rn: every text file (images and other binaries skipped)
        for n, line in lines(f):
            if 'PLACEHOLDER' in line:
                show(f, n, line.strip(), root)
                total += 1
    print(f'OK placeholders: {total} (each one a client to-do in the report)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
