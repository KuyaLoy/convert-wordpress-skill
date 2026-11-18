# AI handoff summary: {{SITE_NAME}} WordPress build
Updated: {{NOW}} | By: <AI or tool, and chat or task name if known>
Last change: project created from the convert-to-wordpress skill (new-site.py)
Status: ACTIVE

## Now
- Phase: P0 Plan, IN PROGRESS. Gate: run `python3 _plan/tools/build-map/gate.py BUILD-MAP.md`.
- Waiting on: the developer's Plan OK (with the decisions on BUILD-MAP.md).

## Next action
- Finish `_plan/PLAN.md` (start.py filled its source table; `_plan/analyze.txt` has the full study).

## Verified facts
- BUILD-MAP.md, _plan/ and these handoff files were created by new-site.py [verified {{DATE}}: new-site.py output]

## Key paths
- BUILD-MAP.md: private board (phases, pages and sections, QA findings)
- handoff.md: the full record
- _plan/: plan documents and tools
- _setup/seed/: seed files for Tools > Seeder

## Rules for this project
- One phase at a time; QA after each phase only logs findings; only a blocker is fixed before P5 (the fix loop).
- The developer's gates: the Plan OK and the Go-live (`ok <date>` on the board only after they say it).
- 1:1 with the static site: copy its markup and CSS; fields replace content only. The diff decides.
- Never type passwords, licence keys or API keys (only install-wp.py reads the local admin password, never shown).
- BUILD-MAP is private. Stakeholder updates: plain language, verified facts, no phase numbers.
- After every PHP save: php -l, PHPCS, the duplicate function check. Context from 50%: checkpoint, new chat.

## Open questions
- (none yet)

## Where to look in handoff.md
- History of each change: handoff.md > Changes Made
- What already failed: handoff.md > Failed Attempts
