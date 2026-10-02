#!/usr/bin/env python3
"""Write wp-config.php for a local copy from wp-config-sample.php. Salts are generated here and never printed.

    python3 make-wp-config.py <site folder> --db db_example [--user root] [--host localhost] [--prefix wp_]
                              [--env local] [--force]

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
import os
import re
import secrets
import string
import sys

ap = argparse.ArgumentParser()
ap.add_argument('site')
ap.add_argument('--db', required=True)
ap.add_argument('--user', default='root')
ap.add_argument('--host', default='localhost')
ap.add_argument('--prefix', default='wp_')
ap.add_argument('--env', default='local', choices=['local', 'development', 'staging', 'production'])
ap.add_argument('--force', action='store_true')
a = ap.parse_args()

sample = os.path.join(a.site, 'wp-config-sample.php')
target = os.path.join(a.site, 'wp-config.php')
if not os.path.exists(sample):
    sys.exit('wp-config-sample.php not found: unpack WordPress first (get-wordpress.py)')
if os.path.exists(target) and not a.force:
    sys.exit('wp-config.php already exists: left as it is (use --force to replace it)')
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
extra = (f"define( 'WP_ENVIRONMENT_TYPE', '{a.env}' );\n"
         f"define( 'WP_DEBUG', {'true' if a.env != 'production' else 'false'} );\n"
         f"define( 'WP_DEBUG_LOG', {'true' if a.env != 'production' else 'false'} );\n"
         "define( 'WP_DEBUG_DISPLAY', false );\n"
         "define( 'DISALLOW_FILE_EDIT', true );\n\n"
         "// ACF PRO licence: the developer pastes the key and removes the two slashes (ACF then activates this site).\n"
         "// define( 'ACF_PRO_LICENSE', '' );\n\n")
marker = "/* That's all, stop editing!"
if marker in s:
    s = s.replace(marker, extra + marker, 1)
else:
    s = s.replace("/** Absolute path", extra + "/** Absolute path", 1)
s = re.sub(r"\n\s*define\(\s*'WP_DEBUG',\s*false\s*\);\n", '\n', s, count=1)  # the sample's own WP_DEBUG line
with open(target, 'w', encoding='utf-8') as fh:
    fh.write(s)
os.chmod(target, 0o644)
print(f'wp-config.php written: DB {a.db} on {a.host} as {a.user} (password {"from DB_PASSWORD" if password else "empty"}), '
      f'prefix {a.prefix}, environment {a.env}, 8 fresh salts (not shown), debug to wp-content/debug.log, file editing off; '
      'ACF_PRO_LICENSE line ready for the developer to fill')
