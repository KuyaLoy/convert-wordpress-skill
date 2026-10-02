# {{SITE_NAME}}: WordPress conversion, sprint plan

Status: **Sprint 0 (planning)**. Written {{DATE}}.
Read with: `CONTENT-MODEL.md` (what gets built), `ARCHITECTURE.md` (how), `SOURCE-NOTES.md` (what the source says),
`../BUILD-MAP.md` (live status, private), `../handoff.md` (session state).

## 1. The team

The agent plays every role, one hat at a time. Builders build, reviewers check, and nobody approves their own work:
the developers hand each task to the Lead developer, and the reviewers (UI to QA) sign the sprint gates. "The
developer" in these files always means the human running the build; the two developer roles below are agent roles.

| Role | Owns | Gate (must pass before the sprint closes) |
|---|---|---|
| **Owner** | Scope: the task tracker's requests, the 1:1 rule, acceptance | Every request in scope for the sprint is met or listed as open; nothing outside scope was added |
| **Manager** | Plan, BUILD-MAP, ceremonies, blockers, handoff, stakeholder updates | BUILD-MAP true (gate.py runs clean), both handoff files current, demo given to the developer |
| **Lead developer** | Architecture, code standards, the sprint backlog, review | Every task reviewed and its findings fixed (fresh-reviewer code review at sprint end); PHPCS clean; php -l; no duplicate functions; every output escaped |
| **Front-end developer** | Static first: markup copied from the golden master, CSS, fonts, images, vanilla JS behaviour | (builds, does not sign) each task self-tested: local diff clean, no console errors |
| **WordPress developer** | Dynamic: ACF field groups and sync, wiring, seeder, CF7, SEO plugin, PHP hooks | (builds, does not sign) each task self-tested: php -l, PHPCS, seeder twice |
| **UI** | Visual parity | Pixel diff within anti-aliasing at every test width for the sprint's pages; no restyled CSS; fonts and images as static |
| **UX** | Behaviour parity, editor experience | Menus, pop-ups, forms, keyboard and reduced motion as static; wp-admin fields in page order with instructions and defaults |
| **Security** | Hardening | No secrets in files or chats; private files blocked; nonces and capability checks; file editing off; input sanitised, output escaped |
| **Tester** | Automated checks | Parity, DOM and text diff clean; seeder second run "same"; no PHP notices or console errors; forms with JS off when in scope |
| **QA** | Proof, as the visitor sees it | The sprint's pages checked in a real browser at phone and desktop widths; launch: live QA ALL PASS, test leads received, report |

How the Lead guides the developers:

- **Sprint planning:** the Lead splits each story into tasks in the sprint backlog (section 7): which partial, which
  fields, which hook, what "done" looks like, who builds it (FE or WP), in what order.
- **Hand-off note:** a developer finishes a task with three lines: what changed (files), how it was tested, anything
  open. Then the Lead reviews it.
