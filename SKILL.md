---
name: convert-to-wordpress
description: Converts any existing website (plain HTML, Next.js, React, Astro, Vue and other stacks) into a 1:1 WordPress site with the same design, URLs, SEO and tracking, every page editable in ACF PRO and every form in Contact Form 7. Phase by phase (plan, setup in one go, pages section by section, forms and email, SEO/security/speed), QA after each phase, one fix loop until QA finds 0, then go-live, live QA and the report. Use whenever a site built outside WordPress has to be rebuilt in WordPress.
license: GPL-2.0-or-later
---

# Convert a website to WordPress, 1:1

The site already exists: as code, as a build, or live. The job is to rebuild it in WordPress so it looks and
behaves the same at every screen size, keeps every URL and SEO signal, and lets editors change everything in
wp-admin: content in ACF PRO, forms and emails in Contact Form 7. Optimized by default: SEO standard, PageSpeed
Insights aimed at a pass (a target, not a must). Any stack, any kind of
business, any country and language.

Its lessons come from real builds: a 36-page Next.js export, a PHP and Tailwind landing page, and a clinic site
taken live on cPanel.

**The yardstick for every choice:** fast, quality, best practice, low usage, straightforward: seen from the
client's side. The client is usually not technical: what they see, read, edit and receive must be simple and plain.

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
| `references/phases-and-qa.md` | At the start of every phase: the phases, QA that logs, the fix loop, the checklist, context |
| `references/wordpress-essentials.md` | The WordPress rules in one page (plugins, setup, theme, fields, forms, SEO, security, speed, launch) |
| `references/setup.md` | Intake, the database, WordPress in one go, the starter theme, the plugins |
| `references/source-types.md` | Studying the source, the golden master for each stack, Tailwind, languages |
| `references/build.md` | P1 and P2: CSS, head, ACF, media, templates, the seeder, parity checks |
| `references/forms-email.md` | P3: Contact Form 7, the email, spam protection, the chat |
| `references/seo-security.md` | P4, and the security basics from P1 |
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
4. **Two gates, then straight through.** The developer's **Plan OK** covers every download and install the plan
   lists (WordPress, the theme, ACF PRO from their zip, Contact Form 7, Yoast SEO), so setup runs in one go. Ask
   first only for what the plan did not list, a delete outside a fresh install, and every live step (one at a time);
   the **Go-live** is the second gate. Decide what has a sensible default and list it in the stop report.
5. **Never type a password, licence key or API key**, with one exception: the developer's default local admin
   password, which `install-wp.py` reads from `profile.local.json` (`local_admin`) for a local site only and never
   prints. Live admins get their own strong password, typed by the developer; reports say `[PASTE PASSWORD HERE]`.
   ACF PRO's key: the developer puts it once in `profile.local.json` (`acf_pro_license`), and make-wp-config.py
   writes it into each local wp-config (never printed), or pastes it into wp-config (`ACF_PRO_LICENSE`). Not on live
   unless the developer chooses.
6. **One phase at a time; QA only logs.** After each phase QA writes its findings in one list on the board; nothing
   is fixed before the fix loop except a blocker (the site breaks, or the next phase cannot start). `gate.py`
   opens the next phase.
7. **Manual steps** for the developer (wp-admin, the host panel, Duplicator): one at a time, then wait for "done".
8. **Handoff files** (`handoff.md`, `ai-handoff-summary.md` at the project root): update both after every
   significant change and before stopping. A new session reads the summary first.
9. **Private:** BUILD-MAP.md and its board page, `_plan/`, `_setup/`, the handoff files. Anything for the client or
   a stakeholder: plain language, verified facts only, no phase or step numbers, files as PDF.
10. **Read only:** the source folder and the golden master. Build or `npm install` only in a copy.
11. **Code:** every global prefixed (`<prefix>_`); PHP 8.1 to 8.4; escape at output, sanitise input, nonces and
    capability checks. After every PHP save: `php -l`, PHPCS and the duplicate function check. What the build writes
    itself uses tokens, never one-off values; only what the site uses ships; a section past about 15 fields or 250
    lines is split; JS is enqueued, never inline; comments say why, never a task or ticket ID. Every phase gate:
    PHPCS with the kit's escaping helpers registered (no blanket ignores), `npm run lint` (ESLint and Prettier)
    and the read-only code review (`references/build.md` > Code quality).
