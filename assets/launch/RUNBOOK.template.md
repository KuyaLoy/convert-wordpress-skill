# {{SITE_NAME}}: WordPress launch runbook

Private (the developer). Live address https://{{LIVE_HOST}}, same host as the site it replaces, no DNS change.
Plan about 2 hours on a quiet day (not Friday). The developer does the hosting steps, one at a time, and says
"done" after each; the agent checks and gives the next step. The agent never types a password or key.

## 0. Go / no-go (the day before)

- [ ] P5 closed: `python3 _plan/tools/build-map/gate.py BUILD-MAP.md` shows QA found 0 and the Go-live; final
      local parity run clean; seeder second run "same" everywhere.
- [ ] New copy the static site did not have (a blog page, say) approved by the client; new URLs told to whoever
      runs SEO.
- [ ] reCAPTCHA v3 keys made for {{LIVE_HOST}}; badge position decided.
- [ ] Plugin zips are the newest: `python3 _plan/tools/launch/plugin-versions.py --profile <kit>/profile.local.json`
      lists each zip's plugin, version and file date; the developer confirms each or replaces it in their folder
      (the agent never updates a zip).
- [ ] Mail: SPF includes the server (and the host's outgoing filter, if any); DMARC exists (cPanel > Email
      Deliverability shows both green).
<!-- if:redirects -->
- [ ] Old URL list complete: `_setup/seed/redirects.json` covers every old page and archive URL
      (`_plan/OLD-SITE-URLS.md`); the Redirection plugin is on the live plugin checklist (section 4).
<!-- /if:redirects -->
<!-- unless:redirects -->
- [ ] Old URLs: none to redirect (site.json "redirects" is false and `_plan/OLD-SITE-URLS.md` lists no 301), so no
      Redirection plugin. If old URLs turn up before launch: plan them, set "redirects": true in site.json and run
      `python3 <kit>/scripts/new-site.py _plan/site.json --launch-files` (this runbook again, with those steps).
<!-- /unless:redirects -->
- [ ] Where live leads go: {{LEADS_TO_ITEM}}
- [ ] Client to-dos told to the client: every seeded placeholder (`grep -rn "PLACEHOLDER" _setup/seed` or
      `python3 _plan/tools/report/text-check.py placeholders`, and
      "PLACEHOLDER" in the Media Library search) and every empty fact, each a `decided` finding on the board with
      what the client sends. Launching with any left is the client's choice; they go in the report's next steps.
<!-- if:portal -->
- [ ] Leads portal ready: the project exists in the portal admin (domain {{LIVE_HOST}}) and
      `python3 _plan/tools/report/leads-check.py` with the live key answers OK (the developer runs it; a GET stores
      nothing). On live the address and password go into Theme Settings > Leads portal (section 4).
<!-- /if:portal -->
- [ ] Rollback understood (section 6).

## 1. Back up the live site

1. cPanel > File Manager > `public_html`: select all > Compress > `<old>-backup-YYYYMMDD.zip`. Download it.
2. Download the current `.htaccess` separately (keep any "cPanel-generated handler" block).
3. If the live site is an old WordPress: also a full cPanel backup (home directory + database). Keep it 90 days.
4. Note the PHP version (cPanel > PHP Selector or MultiPHP Manager). WordPress needs 8.1+; aim for 8.3.

## 2. Build the package (local)

1. Stop `npm run dev` (or watch); <!-- starter:barebones -->`npm run build`<!-- /starter:barebones --><!-- starter:tw -->`npm run prod`<!-- /starter:tw --> in `wp-content/themes/{{THEME}}`.
2. Local checks: no PHP notices in `wp-content/debug.log` from today; ACF (or SCF) > Field Groups: nothing to sync.
3. Duplicator > Backups > Add New (older versions and Pro: Packages > New), default name. Backup Filters > File
   Filters (older: Archive > Files > Filters): tick Enable, then paste the output of
   `python3 _plan/tools/launch/duplicator-filters.py <root as Duplicator shows it> {{THEME}}<!-- starter:tw --> --starter tw<!-- /starter:tw -->`
   (full paths, each ending with `;`, one per line, never `;;`).
4. Build. Scan warnings about size usually point at a folder that should be filtered (tests, node_modules). On
   Windows with serve-wp, keep the Backups page open until it is done (reload it if it stays on "Initializing").
5. Download the installer and the archive.

## 3. Move it to the server

1. cPanel > MySQL Databases: new database, new user, all privileges. The developer keeps the password.
2. cPanel > PHP Selector: PHP 8.3 with zip, mysqli (nd_mysqli), pdo_mysql (nd_pdo_mysql), intl, imagick, opcache.
   "Class ZipArchive not found" in the installer = zip is off; an nd_mysqli "conflicting" warning is harmless.
