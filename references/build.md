# Build: 1:1 theme, ACF, media, pages, seeder, parity

Read this in P1 and P2. The kit files named here are in the theme's `includes/` after new-site.py.

## Contents

- Static first, then dynamic
- Foundation: CSS, head, clean-up, global layout
- ACF: JSON, the builder, sync, Theme Settings
- The client's wp-admin
- Media: sizes, WebP, srcset, priority
- Templates and pages
- The seeder
- Snapshots and parity checks
- Design checks: states, motion, long content
- Code quality: tokens, only what is used, sizes, gates
- Kit functions at a glance

## Static first, then dynamic

Every section goes through the same steps (PLAN.md section 4): first copy the section's
rendered HTML from the golden master into its partial (same tags, classes, attributes, order) with the copy
hardcoded, and diffs it to zero. Only then does the WordPress developer add fields, sync, wire, seed and test
again. Fields replace content, never structure, classes or order.

## Foundation: CSS, head, clean-up, global layout

- **CSS:** Barebones: the static build's compiled CSS byte for byte (Vite `cssMinify: false`). _tw: the same
  Tailwind version and tokens, compiled from the theme (`references/source-types.md`). A source with several
  stylesheets or critical CSS inlined in its `<head>`: copy its compiled files into the theme with the same
  `assets/` layout and list them in `config.php`: `KITWP_STYLESHEETS` (in the static order; the starter's own
  stylesheet is then left out) and `KITWP_INLINE_CSS` (printed in a `<style>` before them, `url(assets/` turned
  into theme URLs). Self-hosted fonts the static head preloads: `KITWP_PRELOAD_FONTS`. Either way the swap test
  must diff 0.000%: `tests/parity/swaptest.py` writes the golden master with the theme's CSS swapped in, served from
  one origin, and `parity.mjs` compares it with the golden master.
- **Global layout check (P1-06):** before the pages exist, compare regions, not pages: `region-check.mjs` (pixels
  of header, footer, pop-up, with `main` and fixed overlays hidden on both sides) and `domdiff.py` (structure).
- **Nothing else styles the page** (`cleanup.php`): block library, classic and global styles (and the footer copy),
  block supports, the image auto-sizes CSS, CF7's CSS, emoji, and the head extras. The admin bar is hidden on the
  front end (it shifts the layout).
