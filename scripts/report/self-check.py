#!/usr/bin/env python3
"""Pre-QA self-check: the finding classes a build can catch itself, run before every QA run so QA finds fewer.

    python3 self-check.py <wp_root> [--theme <name or folder>] [--url http://site.test]
                          [--profile <kit>/profile.local.json] [--wp "<WP-CLI command>"] [-v]

It checks less than QA does, never instead of QA: the classes that cost a real build 4 QA runs (launch files,
dead code, field instructions, unsafe casts). Line 1: "OK self-check: 0 found" or "FAIL self-check: <n> found";
then one line per finding: "<class>: <where>: <what>". Exit 1 when anything is found. Classes:
  instructions   an ACF field (acf-json) without instructions, or with developer words in them
  repeater       (array) on a field read: an empty repeater is false and (array) false is [false]: kitwp_rows()
  abspath        a theme PHP file without the ABSPATH guard (a direct request prints the server path)
  phpcs-ignore   a phpcs:ignore without its reason after " -- "
  php-gap        "?>" and "<?php" with only whitespace between: prints a blank line (in <head>, too)
  unused         a theme function defined and never called or hooked
  missing-file   a theme file path in the code that does not exist (a fallback logo, a favicon)
  size           a theme PHP or JS file over 300 lines (the guide is about 250, one job per file)
  leftover       starter or kit leftovers: readme.txt files, the starter's author, feed links, a starter palette
  launch         _setup/launch: an unfilled {{TOKEN}}, a doubled www in the host rule, acf-json or readme.html not
                 denied in htaccess-live.txt
  public         with --url: the acf-json files answer 200, or oEmbed shows the author
  lead-storage   the theme or a must-use plugin stores leads itself: CREATE TABLE or dbDelta, a $wpdb write, or a
                 register_post_type / add_menu_page / add_submenu_page named for enquiries, leads, submissions,
                 contacts, messages or form entries (leads are stored by Contact Form CFDB7 on live only)
  tracking       with --profile naming a tracking plugin (tracking.plugin): the theme loads GTM itself or has ACF
                 tracking fields (GTM, head or body scripts): tracking goes through that plugin only
  branding       a kit theme without the agency badge in its footer (no <prefix>_agency_badge() call), or without
                 its default image or link in config.php; a seeded form (_setup/seed/forms.json) whose email or
                 auto-reply template is not the branded HTML one (logo and badge mail-tags); with --url: the home
                 page has no badge, linked; with --wp (WP-CLI, for example --wp wp): a CF7 form's email or auto-reply
                 in the database is not the branded HTML template. The badge parts are skipped when config.php's
                 <PREFIX>_BADGE_HIDE_NOTE records that the client asked (site.json "agency_badge_hide")
"""
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import branding_check  # noqa: E402 (the shared branding checks, next to this script)

LAYOUT = {'tab', 'message', 'accordion', 'group', 'repeater', 'flexible_content', 'clone'}
DEV_WORDS = re.compile(r'\b(slug|token|array|repeater|post type|taxonomy|hook|constant|meta key|field key|'
                       r'developer key|php|json)\b', re.I)
PLAIN_TOKEN = re.compile(r'\b(write|type|shows?|replaced|becomes)\b|\}\s*(=|is\b|means\b)', re.I)
# A field read cast to array: an empty repeater is false and (array) false is [false]. get_option() takes a default
# and a cast wrapped in array_filter() drops the false, so neither is flagged.
CAST = re.compile(r'(?<!array_filter\( )\(\s*array\s*\)\s*(get_field|get_sub_field|[a-z0-9]+_(field|setting|'
                  r'sub_field))\s*\(')
GTM_CODE = re.compile(r'googletagmanager\.com/(gtm\.js|ns\.html)|\bGTM-(?!X+\b)[A-Z0-9]{5,}\b')
TRACK_FIELD = re.compile(r'(^|_)(gtm|tag_manager|tracking|head_scripts?|body_scripts?|header_(code|scripts?)|'
                         r'footer_(code|scripts?)|analytics)(_|$)', re.I)
