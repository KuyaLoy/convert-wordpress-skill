# AGENTS.md

{{SITE_NAME}} WordPress theme ({{DOMAIN}}): a 1:1 conversion of the static site, built with the
convert-to-wordpress skill on the {{STARTER}} starter theme.

## Read first

- `../../../ai-handoff-summary.md` (short), then only the section you need from `../../../handoff.md`.
- Work follows `../../../BUILD-MAP.md` story by story, one sprint at a time: run
  `python3 ../../../_plan/tools/build-map/gate.py ../../../BUILD-MAP.md` before you start and before a sprint closes.
- The plan lives in `../../../_plan/`: SPRINT-PLAN (team gates, life cycle, workflow, Done), CONTENT-MODEL (fields),
  ARCHITECTURE (how it is built), SOURCE-NOTES (what the static source says).

## The rule above all others: 1:1

The design is the static site (the golden master). Copy its markup and CSS; fields replace content only. Never
restyle, reorganise or "clean up" the copied markup or CSS. The visual, DOM and text diffs decide when a change is
done, not the eye.

## Structure

<!-- starter:barebones -->
- `assets/styles/` Sass sources: the static site's BUILT CSS goes in verbatim (no second minifier).
- `assets/scripts/` theme JavaScript source: vanilla, no jQuery.
- `includes/` WordPress setup and hooks. Starter: setup, loaders (enqueue), menus, admin, custom. Kit: config
  (site constants), cleanup, head, acf, helpers, media, forms, schema, seo, seed and seed-pages (local only),
  snapshot (local only).
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
  helpers, media, forms, schema, seo, seed and seed-pages (local only), snapshot (local only).
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
- Match the indentation of the file you edit.

## ACF JSON

- Keys `group_kitk_*`, `field_kitk_*`, `layout_kitk_*`. Never change a key once content is seeded.
- Field groups come from `../../../_plan/tools/acf/build_field_groups.py` (it bumps `modified` only for groups that
  changed). Then wp-admin > ACF > Field Groups > each group's own Sync link.
- Never hide the ACF menu: the licence and the field groups live there, on live too.

## Checks before a change is done

1. Build the CSS and JS after any source change (<!-- starter:barebones -->`npm run build`<!-- /starter:barebones --><!-- starter:tw -->`npm run dev`<!-- /starter:tw -->).
2. `php -l` on changed files; `composer install` once, then `vendor/bin/phpcs`; the duplicate function check
   (`grep -h "^function" <!-- starter:tw -->theme/<!-- /starter:tw -->includes/*.php | sed 's/(.*//' | sort | uniq -d` prints nothing).
3. Parity checks (visual, DOM, text, SEO) against the golden master for any front-end change.
4. Update BUILD-MAP.md, handoff.md and ai-handoff-summary.md.
5. Never type passwords, licence keys or API keys. Ask before installing any plugin.
