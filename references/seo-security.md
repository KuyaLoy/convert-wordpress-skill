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

- One H1 per page; headings in order (the static outline kept, no levels skipped that the static page did not
  skip); checked on every section, not at the end.
- `/thank-you/`: noindex, out of the sitemap, and reached after every lead (the conversion fires there).
- Every static route in the sitemap, with the same slug; pages the static site lacked (a blog) are flagged to
  whoever owns SEO.

## Old URLs and redirects

- Every old URL (`_plan/OLD-SITE-URLS.md`: the old sitemap, the REST counts, the designer's map, archive and
  theme-part URLs, campaign URLs) is KEEP or a 301 target, in `_setup/seed/redirects.json`.
- Only when there are old URLs: install Redirection (ask first). No old URLs, no Redirection, and the seeder's
  redirects step is skipped.
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

WCAG 2.2 AA as the static site delivers it, and never worse, checked per section from the first one: landmarks
(`header`, `nav` with labels, `main id="main"`, `footer`), a skip link if the static has one, one H1, alt text on
every content image from the Media Library (decorative: `alt=""`), an `aria-label` on every control without visible
text (icon buttons, the menu toggle, social links), labelled form fields, `aria-expanded` and focus handling on
menus and pop-ups as static, keyboard reachable, reduced motion respected. The UX and QA gates check it each sprint.

## Security

- **No secrets** in files, chats, commits or reports. The developer types passwords and keys; reports say
  `[PASTE PASSWORD HERE]`.
- wp-config: `DISALLOW_FILE_EDIT` true; on live `WP_DEBUG` false and `WP_ENVIRONMENT_TYPE` production.
- **Private files:** `_plan`, `_setup`, BUILD-MAP.md, the handoff files and debug.log answer 403 (the root
  `.htaccess` block) and are left out of the package (duplicator-filters.py). The installer files and the archive
  are gone after the move (`htaccess-live.txt` blocks them too).
- **Code:** escape at output, sanitise input, nonces and capability checks on anything custom, prepared SQL,
  prefixed globals. The seeder and snapshots run only on `local`.
- The REST user list (`/wp-json/wp/v2/users`) shows usernames to visitors: `kitwp_rest_hide_users()` hides it
  (filter `kitwp_hide_rest_users` to keep it).
- XML-RPC as the host sets it; only the plugins the task needs; the admin username not "admin".
- File modes 0644 and folders 0755 (zips made in some VMs keep 0700 and LiteSpeed answers 403).

## Performance

**Build to Core Web Vitals from the first section**, not as a clean-up at the end. Parity first: an optimisation
must keep the diff clean, so with a golden master each item matches or beats the static page without changing a
pixel; for pages and sections the build writes itself, every item applies in full.

- **LCP image:** a head preload (`kitwp_preload_image()`) and `fetchpriority="high"` on it and its `<img>`
  (`'fetchpriority' => 'high'` in `kitwp_img()`; with a golden master only where the static build prints it, or
  accepted as an addition in the DOM diff). Never `loading="lazy"` above the fold; everything below it lazy.
- **Sized srcset:** the static widths and a `sizes` that matches the layout (`KITWP_IMAGE_WIDTHS`), WebP.
- **Reserved space:** width and height (or `aspect-ratio`) on every image, video and iframe, so nothing shifts.
- **Fonts:** the static fonts and preloads, `font-display: swap`, and a metric-matched fallback font, so the swap
  does not move the text. next/font sources already ship one in the compiled CSS; otherwise add it:

  ```css
  @font-face { font-family: "Inter Fallback"; src: local("Arial");
    size-adjust: 107%; ascent-override: 90%; descent-override: 22%; line-gap-override: 0%; }
  /* then: font-family: Inter, "Inter Fallback", sans-serif; (values from a fallback-metrics tool, per font) */
  ```
- **Minimal JavaScript, deferred:** vanilla, `defer` or after the load event (the chat widget, maps below the
  fold), no jQuery for theme code; the static site's own scripts deferred as they were.
- **No speed plugin** (caching, minify, lazy-load, "optimisation" suites) unless the theme cannot do it; caching
  and compression rules are in `htaccess-live.txt`. Converter for Media stays (S1-02): it serves WebP for images
  the client uploads later.

**Measure:** local Lighthouse is a regression guard only (a local stack is not representative): run it after a
big change to catch a drop. The real check is **PageSpeed Insights** (pagespeed.web.dev, mobile and desktop) on
staging, when the build has a public one, and on live. Mobile performance is mostly third-party (reCAPTCHA, tags)
and icon fonts; report the field and lab numbers honestly.
