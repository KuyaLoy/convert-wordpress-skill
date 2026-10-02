# SEO, tracking, accessibility, security, performance

Read this in Sprint 6, and in Sprint 1 for the security basics. Code: the theme's `seo.php`, `schema.php`,
`cleanup.php`, `head.php`; seed files: `seo.json`, `og-images.json`, `redirects.json`.

## Contents

- The SEO plugin, seeded
- JSON-LD rebuilt from the page
- Headings, thank-you page, sitemap
- Old URLs and redirects
- Tracking
- Accessibility
- Security
- Performance

## The SEO plugin, seeded

Yoast SEO by default (decision D3; ask before installing). The seeder's SEO step writes:

- **Head clean-up on:** feeds, shortlinks, REST and oEmbed links, RSD and WLW, generator, emoji, powered-by and
  pingback headers.
- **Campaign URL clean-up and permalink clean-up OFF** (`clean_campaign_tracking_urls`, `clean_permalinks`):
  campaign URLs and their tags must keep working.
- Author, date, attachment and format archives off; categories and tags noindex; the sitemap on.
- Company name and logo, the default share image, and each page's share image from the static build
  (`og-images.json`); page types for About and Contact (`seo.json` page_meta).
- Titles and descriptions verbatim from the static pages (in each page's seed row).

Theme filters (`seo.php`): `og:type` website and the static `og:locale`; robots limited to index/follow or
noindex/follow, nothing else; robots.txt equal to the static one plus `Sitemap: /sitemap_index.xml`. WordPress core
still adds `max-image-preview:large` to robots: accept it, or remove the core filter if the head must match exactly.

## JSON-LD rebuilt from the page

The SEO plugin's schema is off (`wpseo_json_ld_output`). `schema.php` prints the static site's blocks from the
page's own content: the business (Organization or a LocalBusiness type, `KITWP_SCHEMA_TYPE`, phone in
international form), Service on the service templates, a place list on location templates (an `areas` repeater), the
area served, Article on posts, AboutPage and
ContactPage, one FAQPage for every FAQ printed on the page (partials call `kitwp_schema_add( 'faq', $rows )`), and
BreadcrumbList. Values nobody filled are left out, not printed empty. Compare every route's head and JSON-LD with the
static page (the parity SEO diff).

## Headings, thank-you page, sitemap

- One H1 per page; the static heading outline kept (no levels skipped that the static page did not skip).
- `/thank-you/`: noindex, out of the sitemap, and reached after every lead (the conversion fires there).
- Every static route in the sitemap, with the same slug; pages the static site lacked (a blog) are flagged to
  whoever owns SEO.

## Old URLs and redirects

- Every old URL (`_plan/OLD-SITE-URLS.md`: the old sitemap, the REST counts, the designer's map, archive and
  theme-part URLs, campaign URLs) is KEEP or a 301 target, in `_setup/seed/redirects.json`.
- The seeder writes them into the Redirection plugin (editable in Tools > Redirection): 301, query strings passed
  on, case and trailing slash ignored, permalink monitor on, logs on, no IP logging. A source that already has a rule
  is left as it is.
- `.htaccess` does only host rules (http and www to https non-www in one hop).
- Check every old URL locally, and again on live (live-qa.py).

## Tracking

- GTM as the tracking task asks: the head snippet at the top of `<head>` (right after the required meta tags) and
  the noscript right after `<body>`, on every page including `/thank-you/`. A tracking plugin or the theme's
  `wp_head` priority 0 and `wp_body_open`; the profile says which.
- Conversions fire on the thank-you page only; prove it with `track.mjs` on live.
- Never inject GTM into a built Next.js page (hydration errors); in the Next source use `next/script`.
- Campaign and landing page URLs never change.

## Accessibility

WCAG 2.2 AA as the static site delivers it, and never worse: landmarks (`header`, `nav` with labels, `main
id="main"`, `footer`), a skip link if the static has one, one H1, alt text from the Media Library, labelled form
fields, `aria-expanded` and focus handling on menus and pop-ups as static, keyboard reachable, reduced motion
respected. The UX and QA gates check it each sprint.

## Security

- **No secrets** in files, chats, commits or reports. The developer types passwords and keys; reports say
  `[PASTE PASSWORD HERE]`.
- wp-config: `DISALLOW_FILE_EDIT` true; on live `WP_DEBUG` false and `WP_ENVIRONMENT_TYPE` production.
- **Private files:** `_plan`, `_setup`, BUILD-MAP.md, the handoff files and debug.log answer 403 (the root
  `.htaccess` block) and are left out of the package (duplicator-filters.py). `installer.php` and archives answer
  404 after the move.
- **Code:** escape at output, sanitise input, nonces and capability checks on anything custom, prepared SQL,
  prefixed globals. The seeder and snapshots run only on `local`.
- The REST user list (`/wp-json/wp/v2/users`) shows usernames to visitors: `kitwp_rest_hide_users()` hides it
  (filter `kitwp_hide_rest_users` to keep it).
- XML-RPC as the host sets it; only the plugins the task needs; the admin username not "admin".
- File modes 0644 and folders 0755 (zips made in some VMs keep 0700 and LiteSpeed answers 403).

## Performance

Parity first: an optimisation must keep the diff clean. The same fonts, preloads and image widths as static;
images lazy except the priority ones; the static site's own scripts deferred as they were. Caching and compression
rules are in `htaccess-live.txt`. Measure with Lighthouse on the live site only (a local stack is not
representative): mobile performance is mostly third-party (reCAPTCHA, tags) and icon fonts; report the numbers
honestly.
