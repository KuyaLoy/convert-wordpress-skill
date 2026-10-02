# Handoff: {{SITE_NAME}} WordPress build

The full record. AI: read `ai-handoff-summary.md` first and open this file only for the section you need.
Update both files after any significant change and before ending a session.
Last updated: **{{DATE}}**, Sprint 0 (planning).

---

## Goal

Turn the static site for https://{{DOMAIN}} into WordPress with ACF PRO and Contact Form 7:
- **1:1** with the static site in design and behaviour on every screen size, proven by automated diffs;
- the same URLs, titles, descriptions and redirects, with proper heading order and ARIA;
- every piece of content editable (Theme Settings for anything repeated, ACF on every page);
- the requests in the task tracker, and lead emails delivered as the static site delivered them.

## Current State

- Sprint 0 (planning) started {{DATE}}, IN PROGRESS. Nothing built yet.
- Sprint gate: run `python3 _plan/tools/build-map/gate.py BUILD-MAP.md` (exit 0 = may close, 1 = open items,
  2 = the board breaks the one-sprint-at-a-time rule).
- Local: `{{SITE_DIR}}`, http://{{LOCAL_HOST}} (environment local).

## Active Files

| File | What it is |
|---|---|
| `ai-handoff-summary.md` | Short AI brief of this file. Read first |
| `BUILD-MAP.md` | Private status board (the developer only) |
| `_plan/` | SPRINT-PLAN, CONTENT-MODEL, ARCHITECTURE, SOURCE-NOTES, OLD-SITE-URLS, tools/ |
| `_setup/seed/` | Seed files for Tools > Seeder |
| `_setup/launch/` | RUNBOOK.md, htaccess-live.txt, report.html |
| `wp-content/themes/{{THEME}}/` | The theme (<!-- starter:tw -->`theme/` is what WordPress loads: <!-- /starter:tw -->`includes/`, `acf-json/`; `tests/parity/`) |

References (read only): the static source folder and its build, the old site if any.

## Changes Made

### {{DATE}}, Sprint 0

- Project created from the convert-to-wordpress skill (new-site.py).

## Failed Attempts

(Nothing yet. Every entry: date, what was tried, what happened, what works instead.)

## Next Steps

1. Study the source: `python3 _plan/tools/analyze-source.py <static source>`; set the golden master.
2. Write the plan docs and settle the decisions in BUILD-MAP.md.
3. Close S0 through its gate (review, demo, retro, every role's gate, the developer's go), then start S1.
