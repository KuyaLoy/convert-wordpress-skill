# Gotchas (keep adding)

Each one cost real time on a build. Read the section you are working in; add new lessons here and in the
project's handoff.md (Failed Attempts) as they happen.

## WordPress and PHP

- A form field named `name`, `s`, `p`, `m`, `page` or `year` (any public query var) makes the form post answer 404:
  WordPress reads query vars from POST. Keep `kitwp_lead_query_vars()`.
- A duplicate function name across two include files takes the site down, and php -l cannot catch it. After EVERY
  PHP save: `grep -h "^function" includes/*.php | sed 's/(.*//' | sort | uniq -d` must print nothing.
- A `*/` inside a PHP docblock ends the comment early (for example a `sed 's/(.*//'` example): use `//` comments.
- Build a PHP file completely before it replaces a live one: placeholder edits are a parse error on live.
- WordPress texturizes titles: `&` becomes `&#038;`. Print raw titles (`kitwp_title()`), menu titles too.
- `esc_url()` turns `&` into `&#038;` in an iframe src: use `esc_attr( esc_url_raw() )`.
- The theme activation link in `_wpThemeSettings` is HTML-encoded (`&amp;`): decode it before using it.
- An old PHP build (8.1.x on the reference build) could not reach wordpress.org over HTTPS: use 8.3 or 8.4 locally.
- Barebones is a classic PHP theme, not a block theme. Read a repo's files before ruling it out.
- Barebones' own `includes/acf.php` hides the ACF menu outside the "development" environment (so on local and on
  live): new-site.py moves it aside. Hiding the ACF menu also hides the licence page. Never hide it.
- PHP's opcache can serve the old `wp-config.php` for a couple of seconds after an edit: wait before testing a
  config change (an environment switch looked broken in testing until then).
- Nginx ignores `.htaccess`: on an Nginx stack the private-files block does nothing. Add the same deny rules to the
  server config, and remember the private files are never deployed (Duplicator filters).

## ACF and the seeder

- The bulk "Sync changes" did nothing on the reference build: use each group's own Sync link.
- Set `modified` only for groups that changed (the builder does), or every group asks to sync.
- Field edits on live write JSON into the live theme's `acf-json/`: copy it back to local.
- Theme Settings read by field key render a default even when nobody saved the setting; read by name they do not.
- The Redirection plugin creates its tables in its own setup screen (or `wp redirection database install`), not on
  activation: the seeder's redirects step says so and stops until then.
- ACF returns `false` or `null` for an empty repeater: loop over `kitwp_rows()`.
- The seeder's second run must say "same" everywhere; anything else is a bug in the seed or the hash.

## Parity and screenshots

- Map iframes never reach network idle: fixed waits.
- Scroll reveal leaves half-faded sections: force the reveal class in the shot tools.
- An image can swap srcset mid-shot (Chrome re-picks on resize): grow the viewport first and wait for images.
  Never chase a 0.1 to 0.3% band before checking that.
- next/image leaves small widths out of srcset when sizes uses vw; the DOM diff ignores srcset, so compare srcsets
  separately.
- One wild shot with fallback fonts (20% and more) is a web font that loaded late under load: re-run that shot.
- SVG paths typed by hand had typos: copy them by script.
- Keeping every parity screenshot filled 1.7 GB: keep only failures (the default).

## Forms and email

- A multipart email with an inline (CID) logo was blocked by the host's outgoing filter (550 5.7.1): one HTML part,
  no attachments, the logo by URL, From on the domain, envelope sender set.
- CF7's `get_id_option()` returns the id once per request; select values post as arrays; error tips need
  `wp_strip_all_tags()`.
- Adding a CF7 form tag never replaces CF7's own: remove first.
- The chat's REST post: a JSON body gets 415; a missing `_wpcf7_unit_tag` gets 400.
- reCAPTCHA keys work only on the domains listed in Google's console: add the local host too.
- CF7 validates before its spam check: a honeypot test with invalid fields shows the field errors, not the
  thank-you page. Test the honeypot with valid fields.
- A mail-tag for a field the form does not have prints as text (`[postcode]`): the kit empties the lead fields a
  form does not post (`kitwp_lead_fields`), so "Exclude lines with blank mail-tags" drops the row.
- The local URL (`.test`) is not the From domain: the mail rules check `KITWP_DOMAIN` (the live domain), so local
  mail is built exactly as on live (one HTML part, Message-ID and envelope sender on the domain).

## Static sources

- Never inject GTM into built Next.js HTML: React hydration error #418 on every page.
- Upload the built `out/`, never the repo zip. `robots.ts` and `sitemap.ts` need `dynamic = 'force-static'`.
- Stop `npm run dev` before a build.
- React prints no whitespace between tags: strip it in templates (inline-block gaps), tab-only gaps and the buffer
  edges included.

## Live and hosting

- LiteSpeed can serve a soft 404 (status 200) on a repeat request: check the 404 twice.
- Imunify360 can answer scripted requests with "One moment, please" or 415: check from a real browser.
- Zips made in some VMs keep 0700 modes and LiteSpeed answers 403: set 0644 files and 0755 folders before zipping.
- A zip left in `public_html` is public: remove it after extracting.
- A live wp-config left on `local` loads the seeder and sends every lead to the admin only.
- After any plugin install, read debug.log: a second copy of a plugin gives "Cannot redeclare" fatals.
- The REST user list shows the admin username to visitors unless hidden.
- The developer may install plugins on live after the move: list them before the handoff.
- The shared PageSpeed API key runs out: run Lighthouse yourself.

## Agent tooling

- Browser tools can block output that looks like cookies or query strings: strip `=`, `;` and `?`. Long loops time
  out: start them async, keep the results on `window`, read them in a second call.
- A browser click by element reference can fire before the scroll: scroll, screenshot, click by coordinate, check
  the URL.
- The browser tool may be driving a different browser profile that cannot resolve `.test` names.
  `DNS_PROBE_FINISHED_NXDOMAIN` on `.test` usually means the local stack is not running.
- A cloud shell cannot reach the developer's `.test` sites, and a file bridge to the developer's machine may cap file
  sizes (20 MB on the reference build) and add metadata to images (the md5 changes; harmless).
- A file re-copied under the same staged name can arrive with the OLD content: use a new name and check the md5 on
  the other side after every copy.
- `pkill -f` in a shared shell can kill your own shell (the pattern matches the command running pkill): match the
  process exactly (`pgrep -f "^php -S"`) and kill by PID.
- `wp package install` can fail behind a proxy that injects tokens; the _tw generator also works in the browser
  (underscoretw.com) and gives the same zip.
- Research links found before a context reset are lost: write sources (with the date checked) into ARCHITECTURE.md
  as you go. Re-check plugin versions right before installing.
