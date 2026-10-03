#!/usr/bin/env python3
"""Write wp-config.php for a local copy from wp-config-sample.php, or add the kit's settings to a WordPress that a
local app already made (Local, DDEV, a host's installer). Salts are generated here and never printed.

    python3 make-wp-config.py <site folder> --db db_example [--user root] [--host localhost] [--prefix wp_]
                              [--env local] [--no-cron] [--force]
    python3 make-wp-config.py <site folder> --existing [--env local] [--no-cron]

--existing keeps the database settings and the salts as they are, saves a copy in _setup/backups/, writes the kit
block (between /* kit:settings start */ and /* kit:settings end */; running it again replaces the block) and turns
the file's own lines for the same constants into comments, so each constant is defined once.
--no-cron adds DISABLE_WP_CRON (for serve-wp.py, which answers one request at a time).

The database password comes from the DB_PASSWORD environment variable (never a command-line argument, so it is not
saved in shell history). Laragon's default MySQL root user has no password: leave DB_PASSWORD unset. The developer
types any real password; the agent never does.

Adds before "That's all, stop editing!":
  WP_ENVIRONMENT_TYPE local (the theme's seeder, snapshots and local mail capture run only on "local"),
  WP_DEBUG and WP_DEBUG_LOG on with WP_DEBUG_DISPLAY off (errors go to wp-content/debug.log),
  DISALLOW_FILE_EDIT on,
  and a commented ACF_PRO_LICENSE line for the developer to fill (the agent never types the key).
On live, Duplicator copies this file: switch WP_ENVIRONMENT_TYPE to production and WP_DEBUG off there.
"""
import argparse
import datetime
import os
import re
import secrets
import shutil
import string
import sys

ap = argparse.ArgumentParser()
ap.add_argument('site')
ap.add_argument('--db')
ap.add_argument('--existing', action='store_true', help='add the kit block to a wp-config.php that already exists')
ap.add_argument('--no-cron', action='store_true', help='add DISABLE_WP_CRON (serve-wp.py)')
ap.add_argument('--user', default='root')
ap.add_argument('--host', default='localhost')
ap.add_argument('--prefix', default='wp_')
ap.add_argument('--env', default='local', choices=['local', 'development', 'staging', 'production'])
ap.add_argument('--force', action='store_true')
a = ap.parse_args()

sample = os.path.join(a.site, 'wp-config-sample.php')
target = os.path.join(a.site, 'wp-config.php')
START, END = '/* kit:settings start */', '/* kit:settings end */'
OWN = ['WP_ENVIRONMENT_TYPE', 'WP_DEBUG', 'WP_DEBUG_LOG', 'WP_DEBUG_DISPLAY', 'DISALLOW_FILE_EDIT'] + (
    ['DISABLE_WP_CRON'] if a.no_cron else [])


def kit_block(has_acf_key):
    debug = 'true' if a.env != 'production' else 'false'
    lines = [START,
             f"define( 'WP_ENVIRONMENT_TYPE', '{a.env}' );",
             f"define( 'WP_DEBUG', {debug} );",
             f"define( 'WP_DEBUG_LOG', {debug} );",
             "define( 'WP_DEBUG_DISPLAY', false );",
             "define( 'DISALLOW_FILE_EDIT', true );"]
    if a.no_cron:
        lines.append("define( 'DISABLE_WP_CRON', true ); // serve-wp.py answers one request at a time")
    if not has_acf_key:
        lines += ['// ACF PRO licence: the developer pastes the key and removes the two slashes (ACF then activates '
                  'this site).', "// define( 'ACF_PRO_LICENSE', '' );"]
    return '\n'.join(lines + [END]) + '\n\n'