LEAD_WORDS = re.compile(r'enquir|inquir|lead|submission|contact|message|form[-_ ]?entr', re.I)
TABLE_MAKE = re.compile(r'CREATE\s+TABLE|\bdbDelta\s*\(', re.I)
WPDB_WRITE = re.compile(r'\$wpdb\s*->\s*(insert|replace|update|query)\s*\(', re.I)
LEAD_CALL = re.compile(r'\b(register_post_type|add_menu_page|add_submenu_page)\s*\(')
# The kit's own files (theme-relative, and the must-use files by their end), skipped by lead-storage.
KIT_FILES = {'includes/acf.php', 'includes/cleanup.php', 'includes/client-admin.php', 'includes/config.php',
             'includes/forms-attribution.php', 'includes/forms-controls.php', 'includes/forms-lead-source.php',
             'includes/forms-local-mail.php', 'includes/forms-mail.php', 'includes/forms-portal.php',
             'includes/forms-spam.php', 'includes/forms.php', 'includes/head.php', 'includes/helpers-maps.php',
             'includes/helpers.php', 'includes/media-svg.php', 'includes/media.php', 'includes/schema.php',
             'includes/seed-forms.php', 'includes/seed-media.php', 'includes/seed-menus.php',
             'includes/seed-pages.php', 'includes/seed-seo.php', 'includes/seed-settings.php', 'includes/seed.php',
             'includes/seo.php', 'includes/snapshot.php', 'template-parts/sections/lead-form.php'}
KIT_MU = ('-environment.php', '-lead-source.php')
SKIP_DIRS = ('node_modules', 'vendor', 'tests', '.git', 'acf-json', 'starter-removed', 'dist', 'build')


def files(root, exts):
    for d, dirs, names in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for n in names:
            if n.endswith(exts) and not n.endswith('.min.js'):
                yield os.path.join(d, n)


def read(p):
    try:
        with open(p, encoding='utf-8', errors='replace') as fh:
            return fh.read()
    except OSError:
        return ''


def resolve_theme(wp_root, value):
    """--theme as a folder name under wp-content/themes, a path from the WordPress root or this folder, or a full path.
    A _tw theme's outer folder gives its theme/ folder (the part WordPress loads)."""
    for cand in ([value] if os.path.isabs(value) else
                 [os.path.join(wp_root, 'wp-content', 'themes', value), os.path.join(wp_root, value), value]):
        if os.path.isdir(cand):
            inner = os.path.join(cand, 'theme')
            if not os.path.isfile(os.path.join(cand, 'functions.php')) and \
                    os.path.isfile(os.path.join(inner, 'functions.php')):
                cand = inner
            return os.path.abspath(cand)
    return None


def find_theme(wp_root):
    """The kit theme: the folder under wp-content/themes with includes/config.php next to functions.php."""
    for cfg in glob.glob(os.path.join(wp_root, 'wp-content', 'themes', '*', '**', 'includes', 'config.php'),
                         recursive=True):
        d = os.path.dirname(os.path.dirname(cfg))
        if os.path.isfile(os.path.join(d, 'functions.php')) and 'node_modules' not in d:
            return d
    return None


def dev_word(text):
    # A {token} is fine when the instruction says what to do with it ("Write {phone} to show the number").
    m = DEV_WORDS.search(text)
    if m:
        return m.group(0)
    m = re.search(r'\{[a-z_]+\}', text)
    return m.group(0) if m and not PLAIN_TOKEN.search(text) else ''


def check_instructions(theme, out):
    for p in glob.glob(os.path.join(theme, 'acf-json', '*.json')):
        try:
            group = json.loads(read(p))
        except ValueError:
            continue

        def walk(fields, trail):
            for f in fields or []:
                label = f'{trail} > {f.get("label") or f.get("name")}'
                text = (f.get('instructions') or '').strip()
                if f.get('type') not in LAYOUT and not text:
                    out.append(('instructions', os.path.basename(p), f'{label}: no instructions'))
                elif text and dev_word(text):
                    out.append(('instructions', os.path.basename(p),
                                f'{label}: developer words ("{dev_word(text)}"): say it plainly'))
                walk(f.get('sub_fields'), label)
                for lay in f.get('layouts') or []:
                    walk(lay.get('sub_fields'), f'{label} > {lay.get("label")}')
        walk(group.get('fields'), group.get('title', ''))


