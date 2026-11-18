#!/usr/bin/env python3
"""Set up a LOCAL WordPress in one go: install, the default local admin, settings, starter plugins.

    python3 install-wp.py <wp_root> --url http://<site>.test --title "<Site>" --profile <kit>/profile.local.json
                          [--php <php>] [--fields acf|scf] [--timezone Australia/Sydney] [--dry-run]

Run it after get-wordpress.py and make-wp-config.py (the plan OK covers the downloads it lists). It:
  1. refuses unless wp-config.php says WP_ENVIRONMENT_TYPE 'local' AND the URL is a local address (localhost,
     127.0.0.1, [::1], *.test, *.localhost, *.local): the default password is for local sites only;
  2. installs WordPress if it is not installed yet: admin = the profile's local_admin.username (e.g. agency-dev) and
     local_admin.email; the password comes from local_admin.password in profile.local.json (git ignores that file) or
     the KITWP_ADMIN_PASSWORD environment variable. It is passed to PHP through the environment, never on a command
     line, and never printed or written anywhere else. An existing install keeps its users and passwords untouched;
  3. sets permalinks /%postname%/, "Discourage search engines" on, the timezone (if given), the WordPress block
     in .htaccess;
  4. on a fresh install only (made by this run): deletes the sample post, page and comment, Hello Dolly and Akismet;
  5. installs the starter plugins: Contact Form 7 and Yoast SEO from wordpress.org (every file checked against
     the official checksums), plus ACF PRO from the profile's plugin_zips.acf_pro (default) or Secure Custom Fields
     from wordpress.org (--fields scf, only when the developer asks for it); a plugin folder that exists is kept;
  6. activates them and reads new lines in wp-content/debug.log.
Prints a short summary. Exit 0: all done; 1: done with open items listed (e.g. no ACF PRO zip); 2: refused.
Live sites never use this script: the live admin gets its own strong password, typed by the developer.
"""
import argparse
import hashlib
import io
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

ap = argparse.ArgumentParser()
ap.add_argument('site')
ap.add_argument('--url', required=True)
ap.add_argument('--title', default='')
ap.add_argument('--profile', help='the kit\'s profile.local.json (local_admin, plugin_zips)')
ap.add_argument('--php', default='php')
ap.add_argument('--fields', choices=['acf', 'scf'], default='acf')
ap.add_argument('--timezone', default='')
ap.add_argument('--dry-run', action='store_true')
a = ap.parse_args()

ROOT = os.path.abspath(a.site)
PLUGINS = os.path.join(ROOT, 'wp-content', 'plugins')
LOCAL_HOST = re.compile(r'^(localhost|127\.0\.0\.1|\[::1\]|::1|[a-z0-9.-]+\.(test|localhost|local))$', re.I)
WPORG = ['contact-form-7', 'wordpress-seo'] + (['secure-custom-fields'] if a.fields == 'scf' else [])
opened = []


out = []


def say(line):
    out.append(line)


def stop(msg):
    print('FAIL install-wp: refused: ' + msg)
    sys.exit(2)


# 1. Local only.
cfg_path = os.path.join(ROOT, 'wp-config.php')
if not os.path.isfile(os.path.join(ROOT, 'wp-load.php')):
    stop(f'no WordPress in {ROOT}: run get-wordpress.py first')
if not os.path.isfile(cfg_path):
    stop('no wp-config.php: run make-wp-config.py first')
cfg = open(cfg_path, encoding='utf-8', errors='replace').read()
# Read the defines with comments removed; exactly one WP_ENVIRONMENT_TYPE, and it must be 'local'.
code = re.sub(r'/\*.*?\*/', '', cfg, flags=re.S)
code = re.sub(r'(?m)^\s*(//|#).*$', '', code)
envs = re.findall(r"^\s*define\(\s*['\"]WP_ENVIRONMENT_TYPE['\"]\s*,\s*['\"](\w+)['\"]", code, re.M)
if envs != ['local']:
    stop("wp-config.php must define WP_ENVIRONMENT_TYPE 'local' exactly once: this script is for local sites only")
db = re.findall(r"^\s*define\(\s*['\"]DB_HOST['\"]\s*,\s*['\"]([^'\"]*)['\"]", code, re.M)
if len(db) != 1 or not re.match(r'^(localhost|127\.0\.0\.1|::1|\[::1\]|[a-z0-9-]+)(:\S*)?$', db[0], re.I) or \
        ('.' in db[0].split(':')[0] and db[0].split(':')[0] != '127.0.0.1'):
    stop('DB_HOST in wp-config.php is not a local database host (localhost, 127.0.0.1, a socket or a container name)')
host = urllib.parse.urlsplit(a.url).hostname or ''
if not LOCAL_HOST.match(host):
    stop(f'{host or a.url} is not a local address (localhost, 127.0.0.1, *.test, *.localhost, *.local)')

