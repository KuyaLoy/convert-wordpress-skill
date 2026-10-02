#!/usr/bin/env python3
"""The Duplicator package filters for a converted site: paste the output into Duplicator > Packages > New >
Archive > Files > Filters (one textarea: full paths, each ending with ";", one per line, never ";;").

    python3 duplicator-filters.py <WordPress root as Duplicator shows it> <theme folder> [--starter tw] [--check <root here>]

Example: python3 duplicator-filters.py D:/laragon/www/example example
--starter tw: the theme is _tw, so everything in its folder except theme/ (the part WordPress loads) is left out.
--check: the paths are looked up on this machine and missing ones are marked, so you can see what exists.
Left out: planning and handoff files, the seed and setup folders, the debug log, the theme's tests (parity
screenshots can be gigabytes), node_modules, vendor, build configs and dotfiles, readme.html and wp-content/upgrade*.
"""
import os
import sys

args = [x for x in sys.argv[1:]]
check = starter = None
if '--check' in args:
    i = args.index('--check')
    check = args[i + 1] if i + 1 < len(args) else sys.exit('--check needs the WordPress root on this machine')
    del args[i:i + 2]
if '--starter' in args:
    i = args.index('--starter')
    starter = args[i + 1] if i + 1 < len(args) else None
    del args[i:i + 2]
if len(args) < 2 or starter not in (None, 'barebones', 'tw'):
    print(__doc__)
    sys.exit(2)
root = args[0].replace('\\', '/').rstrip('/')
t = f'wp-content/themes/{args[1]}'
paths = [
    '_plan', '_setup', 'BUILD-MAP.md', 'handoff.md', 'ai-handoff-summary.md', 'PLAN.md', 'readme.html',
    'wp-content/debug.log', 'wp-content/upgrade', 'wp-content/upgrade-temp-backup',
]
dev = ['tests', 'node_modules', 'vendor', 'AGENTS.md', 'README.md', 'package.json', 'package-lock.json',
       'composer.json', 'composer.lock', 'phpcs.xml.dist', '.gitignore', '.gitattributes', '.editorconfig']
if starter == 'tw':
    dev += ['tailwind', 'javascript', 'node_scripts', 'tailwind.css', 'tailwind-intellisense.css', 'postcss.config.js',
            'prettier.config.js', 'eslint.config.js', '.npmrc', '.prettierignore', 'LICENSE']
else:
    dev += ['vite.config.js', '.nvmrc']
paths += [f'{t}/{x}' for x in dev]
lines = []
for p in paths:
    note = ''
    if check:
        note = '' if os.path.exists(os.path.join(check, *p.split('/'))) else '   <- not on this machine (harmless, or drop it)'
    lines.append(f'{root}/{p};{note}')
print('\n'.join(lines))
if check:
    print('\nRemove the "<- not on this machine" notes before pasting.')
