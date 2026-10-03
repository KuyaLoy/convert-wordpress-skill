#!/usr/bin/env python3
"""Serve a local WordPress at its own address with PHP's built-in server, for local tools that do not give each
site an address of its own (XAMPP, MAMP, WampServer, a native PHP and MySQL).

    python3 serve-wp.py <wp_root> [--port 8081] [--php <path to php>] [--background]

The site runs at the root of http://localhost:<port>, so every page has the same path as on the golden master and
the 1:1 comparison works (a subfolder such as http://localhost/my-site/ would change every link). No admin rights
and no hosts file change are needed. wp-router.php sends files as they are and every other address to WordPress
(pretty permalinks), and answers 403 for the private project files.

Use the same address in WordPress (install at http://localhost:<port>) and in site.json ("local_host":
"localhost:<port>"). The PHP comes from --php, then doctor.json's suggestion if found next to the project, then PATH.
Foreground: Ctrl+C stops it. --background: starts it detached and writes _setup/serve-wp.pid and serve-wp.log
(stop: kill that PID). macOS and Linux get four PHP workers (PHP_CLI_SERVER_WORKERS), so WordPress can call itself
(Duplicator's build, Site Health). Windows PHP has one: requests wait in turn, so keep Duplicator's Backups page
open while it builds; WordPress's own cron calls would wait too, so the kit's local wp-config has DISABLE_WP_CRON.
"""
import argparse
import json
import os
import shutil
import socket
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUTER = os.path.join(HERE, 'wp-router.php')

ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
ap.add_argument('wp_root')
ap.add_argument('--port', type=int, default=8081)
ap.add_argument('--php')
ap.add_argument('--background', action='store_true')
a = ap.parse_args()

root = os.path.abspath(a.wp_root)
if not os.path.isfile(os.path.join(root, 'index.php')):
    sys.exit(f'FAIL serve-wp: no index.php in {root} (install WordPress there first: get-wordpress.py)')

php = a.php
if not php:
    for cand in (os.path.join(root, '_plan', 'doctor.json'), os.path.join(os.path.dirname(root), 'doctor.json')):
        if os.path.isfile(cand):
            with open(cand, encoding='utf-8') as fh:
                php = ((json.load(fh).get('suggestion') or {}).get('php')) or None
            if php:
                break
php = php or shutil.which('php')
if not php or not (os.path.isfile(php) or shutil.which(php)):
    sys.exit('FAIL serve-wp: PHP not found: give --php <path> (doctor.py shows where your local tool keeps it)')

with socket.socket() as s:
    if s.connect_ex(('127.0.0.1', a.port)) == 0:
        sys.exit(f'FAIL serve-wp: port {a.port} is in use: pick another with --port')

cmd = [php, '-S', f'127.0.0.1:{a.port}', '-t', root, ROUTER]
url = f'http://localhost:{a.port}/'
env = dict(os.environ)
if os.name != 'nt':  # macOS and Linux: four PHP workers, so WordPress can call itself (Duplicator, Site Health)
    env.setdefault('PHP_CLI_SERVER_WORKERS', '4')
if a.background:
    setup = os.path.join(root, '_setup')  # private (the router answers 403), so the PID and log never sit in the web root
    os.makedirs(setup, exist_ok=True)
    log = open(os.path.join(setup, 'serve-wp.log'), 'a')
    kw = {'creationflags': 0x00000008 | 0x00000200} if os.name == 'nt' else {'start_new_session': True}
    p = subprocess.Popen(cmd, stdout=log, stderr=log, stdin=subprocess.DEVNULL, env=env, **kw)
    with open(os.path.join(setup, 'serve-wp.pid'), 'w') as fh:
        fh.write(str(p.pid))
    print(f'OK serve-wp: {url} (PID {p.pid}, stop it with: kill {p.pid}' + (' or taskkill /PID ' + str(p.pid)
          if os.name == 'nt' else '') + ')')
else:
    print(f'OK serve-wp: {url} (Ctrl+C stops it)')
    try:
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        pass
