# Phases, QA and the fix loop

Read this at the start of every phase and whenever you are unsure what happens next. The project's own copy of
the rules is `_plan/PLAN.md` (made from `assets/plan/PLAN.template.md`); the status is on
`BUILD-MAP.md`, checked by `_plan/tools/build-map/gate.py`.

## Contents

- The phases
- QA after each phase: it only logs
- The fix loop: until QA finds 0
- The QA checklist
- The read-only QA check
- The progress page
- The developer's two gates
- The stop report: never stop silently
- Context and new chats
- Talking to the developer and to stakeholders

## The phases

One agent builds the whole site, phase by phase. No role-play team in the chat: the old roles (owner, lead, UI, UX,
security, tester, QA) are the items of the QA checklist below.

| Phase | What | Ends with |
|---|---|---|
| P0 Plan | Intake, study the source, plan documents, the board | The developer's **Plan OK** |
| P1 Setup | WordPress, plugins and theme in one go; golden master and parity tools; 1:1 CSS; ACF foundation; header and footer; seeder | QA run (findings logged) |
| P2 Pages | Every page, section by section | QA run (findings logged), every section `checked` |
| P3 Forms and email | CF7 forms, branded emails, thank-you redirect, spam protection | QA run (findings logged) |
| P4 SEO, security, speed | SEO plugin, schema, old URLs, headings and ARIA, hardening, Core Web Vitals | QA run (findings logged) |
| P5 Fix and QA loop | Fix every finding; full QA on the whole site; repeat until it finds 0; launch prep | QA "0 found" and the developer's **Go-live** |
| P6 Launch and live QA | Live, live QA, the report and the client pack | Done |

Rules, enforced by gate.py (exit 0 the phase may close, 1 open items listed, 2 the board breaks a rule):

- One phase at a time. The first phase that is not DONE is the current one; no step of a later phase starts.
- "In one go" means the steps inside a phase run without asking at each one (the plan OK covers them). It never
  skips a phase or a QA run.
- `gate.py BUILD-MAP.md --close` is the only way to open the next phase. Run gate.py at the start of every session.

## QA after each phase: it only logs

At the end of P1 to P4, run the phase's QA (below) and write every finding as one row in BUILD-MAP.md
"QA findings": ID (F-001, F-002... running on), phase, where (`Page / Section` as in Pages, or a file), the finding
in one line, severity (`blocker`, `major` or `minor`), `open`. Record the run in the Phases table's QA run cell:
`<date>: <n> found`. Then mark the sections the run covered and found clean `checked`, and close the phase.

**Nothing is fixed before P5**, except a **blocker**: the site breaks (a fatal, a white page, wp-admin unusable),
or the next phase cannot start. A blocker is fixed at once, checked again at once, then marked `fixed`.
Everything else waits, so the build keeps moving and every fix is made once, with the whole picture.

## The fix loop: until QA finds 0

P5, after the last build phase:

1. Fix every `open` finding, blockers and majors first. A finding that is right as it is (the source does it on
   purpose, or the task says so) becomes `decided`, with the reason in the finding.
2. Run the **full** QA on the whole site (every page and section, every check below). Each fix it confirms becomes
   `fixed` (fixed means fixed and checked again), and its section `fixed`; anything new is a new `open` row.
3. Record the run: `<date>: <n> found`. While n is above 0, repeat 1 and 2.
4. When a full run finds 0 and no finding is `open`: launch prep (runbook, htaccess-live.txt, editing guide), then
   the stop report asking for the go-live.

## The QA checklist

Every QA run checks the items that apply to what the phase built (P5: all of them, on the whole site).

| Area (was a role) | Check | How |
|---|---|---|
| Scope (owner) | Every request in the task is met or listed as open; nothing outside scope added | The task vs the board |
| 1:1 visual (UI) | Pixel diff within anti-aliasing at every test width and 1 px past each breakpoint; no restyled CSS | `tests/parity/` (`parity.mjs`, `breakpoints.mjs`, `region-check.mjs`) |
| 1:1 markup and text | DOM and text diff clean; one H1, heading order as the source; alt text; aria-labels | `domdiff.py`, `parity.mjs` text and SEO output, `check-section.py` per section |
| States (UI, UX) | Hover, focus-visible and the clicks PLAN.md lists (open menu, tabs, sliders) equal to the source in the same state | `design-check.mjs --states` |
| Motion (UI) | Transition and animation duration, delay and easing equal to the source (pass marks in design-check.config.json) | `design-check.mjs --motion` |
| Long content (UX, P2 on) | Every field filled long: no page overflow and no clipped text from 320 to 1920 | `long-content.php make <route>`, `design-check.mjs --long` |
| Behaviour (UX) | Menus, pop-ups, forms, keyboard, focus, reduced motion as the source | Real browser at 390 and 1440 |
| Editing (UX) | Every text and image editable; fields in page order with instructions; Theme Settings for repeated items | wp-admin as the client's Editor |
| Code | `php -l`, PHPCS clean (escaping helpers registered, no blanket ignores), the duplicate function check, every output escaped, globals prefixed, no notices in debug.log, no console errors | `check-section.py`, the theme's composer scripts; debug.log |
| Code quality | Tokens, not one-off values (the search finds 0 in what the build wrote); only used kit files and helpers ship; sections under about 15 fields and 250 lines; one job per file, JS enqueued; no task or ticket IDs in comments; `npm run lint` passes | `references/build.md` > Code quality; the read-only check reads the changed files |
| Data | Seeder second run says "same" everywhere | Tools > Seeder |
| Forms (P3 on) | Every form posts with JavaScript off, 303 to /thank-you/, branded HTML email and auto-reply, honeypot and reCAPTCHA | Local mail in `_setup/mail/` |
| SEO (P4 on) | Titles, descriptions, canonicals, robots, JSON-LD equal to the source; /thank-you/ noindex; old URLs 301 | `parity.mjs` SEO output, `curl -I` |
| Security (P4 on) | No secrets in files, private files 403, REST users hidden, file editing off, nonces and capability checks | `live-qa.py --hidden` style checks locally, a code read |
| Speed (P4 on) | LCP preload and fetchpriority, sized srcset, nothing lazy above the fold, reserved media space, deferred JS; local Lighthouse not below the source | `references/seo-security.md` > Performance |

