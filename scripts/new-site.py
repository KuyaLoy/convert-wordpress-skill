#!/usr/bin/env python3
"""Start a conversion: prepare the starter theme, copy the skill's kit into the WordPress project and fill in the
site's values. Safe to run again (it keeps what is there and reports it).

    python3 scripts/new-site.py --start <wp_root> [--name "Site"]   at intake: the folder and two short handoff files
    python3 scripts/new-site.py site.json --plan-only     P0: plan, board, handoff files, tools
    python3 scripts/new-site.py site.json                 P1: prepare the starter theme and copy the kit in
    python3 scripts/new-site.py site.json --launch-files  the runbook and live .htaccess again (forms, redirects...)
    options: [--profile profile.local.json] [--dry-run] [--force]

site.json: copy assets/site.example.json and fill it in (the intake answers). The profile holds the developer's or
agency's defaults (lead Bcc list, task tracker, extra plugins, reply style); it is optional. site.json wins where it
sets a value; the Bcc lists are combined.

Before running: WordPress is installed at wp_root and the starter theme is in wp-content/themes/<theme>/:
  starter "barebones" (plain CSS): Barebones (github.com/benchmarkstudios/barebones), unzipped, folder renamed <theme>
  starter "tw" (Tailwind): _tw generated with the theme slug and prefix (underscoretw.com, or
      wp scaffold _tw <theme> --theme_name="<Site>" --prefix=<prefix>); WordPress uses its theme/ subfolder

What it does (a file that exists is kept; --force replaces kit code only, after backing it up to
_setup/kit-backup-<time>/, and never the plan, the board, the handoff files, the seed data, the launch files, the
content model in build_field_groups.py or the parity routes and settings):
  1. Prepares the starter. Barebones: global functions renamed to the prefix, text domain and theme header set,
     front-end jQuery dropped; the sample block, the shortcode file, its acf.php (it hides the ACF menu outside
     "development"), its functions.php and AGENTS.md moved to _setup/starter-removed/ (nothing is deleted). _tw: checked that
     it was generated (the raw repo still says _tw); its PHPCS ruleset swapped for the kit's. Both: what this site
     does not use moved aside too (no blog: _tw's post, archive, search and comment templates and inc/ helpers; no
     chat: assets/chat-save.js; the readme stubs, the unused widget area and supports), the theme header and
     theme.json set to the site (site.json "blog", "chat", "palette", "content_size", "wide_size").
  2. Theme: includes/, template-parts/, assets/, acf-json/ (empty), AGENTS.md, phpcs.xml.dist,
     composer.json, tests/parity/, and functions.php (Barebones: the kit's; _tw: the kit's lines appended).
  3. Project: _plan/ (plan templates, tools/), _setup/seed/, _setup/launch/ (RUNBOOK.md, htaccess-live.txt,
     report.html), BUILD-MAP.md, handoff.md, ai-handoff-summary.md, and the private-files block in .htaccess.
Tokens: kitwp/KITWP/Kitwp (PHP prefix), kitk (ACF key prefix), every {{NAME}} from site.json,
<!-- starter:barebones --> / <!-- starter:tw --> blocks, on their own lines or inline (kept only for the chosen
starter), and <!-- if:NAME --> / <!-- unless:NAME --> blocks for this site's switches: redirects, tracking, forms,
portal, chat, blog, www (the runbook and the live .htaccess hold only the steps this site needs).
"""
import argparse
import datetime
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
TEXT = ('.php', '.js', '.mjs', '.py', '.json', '.md', '.txt', '.html', '.xml', '.dist', '.css', '.scss', '.htaccess')
KIT_FILES = ['config', 'cleanup', 'head', 'acf', 'helpers', 'media', 'forms', 'client-admin', 'schema', 'seo', 'seed', 'seed-pages',
             'snapshot']
# The kit's own functions.php is the one list of include files: _tw gets the same list appended, so a new include
# never has to be added in two places.
try:
    with open(os.path.join(SKILL, 'assets', 'theme', 'functions.php'), encoding='utf-8') as _fh:
        _m = re.search(r'\$kitwp_kit = \[(.*?)\];', _fh.read(), re.S)
    if _m and re.findall(r"'([\w-]+)'", _m.group(1)):
        KIT_FILES = re.findall(r"'([\w-]+)'", _m.group(1))
except OSError:
    pass
PHP_MIN = '8.1'  # the kit's code runs on PHP 8.1 to 8.4 (phpcs.xml.dist testVersion)

ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
ap.add_argument('site_json', nargs='?')
ap.add_argument('--start', metavar='WP_ROOT', help='intake: create the folder and the intake handoff files only')
ap.add_argument('--name', help='with --start: the site name for the handoff files')
ap.add_argument('--allow-example', action='store_true', help=argparse.SUPPRESS)
ap.add_argument('--profile')
ap.add_argument('--dry-run', action='store_true')
ap.add_argument('--force', action='store_true')
ap.add_argument('--plan-only', action='store_true', help='P0: only the plan, the board, the handoff files and the tools (no WordPress or theme yet)')
ap.add_argument('--launch-files', action='store_true',
                help='write _setup/launch/RUNBOOK.md and htaccess-live.txt again from site.json and the plan (the '
                     'old ones are kept in _setup/launch/before-<time>/)')
a = ap.parse_args()

INTAKE = '<!-- kit:intake: written by new-site.py --start; --plan-only replaces it and keeps the notes below -->'
if a.start:
    root = os.path.abspath(a.start)
    os.makedirs(root, exist_ok=True)
    name = a.name or os.path.basename(root)
    day = datetime.date.today().isoformat()
    docs = {
        'handoff.md': f"""{INTAKE}
# Handoff: {name} WordPress build

## Goal
Rebuild {name} in WordPress 1:1 with the convert-to-wordpress skill.

## Current State
Intake started {day}. Folder: {root}.

## Changes Made
### {day}: intake started
- doctor.py run; the folder for the site chosen.

## Failed Attempts

## Next Steps
1. Finish the intake (SKILL.md > Start: start.py, site.json, new-site.py --plan-only).
""",
        'ai-handoff-summary.md': f"""{INTAKE}
# AI handoff summary: {name} WordPress build
Updated: {day} | By: <agent>
Last change: intake started
Status: ACTIVE

## Now
- Intake (SKILL.md > Start). The answers so far are in handoff.md.

## Next action
- Continue the intake from the first step not done: start.py, site.json, new-site.py --plan-only.
""",
    }
    made = []
    for f, text in docs.items():
        target = os.path.join(root, f)
        if not os.path.exists(target):
            with open(target, 'w', encoding='utf-8') as fh:
                fh.write(text)
            made.append(f)
    print(f"OK new-site: intake handoff files {'written: ' + ', '.join(made) if made else 'already there (kept)'} in "
          f'{root}')
    sys.exit(0)
if not a.site_json:
    ap.error('give site.json (or --start <wp_root> at intake)')

site = json.load(open(a.site_json, encoding='utf-8'))
prof_path = a.profile or os.path.join(SKILL, 'profile.local.json')
profile = json.load(open(prof_path, encoding='utf-8')) if os.path.exists(prof_path) else {}

errors = []
for k in ('site_name', 'domain', 'wp_root', 'local_host', 'theme', 'prefix', 'key', 'starter'):
    if not site.get(k):
        errors.append(f'site.json: "{k}" is required')
if site.get('theme') and not re.fullmatch(r'[a-z][a-z0-9-]{1,39}', site['theme']):
    errors.append('theme: the theme folder name, lowercase letters, digits and dashes')
if site.get('prefix') and not re.fullmatch(r'[a-z][a-z0-9]{1,19}', site['prefix']):
    errors.append('prefix: 2 to 20 lowercase letters or digits, starting with a letter (it prefixes every PHP function)')
if site.get('key') and not re.fullmatch(r'[a-z][a-z0-9]{1,5}', site['key']):
    errors.append('key: 2 to 6 lowercase letters or digits (the ACF key prefix: group_<key>_*, field_<key>_*)')