12. **Live:** surgical changes only, a rollback copy of every replaced file, PHP files complete before upload,
    theme zips with 0644 files and 0755 folders.
13. **Replies** follow the profile's `level`: `new` = plain words, each term explained once
    (`references/glossary.md`), exact clicks, the `Next:` line (rule 15) in plain words at the end; `developer` =
    short (asked at intake).
14. **Spend less:** read the summary, not whole files; never read node_modules, minified, vendor or lock files;
    scripts copy markup and print summaries (detail stays in files); screenshots only as cropped failures. Context:
    from 50% finish the section or page, checkpoint (board, handoff files) and continue in a new chat; cap 75%.
15. **Never stop silently.** Every turn that ends without the work going on (a phase closed, a part done, a
    checkpoint or new chat, a pause, a block, waiting for a go or a manual step) ends with a short stop report, never
    a bare status: what was done, the state, every decision taken on your own (with the default chosen), and last
    `Next: <step> — waiting on <who>`. Send it to whoever started the work: a parent session (for example a Command
    Center) as well as your own chat; with no parent, the developer, with the recommended step first ("Proceed:
    <step>"). Every role and subagent reports upward this way; nobody waits unreported.

## The phases

One agent builds the whole site. No role-play team in the chat: the old roles are the QA checklist
(`references/phases-and-qa.md`).

| Phase | What | Ends with |
|---|---|---|
| P0 Plan | Intake, study the source, plan documents, the board | The developer's **Plan OK** |
| P1 Setup | WordPress, plugins and theme in one go; golden master; 1:1 CSS; ACF; header and footer; seeder | QA logs |
| P2 Pages | Every page, section by section | QA logs |
| P3 Forms and email | CF7 forms, branded emails, thank-you, spam protection | QA logs |
| P4 SEO, security, speed | SEO plugin, schema, old URLs, ARIA, hardening, Core Web Vitals | QA logs |
| P5 Fix and QA loop | One full QA run; fix passes, each re-checking what changed, until a re-check finds 0; launch prep | The developer's **Go-live** |
| P6 Launch and live QA | Live, live QA, the report and the client pack | Done |

**QA per phase** = the self-check first (`self-check.py`: the build fixes what it finds before QA starts) + gate.py
+ the parity, SEO and design checks + one fresh read-only check against the QA checklist (a subagent, or a new chat
in tools without subagents; a faster model where the tool lets you pick). Findings go in BUILD-MAP.md "QA findings"
(`open` > `fixed` after a re-check, or `decided`).
**All rules at the plan:** P0 decides the forms and where leads go, placeholders, the live plugin checklist and the
leads portal; a skill update during a task applies at the next site or phase boundary, never inside a QA run.

```
python3 _plan/tools/build-map/gate.py BUILD-MAP.md           # 0 may close, 1 open items listed, 2 a rule broken
python3 _plan/tools/build-map/gate.py BUILD-MAP.md --close   # opens the next phase
python3 _plan/tools/build-map/render.py BUILD-MAP.md _plan/progress.html   # progress page + progress.json
python3 _plan/tools/report/self-check.py <wp_root> --url <local url>      # before every QA run
```

Run gate.py at the start of every session. Write `ok <date>` in "Developer gates" only after the developer says it
in the chat. After `--close`: update both handoff files. The progress page: update the board's "## Now" lines,
render and push at every unit end (a page built, a QA run collected, a fix batch, a site done) and every stop;
before a long step (a QA run, a full pixel run) write Now and push first. In Claude the page is live (the artifact
database: render.py writes the rows, ArtifactData sends them, the open page updates itself); elsewhere republish
the static page (references/phases-and-qa.md > The progress page). Resume short: checkpoint at a page, site or
phase end with the exact next step; a resume re-checks only what can have changed.

## Start: intake

1. **An existing project?** Read `ai-handoff-summary.md`, run gate.py, continue from the Next action.
2. **This computer:** `python3 <kit>/scripts/doctor.py --name <site> --json doctor.json` (`python3` = the command it
   prints, often `py -3` on Windows; no Python at all: `references/agents.md`). It finds the tools and the local
   WordPress app and suggests the folder, address and database. No shell (a chat app): say so, offer the plan from
   uploaded files. Exit 3: help install what it names, then run it again.
3. **Ask once**, in one batch (a question tool, else a short numbered list), the suggestion first, in plain words
   for `level: new`, and only what the task, the profile and doctor.py do not answer: where to build; the site
   (GitHub link, zip, folder or only its address) if not given with `/convert-to-wordpress <source>`; built
   websites before?; live domain and host; lead email recipients; country, languages, right-to-left; the task's
   scope; old URLs to keep. ACF PRO is the default (Secure Custom Fields only if the developer asks for it).
4. **Start:** `python3 <kit>/scripts/start.py <source> --root <wp_root> --name "<Site>" --env doctor.json`: the
   folder and two handoff files (a closed chat loses nothing), the working copy `<name>-source` next to it (clone,
   safe unzip, copy, or a capture of the live site; the original is never touched), and the study of the copy:
   stack, starter, routes, forms, tracking, fonts, secrets to never copy, the golden master
   (`references/source-types.md`). One line per step; the full study in `_plan/analyze.txt`. Ask only what is
   still open.
5. **Finish** `_plan/site.json` (start.py drafted it; `references/setup.md`), then `python3 <kit>/scripts/new-site.py
   <wp_root>/_plan/site.json --plan-only` (plan, tools, BUILD-MAP.md, private-files block). Then P0, up to the
   Plan OK. Three commands in all: doctor.py, start.py, new-site.py.

## P0 Plan (no code)

- **P0-01 Study the source and set the golden master:** `_plan/PLAN.md` > The source (start.py filled its table);
  serve the golden master unchanged (its own local site such as `<site>-ref.test`, or `serve.py`). Until launch the
  live static site can stand in; it changes at launch, so capture it first.
- **P0-02 Plan documents** (templates already in `_plan/`), short:
  - `PLAN.md`: the goal and success measures, the source, how it is built (stack, 1:1 method, checks, the states
    to check: menu, tabs, sliders...), the phases for this site, the per-section workflow, Done. One page to read
    for the Plan OK.
  - `CONTENT-MODEL.md`: every route plus `/thank-you/` and the 404; Theme Settings; menus; template field groups;
    Page Sections layouts; forms; media; key naming.
  - `OLD-SITE-URLS.md`: every old URL, KEEP or a 301 target (the old sitemap, REST counts, the designer's map,
    archive and theme-part URLs, campaign URLs).
- **P0-03 Board and handoff:** every page and its sections in BUILD-MAP.md "Pages" (keep its headings: render.py
  and gate.py read them); the private progress page (the same page and progress.json keys as figma-to-wordpress): `python3
  _plan/tools/build-map/render.py BUILD-MAP.md _plan/progress.html`; in Claude the live page
  (`_plan/progress-live.html`, published once with the database) gets rows at every step start and stop, elsewhere
  the static page is republished (references/phases-and-qa.md > The progress page).
- **P0-04 Decisions and the Plan OK** (defaults in brackets; the developer may just say OK): local folder, URL and
  database; starter theme (_tw for a Tailwind source or a site clearly easier in Tailwind, else Barebones with
  CSS-variable tokens; the choice and one reason); spam protection (CF7 reCAPTCHA v3 plus the static honeypot, badge
  position); editor (block editor unless classic); pages the static site lacks, like a blog (site design, new URLs
  flagged to SEO); old URLs to redirect (Redirection only if any); git; for a multilingual source, how languages are
  built; every form and where its leads go (CF7 for each, the leads portal or "none: <reason>"), missing content as
  marked placeholders, a chat or search if the source has one, the live plugin checklist. All of it now, so no rule
  reopens finished work later. The OK message lists the downloads of P1 (WordPress, theme, ACF PRO zip, Contact Form
  7, Yoast SEO).

## P1 Setup (in one go, after the Plan OK)

1. **P1-01 WordPress, admin, settings, plugins:** one command, `python3 _plan/tools/setup/setup.py
   <wp_root>/_plan/site.json --profile <kit>/profile.local.json`. From site.json and doctor.json it creates the local
   database if missing (never drops one), gets WordPress with checksums (or verifies the one a local app made), writes
   wp-config (local, debug log, no file editing, an `ACF_PRO_LICENSE` line), starts `serve-wp.py` when the local app
   has no site addresses, then `install-wp.py`: the default local admin from the profile (`local_admin`, e.g.
   `agency-dev`; local sites only), permalinks `/%postname%/`, "Discourage search engines", the fresh-install samples
   removed, Contact Form 7 and Yoast SEO (checksums) and ACF PRO from the profile's zip, all active. `--dry-run`
   shows the steps first. Exit 1 lists open items (no ACF PRO zip or local password yet: the developer adds them to
   the profile, then run it again). ACF PRO activates itself when the profile has `acf_pro_license`; otherwise the
   developer pastes the licence. The business's language and date
   formats in Settings. Profile `extra_plugins` marked `required` go in here too. **The ACF menu shows** to
   administrators, on live too. Converter for Media and Contact Form CFDB7 are not installed locally: they go on
   live at launch. The separate scripts (`references/setup.md`) stay for a step that needs repeating.
2. **P1-02 Theme.** Get the starter into `wp-content/themes/<theme>/`: Barebones
   (github.com/benchmarkstudios/barebones) for plain CSS, or _tw generated with the slug and prefix (`wp scaffold
   _tw <theme> --theme_name="<Site>" --prefix=<prefix>`, or underscoretw.com) for Tailwind. Then
   `python3 <kit>/scripts/new-site.py <wp_root>/_plan/site.json`: it prepares the starter (prefix renames, its
   samples and its ACF-hiding `acf.php` moved aside, PHPCS fixes) and copies the kit in. Build the assets, activate,
   `composer install`, PHPCS clean.
3. **P1-03 Golden master served, parity tools ready:** the theme's `tests/parity/` (its README has every command);
   the golden master against itself must diff 0.000%.
4. **P1-04 Design system 1:1:** the static CSS byte for byte (`KITWP_STYLESHEETS`, `KITWP_INLINE_CSS`), or for
   _tw the same Tailwind version and tokens. Swap test (`swaptest.py`): 0.000%. Nothing else styles the page.
   CSS the build writes itself on _tw: utilities on the `@theme` tokens, custom CSS only for CF7 and what
   utilities cannot express, no `text-wrap: balance` on headings, letter-spacing end padding
   (`references/source-types.md` > Writing CSS on _tw).
5. **P1-05 ACF foundation and seeder:** groups and Theme Settings (options page, tabs) from
   `_plan/tools/acf/build_field_groups.py`, then `sync.php` (until nothing syncs); client-friendly fields; Theme
   Settings read by field key. Tools > Seeder (local only) for media, settings and menus; run it twice: the second
   run says "same" everywhere.
6. **P1-06 Global layout:** header, footer, mobile bar, pop-up: copied markup with React-style tight whitespace,
   behaviour in vanilla JS with the same state classes; the head as static (`head.php`, `<html lang dir>`).
   `region-check.mjs` (pixels) and `domdiff.py` per region: 0. Toolbar: `KITWP_ADMIN_BAR_CSS`.
7. **P1-07 QA run:** findings logged (`references/phases-and-qa.md`), then `gate.py --close`.

## P2 Pages (section by section)

Every section, every time: **static** (copy the rendered HTML, diff 0) > **model** (fields in the builder) >
**sync** > **dynamic** (fields replace the copy, every output escaped) > **seed** > **check and clean** in one call:
`python3 tests/parity/check-section.py <route> --section <selector>` (pixel and text at the quick widths, DOM, php
-l, PHPCS, duplicates; one line back, OK before moving on), plus one H1 and heading order, aria-labels, alt, schema,
the CWV items, no notices, no console errors > the section's board row `built`. Then the phase's QA run marks them
`checked`.

**Design checks** (numbers first, images only for failures; `references/build.md` > Design checks):
`design-check.mjs --states` (hover, focus and the clicks PLAN.md lists: open menu, tabs, sliders, against the source
in the same state), `--motion` (transition and animation duration, delay, easing against the source) and `--long`
(the page from `long-content.php make <route>` with every field long: no overflow, no clipped text from 320 to
1920). States and motion at the end of each page; all three in each QA run from P2 on. The pass marks are in
`design-check.config.json` (defaults until the first real build sets the final ones).

- Pages, not custom post types, so URLs stay at the root. Fixed templates where pages share a layout; one Flexible
  Content field ("Page Sections") for one-off pages. Grids list pages by template in menu order.
- Say it once: anything on two pages lives in Theme Settings, with tokens (`{phone}`, `{year}`...). An empty page
  field falls back to the default.
- next/image parity: same widths, sizes, srcset rule, width and height attributes, priority preloads.
- Media and maps: logos (the agency badge and its link too), the Site Icon, email images and every content image
  are seeded into the Media Library and set in ACF or Theme Settings, never hard-coded; maps are live Google
  iframes from one field that takes a Maps link, embed code or address (the default city until the address is
  confirmed).
- **Missing content is a seeded placeholder** (by default): an image or field the source leaves empty, or a file
  that is missing, gets a clearly marked placeholder in its ACF field (an image of the same size and ratio titled
  `PLACEHOLDER`, or `[PLACEHOLDER: what goes here]` text), never hard-coded in a template, so every page renders 1:1
  and stays editable. Each one (page, field) is on the board and in the report as a client to-do
  (`references/build.md` > The seeder).
- Raw titles, SVG copied by script. Details: `references/build.md`.
- **Thank-you and 404 pages always exist.** If the source has none, design them from the site's own parts
  (header, footer, hero, buttons, type), never a new look: a plain message, the phone, a way home and to the
  main pages. Thank-you: noindex, out of the sitemap, the conversion fires there, one line per form if the
  forms differ. 404: real 404 status, text editable in Theme Settings. Both go through the same checks as every
  page (`references/build.md` > Thank-you and 404).

## P3 Forms and email

Contact Form 7 holds each form and its email; the theme prints CF7's tags as the static markup. Forms post natively
and answer 303 to `/thank-you/`, so they work without JavaScript; one HTML email part, envelope sender and
Message-ID on the domain; local mail to the admin and `_setup/mail/`; a chat widget posts to CF7's REST endpoint
(`assets/chat-save.js`); spam: the honeypot plus reCAPTCHA v3. CF7's autop is off on every form (no stray `<p>`
or `<br>`). Every notification and every auto-reply (Mail (2)) uses the branded HTML template, never CF7's plain
text; both carry the profile's agency badge in the footer (`branding`); the email logo and badge come from Theme
Settings.
Every lead also goes to the profile's leads portal (`leads_portal`), server to server, whether the email went out
or failed: mandatory on live for a site with a lead form (no portal in the profile is a go-live blocker; a site
without forms says so in site.json). The keys go only into the live wp-config; never from local, development or
staging.
Details: `references/forms-email.md`.

