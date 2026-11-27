"""The agency branding checks shared by self-check.py and live-qa.py (not run on its own).

A site's footer carries the agency badge, linked, and every Contact Form 7 form sends its email and its auto-reply
in the kit's branded HTML template (the logo and the badge mail-tags in an HTML body), unless the build recorded
that the client asked to hide the badge (site.json "agency_badge_hide", in config.php as KITWP_BADGE_HIDE_NOTE).
"""
import json
import re
import shlex
import shutil
import subprocess

# The footer badge kitwp_agency_badge() prints: a link with data-<prefix>-badge="agency" and an image inside.
BADGE = re.compile(r'<a\b[^>]*\bdata-[a-z0-9]+-badge="agency"[^>]*>(.*?)</a>', re.I | re.S)
HREF = re.compile(r'\bhref="(https?://[^"]+)"', re.I)
IMG_SRC = re.compile(r'<img\b[^>]*\bsrc="([^"]+)"', re.I)
LOGO_TAG = re.compile(r'\[_[a-z0-9]+_logo\]')
BADGE_TAG = re.compile(r'\[_[a-z0-9]+_badge\]')
# Runs inside WordPress (wp eval): each CF7 form's email and auto-reply, as facts only.
MAIL_PHP = (
    'if ( ! class_exists( "WPCF7_ContactForm" ) ) { echo "{\\"error\\":\\"Contact Form 7 is not active\\"}"; return; }'
    '$o = []; foreach ( get_posts( [ "post_type" => "wpcf7_contact_form", "numberposts" => -1, "post_status" => "any" ] )'
    ' as $p ) { $f = WPCF7_ContactForm::get_instance( $p->ID ); foreach ( [ "mail", "mail_2" ] as $m ) { $x = (array)'
    ' $f->prop( $m ); $o[] = [ "form" => $p->post_title, "mail" => $m, "active" => "mail" === $m || ! empty( $x["active"] ),'
    ' "html" => ! empty( $x["use_html"] ), "body" => (string) ( $x["body"] ?? "" ) ]; } } echo wp_json_encode( [ "mails"'
    ' => $o ] );'
)


def badge_problem(html_text):
    """'' when the page has the footer badge, linked, with an image; else what is missing."""
    m = BADGE.search(html_text or '')
    if not m:
        return 'no agency badge in the footer (kitwp_agency_badge())'
    if not HREF.search(m.group(0)):
        return 'the agency badge has no link (Theme Settings > Branding "Agency badge link")'
    src = IMG_SRC.search(m.group(1))
    if not src or not src.group(1).strip():
        return 'the agency badge has no image (Theme Settings > Branding "Agency badge")'
    return ''


def template_problem(body, html=True):
    """'' when a mail body is the branded HTML template (logo and badge mail-tags in an HTML body)."""
    missing = [n for n, rx in (('logo', LOGO_TAG), ('badge', BADGE_TAG)) if not rx.search(body or '')]
    if not html:
        return 'not HTML (Mail tab: "Use HTML content type")'
    if missing:
        return 'not the branded template (no ' + ' and no '.join(missing) + ' mail-tag)'
    return ''


def mail_problems(mails):
    """Problems in the list wp eval returns: [(form, what)]."""
    out = []
    for m in mails:
        name = 'auto-reply' if m.get('mail') == 'mail_2' else 'email'
        if not m.get('active'):
            out.append((m.get('form', '?'), 'no auto-reply (Mail (2) is off)'))
            continue
        what = template_problem(m.get('body', ''), bool(m.get('html')))
        if what:
            out.append((m.get('form', '?'), f'{name}: {what}'))
    return out


def read_mails(wp, path='', timeout=120):
    """Each CF7 form's email and auto-reply from WordPress: (list, '') or (None, why)."""
    cmd = shlex.split(wp) if wp else ([shutil.which('wp')] if shutil.which('wp') else None)
    if not cmd:
        return None, 'WP-CLI not found: pass --wp "wp @live" or --wp "php <path>/wp-cli.phar"'
    try:
        r = subprocess.run(cmd + ([f'--path={path}'] if path else []) + ['eval', MAIL_PHP], capture_output=True,
                           text=True, timeout=timeout, errors='replace')
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, f'WP-CLI did not answer ({e.__class__.__name__})'
    try:
        data = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return None, f'WP-CLI gave no answer (exit {r.returncode})'
    if data.get('error'):
        return None, data['error']
    return data.get('mails', []), ''
