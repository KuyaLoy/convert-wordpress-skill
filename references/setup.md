# Setup: intake, local WordPress, theme, plugins

Read this in Sprint 0 (intake) and Sprint 1 (foundation). Every download, install, database change and folder
access needs the developer's OK first. The developer types every password and licence key.

## Contents

- Intake: what to ask
- site.json and the profile
- Folders
- The database
- WordPress
- The starter theme: Barebones or _tw
- Starter plugins
- PHP checks (PHPCS, php -l, duplicates)
- The golden master

## Intake: what to ask

If the project exists, read `ai-handoff-summary.md` and continue from its Next action. Otherwise read what is
there first (the source, the task, the profile), then ask once, in one batch, only what you could not find:

1. Site name and live domain.
2. The source: folder, repo or zip; its built output if any; whether the static site is live now, and where.
3. The task tracker: which tasks belong to this build (website, tracking, SEO) and how to read them (a connector,
   or the developer pastes them). Pull out: requested pages, the GTM ID, where tags must fire (`/thank-you/`),
   rules such as "campaign URLs stay the same", lead recipients, deadlines. The task's requirements are in scope;
   follow them even where this skill's defaults differ.
4. Local stack and folder (the profile's default, for example Laragon: `D:/laragon/www/<site>`,
   `http://<site>.test`), and how to create the database.
5. The old site, if one is being replaced: its URL, its full sitemap, and for WordPress its REST page and post
   counts (`/wp-json/wp/v2/pages?per_page=1` header `X-WP-Total`). A designer's redirect map can miss archive and
   theme-part URLs (on the reference build it missed 30 of 96).
6. Repo documents: redirect map, copy brief, open items, design system spec. Note which are still valid
   (`_plan/SOURCE-NOTES.md`).
7. Lead email: To (the client's inbox), Bcc (the profile's list), From (`<Site> <no-reply@domain>`).
8. Country and language: the site's language or languages, right-to-left or not, timezone, how dates and phone
   numbers are written. The skill works for any country; nothing defaults to one.
9. The host and the move: cPanel and Duplicator Pro by default (`references/launch.md`).

## site.json and the profile

`analyze-source.py --site-draft <wp_root>/_plan/site.json` writes a first one (starter, GTM, html attributes, fonts
from the source); without it, copy `assets/site.example.json`. Fill the rest from the intake. Then create the project
(Sprint 0: plan, board, handoff files, tools; no WordPress needed yet):

```
python3 <kit>/scripts/new-site.py <wp_root>/_plan/site.json --plan-only
```

The fields:

| Field | Meaning |
|---|---|
| `site_name`, `legal_name`, `domain` | As the business uses them |
| `wp_root`, `site_dir`, `local_host` | The WordPress folder, its name, the local URL host |
| `theme` | The theme folder (lowercase, dashes allowed) |
| `prefix` | PHP prefix for every function, hook, global and constant (2 to 20 lowercase letters or digits) |
| `key` | ACF key prefix: `group_<key>_*`, `field_<key>_*` (2 to 6 characters) |
| `starter` | `barebones` (plain CSS) or `tw` (Tailwind), from analyze-source.py |
| `schema_type`, `area_served`, `country_code`, `price_range` | The static JSON-LD's values |
| `brand_colour`, `og_locale`, `timezone` | As the static site and the business use them (any country and language) |
| `html_attributes` | The static `<html>` lang and dir, exactly (`lang="en"`, `lang="ar" dir="rtl"`): analyze-source.py reports them |
| `form_class`, `chat_selector` | The static lead form's class, and the chat widget's root selector if any |
| `phone_display`, `phone_tel`, `email`, `gtm` | Business details and the GTM container |
| `font_links` | The static `<head>`'s font `<link>` tags, exactly |
| `lead.to`, `lead.bcc`, `lead.from` | Lead email recipients and sender |

The profile (`profile.local.json` next to SKILL.md, never committed; start from `profile.example.json`) holds the
developer's or agency's defaults: Bcc list, task tracker, stakeholder role and channel, admin username, local stack,
host, extra plugins, reply style. site.json wins where both set a value.

## Folders

| Folder | What | Rule |
|---|---|---|
| `<www>/<site>` | WordPress, the plan (`_plan/`), setup files (`_setup/`), BUILD-MAP and handoff | The only folder the build writes |
| The source | The designer's code | Read only. Build or `npm install` only in a copy |
| `<www>/<site>-ref` | The golden master: the static build, served unchanged | Never edited |

The private files (`_plan`, `_setup`, BUILD-MAP.md, the handoff files, debug.log) are blocked by the root
`.htaccess` block that new-site.py adds, and left out of the Duplicator package.

## The database

Ask first, then use what the developer has:

- **phpMyAdmin** in the developer's browser (Laragon: http://localhost/phpmyadmin/ or the Database button). With a
  browser tool, open it, let the developer log in if it asks for a password, then run in the SQL tab:
  `CREATE DATABASE db_<site> CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci;`
