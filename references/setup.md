# Setup: intake, local WordPress, theme, plugins

Read this in Sprint 0 (intake) and Sprint 1 (foundation). Every download, install, database change and folder
access needs the developer's OK first. The developer types every password and licence key.

## Contents

- Intake: what to ask
- Where WordPress runs
- site.json and the profile
- Folders
- The database
- WordPress
- The starter theme: Barebones or _tw
- Starter plugins
- PHP checks (PHPCS, php -l, duplicates)
- The golden master

## Intake: what to ask

If the project exists, read `ai-handoff-summary.md` and continue from its Next action. Otherwise run doctor.py
first (`python3 <kit>/scripts/doctor.py --name <site> --json doctor.json`): it finds the tools, the local WordPress
app and the folder and address to suggest, so you do not ask what it already knows. Then read what is there (the
source, the task, the profile) and ask once, in one batch, the suggestion first. For a developer new to this
(profile `level: new`, or they say so), use these words:

1. "Where should I build the new site?" Suggest doctor's folder and address; other choices: the other apps it
   found, "a folder you pick", "help me install a free app" (Local on any computer, or Laragon on Windows).
2. "What do you have of the site?" A GitHub link, a zip, a folder, or only its web address (then the live site is
   captured; only a site they own or may rebuild). Usually given with `/convert-to-wordpress <source>`.
3. "Have you built websites before?" Sets `level` (`new` or `developer`) for every reply after this one.
4. "Which fields plugin: ACF PRO (paid, advancedcustomfields.com) or the free Secure Custom Fields?" Both run the
   kit unchanged. The move to live uses Duplicator: the free version is enough for a normal site. Say it plainly
   before Sprint 1.
5. "Where will the site live, and what is its domain?" The host (cPanel or another), the live domain.

Ask the developer-level questions too when they apply (in the same batch):

- The task tracker: which tasks belong to this build and how to read them (a connector, or the developer pastes
  them). Pull out requested pages, the GTM ID, where tags must fire (`/thank-you/`), rules such as "campaign URLs
  stay the same", lead recipients, deadlines. The task's requirements win over this skill's defaults.
- The old site, if one is replaced: its URL, its full sitemap, and for WordPress its REST page and post counts
  (`/wp-json/wp/v2/pages?per_page=1`, header `X-WP-Total`). A designer's redirect map can miss archive and
  theme-part URLs (on the reference build it missed 30 of 96).
- Repo documents: redirect map, copy brief, open items, design system spec (`_plan/SOURCE-NOTES.md`).
- Lead email: To (the client's inbox), Bcc (the profile's list), From (`<Site> <no-reply@domain>`).
- Country and language: languages, right-to-left, timezone, how dates and phone numbers are written.

As soon as the folder is chosen: `python3 <kit>/scripts/new-site.py --start <wp_root> --name "<Site>"` writes two
short handoff files there, so a closed chat loses nothing ("continue the WordPress conversion" picks it up).

## Where WordPress runs

doctor.py's `suggestion` says how, for the local app it found:

| doctor `serve` | Apps | What to do in Sprint 1 |
|---|---|---|
| `vhost` | Laragon, Laravel Herd | The app gives every folder in its web folder its own address (`<site>.test`): download WordPress into `<www>/<site>` |
| `local-app` | Local | The developer makes the site in Local (+, Create a new site); the skill keeps that WordPress (`get-wordpress.py --verify`, `make-wp-config.py --existing`) |
| `serve-wp` | XAMPP, MAMP, WampServer, a native PHP and MySQL | No address per site: `python3 _plan/tools/setup/serve-wp.py <wp_root> --background` runs it at `http://localhost:8081` (root paths, so 1:1 works; no admin rights or hosts edits; four PHP workers on macOS and Linux, one request at a time on Windows); wp-config with `--no-cron` |
| `ddev`, `wp-env` | DDEV, wp-env (Docker) | Their own WordPress: as `local-app` |

Never put the site in a subfolder address (`http://localhost/my-site/`): every link changes and the diffs fail.
On Nginx (Local, Herd) the `.htaccess` private-files block does nothing: locally that is fine; the launch package
leaves the private files out anyway. Keep projects out of synced folders (OneDrive, Dropbox, iCloud) and away from
long or spaced paths when doctor.py warns.

## site.json and the profile

