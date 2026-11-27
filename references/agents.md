# Running the skill in your agent

The skill follows the open Agent Skills format (SKILL.md plus `references/`, `scripts/` and `assets/`), so any agent
that reads skills can run it. Paths in SKILL.md are relative to the skill folder.

## Contents

- Where the skill lives, and updating it
- Per tool: Claude Code, Codex, Antigravity, T3 Code
- What the machine needs
- Asking the developer
- Replies: beginner mode
- Spend fewer tokens
- Shells, files and the browser
- Subagents
- Agents without skill support
- Picking up another agent's work

## Where the skill lives, and updating it

The folder must be named `convert-to-wordpress` (the `name` in SKILL.md; Cursor and Cline refuse a skill whose
folder and name differ). SKILL.md's frontmatter has only `name`, `description` and `license`, so every tool reads
it, and its steps are plain words: where a step needs something only some tools have (subagents, a question tool,
a parent session), it says what to do without it.

| Agent | Personal (all projects) | One project |
|---|---|---|
| Claude Code | `~/.claude/skills/convert-to-wordpress/` | `.claude/skills/convert-to-wordpress/` |
| Codex | `~/.agents/skills/convert-to-wordpress/` | `.agents/skills/convert-to-wordpress/` |
| Cursor | `~/.cursor/skills/` or `~/.agents/skills/` | `.cursor/skills/` or `.agents/skills/` (it also reads `.claude/skills/`) |
| Antigravity and Antigravity CLI (the CLI replaced Gemini CLI on 18 Jun 2026) | `~/.gemini/config/skills/` | `.agents/skills/` |
| OpenCode | `~/.config/opencode/skills/` (it also reads `~/.agents/skills/` and `~/.claude/skills/`) | `.opencode/skills/` |
| Cline | `~/.cline/skills/` (each skill is also a slash command) | see Cline's docs |
| Devin Desktop (was Windsurf) | `~/.config/devin/skills/` or `~/.agents/skills/` | see Devin's docs |
| Grok Build and others that read skills | `~/.agents/skills/` (check the tool's docs) | `.agents/skills/` |
| T3 Code | the folder of the agent it runs (Claude Code or Codex above; Antigravity's folder is linked in) | the same |
| Claude apps (claude.ai, Cowork) | Upload the folder as a skill (zipped), or save it from a skill card | |

Install by cloning the repo into one of those folders. The developer's own defaults go in `profile.local.json` next
to SKILL.md (never committed).

Updating: `/update-convert-wordpress-skill` (added once with `python3 <kit>/scripts/update.py --add-command`), or
when the developer asks to update the skill: `update.py --check` first (installed and newest version, what is
new), then ask (it downloads), then `update.py`. A git clone updates with `git pull --ff-only` and stops on local
edits; any other install gets the release zip after a backup in `_backups/`; `profile.local.json` is kept. A new
chat reads the new version. A copy saved in a Claude app updates by uploading the new version there.

## Per tool: Claude Code, Codex, Antigravity, T3 Code

SKILL.md names the Claude step; in another tool do this instead (open this section whenever a step names a Claude
tool: an Artifact, a question tool, a subagent, Claude in Chrome, the context meter, the chat title). T3 Code runs
Claude Code, Codex or Antigravity underneath: use that agent's column (in T3, Antigravity gets no hooks or custom
agents).

| Step | Claude Code (CLI, desktop app) | Codex | Antigravity | Any other agent |
|---|---|---|---|---|
| Load the skill | Automatic from the description, or `/convert-to-wordpress` | Automatic, or `$convert-to-wordpress` or `/skills` | The model decides from the description; `/convert-to-wordpress` in the App; in T3 say "use the convert-to-wordpress skill" in words | "Read `<path>/convert-to-wordpress/SKILL.md` and follow it" |
| Ask the developer (intake, gates) | The question tool (AskUserQuestion) | `request_user_input` | Numbered options in the text, the recommended one first, then wait | A numbered list, then wait |
| The fresh read-only QA check | A subagent | A subagent (`spawn_agent`) | A subagent (`invoke_subagent`), not a new conversation | A new chat with the QA brief |
| Browser steps (installer, wp-admin, live checks) | Claude in Chrome or the desktop app's browser pane | The in-app browser (`browser_use`) | The lead's Chrome through the chrome-devtools MCP (zoho-command-center 2.10.2 sets it up); list the pages first; act only on the task's own site tabs; the built-in browser pane only as a fallback | The kit's Playwright scripts; else the URL and the exact clicks for the developer |
| The progress page | The Artifact, live with the database (`references/phases-and-qa.md`) | The local file: `render.py BUILD-MAP.md _plan/progress.html --refresh 30 --open`, same content | The same local file | The same local file |
| Context used | Desktop app: the usage tool; CLI: `/context` | `/status` | No meter: checkpoint at every page end and phase end | The tool's meter if it has one, else as Antigravity |
| The chat's state in its title | Desktop app: `set_session_title` with "self" | Skip (no title tool) | The conversation's title | Skip |
| Hooks | None needed: the skill runs without hooks | None needed | None needed | None needed |

- The progress page as a local file: `--open` opens it once in the default browser; `--refresh 30` makes the open
  tab reload itself every 30 seconds, so each render shows without a click. A lead or a Command Center reads
  `_plan/progress.json` (the same keys as the published page).
- Test leads on live (`references/qa-report.md`): with the developer's OK, the browser tool and the real submit
  button. reCAPTCHA can score an automated browser as a bot: a "spam" answer there is not a site bug; the developer
  sends that lead from their own browser (no AI extension) and the check continues.
- Codex and Antigravity: a subagent, not a new chat or conversation, for the QA check and long mechanical jobs (it
  costs less and reports back into this chat).

## What the machine needs

Run `python3 <kit>/scripts/doctor.py` first: it shows what is ready, what is missing (with the install line for this
system) and which local WordPress app to use. Needed, by step:

- P0 Plan: Python 3.9 or later (standard library only); git for GitHub links (without git, GitHub zips work); for
  a source that is only a web address, Node.js and Playwright with Chromium (the capture).
- From P1 Setup: a local WordPress app (Laragon, Local, MAMP, XAMPP, WampServer, Herd, DDEV, wp-env or a native
  PHP and MySQL), PHP 8.1 to 8.4; Node.js 18 or later and Playwright with Chromium (`npm install -g playwright`,
  then `npx playwright install chromium`) for the diffs and the report; Composer for PHPCS. WP-CLI is optional.
- No Python at all (`python3`, `py -3` and `python` all fail): install it first (Windows `winget install -e --id
  Python.Python.3.12`, Mac `xcode-select --install` or python.org), open a new terminal, then run doctor.py. On a
  Mac the first `python3` may ask to install the Command Line Tools: say yes, wait, run it again.
- On Windows, `python3` is often missing or opens the Microsoft Store: use the command doctor.py prints (`py -3`
  or `python`) wherever the skill says `python3`.

## Asking the developer

- With a question tool (AskUserQuestion, Codex's `request_user_input` and similar): one batch of questions at
  intake, with the recommended answer first. Without one (Antigravity, most others): a short numbered list in the
  chat, and wait.
- Two gates: the **Plan OK** and the **Go-live** (`references/phases-and-qa.md`). The Plan OK lists the P1
  downloads, each with its source and size ("P1 setup: WordPress, latest.zip from wordpress.org, about 30 MB;
  Barebones from GitHub; ACF PRO from your zip; Contact Form 7 and Yoast SEO from wordpress.org"), so setup then runs
  in one go. With profile `oks: each`, ask for each of those on its own instead. Ask first for anything the plan did
  not list; deletes outside a fresh install and live steps are always asked one at a time.
- Never type a password, licence key or API key, except the default local admin password that install-wp.py reads
  from profile.local.json (local sites only, never printed). The developer pastes the rest; reports say
  `[PASTE PASSWORD HERE]`. If the developer pastes one into the chat by mistake: do not repeat it, point to where it
  belongs, suggest changing it.
- Manual steps (wp-admin, the host panel, Duplicator): one at a time, wait for "done".

## Replies: beginner mode

Profile `level: new` (or the developer says they are new to this):

- Plain words. The first time a term comes up, say what it means in a few words (`references/glossary.md`).
- Every manual step with the exact clicks ("In Local, click + at the bottom left, then Create a new site").
- End every message that stops the work with the stop report (`references/phases-and-qa.md`), its last line
  `Next: <step> — waiting on <who>` in plain words: the one thing they do next, with the exact clicks.
- Ask in multiple choice with the recommended answer first. Say what each step costs (paid plugins, AI credits).

`level: developer`: short, commands and paths, no explanations they did not ask for.

## Spend fewer tokens

Every turn re-sends the conversation, output costs more than input, a screenshot costs about a thousand tokens and
a minified bundle tens of thousands. So:

- Start each session with `ai-handoff-summary.md` and gate.py; open `handoff.md` only at the section you need; read
  one reference at a time, at the part you need.
- Never read node_modules, minified, vendor or lock files, or lines over 1,000 characters; search them with a
  pattern and a line limit instead.
- Let the scripts do the copying and the checking: they print a summary and write the detail to a file. Read that
  file only when something failed.
- Screenshots only for a failure, cropped to the region. Batch shell commands.
- Context: from 50% finish the section or page, checkpoint (board, both handoff files), send the stop report and
  continue in a new chat ("continue the WordPress conversion"); at 75% checkpoint at the next safe point. Where to
  see it per tool, and what to do without a meter: > Per tool.
- Model choice where the agent offers it: the strongest model for P0 analysis, CSS and layout failures the
  diffs cannot place, forms and email, the security review and the launch; a faster one for running scripts,
  seeding, lint loops, board and handoff updates and re-runs of failed checks.

## Shells, files and the browser

- Work where the files are. If the agent runs on the developer's machine, everything runs there. If it runs in a
  cloud sandbox linked to the developer's machine, edit the project's files on the developer's machine and use the
  sandbox only for what that machine lacks (PHP and PHPCS, Playwright, Lighthouse, PDFs), moving only the files
  that step needs and checking them on the way back (md5).
- A cloud sandbox cannot reach the developer's local sites: run parity there against snapshots and a mirror
  (`tests/parity/README.md`), or run it on the developer's machine.
- Windows paths: `D:/sites/<site>` works in Python and Node; Git Bash uses `/d/sites/<site>`. Quote every path
  with a space (`"C:/Users/Jane Doe/sites/<site>"`).
- Every kit script is Python or Node and runs from any shell. A `grep` check in the docs has a Python twin that
  runs in PowerShell too: `python3 _plan/tools/report/text-check.py fill|plain|dupes|oneoff|placeholders`
  (`references/scripts.md`). In Windows PowerShell 5.1, `curl` is another command: type `curl.exe`; `&&` does
  not exist there: run the commands one by one (or join them with `;`).
- An app in a browser chat cannot run the build: it can read uploaded files and write the P0 plan. For the
  build, use an agent that runs commands on the developer's computer (Claude Code, Codex, Cursor, Antigravity CLI, OpenCode, Cline...).
- A browser tool (the developer's browser, or the agent's own) is for phpMyAdmin, the WordPress installer, wp-admin
  checks, the test leads and the live checks a bot filter blocks. Check which browser profile it drives before
  blaming the local stack.
- No browser tool: give the developer the URL and the exact clicks, and ask for a screenshot or the result.

## Subagents

When the agent can start subagents, use them where the team needs a second pair of eyes or parallel hands:

- the read-only QA check at the end of each phase: a fresh subagent that did not write the code, run in the
  background (each tool's call is in > Per tool), on a faster model where the tool lets you pick, e.g. Sonnet;
  without subagents, a new chat with the same brief (the brief is in `references/phases-and-qa.md`);
- a long mechanical job (seeding a batch of pages, exporting content); its result goes through the phase's QA;
- independent research (plugin docs, a host's limits) whose sources go into PLAN.md (Research sources).

Without subagents, run the QA check in a new chat that never saw the build.

## Agents without skill support

Point the agent at the skill: "Read `<path>/convert-to-wordpress/SKILL.md` and follow it." The repo's `AGENTS.md`
says the same for agents that read AGENTS.md.

## Picking up another agent's work

The project carries its own memory: `ai-handoff-summary.md` (read first), `handoff.md` (the full record),
`BUILD-MAP.md` (the board) and `_plan/`. Any agent, any session: read the summary, run gate.py, continue from the
Next action. Before stopping, update both handoff files and send the stop report upward (the parent session,
else the developer).
