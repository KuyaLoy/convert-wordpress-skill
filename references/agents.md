# Running the skill in your agent

The skill follows the open Agent Skills format (SKILL.md plus `references/`, `scripts/` and `assets/`), so any agent
that reads skills can run it. Paths in SKILL.md are relative to the skill folder.

## Contents

- Where the skill lives, and updating it
- What the machine needs
- Asking the developer
- Replies: beginner mode
- Spend fewer tokens
- Shells, files and the browser
- Subagents
- Agents without skill support
- Picking up another agent's work

## Where the skill lives, and updating it

The folder must be named `convert-to-wordpress` (the `name` in SKILL.md).

| Agent | Personal (all projects) | One project |
|---|---|---|
| Claude Code | `~/.claude/skills/convert-to-wordpress/` | `.claude/skills/convert-to-wordpress/` |
| Codex | `~/.agents/skills/convert-to-wordpress/` | `.agents/skills/convert-to-wordpress/` |
| Cursor | `~/.cursor/skills/` or `~/.agents/skills/` | `.cursor/skills/` or `.agents/skills/` (it also reads `.claude/skills/`) |
| Gemini CLI | `~/.gemini/skills/` or `~/.agents/skills/` | `.gemini/skills/` or `.agents/skills/` |
| Antigravity | `~/.gemini/config/skills/` | `.agents/skills/` |
| Grok Build and others that read skills | `~/.agents/skills/` (check the tool's docs) | `.agents/skills/` |
| Claude apps (claude.ai, Cowork) | Upload the folder as a skill (zipped), or save it from a skill card | |

Install by cloning the repo into one of those folders. The developer's own defaults go in `profile.local.json` next
to SKILL.md (never committed).

Updating: `/update-convert-wordpress-skill` (added once with `python3 <kit>/scripts/update.py --add-command`), or
when the developer asks to update the skill: `update.py --check` first (installed and newest version, what is
new), then ask (it downloads), then `update.py`. A git clone updates with `git pull --ff-only` and stops on local
edits; any other install gets the release zip after a backup in `_backups/`; `profile.local.json` is kept. A new
chat reads the new version. A copy saved in a Claude app updates by uploading the new version there.

## What the machine needs

Run `python3 <kit>/scripts/doctor.py` first: it shows what is ready, what is missing (with the install line for this
system) and which local WordPress app to use. Needed, by step:

- Sprint 0: Python 3.9 or later (standard library only); git for GitHub links (without git, GitHub zips work); for
  a source that is only a web address, Node.js and Playwright with Chromium (the capture).
- From Sprint 1: a local WordPress app (Laragon, Local, MAMP, XAMPP, WampServer, Herd, DDEV, wp-env or a native
  PHP and MySQL), PHP 8.1 to 8.4; Node.js 18 or later and Playwright with Chromium (`npm install -g playwright`,
  then `npx playwright install chromium`) for the diffs and the report; Composer for PHPCS. WP-CLI is optional.
- No Python at all (`python3`, `py -3` and `python` all fail): install it first (Windows `winget install -e --id
  Python.Python.3.12`, Mac `xcode-select --install` or python.org), open a new terminal, then run doctor.py. On a
  Mac the first `python3` may ask to install the Command Line Tools: say yes, wait, run it again.
- On Windows, `python3` is often missing or opens the Microsoft Store: use the command doctor.py prints (`py -3`
  or `python`) wherever the skill says `python3`.

## Asking the developer

- With a question tool (AskUserQuestion and similar): one batch of questions at intake, with the recommended answer
  first. Without one: a short numbered list in the chat, and wait.
- Ask before: any download, plugin or package install, database change, delete, live change, publishing a board
  page. With profile `oks: group` (the default), one OK covers the items listed with it, each named with its source
  and size ("Sprint 1 setup: WordPress, latest.zip from wordpress.org, about 30 MB; Barebones from GitHub; Contact
  Form 7 and Yoast SEO from wordpress.org. OK?"); with `oks: each`, ask one by one. Deletes and live steps are
  always asked one at a time.
- Never type a password, licence key or API key. The developer pastes them; reports say `[PASTE PASSWORD HERE]`. If
  the developer pastes one into the chat by mistake: do not repeat it, point to where it belongs, suggest changing it.
- Manual steps (wp-admin, the host panel, Duplicator): one at a time, wait for "done".

## Replies: beginner mode

Profile `level: new` (or the developer says they are new to this):

- Plain words. The first time a term comes up, say what it means in a few words (`references/glossary.md`).
- Every manual step with the exact clicks ("In Local, click + at the bottom left, then Create a new site").
- End every message with **Your turn:** and the one thing they do next (or "Nothing: I am working on it").
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
- One sprint per chat: after a gate closes, start a new chat ("continue the WordPress conversion").
- Model choice where the agent offers it: the strongest model for Sprint 0 analysis, CSS and layout failures the
  diffs cannot place, forms and email, the security review and the launch; a faster one for running scripts,
  seeding, lint loops, board and handoff updates and re-runs of failed checks.

## Shells, files and the browser

- Work where the files are. If the agent runs on the developer's machine, everything runs there. If it runs in a
  cloud sandbox linked to the developer's machine, edit the project's files on the developer's machine and use the
  sandbox only for what that machine lacks (PHP and PHPCS, Playwright, Lighthouse, PDFs), moving only the files
  that step needs and checking them on the way back (md5).
- A cloud sandbox cannot reach the developer's local sites: run parity there against snapshots and a mirror
  (`tests/parity/README.md`), or run it on the developer's machine.
- Windows paths: `D:/sites/<site>` works in Python and Node; Git Bash uses `/d/sites/<site>`.
- An app in a browser chat cannot run the build: it can read uploaded files and write the Sprint 0 plan. For the
  build, use an agent that runs commands on the developer's computer (Claude Code, Codex, Cursor, Gemini CLI...).
- A browser tool (the developer's browser, or the agent's own) is for phpMyAdmin, the WordPress installer, wp-admin
  checks, the test leads and the live checks a bot filter blocks. Check which browser profile it drives before
  blaming the local stack.
- No browser tool: give the developer the URL and the exact clicks, and ask for a screenshot or the result.

## Subagents

When the agent can start subagents, use them where the team needs a second pair of eyes or parallel hands:

- the sprint review (always a fresh reviewer that did not write the code);
- a developer task from the sprint backlog (the task card: backlog row, files to read, acceptance, test commands),
  reviewed by the Lead afterwards;
- independent research (plugin docs, a host's limits) whose sources go into ARCHITECTURE.md.

Without subagents, review in a new session, or switch hats explicitly (`references/team-and-sdlc.md`).

## Agents without skill support

Point the agent at the skill: "Read `<path>/convert-to-wordpress/SKILL.md` and follow it." The repo's `AGENTS.md`
says the same for agents that read AGENTS.md.

## Picking up another agent's work

The project carries its own memory: `ai-handoff-summary.md` (read first), `handoff.md` (the full record),
`BUILD-MAP.md` (the board) and `_plan/`. Any agent, any session: read the summary, run gate.py, continue from the
Next action. Before stopping, update both handoff files.