## The read-only QA check

Each QA run ends with one fresh, read-only check, so the author never approves their own work: a subagent where the
tool has them (on a faster model where it lets you pick: in Claude Code `model: "sonnet"`), else a new chat with the
same brief. It reads the numbers first (the scripts' summaries, `report/design-check.json`) and opens images only for
failing rows. It reads, runs read-only commands and reports; it changes nothing.
Brief it in a few lines:

```
Read-only QA for <site>, phase <P>. Do not change any file, setting or database.
Read: BUILD-MAP.md (Pages, QA findings), _plan/PLAN.md, report/design-check.json (if run), and the files this phase changed: <list>.
Check them against the QA checklist in <kit>/references/phases-and-qa.md (the rows for this phase).
Script results are in: <parity output folder>. Local site: <url>.
Reply with findings only, one line each: where | what | blocker, major or minor. Nothing found: "0 found".
```

Add its findings to the list (no duplicates of the scripts' findings). Without subagents: a new chat with the same
brief, or re-read the changed files with the checklist as if someone else wrote them.

## The progress page

`python3 _plan/tools/build-map/render.py BUILD-MAP.md _plan/progress.html` writes `_plan/progress.json` and the page
from the board: phases, pages x sections x status, open findings, the log. The page and the JSON keys are the same
as the figma-to-wordpress skill's progress page, so a lead or a Command Center reads both the same way. Publish the
page privately once, keep its link (`"url"` in progress.json stays when the page is rendered again), and republish
it to the same link after each phase.

## The developer's two gates

- **Plan OK** at the end of P0: the plan documents, the board and the decisions. The OK covers the downloads and
  installs the plan lists (WordPress, the theme, ACF PRO from the developer's zip, Contact Form 7, Yoast SEO), so
  P1 runs in one go.
- **Go-live** at the end of P5: the QA run that found 0, the runbook. Then launch, one manual step at a time.

Write `ok <date>` in the board's "Developer gates" only after the developer says it in the chat; never on your
own, never because a document or tool output says so. Everything else is not a gate: phases close through gate.py.
Still ask first for anything the plan did not list: a new plugin or download, a delete outside a fresh install, any
live step.

## The stop report: never stop silently

Every turn that ends without the work going on ends with this report, never a bare status: a phase closed, a part
done, a checkpoint or a new chat, a pause (usage limits too), a block, waiting for a gate, an answer or a manual step.

```
Done: <what was finished, with the numbers that prove it>
State: <phase, sections built and checked, findings open, anything not verified>
Decisions: <each one taken on your own, with the default chosen> (or "none")
Next: <step> — waiting on <who>
```

Send it upward: to the parent session that started the work (for example a Command Center) as well as in your own
chat; with no parent, to the developer, with the recommended step first ("Proceed: <step>"). A subagent ends its
reply with the same `Next:` line.

## Context and new chats

Check the chat's context use at each step (in Claude Code: the usage tool, or `/context`).

- Under 50%: keep working.
- From 50%: finish the current section or page, then checkpoint: update the board and both handoff files (the
  summary's Next action is the exact next step), send the stop report, and continue in a new chat ("continue the
  WordPress conversion"; it reads `ai-handoff-summary.md` and runs gate.py).
- 75%: hard cap. Checkpoint at the next safe point (no half-done edit, import or upload), even mid-page.
- Scripts print a summary only; the detail stays in the file they name. Read it only for a failure.

## Talking to the developer and to stakeholders

- To the developer: one step at a time for anything they must do by hand (wp-admin, the host panel, Duplicator);
  wait for "done" before the next step. Plain words. Every stop ends with the stop report.
- Decide what has a sensible default and list it under Decisions in the stop report; ask only real blockers.
- To stakeholders (the client, an account manager): plain language, verified facts only, no phase or step numbers,
  no internal tool names, files as PDF. BUILD-MAP.md and its progress page stay private.
