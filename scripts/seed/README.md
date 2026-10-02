# Seed exporters

The theme's seeder (Tools > Seeder, local only) reads `_setup/seed/`. These two scripts write it from the static
site, so WordPress starts with exactly the static content. Run them again whenever the static content changes,
then run the seeder twice: the second run must say "same" everywhere.

| Script | Reads | Writes |
|---|---|---|
| `export.mjs` | the static content modules (bundled), the static `out/` and `public/` | `media.json` + `files/`, `settings.json`, `menus.json`, `template-pages.json`, `content.json` |
| `export-pages.py` | the static build's HTML | `pages.json` (Page Sections rows for the one-off pages) |

The other seed files are written by hand from the examples in `_setup/seed/` (the skill's `assets/seed/`): `forms.json`, `quote-form.txt`,
`chat-form.txt`, `lead-email.html`, `seo.json`, `og-images.json`, `redirects.json`.

Order on the seeder screen: media, settings, forms, template pages, flexible pages, menus, SEO, redirects. Menus
come after the pages because a menu item links a page only once the page exists.

Rules:
- Work on a copy of the static source (bundling or `npm install` writes files); never edit the static folder.
- Images: the static WebP widths are copied as they are and attached as the `kitk-<width>` sizes, so srcsets match.
  Copy files with 0644 modes (files from a Windows mount keep 0700).
- Text: exact. Phone, email and similar values become tokens (`{phone}`) so Theme Settings changes reach every page.
- Overrides equal to the Theme Settings default stay empty.
- Copy SVG paths and markup by script, never by hand.
