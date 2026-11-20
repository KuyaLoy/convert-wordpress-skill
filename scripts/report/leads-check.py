#!/usr/bin/env python3
"""Check the leads portal endpoint and write key with a GET (the portal stores nothing for a GET).

    python3 leads-check.py [--endpoint https://<portal>/ingest/<project>]
    KITWP_LEADS_ENDPOINT=... KITWP_LEADS_KEY=... python3 leads-check.py

The developer runs it in their own terminal: the key comes from KITWP_LEADS_KEY or a hidden prompt (it is never a
command-line argument, never printed and never logged). Run it before launch with the live key, so the key is proven
before the switch, and again on the go/no-go list. A POST would store a real lead: this script never posts.
Line 1: OK|FAIL leads-check: <what the portal answered>. Exit 0 on 200, 1 otherwise, 2 on a usage error.
"""
import argparse
import getpass
import os
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


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--endpoint', default=os.environ.get('KITWP_LEADS_ENDPOINT', ''))
    ap.add_argument('--timeout', type=float, default=15)
    a = ap.parse_args()
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
    if code == 200:
        print(f'OK leads-check: {parts.netloc}{parts.path} accepts this key (200; nothing stored)')
        sys.exit(0)
    print(f'FAIL leads-check: HTTP {code}: ' + ANSWERS.get(code, 'unexpected answer: check the endpoint in the portal admin'))
    sys.exit(1)


if __name__ == '__main__':
    main()