if site.get('starter') and site['starter'] not in ('barebones', 'tw'):
    errors.append('starter: "barebones" (plain CSS) or "tw" (Tailwind)')
if not a.allow_example:
    if site.get('site_name') in ('Example Co', 'Example Co Ltd') or site.get('domain') == 'example.com':
        errors.append('site.json still holds the example values (Example Co, example.com): fill in the real site')
    if '<' in str(site.get('wp_root', '')) or str(site.get('wp_root', '')).replace('\\', '/').endswith('laragon/www/example'):
        errors.append('wp_root is still the example: use the folder from the intake (doctor.py suggests it)')
if errors:
    sys.exit('\n'.join(errors))

starter, prefix, key = site['starter'], site['prefix'], site['key']
# Lead email: the profile's defaults, then the site's non-empty values; the Bcc lists are combined (the agency's
# usual copies plus the site's own, for example its account manager).
lead = {k: v for k, v in profile.get('lead', {}).items() if not k.startswith('_')}
branding = {k: v for k, v in profile.get('branding', {}).items() if not k.startswith('_')}
for _b in ('email_badge_png', 'site_badge'):
    if branding.get(_b) and not os.path.isabs(branding[_b]):
        branding[_b] = os.path.join(SKILL, branding[_b])
    if branding.get(_b) and not os.path.exists(branding[_b]):
        sys.exit(f'profile branding.{_b} not found: ' + branding[_b])
for k, v in site.get('lead', {}).items():
    if k == 'bcc':
        lead['bcc'] = list(dict.fromkeys(list(lead.get('bcc', [])) + list(v or [])))
    elif v not in (None, '', []):
        lead[k] = v
today = datetime.date.today()
NO_PORTAL = str(site.get('leads_portal') or '').strip()
# The live host: site.json "www" (true or false) says whether the address is www.<domain>; without it, the domain
# as written decides. Both host rules are built from the bare domain, so a "www." domain can never give a rule for
# www.www.<domain> (a real build shipped that: the bare domain never reached https).
BARE = re.sub(r'^www\.', '', site['domain'].strip().lower().rstrip('/').split('://')[-1])
WWW = site['www'] if isinstance(site.get('www'), bool) else site['domain'].strip().lower().startswith('www.')
LIVE_HOST, OTHER_HOST = ('www.' + BARE, BARE) if WWW else (BARE, 'www.' + BARE)
# The site's lead forms in plain words, for the runbook's test leads (site.json "forms"; [] = no forms). The chat
# (site.json "chat", or a chat_selector) is one of them. Without a list: the contact form, and a note to fill it.
CHAT = site['chat'] if isinstance(site.get('chat'), bool) else bool(str(site.get('chat_selector') or '').strip())
BLOG = bool(site.get('blog'))
FORMS = [str(x).strip() for x in (site['forms'] if isinstance(site.get('forms'), list) else ['the contact form'])
         if str(x).strip()]
if CHAT and not any('chat' in x.lower() for x in FORMS):
    FORMS.append('the chat')
GTM = str(site.get('gtm') or '').strip()
TRACKING = bool(GTM) and not re.fullmatch(r'GTM-X+', GTM, re.I)  # GTM-XXXXXXX is the example's placeholder
_tracking = profile.get('tracking') or {}
TO = str(site.get('lead', {}).get('to') or profile.get('lead', {}).get('to') or '').strip()
if not FORMS:
    LEADS_TO_ITEM = ('no lead forms on this site; Settings > General > Administration email is still a monitored '
                     'live address of the client, not a local, test or developer address.')
elif TO:
    LEADS_TO_ITEM = (f'each Contact Form 7 form\'s Mail tab "To" is the client\'s live address ({TO}, site.json '
                     'lead.to), and so are the email settings leads may fall back to (Settings > General > '
                     "Administration email, the theme's own email setting): never a local, test or admin address.")
else:
    LEADS_TO_ITEM = ('BLOCKER: site.json lead.to is empty. Ask the client which address gets the leads, then set it '
                     'in each Contact Form 7 form\'s Mail tab "To" and in Settings > General > Administration email '
                     '(never a local, test or admin address).')
values = {
    'SITE_NAME': site['site_name'],
    'LEGAL_NAME': site.get('legal_name', site['site_name']),
    'DOMAIN': site['domain'],
    'DOMAIN_REGEX': site['domain'].replace('.', '\\.'),
    'LIVE_HOST': LIVE_HOST,
    'LIVE_HOST_REGEX': LIVE_HOST.replace('.', '\\.'),
    'OTHER_HOST': OTHER_HOST,
    'OTHER_HOST_REGEX': OTHER_HOST.replace('.', '\\.'),
    'FORMS_LIST': ', '.join(FORMS),
    'LEADS_TO_ITEM': LEADS_TO_ITEM,
    'TRACKING_WHERE': (f"the {_tracking['plugin']} plugin" if _tracking.get('plugin') else
                       str(_tracking.get('method') or "the theme's tracking setting")),
    'LOCAL_HOST': site['local_host'].replace('http://', '').replace('https://', '').rstrip('/'),
    'REF_URL': site.get('ref_url', ''),
    'SITE_DIR': site.get('site_dir', os.path.basename(os.path.normpath(site['wp_root']))),
    'THEME': site['theme'],
    'STARTER': 'Barebones' if starter == 'barebones' else '_tw',
    'SCHEMA_TYPE': site.get('schema_type', 'Organization'),
    'AREA_SERVED': site.get('area_served', ''),
    # The map's default until the address is confirmed (usually the city); falls back to area_served.
    'MAP_DEFAULT': str(site.get('map_default', '') or site.get('area_served', '')).replace("'", "\\'"),
    'COUNTRY_CODE': site.get('country_code', ''),
    'PRICE_RANGE': site.get('price_range', ''),
    'BRAND_COLOUR': site.get('brand_colour', '#000000'),
    'OG_LOCALE': site.get('og_locale', 'en_US'),
    'HTML_ATTRIBUTES': site.get('html_attributes', '').replace("'", "\\'"),
    'TIMEZONE': site.get('timezone', 'UTC'),
    'FORM_CLASS': site.get('form_class', 'lead-form'),
    'CHAT_SELECTOR': site.get('chat_selector', ''),
    # Font links exactly as the static <head> prints them. PHPCS flags hand-printed stylesheets: each line gets an
    # ignore on the line before it (the closing ?> eats its newline, so the page shows only the link).
    'FONT_LINKS': '\n'.join('<?php // phpcs:ignore WordPress.WP.EnqueuedResources.NonEnqueuedStylesheet -- the static head\'s own '
                            'font link, 1:1 ?>\n' + l
                            for l in site.get('font_links', [])),
    'PRECONNECT_FONTS': 'true' if any('fonts.googleapis' in l for l in site.get('font_links', [])) else 'false',
    'PHONE_DISPLAY': site.get('phone_display', ''),
    'PHONE_TEL': site.get('phone_tel', ''),
    'EMAIL': site.get('email', ''),
    # The agency badge in the footer of the lead email and the auto-reply (profile "branding"; empty = none).
    'EMAIL_BADGE': ('assets/email/' + os.path.basename(branding['email_badge_png'])) if branding.get('email_badge_png') else '',
    'EMAIL_BADGE_LINK': branding.get('link', '').replace("'", "\\'"),
    'EMAIL_BADGE_ALT': branding.get('alt', '').replace("'", "\\'"),
    'EMAIL_BADGE_WIDTH': str(int(branding.get('width', 120))),
    'SITE_BADGE': ('assets/brand/' + os.path.basename(branding['site_badge'])) if branding.get('site_badge') else '',
    # Leads portal: its values live in Theme Settings > Leads portal; the profile's constant prefix names only the
    # wp-config constants that win when defined (<PREFIX>_ENDPOINT, <PREFIX>_KEY).
    # The client's dashboard "Need help?" line (site.json or the profile; empty hides it).
    'CLIENT_HELP': str(site.get('client_help', profile.get('client_help', ''))).replace("'", "\\'"),
    'LEADS_PREFIX': re.sub(r'[^A-Z0-9_]', '', str(profile.get('leads_portal', {}).get('constant_prefix', '')).upper()),
    # The leads portal is mandatory for a site with a lead form; site.json "leads_portal": "none: <reason>" says why not.
    'LEADS_ITEM': '',
    # The theme answers 404 for archives, feeds and search unless the site has them (config.php KITWP_KEEP_BLOG,
    # KITWP_SITE_SEARCH): site.json "blog" and "search".
    'KEEP_BLOG': 'true' if BLOG else 'false',
    'SITE_SEARCH': 'true' if site.get('search') else 'false',
    'GTM_ID': site.get('gtm', ''),
    # The live cache plugin (RUNBOOK section 4): LiteSpeed Cache unless the profile or site.json names another.
    'CACHE_PLUGIN': str(site.get('cache_plugin') or profile.get('cache_plugin') or 'LiteSpeed Cache'),
    # The live plugin checklist's own lines (RUNBOOK section 4): the profile's extra_plugins that must be on live
    # ("required" or "live", with "where" "live" or "all"), each from its zip in plugin_zips. "where": "live" ones
    # are installed here at launch and never on local or staging.
    'LIVE_PLUGINS': '\n'.join(
        f"   - [ ] {p.get('name', '?')}: from your plugin folder"
        + (f" (`plugin_zips.{p['zip']}`)" if p.get('zip') else '')
        + (' (live only: never local or staging)' if str(p.get('where', '')).lower() == 'live' else '')
        + (f"; {p['live_note']}" if p.get('live_note') else '') + '.'
        for p in profile.get('extra_plugins', []) if isinstance(p, dict) and (p.get('required') or p.get('live'))
        and str(p.get('where') or 'live').lower() in ('live', 'all')
    ) or '   - (no live plugins of your own in the profile)',
    'LEAD_TO': lead.get('to', ''),
    'LEAD_BCC': ', '.join(lead.get('bcc', [])),
    'LEAD_FROM': lead.get('from', f"{site['site_name']} <no-reply@{site['domain']}>"),
    'DEVELOPER': site['developer'] if site.get('developer') not in (None, '', 'the developer') else profile.get('developer', 'the developer'),
    'DATE': f'{today.day} {today:%b %Y}',
    # The handoff summary's "Updated:" stamp: YYYY-MM-DD HH:MM and the numeric timezone (the handoff skill's format).
    'NOW': (lambda t: t.strftime('%Y-%m-%d %H:%M ') + t.strftime('%z')[:3] + ':' + t.strftime('%z')[3:])(
        datetime.datetime.now().astimezone()),
}


