# {{SITE_NAME}}: WordPress conversion, build plan

Status: **P0 Plan**. Written {{DATE}}.
Read with: `CONTENT-MODEL.md` (what gets built), `ARCHITECTURE.md` (how), `SOURCE-NOTES.md` (what the source says),
`../BUILD-MAP.md` (status and QA findings, private), `../handoff.md` (session state).
The kit's rules: `<kit>/references/phases-and-qa.md`.

## 1. Goal

Replace the static site with a WordPress site that **looks and behaves exactly the same on every screen size**,
**keeps every URL and SEO signal**, and lets editors **change all content in ACF**, with the forms in
**Contact Form 7**. Optimized by default: SEO standard, PageSpeed Insights aimed at a pass (not a must; the design
is never changed for a score).

Success measures: every static route exists with the same slug, title, description and H1; automated diffs show no
visible difference at every breakpoint; all content editable; leads delivered with the branded emails; no new 404s
after launch; QA finds 0 before go-live.

## 2. Phases

| Phase | Output for this site |
|---|---|
| P0 Plan | SOURCE-NOTES, CONTENT-MODEL, ARCHITECTURE, OLD-SITE-URLS, this plan, the board; the developer's Plan OK |
| P1 Setup | Local WordPress at {{LOCAL_HOST}} (admin from the profile), plugins, theme, golden master, parity tools, 1:1 CSS, ACF foundation, header and footer, seeder |
| P2 Pages | Every page on the board, section by section |
| P3 Forms and email | Every form in CF7, branded lead email and auto-reply, /thank-you/, spam protection |
| P4 SEO, security, speed | SEO plugin seeded, JSON-LD, old URLs, headings and ARIA, hardening, Core Web Vitals |
| P5 Fix and QA loop | Every finding fixed; full QA until it finds 0; runbook, editing guide; the developer's Go-live |
| P6 Launch and live QA | Live (Converter for Media and Contact Form CFDB7 added there), live QA, report, client pack |

QA after each phase only logs findings in BUILD-MAP.md; only a blocker is fixed before P5.

## 3. Per-section workflow (every section, every time)

1. **Static.** Copy the section's rendered HTML from the golden master into the partial: same tags, classes,
   attributes, order. Diff until it shows no difference.
2. **Model.** Add the fields to the group in `tools/acf/build_field_groups.py` (stable keys); run it.
3. **Sync.** `_plan/tools/acf/sync.php` (or the group's Sync link) until nothing is listed under "Sync available".
4. **Dynamic.** Replace the copy with the fields; escape every output.
5. **Seed.** Exporter, then Tools > Seeder for that step.
6. **Check.** Visual, DOM and text diff; one H1 and heading order; no PHP notices; no console errors.
7. **Clean.** php -l, PHPCS, the duplicate function check.
8. **Board.** The section's row `built`; handoff files after each page.

## 4. Done

- A phase is done when gate.py says it may close: every step DONE, its QA run recorded, no open blocker (P0: the
  Plan OK; P5: QA "0 found", no finding open, the Go-live).
- The build is done when the site is live, live QA passes, and the report and client pack are handed over.

## 5. Every session

- Start: read ai-handoff-summary.md, then run gate.py.
- During: one section at a time; the board updated as sections move; context checked at each step (from 50% finish
  the section or page and continue in a new chat; cap 75%).
- Stop: update both handoff files (and the progress page after a phase closes), then send the stop report upward
  (the parent session, else the developer): done, state, decisions taken with the default chosen, and last
  `Next: <step> — waiting on <who>`. Never stop silently.