3. Move the old site out of `public_html` into a sibling folder `<old>-old` (rollback = move it back). Leave
   `.ftpquota`, `.well-known` and `cgi-bin`.
4. Upload `installer.php` and the archive to `public_html`. Open `https://{{LIVE_HOST}}/installer.php`: database
   details (the developer types them), URL `https://{{LIVE_HOST}}`. Run it.
5. After the installer: nothing of it is left in `public_html` (anyone could download it): `installer.php` and
   `installer-backup.php` answer 404; `dup-installer/`, `dup-installer-bootlog__*.txt` and the archive (`.zip` or
   `.daf`) are gone. Duplicator keeps the original `.htaccess` in its `original_files_` folder.
6. `wp-config.php` (Duplicator copied the local one): `WP_ENVIRONMENT_TYPE` `production` (on "local" the seeder
   loads and every lead goes to the admin only), `WP_DEBUG`, `WP_DEBUG_LOG`, `WP_DEBUG_DISPLAY` false,
   `DISALLOW_FILE_EDIT` true. The `ACF_PRO_LICENSE` line from the local profile: removed, unless the developer
   chooses to keep it (it activates this URL too).
7. `.htaccess` = `_setup/launch/htaccess-live.txt` (paste the cPanel handler block back at the top if there was one).

## 4. Switch on (wp-admin, live)

1. Settings > Reading: untick "Discourage search engines". Settings > Permalinks: Save.
2. Local addresses: the installer replaced the local address, but other local hosts (a sister site's `.test` link,
   a setting saved with `localhost`) stay in the content and settings. Replace them, dry run first, then check:
   - [ ] `wp search-replace '//{{LOCAL_HOST}}' '//{{LIVE_HOST}}' --all-tables --dry-run`, then without `--dry-run`;
         the same for each other local host the check below finds (its live address from the client or the plan).
   - [ ] `wp search-replace 'http://{{LIVE_HOST}}' 'https://{{LIVE_HOST}}' --all-tables` (links saved over http).
   - [ ] `wp db search '[a-z0-9-]+\.test|localhost' --all-tables --regex` finds nothing (no WP-CLI: the same search in
         phpMyAdmin); live-qa.py's "local" check (section 5) finds no local host on any page.
3. **The live plugin checklist** (the one list; live only, staging gets none of it). Live has exactly ACF PRO,
   Contact Form 7, Yoast SEO, the plugins below and Duplicator until the clean-up (section 5), nothing else unless
   the task asks for it (site.json "task_plugins"). Each installed and active:
{{LIVE_PLUGINS}}
   - [ ] Contact Form CFDB7 (every enquiry kept in wp-admin).
   - [ ] Converter for Media (WebP and AVIF): then regenerate the images and check a few pages.
<!-- if:redirects -->
   - [ ] Redirection: Tools > Redirection, import `_setup/seed/redirects.json` (the real list, not the sample). Every
         live redirect goes here, never in `.htaccess` (host rules only) or theme code.
<!-- /if:redirects -->
   - [ ] reCAPTCHA v3: Contact > Integration > reCAPTCHA, the keys for {{LIVE_HOST}} (the developer pastes them),
         active on every form: the test leads in section 5 go through with it.
<!-- if:leadsitem -->
   - [ ] {{LEADS_ITEM}}
<!-- /if:leadsitem -->
   - [ ] {{CACHE_PLUGIN}} (the cache plugin): page cache and browser cache on; CSS and JS options one at a time, each
         followed by a parity spot check and `live-qa.py` (anything that changes a pixel or breaks a form goes off
         again); purge everything after "Discourage search engines" is unticked.
   Profile plugins come only from the developer's plugin folder (`plugin_zips`), never downloaded elsewhere. Prove
   the list: `wp plugin list --format=json --fields=name,status,title` on the server (or the Plugins screen, one
   per line) saved as `_plan/live-plugins.json`, then
   `python3 _plan/tools/report/plugin-check.py _plan/site.json --env live --profile <kit>/profile.local.json --list _plan/live-plugins.json`
   says OK (missing, inactive or extra plugins are a FAIL). live-qa.py checks the reCAPTCHA script on the form pages.
