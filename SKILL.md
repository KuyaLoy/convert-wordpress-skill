---
name: convert-to-wordpress
description: Converts any existing website (plain HTML, Next.js, React, Astro, Vue and other stacks) into a 1:1 WordPress site with the same design, URLs, SEO and tracking, every page editable in ACF PRO (or the free Secure Custom Fields) and every form in Contact Form 7. Works as a full team (owner, manager, lead and developers, UI, UX, security, tester, QA), one sprint at a time with a gate per sprint, from intake and local setup to go-live, live QA and the report. Use whenever a site built outside WordPress has to be rebuilt in WordPress.
license: GPL-2.0-or-later
---

# Convert a website to WordPress, 1:1

The site already exists: as code, as a build, or live. The job is to rebuild it in WordPress so it looks and
behaves the same at every screen size, keeps every URL and SEO signal, and lets editors change everything in
wp-admin: content in ACF PRO or Secure Custom Fields, forms and emails in Contact Form 7. Any stack, any kind of
business, any country and language.

Its lessons come from real builds: a 36-page Next.js export, a PHP and Tailwind landing page, and a clinic site
taken live on cPanel.

**The yardstick for every choice:** clean quality, delivered fast without losing quality, seen from the client's
side. The client is usually not technical: what they see, read, edit and receive must be simple and plain.

## The kit

Paths are relative to this file's folder:

| Path | What |
|---|---|
| `references/` | The detailed guides. Read only the one you need, when you need it (table below) |
| `scripts/` | The tools. `new-site.py` copies them into the project's `_plan/tools/` |
| `assets/` | Templates: theme code, seed examples, plan documents, the board, handoff, launch, report |
| `profile.local.json` | The developer's or agency's defaults (never committed); start from `profile.example.json` |

No `scripts/` folder next to this file (a copy saved inside a chat app)? The kit is a clone of
https://github.com/KuyaLoy/convert-wordpress-skill: ask the developer where theirs is (none yet: ask, then clone it).

| Read | When |
|---|---|
| `references/team-and-sdlc.md` | At the start of every sprint: the roles, the seven sprint steps, the gate |
| `references/setup.md` | Intake, the database, WordPress, the starter theme, the plugins |
| `references/source-types.md` | Studying the source, the golden master for each stack, Tailwind, languages |
| `references/build.md` | Sprints 1 to 4: CSS, head, ACF, media, templates, the seeder, parity checks |
| `references/forms-email.md` | Sprint 5: Contact Form 7, the email, spam protection, the chat |
| `references/seo-security.md` | Sprint 6, and the security basics from Sprint 1 |
| `references/launch.md` | Go-live with Duplicator, other hosts, changes after launch |
| `references/qa-report.md` | Live QA, test leads, the report, the task comment |
| `references/handover.md` | After live QA: the client pack (website sheet, editing guide, message) |
| `references/gotchas.md` | Before anything risky. Add every new lesson there |
| `references/agents.md` | Each agent; beginner mode; fewer tokens; which model for which step |
| `references/glossary.md` | Plain-word meanings for newcomers |

## Rules (always)

1. **1:1 above all.** The golden master (the site exactly as visitors get it) is the design. Copy its markup and
   CSS; fields replace content, never structure, classes or order. The diffs decide, not the eye.
2. **Static first, then dynamic.** Every section is copied as static HTML and diffed to zero before it gets fields.
3. **The task decides.** The task tracker's requests are the scope; where they differ from this skill's defaults,
   the task wins. Campaign and landing page URLs never change.
4. **Ask first** before any download, plugin or package install, database change, delete, live change or publish.
   One OK covers the items listed with it (each named with its source and size); profile `oks: each` asks one by one.
   Deletes and live steps: always one at a time.
5. **Never type a password, licence key or API key.** The developer pastes them. Reports and messages say
   `[PASTE PASSWORD HERE]`. ACF PRO's key: the developer pastes it into wp-config (`ACF_PRO_LICENSE`).
6. **One sprint at a time.** Nothing from a later sprint starts until the current sprint's gate passes and the
   developer says go (`gate.py`, below).
7. **Manual steps** for the developer (wp-admin, the host panel, Duplicator): one at a time, then wait for "done".
8. **Handoff files** (`handoff.md`, `ai-handoff-summary.md` at the project root): update both after every
   significant change and before stopping. A new session reads the summary first.