profile = {}
if a.profile:
    try:
        profile = json.load(open(a.profile, encoding='utf-8'))
    except (OSError, ValueError) as e:
        stop(f'cannot read the profile {a.profile}: {e}')
admin = profile.get('local_admin') or {}
user = (admin.get('username') or profile.get('admin_username') or '').strip()
email = (admin.get('email') or '').strip() or (
    f'{user or "admin"}@{host}' if '.' in host and not host[0].isdigit() else f'{user or "admin"}@example.com')
password = os.environ.get('KITWP_ADMIN_PASSWORD') or admin.get('password') or ''
acf_zip = ((profile.get('plugin_zips') or {}).get('acf_pro') or '').strip()
if acf_zip and not os.path.isabs(acf_zip) and a.profile:
    acf_zip = os.path.join(os.path.dirname(os.path.abspath(a.profile)), acf_zip)

PHP_CODE = r'''<?php
error_reporting( E_ALL & ~E_DEPRECATED & ~E_NOTICE & ~E_WARNING );
$kit_url = getenv( 'KITWP_URL' );
$kit_p = parse_url( $kit_url );
$_SERVER['HTTP_HOST'] = $kit_p['host'] . ( isset( $kit_p['port'] ) ? ':' . $kit_p['port'] : '' );
$_SERVER['SERVER_NAME'] = $kit_p['host'];
$_SERVER['REQUEST_URI'] = '/';
$_SERVER['HTTPS'] = ( 'https' === $kit_p['scheme'] ) ? 'on' : '';
$kit_mode = getenv( 'KITWP_MODE' );
$kit_out = array();
if ( 'configure' !== $kit_mode ) {
	define( 'WP_INSTALLING', true ); // no redirect to install.php before the install
}
require getenv( 'KITWP_WP_ROOT' ) . '/wp-load.php';
require_once ABSPATH . 'wp-admin/includes/upgrade.php';
require_once ABSPATH . 'wp-admin/includes/plugin.php';
require_once ABSPATH . 'wp-admin/includes/misc.php';
if ( 'status' === $kit_mode ) {
	$kit_out['installed'] = is_blog_installed();
} elseif ( 'install' === $kit_mode ) {
	if ( is_blog_installed() ) {
		$kit_out['installed'] = 'already';
	} else {
		$kit_r = wp_install( getenv( 'KITWP_TITLE' ), getenv( 'KITWP_USER' ), getenv( 'KITWP_EMAIL' ), false, '', wp_slash( getenv( 'KITWP_ADMIN_PASSWORD' ) ) );
		$kit_out['installed'] = ! empty( $kit_r['user_id'] ) ? 'now' : 'failed';
	}
} elseif ( 'configure' === $kit_mode ) {
	update_option( 'siteurl', untrailingslashit( $kit_url ) );
	update_option( 'home', untrailingslashit( $kit_url ) );
	update_option( 'blog_public', '0' );
	if ( getenv( 'KITWP_TZ' ) ) {
		update_option( 'timezone_string', getenv( 'KITWP_TZ' ) );
	}
	global $wp_rewrite;
	$wp_rewrite->set_permalink_structure( '/%postname%/' );
	$wp_rewrite->flush_rules( false );
	$kit_rules = $wp_rewrite->mod_rewrite_rules();
	$kit_out['htaccess'] = $kit_rules ? insert_with_markers( ABSPATH . '.htaccess', 'WordPress', explode( "\n", $kit_rules ) ) : false;
	if ( '1' === getenv( 'KITWP_FRESH' ) ) {
		$kit_out['removed'] = array();
		foreach ( array( 1 => 'Hello world!', 2 => 'Sample Page' ) as $kit_id => $kit_title ) {
			$kit_post = get_post( $kit_id );
			if ( $kit_post && $kit_title === $kit_post->post_title ) {
				wp_delete_post( $kit_id, true );
				$kit_out['removed'][] = $kit_title;
			}
		}
		if ( get_comment( 1 ) ) {
			wp_delete_comment( 1, true );
			$kit_out['removed'][] = 'sample comment';
		}
	}
	$kit_want = array_filter( explode( ',', getenv( 'KITWP_PLUGINS' ) ) );
	$kit_out['active'] = array();
	foreach ( get_plugins() as $kit_file => $kit_data ) {
		if ( in_array( dirname( $kit_file ), $kit_want, true ) ) {
			$kit_res = is_plugin_active( $kit_file ) ? null : activate_plugin( $kit_file );
			$kit_out['active'][ dirname( $kit_file ) ] = is_wp_error( $kit_res ) ? $kit_res->get_error_message() : $kit_data['Version'];
		}
	}
	$kit_out['permalinks'] = get_option( 'permalink_structure' );
	$kit_out['blog_public'] = get_option( 'blog_public' );
	$kit_u = get_user_by( 'login', getenv( 'KITWP_USER' ) );
	$kit_out['admin_exists'] = $kit_u && user_can( $kit_u, 'manage_options' );
}
echo "\nKITWP_JSON" . wp_json_encode( $kit_out );
'''


