"""0.9.9: form attribution on every lead form: browser capture, server checks, the email block, the portal fields
and generate_lead."""
import json
import shutil
import subprocess
import unittest

from helpers import path
from test_theme_kit import FORMS, INC, MAIL, PORTAL, PORTAL_STUBS, php

ATTR = INC + 'forms-attribution.php'
CORE = [(ATTR, 'kitwp_attribution_fields'), (ATTR, 'kitwp_attribution_url'), (ATTR, 'kitwp_attribution_clean'),
        (ATTR, 'kitwp_attribution_lines')]
PAID = {'utm_source': 'google', 'utm_medium': 'cpc', 'utm_campaign': 'spring', 'gclid': 'Cj0KCQ-test',
        'landing_page': 'https://example.org/offer/?email=a@b.example', 'referrer': 'https://www.google.com/',
        'first_source': 'newsletter', 'first_medium': 'email', 'first_seen': '2026-11-01',
        'first_landing_page': 'https://example.org/'}


def clean(posted, referer=''):
    return php(CORE, f'echo json_encode( kitwp_attribution_clean( json_decode( {json.dumps(json.dumps(posted))}, '
                     f'true ), {json.dumps(referer)} ) );')


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class ServerChecks(unittest.TestCase):
    def test_allow_list_caps_and_addresses(self):
        got = clean(dict(PAID, utm_term='k' * 900, injected='x', utm_content=['array'], first_seen='yesterday',
                         first_referrer='javascript:alert(1)', landing_page='https://example.org/' + 'p' * 900))
        self.assertEqual(len(got['utm_term']), 200)
        self.assertEqual(len(got['landing_page']), 500)
        for gone in ('injected', 'utm_content', 'first_seen', 'first_referrer'):
            self.assertNotIn(gone, got)
        self.assertEqual(clean(PAID)['landing_page'], 'https://example.org/offer/')  # the query (an email) goes

    def test_no_javascript_takes_the_form_page_address(self):
        got = clean({}, 'https://example.org/contact/?utm_source=bing&utm_medium=cpc&msclkid=abc&name=Sam')
        self.assertEqual((got['utm_source'], got['msclkid'], got['landing_page']),
                         ('bing', 'abc', 'https://example.org/contact/'))
        self.assertNotIn('name', got)
        self.assertEqual(clean({'utm_source': 'x'}, 'https://example.org/?utm_source=y')['utm_source'], 'x')

    def test_posted_filter_replaces_raw_values(self):
        body = ('$_SERVER = []; echo json_encode( kitwp_attribution_posted( [ "your-name" => "Sam", '
                '"utm_source" => " google ", "utm_term" => str_repeat( "t", 300 ), "gclid" => [ "x" ] ] ) );')
        got = php(CORE + [(ATTR, 'kitwp_attribution_posted')], body)
        self.assertEqual((got['your-name'], got['utm_source'], len(got['utm_term'])), ('Sam', 'google', 200))
        self.assertNotIn('gclid', got)


MAIL_STUBS = r'''
const KITWP_BRAND_COLOUR = '#123456';
class WPCF7_Submission {
	public static function get_instance() { return new self(); }
	public function get_posted_data( $name = '' ) { return '' === $name ? $GLOBALS['posted'] : ( $GLOBALS['posted'][ $name ] ?? null ); }
}
function kitwp_lead_fields() { return []; }
function kitwp_lead_data( $s ) { return []; }
function kitwp_lead_extras( $l ) { return []; }
'''


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class EmailBlock(unittest.TestCase):
    def tag(self, posted, html=True):
        body = (f'$GLOBALS["posted"] = json_decode( {json.dumps(json.dumps(posted))}, true ); echo json_encode( '
                f'kitwp_lead_special_tags( null, "_kitk_source", {"true" if html else "false"} ) );')
        return php(CORE + [(MAIL, 'kitwp_lead_special_tags'), (MAIL, 'kitwp_mail_h')], body, MAIL_STUBS)

    def test_paid_lead_in_the_email(self):
        out = self.tag(dict(PAID, utm_campaign='<b>spring</b>'))
        self.assertIn('Source / medium: google / cpc<br>', out)
        self.assertIn('Campaign: &lt;b&gt;spring&lt;/b&gt;', out)
        self.assertIn('Ad click: Google Ads (gclid)', out)
        self.assertIn('Landing page: https://example.org/offer/', out)
        self.assertIn('First visit: 2026-11-01, newsletter / email, https://example.org/', out)
        self.assertNotIn('Direct', out)
        self.assertNotIn('<p', out)
        self.assertIn('\n', self.tag(PAID, html=False))

    def test_direct_lead(self):
        out = self.tag({'landing_page': 'https://example.org/', 'first_seen': '2026-11-20'})
        self.assertTrue(out.startswith('Direct (no campaign, ad click or other site)<br>'), out)
        self.assertIn('First visit: 2026-11-20, direct', out)
        self.assertEqual(self.tag({}), 'Direct (no campaign, ad click or other site)')

    def test_template_has_the_row(self):
        with open(path('assets/seed/lead-email.html'), encoding='utf-8') as fh:
            self.assertIn('Where this lead came from:', fh.read())


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class PortalFields(unittest.TestCase):
    FUNCS = [(PORTAL, 'kitwp_leads_tracking'), (PORTAL, 'kitwp_leads_allowed_fields'), (PORTAL, 'kitwp_leads_send'),
             (FORMS, 'kitwp_lead_fields')] + CORE[:3]

    def test_attribution_goes_to_the_portal(self):
        posted = dict(PAID, **{'your-name': 'Sam', 'utm_term': 'x' * 400})
        body = (f'$_SERVER = [ "REMOTE_ADDR" => "8.8.4.4" ]; $GLOBALS["posted"] = json_decode( '
                f'{json.dumps(json.dumps(posted))}, true ); kitwp_leads_send( new Kit_Form() ); '
                f'echo json_encode( $GLOBALS["posts"] );')
        lead = php(self.FUNCS, body, PORTAL_STUBS)[0]
        self.assertEqual((lead['utm_source'], lead['utm_medium'], lead['gclid']), ('google', 'cpc', 'Cj0KCQ-test'))
        self.assertEqual(lead['landing_page'], 'https://example.org/offer/')
        self.assertEqual((lead['first_source'], lead['first_seen']), ('newsletter', '2026-11-01'))
        self.assertEqual(len(lead['utm_term']), 200)
        self.assertEqual(lead['your-name'], 'Sam')