def place_block(text):
    """Put the kit block in (or replace it), and comment out the file's own lines for the same constants."""
    text = re.sub(re.escape(START) + r'.*?' + re.escape(END) + r'\n*', '', text, flags=re.S)
    switched = []
    for key in OWN:
        pat = re.compile(r"^([ \t]*)(define\(\s*['\"]" + key + r"['\"]\s*,[^;]*\);)", re.M)
        if pat.search(text):
            switched.append(key)
            text = pat.sub(lambda m: m.group(1) + '// kit (was): ' + m.group(2), text)
    block = kit_block(re.search(r"^\s*define\(\s*['\"]ACF_PRO_LICENSE", text, re.M) is not None)
    marker = "/* That's all, stop editing!"
    if marker in text:
        text = text.replace(marker, block + marker, 1)
    elif '/** Absolute path' in text:
        text = text.replace('/** Absolute path', block + '/** Absolute path', 1)
    else:
        text = text.replace("require_once ABSPATH . 'wp-settings.php';", block + "require_once ABSPATH . 'wp-settings.php';", 1)
    return text, switched


if a.existing:
    if not os.path.exists(target):
        sys.exit('FAIL make-wp-config: no wp-config.php in that folder: make the site in your local app first, or '
                 'use --db to write a new one')
    backups = os.path.join(a.site, '_setup', 'backups')
    os.makedirs(backups, exist_ok=True)
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    shutil.copy2(target, os.path.join(backups, f'wp-config.php.{stamp}'))
    with open(target, encoding='utf-8') as fh:
        text = fh.read()
    text, switched = place_block(text)
    with open(target, 'w', encoding='utf-8') as fh:
        fh.write(text)
    print(f'OK make-wp-config: kit settings added to the existing wp-config.php (environment {a.env}, debug to '
          'wp-content/debug.log, file editing off' + (', WP-Cron off' if a.no_cron else '') + '); database settings '
          'and salts kept' + (f"; the file's own {', '.join(switched)} turned into comments" if switched else '')
          + f'; backup in _setup/backups/wp-config.php.{stamp}')
    sys.exit(0)

if not a.db:
    sys.exit('FAIL make-wp-config: give --db <database name> (or --existing for a WordPress that is already set up)')
if not os.path.exists(sample):
    sys.exit('wp-config-sample.php not found: unpack WordPress first (get-wordpress.py)')
if os.path.exists(target) and not a.force:
    sys.exit('wp-config.php already exists: left as it is (use --existing to add the kit settings, or --force to '
             'replace it)')
if not re.fullmatch(r'[A-Za-z0-9_]+', a.db) or not re.fullmatch(r'[A-Za-z0-9_]+', a.prefix):
    sys.exit('database name and table prefix: letters, digits and _ only')

s = open(sample, encoding='utf-8').read()
password = os.environ.get('DB_PASSWORD', '')


def define(text, key, value):
    return re.sub(r"define\(\s*'" + key + r"',\s*'[^']*'\s*\);", lambda m: f"define( '{key}', '{value}' );", text, count=1)


s = define(s, 'DB_NAME', a.db)
s = define(s, 'DB_USER', a.user)
s = define(s, 'DB_PASSWORD', password.replace('\\', '\\\\').replace("'", "\\'"))
s = define(s, 'DB_HOST', a.host)
alphabet = string.ascii_letters + string.digits + '!#$%&()*+,-./:;<=>?@[]^_{|}~'
for key in ('AUTH_KEY', 'SECURE_AUTH_KEY', 'LOGGED_IN_KEY', 'NONCE_KEY', 'AUTH_SALT', 'SECURE_AUTH_SALT', 'LOGGED_IN_SALT', 'NONCE_SALT'):
    s = define(s, key, ''.join(secrets.choice(alphabet) for _ in range(64)))
s = re.sub(r"\$table_prefix\s*=\s*'[^']*';", f"$table_prefix = '{a.prefix}';", s, count=1)
s = re.sub(r"\n\s*define\(\s*'WP_DEBUG',\s*false\s*\);\n", '\n', s, count=1)  # the sample's own WP_DEBUG line
s, _ = place_block(s)
with open(target, 'w', encoding='utf-8') as fh:
    fh.write(s)
os.chmod(target, 0o644)
print(f'OK make-wp-config: wp-config.php written: DB {a.db} on {a.host} as {a.user} (password '
      f'{"from DB_PASSWORD" if password else "empty"}), prefix {a.prefix}, environment {a.env}, 8 fresh salts (not '
      'shown), debug to wp-content/debug.log, file editing off' + (', WP-Cron off' if a.no_cron else '')
      + '; ACF_PRO_LICENSE line ready for the developer to fill')