<!-- if:tracking -->
<!-- if:trackplugin -->
4. Tracking goes through {{TRACKING_WHERE}} only (the profile's tracking plugin): the Google Tag Manager ID
   {{GTM_ID}} goes in it, on live only. The theme has no tracking fields and loads no GTM of its own
   (`self-check.py --profile` flags it), so the container loads once.
<!-- /if:trackplugin -->
<!-- unless:trackplugin -->
4. Tracking: the Google Tag Manager ID {{GTM_ID}} goes where this build loads it ({{TRACKING_WHERE}}), on live
   only (local and staging stay empty). If a tracking plugin loads the same container, leave the theme's setting
   empty so it loads once.
<!-- /unless:trackplugin -->
<!-- /if:tracking -->
<!-- unless:tracking -->
<!-- if:trackplugin -->
4. Tracking: {{TRACKING_WHERE}} is installed and stays empty until the tracking task brings the GTM ID or the
   numbers; tracking goes through it only (no tracking fields or GTM in the theme).
<!-- /if:trackplugin -->
<!-- unless:trackplugin -->
4. Tracking: none in this build (site.json "gtm" is empty). If the tracking task brings an ID, add it here first.
<!-- /unless:trackplugin -->
<!-- /unless:tracking -->
5. ACF > Updates: the ACF PRO licence active (the developer). The ACF menu must show (never hide it on live).
6. Read `wp-content/debug.log` once (a second copy of a plugin gives "Cannot redeclare" fatals); list the live
   plugins for the handoff.
7. Users: the client's own login (Editor role) if they edit; never share the admin account.

**Staging** (a public copy before live, when the build has one): ACF PRO, Contact Form 7 and Yoast SEO only
(<!-- if:redirects -->Redirection for the redirects, <!-- /if:redirects -->Duplicator for the move); none of the live
plugin checklist and no reCAPTCHA keys (`plugin-check.py ... --env staging` says OK); it stays noindex
(`live-qa.py --hidden`). The import replaces wp-config, the root .htaccess and the Reading setting: the must-use
file `wp-content/mu-plugins/kitwp-environment.php` and the theme's `acf-json/.htaccess` travel in the package;
`wp eval 'echo wp_get_environment_type();'` on staging says `staging` (paste the output).

## 5. Checks (references/qa-report.md has the full list)

- [ ] `python3 _plan/tools/report/live-qa.py https://{{LIVE_HOST}}<!-- if:tracking --> --gtm {{GTM_ID}}<!-- /if:tracking --> --local {{LOCAL_HOST}} --theme wp-content/themes/{{THEME}}<!-- if:redirects --> --redirects _setup/seed/redirects.json<!-- /if:redirects -->`
<!-- if:redirects -->
      (export the real redirects first, the seed file is a sample)
<!-- /if:redirects -->
      ALL PASS (bot filter: run `live-qa-console.js` in a real browser instead).
<!-- if:tracking -->
- [ ] `node _plan/tools/report/track.mjs https://{{LIVE_HOST}} {{GTM_ID}} / /thank-you/`: GTM loaded; the conversion
      request only on /thank-you/.
<!-- /if:tracking -->
<!-- if:forms -->
- [ ] One real test lead per form ({{FORMS_LIST}}) with the real submit button: lands on /thank-you/, the email
      arrives, every recipient "Accepted" in cPanel > Track Delivery. Open the first form's page with
      `?utm_source=qa&utm_medium=test&utm_campaign=launch&gclid=TEST`: its email's Lead source table
      shows them (CFDB7 too), and GTM's preview shows `generate_lead` on /thank-you/.
<!-- if:portal -->
      Each test lead also shows in the leads portal's form counts.
<!-- /if:portal -->
<!-- /if:forms -->
<!-- unless:forms -->
- [ ] No lead forms on this site (site.json "forms" is empty): no test leads.
<!-- /unless:forms -->
- [ ] Real phones (iOS Safari, Android Chrome): menu, forms, call links.
- [ ] PageSpeed Insights, mobile and desktop, on Home, one template page, Contact (numbers go in the report as they are).
- [ ] Search Console: sitemap `sitemap_index.xml` submitted (whoever owns SEO).
<!-- if:redirects -->
- [ ] Next 30 days: Tools > Redirection > 404s weekly; add a redirect for anything real.
<!-- /if:redirects -->
<!-- unless:redirects -->
- [ ] Next 30 days: Search Console > Pages > Not found weekly; an old URL that is really used gets planned as a
      redirect (the Redirection plugin then joins the live plugins).
<!-- /unless:redirects -->

**Clean-up, after live QA is at 0 and the report is done** (Duplicator is not needed any more):
- [ ] Duplicator > Backups: delete every backup; then Plugins: deactivate and delete Duplicator (Pro).
- [ ] File Manager: `wp-content/backups-dup-pro/` (or `backups-dup-lite/`, `duplicator-backups/`) and any installer
      or archive file in `public_html` deleted.
- [ ] `plugin-check.py _plan/site.json --env live --profile <kit>/profile.local.json --list _plan/live-plugins.json
      --files _plan/live-files.txt --done` says OK with a fresh plugin list and `ls -a ~/public_html
      ~/public_html/wp-content` saved as `_plan/live-files.txt` ("Duplicator gone").

## 6. Rollback (a check fails and cannot be fixed quickly)

1. Move the WordPress files out of `public_html` into `wp-failed-YYYYMMDD` (keep them for the fix).
2. Move `<old>-old` back into `public_html`; restore the old `.htaccess`.
3. A static site needs no database, so it is back at once. Check Home, a template page, the form.
