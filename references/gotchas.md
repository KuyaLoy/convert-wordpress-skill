# Gotchas (keep adding)

Each one cost real time on a build. Read the section you are working in; add new lessons here and in the
project's handoff.md (Failed Attempts) as they happen.

## WordPress and PHP

- A form field named `name`, `s`, `p`, `m`, `page` or `year` (any public query var) makes the form post answer 404:
  WordPress reads query vars from POST. Keep `kitwp_lead_query_vars()`.
- A duplicate function name across two include files takes the site down, and php -l cannot catch it. After EVERY
  PHP save: `grep -h "^function" includes/*.php | sed 's/(.*//' | sort | uniq -d` must print nothing.
- A `*/` inside a PHP docblock ends the comment early (for example a `sed 's/(.*//'` example): use `//` comments.
- The kit used to hide the WordPress toolbar for everyone (`show_admin_bar` false) to keep pages 1:1; the developer
  missed Dashboard and Edit Page on the front end. Visitors never get the toolbar, so it stays on for logged-in
  users. A sticky static header then slides under it: set `KITWP_ADMIN_BAR_CSS` (header `top` by
  `--wp-admin--admin-bar--height`, and every other place the static CSS uses the header height, such as a mobile
  menu panel below it). The static `<body>` has no WordPress classes, so `.admin-bar` selectors do not apply.
  Check logged in at 1440, 700 and 390 (menu open: its close button clickable), and that the logged-out HTML is
  byte-identical.
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

- The bulk "Sync changes" did nothing on the reference build: use `sync.php` or each group's own Sync link.
- Field groups left as JSON only (never synced) still work on the site, but ACF > Field Groups shows every one
  under "Sync available" and the developer reads it as broken. Run `sync.php` until it says "Nothing to sync".
- Theme Settings registered only in PHP (`acf_add_options_page`) never shows in ACF > Options Pages: the developer
  looked for it there and thought it was missing. Ship it as the builder's options page JSON; PHP is the fallback.
- A generator that made one field per rendered text node (to reach 1:1 fast) gave up to 280 fields per page:
  sentence pieces (", from a"), "/" separators, breadcrumbs, chip and accordion text twice, numbered fields instead
  of repeaters. 1:1 held, but the developer rejected it as not client friendly. Model fields on the source's content
  files; keep 1:1 in the templates.
- Set `modified` only for groups that changed (the builder does), or every group asks to sync.
- Field edits on live write JSON into the live theme's `acf-json/`: copy it back to local.
- Theme Settings read by field key render a default even when nobody saved the setting; read by name they do not.
- The Redirection plugin creates its tables in its own setup screen (or `wp redirection database install`), not on
  activation: the seeder's redirects step says so and stops until then.
- ACF returns `false` or `null` for an empty repeater: loop over `kitwp_rows()`.
- The seeder's second run must say "same" everywhere; anything else is a bug in the seed or the hash.
- Secure Custom Fields (free) runs the kit's field groups, options page, seeder and `get_field()` as ACF PRO does;
  only the menu name differs (SCF). The flexible content field is `page_sections`, not `sections`.
- `new-site.py --force` used to replace `build_field_groups.py`, which by then holds the site's content model: it
  is kept now, like the parity routes and settings.
- ACF returns false (not []) for a repeater, flexible field or multi-select with nothing in it, and `(array) false`
  is `[false]`: one blank row (and "array offset on bool" warnings). Loop over `bah_rows()`-style guards
  (`is_array() ? ... : []`); test every template with its lists emptied.
