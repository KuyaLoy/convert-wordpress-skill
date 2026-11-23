"""The theme kit's form, security and clean-up code, run with small WordPress stubs (functions taken by name).

Each class covers one thing a real build found wrong in code that came from the kit.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

from helpers import path
from test_theme_php import php_function, php_str, run_php

INC = 'assets/theme/includes/'
FORMS = INC + 'forms.php'
SPAM = INC + 'forms-spam.php'
CONTROLS = INC + 'forms-controls.php'
MAIL = INC + 'forms-mail.php'
PORTAL = INC + 'forms-portal.php'

BASE = r'''
error_reporting( E_ALL );
set_error_handler( function ( $no, $str ) { fwrite( STDERR, "PHP: $str\n" ); exit( 3 ); } );
const DAY_IN_SECONDS = 86400;
function wp_unslash( $v ) { return $v; }
function sanitize_text_field( $v ) { return trim( (string) $v ); }
function esc_html( $t ) { return htmlspecialchars( (string) $t, ENT_QUOTES, 'UTF-8' ); }
function esc_attr( $t ) { return htmlspecialchars( (string) $t, ENT_QUOTES, 'UTF-8' ); }
function esc_url( $u ) { return (string) $u; }
function esc_url_raw( $u ) { return (string) $u; }
function __( $t ) { return $t; }
function esc_html__( $t ) { return esc_html( $t ); }
function apply_filters( $hook, $value ) { return $value; }
function wp_hash( $data ) { return hash_hmac( 'md5', $data, 'test-salt' ); }
function wp_strip_all_tags( $t ) { return trim( strip_tags( (string) $t ) ); }
function wp_parse_url( $url, $component = -1 ) { return parse_url( $url, $component ); }
function untrailingslashit( $s ) { return rtrim( (string) $s, '/\\' ); }
function wpcf7_flat_join( $input ) {
	$out   = [];
	$input = is_array( $input ) ? $input : [ $input ];
	array_walk_recursive( $input, function ( $v ) use ( &$out ) { if ( is_scalar( $v ) ) { $out[] = trim( (string) $v ); } } );
	return implode( ', ', $out );
}
function add_query_arg( $key, $value, $url ) {
	$p = explode( '?', $url, 2 );
	parse_str( $p[1] ?? '', $q );
	$q[ $key ] = $value;
	return $p[0] . '?' . http_build_query( $q );
}
'''


def php(functions, body, stubs=''):
    """Run kit functions with the base stubs; any PHP notice or warning fails the run. Returns the JSON printed."""
    code = '<?php\n' + BASE + stubs + '\n' + ''.join(php_function(f, n) for f, n in functions) + '\n' + body
    with tempfile.NamedTemporaryFile('w', suffix='.php', delete=False, encoding='utf-8') as fh:
        fh.write(code)
    try:
        out = subprocess.run(['php', fh.name], capture_output=True, text=True, timeout=60)
    finally:
        os.unlink(fh.name)
    if out.returncode or out.stderr.strip():
        raise AssertionError(out.stdout + out.stderr)
    return json.loads(out.stdout)


def read(rel):
    with open(path(rel), encoding='utf-8') as fh:
        return fh.read()


SUBMISSION = r'''
class WPCF7_Submission {
	public static $rest = false;
	public $log = [];
	public $posted = [];
	public static function is_restful() { return self::$rest; }
	public function get_spam_log() { return $this->log; }
	public function get_contact_form() { return true; }
	public function get_posted_data( $name = '' ) { return $this->posted[ $name ] ?? null; }
}
function kitwp_is_lead_form( $form ) { return (bool) $form; }
'''


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class SpamChecks(unittest.TestCase):
    """reCAPTCHA keys set: a post without JavaScript keeps its lead, bots still stop; the honeypot reads company[]."""

    def rescue(self, on):
        body = r'''
$case = function ( $log, $post, $posted = [], $rest = false, $flag = false, $spam = true ) {
	$_POST = $post;
	WPCF7_Submission::$rest = $rest;
	$GLOBALS['kitwp_lead_honeypot'] = $flag;
	$s = new WPCF7_Submission();
	$s->log = $log;
	$s->posted = $posted;
	return kitwp_recaptcha_no_js( $spam, $s );
};
$rc  = [ [ 'agent' => 'recaptcha', 'reason' => 'reCAPTCHA response token is empty.' ] ];
$ok  = [ '_wpcf7_recaptcha_response' => '', '_wpcf7_kitwp_ts' => kitwp_form_stamp( time() - 10 ) ];
$with = function ( $extra ) use ( $ok ) { return array_merge( $ok, $extra ); };
echo json_encode( [
	'kept'        => $case( $rc, $ok ),
	'no_stamp'    => $case( $rc, [ '_wpcf7_recaptcha_response' => '' ] ),
	'too_fast'    => $case( $rc, $with( [ '_wpcf7_kitwp_ts' => kitwp_form_stamp( time() - 1 ) ] ) ),
	'too_old'     => $case( $rc, $with( [ '_wpcf7_kitwp_ts' => kitwp_form_stamp( time() - 8 * DAY_IN_SECONDS ) ] ) ),
	'forged'      => $case( $rc, $with( [ '_wpcf7_kitwp_ts' => ( time() - 10 ) . '.0123456789abcdef0123' ] ) ),
	'low_score'   => $case( $rc, $with( [ '_wpcf7_recaptcha_response' => 'a-token' ] ) ),
	'other_check' => $case( array_merge( $rc, [ [ 'agent' => 'wpcf7', 'reason' => 'nonce' ] ] ), $ok ),
	'no_log'      => $case( [], $ok ),
	'rest'        => $case( $rc, $ok, [], true ),
	'honeypot'    => $case( $rc, $ok, [ 'company' => 'Acme' ] ),
	'flagged'     => $case( $rc, $ok, [], false, true ),
	'not_spam'    => $case( $rc, $ok, [], false, false, false ),
] );'''
        return php([(SPAM, 'kitwp_form_stamp'), (SPAM, 'kitwp_form_stamp_ok'), (SPAM, 'kitwp_recaptcha_no_js')],
                   body, 'const KITWP_NOJS_LEADS = ' + ('true' if on else 'false') + ";\n" + SUBMISSION)

    def test_no_js_post_stays_spam_by_default(self):
        got = self.rescue(False)
        self.assertIs(got.pop('not_spam'), False)
        self.assertEqual({k: v for k, v in got.items() if v is not True}, {})
        self.assertIn('const KITWP_NOJS_LEADS = false;', read(INC + 'config.php'))

    def test_opt_in_keeps_a_no_js_post_only_when_recaptcha_was_the_one_reason(self):
        got = self.rescue(True)
        self.assertIs(got.pop('kept'), False)
        self.assertIs(got.pop('not_spam'), False)
        self.assertEqual({k: v for k, v in got.items() if v is not True}, {})

    def test_honeypot_reads_an_array_without_a_warning(self):
        body = r'''
$s = new WPCF7_Submission();
$out = [];
foreach ( [ 'Acme', [ '', 'x' ], [ [ 'x' ] ], [ '' ], '', null ] as $company ) {
	$GLOBALS['kitwp_lead_honeypot'] = false;
	$s->posted = [ 'company' => $company ];
	$out[] = kitwp_lead_honeypot( false, $s );
}
echo json_encode( $out );'''
        got = php([(SPAM, 'kitwp_lead_honeypot')], body, SUBMISSION)
        self.assertEqual(got, [True, True, True, False, False, False])

    def test_stamp_is_a_cf7_hidden_field_for_lead_forms(self):
        text = read(SPAM)
        self.assertIn("add_filter( 'wpcf7_form_hidden_fields', 'kitwp_form_stamp_field' );", text)
        self.assertIn("add_filter( 'wpcf7_spam', 'kitwp_recaptcha_no_js', 9, 2 );", text)
        self.assertIn("$fields['_wpcf7_kitwp_ts']", text)


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class FailedNote(unittest.TestCase):
    """CF7's response after a failed post stays visible (role=alert), with the phone when CF7 stopped the post."""

    STUBS = r'''
const KITWP_FORM_CLASS = 'lead-form';
function kitwp_phone() { return $GLOBALS['phone'] ?? '555 0100'; }
function kitwp_tel() { return $GLOBALS['tel'] ?? '+15550100'; }
'''
    HTML = ('<div class="wpcf7 no-js"><div class="screen-reader-response"><p role="status"></p></div>'
            '<form action="/x/#wpcf7-f1-o1" method="post" class="wpcf7-form spam">'
            '<fieldset class="hidden-fields-container"><input type="hidden" name="_wpcf7" value="1"></fieldset>'
            '<p><input name="name"></p>\n<div class="wpcf7-response-output" aria-hidden="true">%s</div></form></div>')

    def clean(self, cases):
        body = 'echo json_encode( [ ' + ', '.join(
            f'kitwp_cf7_clean( {php_str(self.HTML % text)}, "", {php_str(status)} )' for text, status in cases) + ' ] );'
        return php([(CONTROLS, 'kitwp_cf7_clean'), (CONTROLS, 'kitwp_lead_failed_note')], body, self.STUBS)

    def test_notes(self):
        spam, phone_tag, invalid, empty = self.clean([
            ('There&#039;s been an error.', 'spam'),
            ('Sorry, call {phone} now.', 'aborted'),
            ('One or more fields have an error.', 'validation_failed'),
            ('', ''),
        ])
        note = ('<p class="form-note" role="alert">There&#039;s been an error. Or call '
                '<a href="tel:+15550100">555 0100</a>.</p>')
        self.assertIn(note, spam)
        self.assertTrue(spam.startswith('<form class="lead-form" action="" method="post">'))
        self.assertNotIn('wpcf7-response-output', spam)
        self.assertIn('Sorry, call <a href="tel:+15550100">555 0100</a> now.</p>', phone_tag)
        self.assertIn('<p class="form-note" role="alert">One or more fields have an error.</p>', invalid)
        self.assertNotIn('form-note', empty)


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class RecaptchaScript(unittest.TestCase):
    """The token code is a theme file versioned by its date; the site key goes in as data, not as inline code."""

    def enqueue(self, lazy):
        stubs = r'''
const KITWP_FORM_CLASS = 'lead-form';
const KITWP_CHAT_SELECTOR = '#chat';
define( 'KITWP_RECAPTCHA_LAZY', %s );
$GLOBALS['calls'] = [];
function kitwp_recaptcha_sitekey() { return 'site-key'; }
function get_stylesheet_directory() { return %s; }
function kitwp_asset( $p ) { return 'https://example.test/theme/' . $p; }
function wp_script_is( $h, $what ) { return true; }
function wp_scripts() { return (object) [ 'registered' => [ 'google-recaptcha' => (object) [ 'src' => 'https://www.google.com/recaptcha/api.js?render=site-key' ] ] ]; }
function wp_enqueue_script( ...$a ) { $GLOBALS['calls']['enqueue'] = $a; }
function wp_localize_script( ...$a ) { $GLOBALS['calls']['localize'] = $a; }
function wp_dequeue_script( $h ) { $GLOBALS['calls']['dequeue'] = $h; }
function wp_add_inline_script( ...$a ) { $GLOBALS['calls']['inline'] = $a; }
''' % ('true' if lazy else 'false', php_str(path('assets/theme').replace('\\', '/')))
        return php([(SPAM, 'kitwp_recaptcha_submit_script')],
                   'kitwp_recaptcha_submit_script(); echo json_encode( $GLOBALS["calls"] );', stubs)

    def test_enqueued_as_a_file_with_data(self):
        mtime = str(int(os.path.getmtime(path('assets/theme/assets/recaptcha.js'))))
        got = self.enqueue(False)
        self.assertNotIn('inline', got)
        handle, src, deps, ver, args = got['enqueue']
        self.assertEqual((handle, src, deps, ver), ('kitwp-recaptcha', 'https://example.test/theme/assets/recaptcha.js',
                                                    ['wpcf7-recaptcha'], mtime))
        self.assertEqual(args, {'in_footer': True})
        self.assertEqual(got['localize'][:2], ['kitwp-recaptcha', 'kitwpRecaptchaConfig'])
        self.assertEqual(got['localize'][2]['key'], 'site-key')
        self.assertEqual(got['localize'][2]['lazy'], '')
        lazy = self.enqueue(True)
        self.assertEqual(lazy['dequeue'], 'wpcf7-recaptcha')
        self.assertEqual(lazy['enqueue'][2], [])
        self.assertEqual(lazy['localize'][2]['warm'], 'form.lead-form,#chat')
        self.assertIn('google.com/recaptcha/api.js', lazy['localize'][2]['api'])

    def test_script_reads_the_data(self):
        js = read('assets/theme/assets/recaptcha.js')
        self.assertIn('window.kitwpRecaptchaConfig', js)
        self.assertIn('_wpcf7_recaptcha_response', js)
        self.assertNotIn('grecaptcha', read(SPAM))
        if shutil.which('node'):
            out = subprocess.run(['node', '--check', path('assets/theme/assets/recaptcha.js')], capture_output=True,
                                 text=True)
            self.assertEqual(out.returncode, 0, out.stderr)


