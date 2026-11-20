# BUILD-MAP: {{SITE_NAME}} WordPress build

**Private: the developer only.** Not shared with the client or their contacts, and never deployed. Stakeholder
updates are written separately, in plain language, with no phase or step numbers.

Updated: **{{DATE}}** | Phase: **P0 Plan** | Next: **P1 Setup**

Status key: phases and steps `DONE` `IN PROGRESS` `TODO` `BLOCKED`; sections `todo` `building` `built` `checked`
`fixed`; QA findings `open` `fixed` `decided`, severity `blocker` `major` `minor`.
Plan: `_plan/PLAN.md` (goal, source, how it is built) | Content: `_plan/CONTENT-MODEL.md` | Old URLs:
`_plan/OLD-SITE-URLS.md` | Session state: `handoff.md`

Phase rule: one phase at a time. After each phase QA only logs findings in "QA findings"; nothing is fixed before
P5 except a `blocker` (the site breaks, or the next phase cannot start). `python3 _plan/tools/build-map/gate.py
BUILD-MAP.md` checks the board; `--close` is the only way to open the next phase. The developer's gates: the plan
and go-live.

---

## Phases

| Phase | Goal | Status | QA run |
|---|---|---|---|
| P0 Plan | Study the source, plan documents, this board; the developer's OK | IN PROGRESS | n/a |
| P1 Setup | WordPress, plugins and theme in one go; golden master and parity tools; 1:1 CSS; ACF; header and footer; seeder | TODO | |
| P2 Pages | Every page, section by section: static copy, fields, seed, checks | TODO | |
| P3 Forms and email | CF7 forms, branded emails, thank-you redirect, spam protection | TODO | |
| P4 SEO, security, speed | SEO plugin, schema, old URLs, headings and ARIA, hardening, Core Web Vitals | TODO | |
| P5 Fix and QA loop | Fix every finding, full QA again until it finds 0; launch prep | TODO | |
| P6 Launch and live QA | Live after the developer's go; live QA; the report and the client pack | TODO | n/a |

## Developer gates

Written only after the developer says it in the chat: `ok <date>`.

| Gate | Status |
|---|---|
| Plan OK | |
| Go-live | |

## Now

The top of the progress page. Update the Doing line (with the time it started, `(started 14:05)`) when a step
starts, the rest at every stop, then render and republish.

- **Doing:** P0 planning.
- **Next:** the plan OK, then P1 Setup.
- **Waiting on the developer:** the plan OK (with the decisions below).
- **Blocked:** nothing.

## Decisions

| # | Decision | Status | Recommendation / answer |
|---|---|---|---|
| D1 | Local folder, URL, database | DECISION | `{{SITE_DIR}}`, http://{{LOCAL_HOST}}, DB `db_{{THEME}}` |
| D2 | Starter theme | DECISION | Tailwind source, or clearly easier in Tailwind: _tw. A normal site: Barebones with CSS-variable tokens. One reason in PLAN.md |
| D3 | Spam protection | DECISION | CF7 reCAPTCHA v3 + the static honeypot; badge position |
| D4 | Editor for ACF pages | DECISION | Block editor unless the developer says classic |
| D5 | Pages the static site lacks (blog, archives) | DECISION | In the site's design, new URLs flagged to SEO |
| D6 | Old URLs | DECISION | Redirection only if the site has old URLs |
| D7 | Git | DECISION | Only if the developer says so |

---

## Phase 0: Plan (IN PROGRESS)

| ID | Step | Status | Notes |
|---|---|---|---|
| P0-01 | Study the source (start.py) and set the golden master | IN PROGRESS | |
| P0-02 | Plan docs: PLAN, CONTENT-MODEL, OLD-SITE-URLS | TODO | |
| P0-03 | This board (pages and sections listed) and the handoff files | TODO | |
| P0-04 | Decisions D1 to D7 and the plan OK | TODO | |

## Phase 1: Setup (TODO)

