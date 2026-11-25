# The phase steps in full

SKILL.md keeps the rules, the phase list and what each phase must prove; the steps of each phase are here, moved
unchanged in 0.10.0. Open the phase's section at its start (with `references/phases-and-qa.md`), and only that
section. Paths are relative to the skill folder.

## Contents

- Start: intake
- P0 Plan (no code)
- P1 Setup (in one go, after the Plan OK)
- P2 Pages (section by section)
- P3 Forms and email
- P4 SEO, security, speed
- P5 Fix and QA loop
- P6 Launch (the developer does each step; you give one at a time)
- P6 Live QA and the report

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
  the static page, opened locally with `--refresh 30 --open` (references/phases-and-qa.md > The progress page).
- **P0-04 Decisions and the Plan OK** (defaults in brackets; the developer may just say OK): local folder, URL and
  database; starter theme (_tw for a Tailwind source or a site clearly easier in Tailwind, else Barebones with
  CSS-variable tokens; the choice and one reason); spam protection (CF7 reCAPTCHA v3 plus the static honeypot, badge
  position); editor (block editor unless classic); pages the static site lacks, like a blog (site design, new URLs
  flagged to SEO); old URLs to redirect (Redirection only if any); git; for a multilingual source, how languages are
  built; every form and where its leads go (CF7 for each, the leads portal or "none: <reason>"), missing content as
  marked placeholders, a chat or search if the source has one, the live plugin checklist. All of it now, so no rule
  reopens finished work later. The OK message lists the downloads of P1 (WordPress, theme, ACF PRO zip, Contact Form
  7, Yoast SEO).
- **Recommended additions, raised at the plan** (PLAN.md's list, and first in the Plan OK message): form
  attribution, SEO, site speed, testing, tracking; for each, what the site lacks and what we recommend, one line with
  its size ("nothing to add" is a valid line). Form attribution is built in by default; the rest are
  recommendations: the developer decides, approved ones go into the plan, the others into the report. Anything else
  that changes the work (a risk, a blocker, a better way) is said in one line as soon as it is known, never first
  at done.

## P1 Setup (in one go, after the Plan OK)

1. **P1-01 WordPress, admin, settings, plugins:** one command, `python3 _plan/tools/setup/setup.py
   <wp_root>/_plan/site.json --profile <kit>/profile.local.json`. From site.json and doctor.json it creates the local
   database if missing (never drops one), gets WordPress with checksums (or verifies the one a local app made), writes
   wp-config (local, debug log, no file editing, an `ACF_PRO_LICENSE` line), starts `serve-wp.py` when the local app
   has no site addresses, then `install-wp.py`: the default local admin from the profile (`local_admin`, e.g.
   `agency-dev`; local sites only), permalinks `/%postname%/`, "Discourage search engines", the fresh-install samples
   removed, Contact Form 7 and Yoast SEO (checksums), ACF PRO from the profile's zip and Duplicator Pro from
   `plugin_zips.duplicator_pro` when set, all active. `--dry-run`
   shows the steps first. Exit 1 lists open items (no ACF PRO zip or local password yet: the developer adds them to
   the profile, then run it again). ACF PRO activates itself when the profile has `acf_pro_license`; otherwise the
   developer pastes the licence. The business's language and date formats in Settings. Profile `extra_plugins` marked
   `required` go in here too, except `"where": "live"` ones (launch only). **The ACF menu shows** to administrators, on
   live too. Converter for Media, Contact Form CFDB7 and the cache plugin are not installed locally or on staging: they
   go on live at launch (references/wordpress-essentials.md > Plugins: the list per environment). The separate scripts
   (`references/setup.md`) stay for a step that needs repeating.
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
without forms says so in site.json). Its address and password always live in Theme Settings > Leads portal
(administrators only, seeded empty, pasted on live; wp-config constants win when defined); never sent from local,
development or staging.
Every lead form also says where the lead came from (form attribution, built in: UTM tags, ad click ids, landing
page, referrer, first visit), in the lead email, CFDB7, the portal and `generate_lead`.
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
package in one step and prints the archive's top level; report that output) >
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
delivery log. Fill `report.html` with verified facts only (`grep -n "\[\[" report.html` prints nothing; any shell:
`python3 _plan/tools/report/text-check.py fill report.html` says OK), make one PDF, and draft the task comment and
the stakeholder message (login with `[PASTE PASSWORD HERE]`, which the developer fills; the agent never types a
password). Details: `references/qa-report.md`. Then the client pack from `_setup/handover/` (guide screenshots taken
as the client's Editor, plain English only): `references/handover.md`.
