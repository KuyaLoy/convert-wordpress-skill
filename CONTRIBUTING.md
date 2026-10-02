# Contributing

Thanks for helping. Reports, setup notes and fixes are all welcome.

## Report a problem or share your setup

Open an issue with one of the two templates (Report a problem, Share your setup). Paste error lines as text, and
never paste passwords, licence keys, API keys, client names or anyone's personal data.

## Send a fix

1. Fork the repository and make a branch.
2. Keep to the rules in [AGENTS.md](AGENTS.md): plain English, no dashes as punctuation, no client, agency or
   personal names, any stack, business, country and language.
3. Run the checks AGENTS.md lists for what you changed (`php -l`, PHPCS, `python3 -m py_compile`, `node --check`,
   JSON parses), and run the changed tool once on a test project.
4. Add a line to CHANGELOG.md under Unreleased.
5. Open a pull request that says what changed and how you tested it.

## The website

The website lives in `site/` (Next.js static export, Tailwind 4, 8bitcn/ui, Pixelarticons) and is published by
GitHub Actions when `main` changes. All of its words are in `site/src/content/site.ts`; the patch notes are read
from CHANGELOG.md at build time.

```
cd site
npm install
npm run dev      # http://localhost:3000/convert-wordpress-skill/
npm run build    # writes site/out
```

By contributing, you agree that your contribution is licensed under the GNU GPL, version 2 or later.
