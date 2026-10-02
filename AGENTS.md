# AGENTS.md

This repository is the **convert-to-wordpress** Agent Skill.

## Using it

To convert a website to WordPress, read `SKILL.md` in this folder and follow it. Its paths (`references/`,
`scripts/`, `assets/`) are relative to this folder. `references/agents.md` explains how to install and run it in
each agent.

## Working on the skill itself

- Keep `SKILL.md` under 500 lines; detail belongs in `references/`.
- No client, agency or personal names, no email addresses, no internal IDs, no secrets: examples use Example Co and
  example.com. `profile.local.json` and the handoff files stay out of the repository (`.gitignore`).
- Any stack, business, country and language: no defaults tied to one.
- Tokens in templates: `kitwp` / `KITWP` / `Kitwp` (PHP prefix), `kitk` (ACF key prefix), `{{NAME}}` values,
  `<!-- starter:barebones -->` and `<!-- starter:tw -->` blocks, `[[...]]` report facts.
- Before a change is done: `php -l` on every PHP file in `assets/`; PHPCS on a theme made by `scripts/new-site.py`
  (both starters); `python3 -m py_compile` on the scripts; `node --check` on the JavaScript; every JSON file parses;
  run the changed tool once on a test project.
- Add every new lesson to `references/gotchas.md`.
- Record every change in `CHANGELOG.md`: under Unreleased while you work, then under a new version (Semantic
  Versioning) when it is released.
- Licence: GPL-2.0-or-later.
- `site/` is the website (see `site/README.md`), not part of the skill: never read it while converting a site.
