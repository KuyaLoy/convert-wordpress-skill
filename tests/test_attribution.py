"""0.9.9: form attribution on every lead form: browser capture, server checks, the email block, the portal fields
and generate_lead."""
import json
import shutil
import subprocess
import unittest

from helpers import path
from test_theme_kit import FORMS, INC, MAIL, PORTAL, PORTAL_STUBS, php

ATTR = INC + 'forms-attribution.php'
SRC = INC + 'forms-lead-source.php'
CORE = [(ATTR, 'kitwp_attribution_fields'), (ATTR, 'kitwp_attribution_touch'), (ATTR, 'kitwp_attribution_url'),
        (ATTR, 'kitwp_attribution_clean'), (SRC, 'kitwp_attribution_visits'), (SRC, 'kitwp_attribution_source'),
        (SRC, 'kitwp_attribution_rows'), (SRC, 'kitwp_attribution_table'),
        (SRC, 'kitwp_attribution_title_colours')]
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
function kitwp_lead_data( $s ) { return [ 'page' => $GLOBALS['page'] ?? '' ]; }
function kitwp_lead_extras( $l ) { return []; }
'''


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class EmailBlock(unittest.TestCase):
    def tag(self, posted, html=True, page='https://example.org/booking/'):
        body = (f'$GLOBALS["posted"] = json_decode( {json.dumps(json.dumps(posted))}, true ); $GLOBALS["page"] = '
                f'{json.dumps(page)}; echo json_encode( kitwp_lead_special_tags( null, "_kitk_source", '
                f'{"true" if html else "false"} ) );')
        return php(CORE + [(MAIL, 'kitwp_lead_special_tags'), (MAIL, 'kitwp_mail_h')], body, MAIL_STUBS)

    def rows(self, out):
        """The table as (label, cell text) pairs."""
        import re
        cells = re.findall(r'<tr>(.*?)</tr>', out)
        return [tuple(re.sub(r'<br>', ' | ', re.sub(r'<(?!br)[^>]+>', '', c)).strip()
                      for c in re.findall(r'<td[^>]*>(.*?)</td>', row)) for row in cells]

    def test_direct_first_visit_as_the_existing_build_shows_it(self):
        out = self.tag({'first_landing_page': 'https://example.org/', 'first_seen': '2026-11-23 09:45'})
        self.assertIn('background-color:#123456;', out)  # the title row in the email's brand colour
        self.assertEqual(self.rows(out), [
            ('Lead source',),
            ('First visit', 'Direct (typed in, bookmark or no source) | Landing page: https://example.org/ | '
                            'When: 2026-11-23 09:45 UTC'),
            ('Form sent from', 'https://example.org/booking/')])
        self.assertIn('<b>Direct (typed in, bookmark or no source)</b>', out)

    def test_paid_click_without_tags_and_a_google_search(self):
        out = self.tag({'gclid': 'G1', 'landing_page': 'https://example.org/offer/', 'last_seen': '2026-11-23 10:00',
                        'first_referrer': 'https://www.google.com/search', 'first_landing_page': 'https://example.org/',
                        'first_seen': '2026-11-01 08:00'})
        first, latest = self.rows(out)[1:3]
        self.assertEqual(first[0], 'First visit')
        self.assertTrue(first[1].startswith('Google search | From: https://www.google.com/search'), first)
        self.assertEqual(latest, ('Latest campaign visit', 'Google Ads click | gclid: G1 | Landing page: '
                                  'https://example.org/offer/ | When: 2026-11-23 10:00 UTC'))

    def test_tags_words_and_escaping(self):
        out = self.tag(dict(PAID, utm_campaign='<b>spring</b>', utm_term='plumber', utm_content='ad 2',
                            last_seen='2026-11-23 10:00'))
        latest = dict(r for r in self.rows(out) if len(r) == 2)['Latest campaign visit']
        self.assertTrue(latest.startswith('google / cpc | Campaign: &lt;b&gt;spring&lt;/b&gt; | Keyword: plumber | '
                                          'Ad: ad 2 | gclid: Cj0KCQ-test | From: https://www.google.com/'), latest)
        self.assertIn('First visit', dict(r for r in self.rows(out) if len(r) == 2))
        self.assertNotIn('<p', out)

    def test_same_visit_shown_once_and_no_data(self):
        same = {'utm_source': 'bing', 'landing_page': 'https://example.org/', 'last_seen': '2026-11-23 10:00',
                'first_source': 'bing', 'first_landing_page': 'https://example.org/', 'first_seen': '2026-11-23 10:00'}
        labels = [r[0] for r in self.rows(self.tag(same))]
        self.assertEqual(labels, ['Lead source', 'First visit', 'Form sent from'])
        none = self.rows(self.tag({}))
        self.assertEqual(none[1], ("Not recorded (the visitor&#039;s browser did not run the page script).",))
        self.assertEqual(none[2], ('Form sent from', 'https://example.org/booking/'))

    def test_plain_text(self):
        text = self.tag({'first_landing_page': 'https://example.org/', 'first_seen': '2026-11-23 09:45'}, html=False)
        self.assertEqual(text, 'Lead source\nFirst visit: Direct (typed in, bookmark or no source)\n'
                               '  Landing page: https://example.org/\n  When: 2026-11-23 09:45 UTC\n'
                               'Form sent from: https://example.org/booking/')

    def test_template_has_the_table_not_the_old_row(self):
        with open(path('assets/seed/lead-email.html'), encoding='utf-8') as fh:
            html = fh.read()
        self.assertIn('</table>\n[_kitk_source]\n', html)
        self.assertNotIn('Where this lead came from', html)


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class PortalFields(unittest.TestCase):
    FUNCS = [(PORTAL, 'kitwp_leads_tracking'), (PORTAL, 'kitwp_leads_allowed_fields'), (PORTAL, 'kitwp_leads_send'),
             (PORTAL, 'kitwp_leads_settings'),
             (FORMS, 'kitwp_lead_fields')] + CORE[:4]

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
        self.assertRegex(filled['first_seen'], r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$')  # UTC
        self.assertEqual(filled['first_seen'], filled['last_seen'])  # one visit: first and latest are the same
        self.assertEqual(later['utm_source'], 'google')  # the visit keeps its campaign on later pages
        self.assertEqual(later['first_source'], 'google')
        self.assertEqual(thanks, [{'event': 'generate_lead', 'form_name': 'Quote form', 'lead_source': 'google',
                                   'lead_medium': 'cpc'}])
        self.assertEqual(refresh, [])  # a refresh pushes nothing


if __name__ == '__main__':
    unittest.main()


CONSENT_HARNESS = r'''
const fs = require('fs'), vm = require('vm');
const code = fs.readFileSync(process.argv[process.argv.length - 1], 'utf8');
function store() { const m = new Map(); return { m, getItem: (k) => (m.has(k) ? m.get(k) : null),
  setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) }; }