- **Review:** the Lead checks every task against ARCHITECTURE.md and the 1:1 rule before it counts as done; at
  sprint end a fresh reviewer (a subagent or a new session, not the author's context) reviews everything changed.
- **Limits:** one task in progress per developer; one sprint at a time; a blocker goes to the Manager, not around
  the plan.
- **Subagents:** when the agent can run subagents, the Lead may give a task card (the backlog row plus the files to
  read) to a developer subagent; the Lead still reviews the result. Without subagents, switch hats explicitly and
  write the hand-off note before reviewing.

Decision rights: the Owner decides scope, the Lead developer the technical approach, the developer (human) every
plugin, password, licence, live step and every sprint sign-off.

## 2. Product goal

Replace the static site with a WordPress site that **looks and behaves exactly the same on every screen size**,
**keeps every URL and SEO signal**, and lets editors **change all content in ACF**, with the forms in
**Contact Form 7**.

Success measures: every static route exists with the same slug, title, description and H1; automated diffs show no
visible difference at every breakpoint; all content editable; leads delivered (Track Delivery: Accepted); no new
404s after launch.

## 3. The life cycle (SDLC), sprint by sprint

| Phase | Where | Output |
|---|---|---|
| Requirements | Intake, the task tracker | Scope, requested pages, tracking, campaign URLs, lead recipients |
| Analysis and design | S0 Planning | SOURCE-NOTES, CONTENT-MODEL, ARCHITECTURE, OLD-SITE-URLS, this plan, the board |
| Build and test | S1 to S6, one at a time | 1:1 pages, fields, forms, SEO, hardening; tested inside each sprint |
| System test | S7 QA and launch prep | Full parity run, old URLs, real phones, runbook, editing guide |
| Release | Launch (RUNBOOK.md) | The site live, rollback ready |
| Verification and handover | Live QA, report | ALL PASS, test leads, the report, both handoff files |

Sprints, in order: S0 Planning, S1 Foundation, S2 the template most pages share, S3 the other fixed templates,
S4 flexible pages, S5 forms and email, S6 SEO / security / performance, S7 QA and launch prep. The stories are on
the board (BUILD-MAP.md).

**One sprint at a time.** The current sprint is the only one with work in progress. Nothing from a later sprint is
started, not even "while waiting"; a blocker is recorded and raised, not worked around by skipping ahead.

### Every sprint runs the same seven steps

1. **Plan.** Restate the sprint goal; check the entry criteria (5.1); the Lead writes the sprint backlog
   (section 7): tasks, acceptance, FE or WP, order; mark the sprint IN PROGRESS.
2. **Build.** Task by task, each section with the per-section workflow (section 4); every task ends with the
   hand-off note and the Lead's review.
3. **Review.** A fresh reviewer (a subagent or a new session) reads everything the sprint changed; fix every real
   finding.
4. **Test.** Parity, DOM, text and SEO diffs for the sprint's pages; the seeder twice (second run "same"); PHPCS,
   php -l, the duplicate function check; forms and email when in scope.
5. **Demo.** Show the developer what the sprint built: the pages (local URLs or screenshots), the diff results, the
   wp-admin screens, anything open.
6. **Retro.** Three lines in the board's Log: keep, change, try. Lessons go to handoff.md too.
7. **Gate.** Each role writes its result in "Sprint gates"; `python3 _plan/tools/build-map/gate.py BUILD-MAP.md`
   must pass; ask the developer for the go; write `go <date>` only when they say it; then
   `gate.py BUILD-MAP.md --close` opens the next sprint.

## 4. Per-section workflow (every section, every time)

1. **Static** (FE). Copy the section's rendered HTML from the golden master into the partial: same tags, classes,
   attributes, order. Copy hardcoded. Diff until it shows no difference.
2. **Model** (WP). Add the fields to the group in `tools/acf/build_field_groups.py` (stable keys); run it.
3. **Sync** (WP). ACF > Field Groups > the group's own Sync link (only changed groups are offered).
4. **Dynamic** (WP). Replace the hardcoded copy with the fields; escape every output.
5. **Seed** (WP). Exporter, then Tools > Seeder for that step.
6. **Test** (FE and WP, then Tester). Visual diff, text, headings, keyboard and ARIA, no PHP notices, no console
   errors.
7. **Clean** (the author). Remove leftovers and debug code; php -l, PHPCS, the duplicate function check.
8. **Review** (Lead). The hand-off note, the diff results and the code; fix, then it counts as done.
9. **Hand off** (Manager). BUILD-MAP rows (page tracker cells `ok`) and handoff.

## 5. Ready and Done

### 5.1 A sprint is ready to start when

- the sprint before it is DONE (gate passed, signed off);
- the decisions it needs are answered (BUILD-MAP Decisions);
- each story has acceptance criteria and the golden-master pages and sections are identified.

### 5.2 A story is done when

Its tasks are reviewed by the Lead, its acceptance criteria hold, its pages are `ok` in all five tracker steps,
PHPCS is clean, and BUILD-MAP and the handoff say so.

### 5.3 A sprint is done when

Every story is DONE, every gate in section 1 passes, the review findings are fixed, the retro is written, gate.py
passes, and the developer said go.

## 6. Every session

- Start: read ai-handoff-summary.md, then run gate.py to see where the sprint stands.
- During: one story at a time; BUILD-MAP updated as stories move.
- Stop: update both handoff files (and the board page after a sprint closes).

## 7. Sprint backlog (the Lead writes it at each sprint's planning)

Replace this table at every sprint planning; keep the finished sprints' tables below it, newest first.

| Task | Story | Dev | Done when | Review |
|---|---|---|---|---|
| (one line per task: the partial, field group, hook or file) | S1-04 | FE / WP | (acceptance in one line) | (Lead: OK, or the findings) |