def check_php(theme, out):
    php = list(files(theme, ('.php',)))
    sources = {p: read(p) for p in php}
    js = {p: read(p) for p in files(theme, ('.js',))}
    every = '\n'.join(list(sources.values()) + list(js.values()))
    # Functions called by a built name ('prefix_seed_' . $step) count as used.
    dynamic = set(re.findall(r"['\"]([a-z0-9_]+_)['\"]\s*\.", every, re.I))
    for p, s in sources.items():
        rel = os.path.relpath(p, theme).replace('\\', '/')
        for i, line in enumerate(s.splitlines(), 1):
            cast = CAST.search(line)
            if cast and 'array_filter(' not in line[:cast.start()]:
                out.append(('repeater', f'{rel}:{i}', 'use kitwp_rows() (or the site prefix\'s) for a field read'))
            if 'phpcs:ignore' in line and ' -- ' not in line:
                out.append(('phpcs-ignore', f'{rel}:{i}', 'say why after " -- "'))
        if not re.search(r"defined\(\s*'ABSPATH'\s*\)", s):
            out.append(('abspath', rel, "add defined( 'ABSPATH' ) || exit; after the file header"))
        for m in re.finditer(r'\?>\s*<\?php', s) if rel.startswith('includes/') else ():
            if 'ob_start(' in s[max(0, m.start() - 300):m.start()]:
                continue  # buffered and trimmed: nothing reaches the page
            out.append(('php-gap', f'{rel}:{s[:m.start()].count(chr(10)) + 1}', 'remove the ?> <?php pair'))
        for m in re.finditer(r'^function\s+([a-z0-9_]+)\s*\(', s, re.M | re.I):
            if any(m.group(1).startswith(d) for d in dynamic):
                continue
            if len(re.findall(r'\b' + re.escape(m.group(1)) + r'\b', every)) < 2:
                out.append(('unused', f'{rel}:{s[:m.start()].count(chr(10)) + 1}',
                            f'{m.group(1)}() is never called: remove it (and its PHPCS allow-list entry)'))
        for m in re.finditer(r"(?:get_theme_file_(?:uri|path)|get_template_directory_uri\(\)\s*\.)\s*\(?\s*'/?"
                             r"([\w./-]+\.(?:png|jpe?g|svg|webp|ico|css|js))'", s):
            line = s[s.rfind(chr(10), 0, m.start()) + 1:s.find(chr(10), m.end())]
            if 'file_exists(' in line or 'is_file(' in line:
                continue  # the code checks the file itself before using it
            if not os.path.isfile(os.path.join(theme, m.group(1).lstrip('/'))):
                out.append(('missing-file', rel, f'{m.group(1)} does not exist in the theme'))
    for p, s in list(sources.items()) + list(js.items()):
        n = s.count('\n')
        if n > 300:
            out.append(('size', os.path.relpath(p, theme).replace('\\', '/'), f'{n} lines: split it by job'))


def check_leftovers(theme, out):
    for d, dirs, names in os.walk(theme):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for n in names:
            rel = os.path.relpath(os.path.join(d, n), theme).replace('\\', '/')
            if re.search(r'(^|/)(js|languages)/readme\.txt$', rel):
                out.append(('leftover', rel, 'starter file: move it to _setup/starter-removed/'))
    style = read(os.path.join(theme, 'style.css'))
    # The starter's credit line ("based on _tw ...") stays: the GPL asks for it. Its header fields do not.
    if re.search(r'^(Theme URI|Author|Author URI):.*(underscoretw|barebones)|^Requires PHP:\s*7\.', style,
                 re.M | re.I):
        out.append(('leftover', 'style.css', 'the starter\'s author, URI or Requires PHP: the site\'s own header'))
    funcs = read(os.path.join(theme, 'functions.php'))
    if 'automatic-feed-links' in funcs:
        out.append(('leftover', 'functions.php', 'automatic-feed-links: the site has no feeds (the kit 404s them)'))
    tj = read(os.path.join(theme, 'theme.json'))
    if re.search(r'#(b91c1c|15803d|0369a1)\b', tj, re.I):
        out.append(('leftover', 'theme.json', 'the starter palette: the site\'s colours or none'))


def check_launch(wp_root, out):
    launch = os.path.join(wp_root, '_setup', 'launch')
    for p in glob.glob(os.path.join(launch, '*.md')) + glob.glob(os.path.join(launch, '*.txt')):
        s, rel = read(p), os.path.relpath(p, wp_root).replace('\\', '/')
        for tok in sorted(set(re.findall(r'\{\{[A-Z_]+\}\}', s))):
            out.append(('launch', rel, f'{tok} is not filled'))
        if p.endswith('htaccess-live.txt'):
            if re.search(r'www\\?\.www\\?\.', s):
                out.append(('launch', rel, 'the host rule reads www.www.: the bare domain would never redirect'))
            for need, what in (('acf-json', 'the theme\'s acf-json folder'), ('readme', 'readme.html')):
                if need not in s:
                    out.append(('launch', rel, f'{what} is not denied'))


