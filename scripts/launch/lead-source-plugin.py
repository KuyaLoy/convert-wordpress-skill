#!/usr/bin/env python3
"""Make the Lead source must-use plugin for a WordPress site the kit did not build (an existing site).

    python3 <kit>/scripts/launch/lead-source-plugin.py <out_dir> [--brand '#28292D'] [--days 90]
                                                      [--consent auto|banner|none] [--thank-you /thank-you/]

Writes <out_dir>/kitwp-lead-source.php (the loader) and <out_dir>/kitwp-lead-source/ (the theme kit's own
forms-attribution.php, forms-lead-source.php and attribution.js, copied, so the plugin and the kit stay one code).
Copy both into the site's wp-content/mu-plugins/. --brand: the email's brand colour for the table's title row (its
text black or white, whichever reads better). --consent: as KITWP_ATTRIBUTION_CONSENT ("auto" reads Google Consent
Mode; "banner" for a banner that calls window.kitwpConsent(); "none"). Run it from the kit, not from _plan/tools
(it needs the kit's assets/ folder). Never install it on a site whose theme the kit built: that has it already.
"""
import argparse
import os
import re
import shutil
import sys

KIT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILES = ['assets/theme/includes/forms-attribution.php', 'assets/theme/includes/forms-lead-source.php',
         'assets/theme/assets/attribution.js']
LOADER = 'assets/mu-plugin/kitwp-lead-source.php'


def version():
    try:
        with open(os.path.join(KIT, 'CHANGELOG.md'), encoding='utf-8') as fh:
            m = re.search(r'^## \[(\d+\.\d+\.\d+)\] - \d{4}-\d{2}-\d{2}', fh.read(), re.M)
        return m.group(1) if m else '1.0.0'
    except OSError:
        return '1.0.0'


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('out_dir')
    ap.add_argument('--brand', default='#28292D')
    ap.add_argument('--days', type=int, default=90)
    ap.add_argument('--consent', choices=['auto', 'banner', 'none'], default='auto')
    ap.add_argument('--thank-you', default='/thank-you/')
    a = ap.parse_args(argv)
    missing = [f for f in FILES + [LOADER] if not os.path.isfile(os.path.join(KIT, f))]
    if missing:
        print(f'FAIL lead-source-plugin: not the kit ({missing[0]} is missing): run <kit>/scripts/launch/'
              'lead-source-plugin.py, not the copy in _plan/tools')
        return 2
    if not re.fullmatch(r'#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})', a.brand):
        print(f'FAIL lead-source-plugin: --brand "{a.brand}" is not a #rgb or #rrggbb colour')
        return 2
    if a.days < 0 or not re.fullmatch(r'/[\w\-/]*', a.thank_you):
        print('FAIL lead-source-plugin: --days must be 0 or more and --thank-you a path such as /thank-you/')
        return 2
    folder = os.path.join(a.out_dir, 'kitwp-lead-source')
    os.makedirs(folder, exist_ok=True)
    for f in FILES:
        shutil.copyfile(os.path.join(KIT, f), os.path.join(folder, os.path.basename(f)))
    with open(os.path.join(KIT, LOADER), encoding='utf-8') as fh:
        text = fh.read()
    for token, value in (('{{VERSION}}', version()), ('{{BRAND_COLOUR}}', a.brand), ('{{DAYS}}', str(a.days)),
                         ('{{CONSENT}}', a.consent), ('{{THANK_YOU}}', a.thank_you)):
        text = text.replace(token, value)
    with open(os.path.join(a.out_dir, 'kitwp-lead-source.php'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    print(f'OK lead-source-plugin: {a.out_dir}/kitwp-lead-source.php and kitwp-lead-source/ (3 files); copy both '
          'into wp-content/mu-plugins/, then send a TEST lead with ?utm_source=qa&utm_medium=test')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
