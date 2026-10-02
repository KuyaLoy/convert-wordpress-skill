# convert-to-wordpress

An [Agent Skill](https://agentskills.io) that converts an existing website into a WordPress site that looks and
behaves exactly the same, keeps every URL and SEO signal, and lets editors change everything in wp-admin: content in
ACF PRO fields, forms and emails in Contact Form 7.

It works with any source (plain HTML, Next.js, React, Astro, Vue, Gatsby, Nuxt, SvelteKit...), any kind of business,
and any country or language, and with any agent that reads skills: Claude, Codex, Cursor, Gemini CLI, Antigravity,
Grok Build and others.

## What it does

- **Studies the source first:** the stack, the routes, Tailwind or plain CSS, forms, tracking, fonts, languages and
  right-to-left, and how to produce the golden master (the site as visitors get it) that every page is compared to.
- **Sets up the project:** asks the intake questions once, creates the database with your OK, downloads WordPress
  with checksums, writes wp-config without anyone typing a secret, and prepares the starter theme: **_tw** when the
  source uses Tailwind, **Barebones** otherwise. Starter plugins: ACF PRO and Contact Form 7, and the ACF menu
  always shows.
- **Builds 1:1, static first:** every section is copied as static HTML and diffed to zero, then made editable (ACF
  JSON with stable keys, sync, seed, clean). Pixel, DOM, text and SEO diffs prove each page.
- **Works as a full team:** owner, manager, lead developer guiding a front-end and a WordPress developer, UI, UX,
  security, tester and QA. Builders build, reviewers sign the gates, nobody approves their own work.
- **One sprint at a time:** `gate.py` refuses to open the next sprint until every story, page and gate is done and
  the developer says go.
- **Goes live and proves it:** a Duplicator Pro runbook with rollback, live QA (pages, tracking, redirects, private
  files, host rules), test leads, and a client-ready PDF report.
- **Keeps a memory:** `handoff.md` and `ai-handoff-summary.md` in every project, so any agent or developer can carry
  on without guessing.

## Install

Clone this repository into your agent's skills folder. The folder must be named `convert-to-wordpress`.

| Agent | Personal (all projects) | One project |
|---|---|---|
| Claude Code | `~/.claude/skills/convert-to-wordpress` | `.claude/skills/convert-to-wordpress` |
| Codex | `~/.agents/skills/convert-to-wordpress` | `.agents/skills/convert-to-wordpress` |
| Cursor | `~/.cursor/skills/` or `~/.agents/skills/` | `.cursor/skills/` or `.agents/skills/` |
| Gemini CLI | `~/.gemini/skills/` or `~/.agents/skills/` | `.gemini/skills/` or `.agents/skills/` |
| Antigravity | `~/.gemini/config/skills/` | `.agents/skills/` |
| Grok Build and others | `~/.agents/skills/` (check the tool's docs) | `.agents/skills/` |

```
git clone https://github.com/KuyaLoy/convert-wordpress-skill ~/.claude/skills/convert-to-wordpress
```

Claude apps (claude.ai, Cowork): upload the folder as a skill, or keep a clone on your machine and tell the agent
where it is. Agents without skill support: ask them to read `SKILL.md` and follow it.

Then copy `profile.example.json` to `profile.local.json` (never committed) and fill in your defaults: your name,
the Bcc list for lead emails, your task tracker, your local stack, your host, the path to your ACF PRO zip.

## Use

Give the skill the site to convert, as a git URL, a zip or a folder:

```
/convert-to-wordpress https://github.com/you/your-site      Claude Code (Codex: $convert-to-wordpress ...)
/convert-to-wordpress D:/sites/my-site.zip
/convert-to-wordpress ./my-site
```

Or in plain words: "Convert the site in D:/sites/my-site to WordPress". It makes a working copy (the original is
never touched), studies it, asks only what it cannot find out, writes the plan and Sprint 0, and stops at the gate
for your go. Later: "continue the WordPress conversion" (it reads the handoff summary), "where are we?", "go".

## Requirements

- Python 3.9+ and Node.js 18+ (Playwright with Chromium for the parity, screenshot and PDF tools).
- PHP 8.1 to 8.4 with Composer where PHP is linted; WP-CLI optional.
- A local WordPress stack (Laragon, Local, MAMP, XAMPP, DDEV, wp-env...).
- Your own licences for the commercial plugins you use (ACF PRO; Duplicator Pro for the default launch path).

## Safety

The skill never types passwords, licence keys or API keys (you paste them), asks before every download, plugin
install, database change, delete and live step, never edits the source or the golden master, and keeps planning
files private (blocked on the web server and left out of the launch package).

## Layout

```
SKILL.md              the workflow and the rules
references/           the detailed guides, read when needed
scripts/              the tools (copied into each project's _plan/tools/)
assets/               templates: theme code, seed examples, plan, board, handoff, launch, report
profile.example.json  your defaults template (copy to profile.local.json)
CHANGELOG.md          what changed in each version
```

## Changelog

Every change is recorded in [CHANGELOG.md](CHANGELOG.md), newest first.

## Credits and licence

Starter themes: [Barebones](https://github.com/benchmarkstudios/barebones) by Benchmark Studios and
[_tw](https://underscoretw.com/) by Greg Sullivan, both GPL-2.0-or-later. WordPress, Advanced Custom Fields,
Contact Form 7, Yoast SEO, Redirection and Duplicator are the work and trademarks of their owners.

This skill is free software under the GNU General Public License, version 2 or (at your option) any later version.
See [LICENSE](LICENSE).