def check_public(url, wp_root, theme, out):
    url = url.rstrip('/')
    rel = os.path.relpath(theme, wp_root).replace('\\', '/')
    for p in glob.glob(os.path.join(theme, 'acf-json', '*.json'))[:1]:
        target = f'{url}/{rel}/acf-json/{os.path.basename(p)}'
        if status(target) == 200:
            out.append(('public', target, 'answers 200: deny the folder (acf-json/.htaccess, htaccess-live)'))
    body = fetch(f'{url}/wp-json/oembed/1.0/embed?url={url}/')
    if '"author_name"' in body or '"author_url"' in body:
        out.append(('public', '/wp-json/oembed/1.0/embed', 'shows the author: drop author_name and author_url'))


def check_lead_storage(theme, wp_root, out):
    """Leads are stored by Contact Form CFDB7 on live only: no table, write, post type or admin page of the build's
    own for them, in the theme or a must-use plugin. Each call is read up to its ";" so a call over lines counts."""
    places = [(p, os.path.relpath(p, theme).replace(os.sep, '/')) for p in files(theme, ('.php',))]
    mu = os.path.join(wp_root, 'wp-content', 'mu-plugins')
    places += [(p, 'mu-plugins/' + os.path.relpath(p, mu).replace(os.sep, '/')) for p in files(mu, ('.php',))]
    for p, rel in places:
        if rel in KIT_FILES or (rel.startswith('mu-plugins/') and rel.count('/') == 1 and rel.endswith(KIT_MU)):
            continue
        s = read(p)
        hits = [(m, 'creates a table') for m in TABLE_MAKE.finditer(s)]
        for rx, what in ((WPDB_WRITE, 'writes with $wpdb'), (LEAD_CALL, None)):
            for m in rx.finditer(s):
                end = s.find(';', m.end())
                call = s[m.start():end if end != -1 else len(s)][:400]
                if LEAD_WORDS.search(call):
                    hits.append((m, what or f'{m.group(1)} for enquiries'))
        lines = {}  # one finding per line: a table created wins over the write that runs it
        for m, what in hits:
            lines.setdefault(s[:m.start()].count(chr(10)) + 1, what)
        for n in sorted(lines):
            out.append(('lead-storage', f'{rel}:{n}',
                        f'{lines[n]}: leads are stored by Contact Form CFDB7 on live only, remove it'))


def check_tracking(theme, profile, out):
    """With a tracking plugin in the profile, the theme has no tracking of its own."""
    try:
        with open(profile, encoding='utf-8') as fh:
            plugin = str((json.load(fh).get('tracking') or {}).get('plugin') or '').strip()
    except (OSError, ValueError):
        return
    if not plugin:
        return
    for p in files(theme, ('.php', '.js')):
        for n, line in enumerate(read(p).splitlines(), 1):
            if GTM_CODE.search(line):
                out.append(('tracking', f"{os.path.relpath(p, theme).replace(os.sep, '/')}:{n}",
                            f'the theme loads GTM: tracking goes through {plugin} only, remove it'))
    for p in glob.glob(os.path.join(theme, 'acf-json', '*.json')):
        try:
            group = json.loads(read(p))
        except ValueError:
            continue
        stack = list(group.get('fields') or [])
        while stack:
            f = stack.pop()
            if TRACK_FIELD.search(str(f.get('name') or '')):
                out.append(('tracking', os.path.basename(p), f'ACF tracking field "{f.get("name")}": tracking goes '
                            f'through {plugin} only, remove the field'))
            stack += list(f.get('sub_fields') or [])
            for lay in f.get('layouts') or []:
                stack += list(lay.get('sub_fields') or [])