`analyze-source.py --env doctor.json --site-draft <wp_root>/_plan/site.json` writes a first one (starter, GTM, html
attributes, fonts from the source; folder, address and how WordPress is made from doctor.py); without it, copy
`assets/site.example.json`. new-site.py refuses the example values (Example Co, example.com, an empty folder). Fill
the rest from the intake. Then create the project (Sprint 0: plan, board, handoff files, tools; no WordPress needed
yet):

```
python3 <kit>/scripts/new-site.py <wp_root>/_plan/site.json --plan-only
```

The fields:

| Field | Meaning |
|---|---|
| `site_name`, `legal_name`, `domain` | As the business uses them |
| `wp_root`, `site_dir`, `local_host` | The WordPress folder, its name, the local address (`shop.test`, `shop.local`, `localhost:8081`) |
| `wordpress`, `serve` | From doctor.py: `download` or `existing`; `vhost`, `local-app`, `serve-wp`, `ddev` |
| `ref_url` | Where the golden master is served for the diffs, if not `<site>-ref.test` (for example `http://localhost:8080`) |
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
developer's or agency's defaults: `level` (`new` or `developer`), `oks` (`group` or `each`), Bcc list, task
tracker, stakeholder role and channel, admin username, local app (doctor.py fills it, with an OK), host, extra
plugins, reply style. site.json wins where both set a value.

## Folders

| Folder | What | Rule |
|---|---|---|
| `<www>/<site>` | WordPress, the plan (`_plan/`), setup files (`_setup/`), BUILD-MAP and handoff (`<www>`: the web folder doctor.py found) | The only folder the build writes |
| The source | The designer's code (a folder, a repo or a zip) | Never touched |
| `<www>/<name>-source` | The working copy `get-source.py --into <www>` makes (clone or GitHub zip, safe unzip, copy, or a live capture; `.source.json`: where it came from, the commit or SHA-256) | Builds and `npm install` happen here only |
| `<www>/<site>-ref` | The golden master: the static build, served unchanged | Never edited |

The private files (`_plan`, `_setup`, BUILD-MAP.md, the handoff files, debug.log) are blocked by the root
`.htaccess` block that new-site.py adds, and left out of the Duplicator package.

## The database

Ask first, then use what the developer has (doctor.py's `db` shows the app's defaults):

- **phpMyAdmin** in the developer's browser (most apps have it: http://localhost/phpmyadmin/, or the app's
  Database button). With a browser tool, open it, let the developer log in if it asks for a password, then run in
  the SQL tab: `CREATE DATABASE db_<site> CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci;`
- **HeidiSQL**, TablePlus or another client: give the developer the same SQL line to run.
- **A shell that reaches MySQL** (the app's terminal): `mysql -u root -e "CREATE DATABASE ..."` (MAMP on a Mac:
  `-P 8889 -u root -p`).
- **Local, DDEV, wp-env:** the app made the database with the site: nothing to create.

Laragon, XAMPP and WampServer: `root` without a password by default; MAMP and Local: `root` / `root`. Never type a
database password the developer chose; if one is needed, they set `DB_PASSWORD` in their own shell for
make-wp-config.py.

## WordPress

**A WordPress the local app made** (doctor `wordpress: existing`: Local, DDEV, wp-env): the developer makes the site
in the app (its own admin user and password), then:

1. `python3 _plan/tools/setup/get-wordpress.py <wp_root> --verify`: every core file against the official list.
2. `python3 _plan/tools/setup/make-wp-config.py <wp_root> --existing`: adds the kit block (environment local, debug
   log, file editing off, the `ACF_PRO_LICENSE` line), keeps the database settings and salts, saves a backup in
   `_setup/backups/`, and turns the file's own lines for the same constants into comments.

**Otherwise** (doctor `wordpress: download`):

1. Ask: "May I download WordPress (latest.zip from wordpress.org, about 30 MB) into `<wp_root>`?" With profile
   `oks: group`, list it with the theme and the plugins in one OK.
2. `python3 _plan/tools/setup/get-wordpress.py <wp_root>`: SHA-1 of the zip and every core file against the official
   MD5 list; never overwrites; sets 0644/0755. No network in this shell: the developer downloads the zip and you
   pass `--zip`.
3. `python3 _plan/tools/setup/make-wp-config.py <wp_root> --db db_<site>` (`--no-cron` with serve-wp.py): salts
   generated and never printed; `WP_ENVIRONMENT_TYPE` local, debug log on (display off), `DISALLOW_FILE_EDIT`.
4. doctor `serve: serve-wp`: `python3 _plan/tools/setup/serve-wp.py <wp_root> --background` (the PHP doctor.py
   found; `--port` if 8081 is taken).
