"""0.12.0: the company attribution standard (eleven labelled fields, in order, in the email, CFDB7 and the posted
names a CRM maps), Google Ads Campaign ID, dates in the site's time zone, landing pages with their query, the
connector's live checklist box, and the kit's default form layout (form-layout.mjs)."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

from helpers import path
from test_theme_kit import FORMS, INC, MAIL, php

ATTR = INC + 'forms-attribution.php'
SRC = INC + 'forms-lead-source.php'
LABELS = ['Lead Source', 'Google Ads Campaign ID', 'Google Click ID', 'Landing Page', 'Referrer', 'Lead Source Date',
          'Form Submitted From', 'First Touch Source', 'First Visit Date', 'First Touch Landing Page',
          'First Touch Referrer']
CORE = [(ATTR, n) for n in ('kitwp_attribution_fields', 'kitwp_attribution_touch', 'kitwp_attribution_url',
                            'kitwp_attribution_clean', 'kitwp_attribution_form_page', 'kitwp_attribution_posted',
                            'kitwp_attribution_cfdb7')] + \
       [(SRC, n) for n in ('kitwp_attribution_standard', 'kitwp_attribution_extras', 'kitwp_attribution_date',
                           'kitwp_attribution_values', 'kitwp_attribution_extra_rows', 'kitwp_attribution_visits',
                           'kitwp_attribution_source', 'kitwp_attribution_rows', 'kitwp_attribution_table',
                           'kitwp_attribution_title_colours')]
# The site's time zone is Australia/Sydney (UTC+11 in November): 2026-11-25 20:30 UTC is 2026-11-26 there.
STUBS = r'''
const KITWP_BRAND_COLOUR = '#123456';
function wp_timezone() { return new DateTimeZone( 'Australia/Sydney' ); }
function wp_date( $format, $ts, $tz ) { return ( new DateTime( '@' . $ts ) )->setTimezone( $tz )->format( $format ); }
function home_url( $p = '' ) { return 'https://example.org' . $p; }
class WPCF7_Submission {
	public static function get_instance() { return new self(); }
	public function get_posted_data( $name = '' ) { return '' === $name ? $GLOBALS['posted'] : ( $GLOBALS['posted'][ $name ] ?? null ); }
}
function kitwp_lead_fields() { return []; }
function kitwp_lead_data( $s ) { return [ 'page' => 'https://example.org/meta-url/' ]; }
function kitwp_lead_extras( $l ) { return []; }
'''
# What the browser posts after a visit to /offer/?gad_campaignid=123&gclid=TEST&utm_source=google from Google.
TEST_VISIT = {'utm_source': 'google', 'gclid': 'TEST', 'gad_campaignid': '123',
              'landing_page': 'https://example.org/offer/?gad_campaignid=123&gclid=TEST&utm_source=google',
              'referrer': 'https://www.google.com/', 'last_seen': '2026-11-25 20:30',
              'first_source': 'google', 'first_gclid': 'TEST', 'first_gad_campaignid': '123',
              'first_landing_page': 'https://example.org/offer/?gad_campaignid=123&gclid=TEST&utm_source=google',
              'first_referrer': 'https://www.google.com/', 'first_seen': '2026-11-25 20:30'}
PLAIN_VISIT = {'first_landing_page': 'https://example.org/', 'first_seen': '2026-11-26 01:00'}
FORM_PAGE = 'https://example.org/contact/?from=menu'


def posted(fields, referer=FORM_PAGE):
    """kitwp_attribution_posted() on a post with the form's own fields, as CF7 would run it."""
    body = (f'$_SERVER = [ "HTTP_REFERER" => {json.dumps(referer)} ]; echo json_encode( kitwp_attribution_posted( '
            f'json_decode( {json.dumps(json.dumps(dict({"your-name": "Sam"}, **fields)))}, true ) ) );')
    return php(CORE, body, STUBS)


def email(post, html=True):
    body = (f'$GLOBALS["posted"] = json_decode( {json.dumps(json.dumps(post))}, true ); echo json_encode( '
            f'kitwp_lead_special_tags( null, "_kitk_source", {"true" if html else "false"} ) );')
    return php(CORE + [(MAIL, 'kitwp_lead_special_tags'), (MAIL, 'kitwp_mail_h')], body, STUBS)


