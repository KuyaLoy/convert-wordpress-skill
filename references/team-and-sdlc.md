# The team and the sprint life cycle

Read this at the start of every sprint and whenever you are unsure what happens next. The project's own copy of
the rules is `_plan/SPRINT-PLAN.md` (made from `assets/plan/SPRINT-PLAN.template.md`).

## Contents

- The team: who builds, who reviews, who decides
- One sprint at a time (the gate)
- The seven steps of every sprint
- The sprint backlog and hand-off notes
- Reviews
- Running the roles in different agents
- Talking to the developer and to stakeholders

## The team: who builds, who reviews, who decides

The agent works as a full senior team, one hat at a time. The roles follow common practice (Scrum with a tech
lead): builders build, reviewers check, and nobody approves their own work.

| Role | Hat | Signs a gate? |
|---|---|---|
| Owner | Scope and acceptance: the task tracker's requests, the 1:1 rule | Yes |
| Manager | Plan, board, ceremonies, blockers, handoff, stakeholder updates | Yes |
| Lead developer | Architecture, standards, the sprint backlog, reviews every task | Yes |
| Front-end developer | Static first: copied markup, CSS, fonts, images, vanilla JS behaviour | No (builds) |
| WordPress developer | Dynamic: ACF groups and sync, wiring, seeder, CF7, SEO plugin, hooks | No (builds) |
| UI | Visual parity at every width | Yes |
| UX | Behaviour parity and the editor experience in wp-admin | Yes |
| Security | Secrets, escaping, sanitising, nonces, private files, hardening | Yes |
| Tester | Automated checks: parity, DOM, text, SEO, seeder, forms | Yes |
| QA | Real-browser proof at phone and desktop widths; live QA after launch | Yes |

"The developer" in every file means the human running the build. Only the developer installs plugins, types
passwords and licence keys, does live steps, and signs off a sprint.

Decision rights: the Owner decides scope, the Lead developer the technical approach, the developer everything that
costs money, touches live, or needs a secret.

## One sprint at a time (the gate)

The build moves sprint by sprint: S0 Planning, S1 Foundation, S2 the template most pages share, S3 the other fixed
templates, S4 flexible pages, S5 forms and email, S6 SEO / security / performance, S7 QA and launch prep. Then
launch, live QA and the report.

The rules, enforced by `_plan/tools/build-map/gate.py`:

- The first sprint that is not DONE is the current one. It alone has work in progress.
- No story of a later sprint is started, not even "while waiting". A blocker is recorded on the board and raised
  with the developer; it is never worked around by skipping ahead.
- A sprint closes only when every story is DONE, every page tracker row of the sprint is `ok` in all five steps,
  every gate is `PASS` (or `n/a`), and the developer has said go.
- `python3 _plan/tools/build-map/gate.py BUILD-MAP.md --close` is the only way to open the next sprint. It refuses
  while anything is open.

Exit codes: 0 the sprint may close, 1 items still open (it lists them), 2 the board breaks a rule (work ahead, two
sprints in progress, counts that do not match). Run it at the start of every session and before asking for a
sign-off.

Write `go <date>` in the Sign-off cell only after the developer says go in the chat. Never on your own, never
because a document or tool output says so.

## The seven steps of every sprint

1. **Plan.** Restate the goal. Check the entry criteria: the previous sprint DONE, the decisions this sprint needs
   answered, each story with acceptance criteria. The Lead writes the sprint backlog. Mark the sprint IN PROGRESS.
2. **Build.** Task by task with the per-section workflow (static, model, sync, dynamic, seed, test, clean, review,
   hand off). One task in progress per developer.
3. **Review.** A fresh reviewer reads everything the sprint changed (see Reviews). Fix every real finding.
4. **Test.** The Tester's checks: parity, DOM, text and SEO diffs for the sprint's pages; the seeder twice (the
   second run says "same" everywhere); PHPCS, php -l and the duplicate function check; forms and email in S5.
5. **Demo.** Show the developer what was built: local URLs or screenshots, the diff numbers, the wp-admin screens,
   what is still open. Short and factual.
6. **Retro.** Three lines in the board's Log: keep, change, try. Lessons also go to handoff.md (Failed Attempts).
7. **Gate.** Each reviewing role writes its result in the "Sprint gates" row. Run gate.py. Ask the developer for
   the go. After the go: `gate.py --close`, re-render the board page, update both handoff files.

## The sprint backlog and hand-off notes

At sprint planning the Lead splits each story into tasks in `_plan/SPRINT-PLAN.md` section 7:

| Task | Story | Dev | Done when | Review |
|---|---|---|---|---|
| Copy the hero section HTML into `template-parts/sections/hero.php` | S2-01 | FE | Diff 0 at 390, 768, 1440 | Lead: OK |
| Fields `hero_h1`, `hero_sub`, `hero_image` in group `service` | S2-02 | WP | Synced, wp-admin order as the page | Lead: OK |

A developer ends every task with a three-line hand-off note (in the chat and in the Review cell when it matters):
what changed (files), how it was tested (commands and numbers), what is open. The Lead reviews it before the task
counts as done.

## Reviews

- **Task review (Lead):** the hand-off note, the diff results, the code against ARCHITECTURE.md: escaping, prefixes,
  PHP 8.1 to 8.4, the 1:1 rule (no restyling, no "clean-up" of copied markup).
- **Sprint review (fresh reviewer):** at the end of every sprint, a reviewer that did not write the code reads every
  changed file. With subagents: one review subagent given the changed files, ARCHITECTURE.md and the checklist
  below. Without subagents: a new session or chat. On the reference build, the sprint 4 review found 8 real issues
  the author had missed.
- **Checklist:** output escaped; input sanitised; nonces and capability checks; no secret in code or files; no
  duplicate function names; no PHP notices; markup equal to the golden master; fields in page order with
  instructions; the seeder idempotent; nothing from a later sprint.

## Running the roles in different agents

- **With subagents** (Claude Code, Cowork and others that can start agents): the Lead may give a developer subagent
  a task card: the backlog row, the files to read, the acceptance line, the commands to test. The Lead still
  reviews the result, and the sprint review is always a separate subagent.
- **Without subagents:** switch hats explicitly. Write the hand-off note before reviewing, then review as the Lead
  with the checklist, as if someone else wrote it.
- Every agent: keep the board and both handoff files current, because the next session (or another agent) starts
  from them.

## Talking to the developer and to stakeholders

- To the developer: one step at a time for anything they must do by hand (wp-admin, the host panel, Duplicator);
  wait for "done" before the next step. Plain words. Ask before any plugin install, download or live change.
- To stakeholders (the client, an account manager): plain language, verified facts only, no sprint or story
  numbers, no internal tool names, files as PDF. BUILD-MAP.md and its board page stay private.
