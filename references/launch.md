# Launch: Duplicator on cPanel, and changes after go-live

Read this after Sprint 7 closes. The project's own step list is `_setup/launch/RUNBOOK.md` (from
`assets/launch/RUNBOOK.template.md`): go/no-go, backup, package, move, switch on, checks, rollback. The developer
does every hosting step; the agent gives one step at a time, waits for "done", checks, then gives the next.

## Contents

- Before the day
- The package
- The move
- After the installer
- Other hosts
- Changes on live after launch
- Host quirks

## Before the day

- gate.py says every sprint is DONE; the final full parity run is clean; the seeder's second run says "same".
- The client approved any new copy; new URLs are known to whoever owns SEO.
- reCAPTCHA keys exist for the live domain and the local host; the badge position is decided.
- Mail: SPF includes the server (and the host's outgoing filter, for example MailChannels) and a DMARC record
  exists (cPanel > Email Deliverability).
- A quiet day, not a Friday, with about two hours free.

## The package

- Build the theme assets (Barebones `npm run build`; _tw `npm run prod`), with `npm run dev` stopped.
- Duplicator: the free plugin (`duplicator`) is enough for a normal site; Pro adds scheduled and cloud backups,
  server-to-server import and more. Tested free: Duplicator 5 on WordPress 7.1, with every private path left out.
- Duplicator > Backups > Add New (older versions and Pro: Packages > New). Backup Filters > File Filters: tick
  Enable, then one textarea: full paths, each ending with `;`, one per line, never `;;`. Generate them:
  `python3 _plan/tools/launch/duplicator-filters.py <root as Duplicator shows it> <theme>` (add `--starter tw` for
  _tw, `--check <root on this machine>` to mark paths that do not exist). Left out: the plan, setup and handoff
  files, debug.log, the theme's tests (parity shots can be gigabytes), node_modules, vendor, build configs,
  dotfiles and git folders, readme.html, `wp-content/upgrade*`.
- A size warning in the scan usually points at a folder that should be filtered.
- On serve-wp: macOS and Linux run four PHP workers, so the backup builds on its own in about a minute. On
  Windows it answers one request at a time: Duplicator then lets the browser drive the build ("Client-side
  Kickoff"), so keep the Backups page open until the backup is done, and reload it if it stays on "Initializing"
  for a minute. The scan's Next can take about 45 seconds there.

- **No wp-admin login needed (Duplicator Pro):** `wp duplicator build --template=<id> --phpzip`. Set the
  template once (`wp eval-file`: `TemplateEntity` copy of the default, `archive_filter_on`, `archive_filter_dirs`
  and `archive_filter_files` from the filter lists, `installer_opts_secure_on = 1` with a password, and the global
  installer name mode `withhash`). The agent generates the installer password and writes it to a file OUTSIDE the
  project (never in chat or notes); the developer pastes it into the installer, and the file is deleted after.
- Check the archive before upload: list it (PHP ZipArchive) and grep for the private paths; the database dump is
  in `dup-installer/dup_descriptors_*/db_dumps/`.

## DNS first (optional): the maintenance page

When the developer wants DNS switched before the install, the docroot is public at once. Put up the 503 page
first: `_setup/launch/maintenance/maintenance.html` and `htaccess-maintenance.txt` (as `.htaccess`; keep any
cPanel block below it). Every path answers 503 with Retry-After, `.well-known` and the installer still pass. Check
with `curl --resolve <host>:443:<server ip>` (GET only) before the A record changes.

## The move

- Back up first: compress `public_html` and download it; download `.htaccess` on its own (keep any
  "cPanel-generated handler" block). Replacing an old WordPress: a full cPanel backup too (home directory and
  database).
- New database and user (the developer keeps the password). PHP 8.3 with zip, mysqli, pdo_mysql, intl, imagick and
  opcache. "Class ZipArchive not found" in the installer means zip is off.
- Move the old site into a sibling folder (`<old>-old`) so rollback is one move. Leave `.ftpquota`, `.well-known`
  and `cgi-bin` where they are (they may not exist: fine).
- Upload `installer.php` and the archive; run the installer with the https live URL; the developer types the
  database details.

## After the installer

- **The installer replaces `.htaccess` the moment it extracts** (the maintenance page and every private-path rule
  are gone) and moves the host's `.htaccess`, `.user.ini` and `php.ini` into
  `dup-installer/dup_descriptors_*/orig_files/installer_host_*`. From then on the archive (with wp-config inside)
  is downloadable by its name until the clean-up. Do the clean-up at once: log in from the installer's last step
  (it removes its files). If the developer's machine cannot reach the site yet (DNS cache), remove the archive,
  the installer, `dup-installer/` and the boot log through cPanel straight away; do not wait.
- Then restore the host's `php.ini` and `.user.ini` from those copies, and append the old `.htaccess`'s
  cPanel-generated block (handler or "php ini directives") below `htaccess-live.txt`.
- **Installer screen:** it fills the site URL from the host you opened it on. Open it on the canonical host, or
  switch to Advanced and set every URL field (site, wp-content, uploads, plugins, mu-plugins) to it. Switching
  to Advanced reloads the form and clears the database fields: switch first, then type them. A MariaDB vs MySQL
  notice is harmless for utf8mb4 tables.
- Nothing of the installer is left in `public_html` (anyone could download it): `installer.php` and
  `installer-backup.php` answer 404, and `dup-installer/`, `dup-installer-bootlog__*.txt` and the archive (`.zip` or
  `.daf`) are gone. The installer's last step offers to remove them; `htaccess-live.txt` blocks them as well.
- wp-config: `WP_ENVIRONMENT_TYPE` production, debug off, `DISALLOW_FILE_EDIT` true. Left on `local`, the seeder
  loads and every lead goes to the admin only.
- `.htaccess` = `htaccess-live.txt`: http and www to https in one hop, the private-files block, the WordPress
  block, compression and caching.
- wp-admin: untick "Discourage search engines"; save permalinks; the reCAPTCHA keys and the ACF licence (the developer
  types them); tracking set for the live host; Converter for Media and Contact Form CFDB7 installed and active (ask
  first), then the profile's `extra_plugins` (the `required` ones must be active; a plugin that registers itself with
  an outside service on activation is activated again once DNS points here); read `debug.log` once; list the live
  plugins.
- Leads portal (when the profile has one): the endpoint and key go into the live wp-config (the developer pastes
  them; the local copy may keep them, the theme never sends from local), then one TEST lead per form on live.
- Caching plugins on live (LiteSpeed Cache): purge everything after "Discourage search engines" changes, or
  pages keep the old robots meta for a week.
- After DNS moves: run AutoSSL again (cPanel > SSL/TLS Status) and check the new certificate covers the apex and
  www. An old `_acme-challenge` TXT record left in the zone breaks the wildcard check ("Incorrect TXT record"):
  remove it.
- Then live QA (`references/qa-report.md`).
- Rollback when a check fails and cannot be fixed quickly: move the WordPress files out, move the old site back,
  restore the old `.htaccess`. A static site needs no database, so it is back at once.

## Other hosts

Duplicator works on most hosts. Without cPanel: the same steps through the host's file manager, database tool and
PHP settings. With shell access: WP-CLI (`wp db export`, copy the files, `wp db import`,
`wp search-replace 'http://<local_host>' 'https://<domain>' --skip-columns=guid`), then the same wp-config,
`.htaccess` and wp-admin steps. Ask the developer which path the host allows.

## Changes on live after launch

- Surgical: change only what the task needs. Keep a rollback copy of every file you replace
  (`_setup/launch/rollback-<date>/`), and test before and after.
- Build a PHP file completely before it replaces a live one: a half-edited file is a parse error on live. Run php -l,
  PHPCS and the duplicate function check first.
- Theme fixes ship as `<theme>-theme-update-<date>.zip` with 0644 files and 0755 folders (zips made in some VMs keep
  0700 modes, and LiteSpeed answers 403).
- Field group edits made on live write JSON into the live theme: copy `acf-json/` back to local.
- The developer may install plugins on live after the move: list them before writing the handoff.

## Host quirks

- **LiteSpeed** can answer a repeat request for a missing URL with a soft 404 (status 200): check the 404 twice.
- **Imunify360** (and similar bot filters) can answer scripted requests with "One moment, please" or 415: run the
  checks in a real browser (`live-qa-console.js`).
- `.well-known` must keep working for certificate renewals: the host rules skip it.
