---
name: convert-to-wordpress
description: Converts any existing website (plain HTML, Next.js, React, Astro, Vue and other stacks) into a 1:1 WordPress site with the same design, URLs, SEO and tracking, every page editable in ACF PRO and every form in Contact Form 7. Works as a full team (owner, manager, lead and developers, UI, UX, security, tester, QA), one sprint at a time with a gate per sprint, from intake and local setup to go-live, live QA and the report. Use whenever a site built outside WordPress has to be rebuilt in WordPress.
license: GPL-2.0-or-later
---

# Convert a website to WordPress, 1:1

The site already exists: as code, as a build, or live. The job is to rebuild it in WordPress so it looks and
behaves the same at every screen size, keeps every URL and SEO signal, and lets editors change everything in
wp-admin: content in ACF PRO fields, forms and emails in Contact Form 7. Any stack, any kind of business, any
country and language.

Its lessons come from real builds: a 36-page Next.js export (live in 2026) and a PHP and Tailwind landing page.

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
| `references/launch.md` | Go-live with Duplicator Pro, other hosts, changes after launch |
| `references/qa-report.md` | Live QA, test leads, the report, the task comment |
| `references/gotchas.md` | Before anything risky. Add every new lesson there |
| `references/agents.md` | Installing and running this skill in Claude, Codex, Cursor, Gemini, Antigravity and others |

## Rules (always)

1. **1:1 above all.** The golden master (the site exactly as visitors get it) is the design. Copy its markup and
   CSS; fields replace content, never structure, classes or order. The diffs decide, not the eye.
2. **Static first, then dynamic.** Every section is copied as static HTML and diffed to zero before it gets fields.
3. **The task decides.** The task tracker's requests are the scope; where they differ from this skill's defaults,
   the task wins. Campaign and landing page URLs never change.
4. **Ask first** before any download (name, source, size), any plugin or package install, creating a database,
   deleting anything, any live change, and publishing anything. One OK covers one action.
5. **Never type a password, licence key or API key.** The developer pastes them. Reports and messages say
   `[PASTE PASSWORD HERE]`. ACF PRO's key goes in wp-config (`ACF_PRO_LICENSE`), pasted by the developer.
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
13. Write plainly; follow the profile's reply style.

## The team

You work as a full senior team, one role at a time. Builders build, reviewers check, and nobody approves their own
work.

| Role | Owns | Signs a gate |
|---|---|---|
| Owner | Scope and acceptance: the task's requests, the 1:1 rule | Yes |
| Manager | Plan, board, ceremonies, blockers, handoff, stakeholder updates | Yes |
| Lead developer | Architecture, standards, the sprint backlog, review of every task | Yes |
| Front-end developer | Static first: copied markup, CSS, fonts, images, vanilla JS behaviour | No, builds |
| WordPress developer | Dynamic: ACF groups and sync, wiring, seeder, CF7, SEO plugin, hooks | No, builds |
| UI | Visual parity at every width | Yes |
| UX | Behaviour parity and the editor experience | Yes |
| Security | Secrets, escaping, sanitising, nonces, private files, hardening | Yes |
| Tester | Parity, DOM, text and SEO diffs, the seeder, forms | Yes |
| QA | Real-browser proof at phone and desktop widths; live QA | Yes |

The Lead splits each story into tasks (who builds it, what done looks like) at sprint planning; each developer ends
a task with a three-line hand-off note (what changed, how it was tested, what is open) and the Lead reviews it.
With subagents, the Lead may hand a task card to a developer subagent, and the sprint review is always a fresh
subagent that did not write the code. Without subagents, switch hats explicitly. "The developer" always means the
human running the build: they decide plugins, money, secrets, live steps and every sprint sign-off.

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
2. **Get the source** given with the command (`/convert-to-wordpress <git URL, zip or folder>`) or in words; none
   given: ask for it. Ask, then `python3 <kit>/scripts/get-source.py <source>`: a working copy `<name>-source`
   (shallow clone, safe unzip or copy; the original is never touched). Read the profile and the task tracker's tasks.
3. **Study the copy:** `python3 <kit>/scripts/analyze-source.py <name>-source --json <wp_root>/_plan/analyze.json
   --site-draft <wp_root>/_plan/site.json`: the stack, Tailwind (so the starter), routes, forms, tracking, fonts,
   libraries, secrets to never copy, and the golden master (`references/source-types.md`).
4. **Ask once**, in one batch (a question tool if your agent has one, otherwise a short numbered list), only what
   you could not find: site name and live domain; the source and whether it is live; which tasks are in scope; the
   local stack, folder and URL; how to create the database; the old site and its URLs (if one is replaced); lead
   email recipients; country, language(s) and right-to-left; the host and how the site moves to live.