_lp = values['LEADS_PREFIX']
# The profile has a portal when its leads_portal names anything (the prefix, the admin or how a project is made).
_portal = any(str(v).strip() for k, v in (profile.get('leads_portal') or {}).items() if not str(k).startswith('_'))
if NO_PORTAL.lower().startswith('none'):
    values['LEADS_ITEM'] = f'No leads portal for this site: "{NO_PORTAL}" (site.json).'
elif _portal:
    values['LEADS_ITEM'] = (f'The leads portal: the project for {site["domain"]} exists in the portal admin; its '
                            'address and password pasted into Theme Settings > Leads portal on live (the developer, '
                            'logged in as an administrator)'
                            + (f'; wp-config `{_lp}_ENDPOINT` and `{_lp}_KEY` win when defined' if _lp else '')
                            + '; `python3 _plan/tools/report/leads-check.py --site` on live answers OK (a GET, nothing '
                            "stored); one TEST lead per form shows in the portal's form counts.")
else:
    values['LEADS_ITEM'] = ('BLOCKER: no leads portal in the profile (`leads_portal`). Every live site with a lead '
                            'form sends to it; a site without one says so in site.json: "leads_portal": '
                            '"none: <reason>".')


FLAGS = {}  # filled below, before the first fill(): redirects, tracking, forms, portal, chat, blog, www, trackplugin


def fill(text):
    """Prefix and key tokens, starter blocks, if/unless blocks, then {{NAME}} values (unknown names stay, and are
    reported). <!-- if:NAME --> keeps its block when FLAGS[NAME] is on, <!-- unless:NAME --> when it is off."""
    text = text.replace('KITWP', prefix.upper()).replace('Kitwp', prefix.capitalize()).replace('kitwp', prefix)
    text = text.replace('kitk', key)
    keep = lambda m: m.group(2) if m.group(1) == starter else ''  # noqa: E731
    text = re.sub(r'[ \t]*<!-- starter:(\w+) -->\n(.*?)[ \t]*<!-- /starter:\1 -->\n', keep, text, flags=re.S)
    text = re.sub(r'<!-- starter:(\w+) -->(.*?)<!-- /starter:\1 -->', keep, text)  # inline, within one line
    when = lambda m: m.group(3) if bool(FLAGS.get(m.group(2))) == (m.group(1) == 'if') else ''  # noqa: E731
    while True:  # blocks can nest (an if:portal inside an if:forms): repeat until none is left
        new = re.sub(r'[ \t]*<!-- (if|unless):(\w+) -->\n(.*?)[ \t]*<!-- /\1:\2 -->\n', when, text, flags=re.S)
        new = re.sub(r'<!-- (if|unless):(\w+) -->(.*?)<!-- /\1:\2 -->', when, new)
        if new == text:
            break
        text = new
    return re.sub(r'\{\{([A-Z_]+)\}\}', lambda m: values.get(m.group(1), m.group(0)), text)


root = os.path.abspath(site['wp_root'])
theme_root = os.path.join(root, 'wp-content', 'themes', site['theme'])  # the folder in wp-content/themes
theme = os.path.join(theme_root, 'theme') if starter == 'tw' else theme_root  # the folder WordPress loads
removed = os.path.join(root, '_setup', 'starter-removed')
notes, moved, gone = [], [], set()


def rel(p):
    return os.path.relpath(p, root).replace('\\', '/')


def read(p):
    with open(p, encoding='utf-8', errors='replace') as fh:
        return fh.read()


def write(p, data):
    if a.dry_run:
        return
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(data)
    os.chmod(p, 0o644)


def exists(p):
    return os.path.exists(p) and p not in gone


def move_aside(p):
    """Move a starter file or folder out of the theme (kept under _setup/starter-removed/, never deleted)."""
    if not exists(p):
        return
    gone.add(p)
    dst = os.path.join(removed, os.path.relpath(p, theme_root))
    if os.path.exists(dst):
        dst += '.' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    moved.append(rel(p))
    if not a.dry_run:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(p, dst)


def old_urls_planned():
    """True when the site has old URLs to redirect: site.json "redirects": true, or a 301 row in OLD-SITE-URLS.md."""
    if site.get('redirects') is True:
        return True
    plan_doc = os.path.join(root, '_plan', 'OLD-SITE-URLS.md')
    if os.path.exists(plan_doc):
        # A filled row: | /old-path/ (or a full URL) | 301 ... | target |. The template's empty row does not count.
        return bool(re.search(r'^\|\s*(?:/|https?://)[^|]*\|[^|]*\b301\b', read(plan_doc), re.M))
    return False


FLAGS.update(redirects=old_urls_planned(), tracking=TRACKING, forms=bool(FORMS), chat=CHAT, blog=BLOG, www=WWW,
             portal=not NO_PORTAL.lower().startswith('none'), trackplugin=bool(_tracking.get('plugin')))
if site.get('redirects') is False and FLAGS['redirects']:
    notes.append('site.json says "redirects": false, but _plan/OLD-SITE-URLS.md lists 301 rows: the launch files '
                 'include the Redirection steps')
