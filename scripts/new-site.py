#!/usr/bin/env python3
"""Start a conversion: prepare the starter theme, copy the skill's kit into the WordPress project and fill in the
site's values. Safe to run again (it keeps what is there and reports it).

    python3 scripts/new-site.py site.json --plan-only     Sprint 0: plan, board, handoff files, tools
    python3 scripts/new-site.py site.json                 Sprint 1: prepare the starter theme and copy the kit in
    options: [--profile profile.local.json] [--dry-run] [--force]

site.json: copy assets/site.example.json and fill it in (the intake answers). The profile holds the developer's or
agency's defaults (lead Bcc list, task tracker, extra plugins, reply style); it is optional. site.json wins where it
sets a value; the Bcc lists are combined.

Before running: WordPress is installed at wp_root and the starter theme is in wp-content/themes/<theme>/:
  starter "barebones" (plain CSS): Barebones (github.com/benchmarkstudios/barebones), unzipped, folder renamed <theme>
  starter "tw" (Tailwind): _tw generated with the theme slug and prefix (underscoretw.com, or
      wp scaffold _tw <theme> --theme_name="<Site>" --prefix=<prefix>); WordPress uses its theme/ subfolder

What it does (a file that exists is kept; --force replaces kit code only, after backing it up to
_setup/kit-backup-<time>/, and never the plan, the board, the handoff files, the seed data or the launch files):
  1. Prepares the starter. Barebones: global functions renamed to the prefix, text domain and theme header set,
     front-end jQuery dropped; the sample block, the shortcode file, its acf.php (it hides the ACF menu outside
     "development"), its functions.php and AGENTS.md moved to _setup/starter-removed/ (nothing is deleted). _tw: checked that
     it was generated (the raw repo still says _tw); its PHPCS ruleset swapped for the kit's.
  2. Theme: includes/, template-parts/, assets/, acf-json/ (empty), AGENTS.md, phpcs.xml.dist,
     composer.json, tests/parity/, and functions.php (Barebones: the kit's; _tw: the kit's lines appended).
  3. Project: _plan/ (plan templates, tools/), _setup/seed/, _setup/launch/ (RUNBOOK.md, htaccess-live.txt,
     report.html), BUILD-MAP.md, handoff.md, ai-handoff-summary.md, and the private-files block in .htaccess.
Tokens: kitwp/KITWP/Kitwp (PHP prefix), kitk (ACF key prefix), every {{NAME}} from site.json, and
<!-- starter:barebones --> / <!-- starter:tw --> blocks, on their own lines or inline (kept only for the chosen starter).
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
KIT_FILES = ['config', 'cleanup', 'head', 'acf', 'helpers', 'media', 'forms', 'schema', 'seo', 'seed', 'seed-pages',
             'snapshot']

ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
ap.add_argument('site_json')
ap.add_argument('--profile')
ap.add_argument('--dry-run', action='store_true')
ap.add_argument('--force', action='store_true')
ap.add_argument('--plan-only', action='store_true', help='Sprint 0: only the plan, the board, the handoff files and the tools (no WordPress or theme yet)')
a = ap.parse_args()

site = json.load(open(a.site_json, encoding='utf-8'))
prof_path = a.profile or os.path.join(SKILL, 'profile.local.json')
profile = json.load(open(prof_path, encoding='utf-8')) if os.path.exists(prof_path) else {}

errors = []
for k in ('site_name', 'domain', 'wp_root', 'theme', 'prefix', 'key', 'starter'):
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
if errors:
    sys.exit('\n'.join(errors))

starter, prefix, key = site['starter'], site['prefix'], site['key']
# Lead email: the profile's defaults, then the site's non-empty values; the Bcc lists are combined (the agency's
# usual copies plus the site's own, for example its account manager).
lead = {k: v for k, v in profile.get('lead', {}).items() if not k.startswith('_')}
for k, v in site.get('lead', {}).items():
    if k == 'bcc':
        lead['bcc'] = list(dict.fromkeys(list(lead.get('bcc', [])) + list(v or [])))
    elif v not in (None, '', []):
        lead[k] = v
today = datetime.date.today()
values = {
    'SITE_NAME': site['site_name'],
    'LEGAL_NAME': site.get('legal_name', site['site_name']),
    'DOMAIN': site['domain'],
    'DOMAIN_REGEX': site['domain'].replace('.', '\\.'),
    'LOCAL_HOST': site.get('local_host', site.get('site_dir', site['theme']) + '.test'),
    'SITE_DIR': site.get('site_dir', os.path.basename(os.path.normpath(site['wp_root']))),
    'THEME': site['theme'],
    'STARTER': 'Barebones' if starter == 'barebones' else '_tw',
    'SCHEMA_TYPE': site.get('schema_type', 'Organization'),
    'AREA_SERVED': site.get('area_served', ''),
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
    'FONT_LINKS': '\n'.join('<?php // phpcs:ignore WordPress.WP.EnqueuedResources.NonEnqueuedStylesheet ?>\n' + l
                            for l in site.get('font_links', [])),
    'PHONE_DISPLAY': site.get('phone_display', ''),
    'PHONE_TEL': site.get('phone_tel', ''),
    'EMAIL': site.get('email', ''),
    'GTM_ID': site.get('gtm', ''),
    'LEAD_TO': lead.get('to', ''),
    'LEAD_BCC': ', '.join(lead.get('bcc', [])),
    'LEAD_FROM': lead.get('from', f"{site['site_name']} <no-reply@{site['domain']}>"),
    'DEVELOPER': site['developer'] if site.get('developer') not in (None, '', 'the developer') else profile.get('developer', 'the developer'),
    'DATE': f'{today.day} {today:%b %Y}',
}


def fill(text):
    """Prefix and key tokens, starter blocks, then {{NAME}} values (unknown names stay, and are reported)."""
    text = text.replace('KITWP', prefix.upper()).replace('Kitwp', prefix.capitalize()).replace('kitwp', prefix)
    text = text.replace('kitk', key)
    keep = lambda m: m.group(2) if m.group(1) == starter else ''  # noqa: E731
    text = re.sub(r'[ \t]*<!-- starter:(\w+) -->\n(.*?)[ \t]*<!-- /starter:\1 -->\n', keep, text, flags=re.S)
    text = re.sub(r'<!-- starter:(\w+) -->(.*?)<!-- /starter:\1 -->', keep, text)  # inline, within one line
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


# 1. The starter theme (skipped with --plan-only: Sprint 0 has no WordPress yet).
if a.plan_only:
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
                 f"__( '% comments', '{prefix}' ) ); // phpcs:ignore WordPress.WP.I18n.MissingTranslatorsComment"),
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
            notes.append(f'Barebones prepared: {len(changed)} files renamed or updated; moved aside: '
                         + (', '.join(moved) if moved else 'nothing'))
            notes.append('By hand (S1 theme story): includes/admin.php TinyMCE text-size formats (classes the static CSS '
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
for tool in ('acf', 'seed', 'build-map', 'report', 'launch', 'setup'):
    add_tree(os.path.join(S, tool), os.path.join(root, '_plan', 'tools', tool))
for f in ('analyze-source.py', 'snapshot-routes.mjs'):
    plan.append((os.path.join(S, f), os.path.join(root, '_plan', 'tools', f)))
add_tree(os.path.join(A, 'seed'), os.path.join(root, '_setup', 'seed'))
for f in sorted(os.listdir(os.path.join(A, 'plan'))):
    plan.append((os.path.join(A, 'plan', f), os.path.join(root, '_plan', f.replace('.template', ''))))
plan += [
    (os.path.join(A, 'build-map', 'BUILD-MAP.template.md'), os.path.join(root, 'BUILD-MAP.md')),
    (os.path.join(A, 'handoff', 'handoff.template.md'), os.path.join(root, 'handoff.md')),
    (os.path.join(A, 'handoff', 'ai-handoff-summary.template.md'), os.path.join(root, 'ai-handoff-summary.md')),
    (os.path.join(A, 'launch', 'RUNBOOK.template.md'), os.path.join(root, '_setup', 'launch', 'RUNBOOK.md')),
    (os.path.join(A, 'launch', 'htaccess-live.txt'), os.path.join(root, '_setup', 'launch', 'htaccess-live.txt')),
    (os.path.join(A, 'report', 'report-template.html'), os.path.join(root, '_setup', 'launch', 'report.html')),
]

# The project's own documents and data are never overwritten, not even with --force: the plan, the board, the
# handoff files, the seed data and the launch files belong to the project once written.
PROTECTED = ('BUILD-MAP.md', 'handoff.md', 'ai-handoff-summary.md', '_setup/seed/', '_setup/launch/')
stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
written, kept, backed = [], [], []
for src, dst in plan:
    if not os.path.exists(src):
        continue
    r = rel(dst)
    if exists(dst):
        project_doc = r.startswith(PROTECTED) or (r.startswith('_plan/') and not r.startswith('_plan/tools/'))
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
        write(dst, fill(read(src)))
    elif not a.dry_run:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        os.chmod(dst, 0o644)
if backed:
    notes.append(f'--force: {len(backed)} kit files replaced; the replaced versions are in _setup/kit-backup-{stamp}/')

if not a.plan_only and not os.path.isdir(os.path.join(theme, 'acf-json')):
    written.append(rel(os.path.join(theme, 'acf-json')) + '/')
    if not a.dry_run:
        os.makedirs(os.path.join(theme, 'acf-json'))

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
for n in notes:
    print('- ' + n)
if kept:
    print('kept: ' + ', '.join(kept[:12]) + (f' and {len(kept) - 12} more' if len(kept) > 12 else ''))
if left:
    print('placeholders still to fill: ' + ', '.join(sorted(left)))
build = 'npm install && npm run build' if starter == 'barebones' else 'npm install && npm run dev'
if a.plan_only:
    print('next: Sprint 0 planning in _plan/ and BUILD-MAP.md; in Sprint 1, after WordPress and the starter theme, run this '
          'again without --plan-only.')
else:
    print(f'next: in {rel(theme_root)}: {build}; php -l and PHPCS on the theme; activate it; then the Sprint 1 stories.')
