# Setup: intake, local WordPress, theme, plugins

Read this in P0 (intake) and P1 (setup). The developer's Plan OK covers the downloads and installs the plan lists;
anything else needs its own OK. The developer types every password and licence key, except the default local admin
password install-wp.py reads from profile.local.json.

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
4. "Where will the site live, and what is its domain?" The host (cPanel or another), the live domain.

Ask the developer-level questions too when they apply (in the same batch):

- The task tracker: which tasks belong to this build and how to read them (a connector, or the developer pastes
  them). Pull out requested pages, the GTM ID, where tags must fire (`/thank-you/`), rules such as "campaign URLs
  stay the same", lead recipients, deadlines. The task's requirements win over this skill's defaults.
- The old site, if one is replaced: its URL, its full sitemap, and for WordPress its REST page and post counts
  (`/wp-json/wp/v2/pages?per_page=1`, header `X-WP-Total`). A designer's redirect map can miss archive and
  theme-part URLs (on the reference build it missed 30 of 96).
- Repo documents: redirect map, copy brief, open items, design system spec (`_plan/PLAN.md` > The source).
- Lead email: To (the client's inbox), Bcc (the profile's list), From (`<Site> <no-reply@domain>`).
- Country and language: languages, right-to-left, timezone, how dates and phone numbers are written.

