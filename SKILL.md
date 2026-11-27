---
name: convert-to-wordpress
description: Converts any existing website (plain HTML, Next.js, React, Astro, Vue and other stacks) into a 1:1 WordPress site with the same design, URLs, SEO and tracking, every page editable in ACF PRO and every form in Contact Form 7. Phase by phase (plan, setup in one go, pages section by section, forms and email, SEO/security/speed), QA after each phase, one fix loop until QA finds 0, then go-live, live QA and the report. Use whenever a site built outside WordPress has to be rebuilt in WordPress, for requests like "convert this site to WordPress", "move or migrate my website to WordPress", "rebuild it in WordPress", "HTML (or Next.js, React, Astro, Vue) to WordPress", "make the site editable in WordPress" or "WordPress conversion".
license: GPL-2.0-or-later
---

# Convert a website to WordPress, 1:1

The site already exists: as code, as a build, or live. The job is to rebuild it in WordPress so it looks and
behaves the same at every screen size, keeps every URL and SEO signal, and lets editors change everything in
wp-admin: content in ACF PRO, forms and emails in Contact Form 7. Optimized by default: SEO standard, PageSpeed
Insights aimed at a pass (a target, not a must). Any stack, any kind of
business, any country and language.

Its lessons come from real builds: a 36-page Next.js export, a PHP and Tailwind landing page, and a clinic site
taken live on cPanel.

**Open first:** an existing project: `ai-handoff-summary.md`, then gate.py (Start: intake). A new one: Start:
intake below. Each phase: `references/phases-and-qa.md` at its start. Not in Claude Code (Codex, Antigravity, T3
Code, others): `references/agents.md` > Per tool, for what each Claude-only step becomes there.

**The yardstick for every choice:** fast, quality, best practice, low usage, straightforward: seen from the
client's side. The client is usually not technical: what they see, read, edit and receive must be simple and plain.

## The kit

Paths are relative to this file's folder:

| Path | What |
|---|---|
| `references/` | The detailed guides. Read only the one you need, when you need it (table below) |
| `scripts/` | The tools. `new-site.py` copies them into the project's `_plan/tools/` |
| `assets/` | Templates: theme code, seed examples, plan documents, the board, handoff, launch, report |
| `profile.local.json` | The developer's or agency's defaults (never committed); start from `profile.example.json` |

No `scripts/` folder next to this file (a copy saved inside a chat app)? The kit is a clone of
https://github.com/KuyaLoy/convert-wordpress-skill: ask the developer where theirs is (none yet: ask, then clone it).

