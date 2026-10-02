# {{SITE_NAME}}: architecture

Status: **Sprint 0 draft**. Written {{DATE}}. How the WordPress site is built.

## 1. Stack

| Part | Choice | Notes |
|---|---|---|
| CMS | WordPress, latest release (checksums verified) | |
| PHP | Local 8.4; code runs on 8.1 to 8.4 | Check the live host's version before launch |
| Local | {{SITE_DIR}}, http://{{LOCAL_HOST}} | |
| Golden master | The static build, served unchanged | Never edited |
| Theme | `{{THEME}}` from the starter theme (Barebones for plain CSS, _tw for Tailwind) | |
| Fields | ACF PRO (licence activated by the developer) | JSON in the theme's acf-json |
| Forms | Contact Form 7 | Rendered in the static markup |
| Other plugins | Only when the task needs them, after the developer says yes | |

## 2. 1:1 parity

- **Markup:** each partial starts as the section's rendered HTML from the golden master.
- **CSS:** plain CSS sites: the static BUILT CSS byte for byte (no second minifier). Tailwind sites: the same
  Tailwind version and config, compiled from the theme's templates. Either way the swap test (static build with
  the theme CSS) must diff 0.000%.
- **Nothing else styles the page:** block library, global styles, CF7 CSS and emoji off (includes/cleanup.php).
- **Head:** same lang, viewport, theme colour, preconnects, font links, favicon, preloads (includes/head.php).
- **Images:** same files, widths, sizes and srcset rule as the static build (includes/media.php).
- **Behaviour:** the same state classes and timings in vanilla JS; works with JavaScript off.

Checks: pixel, DOM, text and SEO diffs (tools/parity/) at quick widths per section, the full set (every CSS
breakpoint and 1 px above) per sprint. Stable shots: motion off, reveal forced, clock frozen, maps and chat masked.

## 3. Folders

```
{{SITE_DIR}}/                      WordPress root
  BUILD-MAP.md, handoff.md, ai-handoff-summary.md   private (403, never deployed)
  _plan/                           plan docs and tools (private)
  _setup/                          seed, snapshots, mail copies, launch files (private)
<!-- starter:barebones -->
  wp-content/themes/{{THEME}}/     the theme: includes/, template-parts/, page-templates/, acf-json/, tests/parity/
<!-- /starter:barebones -->
<!-- starter:tw -->
  wp-content/themes/{{THEME}}/     the _tw project: tailwind/, javascript/, tests/parity/, and theme/ (what WordPress
                                   loads: includes/, inc/, template-parts/, page-templates/, acf-json/)
<!-- /starter:tw -->
```

## 4. Code standards

- Every global function, hook and constant prefixed `kitwp_` / `KITWP_`; text domain `kitwp`.
- PHP 8.1 to 8.4: no 8.2+ only features, nothing 8.2 to 8.4 deprecate. PHPCS with WordPress security, prefixes,
  i18n and PHPCompatibilityWP. php -l and the duplicate function check after every save.
- Escape at output; sanitise input; nonces and capability checks on anything custom.
- One partial per layout; partials get their data through `$args`.

## 5. ACF rules

JSON first (built by tools/acf/build_field_groups.py); keys stable; Theme Settings registered in PHP and read by
field key; "modified" bumped only for changed groups; per-group Sync links; return formats: image ID, link array.

## 6. Seeding

Exporters write `_setup/seed/`; Tools > Seeder (local only) writes WordPress in this order: media, settings, forms,
template pages, flexible pages, menus, SEO, redirects. Idempotent: the second run says "same" everywhere.

## 7. Forms and email

CF7 Form tab = the static form; the theme renders CF7's tags in the static markup. Native post, 303 to
/thank-you/ (works with JS off). Mail tab = the full HTML email with mail-tags; one HTML part, envelope sender and
Message-ID on the domain. Local: every email to the admin only, a copy in `_setup/mail/`.

## 8. SEO

Titles and descriptions verbatim; canonical = the page URL; robots index/follow (thank-you noindex); the static
JSON-LD rebuilt (SEO plugin schema off); old URLs as 301s (query strings passed); one H1, the static heading outline.

## 9. Security

No secrets in files or chats; DISALLOW_FILE_EDIT; private files 403 and left out of the package; REST user list
hidden from visitors; XML-RPC as the host sets it; debug off on live; only the plugins the task needs.

## 10. Performance

Parity first: any optimisation must keep the diff clean. Same fonts and preloads as static; images lazy except the
priority ones; caching rules in htaccess-live.txt. Lighthouse on the live server only.

## 11. Research sources (with the date checked)

- WordPress release notes, ACF and CF7 docs: list the pages read and the date.