if not isinstance(site.get('forms'), list):
    notes.append('site.json has no "forms" list: the runbook tests "the contact form" only. List every lead form in '
                 'plain words (for example ["the contact form", "the quote pop-up"]; [] for none), then run this '
                 'again with --launch-files')


def edit_php(p, edits):
    """Apply (label, pattern, replacement) regex edits to one PHP file. Returns the labels that applied. With php on
    the PATH, a result that fails php -l is not written (the starter's file stays as it was, and a note says so)."""
    if not exists(p):
        return []
    old = read(p)
    new, done = old, []
    for label, pat, repl in edits:
        new, n = re.subn(pat, repl, new, flags=re.S)
        if n:
            done.append(label)
    if new == old:
        return []
    php = shutil.which('php')
    if php and not a.dry_run:
        tmp = p + '.kit-check.php'
        with open(tmp, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(new)
        try:
            import subprocess
            ok = subprocess.run([php, '-l', tmp], capture_output=True, text=True).returncode == 0
        finally:
            os.remove(tmp)
        if not ok:
            notes.append(f'{rel(p)}: the starter clean-up would break the file (php -l): left as it was, check by hand')
            return []
    write(p, new)
    return done


def tidy_starter():
    """Move the starter's files and supports this site does not use out of the theme (to _setup/starter-removed/,
    never deleted), and set its theme header and theme.json to this site. Each piece is checked first: anything
    still in use stays, with a note."""
    done = []
    # The theme header: the site's address, its author and the PHP the kit needs (not the starter's own).
    author = (profile.get('agency') or values['DEVELOPER']).strip()
    if author == 'the developer':
        author = site['site_name']
    for p in (os.path.join(theme, 'style.css'), os.path.join(theme, 'style-editor.css'),
              os.path.join(theme_root, 'tailwind', 'custom', 'file-header.css'),
              os.path.join(theme, 'assets', 'styles', 'style.scss')):
        if not exists(p):
            continue
        old = read(p)
        new = re.sub(r'^(Theme URI:[ \t]*).*(?:underscoretw\.com|benchmark)[^\n]*$', rf'\g<1>https://{LIVE_HOST}/',
                     old, flags=re.M | re.I)
        new = re.sub(r'^(Author:[ \t]*).*(?:underscoretw\.com|benchmark)[^\n]*$',
                     lambda m: m.group(1) + author, new, flags=re.M | re.I)
        new = re.sub(r'^Author URI:.*(?:underscoretw\.com|benchmark)[^\n]*\n', '', new, flags=re.M | re.I)
        new = re.sub(r'^Description: A custom theme based on _tw[ \t]*$',
                     f'Description: {site["site_name"]}, a 1:1 WordPress conversion of the static site. Built on _tw.',
                     new, flags=re.M)
        new = re.sub(r'^(Requires PHP:[ \t]*)(\d+)\.(\d+)[^\n]*$',
                     lambda m: m.group(0) if (int(m.group(2)), int(m.group(3))) >= (8, 1) else m.group(1) + PHP_MIN,
                     new, flags=re.M)
        if new != old:
            write(p, new)
            done.append(rel(p) + ' (header)')
    # theme.json: the site's palette and sizes when site.json gives them; otherwise only the starter's sample accent
    # colours go (none of them is the site's). Background and foreground stay: the starter's own CSS reads them.
    tj = os.path.join(theme, 'theme.json')
    if exists(tj):
        try:
            data = json.loads(read(tj))
        except ValueError:
            data = None
            notes.append(f'{rel(tj)} is not valid JSON: its palette was left as it was')
        if isinstance(data, dict):
            settings = data.setdefault('settings', {})
            colour = settings.setdefault('color', {})
            if isinstance(site.get('palette'), list):
                colour['palette'] = site['palette']
            elif isinstance(colour.get('palette'), list):
                colour['palette'] = [c for c in colour['palette'] if str(c.get('color', '')).lower()
                                     not in ('#b91c1c', '#15803d', '#0369a1')]
            for k, src in (('contentSize', 'content_size'), ('wideSize', 'wide_size')):
                if site.get(src):
                    settings.setdefault('layout', {})[k] = site[src]
            text = json.dumps(data, indent='\t', ensure_ascii=False) + '\n'
            if text != read(tj):
                write(tj, text)
                done.append(rel(tj) + ' (palette' + (', sizes' if site.get('content_size') else '') + ')')
    # Kit and tool files the site has no use for.
    if not CHAT:
        move_aside(os.path.join(theme, 'assets', 'chat-save.js'))
    move_aside(os.path.join(theme_root, 'tests', 'parity', 'swap'))  # swaptest.py output, made again when needed
    if starter != 'tw':
        if not BLOG:  # Barebones' post template; the kit answers 404 for posts' archives without a blog
            move_aside(os.path.join(theme, 'single.php'))
        done += abspath_guards()
        return done
    # _tw: its readme stubs, the widget area it registers but never prints, the block editor's heading filter.
    for d in ('js', 'languages'):
        folder = os.path.join(theme, d)
        stub = os.path.join(folder, 'readme.txt')
        if exists(stub):
            only = os.path.isdir(folder) and os.listdir(folder) == ['readme.txt']
            move_aside(folder if only else stub)
    fn_path = os.path.join(theme, 'functions.php')
    edits = [
        ('selective refresh', r"(?:[ \t]*//[^\n]*\n)?[ \t]*add_theme_support\(\s*'customize-selective-refresh-widgets'"
                              r"\s*\);\n(?:[ \t]*\n)?", ''),
        ('footer widget area', r"(?:/\*\*(?:(?!\*/).)*\*/\n)?function \w+_widgets_init\(\)\s*\{.*?\n\}\n"
                               r"add_action\(\s*'widgets_init',\s*'\w+_widgets_init'\s*\);\n(?:\n)?", ''),
        ('heading-level filter', r"(?:/\*\*(?:(?!\*/).)*\*/\n)?function \w+_modify_heading_levels\(.*?\n\}\n"
                                 r"add_filter\(\s*'register_block_type_args',\s*'\w+_modify_heading_levels'[^;]*;\n"
                                 r"(?:\n)?", ''),
    ]
    if not BLOG:
        edits += [
            ('feed links', r"(?:[ \t]*//[^\n]*\n)?[ \t]*add_theme_support\(\s*'automatic-feed-links'\s*\);\n"
                           r"(?:[ \t]*\n)?", ''),
            ('html5 search and comments', r"[ \t]*'(?:search-form|comment-form|comment-list)',\n", ''),
            ('html5 comment', r'for search form, comment form, and comments\n(\s*\*) to output valid HTML5\.',
             r'(the site has no search or comments)\n\1 to output valid HTML5.'),
            ('comment-reply', r"\n\n[ \t]*if \( is_singular\(\) && comments_open\(\)[^\n]*\n[ \t]*wp_enqueue_script\("
                              r"\s*'comment-reply'\s*\);\n[ \t]*\}\n", '\n'),
            ('block editor script', r"(?:/\*\*(?:(?!\*/).)*\*/\n)?function \w+_enqueue_block_editor_script\(\)"
                                    r".*?\n\}\nadd_action\(\s*'enqueue_block_assets',\s*'\w+'\s*\);\n(?:\n)?", ''),
        ]
    done += [f'functions.php: {x}' for x in edit_php(fn_path, edits)]
    if not BLOG:
        done += tidy_tw_blog()
    done += abspath_guards()
    return done


GUARD = "defined( 'ABSPATH' ) || exit;"


def abspath_guards():
    """The starter's own PHP files get the kit's ABSPATH guard (the kit's files have it): a direct request to a
    theme file then exits instead of printing a fatal error with the server path. After the file's docblock."""
    done = []
    for d, dirs, names in os.walk(theme):
        dirs[:] = [x for x in dirs if x not in ('node_modules', 'vendor', 'tests')]
        for n in names:
            f = os.path.join(d, n)
            if not n.endswith('.php') or f in gone or not exists(f):
                continue
            old = read(f)
            if 'ABSPATH' in old:
                continue
            if not old.startswith('<?php'):  # a template that starts with HTML (header.php, footer.php)
                write(f, '<?php ' + GUARD + ' ?>' + chr(10) + old)  # the ?> eats its newline: output unchanged
                done.append(rel(f) + ' (ABSPATH guard)')
                continue
            m = re.match(r'<\?php[ \t]*\n(/\*\*.*?\*/\n)?', old, re.S)
            if m:
                new = old[:m.end()] + ('\n' if m.group(1) else '') + GUARD + '\n' + ('' if m.group(1) else '\n') + \
                    old[m.end():]
            else:  # "<?php get_header(); ?>" on the first line
                new = '<?php\n' + GUARD + '\n' + old[len('<?php'):].lstrip(' \t')
            write(f, new)
            done.append(rel(f) + ' (ABSPATH guard)')
    return done


def tidy_tw_blog():
    """_tw without a blog: its post, archive, search and comment templates go aside, index.php shows the 404 page,
    and the template helpers in inc/ go too once nothing left in the theme calls them."""
    done = []
    for p in ('archive.php', 'search.php', 'single.php', 'comments.php', 'home.php',
              'template-parts/content/content.php', 'template-parts/content/content-excerpt.php',
              'template-parts/content/content-single.php', 'template-parts/content/content-none.php'):
        move_aside(os.path.join(theme, *p.split('/')))
    idx = os.path.join(theme, 'index.php')
    if exists(idx) and 'kit: no blog' not in read(idx):
        move_aside(idx)
        write(idx, f"""<?php
/**
 * The template WordPress falls back to when nothing more specific matches (kit: no blog). The site has only its
 * pages: a listing, a search result or a post answers 404 and shows the 404 page, as the static site does.
 *
 * @link https://developer.wordpress.org/themes/basics/template-hierarchy/
 *
 * @package {prefix}
 */

defined( 'ABSPATH' ) || exit;

if ( ! is_front_page() ) {{
	global $wp_query;
	$wp_query->set_404();
	status_header( 404 );
	nocache_headers();
}}

get_template_part( '404' );
""")
        done.append(rel(idx) + ' (shows the 404 page)')
    # The block editor script only adds the Typography classes to post content: no blog, no use.
    move_aside(os.path.join(theme, 'js', 'block-editor.min.js'))
    move_aside(os.path.join(theme_root, 'javascript', 'block-editor.js'))
    pkg = os.path.join(theme_root, 'package.json')
    if exists(pkg) and ' ./javascript/block-editor.js' in read(pkg):
        write(pkg, read(pkg).replace(' ./javascript/block-editor.js', ''))
        done.append(rel(pkg) + ' (block editor entry)')
    # Templates kept for a plain page: the starter's helpers replaced by the plain markup they print.
    helper_thumb = (f'<?php if ( has_post_thumbnail() && ! post_password_required() ) : ?>\n'
                    f'\t\t<figure><?php the_post_thumbnail(); ?></figure>\n\t<?php endif; ?>')
    page_edits = [
        ('comments', r"\n[ \t]*(?://[^\n]*\n[ \t]*)?if \( comments_open\(\) \|\| get_comments_number\(\) \)\s*[:{]\s*\n"
                     r"\s*comments_template\(\);\s*\n\s*(?:endif;|\})\n", '\n'),
        ('post thumbnail', rf'<\?php {re.escape(prefix)}_post_thumbnail\(\);\s*\?>', lambda m: helper_thumb),
        ('content class', rf"<\?php {re.escape(prefix)}_content_class\(\s*'([^']*)'\s*\);\s*\?>", r'class="\1"'),
    ]
    inc = [os.path.join(theme, 'inc', f) for f in ('template-tags.php', 'template-functions.php')]
    helpers = set()
    for p in inc:
        if exists(p):
            helpers.update(re.findall(r'^function\s+(\w+)\s*\(', read(p), re.M))
    still = []
    for d, dirs, files in os.walk(theme):
        dirs[:] = [x for x in dirs if x not in ('node_modules', 'vendor', '.git')]
        for f in files:
            p = os.path.join(d, f)
            if not f.endswith('.php') or p in inc or not exists(p):
                continue
            done += [f'{rel(p)}: {x}' for x in edit_php(p, page_edits)]
            text = read(p)
            for _, pat, repl in page_edits:  # as written above (a dry run writes nothing, so apply them here too)
                text = re.sub(pat, repl, text, flags=re.S)
            if os.path.basename(p) == 'functions.php':
                text = re.sub(r"require[^\n]*'/inc/template-(?:tags|functions)\.php';", '', text)
            used = sorted(h for h in helpers if re.search(r'\b' + h + r'\b', text))
            if used:
                still.append(f"{rel(p)} ({', '.join(used)})")
    if still:
        notes.append('_tw inc/template-tags.php and template-functions.php kept: still used by ' + '; '.join(still))
    elif any(exists(p) for p in inc):
        req = (r"(?:/\*\*(?:(?!\*/).)*\*/\n)?require(?:_once)? get_template_directory\(\) \. "
               r"'/inc/template-{}\.php';\n(?:\n)?")
        removed_req = edit_php(os.path.join(theme, 'functions.php'),
                               [('template tags', req.format('tags'), ''),
                                ('template functions', req.format('functions'), '')])
        if len(removed_req) == 2 or a.dry_run:
            for p in inc:
                move_aside(p)
            folder = os.path.join(theme, 'inc')
            if os.path.isdir(folder) and not a.dry_run and not os.listdir(folder):
                os.rmdir(folder)  # empty once its two starter files moved aside
            done.append('functions.php: inc/ helpers no longer loaded')
        else:
            notes.append('_tw inc/ helpers kept: functions.php does not load them the usual way, check by hand')
    return done


# 1. The starter theme (skipped with --plan-only: P0 has no WordPress yet; and with --launch-files).
if a.launch_files:
    pass
elif a.plan_only:
    if not os.path.isdir(root) and not a.dry_run:
        os.makedirs(root)
else:
    if not os.path.isdir(root) or not os.path.exists(os.path.join(root, 'wp-includes', 'version.php')):
        sys.exit(f'No WordPress at {root}: install it first (scripts/setup/get-wordpress.py).')
    if not os.path.exists(os.path.join(theme, 'style.css')):
        how = ('Barebones: download github.com/benchmarkstudios/barebones (Code > Download ZIP, or git clone), unzip it '
               f'and rename the folder to {site["theme"]}' if starter == 'barebones' else
               f'_tw: wp scaffold _tw {site["theme"]} --theme_name="{site["site_name"]}" --prefix={prefix} '
               '(after: wp package install underscoretw/scaffold), or generate it on underscoretw.com and unzip it there')
        sys.exit(f'No starter theme at {rel(theme)}/style.css.\n{how}, then run this again.')

    if starter == 'barebones':
        style = read(os.path.join(theme, 'style.css'))
        looks_tw = os.path.exists(os.path.join(theme_root, 'theme', 'functions.php'))
        if looks_tw:
            sys.exit('site.json says "barebones" but this theme looks like _tw (it has a theme/ folder). Check the starter.')
        rename = {'theme_setup': f'{prefix}_setup', 'deregister_scripts': f'{prefix}_deregister_scripts',
                  'editor_styles': f'{prefix}_editor_styles', 'front_page_on_pages_menu': f'{prefix}_front_page_on_pages_menu'}
        words = re.compile(r'\b(' + '|'.join(rename) + r')\b')
        prefixed = re.compile(r'\b(?:barebones|bb)_(?=[a-z])')
        if 'Theme Name: Barebones' in style or os.path.exists(os.path.join(theme, 'includes', 'shortcodes.php')):
            # The sample block, the [button] shortcode, ACF's menu-hiding file and the starter's functions.php go aside.
            for p in ('blocks', 'css/blocks', 'js/blocks', 'includes/blocks.php', 'includes/shortcodes.php',
                      'includes/acf.php', 'functions.php', 'AGENTS.md', 'acf-json/group_6870f0d1f0412.json'):
                move_aside(os.path.join(theme, *p.split('/')))
            changed = []
            for d, dirs, files in os.walk(theme):
                dirs[:] = [x for x in dirs if x not in ('node_modules', 'vendor', '.git')]
                for f in files:
                    p = os.path.join(d, f)
                    if not f.endswith('.php') or any(p == g or p.startswith(g + os.sep) for g in gone):
                        continue
                    old = read(p)
                    new = prefixed.sub(prefix + '_', words.sub(lambda m: rename[m.group(1)], old))
                    new = new.replace("'barebones'", f"'{prefix}'")
                    if f == 'loaders.php':
                        new = new.replace("[ 'jquery' ]", '[]')  # no front-end jQuery: the static site has none
                    if new != old:
                        changed.append(rel(p))
                        write(p, new)
            # Known PHPCS findings in Barebones' own files (escaping, text domains, a WordPress global): exact fixes.
            fixes = [
                ('footer.php', "<?php echo get_bloginfo( 'name' ); ?> <?php echo date('Y'); ?>",
                 "<?php echo esc_html( get_bloginfo( 'name' ) ); ?> <?php echo esc_html( wp_date( 'Y' ) ); ?>"),
                ('single.php', "<?php echo human_time_diff(strtotime($post->post_date)) . ' ' . __('ago'); ?>",
                 f"<?php echo esc_html( human_time_diff( (int) get_post_time( 'U', true ) ) . ' ' . __( 'ago', '{prefix}' ) ); ?>"),
                ('single.php', "comments_popup_link(__('No comments yet'), __('1 comment'), __('% comments'));",
                 f"comments_popup_link( __( 'No comments yet', '{prefix}' ), __( '1 comment', '{prefix}' ), "
                 f"__( '% comments', '{prefix}' ) ); // phpcs:ignore WordPress.WP.I18n.MissingTranslatorsComment -- "
                 f"the starter's own strings; % is the count, as WordPress documents it"),
                ('includes/admin.php', "$submenu['edit.php?post_type=page'][501] = array( \n",
                 "$submenu['edit.php?post_type=page'][501] = array( // phpcs:ignore WordPress.WP.GlobalVariablesOverride"
                 ".Prohibited -- the Front Page link in the Pages menu.\n"),
            ]
            unfixed = []
            for f, find, repl in fixes:
                p = os.path.join(theme, *f.split('/'))
                text = read(p) if os.path.exists(p) else ''
                if find in text:
                    write(p, text.replace(find, repl))
                    changed.append(rel(p)) if rel(p) not in changed else None
                elif repl not in text:
                    unfixed.append(f)
            if unfixed:
                notes.append('PHPCS fixes not applied (Barebones changed?): check ' + ', '.join(sorted(set(unfixed))))
            for p in ('style.css', os.path.join('assets', 'styles', 'style.scss')):
                p = os.path.join(theme, p)
                if os.path.exists(p):
                    old = read(p)
                    new = re.sub(r'Theme Name: Barebones', f'Theme Name: {site["site_name"]}', old)
                    new = re.sub(r'Text Domain: barebones', f'Text Domain: {prefix}', new)
                    new = re.sub(r'Description: .*', f'Description: {site["site_name"]}, a 1:1 WordPress conversion of '
                                 'the static site. Built on Barebones by Benchmark Studios.', new, count=1)
                    if new != old:
                        changed.append(rel(p))
                        write(p, new)
            # Barebones' vite.config.js scans blocks/ for entries: keep the folder (empty) so `npm run build` works.
            if gone and os.path.join(theme, 'blocks') in gone and not a.dry_run:
                write(os.path.join(theme, 'blocks', '.gitkeep'), '')
            # Barebones' sample menu script needs jQuery, which the kit drops from the front end (it would throw on every
            # page): it goes aside and the Vite entry starts empty, for the static site's own vanilla JS.
            sample_js = os.path.join(theme, 'assets', 'scripts', 'scripts.js')
            if exists(sample_js) and 'jQuery' in read(sample_js):
                move_aside(sample_js)
                write(sample_js, "// The site's behaviour in vanilla JS, copied from the static site (same state classes).\n")
            # Lint for the theme's own JS and SCSS (_tw ships its own): ESLint and Prettier, run with `npm run lint`.
            pkg_path = os.path.join(theme, 'package.json')
            if os.path.exists(pkg_path):
                pkg = json.loads(read(pkg_path))
                pkg.setdefault('scripts', {}).update({'lint': 'eslint . && prettier --check .',
                                                      'lint-fix': 'eslint --fix . && prettier --write .'})
                pkg.setdefault('devDependencies', {}).update({'eslint': '^10.0.0', 'prettier': '^3.6.0'})
                write(pkg_path, json.dumps(pkg, indent=2) + '\n')
                for src_name, dst_name in (('eslint.config.js', 'eslint.config.js'),
                                           ('prettier.config.js', 'prettier.config.js'),
                                           ('prettierignore.txt', '.prettierignore')):
                    if not os.path.exists(os.path.join(theme, dst_name)):
                        write(os.path.join(theme, dst_name), read(os.path.join(SKILL, 'assets', 'lint', src_name)))
                changed.append(rel(pkg_path) + ' (lint scripts)')
            notes.append(f'Barebones prepared: {len(changed)} files renamed or updated; moved aside: '
                         + (', '.join(moved) if moved else 'nothing'))
            notes.append('By hand (P1 theme step): includes/admin.php TinyMCE text-size formats (classes the static CSS '
                         'lacks), the Barebones Sass in assets/styles (replaced by the static CSS), index.php welcome text.')
    else:
        fn = os.path.join(theme, 'functions.php')
        if not os.path.exists(fn):
            sys.exit(f'site.json says "tw" but {rel(fn)} is missing: is this a _tw theme?')
        if re.search(r'function\s+_tw_setup\b', read(fn)):
            sys.exit('This _tw copy was not generated (its functions are still named _tw_*). Generate it with the theme '
                     f'slug and prefix: wp scaffold _tw {site["theme"]} --theme_name="{site["site_name"]}" --prefix={prefix} '
                     '--force, or on underscoretw.com.')
        if not re.search(rf'function\s+{prefix}_setup\b', read(fn)):
            notes.append(f'_tw: functions.php has no {prefix}_setup(); was it generated with --prefix={prefix}? '
                         'PHPCS will flag the mix of prefixes.')
        pcs = os.path.join(theme_root, 'phpcs.xml.dist')
        if os.path.exists(pcs) and 'Security, i18n, prefixing' not in read(pcs):
            # _tw's ruleset adds the WordPress formatting rules (long arrays, docs) that the kit's code does not follow;
            # the kit's ruleset keeps security, i18n, prefixes and PHP 8.1 to 8.4, and _tw's own files pass it too.
            move_aside(pcs)
            notes.append("_tw's phpcs.xml.dist moved aside: the kit's ruleset (security, i18n, prefixes, PHP 8.1 to 8.4) "
                         'checks the whole theme')
    _before = len(moved)
    _tidied = tidy_starter()
    if _tidied or len(moved) > _before:
        # One line: the counts; the moved files are in _setup/starter-removed/ (the way back), the edits in git diff.
        notes.append(f"starter tidied for this site ({'blog kept' if BLOG else 'no blog'}, "
                     f"{'chat' if CHAT else 'no chat'}): {len(_tidied)} edits, {len(moved) - _before} files moved "
                     'aside to _setup/starter-removed/')


# 2 and 3. What to copy where: (source, destination).
plan = []


def add_tree(src, dst):
    for d, dirs, files in os.walk(src):
        dirs[:] = [x for x in dirs if x not in ('node_modules', '__pycache__', 'report', 'shots')]
        for f in files:
            s = os.path.join(d, f)
            plan.append((s, os.path.join(dst, os.path.relpath(s, src))))


A, S = os.path.join(SKILL, 'assets'), HERE
if not a.plan_only:
    for folder in ('includes', 'template-parts', 'assets'):
        add_tree(os.path.join(A, 'theme', folder), os.path.join(theme, folder))
    for f in ('AGENTS.md', 'phpcs.xml.dist', 'composer.json'):
        plan.append((os.path.join(A, 'theme', f), os.path.join(theme_root, f)))
    add_tree(os.path.join(S, 'parity'), os.path.join(theme_root, 'tests', 'parity'))
    # Files that travel in the package so a staging copy stays staging after a Duplicator import (which replaces
    # wp-config, the root .htaccess and the Reading setting): the environment by host, and the private-file block
    # inside acf-json/.
    plan.append((os.path.join(A, 'theme', 'acf-json', '.htaccess'), os.path.join(theme, 'acf-json', '.htaccess')))
    plan.append((os.path.join(A, 'mu-plugin', 'kitwp-environment.php'),
                 os.path.join(root, 'wp-content', 'mu-plugins', f'{prefix}-environment.php')))
for tool in ('acf', 'seed', 'build-map', 'report', 'launch', 'setup'):
    add_tree(os.path.join(S, tool), os.path.join(root, '_plan', 'tools', tool))
for f in ('analyze-source.py', 'snapshot-routes.mjs'):
    plan.append((os.path.join(S, f), os.path.join(root, '_plan', 'tools', f)))
add_tree(os.path.join(A, 'seed'), os.path.join(root, '_setup', 'seed'))
add_tree(os.path.join(A, 'handover'), os.path.join(root, '_setup', 'handover'))
if not a.plan_only and branding.get('email_badge_png'):
    plan.append((branding['email_badge_png'], os.path.join(theme, 'assets', 'email', os.path.basename(branding['email_badge_png']))))
if not a.plan_only and branding.get('site_badge'):
    plan.append((branding['site_badge'], os.path.join(theme, 'assets', 'brand', os.path.basename(branding['site_badge']))))
for f in sorted(os.listdir(os.path.join(A, 'plan'))):
    plan.append((os.path.join(A, 'plan', f), os.path.join(root, '_plan', f.replace('.template', ''))))
plan += [
    (os.path.join(A, 'build-map', 'BUILD-MAP.template.md'), os.path.join(root, 'BUILD-MAP.md')),
    (os.path.join(A, 'handoff', 'handoff.template.md'), os.path.join(root, 'handoff.md')),
    (os.path.join(A, 'handoff', 'ai-handoff-summary.template.md'), os.path.join(root, 'ai-handoff-summary.md')),
    (os.path.join(A, 'launch', 'RUNBOOK.template.md'), os.path.join(root, '_setup', 'launch', 'RUNBOOK.md')),
    (os.path.join(A, 'launch', 'htaccess-live.txt'), os.path.join(root, '_setup', 'launch', 'htaccess-live.txt')),
    (os.path.join(A, 'launch', 'maintenance', 'maintenance.html'), os.path.join(root, '_setup', 'launch', 'maintenance', 'maintenance.html')),
    (os.path.join(A, 'launch', 'maintenance', 'htaccess-maintenance.txt'), os.path.join(root, '_setup', 'launch', 'maintenance', 'htaccess-maintenance.txt')),
    (os.path.join(A, 'report', 'report-template.html'), os.path.join(root, '_setup', 'launch', 'report.html')),
]
# The chat lead pattern ships only for a site with a chat (site.json "chat"); an unused kit file is lint noise.
if not CHAT:
    plan = [(s, d) for s, d in plan if not d.endswith(os.path.join('assets', 'chat-save.js'))]
# --launch-files: only the runbook and the live .htaccess, written again (the old ones kept, see below).
LAUNCH = tuple(os.path.join(root, '_setup', 'launch', f) for f in ('RUNBOOK.md', 'htaccess-live.txt'))
if a.launch_files:
    plan = [(s, d) for s, d in plan if d in LAUNCH]

# The project's own documents and data are never overwritten, not even with --force: the plan, the board, the
# handoff files, the seed data and the launch files belong to the project once written.
PROTECTED = ('BUILD-MAP.md', 'handoff.md', 'ai-handoff-summary.md', '_setup/seed/', '_setup/launch/', '_setup/handover/')
# Kit files that hold the project's own data once filled: the content model spec, the routes, the parity settings.
PROJECT_DATA = ('_plan/tools/acf/build_field_groups.py', '/tests/parity/routes.json', '/tests/parity/parity.config.json')
stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
written, kept, backed = [], [], []

# analyze-source.py --json <wp_root>/_plan/analyze.json (start.py writes it) fills PLAN.md's source table.
an_path = os.path.join(os.path.dirname(os.path.abspath(a.site_json)), "analyze.json")
an = json.load(open(an_path, encoding='utf-8')) if os.path.exists(an_path) else None


def source_rows(text):
    if not an:
        return text
    j = lambda xs, n=8: ', '.join(map(str, (xs or [])[:n])) or '-'
    tw = an.get('tailwind')
    nx = an.get('next') or {}
    rows = {
        'Stack': an.get('stack', '?') + (f" (Next {nx.get('version')}, static export {nx.get('static_export')})" if nx else ''),
        'Build command and output': ', '.join(f'{k}: {v}' for k, v in (an.get('scripts') or {}).items() if 'build' in k)
                                    + ('; built: ' + ', '.join(an['built_output']) if an.get('built_output') else '') or '-',
        'Tailwind': (f"yes, {tw.get('dependency') or 'version?'}, config {tw.get('config') or 'none'}" if tw else 'no')
                    + f" -> {an.get('starter_theme')}",
        'Routes': f"{len(an.get('routes', []))}: {j(an.get('routes'), 30)}"
                  + (f"; dynamic: {j(an.get('dynamic_routes'))}" if an.get('dynamic_routes') else ''),
        'Content': j(an.get('content_sources')),
        'Images': f"next/image imports {an.get('next_image_imports', 0)}" + (f", widths {nx.get('srcset_widths')}" if nx else ''),
        'Fonts': j(an.get('fonts')),
        'Icons': j((an.get('icons') or []) + (an.get('libraries') or [])),
        'Forms': j(an.get('forms')) + (f"; mail sent by {j(an.get('mail_handlers'), 3)}" if an.get('mail_handlers') else ''),
        'Tracking': j(an.get('tracking')),
        'Redirects': j(an.get('redirect_sources')),
    }
    for k, v in rows.items():
        text = re.sub(r'^\| ' + re.escape(k) + r' \|[^\n]*\|$', lambda m: f'| {k} | {v.replace("|", "/")} |', text, count=1, flags=re.M)
    gm = an.get('golden_master')
    if gm:
        text = text.replace("How it is produced and where it is served (see the skill's references/source-types.md).",
                            f'From analyze-source.py: {gm}', 1)
    if an.get('private_files'):
        text = text.replace('<!-- kit:secrets -->', '**Secrets and personal data in the source** (never copied, never '
                            'read): ' + ', '.join(f'`{x}`' for x in an['private_files']), 1)
    return text


def parity_tune(dst, text):
    # The parity routes and the reveal rule from what analyze-source.py found.
    if not an:
        return text
    if dst.endswith(os.path.join('parity', 'routes.json')):
        routes = [x for x in an.get('routes', []) if '[' not in x and ':' not in x]
        if routes:
            if not any('thank' in x for x in routes):
                routes.append('/thank-you/')
            return json.dumps(routes + ['/parity-missing-page/']) + '\n'
    if dst.endswith(os.path.join('parity', 'parity.config.json')) and 'AOS' in (an.get('libraries') or []):
        cfg = json.loads(text)
        cfg['reveal'] = {'selector': '[data-aos]', 'addClass': 'aos-animate'}
        return json.dumps(cfg, indent=2) + '\n'
    return text


def intake_notes(dst):
    """The notes of an intake handoff file (new-site.py --start), or None for a real project file."""
    if not os.path.exists(dst):
        return None
    text = read(dst)
    if INTAKE not in text:
        return None
    return text.replace(INTAKE, '').strip()


for src, dst in plan:
    if not os.path.exists(src):
        continue
    r = rel(dst)
    carried = intake_notes(dst) if r in ('handoff.md', 'ai-handoff-summary.md') else None
    if carried is not None:
        new = fill(read(src))
        if r == 'handoff.md':
            body = '\n'.join(l for l in carried.splitlines() if not l.startswith('# Handoff:'))
            note = '\n### Intake notes (kept from the intake handoff)\n\n' + body.strip() + '\n\n'
            new = new.replace('## Failed Attempts', note + '## Failed Attempts', 1) if '## Failed Attempts' in new \
                else new + note
        written.append(r + ' (replaces the intake file)')
        write(dst, new)
        continue
    if exists(dst) and a.launch_files:
        # The launch files are the project's once written; asked for again, the old copy stays next to them.
        backed.append(r)
        if not a.dry_run:
            bak = os.path.join(root, '_setup', 'launch', 'before-' + stamp, os.path.basename(dst))
            os.makedirs(os.path.dirname(bak), exist_ok=True)
            shutil.copy2(dst, bak)
    elif exists(dst):
        project_doc = (r.startswith(PROTECTED) or r.endswith(PROJECT_DATA)
                       or (r.startswith('_plan/') and not r.startswith('_plan/tools/')))
        if not a.force or project_doc:
            kept.append(r)
            continue
        # --force updates kit code; the version being replaced is kept, since a build edits these files too.
        backed.append(r)
        if not a.dry_run:
            bak = os.path.join(root, '_setup', 'kit-backup-' + stamp, *r.split('/'))
            os.makedirs(os.path.dirname(bak), exist_ok=True)
            shutil.copy2(dst, bak)
    written.append(r)
    if src.endswith(TEXT) or os.path.basename(src).startswith('.'):
        if dst.endswith(os.sep + 'PLAN.md'):
            write(dst, source_rows(fill(read(src))).replace('<!-- kit:secrets -->\n\n', ''))
        else:
            write(dst, parity_tune(dst, fill(read(src))))
    elif not a.dry_run:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        os.chmod(dst, 0o644)
if a.launch_files:
    print(f"{'DRY RUN: ' if a.dry_run else ''}OK new-site: launch files written: {', '.join(written) or 'none'}"
          + (f'; the old ones are in _setup/launch/before-{stamp}/' if backed else ''))
    print(f"live https://{LIVE_HOST} ({'www' if WWW else 'no www'}); forms: {values['FORMS_LIST'] or 'none'}; "
          + ', '.join(f"{k} {'yes' if FLAGS[k] else 'no'}" for k in ('redirects', 'tracking', 'chat', 'portal')))
    for n in notes:
        print('- ' + n)
    sys.exit(0)
if backed:
    notes.append(f'--force: {len(backed)} kit files replaced; the replaced versions are in _setup/kit-backup-{stamp}/')

if not a.plan_only and not os.path.isdir(os.path.join(theme, 'acf-json')):
    written.append(rel(os.path.join(theme, 'acf-json')) + '/')
    if not a.dry_run:
        os.makedirs(os.path.join(theme, 'acf-json'))
# ACF reads the field definitions from disk; visitors never need them (a real build served them with 200). The
# live .htaccess closes the folder too, in case a package leaves this dotfile out.
acf_ht = os.path.join(theme, 'acf-json', '.htaccess')
if not a.plan_only and not os.path.exists(acf_ht):
    written.append(rel(acf_ht))
    write(acf_ht, '# ACF reads these field definitions from disk; visitors never need them.\n'
                  '<IfModule mod_authz_core.c>\n\tRequire all denied\n</IfModule>\n'
                  '<IfModule !mod_authz_core.c>\n\tOrder deny,allow\n\tDeny from all\n</IfModule>\n')

# functions.php: Barebones gets the kit's (the starter's own was moved aside); _tw keeps its own plus the kit lines.
fn = os.path.join(theme, 'functions.php')
kit_list = '[ ' + ', '.join(f"'{f}'" for f in KIT_FILES) + ' ]'
kit_block = ('\n// Conversion kit (convert-to-wordpress): config first, seed.php before seed-pages.php. seed, seed-pages and\n'
             '// snapshot do nothing outside WP_ENVIRONMENT_TYPE "local". After every PHP save: php -l, PHPCS, and\n'
             "// grep -h \"^function\" includes/*.php | sed 's/(.*//' | sort | uniq -d   (must print nothing)\n"
             f'foreach ( {kit_list} as ${prefix}_kit_file ) {{\n'
             f"\trequire_once get_template_directory() . '/includes/' . ${prefix}_kit_file . '.php';\n}}\n")
if a.plan_only:
    pass
elif not exists(fn):
    written.append(rel(fn))
    write(fn, fill(read(os.path.join(A, 'theme', 'functions.php'))))
elif "'seed-pages'" not in read(fn):
    text = read(fn).rstrip()
    if text.endswith('?>'):
        text = text[:-2].rstrip()
    write(fn, text + '\n' + kit_block)
    notes.append(f'{rel(fn)}: the kit lines were added at the end')

# The root .htaccess: the private-files block first.
ht = os.path.join(root, '.htaccess')
block = read(os.path.join(A, 'launch', 'htaccess-local.txt'))
if not os.path.exists(ht):
    write(ht, block)
    notes.append('.htaccess created with the private-files block (WordPress adds its block below when permalinks are saved)')
elif 'BEGIN Private project files' not in read(ht):
    if not a.dry_run:
        os.makedirs(os.path.join(root, '_setup'), exist_ok=True)
        shutil.copyfile(ht, os.path.join(root, '_setup', 'htaccess.before-kit'))
    write(ht, block + '\n' + read(ht))
    notes.append('.htaccess: the private-files block was added at the top (the old file: _setup/htaccess.before-kit)')

left = set()
if not a.dry_run:
    for _, dst in plan:  # the tools keep their own runtime placeholders ({{SITE}} in the board template)
        if os.path.exists(dst) and dst.endswith(TEXT) and not rel(dst).startswith('_plan/tools/'):
            left.update(re.findall(r'\{\{([A-Z_]+)\}\}', read(dst)))

print(f"{'DRY RUN: ' if a.dry_run else ''}{len(written)} written, {len(kept)} kept (already there)")
print(f'theme: {rel(theme)} (starter {values["STARTER"]}), functions prefix {prefix}_, ACF keys {key}'
      + (' (not written yet: --plan-only)' if a.plan_only else ''))
if values['LEADS_ITEM'].startswith('BLOCKER'):
    notes.append('leads portal: none in the profile (leads_portal): a go-live blocker for a site with '
                 'a lead form; a site without one: site.json "leads_portal": "none: <reason>"')
for n in notes:
    print('- ' + n)
if kept:
    print('kept: ' + ', '.join(kept[:12]) + (f' and {len(kept) - 12} more' if len(kept) > 12 else ''))
if left:
    print('placeholders still to fill: ' + ', '.join(sorted(left)))
build = 'npm install && npm run build' if starter == 'barebones' else 'npm install && npm run dev'
if a.plan_only:
    print('next: P0 planning in _plan/PLAN.md, CONTENT-MODEL.md, OLD-SITE-URLS.md and BUILD-MAP.md; after the Plan OK, '
          '_plan/tools/setup/setup.py, the starter theme, then this again without --plan-only.')
else:
    print(f'next: in {rel(theme_root)}: {build}; npm run lint-fix once, then npm run lint; php -l and PHPCS on the '
          'theme; activate it; then the P1 steps.')
