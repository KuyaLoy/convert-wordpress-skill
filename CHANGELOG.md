# Changelog

Every change to the skill, newest first. Versions follow [Semantic Versioning](https://semver.org); the format
follows [Keep a Changelog](https://keepachangelog.com).

## [Unreleased]

### Changed

- The update command explains how to update a skill saved in a chat app that shows no update card (zip,
  Upload skill, "Upload and replace", version history kept).

## [0.6.0] - 2026-11-11

Faster launches and a client pack for clients who are not technical. The yardstick: clean quality, fast without
losing quality, seen from the client's side.

### Added

- `scripts/launch/package.py`: builds the launch package with Duplicator Pro through WP-CLI, no wp-admin login.
  It sets a "launch" template (file filters, installer password, hashed installer name), writes the password to
  a file outside the project, checks the archive for private files, the database dump and the wp-config copy,
  and copies the archive and installer to `_setup/launch/upload/`. Has `--dry-run`. Tests: `test_package.py`.
- Client wp-admin (`includes/client-admin.php`): the client's Editor login sees only Dashboard, Pages, Media,
  Theme Settings, Contact, the enquiries and Profile; no update nags or plugin notices; one "Your website"
  dashboard box with plain links and a "Need help?" line (`KITWP_CLIENT_HELP` from `client_help`); the fields
  menu hidden from non-admins. Menus only, nothing removed; enquiries access added at run time for Editors.
  launch.md: the client's own login (`wp user create ... --role=editor --send-email`).
- Client pack: `assets/handover/` (copied to `_setup/handover/`): `website-sheet.html` ("Your new website", one
  A4 page), `editing-guide.html` ("How to edit your website", screenshots taken as the client's Editor) and
  `client-message.md` (tracker and chat versions, logins "sent separately"). `references/handover.md`.
- Thank-you and 404 pages always exist: when the source has none, they are designed from the site's own parts
  (build.md > Thank-you and 404).
- Gotcha: Duplicator Pro's `*_installer.php.bak` and its `installerPassowrd` property.

### Changed

- `live-qa.py` is the one live QA command: routes and a 404 checked twice, every redirect one 301 with the query
  kept, host rules to the canonical host (www or not), private and leftover files 403 or 404, the certificate on
  apex and www (more than 14 days), robots index and canonical, the robots.txt Sitemap line, no `.test` or
  localhost URLs, WebP with `--image`. PASS or FAIL lines, ALL PASS or N FAIL, `--json`, `--hidden` before
  launch. Tests: `test_live_qa.py`.
- qa-report.md: the report appends the pack's `How-to-Edit-Your-Website.pdf`; Done means includes the pack.
- SKILL.md: the yardstick (quality, speed, the client's view) at the top.

## [0.5.0] - 2026-11-11

Lessons from the first live launch with the 0.4 kit (a Next.js site to WordPress on cPanel, DNS first).

### Added

- Leads portal: profile `leads_portal.constant_prefix` fills `KITWP_LEADS_PREFIX`; `kitwp_leads_send()` posts
  every sent lead form to `<PREFIX>_ENDPOINT` with `<PREFIX>_KEY` from wp-config (fields, tracking, idempotency
  key), never from local, development or staging, sensitive fields left out with `kitwp_leads_skip_fields`.
- Site footer agency badge: profile `branding.site_badge` (copied to `assets/brand/`), `kitwp_agency_badge()`,
  Theme Settings > Branding (image, link, hide).
- `/favicon.ico` redirects to the brand icon when no Site Icon is set (no WordPress "W").
- robots.txt blocks everything while "Discourage search engines" is on; the thank-you page stays out of
  Yoast's sitemap.
- DNS-first launches: `_setup/launch/maintenance/` (503 page and its .htaccess, with Retry-After).
- Launch guide: the Duplicator Pro command-line build (no wp-admin login), what the installer does to
  `.htaccess`, `php.ini` and `.user.ini` and why the clean-up is immediate, the Advanced-mode URL fields, cache
  purge after indexing, AutoSSL after DNS and stale `_acme-challenge` records.
- Gotchas: browser DNS cache after the switch, local test leads reaching a live portal, preview parity
  (noindex), cPanel UAPI from a logged-in tab, big uploads through a localhost helper.
- Branded auto-reply: forms.json `autoreply_file` (new `assets/seed/autoreply-email.html`, the lead email's
  template) seeds CF7 Mail (2) as HTML, with `[_<key>_name]` for the greeting. Plain-text auto-replies are gone.
- Agency badge in the footer of the lead email and the auto-reply: profile `branding` (`email_badge_png`, `link`,
  `alt`, `width`) fills `<PREFIX>_EMAIL_BADGE*` in config.php, the builder copies the PNG into
  `theme/assets/email/`, and `[_<key>_badge]` prints it. Both templates end with a brand-colour footer strip.
- Profile `extra_plugins` entries can be marked `required`: installed in S1-02 with the starter plugins and kept
  active on live (SKILL.md S1-02, setup.md, launch.md, the runbook template, `profile.example.json`).
- Gotchas: Contact Form 7 6.2 needs PHP 8.3 (check the host's PHP before the upload; dry-run on the host's version
  locally with `php -S` and the kit's router); plugins that register themselves on activation go on after DNS moves.
- `scripts/acf/sync.php` (`wp eval-file`): syncs the theme's ACF JSON (field groups, options pages, post types,
  taxonomies) into the database with ACF's own sync code, every pending item at once; `dry-run` lists them. A
  second run says "Nothing to sync". S1-06 is done only when ACF shows nothing under "Sync available".
- The builder writes Theme Settings as an ACF options page (`ui_options_page_<key>_theme_settings.json`), so it
  shows in ACF > Options Pages; capability `edit_pages`, so a client with the Editor role can use it.
- `KITWP_ADMIN_BAR_CSS` (config.php): CSS printed only while the logged-in toolbar shows, to move a sticky static
  header (and anything placed below it) down by `--wp-admin--admin-bar--height`.

### Changed

- A failed lead email is logged with the form title only (no field values: personal or health details
  never go into a log).
- The WordPress toolbar shows for logged-in users again (Dashboard, Edit Page). Visitors never get it, so the
  public page stays 1:1.
- `acf.php` registers Theme Settings in PHP only as a fallback, when ACF has not registered it from the JSON.
- Field rules for a non-technical client (build.md, ACF): the source's content model, repeaters for lists, a
  paragraph as one text box with Bold and Link, tabs, plain labels; never one field per rendered text node.

## [0.4.0] - 2026-10-03

Any local setup, plain words for newcomers, fewer tokens, updates in one step. Tried on WordPress 7.1.2 with the
free plugins.

### Added

- Updates in one step: `/update-convert-wordpress-skill` (added once with `scripts/update.py --add-command`), or
  `python3 scripts/update.py`. `--check` shows the installed and the newest version and what is new. A git clone
  updates with `git pull` (local edits stop it); any other install gets the release zip from GitHub after a
  backup in `_backups/`. `profile.local.json` is kept, and doctor.py shows the installed version.
- `scripts/doctor.py` checks the computer before a conversion (Python, Node.js, git, PHP, MySQL, Playwright and
  Chromium) and finds the local WordPress app: Laragon, XAMPP, MAMP, WampServer, Local, Laravel Herd, DDEV,
  wp-env, WordPress Studio or a plain PHP and MySQL. It suggests the folder, the address, the database and how
  WordPress is made, gives the install line for anything missing, warns about synced folders, spaces, long paths,
  busy ports and low disk, and writes `--json` for the other tools. Exit 3: nothing can run WordPress here yet.
- `scripts/setup/serve-wp.py` and `wp-router.php` run WordPress at the root of `http://localhost:8081` with PHP's
  built-in server, for apps that give no site its own address (XAMPP, MAMP, WampServer, plain PHP): pretty
  permalinks, the private files answer 403, no admin rights or hosts edits, four PHP workers on macOS and Linux.
- Bring your own WordPress: `make-wp-config.py --existing` adds the kit's settings to a wp-config.php a local app
  made (a backup first, one marked block, duplicate constants turned into comments); `--no-cron` for serve-wp;
  `get-wordpress.py --verify` checks an existing core against the official checksums.
- A live web address as the source: `scripts/capture-site.mjs` saves every page as the browser renders it, with
  its files (CSS, JS, fonts, every srcset size, CSS `url()` and `@import`), as a servable golden master. Only for
  a site the developer owns or may rebuild.
- get-source.py knows GitHub links (also `/tree/<branch>/<folder>`), other git hosts, zip links, live addresses,
  zips and folders. GitHub works without git (its zip download). `--into <web folder>`, `--branch`, `--dry-run`
  (the size first). It stops safely on unsafe or password zips and on a source that is already WordPress (exit
  4), never prints a token from a link, and finds more secret files.
- Intake for newcomers: five plain questions; `new-site.py --start` writes the handoff files as soon as the folder
  is chosen (`--plan-only` replaces them later and keeps the notes); profile `level` (`new`: plain words, each term
  explained once, exact clicks, "Your turn:"; `developer`: short); `references/glossary.md`.
- One OK for a listed group of downloads and installs (profile `oks: group`, the default; `each` asks one by one).
  Deletes and live steps are still asked one at a time.
- Spend fewer tokens: reading rules (the summary first, never node_modules, minified or lock files), scripts that
  print a one-line verdict and only the failures (`-v` or `--all` for the rest, detail in a log file), cropped
  failure screenshots only, a new chat after each gate, and which model fits which step.
- Free plugins, tried on a real WordPress: Secure Custom Fields runs the kit's field groups, options page, seeder
  and `get_field()` as ACF PRO does; free Duplicator 5 builds the package with the kit's filters.
- The kit's own tests in `tests/` (left out of release archives): `python3 -m unittest discover -s tests`.
- The website in `site/`: a landing page in a retro pixel style (Next.js static export, Tailwind 4, 8bitcn/ui,
  Pixelarticons). Auto, Light and Dark themes, a sticky menu on the right that follows the page, a "Why WordPress"
  comparison for sites built with AI or by hand, the author's contact and social links, patch notes read from this
  file. It builds for a subdomain or a subfolder too (`SITE_URL`, `SITE_BASE_PATH`). Release archives leave
  `site/` and `.github/` out.
- CONTRIBUTING.md and two issue templates: Report a problem, Share your setup.

### Changed

- analyze-source.py `--env doctor.json` fills the site draft's folder, address and how WordPress runs.
- new-site.py refuses the example values (Example Co, example.com) left in site.json.
- On a computer with no mail program (XAMPP, MAMP, WampServer, serve-wp), local mail is kept in `_setup/mail/` and
  reported as sent, so local forms answer as they will on live (`kitwp_mail_to_file` forces either way).
- The Duplicator steps follow Duplicator 5 (Backups > Add New > Backup Filters); the filters leave git folders out.
- `htaccess-live.txt` blocks Duplicator's leftovers (installer, its backup, the boot log, the archive,
  `dup-installer/`); live QA also checks `wp-content/duplicator-backups/`.
- The example profile and site file no longer assume one local app: the folder and the address come from
  doctor.py.
- README: requirements through doctor.py, a live address as a source, no paid plugin required.

### Fixed

- `new-site.py --force` replaced `build_field_groups.py` (by then the site's content model) and the parity routes
  and settings: they are kept now, like the plan.
- `serve-wp.py --background` wrote its PID file into the web root when `_setup/` did not exist yet.

## [0.3.0] - 2026-10-03

### Added

- One-command start: `/convert-to-wordpress <git URL, zip or folder>`. New `scripts/get-source.py` makes the
  working copy `<name>-source` (shallow git clone, safe unzip with a single top folder unwrapped, or a copy without
  node_modules and .git), writes `.source.json` (origin, commit or SHA-256, date) and lists secret files. The
  original is never touched.
- analyze-source.py creates the folders for `--json` and `--site-draft`.
- README: how to start, with sample commands and plain-word prompts.

### Fixed

- analyze-source.py reads the `<html>` attributes (lang, dir) from the home page (`index.html` nearest the top),
  not the first HTML file found.

## [0.2.0] - 2026-10-03

Tested on a real PHP and Tailwind landing page, Sprint 0 and all of Sprint 1.

### Changed

- Starter plugins: ACF PRO, Contact Form 7 and Yoast SEO (Yoast was a later install).
- Redirection is optional: only when the site has old URLs to redirect.
- On live, Converter for Media and Contact Form CFDB7 must be installed and active (SKILL.md, launch guide, runbook,
  Done means). Duplicator Pro stays the move to live.
- The profile's `extra_plugins` now holds only optional plugins of your own or your agency's.

### Added (from a trial run on a real PHP and Tailwind landing page)

- analyze-source.py reads server-rendered PHP sites (index.php plus partials): routes from the PHP files and
  `.htaccess`, the golden master by snapshots, the `<html lang>` from the header partial.
- It reads `package.json` even without a framework (build scripts, Tailwind version), skips placeholder tracking ids
  (GTM-XXXXXXX), lists self-hosted fonts, front-end libraries (Swiper, AOS, GSAP...), the code that sends mail, and
  files holding secrets or personal data (never copied).
- `--site-draft` writes a first site.json from the source; new-site.py fills SOURCE-NOTES.md section 1 from
  `_plan/analyze.json`.
- new-site.py writes the parity `routes.json` from the source's routes and sets the reveal rule for AOS.
- Kit: `KITWP_STYLESHEETS` and `KITWP_INLINE_CSS` ship the static site's own compiled CSS (several files and
  critical CSS in the head), in its order; `KITWP_PRELOAD_FONTS`; Google Fonts preconnects only when the site has
  Google font links.
- `tests/parity/swaptest.py`: the S1-05 swap test as a tool (the golden master with the theme CSS, one origin).
  `tests/parity/region-check.mjs`: the S1-07 pixel check of header, footer and pop-up before pages exist.
- `seed/php-content.php`: a PHP source's content variables as content.mjs for export.mjs (secrets and lead
  recipients left out).
- Setup guide: the direct underscoretw.com download for when `wp package install` fails. Gotchas: PHP source URLs,
  env stubs for the golden master, cache-busting queries, AOS in screenshots.

## [0.1.0] - 2026-10-02

First public version.

### Added

- `SKILL.md`: the whole conversion, from the intake questions to go-live and the report, with 13 rules and a
  "Done means" list.
- The team: owner, manager, lead developer guiding a front-end and a WordPress developer, UI, UX, security, tester
  and QA. Builders build, reviewers sign the gates, nobody approves their own work.
- The sprint life cycle (plan, build, review, test, demo, retro, gate), one sprint at a time:
  `scripts/build-map/gate.py` opens the next sprint only when the gate passes and the developer says go.
- Any source: plain HTML, Next.js, React, Astro, Vue, Gatsby, Nuxt, SvelteKit and others.
  `scripts/analyze-source.py` studies the stack, routes, Tailwind, forms, tracking, fonts and languages (including
  right-to-left) before anything is built.
- Starter themes: _tw when the source uses Tailwind, Barebones otherwise. `scripts/new-site.py` prepares either one
  and copies the kit; `--plan-only` writes the Sprint 0 plan before WordPress exists.
- Starter plugins: ACF PRO and Contact Form 7. The ACF menu always shows; field groups live in ACF JSON with stable
  keys, then sync, seed and clean.
- Static first, then dynamic: every page is diffed against the golden master (pixel, DOM, text and SEO).
- Forms and email: Contact Form 7 holds the form, the theme prints the static markup; one-part HTML email, honeypot,
  chat leads through the CF7 REST endpoint.
- SEO, tracking, accessibility, security and performance guides, old URLs kept with 301 redirects, JSON-LD rebuilt
  from the page.
- Launch: a Duplicator Pro runbook with rollback, live QA (pages, tracking, redirects, private files, host rules),
  test leads and a client-ready PDF report.
- `handoff.md` and `ai-handoff-summary.md` in every project, so any agent or developer can carry on.
- Install and run guides for Claude, Codex, Cursor, Gemini CLI, Antigravity, Grok Build and other agents.
- Any business, any country, any language.
