# Scripts at a glance

Paths are relative to the skill folder; in a project the same tools are in `_plan/tools/` (the parity tools in
the theme's `tests/parity/`). Every Python script is standard library only (Python 3.9 or later) and runs from any
shell: PowerShell, cmd, Git Bash, a Mac or Linux terminal. Use the `python3` command doctor.py printed (often
`py -3` on Windows). The Node scripts need Node.js 18 or later and Playwright with Chromium.

| Script (in the project: `_plan/tools/...`) | Does |
|---|---|
| `scripts/doctor.py` | This computer: tools, the local WordPress app, where to build (`--json`) |
| `scripts/start.py` | The intake in one call: new-site.py --start, get-source.py (the copy) and analyze-source.py (the study) |
| `scripts/get-source.py`, `analyze-source.py` | The working copy (clone, zip, folder or a capture); the study of it |
| `scripts/new-site.py` | `--plan-only` for P0; then prepares the starter theme and copies the kit in |
| `scripts/snapshot-routes.mjs` | Rendered HTML of every route, for client-rendered or server sources |
| `scripts/setup/setup.py` | P1-01 in one call: database, get-wordpress, make-wp-config, serve-wp (if needed), install-wp |
| `scripts/setup/install-wp.py` and the others | Install, admin, settings, plugins; the steps one by one when one needs repeating |
| `scripts/report/text-check.py` | The docs' grep checks in Python, for any shell: `fill` (report), `plain` (client pack), `dupes`, `oneoff` (self-check), `placeholders` |
| `scripts/report/leads-check.py` | The leads portal endpoint and key with a GET (stores nothing; the key never printed) |
| `scripts/launch/lead-source-plugin.py` | The Lead source table and form attribution as a must-use plugin for a WordPress site the kit did not build |
| `scripts/launch/plugin-versions.py` | Go/no-go: each plugin zip in the profile's folder with its version and file date |
| `scripts/report/plugin-check.py` | The plugins per environment (local, staging, live) against the kit's list; `--done`: Duplicator gone after live QA |
| `scripts/acf/build_field_groups.py`, `sync.php` | ACF JSON, stable keys (`--check`); database sync |
| `scripts/seed/export.mjs`, `export-pages.py` | Static content into `_setup/seed/` for Tools > Seeder |
| `scripts/build-map/gate.py`, `render.py`, `live.py` | The phase gate; the private progress page, static and live (the database rows) |
| `scripts/report/self-check.py` | Before every QA run: the classes a build catches itself (instructions, casts, guards, dead code, launch files) |
| `scripts/parity/` (the theme's `tests/parity/`) | `check-section.py` (one call per section), pixel, text, SEO and DOM diffs, `seodiff.py` (head tags and JSON-LD values), `changed-routes.py` (what a fix pass changed), `design-check.mjs` (states, motion, long content), `long-content.php`; mirror and server for cloud runs |
| `scripts/update.py` | Updates this skill from GitHub (`--check` only looks); `/update-convert-wordpress-skill` runs it |
