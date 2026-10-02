# AI handoff summary: {{SITE_NAME}} WordPress build
Updated: {{DATE}} | By: <agent and chat or task name>
Last change: project created from the convert-to-wordpress skill
Status: ACTIVE

## Now
- Sprint: S0 Planning, IN PROGRESS. Gate: not checked (`python3 _plan/tools/build-map/gate.py BUILD-MAP.md`).
- Doing: study the source, plan docs, decisions.
- Waiting on: the developer's answers to the open decisions in BUILD-MAP.md.

## Next action
- Run `python3 _plan/tools/analyze-source.py <static source>` and write `_plan/SOURCE-NOTES.md`.

## Verified facts
- (none yet) [verified YYYY-MM-DD: how]

## Key paths
- BUILD-MAP.md: private board. handoff.md: the full record
- _plan/: plan docs and tools. _setup/seed/: seed files. wp-content/themes/{{THEME}}/: the theme

## Rules for this project
- One sprint at a time: no story from a later sprint starts before the current sprint's gate passes and the
  developer says go (`gate.py --close` opens the next sprint).
- 1:1 with the static site: copy its markup and CSS; fields replace content only. The diff decides.
- Static first, then dynamic: every section is copied as static HTML, matched, then wired to ACF.
- Never type passwords, licence keys or API keys. Ask before installing any plugin.
- BUILD-MAP is private. Stakeholder updates: plain language, verified facts, no sprint numbers.
- After every PHP save: php -l, PHPCS, the duplicate function check.

## Open questions
- (who decides, by when)

## Where to look in handoff.md
- History of each change: handoff.md > Changes Made
- What already failed: handoff.md > Failed Attempts
