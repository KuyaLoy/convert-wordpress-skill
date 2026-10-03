---
name: update-convert-wordpress-skill
description: Updates the convert-to-wordpress skill to its newest version from GitHub and says what changed. Use when the developer asks to update, upgrade or check the version of the convert-to-wordpress skill.
license: GPL-2.0-or-later
---

# Update the convert-to-wordpress skill

1. Find the skill: the folder `convert-to-wordpress` next to this one (it holds `scripts/update.py`). Not there:
   ask the developer where it is.
2. Look first: `python3 <that folder>/scripts/update.py --check` (on Windows often `py -3` instead of `python3`).
   It prints one line: `OK` = already the newest, say so and stop; `WARN` = a newer version, with what is new.
3. Tell the developer the installed and the newest version and what is new, in plain words, and ask before
   updating (it downloads from github.com).
4. With their OK: `python3 <that folder>/scripts/update.py`. A git clone updates with `git pull` (local edits stop
   it, nothing is overwritten); any other install gets the release zip, with a backup in `_backups/` first. The
   developer's `profile.local.json` and the projects are kept.
5. Report the result line. Then: start a new chat, so the agent reads the new version. A project already started
   keeps its own copy of the tools; to refresh them, ask first, then run
   `python3 <that folder>/scripts/new-site.py <wp_root>/_plan/site.json --force` (kit code only, backup first).

A `FAIL` line says what to do (for example commit local edits, or no network here). Never delete or overwrite
files by hand to force an update.

In a chat app that saves skills without their folder (only SKILL.md, no `scripts/`): read the newest notes in
https://raw.githubusercontent.com/KuyaLoy/convert-wordpress-skill/main/CHANGELOG.md, tell the developer what is new,
and with their OK offer https://raw.githubusercontent.com/KuyaLoy/convert-wordpress-skill/main/SKILL.md as the
update to the saved convert-to-wordpress skill, the app's own way (for example a skill card). A local clone they
keep for the kit is updated with the steps above.