- **Head** (`head.php` and the theme's header.php): the static `<head>` in the same order: charset, viewport, the
  preconnects, theme colour, the exact font links (`{{FONT_LINKS}}` from site.json), favicon (printed only when no
  Site Icon is set), image preloads first (`KITWP_PRELOAD_ASSETS` plus the queued priority images). Title,
  description, canonical and Open Graph come from the SEO plugin.
- **`<html>` and `<body>`** as static: the lang and dir from `KITWP_HTML_ATTRIBUTES` (site.json `html_attributes`),
  no `body_class()` if the static body has no class.
- **Agency badge:** when the profile has `branding.site_badge`, call `kitwp_agency_badge()` in the footer's bottom
  bar (next to the copyright or credits). Theme Settings > Branding swaps the image and link or hides it. It is
  the one addition to the static footer, so the footer parity check allows that element.
- **Favicon:** the Site Icon (Settings > General), seeded from the static build's square icon (at least 512 px):
  settings.json `"site_icon": "/brand/icon-512.png"`. The static icons in `assets/brand/` (favicon.svg,
  favicon-32.png, apple-touch-icon.png) are only the fallback while no Site Icon is set; then `/favicon.ico`
  redirects to the PNG instead of WordPress's "W".
- **Header, footer, mobile bar, pop-up:** copied markup; whitespace stripped between tags like React
  (`kitwp_tight_start()` / `kitwp_tight_end()`); behaviour in vanilla JS with the same state classes and timings;
  works with JavaScript off where the static site does.
- **Constants** (`config.php`): schema type, area served, country code, price range, brand colour, OG locale,
  thank-you path, form class, chat selector, reCAPTCHA mode, image widths, first device size, preload assets,
  robots.txt, opening hours. Set them from the static site in P1.

## Any country, any language

- Settings > General: the Site Language, timezone, date and time formats of the business. Lead emails and the
  Received line follow them.
- The static `<html lang dir>` wins on the front end (`KITWP_HTML_ATTRIBUTES`). Right-to-left sites keep
  `dir="rtl"` and are checked in RTL at every width.
- Several languages in the source (`/en/` and `/ar/`, Next.js i18n routing): decide early (a decision on the
  board). Either a multilingual plugin (ask before installing) or one page tree per language with the same templates;
  keep every URL as the static site has it.
- Phone numbers, currency, addresses and legal pages stay as the static site shows them. The JSON-LD phone is
  written in international form (`country_code` in site.json, empty when the number is already international).
- Cookie and consent banners: keep the static site's own; never add or remove one in a 1:1 build.

## ACF: JSON, the builder, sync, Theme Settings

- Field groups are JSON in the theme's `acf-json/` (`acf.php` sets save and load paths). They are generated by
  `_plan/tools/acf/build_field_groups.py`: write the groups in its SPEC section, `--check` validates (unique keys,
  the naming rule, unique names per parent), a normal run writes the JSON and bumps `modified` only for groups that
  changed.
- Keys: `group_<key>_<group>`, `field_<key>_<group>_<field>`, `layout_<key>_<group>_<layout>`. Never change a key
  once content is seeded.
- Sync: `wp eval-file _plan/tools/acf/sync.php` after every builder run (locally, and on live after an upload).
  It runs ACF's own sync for every pending field group and options page (`dry-run` only lists). Done means ACF >
  Field Groups and ACF > Options Pages show nothing under "Sync available"; a second run says "Nothing to sync".
  By hand: each item's own Sync link (the bulk "Sync changes" did nothing on the reference build).
- Field edits made in wp-admin write JSON into the theme too: on live, copy `acf-json/` back to local afterwards.
- **Theme Settings** (options page `<key>-theme-settings`): an ACF options page saved as JSON
  (`ui_options_page_<key>_theme_settings.json`, written by the builder), so the developer and the client find it in
  ACF > Options Pages, not hidden in theme code; `acf.php` registers it in PHP only when ACF has not. Capability
  `edit_pages`, so a client with the Editor role can use it. One group with **tabs** (Business details, Header and
  menu, Footer, pop-up or sticky bar, 404...). Anything on two or more pages lives here, with tokens (`{phone}`,
  `{tel}`, `{email}`, `{year}`, `{legal_name}`, `{company_number}`, `{registration}`, more through the
  `kitwp_tokens` filter). Its defaults are the static copy. `kitwp_setting()` reads by field key, so a setting
  nobody saved still renders 1:1.
- **Fields a non-technical client can use** (the developer's rule): follow the source's content model (its content
  files or types: a heading, a paragraph, an image, a button, a list), not its rendered HTML. One field per real
  piece of content; a paragraph with bold words or links is one text box (Bold and Link only) printed with the
  static markup; lists (cards, steps, FAQs, chips, legal sections) are repeaters; pages that share a layout share
  one group; tabs per section; plain labels ("Hero heading") with a short instruction. Never sentence pieces,
  separators, breadcrumbs or the same words twice as fields. The templates still print the exact static HTML: the
  diffs prove it.
- Component groups (heading, hero, FAQs, icon items, links) are inactive groups used through Clone fields.
- Field instructions carry the copy rules from the source (the copy brief): length, tone, what not to change.
- Return formats: image ID, link array. Read with `get_field()` and escape at output.
- The ACF menu is never hidden from administrators (the client does not see it: next section).

## The client's wp-admin

The client is not technical. They log in as an Editor, never an administrator (`references/launch.md` > The
client's login). `client-admin.php` gives every user without `manage_options` a short wp-admin:

- The menu: Dashboard, Pages, Media, Theme Settings, Contact (no "Add Contact Form"), the CFDB7 enquiries when the
  plugin is active, and Profile. The `kitwp_client_menu` filter changes the list.
- Posts and Comments are hidden while `KITWP_CLIENT_HIDE_POSTS` is true (`config.php`). Set it false when the
  site has a blog.
- It hides menus only. No capability is removed, so nothing breaks. One is added at run time: `cfdb7_access`
  for Editors, so they can read the enquiries (CFDB7 gives it to administrators only).
- No update nags or plugin notices. ACF's "Theme Settings saved." still shows.
- The dashboard has one widget, "Your website", with the links "Edit a page", "Change the phone, email or
  address" and "See enquiries", and a "Need help?" line from `KITWP_CLIENT_HELP` (set at intake, for example the
  developer's email; empty hides it).
- ACF's own menu (Field Groups, Tools) is hidden from the client. Editing pages and Theme Settings still works.
- Check it in P3 or P4 with a local Editor login: the menu, the widget, a page save, a Theme Settings save,
  and the enquiries list. A new plugin menu the client needs goes into the filter, not into the kit file.

## Media: sizes, WebP, srcset, priority

**Every image the client might change lives in the Media Library**, seeded by the seeder and set in ACF or Theme
Settings, never hard-coded in a template: the logos (header, footer, the agency badge and its link), the Site Icon,
the email images (logo, badge) and every content image. Only true UI assets (icons, arrows, decorative shapes)
stay theme files.

- Logos: Theme Settings > Branding (`logo`, `email_logo`, `email_badge`, `agency_badge`, `agency_link`). An `<img>`
  logo: `kitwp_img()` (SVG works: one file, its size from the static code or the file). A logo the static markup has
  as an inline `<svg>`: `kitwp_inline_svg()` prints the Media Library file inline, sanitised, so the DOM stays 1:1;
  a PNG the client uploads instead comes out as an `<img>`. The seeder accepts SVG; wp-admin uploads still do not.
- Email images: PNG (email clients do not show SVG or WebP); the lead email and the auto-reply read them from Theme
  Settings, with the theme files as the fallback.

- Sizes `<key>-<width>` for every static width (`KITWP_IMAGE_WIDTHS`), width only, never cropped; WebP output at
  quality 75, like next/image (`media.php`).
- The seeder imports the static build's own WebP files as those sizes, so no image is re-encoded.
- `kitwp_img( $id, $sizes, [ 'priority' => true ] )` prints the static attributes in next/image's order: alt,
  loading, width, height, decoding, style, sizes, srcset, src. Priority: no `loading="lazy"` and a head preload.
- The srcset rule (`kitwp_srcset_for_sizes()`): with vw sizes, drop the widths below the first device size times the
  smallest vw share.
- Width and height: what the static build prints, stored per image (`_<key>_attr_size`), not the file's size.
- Theme images with WebP widths beside them (`assets/hero/sky.png-640.webp`): `kitwp_asset_img()`.
- WordPress 7.1's WebP output also saves a full-size `.webp` of each original: harmless.

## Templates and pages

- **Pages, not custom post types,** so every URL stays at the root. The page template decides the fields.
- **Fixed templates** (`page-templates/<name>.php`) where pages share a layout; **one Flexible Content field**
  ("Page Sections") for one-off pages. One partial per layout in `template-parts/sections/`, data through `$args`.
- **Grids and hubs** list the pages themselves by template in menu order (`kitwp_template_pages()`), so a new page
  appears everywhere.
- **Say it once:** a page field left empty falls back to the Theme Settings default. The seeder leaves an override
  empty when it equals the default, so editing the default reaches every page.
- **Explicit, not automatic:** a layout choice the static code makes by rule becomes a visible field, seeded with
  what the static page shows.
- **Titles** raw (`kitwp_title()`): WordPress texturizes `&` into `&#038;`. Menu titles too.
- **Maps are live Google iframes, never a static image,** from one field (Theme Settings > Business "Map", or a
  page field) that takes a Google Maps link, the embed code or an address: `kitwp_map_src()` turns any of them
  into the embed URL, printed with `kitwp_iframe_src()` (`esc_attr( esc_url_raw() )`; `esc_url()` breaks the `&`).
  Until the address is confirmed, the map shows the default city (`map_default` in site.json). A copied section
  keeps its own iframe markup and only takes the src; a new section can use `kitwp_map_iframe()`. A short
  `maps.app.goo.gl` link cannot be read: ask for the address-bar link, the embed code or the address.
- **SVG paths and long markup** are copied by script, never retyped.
- **A blog the static site lacks:** a Blog page as the posts page; `home.php` renders its Page Sections with a
  post-cards layout; `archive.php` keeps archives in the site design until they redirect; posts get the page head,
  the static prose styles and the Blog page's form and final call to action. New URLs are flagged to the SEO owner.
- Every page template also handles a password-protected page and a page without Page Sections (`the_content()`).

## The seeder

- Tools > Seeder (`seed.php`, `seed-pages.php`), only when `WP_ENVIRONMENT_TYPE` is `local`. It reads
  `_setup/seed/`. Steps in this order: media, settings, forms, template pages, flexible pages, menus, SEO,
  redirects. Menus come after the pages (a menu item links a page only once it exists); forms before the pages that
  print them.
- Idempotent: a hash per item; each step reports created, updated, same, kept. A CF7 form edited in wp-admin since
  it was seeded is "kept". Run all twice: the second run must say "same" everywhere.
- Settings are written by field key, even when equal to the default; true/false as 1 and 0.
- Exporters (`_plan/tools/seed/`): `export.mjs` reads the source's content modules (fill its SITE MAPPING blocks),
  `export-pages.py` turns the built HTML into Page Sections rows. Work on a copy of the source. Forms, SEO, OG images
  and redirects are written by hand from the examples in `_setup/seed/`.
- Placeholders in seed values: `media:/path/in/static.jpg` (an attachment), `page:/slug/` (a page link).
- **Missing content (the default):** an image or field the source leaves empty, marks as to-do, or whose file is
  missing still gets a value, so every page renders 1:1 and stays editable:
  - an image: a neutral placeholder of the slot's exact size and ratio (a flat tint with its size written on it,
    WebP or PNG in `_setup/seed/placeholders/`), seeded into the Media Library with the title and alt text
    `PLACEHOLDER: <page> <field>` and set in the field like any other image;
  - text: `[PLACEHOLDER: <what goes here>]` in the field (a link: `#` with that label);
  - never hard-coded in a template, never a stock photo or invented copy.
  Where the golden master shows the gap itself, the diff for that box is a `decided` finding naming the placeholder.
  Each placeholder goes on the board's QA findings as `decided` (page, field, what the client sends) and into the
  report's next steps as a client to-do; `grep -rn "PLACEHOLDER" _setup/seed` and a search for "PLACEHOLDER" in
  wp-admin list them. Live QA lists any still there.
- More steps: the `kitwp_seed_steps` filter. Extra page rows: `kitwp_seed_expand_row`.

## Snapshots and parity checks

- Snapshots (`snapshot.php`, local only): any URL with `?<prefix>_snapshot=1` also saves its HTML to
  `_setup/snapshots/`: the DOM diff's input and the cloud mirror's source.
- `tests/parity/` (never deployed; its README has every command): `parity.mjs` pixel, text and SEO diffs per route
  and width; `breakpoints.mjs` every CSS breakpoint and 1 px past it; `domdiff.py` the DOM of each region (ignores
  `style` and `srcset`: compare those separately); `mkmirror.py` and `serve.py` for runs where the local sites are not
  reachable.
- Stable shots: motion off, scroll reveal forced, the clock frozen, maps and chat masked, fixed waits (map iframes
  never reach network idle), the viewport grown and images loaded first.
- Self-test first: the golden master against itself must be 0.000%.
- Quick widths (390, 768, 1440) per section; the full set (every breakpoint and 1 px above) at each phase's QA run and in P5.
- Reading results: 0.000% with equal heights is the goal. A 0.1 to 0.3% band is usually an image caught mid
  srcset swap. One wild shot with fallback fonts is a font that loaded late under load: re-run that shot first.
- Where to run: wherever a browser reaches both sites. A cloud shell cannot reach `.test` sites: use snapshots, the
  mirror and serve.py there, or run on the developer's machine.

## Design checks: states, motion, long content

The diffs prove the still page. These prove what moves and what the client changes, against the source site in the
same state, numbers first (computed values, measured boxes) and images only for failing rows
(`tests/parity/report/design-check/`). Hosts from `parity.config.json`; settings and pass marks in
`design-check.config.json`; results in `report/design-check.json` (the same row shape as figma-to-wordpress).

```
node design-check.mjs --states        # hover and focus-visible of every link, button, tab and field in header, main, footer;
                                      # plus each "states" entry: click a trigger (menu, tab, slider arrow), compare the region
node design-check.mjs --motion        # transition and animation: property, duration, delay, easing, iterations per element
php long-content.php make /about/     # a copy at /kit-long-test-about/: title, every text field ~3x, WYSIWYG x3, rows doubled
node design-check.mjs --long --routes=/kit-long-test-about/   # 320 to 1920: page overflow, clipped text
php long-content.php remove           # deletes exactly the IDs it made (marker _kitwp_long_test)
```

- List the states in PLAN.md and in `design-check.config.json` "states" (name, route, click selector, the region it
  changes, widths, wait for a slider). Elements are matched by DOM path, which the 1:1 DOM diff keeps equal.
- Default pass marks (until the first real build sets the final ones): colours and keywords exact, sizes within
  1 px, durations and delays within 10 ms, easing exact; long content: page overflow at most 1 px, 0 clipped text
  (line clamps and ellipsis are intended and skipped).
- JavaScript-driven motion (a slider's autoplay interval, a counter) is not a CSS value: compare the timing in the
  source code and note it in PLAN.md.
- One long page per template is enough; remove the test pages before the launch package (P5).

## Code quality: tokens, only what is used, sizes, gates

Copied markup and CSS stay exactly as the source has them (rule 1), arbitrary Tailwind values included. These rules
are for everything the build writes itself: fields, partials, its own CSS and JS, pages the source lacks. The same
five rules, in the same order, are in the figma-to-wordpress skill.

1. **Tokens not one-offs.** A design value with no token gets a token (Tailwind `@theme`, or a CSS variable in
   Barebones' `assets/css/tokens.css`); never `text-[19px]`, `bg-[#...]` or a hex in the build's CSS. A shared map
   (colours by option, button variants) lives once, in one helper or one partial.
2. **Ship only what is used.** In P5 the kit files and helpers the site does not use leave the theme (for example
   `assets/chat-save.js` without a chat, the lead-form partial without a form, the map helpers without a map), with
   their line in functions.php and phpcs.xml.dist; no empty configs or seed files in the theme.
3. **Comments say why.** Never a task, ticket or design-tool ID: history lives in git and the task tracker.
4. **Size limits.** A section past about 15 fields or 250 lines is split into smaller partials or a clone group; one
   job per file (form logic, markup and JS apart); JS lives in a file and is enqueued, never printed inline (data for
   it through `wp_add_inline_script()` or a data attribute).
5. **Gates, at every phase gate and before DONE:** PHPCS clean with the theme's escaping helpers registered in
   `phpcs.xml.dist` (`customEscapingFunctions` and `customAutoEscapedFunctions`: `kitwp_inline`, `kitwp_img`,
   `kitwp_inline_svg`, `kitwp_html`... add the build's own); no blanket ignores (a specific `phpcs:ignore` with its
   reason is fine). `npm run lint` (ESLint and Prettier; _tw has it, new-site.py adds it to Barebones with the copied
   static CSS left out of Prettier). The read-only code review (`references/phases-and-qa.md`) at every phase gate,
   not only the first.

**Self-check** in the theme folder before each phase gate and DONE; each hit is fixed, or given a one-line reason
(in a 1:1 build most one-off hits are copied source markup, which stays):

```
X="--exclude-dir=node_modules --exclude-dir=vendor --exclude-dir=tests --exclude-dir=dist --exclude-dir=build"
grep -rnE $X --include='*.php' --include='*.js' -e '[a-z]-\[(#|[0-9])' .            # one-off values
grep -rnE $X --include='*.css' --include='*.scss' -e '#[0-9a-fA-F]{3,8}\b' . | grep -v tokens   # raw hex (build's own CSS)
grep -rnE $X --include='*.php' --include='*.js' -e '[0-9]+:[0-9]+|\b[A-Z][A-Z0-9]+-T[0-9]+\b' .  # node IDs, ticket tags
grep -rn $X --include='*.php' -e 'phpcs:ignore' -e 'phpcs:disable' .                  # every ignore has its reason
```

## Kit functions at a glance

| Need | Function (prefix replaced by yours) |
|---|---|
| Theme Settings value | `kitwp_setting( 'name' )`, `kitwp_opt( 'name', $fallback )` |
| Phone shown / for tel: | `kitwp_phone()`, `kitwp_tel()` |
| Tokens in copy | `kitwp_tokens( $text, $extra )` |
| Short copy with inline HTML | `kitwp_inline( $html )`, `kitwp_html( $tag, $html, $class )` |
| Repeater or flexible rows | `kitwp_rows( get_field( 'x' ) )` |
| Raw title | `kitwp_title( $post )` |
| Pages of a template | `kitwp_template_pages( 'page-templates/x.php' )` |
| Image / theme image | `kitwp_img( $id, $sizes, $args )`, `kitwp_asset_img( $base, $sizes, $args )` |
| Preload | `kitwp_preload_image( $id, $sizes )`, `kitwp_preload_asset( $path, $sizes )` |
| Seeded media by static path | `kitwp_media_by_source( '/photos/x.jpg' )` |
| Theme file URL, site-relative link | `kitwp_asset( $path )`, `kitwp_rel_url( $url )` |
| No whitespace between tags | `kitwp_tight_start()` ... `kitwp_tight_end()` |
| Map from a link, embed code or address | `kitwp_map_src( $value )`, then `kitwp_iframe_src()`; `kitwp_map_iframe()` |
| Logo from the Media Library | `kitwp_img( $id, '' )`; inline SVG: `kitwp_inline_svg( $id )` |
| FAQ or breadcrumbs for JSON-LD | `kitwp_schema_add( 'faq', $rows )`, `kitwp_schema_add( 'crumbs', $rows )` |
| The lead form | `get_template_part( 'template-parts/sections/lead-form', null, $args )` |

## Thank-you and 404

Every site has both, even when the source has neither.

- **Source has them:** copy them 1:1 like any page.
- **Source has none:** design them from the site's own parts (header, footer, hero or page header, buttons, type
  scale, colours, spacing). Never a new look. Show it to the developer before it is final.
- **Thank-you** (`/thank-you/`, `KITWP_THANK_YOU`): a plain message ("Thanks, we have your message. We will be in
  touch within one business day."), the phone, a button home and links to the main pages. One line per form when
  the forms differ (add the form's key to the thank-you redirect as `?form=<key>`). noindex, out of the sitemap, robots.txt Disallow; the
  conversion events fire here.
- **404:** a friendly "Page not found" in the same style, links to Home, the main pages and Contact, the phone.
  Its heading and text live in Theme Settings (404 tab). It answers with a real 404 status, never 200.
- Both are in the page tracker and go through the same parity, accessibility and phone checks as every page.
