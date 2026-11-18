#!/usr/bin/env python3
"""The intake in one call, after doctor.py: the project folder and its handoff files, the working copy of the
source, and the study of that copy.

    python3 scripts/start.py <link | file.zip | folder> --root <wp_root> [--name "Site"] [--env doctor.json]
                             [--into <web folder>] [--branch <name>] [--dry-run]

It runs, in order, and stops at the first that fails (its exit code is passed on):
  1. new-site.py --start <wp_root> --name <Site>       two short handoff files (a closed chat loses nothing)
  2. get-source.py <source> --into <web folder>        the copy <name>-source (the original is never touched);
                                                       skipped when <source> is already such a copy (.source.json)
  3. analyze-source.py <copy> --env <doctor.json> --json <wp_root>/_plan/analyze.json
                              --site-draft <wp_root>/_plan/site.json
     its full output goes to <wp_root>/_plan/analyze.txt; doctor.json is copied to <wp_root>/_plan/doctor.json
     (setup.py reads it after the Plan OK).
<web folder> defaults to the folder that holds <wp_root>. --env defaults to ./doctor.json when it exists.
Then: finish _plan/site.json from the intake answers and run new-site.py <wp_root>/_plan/site.json --plan-only.
Output: line 1 OK|FAIL start: ..., then one line per step. Exit 0 ok, 1 failed, 2 wrong usage, 4 the source is
already a WordPress site.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(args):
    r = subprocess.run([sys.executable] + args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def fail(step, code, out):
    lines = [l for l in out.strip().splitlines() if l.strip()]
    print(f'FAIL start: {step} stopped (exit {code})')
    for l in lines[-12:]:
        print('  ' + l)
    sys.exit(code if code in (2, 4) else 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('source')
    ap.add_argument('--root', required=True, help='the WordPress folder (doctor.py suggests it)')
    ap.add_argument('--name', help='the site name for the handoff files (default: the folder name)')
    ap.add_argument('--env', help="doctor.py's --json file (default: ./doctor.json if it exists)")
    ap.add_argument('--into', help='where the copy goes (default: the folder that holds --root)')
    ap.add_argument('--branch')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    root = os.path.abspath(a.root)
    into = os.path.abspath(a.into or os.path.dirname(root))
    env = a.env or ('doctor.json' if os.path.exists('doctor.json') else None)
    if env and not os.path.exists(env):
        print(f'FAIL start: {env} not found (run doctor.py --json <file> first, or leave --env out)')
        sys.exit(2)
    plan = os.path.join(root, '_plan')
    src_is_copy = os.path.isdir(a.source) and os.path.exists(os.path.join(a.source, '.source.json'))

    if a.dry_run:
        code, out = (0, '') if src_is_copy else run([os.path.join(HERE, 'get-source.py'), a.source, '--into', into,
                                                    '--dry-run'] + (['--branch', a.branch] if a.branch else []))
        if code:
            fail('get-source (dry run)', code, out)
        print('OK start: dry run, nothing written')
        print(f'- folder and handoff files: {root}')
        print('- source copy: ' + (f'{os.path.abspath(a.source)} (already a copy, kept)' if src_is_copy
                                   else out.strip().splitlines()[-1].replace('copy:', '').strip()))
        print(f'- study: {os.path.join(plan, "analyze.json")}, site draft {os.path.join(plan, "site.json")}'
              + (f', doctor {env}' if env else ', no doctor.json (folder and address stay the example)'))
        return

    lines = []
    # 1. Folder and the intake handoff files.
    code, out = run([os.path.join(HERE, 'new-site.py'), '--start', root] + (['--name', a.name] if a.name else []))
    if code:
        fail('new-site --start', code, out)
    lines.append('- handoff files: ' + out.strip().splitlines()[0].replace('OK new-site: intake handoff files ', ''))

    # 2. The working copy.
    if src_is_copy:
        copy = os.path.abspath(a.source)
        try:
            rec = json.load(open(os.path.join(copy, '.source.json'), encoding='utf-8'))
        except (OSError, ValueError):
            rec = {}
        lines.append(f"- source copy: {copy} (already a copy of {rec.get('source', '?')}, kept)")
    else:
        code, out = run([os.path.join(HERE, 'get-source.py'), a.source, '--into', into]
                        + (['--branch', a.branch] if a.branch else []))
        if code:
            fail('get-source', code, out)
        m = re.search(r'^OK get-source: (\S+) -> (.+?) \((.+)\)$', out, re.M)
        if not m:
            fail('get-source', 1, out)
        copy = m.group(2)
        lines.append(f'- source copy: {copy} ({m.group(1)}, {m.group(3)})')
        sec = re.search(r'^Secret or personal files.*$', out, re.M)
        if sec:
            lines.append('- ' + sec.group(0))

    # 3. The study, its full output kept on disk.
    os.makedirs(plan, exist_ok=True)
    if env and os.path.abspath(env) != os.path.abspath(os.path.join(plan, 'doctor.json')):
        shutil.copyfile(env, os.path.join(plan, 'doctor.json'))
    args = [os.path.join(HERE, 'analyze-source.py'), copy, '--json', os.path.join(plan, 'analyze.json'),
            '--site-draft', os.path.join(plan, 'site.json')] + (['--env', env] if env else [])
    code, out = run(args)
    with open(os.path.join(plan, 'analyze.txt'), 'w', encoding='utf-8') as fh:
        fh.write(out)
    if code:
        fail('analyze-source', code, out)
    an = json.load(open(os.path.join(plan, 'analyze.json'), encoding='utf-8'))
    bits = [f"stack {an.get('stack', '?')}", f"starter {an.get('starter_theme', '?')}",
            f"{len(an.get('routes') or [])} routes", f"{len(an.get('forms') or [])} forms",
            'tracking ' + (', '.join(an.get('tracking') or []) or 'none')]
    if an.get('notes'):
        bits.append(f"{len(an['notes'])} notes")
    lines.append('- study: ' + ', '.join(bits) + ' (full output: _plan/analyze.txt)')
    draft = re.search(r'^site draft: .*$', out, re.M)
    if draft:
        lines.append('- ' + draft.group(0).replace(root, '<wp_root>'))

    print(f'OK start: intake ready in {root}')
    print('\n'.join(lines))
    print(f'Next: finish {os.path.join(plan, "site.json")} from the intake answers, then '
          f'new-site.py {os.path.join(plan, "site.json")} --plan-only')


if __name__ == '__main__':
    main()