- JSON-LD printed with `wp_json_encode()` needs "<" escaped (`\u003c`, as React's JsonLd does, or JSON_HEX_TAG):
  a `</script>` typed into a field otherwise ends the script. Check the escape really changes something.
- With no Site Icon set, WordPress answers /favicon.ico with its own "W" logo: hook `do_favicon` to the brand icon.

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
- Content changed on purpose (real phone/email instead of the source's placeholders): swap it on the reference with
  `refReplace` AFTER the page settles. React hydration re-renders text after "load" and undoes an early swap.

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
- With no mail program (XAMPP, MAMP, WampServer, serve-wp), every local form answered "There was an error trying
  to send your message", so the thank-you flow could not be tested. On local, when PHP cannot send, the kit keeps
  the email in `_setup/mail/` and reports it as sent (`kitwp_mail_to_file` forces either way).

## Static sources

- Never inject GTM into built Next.js HTML: React hydration error #418 on every page.
- Upload the built `out/`, never the repo zip. `robots.ts` and `sitemap.ts` need `dynamic = 'force-static'`.
- Stop `npm run dev` before a build.
- React prints no whitespace between tags: strip it in templates (inline-block gaps), tab-only gaps and the buffer
  edges included.

- PHP sources: `.htaccess` strips `.php` and may drop the trailing slash (`/thankyou`, not `/thankyou/`). Keep the
  same URLs in WordPress, or 301 the old form; the PHP built-in server needs a router that does what `.htaccess`
  does.
- PHP sources load `config/env.php` and `.env` before anything else: the golden-master copy gets a stub that
  returns blank values. The real files hold SMTP and reCAPTCHA keys and stay on the developer's machine.
- Asset URLs with a cache-busting query (`style.min.css?v=1790926827`) change on every build: the DOM diff
  compares the path, not the query.
- AOS hides `[data-aos]` until it adds `aos-animate`: the parity reveal rule must add that class (new-site.py sets
  it when analyze-source.py finds AOS), or every screenshot is blank below the fold.

- Swap test with the theme on another origin than the page: the fonts are blocked (no CORS header) and the diff
  looks like a broken CSS. swaptest.py copies the theme assets next to the pages so both load from one origin.
- Region screenshots of a footer under an empty WordPress `<main>`: the footer sits at another fractional offset
  (text 1 px off) and fixed overlays (cookie bar, chat button) land on different parts of it. Hide `main` and the
  overlays on both sides (region-check.mjs does by default for `main`).
- Some static sources never close `</body></html>`: split the golden master at `</main>` and take the rest.
- Google Fonts preconnects on a site with self-hosted fonts are extra head tags: KITWP_PRECONNECT_FONTS is on only
  when site.json has Google font links.

- PHP sources keep content in PHP variables (`data/global-content.php`): `seed/php-content.php` turns them into the
  content.mjs that export.mjs reads. Their config also holds lead recipients (Bcc, CC, CRM inboxes): those are
  never exported or printed; site.json's lead block gets them from the intake.
- The example seed files are examples: the media step fails on the example image until export.mjs writes real
  files. Settings and menus seeded twice: the second run says "same".

## Live and hosting

- LiteSpeed can serve a soft 404 (status 200) on a repeat request: check the 404 twice.
- Imunify360 can answer scripted requests with "One moment, please" or 415: check from a real browser.
- Zips made in some VMs keep 0700 modes and LiteSpeed answers 403: set 0644 files and 0755 folders before zipping.
- A zip left in `public_html` is public: remove it after extracting.
- Free Duplicator 5 may build a `.daf` archive (DupArchive) instead of a zip: the same rules, it holds the whole
  site and database. The installer also leaves `dup-installer/` and a boot log: remove them all.
- A cloned starter theme brings its `.git` folder: the Duplicator filters leave git folders out.
- A live wp-config left on `local` loads the seeder and sends every lead to the admin only.
- Contact Form 7 6.2 needs PHP 8.3: below that its Composer platform check is a fatal error on every page. Check the
  PHP version the host runs for the domain (cPanel > MultiPHP Manager) before the upload. When the host's version
  differs from the local one, dry-run the site on it first: `php -S 127.0.0.1:8781 -t <wp_root>
  _plan/tools/setup/wp-router.php` with that PHP, then `curl -H "Host: <site>.test"` a few routes (GET only).
- A plugin that registers itself with an outside service on activation (it sends `home_url()`) registers the local
  URL if activated locally, and probes the old site if activated on the new server before DNS moves. Activate it on
  live once DNS points there.
- After any plugin install, read debug.log: a second copy of a plugin gives "Cannot redeclare" fatals.
- The REST user list shows the admin username to visitors unless hidden.
- The developer may install plugins on live after the move: list them before the handoff.
- The shared PageSpeed API key runs out: run Lighthouse yourself, or pagespeed.web.dev in a browser.
- Duplicator's installer replaces `.htaccess` on extraction and moves `php.ini`, `.user.ini` and the host's
  `.htaccess` into `dup-installer/`: the archive is public until the clean-up, and the host's PHP settings and
  cPanel block need restoring (launch.md).
- After the DNS switch, the developer's own browser can keep the old IP for up to the old TTL (Chrome has its own
  cache: chrome://net-internals/#dns, Clear host cache). Phones on mobile data see the new site first.
- A local site with the live leads key sends its test submissions to the live leads portal: keep lead forwarding
  off while `WP_ENVIRONMENT_TYPE` is local.
- Parity against a preview deployment (Vercel, Netlify) on live: the preview is noindex, so `seo:robots` differs
  by design; Yoast prints no canonical while the site discourages search engines.

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
- The first HTML file a folder walk finds is often not the home page (about.html sorts before index.html): read
  site-wide facts such as the `<html lang dir>` attributes from `index.html` nearest the top.
- Work on a copy of the source (`get-source.py`), never the folder the developer gave: an `npm install` or a build
  changes it, and a source folder can be tied to a live site.
- `python3` on Windows is often missing, or opens the Microsoft Store (an alias in WindowsApps): doctor.py prints the
  command that works (`py -3`, `python`).
- PHP's built-in server with one process cannot answer WordPress calling itself: Duplicator's scan waited 45 s
  and its build only ran with the Backups page open. serve-wp.py runs four workers on macOS and Linux (Windows
  has one: keep that page open). Its PID file and log go in `_setup/`, never the web root.
- Composer run as root (containers, some VMs) skips its plugins, so PHPCS finds no WordPress standards: run
  `composer run-script post-install-cmd` once after `composer install`.
- A site in a subfolder address (`http://localhost/my-site/`) changes every link, so the diffs fail: give it its own
  address (the app's `<site>.test`, Local's `<site>.local`, or serve-wp.py on a port).
- Local and Herd serve with Nginx: `.htaccess` rules do nothing there (fine locally; the launch package leaves the
  private files out).
- Every `https` link is not a git repository: a live website goes to the capture, a zip link is downloaded, a GitHub
  `/tree/<branch>/<folder>` link keeps only that folder. Logins and tokens inside links are never printed or saved.
- A zip with a password cannot be opened by the script: the developer unzips it and gives the folder.
- A source that is already WordPress (wp-config.php, wp-includes) is not a conversion: get-source.py stops (exit 4).
- Projects inside OneDrive, Dropbox or iCloud folders are slow and can clash while syncing: build outside them.
- Updating the skill does not change a project already started: it keeps its own copy of the tools in `_plan/tools/`
  and the theme. `new-site.py <wp_root>/_plan/site.json --force` refreshes them (kit code only, backup first).
- An agent reads a skill when the chat starts: after an update, start a new chat.
- cPanel UAPI works from a logged-in cPanel tab (`fetch('/cpsess<N>/execute/Fileman/...')`): list, save, upload
  and trash files without the File Manager UI. `save_file_content` writes CRLF line endings (fine for PHP and
  `.htaccess`). Never read wp-config whole into the chat: edit it in the page and print only the changed lines.
- Browser upload tools cap single files (10 MB): for a bigger archive, serve it on `127.0.0.1` with CORS for the
  cPanel origin and `Access-Control-Allow-Private-Network: true`, and let the cPanel page fetch and upload it. Chrome
  may hold such requests from other sites behind a local-network permission prompt.