- **HeidiSQL** or another client: give the developer the same SQL line to run.
- **A shell that reaches MySQL** (for example Laragon's terminal): `mysql -u root -e "CREATE DATABASE ..."`.

Laragon's MySQL `root` user has no password by default. Never type a database password; if one is needed, the
developer sets `DB_PASSWORD` in their own shell for make-wp-config.py.

## WordPress

1. Ask: "May I download WordPress (latest.zip from wordpress.org, about 30 MB) into `<wp_root>`?"
2. `python3 _plan/tools/setup/get-wordpress.py <wp_root>`: SHA-1 of the zip and every core file against the official
   MD5 list; never overwrites; sets 0644/0755. No network in this shell: the developer downloads the zip and you
   pass `--zip`.
3. `python3 _plan/tools/setup/make-wp-config.py <wp_root> --db db_<site>`: salts generated and never printed;
   `WP_ENVIRONMENT_TYPE` local, debug log on (display off), `DISALLOW_FILE_EDIT`.
4. The installer, http://<local_host>/wp-admin/install.php: fill the site title, the admin username (profile) and
   email if asked; the developer types the password.
5. Settings: Permalinks `/%postname%/`; timezone and language as the business; Reading "Discourage search engines"
   on (local only). Delete the sample post, page and comment, Akismet and Hello Dolly, and later the default themes:
   with the developer's OK (permanent deletes are their click).
6. PHP 8.3 or 8.4 locally. On the reference build an old PHP 8.1 build could not reach wordpress.org over HTTPS.

## The starter theme: Barebones or _tw

The rule: **Tailwind in the source: _tw. Otherwise: Barebones.** analyze-source.py reports which; the developer
confirms (decision D2 on the board). Both are classic PHP themes under GPL-2.0-or-later.

- **Barebones** (Benchmark Studios; Vite and Sass): ask, then `git clone --depth 1
  https://github.com/benchmarkstudios/barebones wp-content/themes/<theme>` (or Code > Download ZIP, unzip, rename).
- **_tw** (underscoretw.com; Tailwind 4 and esbuild): generate it with the slug and prefix, never copy the raw repo
  (its names stay `_tw`). With WP-CLI (needs PHP in the shell): `wp package install underscoretw/scaffold`, then
  `wp scaffold _tw <theme> --theme_name="<Site>" --prefix=<prefix>`. Or on underscoretw.com: Generate, unzip into
  `wp-content/themes/`. WordPress loads `<theme>/theme`; the folder around it holds the Tailwind and build files.

Then:

```
python3 <kit>/scripts/new-site.py <wp_root>/_plan/site.json      (add --dry-run first to see what it will write)
```

The same command as at intake, now without `--plan-only`. It prepares the starter (Barebones: prefix renames, text
domain, header, no front-end jQuery, exact PHPCS fixes; its sample block, shortcode file, the acf.php that hides
the ACF menu, its functions.php and AGENTS.md moved to `_setup/starter-removed/`; _tw: checks it was generated, its
PHPCS ruleset swapped for the kit's) and copies the kit into the theme. Files that exist are kept; `--force`
replaces kit code only, after a backup in `_setup/kit-backup-<time>/`, and never the plan, the board, the handoff
files, the seed data or the launch files. It lists any `{{PLACEHOLDER}}` still to fill.

Then build the assets in the theme folder (Barebones `npm install && npm run build`; _tw `npm install && npm run
dev`), and activate the theme (Appearance > Themes, or `wp theme activate <theme>`; for _tw `<theme>/theme`).

## Starter plugins

ACF PRO, Contact Form 7 and Yoast SEO at the start. Ask before installing each.

- Contact Form 7: Plugins > Add New, or `wp plugin install contact-form-7 --activate`.
- Yoast SEO: `wp plugin install wordpress-seo --activate`. Seeded in Sprint 6; its schema is replaced by the
  static JSON-LD.
- ACF PRO: the developer's zip from their ACF account (the profile's `plugin_zips.acf_pro` path, if set). The
  licence: the developer pastes the key into the commented `ACF_PRO_LICENSE` line that make-wp-config.py writes in
  wp-config.php (or enters it in ACF > Updates). Never edit the plugin to hold a key, and never put a key in the
  skill, the profile or a chat.
- The ACF menu always shows to administrators, on live too: the licence page and the field groups live there.
  includes/acf.php never hides it.
- Later, each in the sprint that needs it and after asking:

| Plugin | Slug | When |
|---|---|---|
| Redirection | `redirection` | Optional: only when the site has old URLs to redirect (Sprint 6) |
| Duplicator Pro | the developer's zip | The move to live (launch) |
| Converter for Media | `webp-converter-for-media` | Must be on live: WebP for images uploaded later (launch; check images after) |
| Contact Form CFDB7 | `contact-form-cfdb7` | Must be on live: every enquiry kept in the database (Sprint 5 or launch) |
| The profile's `extra_plugins` | per entry | Optional: the developer's or agency's own plugins, when the entry says |

- After every plugin install: read `wp-content/debug.log`. A second copy of a plugin gives "Cannot redeclare"
  fatals.

## PHP checks (PHPCS, php -l, duplicates)

- `composer install` once in the theme folder, then `vendor/bin/phpcs` (WordPress security, i18n, prefixes,
  PHPCompatibilityWP for PHP 8.1 to 8.4).
- `php -l <file>` after every save.
- The duplicate function check after every PHP save; it must print nothing:
  `grep -h "^function" includes/*.php | sed 's/(.*//' | sort | uniq -d`. A duplicate name took the reference build
  down twice, and php -l cannot catch it.
- No PHP where the agent runs? Lint in a workspace that has it (copy the changed files there, run the checks, never
  edit there).

## The golden master

The design reference is the static build, served unchanged:

- as its own local site (`<site>-ref`, for example http://<site>-ref.test), or
- with `python3 tests/parity/serve.py <folder> 8080` (a real 404 for missing URLs).

Until launch the live static site can stand in, but it is replaced at launch: set up the local copy first. How to
produce the build for each kind of source: `references/source-types.md`.
