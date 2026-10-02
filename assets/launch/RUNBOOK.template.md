# {{SITE_NAME}}: WordPress launch runbook

Private (the developer). Live domain https://{{DOMAIN}}, same host as the site it replaces, no DNS change.
Plan about 2 hours on a quiet day (not Friday). The developer does the hosting steps, one at a time, and says
"done" after each; the agent checks and gives the next step. The agent never types a password or key.

## 0. Go / no-go (the day before)

- [ ] Every sprint closed: `python3 _plan/tools/build-map/gate.py BUILD-MAP.md` says all sprints are DONE; final
      local parity run clean; seeder second run "same" everywhere.
- [ ] New copy the static site did not have (a blog page, say) approved by the client; new URLs told to whoever
      runs SEO.
- [ ] reCAPTCHA v3 keys made for {{DOMAIN}} and {{LOCAL_HOST}}; badge position decided.
- [ ] Mail: SPF includes the server (and the host's outgoing filter, if any); DMARC exists (cPanel > Email
      Deliverability shows both green).
- [ ] Old URL list complete: `_setup/seed/redirects.json` covers every old page and archive URL.
- [ ] Rollback understood (section 6).

## 1. Back up the live site

1. cPanel > File Manager > `public_html`: select all > Compress > `<old>-backup-YYYYMMDD.zip`. Download it.
2. Download the current `.htaccess` separately (keep any "cPanel-generated handler" block).
3. If the live site is an old WordPress: also a full cPanel backup (home directory + database). Keep it 90 days.
4. Note the PHP version (cPanel > PHP Selector or MultiPHP Manager). WordPress needs 8.1+; aim for 8.3.

## 2. Build the package (local)

1. Stop `npm run dev` (or watch); <!-- starter:barebones -->`npm run build`<!-- /starter:barebones --><!-- starter:tw -->`npm run prod`<!-- /starter:tw --> in `wp-content/themes/{{THEME}}`.
2. Local checks: no PHP notices in `wp-content/debug.log` from today; ACF > Field Groups: nothing to sync.
3. Duplicator > Packages > New, default name. Archive > Files > Filters: paste the output of
   `python3 _plan/tools/launch/duplicator-filters.py <root as Duplicator shows it> {{THEME}}<!-- starter:tw --> --starter tw<!-- /starter:tw -->`
   (full paths, each ending with `;`, one per line, never `;;`).
4. Build. Scan warnings about size usually point at a folder that should be filtered (tests, node_modules).
5. Download the installer and the archive.

## 3. Move it to the server

1. cPanel > MySQL Databases: new database, new user, all privileges. The developer keeps the password.
2. cPanel > PHP Selector: PHP 8.3 with zip, mysqli (nd_mysqli), pdo_mysql (nd_pdo_mysql), intl, imagick, opcache.
   "Class ZipArchive not found" in the installer = zip is off; an nd_mysqli "conflicting" warning is harmless.
3. Move the old site out of `public_html` into a sibling folder `<old>-old` (rollback = move it back). Leave
   `.ftpquota`, `.well-known` and `cgi-bin`.
4. Upload `installer.php` and the archive to `public_html`. Open `https://{{DOMAIN}}/installer.php`: database
   details (the developer types them), URL `https://{{DOMAIN}}`. Run it.
5. After the installer: `installer.php` answers 404 and no zip or archive is left in `public_html` (anyone could
   download it). Duplicator keeps the original `.htaccess` in its `original_files_` folder.
6. `wp-config.php` (Duplicator copied the local one): `WP_ENVIRONMENT_TYPE` `production` (on "local" the seeder
   loads and every lead goes to the admin only), `WP_DEBUG`, `WP_DEBUG_LOG`, `WP_DEBUG_DISPLAY` false,
   `DISALLOW_FILE_EDIT` true.
7. `.htaccess` = `_setup/launch/htaccess-live.txt` (paste the cPanel handler block back at the top if there was one).

## 4. Switch on (wp-admin, live)

1. Settings > Reading: untick "Discourage search engines". Settings > Permalinks: Save.
2. Contact > Integration > reCAPTCHA: the developer pastes the site key and secret.
3. Tracking: the GTM container (or the tracking plugin) set for the live host only.
4. ACF > Updates: the developer activates the ACF PRO licence. The ACF menu must show (never hide it on live).
5. Plugins added only on live, if the task wants them (enquiry storage, image conversion): the developer installs.
6. Read `wp-content/debug.log` once (a second copy of a plugin gives "Cannot redeclare" fatals); list the live
   plugins for the handoff.
7. Users: the client's own login (Editor role) if they edit; never share the admin account.

## 5. Checks (references/qa-report.md has the full list)

- [ ] `python3 _plan/tools/report/live-qa.py https://{{DOMAIN}} {{GTM_ID}} _setup/seed/redirects.json {{LOCAL_HOST}}`
      ALL PASS (bot filter: run `live-qa-console.js` in a real browser instead).
- [ ] `node _plan/tools/report/track.mjs https://{{DOMAIN}} {{GTM_ID}} / /thank-you/`: GTM loaded; the conversion
      request only on /thank-you/.
- [ ] One real test lead per form (inline, pop-up, chat) with the real submit button: lands on /thank-you/, email
      arrives, every recipient "Accepted" in cPanel > Track Delivery.
- [ ] Real phones (iOS Safari, Android Chrome): menu, pop-up, forms, call links.
- [ ] Lighthouse mobile on Home, one template page, Contact (numbers go in the report as they are).
- [ ] Search Console: sitemap `sitemap_index.xml` submitted (whoever owns SEO).
- [ ] Next 30 days: Tools > Redirection > 404s weekly; add a redirect for anything real.

## 6. Rollback (a check fails and cannot be fixed quickly)

1. Move the WordPress files out of `public_html` into `wp-failed-YYYYMMDD` (keep them for the fix).
2. Move `<old>-old` back into `public_html`; restore the old `.htaccess`.
3. A static site needs no database, so it is back at once. Check Home, a template page, the form.
