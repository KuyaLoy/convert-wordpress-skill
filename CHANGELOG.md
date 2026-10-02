# Changelog

Every change to the skill, newest first. Versions follow [Semantic Versioning](https://semver.org); the format
follows [Keep a Changelog](https://keepachangelog.com).

## [Unreleased]

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