9. **Private:** BUILD-MAP.md and its board page, `_plan/`, `_setup/`, the handoff files. Anything for the client or
   a stakeholder: plain language, verified facts only, no sprint or story numbers, files as PDF.
10. **Read only:** the source folder and the golden master. Build or `npm install` only in a copy.
11. **Code:** every global prefixed (`<prefix>_`); PHP 8.1 to 8.4; escape at output, sanitise input, nonces and
    capability checks. After every PHP save: `php -l`, PHPCS and the duplicate function check.
12. **Live:** surgical changes only, a rollback copy of every replaced file, PHP files complete before upload,
    theme zips with 0644 files and 0755 folders.
13. **Replies** follow the profile's `level`: `new` = plain words, each term explained once
    (`references/glossary.md`), exact clicks, "Your turn:" at the end; `developer` = short (asked at intake).
14. **Spend less:** read the summary, not whole files; never read node_modules, minified, vendor or lock files;
    scripts copy markup and print summaries; screenshots only as cropped failures; a new chat after each gate.

## The team

You work as a full senior team, one role at a time; builders build, reviewers check, nobody approves their own work.
Owner (scope, the 1:1 rule), Manager (plan, board, handoff, updates), Lead developer (architecture, the backlog,
every review), UI (visual parity), UX (behaviour and editing), Security, Tester (diffs, seeder, forms) and QA (real
browsers, live) sign the gates; the Front-end developer (static markup, CSS, JS) and the WordPress developer
(fields, seeder, CF7, SEO) build. The Lead splits each story into tasks; each task ends with a three-line hand-off
note (changed, tested, open) and the Lead's review. With subagents, a developer subagent may take a task card and
the sprint review is always a fresh subagent; without them, switch hats explicitly. "The developer" is the human
running the build: plugins, money, secrets, live steps and every sign-off are theirs.

## The life cycle

| Phase | Sprint | Gate |
|---|---|---|
| Requirements | Intake | The questions answered, `site.json` written |
| Analysis and design | S0 Planning | Plan documents, board, decisions |
| Build and test | S1 Foundation, S2 the template most pages share, S3 the other fixed templates, S4 flexible pages, S5 forms and email, S6 SEO / security / performance | Each sprint's gate |
| System test | S7 QA and launch prep | Full parity run, runbook, editing guide |
| Release | Launch | Live, rollback ready |
| Verification | Live QA and report | ALL PASS, test leads, report handed over |

Every sprint runs the same seven steps: **plan** (goal, entry criteria, the Lead's backlog) > **build** (task by
task) > **review** (a fresh reviewer on everything changed) > **test** > **demo** (show the developer) > **retro**
(keep, change, try in the Log) > **gate** (each reviewing role writes PASS, n/a or what is open in "Sprint gates").

```
python3 _plan/tools/build-map/gate.py BUILD-MAP.md           # 0 may close, 1 open items listed, 2 a rule broken
python3 _plan/tools/build-map/gate.py BUILD-MAP.md --close   # only after every gate passes and "go <date>"
```

Run gate.py at the start of every session and before asking for a sign-off. Write `go <date>` in the Sign-off cell
only after the developer says go in the chat. After `--close`: plan the next sprint, re-render the board page,
update both handoff files.

## Start: intake

1. **An existing project?** Read `ai-handoff-summary.md`, run gate.py, continue from the Next action.
2. **This computer:** `python3 <kit>/scripts/doctor.py --name <site> --json doctor.json` (`python3` = the command it
   prints, often `py -3` on Windows; no Python at all: `references/agents.md`). It finds the tools and the local
   WordPress app and suggests the folder, address and database. No shell (a chat app): say so, offer the plan from
   uploaded files. Exit 3: help install what it names, then run it again.
3. **Ask once**, in one batch (a question tool, else a short numbered list), the suggestion first, in plain words
   for `level: new`: where to build; the site (GitHub link, zip, folder or only its address) if not given with
   `/convert-to-wordpress <source>`; built websites before?; ACF PRO (paid) or the free Secure Custom Fields; live
   domain and host; lead email recipients; country, languages, right-to-left; the task's scope; old URLs to keep.
   Then `python3 <kit>/scripts/new-site.py --start <wp_root>` (handoff files: a closed chat loses nothing).
