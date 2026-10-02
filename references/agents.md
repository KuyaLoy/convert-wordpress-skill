# Running the skill in your agent

The skill follows the open Agent Skills format (SKILL.md plus `references/`, `scripts/` and `assets/`), so any agent
that reads skills can run it. Paths in SKILL.md are relative to the skill folder.

## Contents

- Where the skill lives
- What the machine needs
- Asking the developer
- Shells, files and the browser
- Subagents
- Agents without skill support
- Picking up another agent's work

## Where the skill lives

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

## What the machine needs

- Python 3.9 or later (the setup, seed, board and QA scripts use the standard library only).
- Node.js 18 or later for the parity, snapshot and report tools; Playwright with Chromium (`npm i -D playwright`,
  `npx playwright install chromium`) where those run.
- PHP 8.1 to 8.4 and Composer where PHP is linted (PHPCS); WP-CLI is optional (theme generation for _tw, plugin
  installs, the move without Duplicator).
- A local WordPress stack (Laragon, Local, MAMP, XAMPP, DDEV, wp-env...). The profile says which.

## Asking the developer

- With a question tool (AskUserQuestion and similar): one batch of questions at intake, with the recommended answer
  first. Without one: a short numbered list in the chat, and wait.
- Ask before: any download (name, source, size), any plugin or package install, creating the database, deleting
  anything, any live change, publishing a board page. Permission covers that one action.
- Never type a password, licence key or API key. The developer pastes them; reports say `[PASTE PASSWORD HERE]`.
- Manual steps (wp-admin, the host panel, Duplicator): one at a time, wait for "done".

## Shells, files and the browser

- Work where the files are. If the agent runs on the developer's machine, everything runs there. If it runs in a
  cloud sandbox linked to the developer's machine, edit the project's files on the developer's machine and use the
  sandbox only for what that machine lacks (PHP and PHPCS, Playwright, Lighthouse, PDFs), moving only the files
  that step needs and checking them on the way back (md5).
- A cloud sandbox cannot reach the developer's `.test` sites: run parity there against snapshots and a mirror
  (`tests/parity/README.md`), or run it on the developer's machine.
- Windows paths: `D:/laragon/www/<site>` works in Python and Node; Git Bash uses `/d/laragon/www/<site>`.
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