def cfdb7(post):
    """kitwp_attribution_cfdb7() as CFDB7 1.4.2 calls it: its data holds only the form's own tags (cfdb7_strict_keys
    is on by default), the attribution comes from the CF7 submission."""
    data = {'cfdb7_status': 'unread', 'your-name': post['your-name']}
    body = (f'$GLOBALS["posted"] = json_decode( {json.dumps(json.dumps(post))}, true ); echo json_encode( '
            f'kitwp_attribution_cfdb7( json_decode( {json.dumps(json.dumps(data))}, true ) ) );')
    return php(CORE, body, STUBS)


def rows(out):
    return [tuple(re.sub(r'<[^>]+>', '', c) for c in re.findall(r'<td[^>]*>(.*?)</td>', r))
            for r in re.findall(r'<tr>(.*?)</tr>', out)]


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class Standard(unittest.TestCase):
    def test_test_lead_has_the_eleven_in_order_with_values(self):
        got = posted(TEST_VISIT)
        table = rows(email(got))
        self.assertEqual(table[0], ('Lead Attribution',))
        self.assertEqual([r[0] for r in table[1:12]], LABELS)
        values = dict(r for r in table[1:12])
        self.assertEqual(values['Lead Source'], 'Google Ads')
        self.assertEqual(values['Google Ads Campaign ID'], '123')
        self.assertEqual(values['Google Click ID'], 'TEST')
        self.assertEqual(values['Landing Page'],
                         'https://example.org/offer/?gad_campaignid=123&amp;gclid=TEST&amp;utm_source=google')
        self.assertEqual(values['Referrer'], 'https://www.google.com/')
        self.assertEqual(values['Lead Source Date'], '2026-11-26')  # the site's time zone, not UTC
        self.assertEqual(values['Form Submitted From'], FORM_PAGE)
        self.assertEqual(values['First Touch Source'], 'Google Ads')
        self.assertEqual(values['First Visit Date'], '2026-11-26')
        self.assertNotIn('none', values.values())
        extras = [r[0] for r in table[12:]]
        self.assertEqual(extras, ['UTM Source'])  # gclid and the campaign are rows already; first touch = latest

    def test_cfdb7_columns_are_the_labels_in_order(self):
        cols = cfdb7(posted(TEST_VISIT))
        keys = list(cols)
        self.assertEqual(keys[:2], ['cfdb7_status', 'your-name'])  # the form's own fields first
        self.assertEqual(keys[2:13], LABELS)
        self.assertEqual(keys[13:], ['UTM Source'])
        self.assertEqual((cols['Lead Source'], cols['Google Ads Campaign ID'], cols['Google Click ID']),
                         ('Google Ads', '123', 'TEST'))
        for raw in ('first_seen', 'last_seen', 'gclid', 'lead_source', 'first_landing_page'):
            self.assertNotIn(raw, cols)

    def test_cfdb7_values_are_escaped_and_off_without_a_submission(self):
        cols = cfdb7(posted({'utm_source': '<b>x</b>', 'last_seen': '2026-11-25 20:30'}))
        self.assertEqual((cols['Lead Source'], cols['UTM Source']), ('&lt;b&gt;x&lt;/b&gt;', '&lt;b&gt;x&lt;/b&gt;'))
        same = php(CORE, '$GLOBALS["posted"] = []; echo json_encode( kitwp_attribution_cfdb7( [ "a" => "b" ] ) );', STUBS)
        self.assertEqual(same, {'a': 'b'})  # another plugin's save, or no attribution: left as it was

    def test_plain_visit_says_direct_and_none(self):
        values = dict(rows(email(posted(PLAIN_VISIT, 'https://example.org/contact/')))[1:])
        self.assertEqual(values['Lead Source'], 'Direct')
        self.assertEqual(values['First Touch Source'], 'Direct')
        for label in ('Google Ads Campaign ID', 'Google Click ID', 'Referrer', 'First Touch Referrer'):
            self.assertEqual(values[label], 'none')
        self.assertEqual(values['Landing Page'], 'https://example.org/')  # the latest touch is the first visit
        self.assertEqual(values['Lead Source Date'], '2026-11-26')
        self.assertEqual(len(values), 11)  # no extras

    def test_no_script_data_and_plain_text(self):
        values = dict(rows(email(posted({}, '')))[1:])
        self.assertEqual(values['Lead Source'], 'Not recorded')
        self.assertEqual(list(values), LABELS)
        text = email(posted(PLAIN_VISIT), html=False).split('\n')
        self.assertEqual(text[0], 'Lead Attribution')
        self.assertEqual([t.split(': ')[0] for t in text[1:]], LABELS)

    def test_campaign_id_sources_and_posted_names_are_replaced(self):
        def campaign(fields):
            return posted(dict(fields, last_seen='2026-11-25 20:30'))['google_ads_campaign_id']
        self.assertEqual(campaign({'utm_source': 'google', 'utm_id': '777', 'utm_campaign': '555'}), '777')
        self.assertEqual(campaign({'utm_source': 'google', 'utm_campaign': '555'}), '555')
        self.assertEqual(campaign({'utm_source': 'google', 'utm_campaign': 'spring'}), 'none')
        forged = posted(dict(PLAIN_VISIT, lead_source='Forged', google_click_id='x'))
        self.assertEqual((forged['lead_source'], forged['google_click_id']), ('Direct', 'none'))

    def test_landing_page_keeps_its_query_but_never_an_email(self):
        got = posted({'landing_page': 'https://example.org/a/?utm_source=x&email=sam%40example.org&q=1#top',
                      'referrer': 'https://other.example/path/?secret=1', 'last_seen': '2026-11-25 20:30'})
        self.assertEqual(got['landing_page'], 'https://example.org/a/?utm_source=x&q=1')
        self.assertEqual(got['referrer'], 'https://other.example/path/')
        self.assertEqual(got['lead_source'], 'other.example (link)')

    def test_extras_show_a_different_first_touch(self):
        got = posted({'msclkid': 'M1', 'utm_source': 'bing', 'last_seen': '2026-11-25 20:30',
                      'first_source': 'newsletter', 'first_medium': 'email', 'first_seen': '2026-11-01 00:00'})
        table = rows(email(got))
        self.assertEqual(dict(table[1:12])['Lead Source'], 'Microsoft Ads')
        self.assertEqual(dict(table[1:12])['First Touch Source'], 'newsletter / email')
        self.assertEqual(table[12:], [('UTM Source', 'bing'), ('Microsoft Click ID', 'M1'),
                                      ('First Touch UTM Source', 'newsletter'), ('First Touch UTM Medium', 'email')])


