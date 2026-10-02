# Changelog

Every change to the skill, newest first. Versions follow [Semantic Versioning](https://semver.org); the format
follows [Keep a Changelog](https://keepachangelog.com).

## [Unreleased]

### Changed

- Starter plugins: ACF PRO, Contact Form 7 and Yoast SEO (Yoast was a later install).
- Redirection is optional: only when the site has old URLs to redirect.
- On live, Converter for Media and Contact Form CFDB7 must be installed and active (SKILL.md, launch guide, runbook,
  Done means). Duplicator Pro stays the move to live.
- The profile's `extra_plugins` now holds only optional plugins of your own or your agency's.

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
