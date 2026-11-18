# {{SITE_NAME}}: WordPress conversion plan

Status: **P0 Plan**. Written {{DATE}}. One page for the Plan OK: the goal, what the source is, how it is built, the
phases. Read with `CONTENT-MODEL.md` (what gets built), `OLD-SITE-URLS.md` (redirects), `../BUILD-MAP.md` (status
and QA findings, private), `../handoff.md` (session state). The kit's rules: `<kit>/references/phases-and-qa.md`.

## 1. Goal

Replace the static site with a WordPress site that **looks and behaves exactly the same on every screen size**,
**keeps every URL and SEO signal**, and lets editors **change all content in ACF**, with the forms in
**Contact Form 7**. Optimized by default: SEO standard, PageSpeed Insights aimed at a pass (not a must; the design
is never changed for a score).

Success measures: every static route exists with the same slug, title, description and H1; the diffs show no
difference at every breakpoint; states, motion and long content pass the design checks; all content editable;
leads delivered with the branded emails; no new 404s after launch; QA finds 0 before go-live.

## 2. The source

`start.py` (analyze-source.py) fills this table; `_plan/analyze.txt` has its full output.

| Item | Found |
|---|---|
| Stack | (plain HTML / PHP / Next.js export / Next.js server / React SPA / Astro / Vue / other) |
| Build command and output | |
| Tailwind | (version, config) -> starter theme |
| Routes | (count, dynamic routes and their real paths) |
| Content | (content modules, Markdown, CMS fetches) |
| Images | (next/image widths, loader, deviceSizes[0]) |
| Fonts | (Google Fonts links, next/font self-hosted files) |
| Icons | |
| Forms | (endpoints, handler, recipients) |
| Tracking | (GTM / GA4 / Ads ids found) |
| Redirects | (redirect map, next.config, vercel.json, .htaccess) |

**Golden master:** How it is produced and where it is served (see the skill's references/source-types.md).

**Documents in the repo, rules that must hold, open items not ours to fix:** (design-system non-negotiables, copy
brief rules, accessibility promises; each open item with how the build handles it)

<!-- kit:secrets -->

## 3. How it is built

| Part | Choice |
|---|---|
| WordPress | Latest release (checksums verified); local {{SITE_DIR}} at http://{{LOCAL_HOST}}; PHP 8.4 locally, code for 8.1 to 8.4 |
| Theme | `{{THEME}}` on {{STARTER}} (Barebones for plain CSS, _tw for Tailwind); every global prefixed `kitwp_` |
| Fields | ACF PRO (licence by the developer), JSON in acf-json, built by `tools/acf/build_field_groups.py` (stable keys) |
| Forms | Contact Form 7 in the static markup; native post, 303 to /thank-you/; branded HTML emails |
| SEO | Yoast seeded; titles, descriptions, canonicals, robots and headings as static; JSON-LD from the static |
| Other plugins | Only what the task needs, after the developer says yes; Converter for Media and CFDB7 on live at launch |

- **1:1:** each partial starts as the section's rendered HTML; the static CSS byte for byte (or the same Tailwind
  version and tokens); nothing else styles the page; the head, images (widths, sizes, srcset) and behaviour (state
  classes, timings, vanilla JS, works without JavaScript) as static.
- **Checks:** `tests/parity/check-section.py` per section (pixel, text, DOM, php -l, PHPCS, duplicates); the full
  parity run (every CSS breakpoint and 1 px past it) at each phase's QA; `design-check.mjs` for states (hover, focus,
  the clicks listed below), motion and long content, numbers first, images only for failures.
- **States to check** (design-check.config.json "states"): (open menu, tabs, sliders, accordions, pop-up: the
  trigger, the region it changes, the widths)
- **Seeding:** exporters write `_setup/seed/`; Tools > Seeder (local only), idempotent (the second run: "same").
- **Security and speed:** no secrets in files or chats; file editing off; private files 403 and out of the package;
  debug off on live; Core Web Vitals from the first section; caching rules in htaccess-live.txt; a speed plugin only
  when live misses PageSpeed Insights and the theme cannot fix it.
- **Folders:** `{{SITE_DIR}}/` (WordPress root; BUILD-MAP.md, handoff files, `_plan/`, `_setup/` private);
<!-- starter:barebones -->
  the theme in `wp-content/themes/{{THEME}}/` (includes/, template-parts/, acf-json/, tests/parity/).
<!-- /starter:barebones -->
<!-- starter:tw -->
  the _tw project in `wp-content/themes/{{THEME}}/` (tailwind/, tests/parity/, and theme/: what WordPress loads).
<!-- /starter:tw -->

## 4. Phases

| Phase | Output for this site |
|---|---|
| P0 Plan | This plan, CONTENT-MODEL, OLD-SITE-URLS, the board; the developer's Plan OK |
| P1 Setup | `setup.py` (database, WordPress, admin from the profile, plugins), theme, golden master, parity tools, 1:1 CSS, ACF, header and footer, seeder |
| P2 Pages | Every page on the board, section by section |
| P3 Forms and email | Every form in CF7, branded lead email and auto-reply, /thank-you/, spam protection |
| P4 SEO, security, speed | SEO plugin seeded, JSON-LD, old URLs, headings and ARIA, hardening, Core Web Vitals |
| P5 Fix and QA loop | Every finding fixed; full QA (design checks included) until it finds 0; runbook, editing guide; the Go-live |
| P6 Launch and live QA | Live (Converter for Media and Contact Form CFDB7 added there), live QA, report, client pack |

QA after each phase only logs findings in BUILD-MAP.md; only a blocker is fixed before P5.

**Every section, every time:** static (copy, diff 0) > model (fields in the builder) > sync > dynamic (escaped) >
seed > `check-section.py <route> --section <selector>` (one line; OK before moving on) > the board row `built`.

## 5. Done and every session

- A phase is done when gate.py says it may close (every step DONE, its QA run recorded, no open blocker; P0: the
  Plan OK; P5: QA "0 found", no finding open, the Go-live). The build is done when the site is live, live QA passes,
  and the report and client pack are handed over.
- Start: read ai-handoff-summary.md, run gate.py. During: one section at a time; context checked at each step (from
  50% finish the section or page and continue in a new chat; cap 75%). Stop: both handoff files (and the progress
  page after a phase closes), then the stop report upward with the `Next: <step> — waiting on <who>` line.

## 6. Research sources (with the date checked)

- WordPress release notes, ACF and CF7 docs: the pages read and the date.
