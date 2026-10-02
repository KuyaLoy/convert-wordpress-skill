# Launch: Duplicator Pro on cPanel, and changes after go-live

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
- Duplicator Pro > Packages > New. Filters: one textarea, full paths, each ending with `;`, one per line, never
  `;;`. Generate them: `python3 _plan/tools/launch/duplicator-filters.py <root as Duplicator shows it> <theme>`
  (add `--starter tw` for _tw, `--check <root on this machine>` to mark paths that do not exist). Left out: the plan,
  setup and handoff files, debug.log, the theme's tests (parity shots can be gigabytes), node_modules, vendor, build
  configs and dotfiles, readme.html, `wp-content/upgrade*`.
- A size warning in the scan usually points at a folder that should be filtered.

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

- `installer.php` answers 404, and no zip or archive is left in `public_html` (anyone could download it).
- wp-config: `WP_ENVIRONMENT_TYPE` production, debug off, `DISALLOW_FILE_EDIT` true. Left on `local`, the seeder
  loads and every lead goes to the admin only.
- `.htaccess` = `htaccess-live.txt`: http and www to https in one hop, the private-files block, the WordPress
  block, compression and caching.
- wp-admin: untick "Discourage search engines"; save permalinks; the reCAPTCHA keys and the ACF licence (the
  developer types them); tracking set for the live host; read `debug.log` once; list the live plugins.
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
