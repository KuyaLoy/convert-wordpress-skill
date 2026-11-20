# Changelog

Every change to the skill, newest first. Versions follow [Semantic Versioning](https://semver.org); the format
follows [Keep a Changelog](https://keepachangelog.com).

## [Unreleased]

## [0.9.8] - 2026-11-20

The chat's state shows in its title, so the sidebar shows what is working.

### Added

- **State in the title** (Claude desktop app; other tools skip it): `▶ RUNNING | <title>`, `⏸ WAITING on <who> |
  <title>`, `✋ BLOCKED | <title>`, `✓ DONE | <title>`, set with `set_session_title` "self", one call per state
  change, next to the RUNNING line (SKILL.md, references/phases-and-qa.md > The progress page).

## [0.9.7] - 2026-11-20

A chat that ends its turn while its own work runs says so, so it never looks stopped.

### Added

- **Running, not stopped:** while a background command, a subagent or a check runs past the end of a turn, the
  last message's first line, the recap and the progress page's Now line read `RUNNING, not stopped: <what>, started
  HH:MM; I continue by myself when it finishes.`; a real stop says what it waits on instead (SKILL.md,
  references/phases-and-qa.md > The progress page).

## [0.9.6] - 2026-11-20

A real build's retro: faster, with the same checks. The kit now writes right the first time what QA kept finding,
QA converges (one full run, then re-checks of what changed), every rule is decided at the plan, and the progress
page is live.

### Added

- **Pre-QA self-check** (`scripts/report/self-check.py`), before every QA run: ACF instructions missing or in
  developer words, `(array)` on a field read, the ABSPATH guard, `phpcs:ignore` without a reason, functions never
  called, missing file paths, files over 300 lines, starter leftovers, unfilled or wrong launch files, acf-json and
  the oEmbed author public. QA finds fewer; it does not check less.
- **`seodiff.py`** (theme `tests/parity/`): head tags (title, description, robots, canonical, og, twitter,
  theme-color, viewport, icons, their order) and every JSON-LD value per route, with the HTTP status, read with
  html.parser; no browser. parity.mjs compared JSON-LD types only.
- **`changed-routes.py`**: `save` after the full QA run, `diff` after a fix pass: the routes whose rendering
  changed, the only ones pixel re-runs.
- **The live progress page** (`scripts/build-map/live.py`): render.py also writes `progress-live.html` (published
  once with the artifact database; it shows its embedded snapshot when the database cannot be reached) and
  `progress-rows.json` (ArtifactData batch writes since the last push; `--pushed` records them). The open page
  updates itself. Collections: `meta/now`, `phases`, `items`, `findings`, `log`.
- site.json: `www`, `forms`, `chat`, `blog`, `redirects`, `palette`, `content_size`; `new-site.py --launch-files`
  writes the launch files again; `<!-- if:NAME -->` / `<!-- unless:NAME -->` blocks in the launch templates.
- Theme: `KITWP_KEEP_BLOG`, `KITWP_SITE_SEARCH` (archives, paged lists, feeds, attachment pages and search answer
  404 unless the site has them), `KITWP_NOJS_LEADS` (off: reCAPTCHA stays strict), `kitwp_list()` for relationship
  and gallery fields, `assets/recaptcha.js`.

### Changed

- **QA that converges** (references/phases-and-qa.md): one full run per site (and per template site before its
  clones); then fix passes that re-check each fixed item, review the changed files and their callers in full and
  re-run pixel only on changed routes; blockers and majors fixed at once; a new minor outside the changed code goes
  to the next pass with no new full run; a new full run only when a change touched most of the theme. Clones of a
  proven template: every route's markup and content, the forms, pixel at 360, 768 and 1440.
- **All rules at the plan:** P0 decides the forms and where leads go, placeholders, the live plugin checklist and
  the leads portal; a skill update during a task applies at the next site or phase boundary.
- **Shorter resumes:** checkpoint at a page, site or phase end with the exact next step; a resume re-checks only
  what can have changed.
- The launch files per site: htaccess-live.txt's host rule built from the bare domain (www or not), readme.html,
  license.txt, wp-config-sample.php, xmlrpc.php, acf-json and the theme's dev files denied, three security
  headers; the RUNBOOK names only the site's forms, where live leads go, the client to-dos, local addresses
  replaced, the tracking ID, Redirection only with old URLs.
- Setup moves unused starter and kit files to `_setup/starter-removed/` (chat files without a chat, the blog
  templates without a blog, readme stubs, the starter palette, the widget area, starter supports); style.css
  Requires PHP 8.1.
- build_field_groups.py refuses a field without instructions or with developer words; the kit's own texts fixed.
- install-wp.py (fresh install): CF7's sample form and WordPress's draft privacy page removed; the seeder points
  the privacy setting at the site's page.
- The theme kit split by job: forms.php into forms, forms-controls, forms-spam, forms-mail, forms-local-mail,
  forms-portal; seed.php into seed, seed-media, seed-settings, seed-menus, seed-forms, seed-seo; helpers-maps.php
  and media-svg.php out of helpers.php and media.php. No behaviour change.
- gate.py: an escaped pipe (`\|`) stays in its cell; a findings row split by a `|` is named plainly; a NOTE when
  the board's Now line is not the current phase.

### Fixed

- A failed form post showed nothing (CF7's response box was dropped): it shows CF7's message as `role="alert"` with
  the site's phone.
- The leads portal trusted forwarded IP headers and forwarded every posted key: a valid public IP only, the form's
  own fields only, capped.
- The honeypot read `company[]` as a string (a notice); the email logo fallback pointed at a file the kit lacks;
  the SVG cleaner let `onload`, `<set to="javascript:">` and iframes through; the map host check accepted
  `google.evil.example`; oEmbed showed the author; no ABSPATH guard (a direct request printed the server path);
  the reCAPTCHA token code was an inline script; theme assets kept a fixed `?ver`; `/favicon.ico` fell to
  WordPress's logo; a blank line in `<head>`; long-content.php left an empty option behind.
- Every `phpcs:ignore` in the kit names its reason.

## [0.9.5] - 2026-11-20

The progress page says what the chat is doing now and stays current.

### Added

- **Now and Next at the top** of the progress page, in large type: the board's "## Now" Doing line with the time it
  started (`(started 14:05)`), Next, anything waiting on the developer or blocked, and the time the page was
  rendered ("n min ago" while the page is open; one tiny inline script). The board template gets a Next line.
- **Every QA finding with its status:** counts per status (open, fixed, decided) and per QA run (the finding's Phase
  column: `P2`, `P5 run 2`), open first, fixed and decided folded under them.
- progress.json, additions only: `now` (`step`, `started`), `next`, `waiting`, `blocked`; `updated` is the render
  time (date and time). Boards made before 0.9.5 still render (Next comes from the header line).

### Changed

- **Republish at every unit end, not only at phase ends:** each page built, each QA run collected, each fix batch,
  each site done, and every stop (checkpoint, waiting, paused); before a long step (a QA run, a full pixel run) the
  Now line is written and the page republished first. P5 alone ran for hours with a page hours old.

## [0.9.4] - 2026-11-20

The leads portal is mandatory on live and catches every lead, even when the email fails.

### Fixed

- `kitwp_leads_send()` ran on `wpcf7_mail_sent` only, so when the host's mail failed the lead never reached the
  portal either: it now runs on `wpcf7_mail_failed` too (CF7 fires one of them; spam neither), once per submission.
  A PHP test proves a failed mail still posts the lead and staging never does.

### Added

- **Mandatory portal:** every live site with a lead form sends to the profile's leads portal. No
  `leads_portal.constant_prefix` in the profile is a go-live blocker (new-site.py says so and the RUNBOOK shows it);
  a site without a lead form says so in site.json: `"leads_portal": "none: <reason>"`. The code is in from P3; the
  endpoint and key go only into the live wp-config, pasted by the developer.
- **The live plugin checklist** gets the leads portal item (the project for the live domain, the keys in the live
  wp-config, the GET check, one TEST lead per form in the portal's counts); the go/no-go list checks the project and
  the key.
- **`scripts/report/leads-check.py`:** proves the endpoint and key with a GET, which stores nothing; the key comes from
  `KITWP_LEADS_KEY` or a hidden prompt and is never printed; 401 and 404 named plainly. It never POSTs.
- A WordPress site the kit did not build: the same sender as a small must-use plugin made from the kit's functions.

## [0.9.3] - 2026-11-20

### Added

- **One live plugin checklist** (RUNBOOK section 4; launch.md, SKILL.md P6 and Done means point to it): the profile's
  own live plugins (an `extra_plugins` entry with `"live": true`, its zip named in `"zip"`, a one-line `"live_note"`;
  new-site.py writes them into the project's RUNBOOK), Contact Form CFDB7, Converter for Media (then the images
  regenerated), the reCAPTCHA v3 keys and the cache plugin. Profile plugins come only from the developer's plugin
  folder (`plugin_zips`).
- **LiteSpeed Cache is the default live cache plugin** (the profile's or site.json's `cache_plugin` names another):
  page and browser cache on, CSS/JS options one at a time with a parity check; not on staging or locally. Replaces
  "no speed plugin by default".
- **`scripts/launch/plugin-versions.py`:** each zip in `plugin_zips` with its plugin name, Version header and file
  date, in the go/no-go list; the developer confirms each is the newest or replaces it (never the agent).
- **live-qa.py reCAPTCHA check:** every checked page with a Contact Form 7 form loads the reCAPTCHA script; with
  `--hidden` (staging) none does.

### Changed

- **Staging** (a public copy before live) gets none of the live plugin checklist and no reCAPTCHA keys, and stays
  noindex (`--hidden`): one line in launch.md, the RUNBOOK and qa-report.md.
- Local stays as before: `required` extra plugins in P1 setup; the others only when the plan lists them.

## [0.9.2] - 2026-11-20

### Added

- **ACF PRO pre-activated from the profile:** an optional `acf_pro_license` in `profile.local.json` (typed by the
  developer). With it, make-wp-config.py (`--profile`; setup.py passes it) writes `define( 'ACF_PRO_LICENSE', ... );`
  active in LOCAL wp-config files only (`--env local`), so ACF PRO activates itself on that URL; the value is never
  printed. Empty: today's commented line. setup.py adds the key to a kit block that only has the commented line.
  Clones: `make-wp-config.py <copy> --existing --profile ...` on each copy. Live: not written by default; the launch
  steps remove the line from the copied wp-config unless the developer chooses to keep it.

- **Missing content is a seeded placeholder** (the default): an image or field the source leaves empty, or a missing
  file, gets a clearly marked placeholder in its ACF field (an image of the same size and ratio titled
  `PLACEHOLDER: <page> <field>`, or `[PLACEHOLDER: ...]` text), never hard-coded in a template, so every page
  renders 1:1 and stays editable. Each one is a `decided` finding on the board and a client to-do in the report's
  next steps (SKILL.md P2, `references/build.md` > The seeder, the QA checklist, `report.html`).

### Fixed

- `make-wp-config.py --existing` run again dropped a key the developer had pasted into the kit block: it is kept now
  (a key written from the profile is refreshed from the profile instead).

## [0.9.1] - 2026-11-19

The starter rule's middle case, and the code-quality lessons from a read-only audit of a large Figma build (no
bugs, but thousands of one-off values, copied maps, oversized sections, ticket tags in comments, unused kit files,
PHPCS passing through ignore comments, code review only early).

### Changed

- **Starter theme:** the source is Tailwind: _tw; not Tailwind but clearly easier in Tailwind (repeating tokens, many
  reusable sections): _tw, with the static CSS still loaded verbatim and Tailwind only for what the build writes; a
  normal site: Barebones with CSS-variable tokens (`assets/css/tokens.css`). PLAN.md names the choice and one reason.
- **Code quality** (`references/build.md` > Code quality, SKILL.md rule 11, the QA checklist, the theme's AGENTS.md):
  what the build writes itself uses tokens, never one-off values (a grep before each gate); only used kit files and
  helpers ship (P5 clean-up); comments say why, never a task, ticket or design-tool ID; a section past about 15
  fields or 250 lines is split; one job per file; JS enqueued, never inline. Copied markup and CSS stay 1:1.
  The five rules (Tokens not one-offs, Ship only what is used, Comments say why, Size limits, Gates) and the
  self-check greps carry the same names and order as in figma-to-wordpress.
- **Gates at every phase:** PHPCS with the kit's helpers registered in `phpcs.xml.dist` (`customEscapingFunctions`:
  `kitwp_inline`, `kitwp_svg_clean`; `customAutoEscapedFunctions`: `kitwp_img`, `kitwp_html`, `kitwp_icon`,
  `kitwp_inline_svg`, `kitwp_map_iframe`...), so their output needs no ignore comment; `npm run lint` (ESLint and
  Prettier); the read-only code review at every phase gate.
- **Barebones lint:** new-site.py adds `lint` and `lint-fix` scripts, ESLint 10 and Prettier 3, and three small
  configs (`assets/lint/`); `.prettierignore` leaves every `.css` out except the token file, so copied static CSS
  keeps its bytes.

### Fixed

- Barebones' sample `assets/scripts/scripts.js` used jQuery, which the kit removes from the front end, so it threw on
  every page: new-site.py moves it aside and leaves an empty entry for the static site's vanilla JS.
- Barebones' `vite.config.js` scans `blocks/`, which new-site.py moves aside, so `npm run build` failed: the folder
  stays (with `.gitkeep`).

## [0.9.0] - 2026-11-18

Fewer commands and files, the same checks; design checks beyond the still page; any agent that reads skills.

### Added

- **`scripts/start.py`:** the intake in one call after doctor.py: `new-site.py --start`, `get-source.py` (the
  working copy) and `analyze-source.py` (the study, full output in `_plan/analyze.txt`), one line per step; doctor.json
  copied to `_plan/`. Intake = doctor.py > start.py > new-site.py --plan-only (three commands, was five).
- **`scripts/setup/setup.py`:** P1-01 in one call after the Plan OK, from site.json and doctor.json: the local
  database (`CREATE DATABASE IF NOT EXISTS`, local host only, never drops), get-wordpress.py (or `--verify`),
  make-wp-config.py (`--db` or `--existing`, `--no-cron` for serve-wp), serve-wp.py when needed, install-wp.py.
  Stops at the first failure; install-wp's open items pass through (exit 1). `--dry-run` lists the steps.
- **`check-section.py`** (the theme's `tests/parity/`): one check per section in one call: pixel and text
  (region-check.mjs on the section, or parity.mjs on the route), DOM (domdiff.py), php -l, PHPCS and the duplicate
  function check; one line back, failures only, the rest in `report/check-section.log`.
- **Design checks** (`design-check.mjs`, `design-check.config.json`): `--states` (hover, focus-visible and the
  configured clicks: open menu, tabs, sliders, against the source in the same state), `--motion` (transition and
  animation duration, delay, easing per element) and `--long` (page overflow and clipped text from 320 to 1920 on a
  long-content test page). Numbers first, images only for failing rows; rows in `report/design-check.json`, the
  same shape as figma-to-wordpress's Figma checks. Default pass marks: colours exact, sizes 1 px, times 10 ms, easing
  exact, overflow 1 px, 0 clipped text (the first real build sets the final ones).
- **`long-content.php`** (CLI, local only): `make <route>` copies a page with every text field about three times as
  long, WYSIWYG repeated and repeater rows doubled (marker `_kitwp_long_test`, noindex); `remove` deletes exactly
  the IDs it made.

### Changed

- **One plan document:** `_plan/PLAN.md` (goal, the source, how it is built, phases, per-section workflow, Done)
  replaces BUILD-PLAN.md, ARCHITECTURE.md and SOURCE-NOTES.md; new-site.py fills its source table. CONTENT-MODEL.md
  and OLD-SITE-URLS.md stay. Projects started on 0.8 keep their files.
- `region-check.mjs` also compares the region's text, prints failures only (`--all` for every row), keeps images
  only for failures and ends with `OK|FAIL region-check: n of m pass`. `domdiff.py` takes a simple selector as a
  region (tag, .class, #id, tag.class).
- Install table: Antigravity CLI (it replaced Gemini CLI on 18 Jun 2026), Devin Desktop (was Windsurf), OpenCode and
  Cline added (README, `references/agents.md`, the website).
- Steps in plain words for any agent: the read-only QA check is a subagent where the tool has one, else a new chat;
  it reads the numbers first and opens images only for failures.

### Fixed

- Git Bash on Windows rewrites `/about/` into `C:/Program Files/Git/about/`: check-section.py stops with the fix
  (`MSYS_NO_PATHCONV=1`, or the route without its first slash); a gotcha says so for every parity tool.

### Checked

- Run once on a local test site (Laragon, serve-wp on a port, Secure Custom Fields): start.py, new-site.py
  `--plan-only` (PLAN.md filled), setup.py (database, WordPress 7.1.4 with 3,782 files checked, wp-config, serve-wp,
  admin, Contact Form 7, Yoast SEO, SCF; a second run keeps everything), check-section.py (pass, and a text, DOM and
  PHPCS fault caught), design-check.mjs (a hover colour, a 0.15 s vs 0.3 s transition and a clipped long heading
  caught), long-content.php make and remove. Test site, database and pages removed afterwards.

## [0.8.0] - 2026-11-18

Phase by phase, straight through: setup in one go, QA that only logs, one fix loop until QA finds 0, two gates.

### Changed

- **Phases replace sprints:** P0 Plan (the developer's Plan OK) > P1 Setup > P2 Pages (section by section) > P3
  Forms and email > P4 SEO, security, speed > P5 Fix and QA loop > the developer's Go-live > P6 Launch and live QA.
  After each phase QA only logs findings in one list on the board; nothing is fixed before P5 except a blocker (the
  site breaks, or the next phase cannot start). P5 fixes the whole list and runs the full QA again until it finds 0.
  Two developer gates (Plan OK, Go-live); no go per phase (SKILL.md rules 4 and 6, `references/phases-and-qa.md`).
- **No role-play team:** the roles (owner, lead, UI, UX, security, tester, QA) are now the QA checklist. QA per
  phase = gate.py + the parity scripts + one read-only check by a fresh subagent on a faster model (Sonnet).
  `references/team-and-sdlc.md` is now `references/phases-and-qa.md`; `_plan/SPRINT-PLAN.md` is now
  `_plan/BUILD-PLAN.md` (shorter: goal, phases, per-section workflow, Done, every session).
- **Board = progress page:** BUILD-MAP.md has Phases (with the QA run), Developer gates, steps per phase, Pages (page,
  route, section, status: todo, building, built, checked, fixed), QA findings (F-001...; blocker, major, minor;
  open, fixed after a re-check, or decided) and the Log, in the figma-to-wordpress skill's words. `gate.py` (exit
  0/1/2) rewritten for it; `render.py` writes `progress.json` in the shared shape (figma-to-wordpress's keys and
  phase ids) and the same progress page (its layout, MIT); the old board template is gone. Boards made with 0.7 or
  older keep their kit version.
- **Passwords:** rule 5 allows one exception: the developer's default local admin password, read by install-wp.py
  from `profile.local.json` for local sites only and never printed. Live admins keep their own password, typed by
  the developer.
- **ACF PRO by default:** the intake no longer asks ACF PRO or Secure Custom Fields (SCF only when asked).
- **Optimized by default:** SEO standard; PageSpeed Insights aimed at a pass, not a must. A heavy design that misses
  it on live gets one speed plugin that fits the host, checked for parity after each option; the design is never
  changed for a score (`references/seo-security.md` > Performance).
- **Converter for Media and Contact Form CFDB7** are installed on live at launch, not locally (setup, launch,
  essentials).
- **Context rule:** from 50% finish the section or page, checkpoint and continue in a new chat; cap 75% (replaces
  "a new chat after each gate").
- **Handoff templates** aligned with the handoff skill 1.2: summary header with `Updated: YYYY-MM-DD HH:MM +zz:zz`
  (new `{{NOW}}` value in new-site.py), tagged facts, "Waiting on"; the generated summary passes its checker.

### Added

- `scripts/setup/install-wp.py`: local WordPress in one go: install with the default local admin from the profile's
  new `local_admin` (e.g. `agency-dev`), permalinks, search engines discouraged, timezone, the WordPress block in
  .htaccess, the fresh-install samples removed, Contact Form 7 and Yoast SEO from wordpress.org (every file checked
  against the official checksums), ACF PRO from the profile's zip (or SCF with `--fields scf`), all activated,
  debug.log read. Refuses unless the URL is local and wp-config says `local`. Plugins unzip into a temp folder with
  Windows long-path support and move into place only when complete.
- `references/wordpress-essentials.md`: the WordPress rules in one page (plugins local and live, local setup,
  theme, fields, forms and email, SEO, security, speed, launch, live QA, passwords), a stable path other skills
  read.
- `tests/test_phases.py`: gate rules (work ahead, bad values, QA run, blockers, the fix loop and the go-live),
  render.py, install-wp.py's local-only guard.

## [0.7.1] - 2026-11-17

No agent ends a turn silently: every stop sends a short report upward with its next step.

### Changed

- Never stop silently (SKILL.md rule 15): every turn that ends without the work going on (a sprint gate, a part
  done, a checkpoint or new chat, a pause, a block, waiting for a go or a manual step) ends with a stop report:
  done, state, decisions taken on the agent's own with the default chosen, and last
  `Next: <step> — waiting on <who>`. It goes upward to the parent session (for example a Command Center) as well as
  the agent's own chat, else to the developer with "Proceed: <step>" first. Every role and subagent; the shape is in
  `references/team-and-sdlc.md` > The stop report, and the sprint plan template's session rules.
- Beginner mode: the `Next:` line in plain words replaces "Your turn:" at the end of a message (SKILL.md rule 13,
  `references/agents.md`, `profile.example.json`).

## [0.7.0] - 2026-11-17

Rules from a design-sourced build: theme CSS on _tw, media and maps, performance and SEO. The golden master still
wins on what the page looks like; these rules cover what the build writes itself and what the source never decides.

### Added

- Writing CSS on _tw (`references/source-types.md`): sections are Tailwind utilities on the `@theme` tokens,
  custom CSS only for CF7 and what utilities cannot express, no `text-wrap: balance` on headings, an end padding
  of |letter-spacing| on text tokens so wraps match the design. Lessons in `gotchas.md`.
- Media and maps (`references/build.md`): logos (the agency badge and its link too), the Site Icon, email images
  and content images are seeded into the Media Library and set in ACF or Theme Settings, never hard-coded.
  - Theme Settings example: Branding gets Logo, Email logo and Email badge; Business gets Map.
  - The lead email and the auto-reply read their logo and badge from Theme Settings (theme files as the fallback);
    "Hide agency badge" hides the email badge too.
  - The seeder sets the Site Icon (`"site_icon"` in settings.json) and imports SVG logos (SVG stays closed for
    wp-admin uploads).
  - `kitwp_img()` prints a Media Library SVG; `kitwp_inline_svg()` prints it inline (sanitised), so an inline
    `<svg>` logo stays 1:1.
  - `kitwp_map_src()` / `kitwp_map_iframe()`: a live Google Maps iframe from one field that takes a Maps link, the
    embed code or an address; the default city (`map_default` in site.json) until the address is confirmed.
- Performance and SEO (`references/seo-security.md`): Core Web Vitals from the first section (LCP preload and
  fetchpriority, sized srcset, nothing lazy above the fold, reserved media space, metric-matched fallback font,
  minimal deferred JS), no speed plugin unless the theme cannot do it; one H1, heading order, aria-labels, alt and
  schema in every section's test step. `kitwp_img()` and `kitwp_preload_image()` take an opt-in `fetchpriority`.
- `tests/test_theme_php.py`: the map, SVG, CF7 markup and seeded email helpers.

### Changed

- CF7's autop is off on every form, not only the kit's lead forms, and empty paragraphs are removed.
- The seeder refuses a form whose lead email or auto-reply file is not a full HTML document (the branded
  template), and reports a form with no auto-reply.
- Speed is checked with PageSpeed Insights on staging and live; local Lighthouse is a regression guard only (QA,
  runbook, report, board, architecture template).
- The update command explains how to update a skill saved in a chat app that shows no update card (zip,
  Upload skill, "Upload and replace", version history kept).

### Fixed

- The ACF builder's example spec stopped with an error (`ui=1` on a true/false field, which always has it).

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