function cm(kind, state) { return { 0: 'consent', 1: kind, 2: { ad_storage: state, analytics_storage: state } }; }
function visit(local, session, mode, dataLayer, after) {
  const handlers = {};
  const window = { location: new URL('https://example.org/?utm_source=google&utm_medium=cpc&gclid=G1'),
    sessionStorage: session, localStorage: local, dataLayer,
    kitwpAttributionConfig: { days: '90', consent: mode, thankYou: 'https://example.org/thank-you/' } };
  const document = { referrer: '', readyState: 'complete', forms: [], createElement: () => ({}),
    addEventListener: (t, f) => { handlers[t] = f; } };
  vm.runInNewContext(code, { window, document, URL, URLSearchParams, Date, JSON, Object, Array, parseInt, isNaN });
  if (after) after(window, handlers);
  return { stored: local.m.has('kitwp_attr_first'), visit: session.m.has('kitwp_attr_first'),
           fields: window.kitwpAttribution() };
}
const out = {};
out.none = visit(store(), store(), 'auto', []);
const L = store();
out.pending = visit(L, store(), 'auto', [cm('default', 'denied')]);
out.accepted = visit(L, store(), 'auto', [cm('default', 'denied'), cm('update', 'granted')]);
out.declined = visit(L, store(), 'auto', [cm('default', 'denied'), cm('update', 'denied')]);
const B = store();
out.banner_wait = visit(B, store(), 'banner', []);
out.banner_yes = visit(B, store(), 'banner', [], (w) => w.kitwpConsent(true));
out.banner_no = visit(B, store(), 'banner', [], (w, h) => h['kitwp:consent']({ detail: false }));
console.log(JSON.stringify(out));
'''


@unittest.skipUnless(shutil.which('node'), 'needs Node')
class Consent(unittest.TestCase):
    """With a consent banner the first visit is stored only after an accept; a decline removes it."""

    def test_each_case(self):
        r = subprocess.run(['node', '-e', CONSENT_HARNESS, path('assets/theme/assets/attribution.js')],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        got = json.loads(r.stdout)
        self.assertTrue(got['none']['stored'])  # no banner: as before
        self.assertFalse(got['pending']['stored'])  # banner, no choice yet: this visit only
        self.assertTrue(got['pending']['visit'])
        self.assertTrue(got['accepted']['stored'])
        self.assertFalse(got['declined']['stored'])  # declined after an accept: the stored first visit goes
        self.assertFalse(got['banner_wait']['stored'])
        self.assertTrue(got['banner_yes']['stored'])
        self.assertFalse(got['banner_no']['stored'])
        for case in got.values():  # the form still gets this visit's values in every case
            self.assertEqual((case['fields']['utm_source'], case['fields']['gclid']), ('google', 'G1'))


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class TitleColours(unittest.TestCase):
    """The title row takes the email's brand colour; its text is black or white, whichever reads better."""

    def test_contrast(self):
        body = ('echo json_encode( array_map( "kitwp_attribution_title_colours", [ "#fef151", "#1F4E79", "fff", '
                '"#00a0e0", "nonsense", "" ] ) );')
        got = php([(SRC, 'kitwp_attribution_title_colours')], body)
        self.assertEqual(got, [['#fef151', '#1a1a1a'], ['#1f4e79', '#ffffff'], ['#ffffff', '#1a1a1a'],
                               ['#00a0e0', '#1a1a1a'], ['#28292D', '#ffffff'], ['#28292D', '#ffffff']])
