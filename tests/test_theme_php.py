"""Pure PHP helpers of the theme kit (maps, SVG, CF7 markup, seeded email check), run with small WordPress stubs.

The functions are taken from the kit's PHP files by name, so the files' hooks and template tokens are not loaded.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

from helpers import path

STUBS = r'''
const KITWP_MAP_DEFAULT = 'Leeds, UK';
function kitwp_setting( $name ) { return $GLOBALS['settings'][ $name ] ?? null; }
function wp_parse_url( $url, $component = -1 ) { return parse_url( $url, $component ); }
function wp_strip_all_tags( $text ) { return trim( strip_tags( $text ) ); }
'''


def php_function(file, name):
    """The source of one top-level function in a kit PHP file (from 'function name(' to the closing brace)."""
    with open(path(file), encoding='utf-8') as fh:
        text = fh.read()
    m = re.search(r'^function ' + re.escape(name) + r'\(.*?^}\n', text, re.S | re.M)
    if not m:
        raise AssertionError(f'{name} not found in {file}')
    return m.group(0)


def run_php(functions, body):
    code = '<?php\n' + STUBS + '\n'.join(php_function(f, n) for f, n in functions) + '\n' + body
    with tempfile.NamedTemporaryFile('w', suffix='.php', delete=False, encoding='utf-8') as fh:
        fh.write(code)
    try:
        out = subprocess.run(['php', fh.name], capture_output=True, text=True, timeout=60)
    finally:
        os.unlink(fh.name)
    if out.returncode:
        raise AssertionError(out.stdout + out.stderr)
    return json.loads(out.stdout)


HELPERS = 'assets/theme/includes/helpers.php'
MEDIA = 'assets/theme/includes/media.php'


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class Maps(unittest.TestCase):
    def src(self, values, settings=None):
        body = ('$GLOBALS["settings"] = ' + php_array(settings or {}) + ';\n'
                'echo json_encode( array_map( fn( $v ) => kitwp_map_src( $v ), ' + php_array(values) + ' ) );')
        return run_php([(HELPERS, 'kitwp_map_src'), (HELPERS, 'kitwp_map_embed_url')], body)

    def test_inputs(self):
        embed = 'https://www.google.com/maps/embed?pb=!1m18!1m12&x=1'
        got = self.src([
            embed,
            '<iframe src="' + embed.replace('&', '&amp;') + '" width="600" height="450"></iframe>',
            'https://www.google.com/maps/place/Example+Co,+1+High+St/@53.79,-1.54,17z',
            'https://maps.google.com/?q=1+High+St,+Leeds',
            'https://www.google.com/maps/@53.7997,-1.5492,15z',
            '1 High St, Leeds LS1 1AA',
        ])
        self.assertEqual(got[0], embed)
        self.assertEqual(got[1], embed)
        self.assertEqual(got[2], 'https://maps.google.com/maps?q=Example%20Co%2C%201%20High%20St&output=embed')
        self.assertEqual(got[3], 'https://maps.google.com/maps?q=1%20High%20St%2C%20Leeds&output=embed')
        self.assertEqual(got[4], 'https://maps.google.com/maps?q=53.7997%2C-1.5492&output=embed')
        self.assertEqual(got[5], 'https://maps.google.com/maps?q=1%20High%20St%2C%20Leeds%20LS1%201AA&output=embed')

    def test_default_city(self):
        city = 'https://maps.google.com/maps?q=Leeds%2C%20UK&output=embed'
        got = self.src(['', 'https://maps.app.goo.gl/abc123', 'https://example.com/map', '<iframe></iframe>'])
        self.assertEqual(got, [city] * 4)

    def test_reads_theme_settings(self):
        body = ('$GLOBALS["settings"] = ["map" => "York"];\n'
                'echo json_encode( [ kitwp_map_src(), kitwp_map_src( null, "" ) ] );')
        got = run_php([(HELPERS, 'kitwp_map_src'), (HELPERS, 'kitwp_map_embed_url')], body)
        self.assertEqual(got, ['https://maps.google.com/maps?q=York&output=embed'] * 2)


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class Svg(unittest.TestCase):
    def test_clean(self):
        svg = ('<?xml version="1.0"?><!-- c --><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10" '
               'onload="alert(1)"><script>alert(2)</script><a href="javascript:alert(3)"><use href="#a"/></a>'
               '<foreignObject><div>x</div></foreignObject><path d="M0 0h10" onclick=\'x()\'/></svg>trailing')
        body = 'echo json_encode( kitwp_svg_clean( ' + php_str(svg) + ' ) );'
        got = run_php([(MEDIA, 'kitwp_svg_clean')], body)
        self.assertEqual(got, '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><a><use href="#a"/></a>'
                              '<path d="M0 0h10"/></svg>')

    def test_size(self):
        body = ('echo json_encode( [ kitwp_svg_size_of( \'<svg width="160px" height="40" viewBox="0 0 1 1">\' ), '
                'kitwp_svg_size_of( \'<svg viewBox="0 0 320.4 79.6">\' ), kitwp_svg_size_of( "<p>" ) ] );')
        self.assertEqual(run_php([(MEDIA, 'kitwp_svg_size_of')], body), [[160, 40], [320, 80], [0, 0]])


@unittest.skipUnless(shutil.which('php'), 'needs PHP')
class Forms(unittest.TestCase):
    def test_no_empty_paragraphs(self):
        body = ('echo json_encode( kitwp_cf7_no_empty_p( "<p> </p><label>Name</label><p><br /></p><p>Keep</p>'
                '<P>&nbsp;</P>" ) );')
        got = run_php([('assets/theme/includes/forms.php', 'kitwp_cf7_no_empty_p')], body)
        self.assertEqual(got, '<label>Name</label><p>Keep</p>')

    def test_seeded_emails_must_be_html(self):
        with open(path('assets/seed/lead-email.html'), encoding='utf-8') as fh:
            html = fh.read()
        body = ('$d = fn( $form, $mail, $active, $reply ) => [ "form" => $form, "mail" => [ "body" => $mail ], '
                '"mail_2" => [ "active" => $active, "body" => $reply ] ];\n'
                '$h = ' + php_str(html) + ';\n'
                'echo json_encode( [\n'
                '  kitwp_seed_form_problem( "quote", $d( "[text name]", $h, true, $h ) ),\n'
                '  kitwp_seed_form_problem( "quote", $d( "[text name]", $h, false, "" ) ),\n'
                '  kitwp_seed_form_problem( "quote", $d( "[text name]", "Name: [name]", true, $h ) ),\n'
                '  kitwp_seed_form_problem( "quote", $d( "[text name]", $h, true, "Thanks [name]" ) ),\n'
                '  kitwp_seed_form_problem( "quote", $d( "", $h, true, $h ) ),\n'
                '] );')
        got = run_php([('assets/theme/includes/seed.php', 'kitwp_seed_form_problem')], body)
        self.assertEqual(got[0], '')
        self.assertEqual(got[1], '')
        self.assertIn('body_file of "quote" is not the branded HTML email', got[2])
        self.assertIn('autoreply_file of "quote" is not the branded HTML email', got[3])
        self.assertIn('form or email file missing', got[4])


def php_str(text):
    return "'" + text.replace('\\', '\\\\').replace("'", "\\'") + "'"


def php_array(value):
    if isinstance(value, dict):
        return '[' + ', '.join(php_str(k) + ' => ' + php_str(v) for k, v in value.items()) + ']'
    return '[' + ', '.join(php_str(v) for v in value) + ']'


if __name__ == '__main__':
    unittest.main()