def php(mode, extra=None):
    tmp = tempfile.mkdtemp(prefix='kitwp-')
    script = os.path.join(tmp, 'kitwp-install.php')
    open(script, 'w', encoding='utf-8').write(PHP_CODE)
    e = dict(os.environ, KITWP_MODE=mode, KITWP_WP_ROOT=ROOT.replace('\\', '/'), KITWP_URL=a.url.rstrip('/'),
             KITWP_TITLE=a.title or host, KITWP_USER=user, KITWP_EMAIL=email, KITWP_TZ=a.timezone,
             KITWP_ADMIN_PASSWORD=password if mode == 'install' else '', **(extra or {}))
    try:
        # No arguments in stack traces and no displayed errors, so a failure cannot echo the password.
        r = subprocess.run([a.php, '-d', 'zend.exception_ignore_args=1', '-d', 'display_errors=stderr', script],
                           capture_output=True, text=True, env=e, timeout=300)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    m = re.search(r'KITWP_JSON(\{.*\}|\[\])\s*$', r.stdout, re.S)
    if not m:
        if mode == 'install':
            err = ['output hidden (it could hold the password); wp-content/debug.log has the error']
        else:
            err = (r.stderr or r.stdout).strip().splitlines()[-3:]
        text = ' | '.join(err)[:400]
        if password:
            text = text.replace(password, '[hidden]')
        print(f'FAIL install-wp: php ({mode}): ' + text)
        print(chr(10).join(out))
        sys.exit(1)
    return json.loads(m.group(1)) if m.group(1) != '[]' else {}


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'convert-to-wordpress-kit'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def long(path):
    """Windows: the long-path form, so deep plugin trees unzip past 260 characters."""
    path = os.path.abspath(path)
    prefix = '\\\\?\\'
    return prefix + path if os.name == 'nt' and not path.startswith(prefix) else path


def safe_extract(data, dest, expect_top):
    """Unzip one plugin folder into dest: checked paths, a temp folder first, moved into place only when complete."""
    zf = zipfile.ZipFile(io.BytesIO(data))
    tops = {n.split('/')[0] for n in zf.namelist()}
    if tops != {expect_top}:
        raise ValueError(f'unexpected zip layout: {sorted(tops)[:3]}')
    for n in zf.namelist():
        if n.startswith(('/', '\\')) or '..' in n.replace('\\', '/').split('/') or ':' in n:
            raise ValueError(f'unsafe path in zip: {n}')
    tmp = os.path.join(dest, '.kitwp-unzip-' + expect_top)
    shutil.rmtree(long(tmp), ignore_errors=True)
    try:
        zf.extractall(long(tmp))
        for d, _, fs in os.walk(long(tmp)):
            os.chmod(d, 0o755)
            for f in fs:
                os.chmod(os.path.join(d, f), 0o644)
        os.rename(long(os.path.join(tmp, expect_top)), long(os.path.join(dest, expect_top)))
    finally:
        shutil.rmtree(long(tmp), ignore_errors=True)


def wporg_plugin(slug):
    if os.path.isdir(os.path.join(PLUGINS, slug)):
        return f'{slug}: present, kept'
    info = json.loads(fetch('https://api.wordpress.org/plugins/info/1.2/?action=plugin_information&request[slug]='
                            + slug))
    ver, link = info['version'], info['download_link']
    if a.dry_run:
        return f'{slug}: would download {ver}'
    data = fetch(link)
    sums = json.loads(fetch(f'https://downloads.wordpress.org/plugin-checksums/{slug}/{ver}.json'))['files']
    zf = zipfile.ZipFile(io.BytesIO(data))
    bad = 0
    for n in zf.namelist():
        if n.endswith('/'):
            continue
        rel = n.split('/', 1)[1]
        want = sums.get(rel, {}).get('sha256')
        got = hashlib.sha256(zf.read(n)).hexdigest()
        if want is None or got not in (want if isinstance(want, list) else [want]):
            bad += 1
    if bad:
        raise ValueError(f'{slug} {ver}: {bad} files do not match the official checksums; nothing installed')
    safe_extract(data, PLUGINS, slug)
    return f'{slug}: {ver} installed, {len(sums)} files checked'


# 2. Install.
status = php('status')
fresh = False
if status.get('installed'):
    say(f'wordpress: already installed at {a.url} (users and passwords untouched)')