As soon as the folder and the source are known: `python3 <kit>/scripts/start.py <source> --root <wp_root> --name
"<Site>" --env doctor.json` writes two short handoff files there (a closed chat loses nothing: "continue the
WordPress conversion" picks it up), makes the working copy and studies it (`references/source-types.md`), and copies
doctor.json to `_plan/` for setup.py.

## Where WordPress runs

doctor.py's `suggestion` says how, for the local app it found:

| doctor `serve` | Apps | What to do in P1 |
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

start.py (analyze-source.py `--site-draft`) writes a first one (starter, GTM, html
attributes, fonts from the source; folder, address and how WordPress is made from doctor.py); without it, copy
`assets/site.example.json`. new-site.py refuses the example values (Example Co, example.com, an empty folder). Fill
the rest from the intake. Then create the project (P0: plan, board, handoff files, tools; no WordPress needed
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
| `map_default` | What the map shows until the address is confirmed, usually the city as words (`Leeds, UK`); empty = `area_served` |
| `brand_colour`, `og_locale`, `timezone` | As the static site and the business use them (any country and language) |
| `html_attributes` | The static `<html>` lang and dir, exactly (`lang="en"`, `lang="ar" dir="rtl"`): analyze-source.py reports them |
| `agency_badge_hide` | Empty (the default): the agency badge is in the footer and both emails. Only when the task says the client asked: that note (for example "client asked, task ABC-12"); the Theme Settings toggle then works |
| `form_class`, `chat_selector` | The static lead form's class (`kitwp-form` when the design has no form: the kit's default layout), and the chat widget's root selector if any |
| `phone_display`, `phone_tel`, `email`, `gtm` | Business details and the GTM container |
| `font_links` | The static `<head>`'s font `<link>` tags, exactly |
| `lead.to`, `lead.bcc`, `lead.from` | Lead email recipients and sender |
| `cache_plugin`, `task_plugins` | The live cache plugin when not the profile's (`"none"` when the host caches); plugins the task asks for beyond the kit's list (names or `{"name", "slug", "where"}`) |

The profile (`profile.local.json` next to SKILL.md, never committed; start from `profile.example.json`) holds the
developer's or agency's defaults: `level` (`new` or `developer`), `oks` (`group` or `each`), Bcc list, task
tracker, stakeholder role and channel, admin username, local app (doctor.py fills it, with an OK), host, extra
plugins, reply style. site.json wins where both set a value.

## Folders

| Folder | What | Rule |
|---|---|---|
| `<www>/<site>` | WordPress, the plan (`_plan/`), setup files (`_setup/`), BUILD-MAP and handoff (`<www>`: the web folder doctor.py found) | The only folder the build writes |
| The source | The designer's code (a folder, a repo or a zip) | Never touched |
| `<www>/<name>-source` | The working copy start.py makes (get-source.py `--into <www>`) (clone or GitHub zip, safe unzip, copy, or a live capture; `.source.json`: where it came from, the commit or SHA-256) | Builds and `npm install` happen here only |
| `<www>/<site>-ref` | The golden master: the static build, served unchanged | Never edited |

The private files (`_plan`, `_setup`, BUILD-MAP.md, the handoff files, debug.log) are blocked by the root
`.htaccess` block that new-site.py adds, and left out of the Duplicator package.

## The database

setup.py creates it on the local app's database host (`CREATE DATABASE IF NOT EXISTS`, never a drop), covered by the
Plan OK. When it cannot reach MySQL (the app is stopped, or the root user has a password), start the app or have the
developer set `DB_PASSWORD` in their own shell; or create it by hand, using what the developer has (doctor.py's `db`
shows the app's defaults):

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

All of P1-01 runs in one go after the Plan OK (it listed these downloads); no question at each step:

```
python3 _plan/tools/setup/setup.py <wp_root>/_plan/site.json --profile <kit>/profile.local.json [--dry-run]
```

It reads site.json (`wp_root`, `local_host`, `site_name`, `timezone`, `wordpress`, `serve`) and `_plan/doctor.json`
(the local app's database host, port and user, its PHP), and runs the steps below in order, stopping at the first
that fails: the database (`CREATE DATABASE IF NOT EXISTS db_<site>`, local host only, never drops anything; a
password only from `DB_PASSWORD` in the developer's shell, else the app's documented default), get-wordpress.py,
make-wp-config.py, serve-wp.py (only for `serve: serve-wp`), install-wp.py. Line 1 says OK, WARN (open items from
install-wp.py, exit 1) or FAIL, then one line per step. Run it again after fixing: every step keeps what is there.
The steps one by one, for a step that needs repeating:

**A WordPress the local app made** (doctor `wordpress: existing`: Local, DDEV, wp-env): the developer makes the site
in the app, then:

1. `python3 _plan/tools/setup/get-wordpress.py <wp_root> --verify`: every core file against the official list.
2. `python3 _plan/tools/setup/make-wp-config.py <wp_root> --existing`: adds the kit block (environment local, debug
   log, file editing off, the `ACF_PRO_LICENSE` line), keeps the database settings and salts, saves a backup in
   `_setup/backups/`, and turns the file's own lines for the same constants into comments.

**Otherwise** (doctor `wordpress: download`):

1. The database (above).
2. `python3 _plan/tools/setup/get-wordpress.py <wp_root>`: SHA-1 of the zip and every core file against the official
   MD5 list; never overwrites; sets 0644/0755. No network in this shell: the developer downloads the zip and you
   pass `--zip`.
3. `python3 _plan/tools/setup/make-wp-config.py <wp_root> --db db_<site>` (`--no-cron` with serve-wp.py): salts
   generated and never printed; `WP_ENVIRONMENT_TYPE` local, debug log on (display off), `DISALLOW_FILE_EDIT`.
4. doctor `serve: serve-wp`: `python3 _plan/tools/setup/serve-wp.py <wp_root> --background` (the PHP doctor.py
   found; `--port` if 8081 is taken).

**Then, for both:**

```
python3 _plan/tools/setup/install-wp.py <wp_root> --url http://<site>.test --title "<Site>"         --profile <kit>/profile.local.json [--timezone <Area/City>] [--php <doctor's php>] [--dry-run]
```

- Local only: it refuses unless wp-config says `WP_ENVIRONMENT_TYPE` local and the URL is a local address
  (localhost, 127.0.0.1, `*.test`, `*.localhost`, `*.local`).
- Not installed yet: installs WordPress with the **default local admin** from the profile's `local_admin`
  (username, e.g. `agency-dev`, and email). The password is the developer's default local password, which they put
  once in `profile.local.json` > `local_admin.password` (git ignores that file), or in `KITWP_ADMIN_PASSWORD` in
  their own shell. The script passes it to PHP through the environment and never prints it; the agent never types
  or repeats it. Already installed (a local app made it): users and passwords stay as they are.
- Settings: permalinks `/%postname%/`, "Discourage search engines" on, the timezone, the WordPress block in
  `.htaccess`. Fresh install only: the sample post, page and comment, Hello Dolly and Akismet removed.
- Plugins: Contact Form 7 and Yoast SEO from wordpress.org (every file checked against the official checksums), ACF
  PRO from the profile's `plugin_zips.acf_pro` (`--fields scf`: Secure Custom Fields instead, only when the
  developer asks), all activated; debug.log read. A plugin folder that exists is kept.
- Exit 0 all done; 1 open items listed (no ACF PRO zip yet: the developer downloads it from their ACF account and
  sets the path, then run it again); 2 refused.
- Then: language and date formats as the business (Settings > General); the ACF PRO licence is active when the
  profile has `acf_pro_license` (below), otherwise the developer pastes it.
  Default themes are removed later, with the developer's OK. PHP 8.3 or 8.4 locally (on the reference build an old
  PHP 8.1 build could not reach wordpress.org over HTTPS).
- **Live** never uses install-wp.py or the default password: the live admin gets its own strong password, typed by
  the developer.

## The starter theme: Barebones or _tw

The rule (the plan names the choice and one reason; the developer can override it, decision D2 on the board):

- **The source is Tailwind: _tw.**
- **Not Tailwind, but clearly easier in Tailwind** (a design system with repeating tokens, many reusable sections):
  **_tw.** The static CSS still loads byte for byte for 1:1 (`KITWP_STYLESHEETS`); Tailwind, with `@theme` tokens
  taken from the source's colours, fonts and spacing, styles only what the build writes itself.
- **A normal site that doesn't really need Tailwind** (small, mostly one-off layouts, plain CSS expected):
  **Barebones with CSS-variable tokens**: the source's colours, fonts and spacing as custom properties in one file
  (`assets/css/tokens.css`), used by every style the build writes itself.

start.py (analyze-source.py) reports whether the source is Tailwind; the middle case is the plan's call. Both are
classic PHP themes under GPL-2.0-or-later.

- **Barebones** (Benchmark Studios; Vite and Sass): ask, then `git clone --depth 1
  https://github.com/benchmarkstudios/barebones wp-content/themes/<theme>` (or Code > Download ZIP, unzip, rename).
- **_tw** (underscoretw.com; Tailwind 4 and esbuild): generate it with the slug and prefix, never copy the raw repo
  (its names stay `_tw`). With WP-CLI (needs PHP in the shell): `wp package install underscoretw/scaffold`, then
  `wp scaffold _tw <theme> --theme_name="<Site>" --prefix=<prefix>`. Or on underscoretw.com: Generate, unzip into
  `wp-content/themes/`. When `wp package install` fails (some proxies break Composer's GitHub access), the same zip
  comes straight from the generator (POST to the home page with `underscoretw_cli=1`, as the WP-CLI package does;
  `curl.exe` in Windows PowerShell):
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

ACF PRO, Contact Form 7 and Yoast SEO, installed by install-wp.py in P1 (the Plan OK covers them).

- Contact Form 7 (`contact-form-7`) and Yoast SEO (`wordpress-seo`): from wordpress.org. Yoast is seeded in P4; its
  schema is replaced by the static JSON-LD.
- Secure Custom Fields (free, `secure-custom-fields`; only when the developer asks, `install-wp.py --fields scf`): runs
  it unchanged, with repeater, flexible content, gallery, clone, the options page, local JSON in `acf-json/`, the
  seeder and `get_field()` (tested: SCF 6.9 on WordPress 7.1). Its menu is SCF: read "ACF >" as "SCF >". No
  licence, so the `ACF_PRO_LICENSE` line stays commented. Never ACF PRO and SCF active together.
- ACF PRO: the developer's zip from their ACF account (the profile's `plugin_zips.acf_pro` path, if set). The
  licence, either way typed by the developer, never by the agent:
  - **Pre-activated:** the developer puts the key once in `profile.local.json` as `acf_pro_license` (git-ignored, in
    the skill folder, which is never served). setup.py and make-wp-config.py (`--profile <kit>/profile.local.json`)
    then write `define( 'ACF_PRO_LICENSE', '...' );` active in every LOCAL wp-config (`--env local` only), so ACF PRO
    activates itself on that URL. The value is never printed, logged, or written to notes, reports, handoff files,
    git or the client pack. A rerun writes the profile's current key; a key the developer pasted by hand is kept.
  - **By hand:** the developer pastes the key into the commented `ACF_PRO_LICENSE` line (or enters it in ACF >
    Updates).
  - **Clones** (one site copied to new URLs, several sites from one template): run
    `make-wp-config.py <copy> --existing --profile <kit>/profile.local.json` on each copy, so each activates on its
    own URL.
  - **Live:** the key is not written there by default. Duplicator copies the local wp-config, so at launch the
    `ACF_PRO_LICENSE` line is removed from the live wp-config unless the developer chooses to keep it (then ACF
    activates the live URL too; one licence site each).
  Never edit the plugin to hold a key, and never put a key in the skill's tracked files, a report or a chat.
- The ACF menu always shows to administrators, on live too: the licence page and the field groups live there.
  includes/acf.php never hides it.
- Later, each in the phase that needs it:

| Plugin | Slug | When |
|---|---|---|
| Redirection | `redirection` | Optional: only when the site has old URLs to redirect (P4) |
| Duplicator | `duplicator` (free), or Pro from the developer's zip | The move to live (launch) |
| Converter for Media | `webp-converter-for-media` | Must be on live: WebP for images uploaded later (installed at launch, live only; check images after) |
| Contact Form CFDB7 | `contact-form-cfdb7` | Must be on live: every enquiry kept in the database (installed at launch, live only) |
| The profile's `extra_plugins` | per entry | The developer's or agency's own plugins: `required` ones with `"where": "all"` (or no `where`) in P1 with the starters and active on live; `"where": "live"` ones at launch only, never local or staging; the others when the entry says |

- After every plugin install: read `wp-content/debug.log`. A second copy of a plugin gives "Cannot redeclare"
  fatals.

## PHP checks (PHPCS, php -l, duplicates)

- `composer install --no-interaction --no-progress` once in the theme folder, then `vendor/bin/phpcs -q
  --report=summary` (WordPress security, i18n, prefixes, PHPCompatibilityWP for PHP 8.1 to 8.4); when it finds
  something, the full report (`vendor/bin/phpcs -q`) into `_plan/logs/phpcs.log` (rule 18).
- `php -l <file>` after every save.
- The duplicate function check after every PHP save; it must print nothing:
  `grep -h "^function" includes/*.php | sed 's/(.*//' | sort | uniq -d` (any shell: `text-check.py dupes .` in the
  theme folder). A duplicate name took the reference build
  down twice, and php -l cannot catch it.
- No PHP where the agent runs? Lint in a workspace that has it (copy the changed files there, run the checks, never
  edit there).

## The golden master

The design reference is the static build, served unchanged:

- as its own local site (`<site>-ref`, for example http://<site>-ref.test), or
- with `python3 tests/parity/serve.py <folder> 8080` (a real 404 for missing URLs).

Until launch the live static site can stand in, but it is replaced at launch: set up the local copy first. How to
produce the build for each kind of source: `references/source-types.md`.