PORTAL_STUBS = r'''
const KITWP_LEADS_PREFIX = 'TEST_LEADS';
define( 'TEST_LEADS_ENDPOINT', 'https://portal.example.org/ingest/demo' );
define( 'TEST_LEADS_KEY', 'lk_test_dummy_key' );
$GLOBALS['posts'] = [];
function kitwp_is_lead_form( $form ) { return true; }
function wp_get_environment_type() { return 'production'; }
function wp_generate_uuid4() { return 'uuid-1'; }
function wp_json_encode( $v ) { return json_encode( $v ); }
function wp_get_referer() { return ''; }
function is_wp_error( $v ) { return false; }
function wp_remote_retrieve_response_code( $r ) { return 202; }
function wp_remote_post( $url, $args ) { $GLOBALS['posts'][] = json_decode( $args['body'], true ); return []; }
class Kit_Tag { public $name; public $basetype; public function __construct( $n, $b ) { $this->name = $n; $this->basetype = $b; } }
class Kit_Form {
	public function title() { return 'Quote'; }
	public function scan_form_tags() { return [ new Kit_Tag( 'your-name', 'text' ), new Kit_Tag( 'notes', 'textarea' ), new Kit_Tag( 'company', 'text' ) ]; }
}
class WPCF7_Submission {
	public static function get_instance() { return new self(); }
	public function get_posted_data( $name = '' ) { $d = $GLOBALS['posted']; return '' === $name ? $d : ( $d[ $name ] ?? null ); }
	public function uploaded_files() { return []; }
	public function get_meta( $k ) { return 'https://example.org/contact/'; }
}
'''


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class Portal(unittest.TestCase):
    """The portal gets a validated IP and only the form's own fields, capped in length."""

    FUNCS = [(PORTAL, 'kitwp_leads_tracking'), (PORTAL, 'kitwp_leads_allowed_fields'), (PORTAL, 'kitwp_leads_send'),
             (FORMS, 'kitwp_lead_fields'), (INC + 'forms-attribution.php', 'kitwp_attribution_fields'),
             (INC + 'forms-attribution.php', 'kitwp_attribution_url'),
             (INC + 'forms-attribution.php', 'kitwp_attribution_clean')]

    def test_ip_only_from_a_valid_public_proxy_header(self):
        body = r'''
$out = [];
foreach ( [
	[ 'HTTP_CF_CONNECTING_IP' => '10.0.0.1', 'HTTP_X_FORWARDED_FOR' => '8.8.8.8, 10.0.0.2', 'REMOTE_ADDR' => '172.16.0.9' ],
	[ 'HTTP_CF_CONNECTING_IP' => '1.1.1.1', 'REMOTE_ADDR' => '172.16.0.9' ],
	[ 'HTTP_CF_CONNECTING_IP' => '<script>', 'HTTP_X_FORWARDED_FOR' => '127.0.0.1', 'REMOTE_ADDR' => '192.168.1.5' ],
	[ 'HTTP_X_FORWARDED_FOR' => 'evil', 'REMOTE_ADDR' => 'not-an-ip' ],
] as $server ) {
	$_SERVER = $server;
	$out[] = kitwp_leads_tracking( new WPCF7_Submission() )['ip_address'];
}
echo json_encode( $out );'''
        got = php(self.FUNCS, '$GLOBALS["posted"] = [];\n' + body, PORTAL_STUBS)
        self.assertEqual(got, ['8.8.8.8', '1.1.1.1', '192.168.1.5', ''])

    def test_only_form_fields_and_capped(self):
        body = r'''
$_SERVER = [ 'REMOTE_ADDR' => '8.8.4.4' ];
$GLOBALS['posted'] = [ 'your-name' => str_repeat( 'n', 900 ), 'notes' => str_repeat( 'm', 6000 ), 'phone' => '0400',
	'company' => 'bot', 'injected' => 'x', 'admin' => [ 'a' ], '_wpcf7' => '5' ];
kitwp_leads_send( new Kit_Form() );
echo json_encode( $GLOBALS['posts'] );'''
        got = php(self.FUNCS, body, PORTAL_STUBS)
        self.assertEqual(len(got), 1)
        lead = got[0]
        self.assertEqual(len(lead['your-name']), 500)
        self.assertEqual(len(lead['notes']), 5000)
        self.assertEqual(lead['phone'], '0400')
        for key in ('company', 'injected', 'admin', '_wpcf7'):
            self.assertNotIn(key, lead)
        self.assertEqual(lead['ip_address'], '8.8.4.4')


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class EmailLogo(unittest.TestCase):
    """No email logo set and no theme file: no broken image, the alt text shows instead."""

    def test_logo_fallback_only_when_the_file_exists(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        stubs = r'''
function kitwp_setting( $n ) { return null; }
function wp_get_attachment_url( $id ) { return false; }
function get_theme_file_path( $f ) { return %s . '/' . $f; }
function get_theme_file_uri( $f ) { return 'https://example.test/theme/' . $f; }
''' % php_str(tmp.replace('\\', '/'))
        body = r'''
$a = kitwp_email_logo_url();
mkdir( get_theme_file_path( 'assets/email' ), 0777, true );
touch( get_theme_file_path( 'assets/email/email-logo.png' ) );
echo json_encode( [ $a, kitwp_email_logo_url() ] );'''
        got = php([(MAIL, 'kitwp_email_logo_url')], body, stubs)
        self.assertEqual(got, ['', 'https://example.test/theme/assets/email/email-logo.png'])

    def test_empty_image_becomes_its_alt_text(self):
        html = ('<a href="https://example.com"><img src="" width="180" alt="Example Co" '
                'style="display:block;color:#ffffff;"></a><img src="https://example.com/b.png" alt="Badge">')
        body = 'echo json_encode( kitwp_mail_no_empty_img( [ "body" => ' + php_str(html) + ' ] )["body"] );'
        got = php([(MAIL, 'kitwp_mail_no_empty_img')], body)
        self.assertEqual(got, '<a href="https://example.com"><span style="display:block;color:#ffffff;">Example Co</span>'
                              '</a><img src="https://example.com/b.png" alt="Badge">')


class FileLayout(unittest.TestCase):
    """forms, seed, helpers and media split by job: every kit file is loaded once, no function twice, no file too long."""

    def kit_list(self):
        text = read('assets/theme/functions.php')
        block = re.search(r'\$kitwp_kit = \[(.*?)\];', text, re.S).group(1)
        return re.findall(r"'([\w-]+)'", block)

    def test_functions_php_loads_every_kit_file(self):
        names = self.kit_list()
        self.assertEqual(len(names), len(set(names)))
        files = sorted(os.path.basename(f)[:-4] for f in glob.glob(path(INC + '*.php')))
        self.assertEqual(sorted(names), files)
        self.assertEqual(names[0], 'config')
        self.assertLess(names.index('seed'), min(names.index(n) for n in names if n.startswith('seed-')))

    def test_no_duplicate_functions(self):
        seen = {}
        for f in glob.glob(path(INC + '*.php')):
            with open(f, encoding='utf-8') as fh:
                names = re.findall(r'^function (\w+)\(', fh.read(), re.M)
            for name in names:
                self.assertNotIn(name, seen, f'{name} in {seen.get(name)} and {f}')
                seen[name] = f

    def test_kit_files_are_short(self):
        for f in glob.glob(path(INC + '*.php')):
            with open(f, encoding='utf-8') as fh:
                self.assertLessEqual(len(fh.readlines()), 300, f)

    def test_each_job_in_its_file(self):
        where = {
            FORMS: ['kitwp_cf7_form_id', 'kitwp_quote_form_html', 'kitwp_lead_redirect', 'kitwp_lead_fields',
                    'kitwp_chat_widget'],
            CONTROLS: ['kitwp_cf7_clean', 'kitwp_cf7_control', 'kitwp_cf7_register_controls'],
            SPAM: ['kitwp_lead_honeypot', 'kitwp_recaptcha_sitekey', 'kitwp_recaptcha_no_js'],
            MAIL: ['kitwp_lead_special_tags', 'kitwp_mail_envelope', 'kitwp_email_logo_url'],
            INC + 'forms-local-mail.php': ['kitwp_local_mail_capture', 'kitwp_local_mail_to_file'],
            PORTAL: ['kitwp_leads_send', 'kitwp_leads_tracking'],
            INC + 'seed-forms.php': ['kitwp_seed_forms'],
            INC + 'seed-menus.php': ['kitwp_seed_menus'],
            INC + 'helpers-maps.php': ['kitwp_map_src', 'kitwp_map_iframe', 'kitwp_iframe_src'],
            INC + 'media-svg.php': ['kitwp_svg_clean', 'kitwp_inline_svg', 'kitwp_svg_size'],
            INC + 'media.php': ['kitwp_img', 'kitwp_media_by_source'],
        }
        for f, names in where.items():
            for name in names:
                php_function(f, name)

    def test_seed_parts_stay_local_only(self):
        for f in glob.glob(path(INC + 'seed*.php')):
            with open(f, encoding='utf-8') as fh:
                self.assertIn("if ( 'local' !== wp_get_environment_type() ) {\n\treturn;\n}", fh.read(), f)


class AbspathGuard(unittest.TestCase):
    """A direct request to a theme PHP file stops at once instead of printing a fatal error with the server path."""

    def test_every_theme_php_file_has_the_guard_after_its_header(self):
        files = glob.glob(path('assets/theme/**/*.php'), recursive=True)
        self.assertGreater(len(files), 20)
        for f in files:
            with open(f, encoding='utf-8') as fh:
                text = fh.read()
            m = re.match(r"<\?php\n/\*\*.*?\n \*/\n\ndefined\( 'ABSPATH' \) \|\| exit;\n", text, re.S)
            self.assertTrue(m, f)

    @unittest.skipUnless(shutil.which('php'), 'needs PHP')
    def test_direct_run_prints_nothing(self):
        for rel in (FORMS, PORTAL, INC + 'helpers.php', 'assets/theme/template-parts/sections/lead-form.php'):
            out = subprocess.run(['php', path(rel)], capture_output=True, text=True, timeout=60)
            self.assertEqual((out.returncode, out.stdout, out.stderr), (0, '', ''), rel)


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class Security(unittest.TestCase):
    def test_svg_payloads_removed(self):
        svg = ('<svg xmlns="http://www.w3.org/2000/svg"/onload="alert(1)" viewBox="0 0 10 10">'
               '<a href="#x"><set attributeName="href" to="javascript:alert(2)"/></a>'
               '<animate attributeName="href" values="#a;java&#x09;script:alert(3)"/>'
               '<a xlink:href=javascript:alert(4)>x</a>'
               '<iframe src="javascript:alert(5)"></iframe><embed src="x.swf">'
               '<use href="data:image/svg+xml;base64,PHN2Zz4="/><image href="data:image/png;base64,iVBOR="/>'
               '<animate attributeName="x" from="0" to="10" values="0;10"/></svg>')
        got = run_php([(INC + 'media-svg.php', 'kitwp_svg_clean')], 'echo json_encode( kitwp_svg_clean( ' + php_str(svg) + ' ) );')
        for bad in ('onload', 'javascript', 'alert', 'iframe', 'embed', 'data:image/svg'):
            self.assertNotIn(bad, got.lower())
        self.assertIn('<a href="#x"><set attributeName="href"/></a>', got)
        self.assertIn('<image href="data:image/png;base64,iVBOR="/>', got)
        self.assertIn('<animate attributeName="x" from="0" to="10" values="0;10"/>', got)

    def test_map_host_must_be_google(self):
        body = 'echo json_encode( array_map( "kitwp_map_embed_url", ' + php_list([
            'https://google.evil.example/maps/embed?pb=1', 'https://www.google.com.evil.example/maps/embed?pb=1',
            'https://evilgoogle.com/maps/embed?pb=1', 'https://www.google.com/maps/embed?pb=1',
            'https://www.google.com.au/maps/embed?pb=1', 'https://maps.google.co.uk/maps/embed?pb=1',
            'https://www.google.de/maps/embed?pb=1']) + ' ) );'
        got = run_php([(INC + 'helpers-maps.php', 'kitwp_map_embed_url')], body)
        self.assertEqual(got[:3], ['', '', ''])
        self.assertTrue(all(got[3:]), got)

    def test_oembed_has_no_author(self):
        body = ('echo json_encode( kitwp_oembed_hide_author( [ "title" => "About", "author_name" => "admin", '
                '"author_url" => "https://example.com/author/admin/" ] ) );')
        self.assertEqual(php([(INC + 'cleanup.php', 'kitwp_oembed_hide_author')], body), {'title': 'About'})

    def test_json_ld_keeps_script_text_inside_the_block(self):
        text = 'x</script><script>alert(1)</script> & <!-- "q"'
        stubs = ('function wp_json_encode( $v, $f = 0 ) { return json_encode( $v, $f ); }\n'
                 'function kitwp_schema_blocks() { return [ [ "@type" => "Thing", "name" => ' + php_str(text) + ' ] ]; }\n')
        body = 'ob_start(); kitwp_schema_print(); echo json_encode( ob_get_clean() );'
        out = php([(INC + 'schema.php', 'kitwp_schema_print')], body, stubs)
        self.assertTrue(out.startswith('<script type="application/ld+json">') and out.endswith('</script>'))
        self.assertEqual(out.lower().count('</script'), 1)
        self.assertNotIn('<!--', out)
        inner = out[len('<script type="application/ld+json">'):-len('</script>')]
        self.assertEqual(json.loads(inner)['name'], text)


ROUTE_STUBS = r'''
define( 'KITWP_KEEP_BLOG', $GLOBALS['blog'] );
define( 'KITWP_SITE_SEARCH', false );
foreach ( [ 'is_attachment', 'is_search', 'is_category', 'is_tag', 'is_tax', 'is_date', 'is_author', 'is_paged',
	'is_feed', 'is_singular' ] as $kitwp_fn ) {
	eval( "function $kitwp_fn() { return ! empty( \$GLOBALS['q']['$kitwp_fn'] ); }" );
}
function get_query_var( $k ) { return $GLOBALS['q'][ $k ] ?? ''; }
function get_permalink() { return 'https://example.test' . ( $GLOBALS['q']['own'] ?? '/' ); }
function is_admin() { return false; }
'''


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class StarterRoutes(unittest.TestCase):
    """WordPress's own listings, feeds, attachments and other paths to a page answer 404 as on the static site."""

    def routes(self, blog, cases):
        body = ('$cases = json_decode( ' + php_str(json.dumps(cases)) + ', true );\n'
                'echo json_encode( array_map( function ( $c ) { $GLOBALS["q"] = $c[1]; '
                'return kitwp_is_starter_route( $c[0] ); }, $cases ) );')
        return php([(INC + 'cleanup.php', 'kitwp_is_starter_route')], body,
                   f"$GLOBALS['blog'] = {'true' if blog else 'false'};\n" + ROUTE_STUBS)

    CASES = [
        ['/category/news/', {'is_category': True}],
        ['/page/2/', {'is_paged': True}],
        ['/feed/', {'is_feed': True}],
        ['/2026/', {'is_date': True}],
        ['/search/x/', {'is_search': True}],
        ['/photo/', {'is_attachment': True, 'is_singular': True}],
        ['/home/', {'is_singular': True, 'pagename': 'home', 'own': '/'}],
        ['/About/', {'is_singular': True, 'pagename': 'about', 'own': '/about/'}],
        ['/about', {'is_singular': True, 'pagename': 'about', 'own': '/about/'}],
        ['/services/caf%C3%A9/', {'is_singular': True, 'pagename': 'services/café', 'own': '/services/caf%c3%a9/'}],
        ['/', {'is_singular': True}],
        ['/projects/', {}],
    ]

    def test_without_a_blog(self):
        self.assertEqual(self.routes(False, self.CASES), [True] * 8 + [False] * 4)

    def test_with_a_blog(self):
        self.assertEqual(self.routes(True, self.CASES), [False] * 4 + [True] * 4 + [False] * 4)

    def test_search_query_ignored_but_search_path_kept(self):
        stubs = "define( 'KITWP_SITE_SEARCH', false );\nfunction is_admin() { return false; }\n"
        body = r'''
$GLOBALS['wp'] = (object) [ 'matched_query' => '' ];
$a = kitwp_no_search( [ 's' => 'x', 'pagename' => 'about' ] );
$GLOBALS['wp']->matched_query = 's=x';
$b = kitwp_no_search( [ 's' => 'x' ] );
echo json_encode( [ $a, $b ] );'''
        self.assertEqual(php([(INC + 'cleanup.php', 'kitwp_no_search')], body, stubs),
                         [{'pagename': 'about'}, {'s': 'x'}])

    def test_hooks(self):
        text = read(INC + 'cleanup.php')
        for line in ("add_action( 'wp', 'kitwp_static_routes', -10001 );",
                     "add_filter( 'do_redirect_guess_404_permalink', '__return_false' );",
                     "add_filter( 'wpseo_debug_markers', '__return_false' );",
                     "add_filter( 'oembed_response_data', 'kitwp_oembed_hide_author' );"):
            self.assertIn(line, text)
        config = read(INC + 'config.php')
        self.assertIn("const KITWP_KEEP_BLOG = 'true' === '{{KEEP_BLOG}}';", config)
        self.assertIn("const KITWP_SITE_SEARCH = 'true' === '{{SITE_SEARCH}}';", config)


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class Head(unittest.TestCase):
    def test_favicon_ico_goes_to_the_icon_the_site_has(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        os.makedirs(os.path.join(tmp, 'assets', 'brand'))
        stubs = r'''
function has_site_icon() { return false; }
function get_stylesheet_directory() { return %s; }
function kitwp_asset( $p ) { return 'https://example.test/theme/' . $p; }
function wp_safe_redirect( $u ) { echo json_encode( $u ); }
''' % php_str(tmp.replace('\\', '/'))
        run = 'kitwp_favicon_ico(); echo json_encode( null );'
        self.assertIsNone(php([(INC + 'head.php', 'kitwp_favicon_ico')], run, stubs))
        open(os.path.join(tmp, 'assets', 'brand', 'icon.svg'), 'w').close()
        self.assertEqual(php([(INC + 'head.php', 'kitwp_favicon_ico')], run, stubs),
                         'https://example.test/theme/assets/brand/icon.svg')

    def test_no_blank_line_without_font_links(self):
        stubs = ("const KITWP_PRECONNECT_FONTS = false;\nconst KITWP_BRAND_COLOUR = '#123456';\n"
                 'function has_site_icon() { return true; }\n')
        fn = php_function(INC + 'head.php', 'kitwp_head_tags')
        for links, want in (('', ''), ('<link rel="stylesheet" href="https://fonts.example/x.css">',
                                       '<link rel="stylesheet" href="https://fonts.example/x.css">\n')):
            code = '<?php\n' + BASE + stubs + fn.replace('{{FONT_LINKS}}', links) + 'kitwp_head_tags();'
            with tempfile.NamedTemporaryFile('w', suffix='.php', delete=False, encoding='utf-8') as fh:
                fh.write(code)
            try:
                out = subprocess.run(['php', fh.name], capture_output=True, text=True, timeout=60)
            finally:
                os.unlink(fh.name)
            self.assertEqual(out.stdout, '<meta name="theme-color" content="#123456">\n' + want)

    def test_theme_assets_versioned_by_file_date(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        os.makedirs(os.path.join(tmp, 'js'))
        with open(os.path.join(tmp, 'js', 'script.min.js'), 'w') as fh:
            fh.write('1')
        mtime = str(int(os.path.getmtime(os.path.join(tmp, 'js', 'script.min.js'))))
        stubs = r'''
function get_stylesheet_directory_uri() { return 'https://example.test/wp-content/themes/t'; }
function get_stylesheet_directory() { return %s; }
''' % php_str(tmp.replace('\\', '/'))
        body = 'echo json_encode( [ ' + ', '.join(f'kitwp_asset_version( {php_str(u)}, "h" )' for u in (
            'https://example.test/wp-content/themes/t/js/script.min.js?ver=0.1.0',
            'https://example.test/wp-content/themes/t/js/missing.js?ver=0.1.0',
            'https://cdn.example.org/lib.js?ver=2')) + ' ] );'
        got = php([(INC + 'head.php', 'kitwp_asset_version')], body, stubs)
        self.assertEqual(got, ['https://example.test/wp-content/themes/t/js/script.min.js?ver=' + mtime,
                               'https://example.test/wp-content/themes/t/js/missing.js?ver=0.1.0',
                               'https://cdn.example.org/lib.js?ver=2'])


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class Fields(unittest.TestCase):
    def test_rows_and_lists_of_empty_acf_values(self):
        body = r'''
$post = (object) [ 'ID' => 7 ];
$in = [ false, '', null, 'text', 0, [ false ], [ [ 'a' => 1 ], false, 'x' ], [ 5, null, '', $post, [] ] ];
echo json_encode( [ array_map( 'kitwp_rows', $in ), array_map( 'kitwp_list', $in ) ] );'''
        rows, lists = php([(INC + 'helpers.php', 'kitwp_rows'), (INC + 'helpers.php', 'kitwp_list')], body)
        self.assertEqual(rows, [[], [], [], [], [], [], [{'a': 1}], [[]]])
        self.assertEqual(lists, [[], [], [], [], [], [], [{'a': 1}, 'x'], [5, {'ID': 7}]])

    def test_agents_rule(self):
        self.assertIn('Never `(array)` on a field', read('assets/theme/AGENTS.md'))


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class PrivacyPage(unittest.TestCase):
    """The seeder points Settings > Privacy at the seeded privacy page, once it is published."""

    def test_privacy_setting(self):
        stubs = r'''
$GLOBALS['db'] = [];
function get_option( $k ) { return $GLOBALS['db'][ $k ] ?? false; }
function update_option( $k, $v ) { $GLOBALS['db'][ $k ] = $v; }
function get_page_by_path( $p ) { return $GLOBALS['pages'][ $p ] ?? null; }
'''
        body = r'''
$out = [];
$GLOBALS['pages'] = [ 'privacy' => (object) [ 'ID' => 9, 'post_status' => 'draft' ] ];
$out[] = [ kitwp_seed_privacy_page(), get_option( 'wp_page_for_privacy_policy' ) ];
$GLOBALS['pages']['privacy']->post_status = 'publish';
$out[] = [ kitwp_seed_privacy_page(), get_option( 'wp_page_for_privacy_policy' ) ];
$out[] = [ kitwp_seed_privacy_page(), get_option( 'wp_page_for_privacy_policy' ) ];
$GLOBALS['pages']['privacy-policy'] = (object) [ 'ID' => 4, 'post_status' => 'publish' ];
$out[] = [ kitwp_seed_privacy_page(), get_option( 'wp_page_for_privacy_policy' ) ];
echo json_encode( $out );'''
        got = php([(INC + 'seed-pages.php', 'kitwp_seed_privacy_page')], body, stubs)
        self.assertEqual(got, [[False, False], [True, 9], [False, 9], [True, 4]])


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class LongContent(unittest.TestCase):
    def test_remove_deletes_the_empty_option(self):
        stubs = ("$GLOBALS['db'] = [ 'kitwp_long_test_ids' => [ 4, 5 ] ];\n"
                 'function update_option( $k, $v, $a = null ) { $GLOBALS["db"][ $k ] = $v; }\n'
                 'function delete_option( $k ) { unset( $GLOBALS["db"][ $k ] ); }\n')
        body = ('kitwp_long_keep_ids( [ 1 => 5 ] ); $a = $GLOBALS["db"]; kitwp_long_keep_ids( [] );'
                'echo json_encode( [ $a, $GLOBALS["db"] ] );')
        got = php([('scripts/parity/long-content.php', 'kitwp_long_keep_ids')], body, stubs)
        self.assertEqual(got, [{'kitwp_long_test_ids': [5]}, []])


def php_list(values):
    return '[' + ', '.join(php_str(v) for v in values) + ']'


if __name__ == '__main__':
    unittest.main()