else:
    if not user:
        stop('no admin username: set local_admin.username in profile.local.json (e.g. agency-dev)')
    if not password:
        stop('no local admin password: the developer adds local_admin.password to profile.local.json once '
             '(never committed), or sets KITWP_ADMIN_PASSWORD in their own shell')
    if a.dry_run:
        say(f'wordpress: would install at {a.url}, admin {user}')
    else:
        r = php('install')
        if r.get('installed') != 'now':
            say(f"FAIL install-wp: wordpress install: {r.get('installed')}")
            sys.exit(1)
        fresh = True
        say(f'wordpress: installed at {a.url}, admin {user} (password from the profile, not shown)')

# 4. Fresh-install samples (files part; posts are removed in PHP below).
if fresh:
    for p in ('hello.php', 'akismet'):
        full = os.path.join(PLUGINS, p)
        if os.path.isdir(full):
            shutil.rmtree(full)
        elif os.path.isfile(full):
            os.remove(full)

# 5. Plugins.
want = list(WPORG)
for slug in WPORG:
    try:
        say('plugin ' + wporg_plugin(slug))
    except Exception as e:  # noqa: BLE001 - report and go on with the rest
        opened.append(f'{slug}: {e}')
        say(f'FAIL plugin {slug}: {e}')
if a.fields == 'acf':
    want.append('advanced-custom-fields-pro')
    if os.path.isdir(os.path.join(PLUGINS, 'advanced-custom-fields-pro')):
        say('plugin advanced-custom-fields-pro: present, kept')
    elif not acf_zip or not os.path.isfile(acf_zip):
        opened.append('advanced-custom-fields-pro: no zip at plugin_zips.acf_pro in the profile (the developer downloads it from '
                      'their ACF account and sets the path), then run this again')
        say('OPEN plugin advanced-custom-fields-pro: no zip in the profile')
    elif a.dry_run:
        say(f'plugin advanced-custom-fields-pro: would unzip {os.path.basename(acf_zip)}')
    else:
        data = open(acf_zip, 'rb').read()
        try:
            safe_extract(data, PLUGINS, 'advanced-custom-fields-pro')
            say(f'plugin advanced-custom-fields-pro: unzipped from the profile zip (sha256 '
                  f'{hashlib.sha256(data).hexdigest()[:12]}...)')
        except Exception as e:  # noqa: BLE001
            opened.append(f'advanced-custom-fields-pro: zip refused: {e}')
            say(f'FAIL plugin advanced-custom-fields-pro: {e}')

# 3 and 6. Settings, samples, activation.
if a.dry_run:
    print(('WARN' if opened else 'OK') + f' install-wp: dry run, nothing written; {len(opened)} open item(s)')
    for o in opened:
        print('  - ' + o)
    print(chr(10).join(out))
    sys.exit(1 if opened else 0)
log = os.path.join(ROOT, 'wp-content', 'debug.log')
log_before = os.path.getsize(log) if os.path.isfile(log) else 0
r = php('configure', {'KITWP_FRESH': '1' if fresh else '0', 'KITWP_PLUGINS': ','.join(want)})
say(f"settings: permalinks {r.get('permalinks')}, search engines discouraged: {r.get('blog_public') == '0'}, "
      f".htaccess WordPress block: {'ok' if r.get('htaccess') else 'not written'}")
if r.get('removed'):
    say('removed (fresh install): ' + ', '.join(r['removed']) + ', Hello Dolly, Akismet')
for slug, v in (r.get('active') or {}).items():
    say(f'active: {slug} {v}')
for slug in want:
    if slug not in (r.get('active') or {}) and not any(slug in o for o in opened):
        opened.append(f'{slug}: not active')
if not r.get('admin_exists'):
    opened.append(f'admin user {user or "(none)"} not found with administrator rights')
if os.path.isfile(log) and os.path.getsize(log) > log_before:
    with open(log, encoding='utf-8', errors='replace') as fh:
        fh.seek(log_before)
        fatal = [l for l in fh.read().splitlines() if 'Fatal' in l]
    say(f'debug.log: new lines written, {len(fatal)} fatal')
    if fatal:
        opened.append('debug.log: ' + fatal[0][:200])
else:
    say('debug.log: no new lines')
if a.fields == 'acf' and 'ACF_PRO_LICENSE' in cfg and re.search(r"^\s*//\s*define\(\s*'ACF_PRO_LICENSE'", cfg, re.M):
    say('note: the developer pastes the ACF PRO licence into the ACF_PRO_LICENSE line in wp-config.php')
if opened:
    print(f'WARN install-wp: {a.url}: {len(opened)} open item(s):')
    for o in opened:
        print('  - ' + o)
    print(chr(10).join(out))
    sys.exit(1)
print(f'OK install-wp: {a.url} ready (WordPress, admin, settings, {len(r.get("active") or {})} plugins active)')
print(chr(10).join(out))