| ID | Step | Status | Notes |
|---|---|---|---|
| P1-01 | WordPress, admin, settings and plugins in one go (setup.py) | TODO | |
| P1-02 | Theme (starter by the Tailwind rule, new-site.py, prefix, PHPCS) | TODO | |
| P1-03 | Golden master served, parity tools self-test at 0.000% | TODO | |
| P1-04 | Design system 1:1 (built CSS, swap test 0.000%) | TODO | |
| P1-05 | ACF foundation (acf-json, Theme Settings) and the seeder (second run "same") | TODO | |
| P1-06 | Global layout (header, footer, mobile bar, pop-up) | TODO | |
| P1-07 | Phase QA run (findings logged) | TODO | |

## Phase 2: Pages (TODO)

| ID | Step | Status | Notes |
|---|---|---|---|
| P2-01 | Fixed templates, section by section (static, fields, sync, seed, checks) | TODO | |
| P2-02 | Flexible pages (Page Sections) | TODO | |
| P2-03 | Thank-you (noindex), legal pages, 404, posts (if any) | TODO | |
| P2-04 | Phase QA run (findings logged) | TODO | |

## Phase 3: Forms and email (TODO)

| ID | Step | Status | Notes |
|---|---|---|---|
| P3-01 | CF7 forms 1:1, working with JavaScript off, 303 to /thank-you/ | TODO | |
| P3-02 | Pop-up and chat (if any) through CF7 | TODO | |
| P3-03 | Branded lead email and auto-reply; honeypot and reCAPTCHA | TODO | |
| P3-04 | Phase QA run (findings logged) | TODO | |

## Phase 4: SEO, security, speed (TODO)

| ID | Step | Status | Notes |
|---|---|---|---|
| P4-01 | SEO plugin seeded, JSON-LD, robots, sitemap, old URLs as 301s | TODO | |
| P4-02 | Headings, ARIA, keyboard; security hardening | TODO | |
| P4-03 | Speed: Core Web Vitals items, local Lighthouse as a guard | TODO | |
| P4-04 | Phase QA run (findings logged) | TODO | |

## Phase 5: Fix and QA loop (TODO)

| ID | Step | Status | Notes |
|---|---|---|---|
| P5-01 | One full QA run on the whole site (self-check first); changed-routes.py save | TODO | |
| P5-02 | Fix passes: fix, re-check the fixed items and the changed files, pixel on the changed routes; until a re-check finds 0 | TODO | |
| P5-03 | Launch prep: runbook, htaccess-live.txt, editing guide | TODO | |
| P5-04 | The developer's go for live | TODO | |

## Phase 6: Launch and live QA (TODO)

| ID | Step | Status | Notes |
|---|---|---|---|
| P6-01 | Launch (runbook, one step at a time), Converter for Media and Contact Form CFDB7 on live | TODO | |
| P6-02 | Live QA, test leads, PageSpeed Insights | TODO | |
| P6-03 | Report, client pack, task comment and stakeholder message | TODO | |

---

## Pages

One row per section; the same words as the figma-to-wordpress progress page. Status: `todo` > `building` > `built`
(static copy at 0, fields, seed) > `checked` (a clean QA run covered it) > `fixed` (it had findings; all fixed and
checked again). Page and Section are short names; render.py makes the slugs.

| Page | Route | Section | Status | Notes |
|---|---|---|---|---|
| Global | | Header | todo | |
| Global | | Footer | todo | |
| Home | `/` | Hero | todo | |
| Thank you | `/thank-you/` | Message | todo | |
| 404 | | Message | todo | |

## QA findings

One list for the whole build, IDs running on (F-001, F-002...). Where: `Page / Section` as in Pages, or a file.
Severity `blocker` (fixed at once), `major` or `minor` (both wait for P5). Status `open` > `fixed` (fixed AND
checked again by a QA run) or `decided` (kept as it is on purpose, with the reason in the finding). Phase names the
QA run that found it (`P2`; in P5 `P5 run 1`, `P5 run 2`): the progress page counts findings per run.

| ID | Phase | Where | Finding | Severity | Status |
|---|---|---|---|---|---|

## Risks to watch

| Risk | Where it bites | Plan |
|---|---|---|
| Parity tools cannot reach the local sites from the agent's shell | P1-03 | Run them where the browser can reach the local site, or use snapshots and the mirror |
| A duplicate PHP function name takes the site down | Every PHP change | Duplicate function check after every save |

## Log

- {{DATE}}: Project started from the convert-to-wordpress skill.
