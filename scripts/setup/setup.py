#!/usr/bin/env python3
"""P1-01 in one call, after the Plan OK: the local database, WordPress, wp-config, the server (when needed) and
install-wp.py, for a LOCAL site only.

    python3 _plan/tools/setup/setup.py <wp_root>/_plan/site.json --profile <kit>/profile.local.json
                                       [--doctor <wp_root>/_plan/doctor.json] [--db db_<site>] [--php <php>]
                                       [--port 8081] [--fields acf|scf] [--zip wordpress.zip] [--dry-run]

Reads site.json (wp_root, local_host, site_name, timezone, wordpress, serve) and doctor.json (the database host,
port and user of the local app; its PHP). Then, stopping at the first step that fails:
  1. database (wordpress "download" only): CREATE DATABASE IF NOT EXISTS <db> (utf8mb4_unicode_520_ci) on the
     local database host; never drops or empties anything. Default name db_<site_dir>. A password only from the
     DB_PASSWORD environment variable (the developer sets it), else the app's documented default from doctor.json.
  2. get-wordpress.py: download with checksums (never overwrites), or --verify when WordPress is already there.
  3. make-wp-config.py: --db <db> for a new wp-config.php, --existing for one a local app made (skipped when the kit
     block is already in it); --no-cron with serve-wp.
  4. serve-wp.py --background when site.json says serve "serve-wp" and nothing answers on the port yet.
  5. install-wp.py --url http://<local_host> --title <site_name> --profile ...: the default local admin, settings,
     Contact Form 7, Yoast SEO and ACF PRO (or SCF with --fields scf).
Output: line 1 OK|WARN|FAIL setup: ..., then one line per step (install-wp's own lines follow). Exit 0 all done;
1 done with open items (install-wp's: no ACF PRO zip, no local password...) or a step failed; 2 refused (not
local, wrong usage).
"""
import argparse
import json
import os
import re
import socket
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL_DB = re.compile(r'^(localhost|127\.0\.0\.1|::1|\[::1\])$', re.I)
LOCAL_URL = re.compile(r'^(localhost|127\.0\.0\.1|\[::1\]|[a-z0-9.-]+\.(test|localhost|local))(:\d+)?$', re.I)

DB_PHP = r'''<?php
mysqli_report( MYSQLI_REPORT_OFF );
$n = getenv( 'KITWP_DB_NAME' );
$m = @new mysqli( getenv( 'KITWP_DB_HOST' ), getenv( 'KITWP_DB_USER' ), (string) getenv( 'DB_PASSWORD' ), '', (int) getenv( 'KITWP_DB_PORT' ) );
if ( $m->connect_errno ) { echo 'connect: ' . $m->connect_error; exit( 3 ); }
$r = $m->query( "SHOW DATABASES LIKE '" . $m->real_escape_string( $n ) . "'" );
if ( $r && $r->num_rows ) { echo 'exists'; exit( 0 ); }
if ( ! $m->query( 'CREATE DATABASE IF NOT EXISTS `' . $n . '` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci' ) ) { echo 'create: ' . $m->error; exit( 4 ); }
echo 'created';
'''


def refuse(msg):
    print('FAIL setup: refused: ' + msg)
    sys.exit(2)


def run(args, env=None, php=None):
    cmd = ([php] if php else [sys.executable]) + args
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
    return r.returncode, ((r.stdout or '') + (r.stderr or '')).strip()