def check_branding(theme, wp_root, url, wp, out):
    """The agency badge in the footer and the branded emails (kit themes only: they define <prefix>_agency_badge())."""
    php = {os.path.relpath(p, theme).replace(os.sep, '/'): read(p) for p in files(theme, ('.php',))}
    if not any(re.search(r'function\s+[a-z0-9]+_agency_badge\s*\(', s) for s in php.values()):
        return
    config = next((s for rel, s in php.items() if rel.endswith('includes/config.php')), '')
    note = re.search(r"_BADGE_HIDE_NOTE\s*=\s*'([^']*)'", config)
    hidden = bool(note and note.group(1).strip() and '{{' not in note.group(1))
    if not hidden:
        # A call in a template (the footer), comments left out: the kit's includes/ only define and mention it.
        calls = [rel for rel, s in php.items() if '/includes/' not in '/' + rel and re.search(
            r'(?<!function )\b[a-z0-9]+_agency_badge\s*\(', re.sub(r'/\*.*?\*/|//[^\n]*', '', s, flags=re.S))]
        if not calls:
            out.append(('branding', 'footer', 'no agency badge: call <prefix>_agency_badge() in the footer\'s bottom '
                        'bar (add one in the footer\'s style when the design has none)'))
        for const, what in (('SITE_BADGE', 'footer badge image'), ('SITE_BADGE_LINK', 'badge link'),
                            ('EMAIL_BADGE', 'email badge PNG'), ('EMAIL_BADGE_LINK', 'email badge link')):
            m = re.search(r"_%s\s*=\s*'([^']*)'" % const, config)
            if m and (not m.group(1).strip() or '{{' in m.group(1)):
                out.append(('branding', 'includes/config.php', f'no default {what} ({const}): fill the profile\'s '
                            'branding and run new-site.py again'))
        if url:
            why = branding_check.badge_problem(fetch(url.rstrip('/') + '/'))
            if why:
                out.append(('branding', url, why))
    seed = os.path.join(wp_root, '_setup', 'seed')
    try:
        with open(os.path.join(seed, 'forms.json'), encoding='utf-8') as fh:
            forms = json.load(fh)
    except (OSError, ValueError):
        forms = {}
    for key, form in (forms.items() if isinstance(forms, dict) else []):
        for field, name in (('body_file', 'email'), ('autoreply_file', 'auto-reply')):
            f = (form or {}).get(field) if isinstance(form, dict) else None
            body = read(os.path.join(seed, f)) if f and os.path.isfile(os.path.join(seed, f)) else ''
            why = branding_check.template_problem(body) if body else f'no {field}'
            if why:
                out.append(('branding', f'_setup/seed/forms.json {key}', f'{name}: {why}'))
    if wp:
        mails, why = branding_check.read_mails(wp, wp_root)
        if mails is None:
            out.append(('branding', 'WP-CLI', f'CF7 emails not checked: {why}'))
        for form, what in branding_check.mail_problems(mails or []):
            out.append(('branding', f'CF7 "{form}"', what))


def status(url):
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, OSError):
        return 0


def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return r.read().decode('utf-8', 'replace')
    except (urllib.error.URLError, OSError):
        return ''


def main(argv):
    args = [a for a in argv if a != '-v']
    opt = {}
    for k in ('--theme', '--url', '--profile', '--wp'):
        if k in args:
            i = args.index(k)
            opt[k] = args[i + 1]
            del args[i:i + 2]
    if not args:
        print(__doc__)
        return 2
    wp_root = args[0]
    theme = resolve_theme(wp_root, opt['--theme']) if opt.get('--theme') else find_theme(wp_root)
    if not theme or not os.path.isdir(theme):
        print(f'FAIL self-check: no theme folder "{opt["--theme"]}" (a name under wp-content/themes, or a path)'
              if opt.get('--theme') else
              f'FAIL self-check: no kit theme found under {wp_root}/wp-content/themes (pass --theme)')
        return 2
    out = []
    check_instructions(theme, out)
    check_php(theme, out)
    check_leftovers(theme, out)
    check_launch(wp_root, out)
    check_lead_storage(theme, wp_root, out)
    check_branding(theme, wp_root, opt.get('--url', ''), opt.get('--wp', ''), out)
    if opt.get('--profile'):
        check_tracking(theme, opt['--profile'], out)
    if opt.get('--url'):
        check_public(opt['--url'], wp_root, theme, out)
    classes = sorted({c for c, _, _ in out})
    print('OK self-check: 0 found' if not out else f'FAIL self-check: {len(out)} found ({", ".join(classes)})')
    shown = out if '-v' in argv else out[:20]
    for c, where, what in shown:
        print(f'{c}: {where}: {what}')
    if len(out) > len(shown):
        print(f'... and {len(out) - len(shown)} more (-v lists them all)')
    return 1 if out else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
