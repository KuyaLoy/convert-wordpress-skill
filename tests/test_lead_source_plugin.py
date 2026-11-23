"""0.9.10: the Lead source must-use plugin for a WordPress site the kit did not build."""
import os
import re
import shutil
import subprocess
import tempfile
import unittest

from helpers import run
from test_theme_kit import php
from test_theme_php import php_function

STUBS = r'''
class WPCF7_Submission {
	public static function get_instance() { return new self(); }
	public function get_posted_data( $name = '' ) { return []; }
	public function get_meta( $k ) { return 'https://example.org/contact-us/'; }
}
class Kit_Mail { public $n; public function __construct( $n ) { $this->n = $n; } public function name() { return $this->n; } }
class Kit_Form { public $html; public function __construct( $h ) { $this->html = $h; } public function prop( $p ) { return [ 'use_html' => $this->html ]; } }
function kitwp_attribution_clean( $p ) { return []; }
function kitwp_attribution_table( $a, $page, $html ) {
	if ( ! empty( $GLOBALS['boom'] ) ) { throw new RuntimeException( 'x' ); }
	return $html ? '<table>LS ' . $page . '</table>' : "Lead source\nForm sent from: " . $page;
}
'''


class LeadSourcePlugin(unittest.TestCase):
    def build(self, *args):
        out = tempfile.mkdtemp()
        return out, run('scripts/launch/lead-source-plugin.py', out, *args)

    def test_builds_the_plugin_from_the_kit_files(self):
        out, r = self.build('--brand', '#fef151', '--days', '30', '--consent', 'banner')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.startswith('OK lead-source-plugin:'), r.stdout)
        loader = os.path.join(out, 'kitwp-lead-source.php')
        with open(loader, encoding='utf-8') as fh:
            text = fh.read()
        self.assertNotIn('{{', text)
        self.assertIn("'#fef151'", text)
        self.assertIn("(int) '30'", text)
        self.assertIn("'banner'", text)
        self.assertRegex(text, r'Version: \d+\.\d+\.\d+')
        self.assertEqual(sorted(os.listdir(os.path.join(out, 'kitwp-lead-source'))),
                         ['attribution.js', 'forms-attribution.php', 'forms-lead-source.php'])
        if shutil.which('php'):
            for p in (loader, os.path.join(out, 'kitwp-lead-source', 'forms-lead-source.php')):
                self.assertEqual(subprocess.run(['php', '-l', p], capture_output=True).returncode, 0, p)

    def test_refuses_bad_values(self):
        for args in (('--brand', 'yellow'), ('--days', '-1'), ('--thank-you', 'thanks"><script>')):
            out, r = self.build(*args)
            self.assertEqual(r.returncode, 2, args)
            self.assertTrue(r.stdout.startswith('FAIL lead-source-plugin:'), r.stdout)

    @unittest.skipUnless(shutil.which('php'), 'needs PHP')
    def test_mail_filter_places_the_table_and_never_breaks_the_email(self):
        out, r = self.build()
        loader = os.path.join(out, 'kitwp-lead-source.php')
        fn = [(loader, 'kitwp_lead_source_mail')]
        body = r'''
$cases = [];
$m = new Kit_Mail( 'mail' );
$cases[] = kitwp_lead_source_mail( [ 'body' => '<html><body><table>x</table><!-- kitwp-lead-source --><p>end</p></body></html>' ], new Kit_Form( true ), $m )['body'];
$cases[] = kitwp_lead_source_mail( [ 'body' => '<html><body><p>hi</p></body></html>' ], new Kit_Form( true ), $m )['body'];
$cases[] = kitwp_lead_source_mail( [ 'body' => 'Name: Sam' ], new Kit_Form( false ), $m )['body'];
$cases[] = kitwp_lead_source_mail( [ 'body' => 'copy' ], new Kit_Form( false ), new Kit_Mail( 'mail_2' ) )['body'];
$GLOBALS['boom'] = true;
$cases[] = kitwp_lead_source_mail( [ 'body' => '<p>keep</p></body>' ], new Kit_Form( true ), $m )['body'];
echo json_encode( $cases );'''
        marker, before_end, plain, copy, broken = php(fn, body, STUBS)
        self.assertEqual(marker, '<html><body><table>x</table><table>LS https://example.org/contact-us/</table>'
                                 '<p>end</p></body></html>')
        self.assertTrue(before_end.endswith('<p>hi</p><table>LS https://example.org/contact-us/</table></body></html>'))
        self.assertEqual(plain, 'Name: Sam\n\nLead source\nForm sent from: https://example.org/contact-us/\n')
        self.assertEqual(copy, 'copy')  # the copy to the visitor gets nothing
        self.assertEqual(broken, '<p>keep</p></body>')  # an error leaves the email as it was


if __name__ == '__main__':
    unittest.main()