5. **Finish** the drafted `site.json` with the answers (every field: `references/setup.md`).
6. **Create the project:** `python3 <kit>/scripts/new-site.py <wp_root>/_plan/site.json --plan-only` (plan,
   tools, BUILD-MAP.md, handoff files, private-files block). Then Sprint 0, up to its gate and the developer's go.

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

1. **S1-01 WordPress.** Database: ask, then phpMyAdmin in the developer's browser, their database tool, or a shell
   that reaches MySQL (`CREATE DATABASE db_<site> CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci;`). Ask,
   then `python3 _plan/tools/setup/get-wordpress.py <wp_root>` (checksums verified, never overwrites). Then
   `python3 _plan/tools/setup/make-wp-config.py <wp_root> --db db_<site>` (the database password only from the
   `DB_PASSWORD` environment variable; environment `local`, debug log on, file editing off, a commented
   `ACF_PRO_LICENSE` line). The installer: the developer types the admin password. Settings: permalinks
   `/%postname%/`, language, timezone and date formats of the business, "Discourage search engines" on (local only).
   Clean-up (sample content, unused plugins, later the default themes) with the developer's OK.
2. **S1-02 Starter plugins: ACF PRO, Contact Form 7 and Yoast SEO.** Ask first. ACF PRO comes from the
   developer's zip (the profile's `plugin_zips`), and the developer pastes the licence. **The ACF menu always shows**
   to administrators, on live too. Later, when needed: Redirection (old URLs), Duplicator Pro (the move), Converter
   for Media and Contact Form CFDB7 (must be on live), the profile's optional `extra_plugins`. Read debug.log after
   each install.
3. **S1-03 Theme.** Ask, then get the starter into `wp-content/themes/<theme>/`: Barebones (git clone of
   github.com/benchmarkstudios/barebones) for plain CSS, or _tw generated with the slug and prefix (`wp scaffold
   _tw <theme> --theme_name="<Site>" --prefix=<prefix>`, or underscoretw.com) for Tailwind. Then
   `python3 <kit>/scripts/new-site.py <wp_root>/_plan/site.json`: it prepares the starter (prefix renames, its
   samples and its ACF-hiding `acf.php` moved aside, PHPCS fixes) and copies the kit in. Build the assets, activate,
   `composer install`, PHPCS clean.
4. **S1-04 Golden master served, parity tools ready:** the theme's `tests/parity/` (its README has every command);
   the golden master against itself must diff 0.000%.
5. **S1-05 Design system 1:1:** the static CSS byte for byte (`KITWP_STYLESHEETS`, `KITWP_INLINE_CSS`), or for
   _tw the same Tailwind version and tokens. Swap test (`swaptest.py`): 0.000%. Nothing else styles the page.
6. **S1-06 ACF foundation:** field groups from `_plan/tools/acf/build_field_groups.py` into `acf-json/` (stable
   keys; `modified` bumped only for changed groups), each group's own Sync link; Theme Settings read by field key.
7. **S1-07 Global layout:** header, footer, mobile bar, pop-up: copied markup with React-style tight whitespace,
   behaviour in vanilla JS with the same state classes; the head as static (`head.php`, `<html lang dir>`).
   `region-check.mjs` (pixels) and `domdiff.py` per region: 0.
8. **S1-08 Seeder foundation:** Tools > Seeder (local only) for media, settings and menus; run it twice: the second
   run says "same" everywhere.

## Sprints 2 to 4: templates and pages

Every section, every time: **static** (FE copies the rendered HTML, diff 0) > **model** (WP adds the fields to the
builder) > **sync** > **dynamic** (fields replace the copy, every output escaped) > **seed** > **test** (visual, DOM,
text, headings, keyboard, no notices, no console errors) > **clean** (php -l, PHPCS, duplicates) > **review** by
the Lead > **hand off** (page tracker cells `ok`, handoff).

- Pages, not custom post types, so URLs stay at the root. Fixed templates where pages share a layout; one Flexible
  Content field ("Page Sections") for one-off pages. Grids list pages by template in menu order.
- Say it once: anything on two pages lives in Theme Settings, with tokens (`{phone}`, `{year}`...). An empty page
  field falls back to the default.
- next/image parity: same widths, sizes, srcset rule, width and height attributes, priority preloads.
- Raw titles, safe map iframes, SVG copied by script. Details: `references/build.md`.

## Sprint 5: Forms and email

