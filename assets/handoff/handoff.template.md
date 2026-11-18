# Handoff: {{SITE_NAME}} WordPress build

The full record. AI: read `ai-handoff-summary.md` first and open this file only for the section you need.
Update both files after any significant change and before ending a session.
Last updated: **{{DATE}}**, P0 Plan.

---

## Goal

Turn the static site for https://{{DOMAIN}} into WordPress with ACF PRO and Contact Form 7:
- **1:1** with the static site in design and behaviour on every screen size, proven by automated diffs;
- the same URLs, titles, descriptions and redirects, with proper heading order and ARIA;
- every piece of content editable (Theme Settings for anything repeated, ACF on every page);
- optimized by default: SEO standard, PageSpeed Insights aimed at a pass (not a must);
- the requests in the task tracker, and lead emails delivered with the branded templates.

## Current State

- P0 Plan started {{DATE}}, IN PROGRESS. Nothing built yet.
- Phase gate: run `python3 _plan/tools/build-map/gate.py BUILD-MAP.md` (exit 0 = may close, 1 = open items,
  2 = the board breaks the one-phase-at-a-time rule).
- QA findings: none yet (BUILD-MAP.md > QA findings).
- Local: `{{SITE_DIR}}`, http://{{LOCAL_HOST}} (environment local).

## Active Files

| File | What it is |
|---|---|
| `ai-handoff-summary.md` | Short AI brief of this file. Read first |
| `BUILD-MAP.md` | Private board: phases, pages and sections, QA findings, the developer's gates |
| `_plan/` | BUILD-PLAN, CONTENT-MODEL, ARCHITECTURE, SOURCE-NOTES, OLD-SITE-URLS, tools/ |
| `_setup/seed/` | Seed files for Tools > Seeder |
| `_setup/launch/` | RUNBOOK.md, htaccess-live.txt, report.html |
| `wp-content/themes/{{THEME}}/` | The theme (<!-- starter:tw -->`theme/` is what WordPress loads: <!-- /starter:tw -->`includes/`, `acf-json/`; `tests/parity/`) |

References (read only): the static source folder and its build, the old site if any.

## Changes Made

### {{DATE}}, P0 Plan

- Project created from the convert-to-wordpress skill (new-site.py).

## Failed Attempts

(Nothing yet. Every entry: date, what was tried, what happened, what works instead.)

## Next Steps

1. Study the source: `python3 _plan/tools/analyze-source.py <static source>`; set the golden master.
2. Write the plan docs, list every page and section on BUILD-MAP.md, settle the decisions.
3. Ask for the Plan OK (the stop report lists the P1 downloads), then P1 Setup in one go.