5. The installer, http://<local_host>/wp-admin/install.php: fill the site title, the admin username (profile) and
   email if asked; the developer types the password.

Then, for both: Permalinks `/%postname%/`; timezone and language as the business; Reading "Discourage search
engines" on (local only). Delete the sample post, page and comment, Akismet and Hello Dolly, and later the default
themes: with the developer's OK (permanent deletes are their click). PHP 8.3 or 8.4 locally (on the reference build
an old PHP 8.1 build could not reach wordpress.org over HTTPS).

## The starter theme: Barebones or _tw

The rule: **Tailwind in the source: _tw. Otherwise: Barebones.** analyze-source.py reports which; the developer
confirms (decision D2 on the board). Both are classic PHP themes under GPL-2.0-or-later.

- **Barebones** (Benchmark Studios; Vite and Sass): ask, then `git clone --depth 1
  https://github.com/benchmarkstudios/barebones wp-content/themes/<theme>` (or Code > Download ZIP, unzip, rename).
- **_tw** (underscoretw.com; Tailwind 4 and esbuild): generate it with the slug and prefix, never copy the raw repo
  (its names stay `_tw`). With WP-CLI (needs PHP in the shell): `wp package install underscoretw/scaffold`, then
  `wp scaffold _tw <theme> --theme_name="<Site>" --prefix=<prefix>`. Or on underscoretw.com: Generate, unzip into
  `wp-content/themes/`. When `wp package install` fails (some proxies break Composer's GitHub access), the same zip
  comes straight from the generator (POST to the home page with `underscoretw_cli=1`, as the WP-CLI package does):
  `curl -X POST https://underscoretw.com/ -d underscoretw_generate=1 -d underscoretw_cli=1 --data-urlencode
  "underscoretw_name=<Site>" -d underscoretw_slug=<theme> -d underscoretw_prefix=<prefix> -o <theme>.zip`.
  WordPress loads `<theme>/theme`; the folder around it holds the Tailwind and build files.

Then:

```
python3 <kit>/scripts/new-site.py <wp_root>/_plan/site.json      (add --dry-run first to see what it will write)
```

The same command as at intake, now without `--plan-only`. It prepares the starter (Barebones: prefix renames, text
domain, header, no front-end jQuery, exact PHPCS fixes; its sample block, shortcode file, the acf.php that hides
the ACF menu, its functions.php and AGENTS.md moved to `_setup/starter-removed/`; _tw: checks it was generated, its
PHPCS ruleset swapped for the kit's) and copies the kit into the theme. Files that exist are kept; `--force`
replaces kit code only, after a backup in `_setup/kit-backup-<time>/`, and never the plan, the board, the handoff
files, the seed data, the launch files, the content model (`build_field_groups.py`) or the parity routes and
settings. It lists any `{{PLACEHOLDER}}` still to fill.

Then build the assets in the theme folder (Barebones `npm install && npm run build`; _tw `npm install && npm run
dev`), and activate the theme (Appearance > Themes, or `wp theme activate <theme>`; for _tw `<theme>/theme`).

## Starter plugins

ACF PRO or Secure Custom Fields, Contact Form 7 and Yoast SEO at the start. Ask before installing each.

- Contact Form 7: Plugins > Add New, or `wp plugin install contact-form-7 --activate`.
- Yoast SEO: `wp plugin install wordpress-seo --activate`. Seeded in Sprint 6; its schema is replaced by the
  static JSON-LD.
- Secure Custom Fields (free, `secure-custom-fields`, the fork of ACF that WordPress.org maintains): the kit runs on
  it unchanged, with repeater, flexible content, gallery, clone, the options page, local JSON in `acf-json/`, the
  seeder and `get_field()` (tested: SCF 6.9 on WordPress 7.1). Its menu is SCF: read "ACF >" as "SCF >". No
  licence, so the `ACF_PRO_LICENSE` line stays commented. Never ACF PRO and SCF active together.
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
| Duplicator | `duplicator` (free), or Pro from the developer's zip | The move to live (launch) |
| Converter for Media | `webp-converter-for-media` | Must be on live: WebP for images uploaded later (launch; check images after) |
| Contact Form CFDB7 | `contact-form-cfdb7` | Must be on live: every enquiry kept in the database (Sprint 5 or launch) |
| The profile's `extra_plugins` | per entry | The developer's or agency's own plugins: `required` ones in S1-02 with the starters and active on live; the others when the entry says |

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