def port_open(port):
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('site_json')
    ap.add_argument('--profile', help="the kit's profile.local.json (local_admin, plugin_zips)")
    ap.add_argument('--doctor', help='doctor.json (default: _plan/doctor.json next to site.json)')
    ap.add_argument('--db', help='database name (default db_<site_dir>)')
    ap.add_argument('--php')
    ap.add_argument('--port', type=int, help='serve-wp port (default: from local_host, else 8081)')
    ap.add_argument('--fields', choices=['acf', 'scf'], default='acf')
    ap.add_argument('--zip', help='a WordPress zip downloaded elsewhere (no network here)')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    try:
        site = json.load(open(a.site_json, encoding='utf-8'))
    except (OSError, ValueError) as e:
        refuse(f'cannot read {a.site_json}: {e}')
    root = os.path.abspath(site.get('wp_root') or '')
    host = re.sub(r'^https?://', '', str(site.get('local_host') or '')).rstrip('/')
    if not site.get('wp_root') or not host:
        refuse('site.json needs wp_root and local_host (the intake fills them)')
    if not LOCAL_URL.match(host):
        refuse(f'{host} is not a local address: setup.py is for local sites only')
    url = 'http://' + host
    doctor_path = a.doctor or os.path.join(os.path.dirname(os.path.abspath(a.site_json)), 'doctor.json')
    sug = {}
    if os.path.isfile(doctor_path):
        try:
            sug = (json.load(open(doctor_path, encoding='utf-8')).get('suggestion') or {})
        except (OSError, ValueError) as e:
            refuse(f'cannot read {doctor_path}: {e}')
    how = site.get('wordpress') or sug.get('wordpress') or 'download'
    serve = site.get('serve') or sug.get('serve') or ''
    php = a.php or sug.get('php') or 'php'
    dbc = sug.get('db') or {}
    db_host = str(dbc.get('host') or '127.0.0.1')
    db_port = int(dbc.get('port') or 3306)
    db_user = str(dbc.get('user') or 'root')
    env = dict(os.environ)
    if 'DB_PASSWORD' not in env:  # the local app's documented default (Laragon, XAMPP: none; MAMP, Local: root)
        default = str(dbc.get('password') or '')
        env['DB_PASSWORD'] = '' if default in ('', 'empty', 'none') else default
    site_dir = site.get('site_dir') or os.path.basename(root)
    db = a.db or site.get('db') or 'db_' + re.sub(r'[^a-z0-9_]', '_', site_dir.lower())
    # The name goes into CREATE DATABASE `<db>`: this pattern is what keeps that statement safe.
    if not re.fullmatch(r'[A-Za-z0-9_]{1,64}', db):
        refuse('database name: letters, digits and _ only')
    m = re.search(r':(\d+)$', host)
    port = a.port or (int(m.group(1)) if m else 8081)
    has_wp = os.path.isfile(os.path.join(root, 'wp-includes', 'version.php'))
    cfg = os.path.join(root, 'wp-config.php')
    cfg_text = open(cfg, encoding='utf-8', errors='replace').read() if os.path.isfile(cfg) else ''
    has_kit = '/* kit:settings start */' in cfg_text
    # The profile's ACF PRO key (never read aloud) goes into a kit block that only has the commented line: run again.
    key_in_profile = False
    if a.profile:
        try:
            key_in_profile = bool(str(json.load(open(a.profile, encoding='utf-8')).get('acf_pro_license') or '').strip())
        except (OSError, ValueError):
            key_in_profile = False
    add_key = has_kit and key_in_profile and not re.search(r"^\s*define\(\s*['\"]ACF_PRO_LICENSE", cfg_text, re.M)
    if add_key:
        has_kit = False
    # A new wp-config.php needs its database; an existing one (a local app's, or a rerun) already has one.
    need_db = not os.path.isfile(cfg)
    if need_db and not LOCAL_DB.match(db_host):
        refuse(f'database host {db_host} is not local')

    steps = []
    if need_db:
        steps.append(('database', f'{db} on {db_host}:{db_port} as {db_user} (created if missing)'))
    steps.append(('wordpress', 'verify the existing core' if has_wp else 'download with checksums into ' + root))
    steps.append(('wp-config', 'kit block already there (kept)' if has_kit else
                  ('--existing' if os.path.isfile(cfg) else f'new, database {db}') + (', --no-cron' if serve == 'serve-wp' else '')
                  + (', the ACF PRO licence from the profile' if key_in_profile and not has_kit else '')))
    if serve == 'serve-wp':
        steps.append(('server', f'serve-wp.py on port {port}' + (' (already answering)' if port_open(port) else '')))
    steps.append(('install', f'install-wp.py {url} ({a.fields})'))
    if a.dry_run:
        print(f'OK setup: dry run, nothing written; {len(steps)} steps for {url}')
        for k, v in steps:
            print(f'- {k}: {v}')
        return

    lines, code = [], 0

    def stop(step, rc, out):
        print(f'FAIL setup: {step} stopped (exit {rc}); done before it: ' + (', '.join(l.split(':')[0][2:] for l in lines) or 'nothing'))
        for l in lines:
            print(l)
        for l in out.splitlines()[-12:]:
            print('  ' + l)
        sys.exit(2 if rc == 2 else 1)

    # 1. Database.
    if need_db:
        env_db = dict(env, KITWP_DB_NAME=db, KITWP_DB_HOST=db_host, KITWP_DB_USER=db_user, KITWP_DB_PORT=str(db_port))
        rc, out = run(['-r', DB_PHP.replace('<?php', '', 1)], env=env_db, php=php)
        if rc:
            stop('database', rc, out + '\n(start the local app\'s MySQL, or set DB_PASSWORD in your own shell)')
        lines.append(f'- database: {db} {out.splitlines()[-1] if out else "?"}')
    # 2. WordPress.
    args = [os.path.join(HERE, 'get-wordpress.py'), root] + (['--verify'] if has_wp else []) + (
        ['--zip', a.zip] if a.zip and not has_wp else [])
    rc, out = run(args)
    if rc:
        stop('get-wordpress', rc, out)
    lines.append('- wordpress: ' + (out.splitlines()[-1] if out else 'ok'))
    # 3. wp-config.
    if has_kit:
        lines.append('- wp-config: kit block already there (kept)')
    else:
        db_arg = ['--host', 'localhost' if db_port == 3306 else f'127.0.0.1:{db_port}', '--user', db_user]
        args = [os.path.join(HERE, 'make-wp-config.py'), root] + (
            ['--existing'] if os.path.isfile(cfg) else ['--db', db] + db_arg) + (['--no-cron'] if serve == 'serve-wp' else [])
        if a.profile:
            args += ['--profile', a.profile]
        rc, out = run(args, env=env)
        if rc:
            stop('make-wp-config', rc, out)
        lines.append('- wp-config: ' + out.splitlines()[0].replace('OK make-wp-config: ', ''))
    # 4. The server.
    if serve == 'serve-wp':
        if port_open(port):
            lines.append(f'- server: port {port} already answering (kept)')
        else:
            rc, out = run([os.path.join(HERE, 'serve-wp.py'), root, '--port', str(port), '--background', '--php', php])
            if rc:
                stop('serve-wp', rc, out)
            lines.append('- server: ' + out.splitlines()[0].replace('OK serve-wp: ', ''))
    # 5. Install, admin, settings, plugins.
    args = [os.path.join(HERE, 'install-wp.py'), root, '--url', url, '--title', site.get('site_name') or site_dir,
            '--php', php, '--fields', a.fields]
    if a.profile:
        args += ['--profile', a.profile]
    tz = site.get('timezone') or ''
    if '/' in tz:
        args += ['--timezone', tz]
    rc, out = run(args, env=env)
    if rc >= 2 or (rc == 1 and not out.startswith('WARN install-wp')):  # 1 without WARN: it crashed
        stop('install-wp', rc, out)
    code = rc
    head, *rest = out.splitlines() or ['']
    print(('WARN' if code else 'OK') + f' setup: {url}: ' + ('done with open items (install-wp)' if code else
                                                            f'local WordPress ready ({len(lines) + 1} steps)'))
    for l in lines:
        print(l)
    print('- install: ' + head)
    for l in rest:
        print('  ' + l.strip())
    sys.exit(1 if code else 0)


if __name__ == '__main__':
    main()