Contact Form 7 holds each form (Form tab) and its email (Mail tab); the theme prints CF7's tags as the static
markup. Forms post natively and answer 303 to `/thank-you/` (sent, mail failed, honeypot), so they work without
JavaScript. The email is one HTML part with the envelope sender and Message-ID on the domain. Local mail goes to the
admin only and is saved in `_setup/mail/`. A chat widget posts FormData to CF7's REST endpoint (the theme's
`assets/chat-save.js`). Spam: the static honeypot plus reCAPTCHA v3 with a token fetched on submit.
Field names like `name` need the query-var filter. Details: `references/forms-email.md`.

## Sprint 6: SEO, security, performance

The SEO plugin seeded (head clean-up on, campaign URL and permalink clean-up off, archives off, share images), its
schema replaced by the static JSON-LD rebuilt from the page; titles, descriptions, canonicals and robots as static;
`/thank-you/` noindex; one H1 and the static heading outline; old URLs (if any) as 301s in Redirection (query
strings passed); GTM as the tracking task says (never injected into a built Next.js page); accessibility as static
or better; hardening (no secrets, file editing off, private files 403, REST user list hidden, debug off on live).
Lighthouse on live only. Details: `references/seo-security.md`.

## Sprint 7: QA and launch prep

Full parity run (every route, every CSS breakpoint and 1 px past it), old URLs checked locally, real phones, the
seeder twice, `RUNBOOK.md` and `htaccess-live.txt` in `_setup/launch/` completed, a short editing guide. The
go/no-go list is in the runbook. gate.py must report every sprint DONE.

## Launch (the developer does each step; you give one at a time)

Backup of the live site (and a full backup if it is an old WordPress) > build the theme assets > Duplicator Pro
package with the filters from `python3 _plan/tools/launch/duplicator-filters.py <root> <theme>` (`--starter tw`
for _tw) > database and PHP on the host > the old site moved into a sibling folder (rollback = move it back) >
installer > `installer.php` answers 404 and no archive is left > wp-config `production`, debug off > `.htaccess` from
`htaccess-live.txt` > wp-admin: search engines allowed, permalinks saved, reCAPTCHA keys and ACF licence (the
developer), tracking, the live plugins (S1-02) active, debug.log read once, the plugin list noted. Rollback if a
check fails and cannot be fixed quickly. Details: `references/launch.md`.

## Live QA and the report

```
python3 _plan/tools/report/live-qa.py https://<domain> <GTM-ID> _setup/seed/redirects.json <local_host>
node _plan/tools/report/track.mjs https://<domain> <GTM-ID> / /thank-you/
node _plan/tools/report/shots.mjs https://<domain> /:1440:home-desktop /thank-you/:1440:thankyou-desktop /<page>/:390:page-mobile
node _plan/tools/report/pdf.mjs _setup/launch/report.html Final-Live-Check.pdf [Editing-Guide.pdf]
```

Three test leads (inline form, pop-up, chat) named `TEST <developer> - please ignore`, sent with the real submit
button, after the developer agrees; the developer confirms the emails and the host's delivery log. Fill
`report.html` with verified facts only (`grep -n "\[\[" report.html` prints nothing), make one PDF, and draft the
task comment and the stakeholder message (login with `[PASTE PASSWORD HERE]`). Details: `references/qa-report.md`.

## Scripts at a glance

| Script (in the project: `_plan/tools/...`) | Does |
|---|---|
| `scripts/get-source.py` | The working copy of the source: git clone, safe unzip or copy |
| `scripts/analyze-source.py` | Studies the source: stack, routes, Tailwind, forms, tracking, the golden-master method |
| `scripts/new-site.py` | `--plan-only` for Sprint 0; then prepares the starter theme and copies the kit in |
| `scripts/snapshot-routes.mjs` | Rendered HTML of every route, for client-rendered or server sources |
| `scripts/setup/get-wordpress.py`, `make-wp-config.py` | WordPress with checksums; wp-config without typing secrets |
| `scripts/acf/build_field_groups.py` | ACF JSON with stable keys; `--check` validates |
| `scripts/seed/export.mjs`, `export-pages.py` | Static content into `_setup/seed/` for Tools > Seeder |
| `scripts/build-map/gate.py`, `render.py` | The sprint gate; the private board page |
| `scripts/parity/` (the theme's `tests/parity/`) | Pixel, text, SEO and DOM diffs; breakpoints; mirror and server for cloud runs |

## Done means

Every route 1:1 and editable; forms and emails proven on live; tracking and the conversion proven; old URLs
redirect; installer and private files not public; the ACF licence active, the ACF menu visible; Converter for
Media and CFDB7 live; every sprint closed through its gate; the board, handoff files and gotchas current; the
report PDF, the task comment and the stakeholder message handed to the developer.
