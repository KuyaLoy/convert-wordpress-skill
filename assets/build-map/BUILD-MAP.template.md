# BUILD-MAP: {{SITE_NAME}} WordPress build

**Private: the developer only.** Not shared with the client or their contacts, and never deployed. Stakeholder
updates are written separately, in plain language, with no sprint or story numbers.

Updated: **{{DATE}}** | Current sprint: **S0 Planning** | Next: **S1 Foundation**.

Status key: `DONE` `IN PROGRESS` `TODO` `BLOCKED` `DECISION` (waiting on the developer)
Plan: `_plan/SPRINT-PLAN.md` | Content: `_plan/CONTENT-MODEL.md` | Build rules: `_plan/ARCHITECTURE.md` |
Source notes: `_plan/SOURCE-NOTES.md` | Session state: `handoff.md`

Sprint rule: one sprint at a time. A sprint closes only when `python3 _plan/tools/build-map/gate.py BUILD-MAP.md`
passes (every story DONE, its pages ok, every gate PASS, the developer's go); `gate.py BUILD-MAP.md --close` is the
only way to open the next sprint.

---

## At a glance

| Sprint | Goal | Status | Stories done |
|---|---|---|---|
| S0 Planning | Study the source, plan, content model, architecture, this board, handoff | IN PROGRESS | 0 / 4 |
| S1 Foundation | Local WordPress, golden master and parity tools, theme, 1:1 CSS, ACF, header and footer, seeder | TODO | 0 / 8 |
| S2 Main template | The template most pages share, 1:1 and editable | TODO | 0 / 4 |
| S3 Other templates | The other fixed templates, 1:1 and editable | TODO | 0 / 4 |
| S4 Flexible pages | Home, about, hubs, contact, thank you, legal, posts, 404 | TODO | 0 / 6 |
| S5 Forms and email | CF7 forms, lead email, redirect, spam protection | TODO | 0 / 4 |
| S6 SEO, security, performance | SEO plugin, schema, redirects, headings and ARIA, hardening, Lighthouse | TODO | 0 / 5 |
| S7 QA and launch prep | Full 1:1 run, content proof, runbook, editing guide | TODO | 0 / 3 |

## Now

- **Doing:** S0 planning.
- **Waiting on the developer:** the decisions marked DECISION below.
- **Blocked:** nothing.

## Decisions

| # | Decision | Status | Recommendation / answer |
|---|---|---|---|
| D1 | Local folder, URL, database | DECISION | `{{SITE_DIR}}`, http://{{LOCAL_HOST}}, DB `db_{{THEME}}` |
| D2 | Starter theme | DECISION | Tailwind source: _tw. Plain CSS: Barebones (from analyze-source.py) |
| D3 | SEO plugin | DECISION | Yoast SEO, its schema replaced by the static JSON-LD |
| D4 | Spam protection | DECISION | CF7 reCAPTCHA v3 + the static honeypot; badge position |
| D5 | Editor for ACF pages | DECISION | Block editor unless the developer says classic |
| D6 | Pages the static site lacks (blog, archives) | DECISION | In the site's design, new URLs flagged to SEO |
| D7 | Enquiry storage | DECISION | Mail only, or a database copy plugin |
| D8 | Git | DECISION | Only if the developer says so |

## Sprint gates

Each role checks its gate at the end of the sprint (`_plan/SPRINT-PLAN.md` section 1 says what): `PASS`, `n/a`, or
what is still open. Sign-off: `go <date>`, written only after the developer says go in the chat.

| Sprint | Owner | Manager | Lead dev | UI | UX | Security | Tester | QA | Retro | Sign-off |
|---|---|---|---|---|---|---|---|---|---|---|
| S0 | | | | | | | | | | |
| S1 | | | | | | | | | | |
| S2 | | | | | | | | | | |
| S3 | | | | | | | | | | |
| S4 | | | | | | | | | | |
| S5 | | | | | | | | | | |
| S6 | | | | | | | | | | |
| S7 | | | | | | | | | | |

---

## Sprint 0: Planning (IN PROGRESS)

| ID | Story | Status | Notes |
|---|---|---|---|
| S0-01 | Study the source (analyze-source.py) and set the golden master | IN PROGRESS | |
| S0-02 | Plan docs: SPRINT-PLAN, CONTENT-MODEL, ARCHITECTURE, SOURCE-NOTES, OLD-SITE-URLS | TODO | |
| S0-03 | Board and handoff | TODO | |
| S0-04 | Decisions D1 to D8 | TODO | |

## Sprint 1: Foundation (TODO)

| ID | Story | Status | Notes |
|---|---|---|---|
| S1-01 | WordPress on the local stack (database, checksums, wp-config, install, settings, clean-up) | TODO | |
| S1-02 | Starter plugins: ACF PRO, Contact Form 7 | TODO | |
| S1-03 | Theme skeleton (starter theme by the Tailwind rule, new-site.py, prefix, PHPCS) | TODO | |
| S1-04 | Golden master served and parity tools self-test at 0.000% | TODO | |
| S1-05 | Design system 1:1 (built CSS, swap test 0.000%) | TODO | |
| S1-06 | ACF foundation (acf-json, Theme Settings, components) | TODO | |
| S1-07 | Global layout (header, footer, mobile bar, pop-up) | TODO | |
| S1-08 | Seeder foundation (media, settings, menus; second run "same") | TODO | |

## Sprint 2: Main template (TODO)

| ID | Story | Status | Notes |
|---|---|---|---|
| S2-01 | Static design of every section (copied HTML) | TODO | |
| S2-02 | Field group + sync | TODO | |
| S2-03 | Wire and seed every page on the template | TODO | |
| S2-04 | Test, clean, cross-check | TODO | |

## Sprint 3: Other templates (TODO)

| ID | Story | Status | Notes |
|---|---|---|---|
| S3-01 | Static design | TODO | |
| S3-02 | Field group + sync | TODO | |
| S3-03 | Wire and seed | TODO | |
| S3-04 | Test, clean, cross-check | TODO | |

## Sprint 4: Flexible pages (TODO)

| ID | Story | Status | Notes |
|---|---|---|---|
| S4-01 | Page Sections field and layout library | TODO | |
| S4-02 | Home | TODO | |
| S4-03 | Inner pages (about, hubs, contact) | TODO | |
| S4-04 | Thank you (noindex), legal pages, 404 | TODO | |
| S4-05 | Posts and the blog (if any) | TODO | |
| S4-06 | Test, clean, cross-check | TODO | |

## Sprint 5: Forms and email (TODO)

| ID | Story | Status | Notes |
|---|---|---|---|
| S5-01 | CF7 lead form 1:1, works with JavaScript off | TODO | |
| S5-02 | Pop-up and chat (if any) through CF7 | TODO | |
| S5-03 | Lead email: one HTML part, Bcc, Reply-To | TODO | |
| S5-04 | Redirect to /thank-you/, honeypot, reCAPTCHA | TODO | |

## Sprint 6: SEO, security, performance (TODO)

| ID | Story | Status | Notes |
|---|---|---|---|
| S6-01 | SEO plugin seeded, robots, sitemap | TODO | |
| S6-02 | JSON-LD equal to the static site | TODO | |
| S6-03 | Old URLs as 301s | TODO | |
| S6-04 | Headings, ARIA, keyboard; security hardening | TODO | |
| S6-05 | Lighthouse and Core Web Vitals (on live) | TODO | |

## Sprint 7: QA and launch prep (TODO)

| ID | Story | Status | Notes |
|---|---|---|---|
| S7-01 | Full 1:1 run, old URLs, real phones | TODO | |
| S7-02 | Content proof and the editing guide | TODO | |
| S7-03 | Launch runbook | TODO | |

---

## Page tracker (0 routes)

Columns follow the section workflow: **Build** (static HTML copied), **ACF** (fields in JSON, synced), **Seed**,
**1:1** (visual, DOM and text diff clean), **SEO/a11y** (headings, meta, schema, ARIA). Mark each cell `ok`.

| Route | Sprint | Build | ACF | Seed | 1:1 | SEO/a11y | Status |
|---|---|---|---|---|---|---|---|
| Header, footer, mobile bar, pop-up (global) | S1 | | | | | | TODO |
| `/` Home | S4 | | | | | | TODO |
| `/thank-you/` | S4 | | | | | | TODO |
| 404 | S4 | | | | | | TODO |

## Shared pieces

| Piece | Sprint | Status |
|---|---|---|
| Theme Settings options page | S1 | TODO |
| Menus | S1 | TODO |
| Page Sections layout library | S4 | TODO |
| CF7 forms and email template | S5 | TODO |
| JSON-LD | S6 | TODO |
| Old-site redirects | S6 | TODO |
| Parity scripts | S1 | TODO |

## Risks to watch

| Risk | Where it bites | Plan |
|---|---|---|
| Parity tools cannot reach the local sites from the agent's shell | S1-04 | Run them where the browser can reach .test, or use snapshots and the mirror |
| A duplicate PHP function name takes the site down | Every PHP change | Duplicate function check after every save |

## Log

- {{DATE}}: Project started from the convert-to-wordpress skill.