## P4 SEO, security, speed

SEO standard by default: Yoast seeded (head clean-up on, campaign URL and permalink clean-up off, archives off,
share images), its schema replaced by the static JSON-LD; titles, descriptions, canonicals, robots and headings as
static; `/thank-you/` noindex; old URLs as 301s (query strings kept); GTM as the task says; accessibility as static
or better; hardening (no secrets, private files 403, REST users hidden, debug off on live). Core Web Vitals are
built in from the first section (LCP preload and fetchpriority, sized srcset, nothing lazy above the fold, reserved
media space, metric-matched fallback font, minimal deferred JS). PageSpeed Insights on live is aimed at a pass, not
a must. The live cache plugin is LiteSpeed Cache by default (the profile's `cache_plugin` names another; live
only); a heavy design that misses a pass gets its further options, one at a time; the design is never changed for a
score. Local Lighthouse is a regression guard only. Details: `references/seo-security.md`.

Client wp-admin: `client-admin.php` gives the client's Editor login a short menu (Pages, Media, Theme Settings,
Contact, enquiries) and one "Your website" dashboard box; administrators keep the full admin
(`references/build.md` > The client's wp-admin). Ask at intake for the "Need help?" contact (`client_help`).

## P5 Fix and QA loop

One **full** QA run on the whole site (every route, every CSS breakpoint and 1 px past it, the design checks, old
URLs checked locally, real phones, the seeder twice, the read-only review of all the theme code; the long-content
test pages removed before the package), then `changed-routes.py save`. Then fix passes: fix every open finding,
re-check each fixed item, a read-only review of the changed files and their callers, pixel only on the routes
`changed-routes.py diff` names; repeat until a re-check finds 0 and no finding is `open`. A new full run only when a
change touched most of the theme. Clones of a proven template: every route's markup and content, the forms, pixel at
360, 768 and 1440 (references/phases-and-qa.md > The fix loop, Clones). Then launch prep: the clean-up (unused kit
files and helpers out of the theme, the one-off value search at 0), `RUNBOOK.md` and `htaccess-live.txt` in
`_setup/launch/` completed, a short editing guide. Then the stop report asking for the **Go-live** (the go/no-go
list is in the runbook).

## P6 Launch (the developer does each step; you give one at a time)

Backup of the live site (full if it is an old WordPress) > build the theme assets > a Duplicator backup
with the filters from `python3 _plan/tools/launch/duplicator-filters.py <root> <theme>` (`--starter tw` for _tw;
with Duplicator Pro and WP-CLI, `python3 _plan/tools/launch/package.py <wp_root> <theme>` builds and checks the
package in one step) >
database and PHP on the host > the old site into a sibling folder (rollback: move it back) > installer >
`installer.php` answers 404, no archive left > wp-config `production`, debug off > `.htaccess` from
`htaccess-live.txt` > wp-admin: search engines allowed, permalinks saved, reCAPTCHA keys and any ACF licence (the
developer), tracking, **the live plugin checklist** (RUNBOOK section 4: the profile's live plugins from the
developer's plugin folder, CFDB7, Converter for Media, the reCAPTCHA keys, the cache plugin; staging gets none
of it), debug.log read
once > the client's own Editor login (`wp user create <login> <email> --role=editor
--send-email`; never share the admin account). The live admin keeps its own strong password, typed by the
developer. Rollback if a check fails. Details: `references/launch.md`.

## P6 Live QA and the report

`live-qa.py` (one command, every live check, on the canonical host; `--hidden` before launch), `track.mjs`
(tracking), `shots.mjs` and `pdf.mjs` (the report) in `_plan/tools/report/`. PageSpeed Insights on live (mobile and
desktop), reported honestly. Three test leads (inline form, pop-up, chat) named `TEST <developer> - please ignore`,
sent with the real submit button after the developer agrees; the developer confirms the emails and the host's
delivery log. Fill `report.html` with verified facts only (`grep -n "\[\[" report.html` prints nothing), make one
PDF, and draft the task comment and the stakeholder message (login with `[PASTE PASSWORD HERE]`, which the
developer fills; the agent never types a password). Details: `references/qa-report.md`. Then the client pack from
`_setup/handover/` (guide screenshots taken as the client's Editor, plain English only): `references/handover.md`.

## Scripts at a glance

| Script (in the project: `_plan/tools/...`) | Does |
|---|---|
| `scripts/doctor.py` | This computer: tools, the local WordPress app, where to build (`--json`) |
| `scripts/start.py` | The intake in one call: new-site.py --start, get-source.py (the copy) and analyze-source.py (the study) |
| `scripts/get-source.py`, `analyze-source.py` | The working copy (clone, zip, folder or a capture); the study of it |
| `scripts/new-site.py` | `--plan-only` for P0; then prepares the starter theme and copies the kit in |
| `scripts/snapshot-routes.mjs` | Rendered HTML of every route, for client-rendered or server sources |
| `scripts/setup/setup.py` | P1-01 in one call: database, get-wordpress, make-wp-config, serve-wp (if needed), install-wp |
| `scripts/setup/install-wp.py` and the others | Install, admin, settings, plugins; the steps one by one when one needs repeating |
| `scripts/report/leads-check.py` | The leads portal endpoint and key with a GET (stores nothing; the key never printed) |
| `scripts/launch/plugin-versions.py` | Go/no-go: each plugin zip in the profile's folder with its version and file date |
| `scripts/acf/build_field_groups.py`, `sync.php` | ACF JSON, stable keys (`--check`); database sync |
| `scripts/seed/export.mjs`, `export-pages.py` | Static content into `_setup/seed/` for Tools > Seeder |
| `scripts/build-map/gate.py`, `render.py`, `live.py` | The phase gate; the private progress page, static and live (the database rows) |
| `scripts/report/self-check.py` | Before every QA run: the classes a build catches itself (instructions, casts, guards, dead code, launch files) |
| `scripts/parity/` (the theme's `tests/parity/`) | `check-section.py` (one call per section), pixel, text, SEO and DOM diffs, `seodiff.py` (head tags and JSON-LD values), `changed-routes.py` (what a fix pass changed), `design-check.mjs` (states, motion, long content), `long-content.php`; mirror and server for cloud runs |
| `scripts/update.py` | Updates this skill from GitHub (`--check` only looks); `/update-convert-wordpress-skill` runs it |

## Done means

Every route 1:1 and editable; forms and emails proven on live; tracking and the conversion proven; old URLs
redirect; installer and private files not public; any ACF PRO licence active, the fields menu visible; every item of the live
plugin checklist ticked (RUNBOOK section 4); QA found 0 before go-live; every phase closed through gate.py; the board, handoff files and gotchas current; the
report PDF, the client pack, the task comment and the stakeholder message handed to the developer.