| Read | When |
|---|---|
| `references/phases-and-qa.md` | At the start of every phase: the phases, QA that logs, the fix loop, the checklist, context; > The progress page before the first render |
| `references/wordpress-essentials.md` | The WordPress rules in one page (plugins, setup, theme, fields, forms, SEO, security, speed, launch) |
| `references/setup.md` | Intake, the database, WordPress in one go, the starter theme, the plugins |
| `references/source-types.md` | Studying the source, the golden master for each stack, Tailwind, languages |
| `references/build.md` | P1 and P2: CSS, head, ACF, media, templates, the seeder, parity checks |
| `references/forms-email.md` | P3: Contact Form 7, the email, spam protection, the chat |
| `references/seo-security.md` | P4, and the security basics from P1 |
| `references/launch.md` | Go-live with Duplicator, other hosts, changes after launch |
| `references/qa-report.md` | Live QA, test leads, the report, the task comment |
| `references/handover.md` | After live QA: the client pack (website sheet, editing guide, message) |
| `references/gotchas.md` | Before anything risky (search it for the step's word, do not read it whole). Add every new lesson there |
| `references/agents.md` | Each agent; beginner mode; fewer tokens; which model for which step; > Per tool when not in Claude Code |
| `references/phase-steps.md` | At the start of each phase: that phase's steps (one section, not the whole file) |
| `references/scripts.md` | Every script and what it does, when you need one this file does not name |
| `references/glossary.md` | Plain-word meanings for newcomers |

## Rules (always)

1. **1:1 above all.** The golden master (the site exactly as visitors get it) is the design. Copy its markup and
   CSS; fields replace content, never structure, classes or order. The diffs decide, not the eye.
2. **Static first, then dynamic.** Every section is copied as static HTML and diffed to zero before it gets fields.
3. **The task decides.** The task tracker's requests are the scope; where they differ from this skill's defaults,
   the task wins. Campaign and landing page URLs never change.
4. **Two gates, then straight through.** The developer's **Plan OK** covers every download and install the plan
   lists (WordPress, the theme, ACF PRO from their zip, Contact Form 7, Yoast SEO), so setup runs in one go. Ask
   first only for what the plan did not list, a delete outside a fresh install, and every live step (one at a time);
   the **Go-live** is the second gate. Decide what has a sensible default and list it in the stop report.
5. **Never type a password, licence key or API key**, with one exception: the developer's default local admin
   password, which `install-wp.py` reads from `profile.local.json` (`local_admin`) for a local site only and never
   prints. Live admins get their own strong password, typed by the developer; reports say `[PASTE PASSWORD HERE]`.
   ACF PRO's key: the developer puts it once in `profile.local.json` (`acf_pro_license`), and make-wp-config.py
   writes it into each local wp-config (never printed), or pastes it into wp-config (`ACF_PRO_LICENSE`). Not on live
   unless the developer chooses.
6. **One phase at a time; QA only logs.** After each phase QA writes its findings in one list on the board; nothing
   is fixed before the fix loop except a blocker (the site breaks, or the next phase cannot start). `gate.py`
   opens the next phase.
7. **Manual steps** for the developer (wp-admin, the host panel, Duplicator): one at a time, then wait for "done".
8. **Handoff files** (`handoff.md`, `ai-handoff-summary.md` at the project root): update both after every
   significant change and before stopping. A new session reads the summary first.
9. **Private:** BUILD-MAP.md and its board page, `_plan/`, `_setup/`, the handoff files. Anything for the client or
   a stakeholder: plain language, verified facts only, no phase or step numbers, files as PDF.
10. **Read only:** the source folder and the golden master. Build or `npm install` only in a copy.
11. **Code:** every global prefixed (`<prefix>_`); PHP 8.1 to 8.4; escape at output, sanitise input, nonces and
    capability checks. After every PHP save: `php -l`, PHPCS and the duplicate function check. What the build writes
    itself uses tokens, never one-off values; only what the site uses ships; a section past about 15 fields or 250
    lines is split; JS is enqueued, never inline; comments say why, never a task or ticket ID. Every phase gate:
    PHPCS with the kit's escaping helpers registered (no blanket ignores), `npm run lint` (ESLint and Prettier)
    and the read-only code review (`references/build.md` > Code quality).
12. **Live:** surgical changes only, a rollback copy of every replaced file, PHP files complete before upload,
    theme zips with 0644 files and 0755 folders.
13. **Replies** follow the profile's `level`: `new` = plain words, each term explained once
    (`references/glossary.md`), exact clicks, the `Next:` line (rule 15) in plain words at the end; `developer` =
    short (asked at intake).
14. **Spend less:** read the summary, not whole files; never read node_modules, minified, vendor or lock files;
    scripts copy markup and print summaries (detail stays in files); screenshots only as cropped failures. Context:
    from 50% finish the section or page, checkpoint (board, handoff files) and continue in a new chat; cap 75%.
    No context meter (Antigravity, T3 Code): checkpoint at every page and phase end (`references/agents.md` >
    Per tool).
15. **Never stop silently.** Every turn that ends without the work going on (a phase closed, a part done, a
    checkpoint or new chat, a pause, a block, waiting for a go or a manual step) ends with a short stop report, never
    a bare status: what was done, the state, every decision taken on your own (with the default chosen), and last
    `Next: <step> — waiting on <who>`. Send it to whoever started the work: a parent session (for example a Command
    Center) as well as your own chat; with no parent, the developer, with the recommended step first ("Proceed:
    <step>"). Every role and subagent reports upward this way; nobody waits unreported.
16. **Kit files as shipped; checks with their output.** Kit files (the theme's includes, the must-use files, the
    tools) are copied with the prefix swap only (`new-site.py` does it); any site change to a kit file is listed with
    its reason (the file, the change, why) in the task's notes.md, or handoff.md > Changes Made without one. A check
    is reported only with its output (the tool's OK or FAIL line and counts, pasted): never "passes", "seeded" or
    "0 private" from memory.
17. **Leads: CFDB7 only.** Leads are stored only by Contact Form CFDB7, installed on live (the kit's plugin list).
    Never create a database table, custom post type, option rows, files or an admin page of your own for enquiries
    or submissions; local mail capture (_setup/mail) is local only. `self-check.py` flags it (`lead-storage`).

## The phases

One agent builds the whole site. No role-play team in the chat: the old roles are the QA checklist
(`references/phases-and-qa.md`).

| Phase | What | Ends with |
|---|---|---|
| P0 Plan | Intake, study the source, plan documents, the board | The developer's **Plan OK** |
| P1 Setup | WordPress, plugins and theme in one go; golden master; 1:1 CSS; ACF; header and footer; seeder | QA logs |
| P2 Pages | Every page, section by section | QA logs |
| P3 Forms and email | CF7 forms, branded emails, thank-you, spam protection | QA logs |
| P4 SEO, security, speed | SEO plugin, schema, old URLs, ARIA, hardening, Core Web Vitals | QA logs |
| P5 Fix and QA loop | One full QA run; fix passes, each re-checking what changed, until a re-check finds 0; launch prep | The developer's **Go-live** |
| P6 Launch and live QA | Live, live QA, the report and the client pack | Done |

**QA per phase** = the self-check first (`self-check.py`: the build fixes what it finds before QA starts) + gate.py
+ the parity, SEO and design checks + one fresh read-only check against the QA checklist (a subagent, or a new chat
in tools without subagents; a faster model where the tool lets you pick). Findings go in BUILD-MAP.md "QA findings"
(`open` > `fixed` after a re-check, or `decided`).
**All rules at the plan:** P0 decides the forms and where leads go, placeholders, the live plugin checklist and the
leads portal (only when the profile names one); a skill update during a task applies at the next site or phase boundary, never inside a QA run.

```
python3 _plan/tools/build-map/gate.py BUILD-MAP.md           # 0 may close, 1 open items listed, 2 a rule broken
python3 _plan/tools/build-map/gate.py BUILD-MAP.md --close   # opens the next phase
python3 _plan/tools/build-map/render.py BUILD-MAP.md _plan/progress.html   # progress page + progress.json
python3 _plan/tools/report/self-check.py <wp_root> --url <local url> --profile <kit>/profile.local.json  # before every QA run
```

Run gate.py at the start of every session. Write `ok <date>` in "Developer gates" only after the developer says it in
the chat. After `--close`: update both handoff files. The progress page: update the board's "## Now" lines, render
and push at every unit end (a page built, a QA run collected, a fix batch, a site done) and every stop; before a long
step (a QA run, a full pixel run) write Now and push first. In Claude the page is live (the artifact database:
render.py writes the rows, ArtifactData sends them, the open page updates itself); elsewhere the static page is a
local file the developer keeps open: `render.py ... --refresh 30 --open` (references/phases-and-qa.md > The progress
page). Resume short: checkpoint at a page, site or phase end with the exact next step; a resume re-checks only what
can have changed. **Running, not stopped:** a turn that ends while its own work keeps running (a background command,
a subagent, a check) starts its last message, its recap and the progress page's Now line with `RUNNING, not stopped:
<what>, started HH:MM; I continue by myself when it finishes.` (the time from the clock); a real stop never says
RUNNING, it says what it waits on. **The title too** (Claude desktop app: `set_session_title` with "self";
Antigravity: its conversation title; other tools skip it): the chat keeps its state at the front of its own title,
one call when the state changes, the rest unchanged: `▶ RUNNING | <title>` while it or its own background work runs,
`⏸ WAITING on <who> | <title>`, `✋ BLOCKED | <title>`, `✓ DONE | <title>` (also in review); never for anything else.

## Start: intake

Open `references/phase-steps.md` > Start: intake. An existing project: the summary, gate.py, the Next action. A new
one: `doctor.py`, `start.py`, `new-site.py --plan-only`; ask once, in one batch, only what is still open.

## What each phase must prove

Open `references/phase-steps.md` > the phase's heading at the start of each phase: its steps, commands and details.
A phase closes only through gate.py, with QA's findings logged (rule 6). At its close, report each item as
`Pass|Fail | item | evidence`; evidence (in brackets) is the tool's output, pasted (rule 16); none is Fail.

- **P0 Plan (no code):** `PLAN.md`, `CONTENT-MODEL.md`, `OLD-SITE-URLS.md`; every page and section on the board
  (gate.py); forms and where leads go, placeholders, the live plugin checklist, the leads portal, the recommended
  additions (PLAN.md); **Plan OK** (`ok <date>`).
- **P1 Setup:** WordPress, ACF PRO, CF7, Yoast SEO active (one `setup.py` run OK); theme active (PHPCS 0); golden
  master against itself and swap test 0.000% (parity, swaptest.py); nothing to sync (sync.php); seeder second run
  "same"; header and footer 0 (region-check.mjs, domdiff.py).
- **P2 Pages:** every section static, diff 0 before its fields, then `check-section.py` OK and the row `built`;
  states, motion, long content within their marks (design-check.mjs); thank-you 200 noindex, 404 page 404
  (curl -I); every placeholder on the board (text-check.py placeholders).
- **P3 Forms and email:** every form, JavaScript off, answers 303 to `/thank-you/` (curl); branded HTML email,
  auto-reply, honeypot, reCAPTCHA v3, the Lead source table (`_setup/mail/`, the markup); a leads portal only when
  the profile names one (Theme Settings group), never sent from local or staging.
- **P4 SEO, security, speed:** head tags and JSON-LD equal to the source (seodiff.py 0); `/thank-you/` noindex, old
  URLs 301, private files 403, REST users hidden (curl -I); one H1, heading order, aria-labels, alt
  (check-section.py); local Lighthouse not below the source.
- **P5 Fix and QA loop:** one full QA run, then a re-check with 0 found and none `open` (gate.py); clean-up
  (text-check.py oneoff, self-check.py 0); `RUNBOOK.md`, `htaccess-live.txt`, the editing guide; **Go-live**
  (`ok <date>`).
- **P6 Launch:** each manual step one at a time (the developer's "done"); the package (package.py output);
  `installer.php` 404 (curl -I); production, debug off (wp-config); the live plugin checklist (RUNBOOK section 4,
  plugin-check.py --env live); a failed check rolled back.
- **P6 Live QA and the report:** `live-qa.py`, track.mjs OK; PageSpeed Insights mobile and desktop (scores as
  measured); three test leads (the developer's confirmation); `report.html` (`text-check.py fill` OK); the PDF,
  client pack, task comment and stakeholder message.

## Scripts

Every script, with what it does: `references/scripts.md`. Run them with the `python3` (or `node`)
command doctor.py printed, from any shell.

## Done means

Every route 1:1 and editable; forms and emails proven on live; tracking and the conversion proven; old URLs
redirect; installer and private files not public; any ACF PRO licence active, the fields menu visible; every item of the live
plugin checklist ticked (RUNBOOK section 4); QA found 0 before go-live; every phase closed through gate.py; the board, handoff files and gotchas current; the
report PDF, the client pack, the task comment and the stakeholder message handed to the developer.