4. **Get the source:** `python3 <kit>/scripts/get-source.py <source> --into <web folder>`: the copy `<name>-source`
   (clone, safe unzip, copy, or a capture of the live site; the original is never touched).
5. **Study the copy:** `python3 <kit>/scripts/analyze-source.py <name>-source --env doctor.json --json
   <wp_root>/_plan/analyze.json --site-draft <wp_root>/_plan/site.json`: stack, starter, routes, forms, tracking,
   fonts, secrets to never copy, the golden master (`references/source-types.md`). Ask only what is still open.
6. **Finish** `site.json` (`references/setup.md`), then `python3 <kit>/scripts/new-site.py <wp_root>/_plan/site.json
   --plan-only` (plan, tools, BUILD-MAP.md, private-files block). Then Sprint 0, up to its gate and the go.

## Sprint 0: Planning (no code)

- **S0-01 Study the source and set the golden master:** `_plan/SOURCE-NOTES.md`; serve the golden master unchanged
  (its own local site such as `<site>-ref.test`, or `serve.py`). Until launch the live static site can stand in;
  it changes at launch, so capture it first.
- **S0-02 Plan documents** (templates already in `_plan/`):
  - `SPRINT-PLAN.md`: the team and gates, the goal and success measures, the life cycle, the per-section
    workflow, Ready and Done, the sprint backlog.
  - `CONTENT-MODEL.md`: every route plus `/thank-you/` and the 404; Theme Settings; menus; template field groups;
    Page Sections layouts; forms; media; key naming.
  - `ARCHITECTURE.md`: stack, starter theme, parity method, folders, code and ACF rules, seeding, forms, SEO,
    security, performance, research sources with the date checked.
  - `OLD-SITE-URLS.md`: every old URL, KEEP or a 301 target (the old sitemap, REST counts, the designer's map,
    archive and theme-part URLs, campaign URLs).
- **S0-03 Board and handoff:** the stories per sprint on BUILD-MAP.md (keep its headings: the board page and
  gate.py read them); optional private board page: `python3 _plan/tools/build-map/render.py BUILD-MAP.md
  board.html`, published privately and republished to the same link after each sprint.
