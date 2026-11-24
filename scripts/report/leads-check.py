#!/usr/bin/env python3
"""Check the leads portal endpoint and write key with a GET (the portal stores nothing for a GET).

    python3 leads-check.py [--endpoint https://<portal>/ingest/<project>]
    KITWP_LEADS_ENDPOINT=... KITWP_LEADS_KEY=... python3 leads-check.py
    python3 leads-check.py --site [<WordPress root>] [--wp "<WP-CLI command>"]

Before launch: the developer runs it in their own terminal; the key comes from KITWP_LEADS_KEY or a hidden prompt (it
is never a command-line argument, never printed and never logged), so the key is proven before the switch.
--site: the values the site itself uses (Theme Settings > Leads portal, or the wp-config constants that win), read
and checked inside WordPress through WP-CLI: the key never leaves PHP. Run it on live once they are pasted, and on the
go/no-go list. --wp "wp @live" (a WP-CLI alias) or --wp "php <path>/wp-cli.phar" when `wp` is not on PATH.
A POST would store a real lead: this script never posts.
Line 1: OK|FAIL leads-check: <what the portal answered>. Exit 0 on 200, 1 otherwise, 2 on a usage error.
"""
import argparse
import getpass
import json
import os
import shlex
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ANSWERS = {
    401: 'the key is wrong, or the project is disabled in the portal admin (rotate the write key if it was lost)',
    403: 'the portal refused this origin (it only takes server-to-server calls)',
    404: 'no project at this endpoint: check the project slug in the URL',
    503: 'the portal is busy: try again in a few minutes',
}


# Runs inside WordPress (wp eval): the theme's own kitwp_leads_settings(), one GET, and only facts back (never the key).
SITE_PHP = r'''
$o = [ 'env' => wp_get_environment_type() ];
if ( ! function_exists( 'kitwp_leads_settings' ) ) {
	$o['error'] = 'no kitwp_leads_settings() in the active theme (a kit theme from 0.9.12 has it)';
} else {
	$s = kitwp_leads_settings();
	$u = wp_parse_url( $s['endpoint'] );
	$o += [ 'from' => $s['from'], 'endpoint' => '' !== $s['endpoint'], 'key' => '' !== $s['key'],
		'https' => 0 === strpos( $s['endpoint'], 'https://' ),
		'where' => ( isset( $u['host'] ) ? $u['host'] : '' ) . ( isset( $u['path'] ) ? $u['path'] : '' ) ];
	if ( $o['endpoint'] && $o['key'] && $o['https'] ) {
		$h = [ 'Authorization' => 'Bearer ' . $s['key'], 'User-Agent' => 'leads-check/1.0' ];
		$r = wp_remote_get( $s['endpoint'], [ 'timeout' => 15, 'redirection' => 0, 'headers' => $h ] );
		$o['code'] = is_wp_error( $r ) ? 0 : (int) wp_remote_retrieve_response_code( $r );
		$o['transport'] = is_wp_error( $r ) ? $r->get_error_code() : '';
	}
}
echo 'KITWP_LEADS_CHECK ' . wp_json_encode( $o ) . "\n";
'''


def verdict(code, where):
    """Print the verdict for a portal answer and exit."""
    if code == 200:
        print(f'OK leads-check: {where} accepts this key (200; nothing stored)')
        sys.exit(0)
    print(f'FAIL leads-check: HTTP {code}: '
          + ANSWERS.get(code, 'unexpected answer: check the endpoint in the portal admin'))
    sys.exit(1)


def check_site(a):
    """--site: read and check the values the site uses, inside WordPress (WP-CLI)."""
    wp = shlex.split(a.wp) if a.wp else ([shutil.which('wp')] if shutil.which('wp') else None)
    if not wp:
        print('FAIL leads-check: WP-CLI not found. Put `wp` on PATH or pass --wp "php <path>/wp-cli.phar".')
        sys.exit(2)
    cmd = wp + ([f'--path={a.site}'] if a.site else []) + ['eval', SITE_PHP]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=a.timeout + 60, errors='replace')
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f'FAIL leads-check: WP-CLI did not run ({type(e).__name__})')
        sys.exit(2)
    line = next((x for x in r.stdout.splitlines() if x.startswith('KITWP_LEADS_CHECK ')), '')
    if not line:
        print(f'FAIL leads-check: WP-CLI gave no answer (exit {r.returncode}); run `wp eval "echo 1;"` there first')
        sys.exit(2)
    o = json.loads(line.split(' ', 1)[1])
    if o.get('error'):
        print('FAIL leads-check: ' + o['error'])
        sys.exit(1)
    src = f"(from {o.get('from')}; environment {o.get('env')})"
    if not o.get('endpoint') or not o.get('key'):
        empty = ' and '.join(x for x, ok in (('the address', o.get('endpoint')), ('the password', o.get('key')))
                             if not ok)
        print(f'FAIL leads-check: {empty} empty in Theme Settings > Leads portal {src}: the developer pastes them '
              '(as an administrator)')
        sys.exit(1)
    if not o.get('https'):
        print(f'FAIL leads-check: the endpoint must be an https:// URL {src}')
        sys.exit(1)
    if o.get('code', 0) == 0:
        print(f"FAIL leads-check: {o.get('where')} did not answer ({o.get('transport') or 'no response'}) {src}")
        sys.exit(1)
    if o.get('env') in ('local', 'development', 'staging'):
        print(f"note: this site's environment is {o.get('env')}: it sends no leads (live only)")
    verdict(o['code'], f"{o.get('where')} {src}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--endpoint', default=os.environ.get('KITWP_LEADS_ENDPOINT', ''))
    ap.add_argument('--site', nargs='?', const='', default=None, help='check the values the site uses (WP-CLI)')
    ap.add_argument('--wp', help='the WP-CLI command when `wp` is not on PATH, or an alias: "wp @live"')
    ap.add_argument('--timeout', type=float, default=15)
    a = ap.parse_args()
    if a.site is not None:
        check_site(a)
    endpoint = (a.endpoint or input('Leads endpoint (https://.../ingest/<project>): ')).strip()
    parts = urllib.parse.urlsplit(endpoint)
    local = parts.hostname in ('127.0.0.1', 'localhost')  # the kit's tests only
    if parts.scheme != 'https' and not (local and parts.scheme == 'http'):
        print('FAIL leads-check: the endpoint must be an https:// URL')
        sys.exit(2)
    key = os.environ.get('KITWP_LEADS_KEY') or getpass.getpass('Write key (hidden): ')
    key = key.strip()
    if not key:
        print('FAIL leads-check: no key given (KITWP_LEADS_KEY or the prompt)')
        sys.exit(2)
    req = urllib.request.Request(endpoint, method='GET', headers={'Authorization': 'Bearer ' + key,
                                                                    'User-Agent': 'leads-check/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=a.timeout) as r:
            code = r.status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception as e:  # noqa: BLE001 - reported in plain words, without the key
        print(f'FAIL leads-check: {parts.netloc} did not answer ({type(e).__name__})')
        sys.exit(1)
    verdict(code, f'{parts.netloc}{parts.path}')


if __name__ == '__main__':
    main()