@unittest.skipUnless(shutil.which('node'), 'needs Node')
class BrowserCapture(unittest.TestCase):
    HARNESS = r'''
const fs = require('fs'), vm = require('vm');
const code = fs.readFileSync(process.argv[process.argv.length - 1], 'utf8');
function store() { const m = new Map(); return { getItem: (k) => (m.has(k) ? m.get(k) : null),
  setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) }; }
const window = { location: new URL('https://example.org/offer/?gad_campaignid=123&gclid=TEST&utm_source=google&utm_id=9&e=a%40b.example#x'),
  sessionStorage: store(), localStorage: store(), kitwpAttributionConfig: { days: '90' } };
const document = { referrer: 'https://www.google.com/', readyState: 'complete', forms: [],
  createElement: () => ({}), addEventListener: () => {} };
vm.runInNewContext(code, { window, document, URL, URLSearchParams, Date, JSON, Object, Array, parseInt, isNaN, decodeURIComponent });
console.log(JSON.stringify(window.kitwpAttribution()));
'''

    def test_campaign_id_utm_id_and_landing_query(self):
        r = subprocess.run(['node', '-e', self.HARNESS, path('assets/theme/assets/attribution.js')],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        f = json.loads(r.stdout)
        self.assertEqual((f['gad_campaignid'], f['utm_id'], f['first_gad_campaignid'], f['first_id']),
                         ('123', '9', '123', '9'))
        self.assertEqual(f['landing_page'], 'https://example.org/offer/?gad_campaignid=123&gclid=TEST&utm_source=google&utm_id=9')
        self.assertEqual(f['referrer'], 'https://www.google.com/')


@unittest.skipUnless(shutil.which('node') and shutil.which('php'), 'needs Node and PHP')
class EndToEnd(unittest.TestCase):
    """The brief's TEST lead through the real code: attribution.js on the ad's landing page, then the form page,
    its hidden fields posted through kitwp_attribution_posted(), then the email table and the CFDB7 columns."""
    HARNESS = r'''
const fs = require('fs'), vm = require('vm');
const code = fs.readFileSync(process.argv[process.argv.length - 1], 'utf8');
function store() { const m = new Map(); return { getItem: (k) => (m.has(k) ? m.get(k) : null),
  setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) }; }
const session = store(), local = store();
function visit(url, referrer) {
  const window = { location: new URL(url), sessionStorage: session, localStorage: local, kitwpAttributionConfig: { days: '90' } };
  const document = { referrer, readyState: 'complete', forms: [], createElement: () => ({}), addEventListener: () => {} };
  vm.runInNewContext(code, { window, document, URL, URLSearchParams, Date, JSON, Object, Array, parseInt, isNaN, decodeURIComponent });
  return window.kitwpAttribution();
}
visit(process.argv[1], process.argv[2]);  // node -e: argv[1] is the first argument
console.log(JSON.stringify(visit('https://example.org/contact/', 'https://example.org/offer/')));
'''

    def run_lead(self, landing, referrer='', form_page='https://example.org/contact/'):
        r = subprocess.run(['node', '-e', self.HARNESS, landing, referrer, path('assets/theme/assets/attribution.js')],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        hidden = json.loads(r.stdout)
        post = posted(hidden, form_page)
        return rows(email(post)), cfdb7(post)

    def test_test_lead_from_the_ad_url(self):
        table, cfdb7 = self.run_lead('https://example.org/offer/?gad_campaignid=123&gclid=TEST&utm_source=google',
                                     'https://www.google.com/')
        self.assertEqual([r[0] for r in table[1:12]], LABELS)
        values = dict(table[1:12])
        self.assertEqual((values['Lead Source'], values['Google Ads Campaign ID'], values['Google Click ID']),
                         ('Google Ads', '123', 'TEST'))
        self.assertEqual(values['Landing Page'],
                         'https://example.org/offer/?gad_campaignid=123&amp;gclid=TEST&amp;utm_source=google')
        self.assertEqual(values['Referrer'], 'https://www.google.com/')
        self.assertEqual(values['Form Submitted From'], 'https://example.org/contact/')
        self.assertRegex(values['Lead Source Date'], r'^\d{4}-\d{2}-\d{2}$')
        self.assertNotIn('none', values.values())
        self.assertEqual(list(cfdb7)[2:13], LABELS)
        self.assertEqual([cfdb7[k] for k in LABELS[:3]], ['Google Ads', '123', 'TEST'])

    def test_plain_visit(self):
        table, cfdb7 = self.run_lead('https://example.org/')
        values = dict(table[1:])
        self.assertEqual(values['Lead Source'], 'Direct')
        self.assertEqual([values[k] for k in ('Google Ads Campaign ID', 'Google Click ID', 'Referrer')],
                         ['none', 'none', 'none'])
        self.assertEqual(cfdb7['Lead Source'], 'Direct')


class Checklist(unittest.TestCase):
    def test_lead_forms_box_in_the_live_checklist(self):
        from helpers import run
        tmp = tempfile.mkdtemp()
        root = os.path.join(tmp, 'shop')
        prof = os.path.join(tmp, 'profile.local.json')
        with open(prof, 'w', encoding='utf-8') as fh:
            json.dump({'extra_plugins': [{'name': 'Example Connector', 'required': True, 'where': 'live',
                                          'zip': 'connector', 'lead_forms': True},
                                         {'name': 'Example Tracker', 'live': True}]}, fh)
        with open(path('assets', 'site.example.json'), encoding='utf-8') as fh:
            site = json.load(fh)
        site.update(site_name='Corner Shop', domain='cornershop.example.org', wp_root=root, local_host='shop.test',
                    site_dir='shop', theme='shop', prefix='shop', key='cs')
        os.makedirs(os.path.join(root, '_plan'))
        with open(os.path.join(root, '_plan', 'site.json'), 'w', encoding='utf-8') as fh:
            json.dump(site, fh)
        r = run('scripts/new-site.py', os.path.join(root, '_plan', 'site.json'), '--plan-only', '--profile', prof)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(os.path.join(root, '_setup', 'launch', 'RUNBOOK.md'), encoding='utf-8') as fh:
            rb = fh.read()
        shutil.rmtree(tmp, ignore_errors=True)
        box = rb.index('Example Connector: from your plugin folder')
        self.assertIn('     - [ ] Every lead form mapped in the app it connects to, with the eleven attribution fields',
                      rb[box:box + 400])
        self.assertEqual(rb.count('Every lead form mapped in the app'), 1)  # not under Example Tracker


class Docs(unittest.TestCase):
    def test_forms_email_lists_the_eleven_in_order(self):
        with open(path('references/forms-email.md'), encoding='utf-8') as fh:
            doc = fh.read()
        table = re.findall(r'^\| \d+ \| ([^|]+) \|', doc, re.M)
        self.assertEqual([t.strip() for t in table], LABELS)
        self.assertIn('## Upgrading a kit site to the attribution standard', doc)
        self.assertIn('## Form layout', doc)


FORM = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><style>{css}</style>
<style>.btn{{background:#123456;color:#fff;border:0;padding:12px 24px;border-radius:6px}}</style></head>
<body style="font-family:Arial,sans-serif;margin:24px">
<form data-form-name="Quote Form" class="kitwp-form" action="#" method="post">
<input type="hidden" name="source" value="home">
<label class="hp" aria-hidden="true">Leave this empty<input type="text" tabindex="-1" autocomplete="off" name="company"></label>
<div class="field"><label for="name">Your Name</label><input id="name" type="text" placeholder="e.g. Sam Lee" required autocomplete="name" name="name"></div>
<div class="field"><label for="phone">Phone</label><input id="phone" type="tel" placeholder="Your phone number" required autocomplete="tel" name="phone"></div>
<div class="field"><label for="email">Email</label><input id="email" type="email" placeholder="you@example.com" autocomplete="email" name="email"></div>
<div class="field"><label for="service">Service</label><select id="service" name="service" required><option value="" disabled selected>Select a service</option><option>Repairs</option></select></div>
<div class="field"><label for="msg">How can we help?</label><textarea id="msg" name="msg" placeholder="Tell us a little about the job"></textarea></div>
<button type="submit" class="btn">Send</button>
</form></body></html>'''


@unittest.skipUnless(shutil.which('node'), 'needs Node')
class FormLayout(unittest.TestCase):
    """The kit default on a form without a design passes form-layout.mjs; the same form unstyled fails it."""

    def check(self, css):
        tmp = tempfile.mkdtemp(prefix='form-')
        page = os.path.join(tmp, 'form.html')
        with open(page, 'w', encoding='utf-8') as fh:
            fh.write(FORM.format(css=css))
        r = subprocess.run(['node', path('scripts/report/form-layout.mjs'), page], capture_output=True, text=True,
                           timeout=180)
        shutil.rmtree(tmp, ignore_errors=True)
        if 'Playwright not found' in r.stdout + r.stderr:
            self.skipTest('needs Playwright')
        return r

    def test_default_layout_passes_and_unstyled_fails(self):
        with open(path('assets/theme/assets/form-default.css'), encoding='utf-8') as fh:
            r = self.check(fh.read())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.startswith('OK form-layout:'), r.stdout)
        self.assertIn('1280px 5 fields, 2 per row', r.stdout)
        self.assertIn('390px 5 fields, 1 per row', r.stdout)
        bad = self.check('')
        self.assertEqual(bad.returncode, 1, bad.stdout + bad.stderr)
        self.assertTrue(bad.stdout.startswith('FAIL form-layout:'), bad.stdout)

    def test_fixture_matches_the_seeded_form(self):
        with open(path('assets/seed/quote-form.txt'), encoding='utf-8') as fh:
            seed = fh.read()
        self.assertEqual(re.findall(r'id:(\w+)', seed), re.findall(r'<div class="field"><label for="(\w+)"', FORM))


if __name__ == '__main__':
    unittest.main()
