# {{SITE_NAME}}: notes from the source

Written {{DATE}} from the code the designer handed over. `python3 _plan/tools/analyze-source.py <source>` output
goes in section 1; read the repo's own docs for the rest.

## 1. What the source is

| Item | Found |
|---|---|
| Stack | (plain HTML / Next.js export / Next.js server / React SPA / Astro / Vue / other) |
| Build command and output | |
| Tailwind | (version, config) -> starter theme |
| Routes | (count, dynamic routes and their real paths) |
| Content | (content modules, Markdown, CMS fetches) |
| Images | (next/image widths, loader, deviceSizes[0]) |
| Fonts | (Google Fonts links, next/font self-hosted files) |
| Icons | |
| Forms | (endpoints, handler, recipients) |
| Tracking | (GTM / GA4 / Ads ids found) |
| Redirects | (redirect map, next.config, vercel.json, .htaccess) |

## 2. Golden master

How it is produced and where it is served (see the skill's references/source-types.md).

## 3. Documents in the repo

| File | Valid for the build? |
|---|---|

## 4. Rules from the source that must hold in WordPress

(design-system non-negotiables, copy brief rules, accessibility promises)

## 5. Open items carried over (not ours to fix)

| Item | How the build handles it |
|---|---|
