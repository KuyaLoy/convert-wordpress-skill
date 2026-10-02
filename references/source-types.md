# Study the source: any stack to a golden master

Read this in Sprint 0, before planning. Every site arrives differently (plain HTML, Next.js, a React app, Astro,
Vue...). Study the code first, write down what it does, and produce one golden master: the site exactly as visitors
get it, served unchanged, that every WordPress page is compared against.

## Contents

- Study first
- The golden master, by stack
- Next.js details that decide parity
- Tailwind sources (the _tw theme)
- Content, forms, tracking, redirects
- Behaviour inventory
- When the source cannot be built

## Study first

1. `python3 _plan/tools/analyze-source.py <source>` (read only). It reports the stack, the build scripts, built
   output already there, Tailwind (and so the starter theme), routes and dynamic routes, content sources, forms,
   tracking ids, fonts, icons, images, redirect sources, and the golden-master method.
2. Read what it points at: `package.json`, the framework config (`next.config.*`, `vite.config.*`,
   `astro.config.*`, `nuxt.config.*`, `svelte.config.*`), the layout and page files, the content modules, the
   repo's README and docs.
3. Write `_plan/SOURCE-NOTES.md` (template in `assets/plan/`): what the source is, how the golden master is made,
   which repo documents are still valid, rules that must hold in WordPress, open items that are not ours to fix.
4. Never build in the source folder: copy it first (`npm install` and builds write files).

## The golden master, by stack

| Source | Golden master | How |
|---|---|---|
| Plain HTML | The files themselves | Serve the folder unchanged (`serve.py <folder> <port>`) |
| Next.js, static export (`output: 'export'`, maybe only when an env var is set) | `out/` | In a copy: `npm ci`, the export build (read the scripts: often `build:static` or an env flag), serve `out/` |
| Next.js, server build | Rendered HTML per route | `npm run build && npm start` in a copy, then `node snapshot-routes.mjs http://localhost:3000 golden/ sitemap`; pixels from the running app |
| React or Vue SPA (Vite, CRA) | The running app plus snapshots | `npm run build && npm run preview` (Vite, port 4173) or `npx serve -s build`; snapshots per route (React Router paths). SPAs need a history fallback: serve.py does not do that |
| Gatsby | `public/` | `gatsby build`; serve `public/` |
| Astro | `dist/` | `astro build` (static unless `output: 'server'`); serve `dist/` |
| Nuxt | `.output/public/` | `nuxi generate` for static; otherwise run it and take snapshots |
| SvelteKit | `build/` | With adapter-static; otherwise run it and take snapshots |
| Remix / React Router with SSR | Snapshots | Run it, snapshot every route |

The snapshots (`snapshot-routes.mjs`) are the markup to copy into the theme partials and the input for the DOM
diff. File names match the WordPress snapshots: `home.html`, `about.html`, `a__b.html`.

Dynamic routes (`[slug]`, `:id`) are expanded to their real paths from the content data or the sitemap. Every
route goes into CONTENT-MODEL.md's page inventory, plus `/thank-you/` and the 404.

## Next.js details that decide parity

- **Upload and serve `out/`**, never the repo zip. `robots.ts` and `sitemap.ts` need
  `export const dynamic = 'force-static'` to export. An "indexable" env flag (for example `SITE_INDEXABLE=1`) may
  decide robots: read the scripts.
- **next/image:** srcset widths come from `images.imageSizes` plus `images.deviceSizes` (defaults 16 to 3840).
  When `sizes` uses vw, Next leaves out the widths below `deviceSizes[0]` times the smallest vw share (default
  640), so the page loads a bigger file than you expect: `kitwp_srcset_for_sizes()` repeats that rule. A custom
  loader (static export) decides the file names. Width and height attributes are what the build prints, not the
  file's size: store them per image.
- **priority images:** no `loading="lazy"`, plus a `<link rel="preload" as="image" imagesrcset imagesizes>` in the
  head. Check the built HTML before adding `fetchpriority`: the Next 15 build on the reference site printed none.