- **S0-04 Decisions** (the developer's; defaults in brackets): local folder, URL and database; starter theme
  (the Tailwind rule); spam protection (CF7 reCAPTCHA v3 plus the static honeypot, badge position); editor (block
  editor unless classic); pages the static site lacks, like a blog (site design, new URLs flagged to SEO); old URLs
  to redirect (Redirection only if any); git; for a multilingual source, how languages are built.

## Sprint 1: Foundation

1. **S1-01 WordPress** (tools in `_plan/tools/setup/`). Made by the local app (doctor: `wordpress: existing`):
   `get-wordpress.py <wp_root> --verify`, then `make-wp-config.py <wp_root> --existing`. Otherwise the database (ask;
   phpMyAdmin, the app's tool, or `CREATE DATABASE db_<site> CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci;`),
   then ask and `get-wordpress.py <wp_root>` (checksums, never overwrites), `make-wp-config.py <wp_root> --db
   db_<site>` (password only from `DB_PASSWORD`; local, debug log, no file editing, an `ACF_PRO_LICENSE` line). No
   address of its own (doctor: `serve: serve-wp`): `serve-wp.py <wp_root> --background`, `--no-cron`. The
   developer types the admin password in the installer. Permalinks `/%postname%/`, the business's language,
   timezone and date formats, "Discourage search engines" (local only); clean-up with the developer's OK.
2. **S1-02 Starter plugins: ACF PRO or Secure Custom Fields (free), Contact Form 7, Yoast SEO.** Ask first. ACF
   PRO comes from the developer's zip (the profile's `plugin_zips`); the developer pastes the licence. **The ACF
   menu shows** to administrators, on live too. Later, when needed: Redirection (old URLs), Duplicator (the move;
   free or Pro), Converter for Media and Contact Form CFDB7 (must be on live). The profile's `extra_plugins`:
   entries marked `required` go in here, with the starters, and stay active on live; the others when their entry
   says. Read debug.log after each install.
3. **S1-03 Theme.** Ask, then get the starter into `wp-content/themes/<theme>/`: Barebones
   (github.com/benchmarkstudios/barebones) for plain CSS, or _tw generated with the slug and prefix (`wp scaffold
   _tw <theme> --theme_name="<Site>" --prefix=<prefix>`, or underscoretw.com) for Tailwind. Then
   `python3 <kit>/scripts/new-site.py <wp_root>/_plan/site.json`: it prepares the starter (prefix renames, its
   samples and its ACF-hiding `acf.php` moved aside, PHPCS fixes) and copies the kit in. Build the assets, activate,
   `composer install`, PHPCS clean.
4. **S1-04 Golden master served, parity tools ready:** the theme's `tests/parity/` (its README has every command);
   the golden master against itself must diff 0.000%.
5. **S1-05 Design system 1:1:** the static CSS byte for byte (`KITWP_STYLESHEETS`, `KITWP_INLINE_CSS`), or for
   _tw the same Tailwind version and tokens. Swap test (`swaptest.py`): 0.000%. Nothing else styles the page.
6. **S1-06 ACF foundation:** groups and Theme Settings (options page, tabs) from
   `_plan/tools/acf/build_field_groups.py`, then `sync.php` (until nothing syncs); client-friendly fields;
   Theme Settings read by field key.
7. **S1-07 Global layout:** header, footer, mobile bar, pop-up: copied markup with React-style tight whitespace,
   behaviour in vanilla JS with the same state classes; the head as static (`head.php`, `<html lang dir>`).
   `region-check.mjs` (pixels) and `domdiff.py` per region: 0. Toolbar: `KITWP_ADMIN_BAR_CSS`.
8. **S1-08 Seeder foundation:** Tools > Seeder (local only) for media, settings and menus; run it twice: the second
   run says "same" everywhere.

## Sprints 2 to 4: templates and pages

Every section, every time: **static** (FE copies the rendered HTML, diff 0) > **model** (WP adds fields to the
builder) > **sync** > **dynamic** (fields replace the copy, every output escaped) > **seed** > **test** (visual, DOM,
text, headings, keyboard, no notices, no console errors) > **clean** (php -l, PHPCS, duplicates) > **review** by
the Lead > **hand off** (page tracker cells `ok`, handoff).

- Pages, not custom post types, so URLs stay at the root. Fixed templates where pages share a layout; one Flexible
  Content field ("Page Sections") for one-off pages. Grids list pages by template in menu order.
- Say it once: anything on two pages lives in Theme Settings, with tokens (`{phone}`, `{year}`...). An empty page
  field falls back to the default.
- next/image parity: same widths, sizes, srcset rule, width and height attributes, priority preloads.
- Raw titles, safe map iframes, SVG copied by script. Details: `references/build.md`.
- **Thank-you and 404 pages always exist.** If the source has none, design them from the site's own parts
  (header, footer, hero, buttons, type), never a new look: a plain message, the phone, a way home and to the
  main pages. Thank-you: noindex, out of the sitemap, the conversion fires there, one line per form if the
  forms differ. 404: real 404 status, text editable in Theme Settings. Both go through the same parity and QA
  checks as every page (`references/build.md` > Thank-you and 404).

## Sprint 5: Forms and email

Contact Form 7 holds each form and its email; the theme prints CF7's tags as the static markup. Forms post natively
and answer 303 to `/thank-you/`, so they work without JavaScript; one HTML email part, envelope sender and
Message-ID on the domain; local mail to the admin and `_setup/mail/`; a chat widget posts to CF7's REST endpoint
(`assets/chat-save.js`); spam: the honeypot plus reCAPTCHA v3. The visitor's auto-reply (Mail (2)) uses the same
branded HTML template as the lead email, and both carry the profile's agency badge in the footer (`branding`).
With a leads portal in the profile (`leads_portal`), every sent lead also goes there server to server (never from
local, development or staging).
Details: `references/forms-email.md`.

## Sprint 6: SEO, security, performance

Yoast seeded (head clean-up on, campaign URL and permalink clean-up off, archives off, share images), its schema
replaced by the static JSON-LD; titles, descriptions, canonicals, robots and headings as static; `/thank-you/`
noindex; old URLs as 301s (query strings kept); GTM as the task says; accessibility as static or better; hardening
(no secrets, private files 403, REST users hidden, debug off on live). Lighthouse on live only. Details:
`references/seo-security.md`.

Client wp-admin: `client-admin.php` gives the client's Editor login a short menu (Pages, Media, Theme Settings,
Contact, enquiries) and one "Your website" dashboard box; administrators keep the full admin
(`references/build.md` > The client's wp-admin). Ask at intake for the "Need help?" contact (`client_help`).

## Sprint 7: QA and launch prep

Full parity run (every route, every CSS breakpoint and 1 px past it), old URLs checked locally, real phones, the
seeder twice, `RUNBOOK.md` and `htaccess-live.txt` in `_setup/launch/` completed, a short editing guide. The
go/no-go list is in the runbook. gate.py must report every sprint DONE.

## Launch (the developer does each step; you give one at a time)

Backup of the live site (full if it is an old WordPress) > build the theme assets > a Duplicator backup
with the filters from `python3 _plan/tools/launch/duplicator-filters.py <root> <theme>` (`--starter tw` for _tw;
with Duplicator Pro and WP-CLI, `python3 _plan/tools/launch/package.py <wp_root> <theme>` builds and checks the
package in one step) >
database and PHP on the host > the old site into a sibling folder (rollback: move it back) > installer >
`installer.php` answers 404, no archive left > wp-config `production`, debug off > `.htaccess` from
`htaccess-live.txt` > wp-admin: search engines allowed, permalinks saved, reCAPTCHA keys and any ACF licence (the
developer), tracking, the live plugins (S1-02) active, debug.log read once > the client's own Editor login
(`wp user create <login> <email> --role=editor --send-email`; never share the admin account). Rollback if a
check fails. Details: `references/launch.md`.

## Live QA and the report

`live-qa.py` (one command, every live check, on the canonical host; `--hidden` before launch), `track.mjs`
(tracking), `shots.mjs` and `pdf.mjs` (the report) in `_plan/tools/report/`. Three
test leads (inline form, pop-up, chat) named `TEST <developer> - please ignore`, sent with the real submit button
after the developer agrees; the developer confirms the emails and the host's delivery log. Fill `report.html` with
verified facts only (`grep -n "\[\[" report.html` prints nothing), make one PDF, and draft the task comment and the
stakeholder message (login with `[PASTE PASSWORD HERE]`, which the developer fills; the agent never types a
password). Details: `references/qa-report.md`. Then the client pack from `_setup/handover/` (guide screenshots
taken as the client's Editor, plain English only): `references/handover.md`.

## Scripts at a glance

| Script (in the project: `_plan/tools/...`) | Does |
|---|---|
| `scripts/doctor.py` | This computer: tools, the local WordPress app, where to build (`--json`) |
| `scripts/get-source.py` | The working copy: git clone or GitHub zip, safe unzip, copy, or `capture-site.mjs` |
| `scripts/analyze-source.py` | Studies the source: stack, routes, Tailwind, forms, tracking, the golden-master method |
| `scripts/new-site.py` | `--plan-only` for Sprint 0; then prepares the starter theme and copies the kit in |
| `scripts/snapshot-routes.mjs` | Rendered HTML of every route, for client-rendered or server sources |
| `scripts/setup/get-wordpress.py`, `make-wp-config.py` | WordPress with checksums (`--verify`); wp-config (`--existing`) |
| `scripts/setup/serve-wp.py` | WordPress at its own port when the local app has no site addresses |
| `scripts/acf/build_field_groups.py`, `sync.php` | ACF JSON, stable keys (`--check`); database sync |
| `scripts/seed/export.mjs`, `export-pages.py` | Static content into `_setup/seed/` for Tools > Seeder |
| `scripts/build-map/gate.py`, `render.py` | The sprint gate; the private board page |
| `scripts/parity/` (the theme's `tests/parity/`) | Pixel, text, SEO and DOM diffs; breakpoints; mirror and server for cloud runs |
| `scripts/update.py` | Updates this skill from GitHub (`--check` only looks); `/update-convert-wordpress-skill` runs it |

## Done means

Every route 1:1 and editable; forms and emails proven on live; tracking and the conversion proven; old URLs
redirect; installer and private files not public; any ACF PRO licence active, the fields menu visible; Converter for
Media and CFDB7 live; every sprint closed through its gate; the board, handoff files and gotchas current; the
report PDF, the client pack, the task comment and the stakeholder message handed to the developer.
