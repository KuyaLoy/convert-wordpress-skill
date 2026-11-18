# WordPress essentials

The WordPress rules every build follows, in one place. This file is a stable entry point: other skills (for
example figma-to-wordpress) read it by path, `<convert-to-wordpress>/references/wordpress-essentials.md`, and follow
the links in it; they never copy its rules. Headings stay the same between versions; details live in the files each
section names. `<kit>` is this skill's folder; in a project the tools are in `_plan/tools/`.

## Contents

- Plugins: local and live
- Local setup in one go
- Theme
- Fields: ACF PRO
- Forms and email
- SEO
- Security
- Speed
- Launch
- Live QA and handover
- Passwords and keys

## Plugins: local and live

| Plugin | Slug | Where | When |
|---|---|---|---|
| ACF PRO | `advanced-custom-fields-pro` (the developer's zip, profile `plugin_zips.acf_pro`) | local and live | Setup (default; Secure Custom Fields `secure-custom-fields` only if the developer asks) |
| Contact Form 7 | `contact-form-7` | local and live | Setup |
| Yoast SEO | `wordpress-seo` | local and live | Setup; seeded in the SEO phase |
| Redirection | `redirection` | local and live | Only when the site has old URLs to redirect |
| Duplicator (Pro) | `duplicator` or the developer's Pro zip | local | The move to live |
| Converter for Media | `webp-converter-for-media` | **live only** | Installed at launch: WebP for images uploaded later |
| Contact Form CFDB7 | `contact-form-cfdb7` | **live only** | Installed at launch: every enquiry kept in the database |
| A speed plugin that fits the host | per host | live, only if needed | Only when PageSpeed Insights misses a pass on a heavy design (Speed, below) |
| The profile's `extra_plugins` | per entry | per entry | `required` ones in Setup and on live; others when the entry says |

Never ACF PRO and Secure Custom Fields active together. Read `wp-content/debug.log` after every install.
Details: `references/setup.md` > Starter plugins, `references/launch.md` > After the installer.

## Local setup in one go

After the plan OK, without asking at each step (the plan lists the downloads):

```
python3 _plan/tools/setup/setup.py <wp_root>/_plan/site.json --profile <kit>/profile.local.json [--dry-run]
```

One command (doctor.py ran at intake): the local database if missing, WordPress with checksums, wp-config (local,
debug log, the `ACF_PRO_LICENSE` line), serve-wp.py when the local app has no site addresses, then install-wp.py: the default local admin from the profile's `local_admin` (username, e.g. `agency-dev`, email,
password), local sites only; permalinks `/%postname%/`, search engines discouraged, the fresh-install samples,
Hello Dolly and Akismet removed; Contact Form 7 and Yoast from wordpress.org with every file checked; ACF PRO from
the developer's zip; all activated. The developer pastes the ACF PRO licence into `ACF_PRO_LICENSE` in wp-config.
Details: `references/setup.md` > WordPress.

## Theme

Classic PHP theme, GPL. **Tailwind in the source or the design: _tw** (generated with the slug and prefix).
**Otherwise: Barebones.** `new-site.py` prepares it and copies the kit in (head, clean-up, ACF, media, forms, seeder,
schema, client admin). Every global prefixed; PHP 8.1 to 8.4; escape at output; after every PHP save `php -l`,
PHPCS and the duplicate function check. Details: `references/setup.md` > The starter theme, `references/build.md`.

## Fields: ACF PRO

Pages, not custom post types (URLs stay at the root). Fixed templates where pages share a layout; one Flexible
Content field ("Page Sections") for one-off pages. Field groups from `_plan/tools/acf/build_field_groups.py`
(stable keys, local JSON in `acf-json/`), synced with `sync.php`. Anything on two pages lives in Theme Settings (an
options page) with tokens (`{phone}`, `{year}`). Logos, the Site Icon, email images and content images go into the
Media Library and are set in fields, never hard-coded. The ACF menu shows to administrators, on live too. Seeded
by Tools > Seeder (local only; a second run says "same"). Details: `references/build.md` > ACF, Media, The seeder.

## Forms and email

Contact Form 7 holds each form and its email; the theme prints CF7's tags as the design's markup. Forms post
natively and answer 303 to `/thank-you/` (works without JavaScript); autop off. Every notification and auto-reply
uses the branded HTML template (logo and agency badge from Theme Settings), envelope sender and Message-ID on the
domain. Spam: the honeypot plus reCAPTCHA v3. Local mail goes to `_setup/mail/`. Thank-you and 404 pages always
exist (thank-you noindex). Details: `references/forms-email.md`, `references/build.md` > Thank-you and 404.

## SEO

Standard by default: Yoast seeded (its schema replaced by the theme's JSON-LD), a title, description and canonical
per page, one H1 and a clean heading order, alt text, robots and the sitemap, `/thank-you/` noindex, old URLs as
301s (query strings kept), tracking as the task says. Details: `references/seo-security.md`.

## Security

No secrets in files or chats; private files (`_plan/`, `_setup/`, handoff files, BUILD-MAP.md, debug.log) answer
403; REST users hidden; file editing off; nonces and capability checks; input sanitised, output escaped; debug off
on live; the installer removed after the move; the client gets their own Editor login. Details:
`references/seo-security.md` > Security.

## Speed

Built to Core Web Vitals from the first section: LCP preload and `fetchpriority`, sized srcset in WebP, nothing lazy
above the fold, reserved media space, metric-matched fallback font, minimal deferred JavaScript, caching and
compression in `.htaccess`. Aim: PageSpeed Insights passes on live (mobile and desktop); it is a target, not a
must. A heavy design that misses it gets a speed plugin that fits the host (the host's own cache, e.g. LiteSpeed
Cache on LiteSpeed); the design is never changed for a score, and parity is checked again after. Details:
`references/seo-security.md` > Performance.

## Launch

Backup of the live site, a Duplicator package (filters from `duplicator-filters.py`), the old site moved aside for
rollback, the installer, then: production in wp-config, debug off, `.htaccess` from `htaccess-live.txt`, search
engines allowed, permalinks saved, licences and reCAPTCHA keys (the developer), tracking, **Converter for Media and
Contact Form CFDB7 installed and active**, debug.log read once. Details: `references/launch.md`.

## Live QA and handover

`live-qa.py` on the live host, tracking checked, three test leads with the real submit button, PageSpeed Insights,
the report as one PDF, the client pack (website sheet, editing guide, message). Details: `references/qa-report.md`,
`references/handover.md`.

## Passwords and keys

The agent never types a password, licence key or API key, with one exception: the developer's **default local
admin password**, which install-wp.py reads from `profile.local.json` (never committed) for a local site only,
passes to PHP through the environment, and never prints. Live admins get their own strong password, typed by the
developer; reports say `[PASTE PASSWORD HERE]`.
