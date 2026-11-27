# AGENTS.md

{{SITE_NAME}} WordPress theme ({{DOMAIN}}): a 1:1 conversion of the static site, built with the
convert-to-wordpress skill on the {{STARTER}} starter theme.

## Read first

- `../../../ai-handoff-summary.md` (short), then only the section you need from `../../../handoff.md`.
- Work follows `../../../BUILD-MAP.md` section by section, one phase at a time: run
  `python3 ../../../_plan/tools/build-map/gate.py ../../../BUILD-MAP.md` before you start and before a phase closes.
- The plan lives in `../../../_plan/`: PLAN (goal, the source, how it is built, phases, per-section workflow, Done),
  CONTENT-MODEL (fields), OLD-SITE-URLS (redirects).

## The rule above all others: 1:1

The design is the static site (the golden master). Copy its markup and CSS; fields replace content only. Never
restyle, reorganise or "clean up" the copied markup or CSS. The visual, DOM and text diffs decide when a change is
done, not the eye.

## Media, maps, forms, speed

- Logos (the agency badge and its link too), the Site Icon, email images and content images live in the Media
  Library and are set in ACF or Theme Settings, never hard-coded; only UI icons and decorative shapes are theme files.
- Maps: a live Google iframe from one field (link, embed code or address) through `kitwp_map_src()`.
- CF7: autop off on every form; every notification and auto-reply in the branded HTML template.
- Core Web Vitals from the first section: LCP preload and fetchpriority, sized srcset, nothing lazy above the fold,
  reserved media space, metric-matched fallback font, minimal deferred JS; one H1, heading order, aria-labels, alt.
  No speed plugin unless the theme cannot do it.
<!-- starter:tw -->
- CSS you write yourself: Tailwind utilities on the `@theme` tokens; custom CSS only for CF7 and what utilities
  cannot express; no `text-wrap: balance` on headings; end padding of |letter-spacing| on text tokens.
<!-- /starter:tw -->

## Structure

<!-- starter:barebones -->
- `assets/styles/` Sass sources: the static site's BUILT CSS goes in verbatim (no second minifier).
- `assets/scripts/` theme JavaScript source: vanilla, no jQuery.
- `includes/` WordPress setup and hooks. Starter: setup, loaders (enqueue), menus, admin, custom. Kit: config (site
  constants), cleanup, head, acf, helpers (and -maps), media (and -svg), forms (forms-controls, -spam, -mail,
  -local-mail, -portal, -attribution, -lead-source), client-admin, schema, seo, seed and its seed-* steps (local
  only), snapshot (local only).
- `page-templates/` page templates; `template-parts/sections/` one partial per section layout.
- `acf-json/` ACF local JSON for every field group.
- `style.css`, `css/` and `js/` are build output: edit the sources, then `npm run build`.
- `tests/parity/` the 1:1 checks (never deployed).
<!-- /starter:barebones -->
<!-- starter:tw -->
- This folder is the _tw project; `theme/` is what WordPress loads (and what gets deployed).
- `tailwind.css` and `tailwind/` the Tailwind sources: the static site's Tailwind version, theme tokens and custom
  CSS go here, so the compiled `theme/style.css` gives the same result as the static CSS (swap test 0.000%).
- `javascript/` theme JavaScript source (esbuild to `theme/js/`): vanilla.
- `theme/inc/` the starter's helpers; `theme/includes/` the kit: config (site constants), cleanup, head, acf,
  helpers (and -maps), media (and -svg), forms (forms-controls, -spam, -mail, -local-mail, -portal, -attribution,
  -lead-source), client-admin, schema, seo, seed and its seed-* steps (local only), snapshot (local only).
- `theme/page-templates/` page templates; `theme/template-parts/sections/` one partial per section layout.
- `theme/acf-json/` ACF local JSON for every field group.
- `theme/style.css` and `theme/js/` are build output: `npm run dev` (or `npm run watch`), `npm run prod` for the
  final build. Classes that only appear in ACF values or JavaScript need `@source inline(...)` in `tailwind.css`.
- `tests/parity/` the 1:1 checks (never deployed).
<!-- /starter:tw -->

## PHP

- Must run unchanged on PHP 8.1 to 8.4: only 8.1 features, nothing that 8.2 to 8.4 deprecate (dynamic properties,
  `${var}` in strings, implicit nullable parameters, `E_STRICT`).
- Prefix every global function, hook name, global variable and constant with `kitwp_` / `KITWP_`. Text domain:
  `kitwp`.
- Escape everything at output (`esc_html`, `esc_attr`, `esc_url`, `wp_kses_post` or `kitwp_inline()`); sanitise all
  input; nonces and capability checks on anything custom. Read ACF values with `get_field()` and escape them
  yourself.
- Every ACF repeater or flexible field read goes through `kitwp_rows()`, every relationship, gallery, checkbox or
  multi-select through `kitwp_list()`, and a group is checked with `is_array()`. Never `(array)` on a field: an empty
  field is `false` or `null`, and `(array) false` is `[false]` (one empty row and a PHP warning).
- Every PHP file starts with its header comment, then `defined( 'ABSPATH' ) || exit;` (a direct request prints
  nothing instead of an error with the server path).
- Theme JavaScript is a file, enqueued with its file date as the version (`filemtime()`); values PHP knows go in as
  data (`wp_localize_script()` or a data attribute), not as code in an inline script.
- Match the indentation of the file you edit.

## ACF JSON

- Keys `group_kitk_*`, `field_kitk_*`, `layout_kitk_*`. Never change a key once content is seeded.
- Field groups and the Theme Settings options page come from `../../../_plan/tools/acf/build_field_groups.py` (it
  bumps `modified` only for groups that changed). Then `wp eval-file ../../../_plan/tools/acf/sync.php` (or each
  item's Sync link): ACF > Field Groups and ACF > Options Pages show nothing under "Sync available".
- Fields are for a non-technical client: the source's content model, repeaters for lists, tabs, plain labels;
  never one field per rendered text node.
- Never hide the ACF menu from administrators: the licence, the options pages and the field groups live there, on
  live too. The client (Editor) does not see it (`includes/client-admin.php`).

## Checks before a change is done

1. Build the CSS and JS after any source change (<!-- starter:barebones -->`npm run build`<!-- /starter:barebones --><!-- starter:tw -->`npm run dev`<!-- /starter:tw -->).
2. `php -l` on changed files; `composer install --no-interaction --no-progress` once, then
   `vendor/bin/phpcs -q --report=summary` (the full report into a log when it finds something); the duplicate function check
   (`grep -h "^function" <!-- starter:tw -->theme/<!-- /starter:tw -->includes/*.php | sed 's/(.*//' | sort | uniq -d` prints nothing).
3. One call per section: `python3 tests/parity/check-section.py <route> --section <selector>` (pixel, text, DOM,
   php -l, PHPCS, duplicates; one line back). Design checks (`design-check.mjs --states --motion`) at the end of a page.
4. `npm run lint` (ESLint and Prettier) passes. What you wrote uses tokens, never one-off values
   (the self-check in the skill's references/build.md > Code quality: every hit fixed or given a reason); only used kit files and helpers;
   a section past about 15 fields or 250 lines is split; JS in a file, enqueued; comments say why, no ticket IDs.
5. Update BUILD-MAP.md, handoff.md and ai-handoff-summary.md.
6. Never type passwords, licence keys or API keys. Ask before installing any plugin.