- **next/font:** the fonts are self-hosted with hashed names under `/_next/static/media/`; copy the files into the
  theme and the `@font-face` rules from the built CSS. Google Fonts `<link>` tags: copy the exact URLs.
- **Tracking:** never inject GTM into built Next.js HTML (React hydration error #418 on every page). In the Next
  source, `next/script`; in WordPress, the head and body-open hooks.
- **React behaviour:** components become vanilla JS with the same state classes, attributes and timings. Read the
  built JS when the source hides timings in libraries.
- **Whitespace:** React prints no whitespace between tags, so inline-block items have no gaps. Templates must
  strip whitespace between tags the same way (`kitwp_tight_start()` / `kitwp_tight_end()`), including tab-only gaps
  and the buffer edges (PHP's `?>` eats the newline and leaves tabs).

## Tailwind sources (the _tw theme)

Tailwind anywhere in the source (a dependency, a config, `@tailwind` or `@import "tailwindcss"` in the CSS): the
theme starts from _tw. The CSS still has to be 1:1, proven by the swap test: the static build with the theme's
compiled CSS in place of its own must diff 0.000%.

- **Tailwind v4 source:** use the same version. Copy the source's `@theme` tokens, custom CSS, `@utility` and
  `@plugin` lines into _tw's `tailwind.css` and `tailwind/` files. Tailwind scans the theme's PHP; classes that only
  exist in ACF values or JavaScript need `@source inline("...")`. Leave out _tw's Typography defaults if the static
  site does not use them.
- **Tailwind v3 source:** v4 changed defaults (border and ring colours and widths, placeholder colour, and more).
  Either upgrade a copy of the source first (`npx @tailwindcss/upgrade`) and prove the static build still diffs 0,
  or ship the static build's compiled CSS verbatim as the theme stylesheet, and record that as a decision. Editors
  only change content in a 1:1 build, so new utility classes are not needed.
- Plain CSS sources (Barebones): the static BUILT CSS byte for byte, after the framework's autoprefixer and
  minifier, not the source CSS. Vite with `cssMinify: false`: a second minifier drops prefixes.

## Content, forms, tracking, redirects

- **Content:** content modules (`content/*.ts`, `data/*.json`), Markdown or MDX, or a CMS fetched at build time.
  The exporters (`_plan/tools/seed/`) read them, or the built HTML, into `_setup/seed/`.
- **Forms:** find the handler (an API route, a third-party form service, a PHP mail script, a fetch to an
  endpoint). Note every field, required flags, honeypots, recipients, the success redirect, and the email layout:
  Contact Form 7 replaces the handler with the same behaviour (`references/forms-email.md`).
- **Tracking:** GTM, GA4, Ads and Meta ids, where they load, which events and conversions fire, and on which pages.
- **Redirects:** `redirects()` in next.config, `vercel.json`, `_redirects`, `.htaccess`, a redirect map file.
  Together with the old site's URLs (setup.md, intake) they make `_plan/OLD-SITE-URLS.md`.
- **Icons and images:** icon fonts and SVG sprites are copied as they are; SVG paths by script, never by hand.

## Behaviour inventory

List every interactive piece before building: menus, the mobile bar, pop-ups and modals, accordions, tabs,
sliders, scroll reveal, counters, clocks, the chat widget, form steps. For each: the trigger, the state classes and
attributes (`aria-expanded`, `hidden`, `.is-open`), the timings, the keyboard behaviour, reduced-motion handling.
That list is the UX gate's checklist.

## Languages

Note the `<html lang dir>` (analyze-source.py prints it), every language the site has and how its URLs are built
(`/en/`, `/ar/`, subdomains, Next.js i18n routing). One language: set the Site Language and keep the static `lang`.
Several: a decision for the board before Sprint 1 (`references/build.md`, any country, any language).

## When the source cannot be built

- Missing secrets, private packages or an old toolchain: try the documented build in a copy once, record the
  error, then use the live static site as the golden master (snapshots of every route plus its assets), and say so
  in SOURCE-NOTES.md and the decisions.
- The live site changes at launch: capture it (snapshots, a mirror of its assets) before then.