JS_HARNESS = r'''
const fs = require('fs'), vm = require('vm');
const code = fs.readFileSync(process.argv[process.argv.length - 1], 'utf8');
function store() { const m = new Map(); return { getItem: (k) => (m.has(k) ? m.get(k) : null),
  setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) }; }
const session = store(), local = store(), out = [];
function load(url, referrer) {
  const handlers = {}, inputs = [];
  const form = { inputs, attrs: { 'data-form-name': 'Quote form' },
    getAttribute: (n) => form.attrs[n] || null,
    querySelector: (sel) => sel === 'input[name="_wpcf7"]' ? {} :
      inputs.find((i) => sel === 'input[type="hidden"][name="' + i.name + '"]') || null,
    appendChild: (i) => inputs.push(i) };
  const window = { location: new URL(url), sessionStorage: session, localStorage: local,
    kitwpAttributionConfig: { days: '90', thankYou: 'https://example.org/thank-you/' } };
  const document = { referrer, readyState: 'complete', forms: [form],
    createElement: () => ({}), addEventListener: (t, f) => { handlers[t] = f; } };
  window.document = document;
  vm.runInNewContext(code, { window, document, URL, URLSearchParams, Date, JSON, Object, Array, parseInt, isNaN });
  return { window, form, handlers };
}
const a = load('https://example.org/offer/?utm_source=google&utm_medium=cpc&gclid=G1&email=a@b.example',
               'https://www.google.com/search?q=x');
out.push(Object.fromEntries(a.form.inputs.map((i) => [i.name, i.value])));
const b = load('https://example.org/contact/', 'https://example.org/offer/');
out.push(b.window.kitwpAttribution());
b.handlers.submit({ target: b.form });
const t = load('https://example.org/thank-you/', 'https://example.org/contact/');
out.push(t.window.dataLayer || []);
const t2 = load('https://example.org/thank-you/', '');
out.push(t2.window.dataLayer || []);
console.log(JSON.stringify(out));
'''


@unittest.skipUnless(shutil.which('node'), 'needs Node')
class BrowserCapture(unittest.TestCase):
    def test_capture_fill_and_generate_lead(self):
        r = subprocess.run(['node', '-e', JS_HARNESS, path('assets/theme/assets/attribution.js')], capture_output=True,
                           text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        filled, later, thanks, refresh = json.loads(r.stdout)
        self.assertEqual((filled['utm_source'], filled['utm_medium'], filled['gclid']), ('google', 'cpc', 'G1'))
        self.assertEqual(filled['landing_page'], 'https://example.org/offer/')  # no query: the email stays out
        self.assertEqual(filled['referrer'], 'https://www.google.com/search')
        self.assertNotIn('email', filled)
        self.assertRegex(filled['first_seen'], r'^\d{4}-\d{2}-\d{2}$')
        self.assertEqual(later['utm_source'], 'google')  # the visit keeps its campaign on later pages
        self.assertEqual(later['first_source'], 'google')
        self.assertEqual(thanks, [{'event': 'generate_lead', 'form_name': 'Quote form', 'lead_source': 'google',
                                   'lead_medium': 'cpc'}])
        self.assertEqual(refresh, [])  # a refresh pushes nothing


if __name__ == '__main__':
    unittest.main()
