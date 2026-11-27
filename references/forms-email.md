# Forms and email: Contact Form 7, 1:1

Read this in P3. The code is the theme's `includes/forms.php` (CF7 setup, ids, redirect) with one file per job:
`forms-controls.php` (tag markup), `forms-spam.php` (honeypot, reCAPTCHA), `forms-mail.php` (mail tags, branded
mail), `forms-local-mail.php` (local capture) and `forms-portal.php` (the leads portal); the seed files are `_setup/seed/forms.json`,
`quote-form.txt`, `chat-form.txt` and `lead-email.html`.

## Contents

- The pattern: CF7 holds the form, the theme prints the static markup
- Posting, the thank-you redirect, errors
- Field names that break WordPress
- The email: one HTML part
- The auto-reply and the agency badge: one look for both emails
- Spam: honeypot and reCAPTCHA v3
- The chat widget through CF7's REST endpoint
- Where the lead came from (form attribution)
- Upgrading a kit site to the attribution standard
- Form layout
- The leads portal
- Where leads are stored: CFDB7 only
- Local mail capture
- Proving delivery

## The pattern: CF7 holds the form, the theme prints the static markup

Editors change forms and emails in Contact > Contact Forms, and the visitor sees exactly the static form.

- The **Form tab** holds the form: labels, placeholders, options, the button, in the static markup around CF7's
  tags. The theme prints CF7's text, email, tel, url, select, textarea and hidden tags as the static HTML
  (`kitwp_cf7_control()`) and drops CF7's wrapper (`kitwp_cf7_clean()`), so the `<form>` carries the static class
  (`KITWP_FORM_CLASS`).
- **Remove before you add:** `wpcf7_remove_form_tag()` first, then `wpcf7_add_form_tag()`. Adding never replaces a
  handler CF7 registered.
- Tag syntax: options before quoted values: `[text* name id:name autocomplete:name placeholder "e.g. Sam Lee"]`.
- CF7's JS and CSS are off (`wpcf7_load_js`, the clean-up). **Autop is off on every form** (`forms.php`), so CF7
  adds no stray `<p>` or `<br>` around the fields, and empty paragraphs are removed. CF7's response box becomes the
  static form note.
- Per page: the service options come from the page (`wpcf7_form_tag` filter accepts the posted value), a
  `[hidden source]` tag records where the lead came from (`home`, `service:<slug>`, `popup:<path>`, `chat:<path>`),
  and a compact variant can drop fields.
- **Two forms on one page never share ids:** the pop-up copy gets an id prefix (`qm-`), and every `for` too.

## Posting, the thank-you redirect, errors

- Forms post natively, as the static form did, with or without JavaScript.
- On `template_redirect` the theme answers **303 to `/thank-you/`** (`KITWP_THANK_YOU`) for: mail sent, mail failed
  (logged), honeypot hit. The thank-you page is where the conversion tags fire, so it must be reached every time.
- Any other result (a required field empty, an invalid email) shows the page again with CF7's messages and the
  values kept. Error tips need `wp_strip_all_tags()`.
- Select values post as arrays: flatten with `wpcf7_flat_join()`.
- CF7's `get_id_option()` returns the id once per request: read the raw option instead.

## Field names that break WordPress

WordPress reads query vars from POST. A field named `name`, `s`, `p`, `m`, `page`, `year` (and other public query
vars) makes the form post answer 404: on the reference build it looked for a post named after the visitor.
`kitwp_lead_query_vars()` takes those vars from the URL only for CF7 posts. Keep that filter whenever the static
form uses such names.

## The email: one HTML part

- The **Mail tab** holds the full HTML email (`lead-email.html`, with `<html>` in it so CF7 does not wrap it):
  one table row per field, "Exclude lines with blank mail-tags" on, field values escaped, the message with line
  breaks kept.
- Special mail tags for what CF7 cannot know: `[_<key>_subject]`, `[_<key>_preheader]`, `[_<key>_tel]`,
  `[_<key>_email]`, `[_<key>_when]`, `[_<key>_via]`, `[_<key>_page]`, `[_<key>_received]`, `[_<key>_logo]`,
  `[_<key>_site]`, `[_<key>_year]` (`kitwp_lead_special_tags()`).
- Reply-To `[email]` only when the visitor gave a valid email.
- **Delivery:** ONE HTML part, no attachments, the logo by URL. CF7 adds a plain-text part, so the theme clears
  `AltBody` at `phpmailer_init` priority 20, and sets the envelope sender and a Message-ID on the site's domain.
  On the reference build's host (MailChannels), a multipart email with an inline (CID) logo was blocked:
  "550 5.7.1 Message blocked".
- From: `<Site> <no-reply@domain>` on the site's own domain. To: the client's inbox. Bcc: the profile's list. All
  three come from forms.json, so they stay editable in CF7.

## The auto-reply and the agency badge: one look for both emails

**Every form's notification and auto-reply use the branded HTML template**, never CF7's plain-text default: the
seeder refuses an email file that is not a full HTML document and reports a form that has no auto-reply.

- The visitor gets an auto-reply (CF7 Mail (2)) in the **same branded HTML template** as the lead email
  (`autoreply-email.html`: logo header, "Hi [_<key>_name],", the thank-you line, the client's phone and email,
  sign-off). Never CF7's plain-text default: it reads as an afterthought next to the branded lead email.
  forms.json per form: `autoreply_file`, `autoreply_subject`, `autoreply_to` (`[email]`; the referral-style form
  that has `referrerEmail` uses that), `autoreply_reply_to` (the client's inbox). "Use HTML content type" on.
- **Agency badge in both footers, always:** every form's lead email and auto-reply use the branded HTML template
  (`lead-email.html`, `autoreply-email.html`: the logo and badge mail-tags) and end with the badge, linked (hidden
  only with the client's recorded request, as the footer badge: build.md). `self-check.py` (the seeded forms; the
  database with `--wp`) and `live-qa.py --wp "wp @live"` fail on a form whose email or auto-reply is not the
  branded template, is plain text or has no auto-reply. The badge is `[_<key>_badge]`: Theme Settings > Branding
  "Email badge", else config.php `<PREFIX>_EMAIL_BADGE*` (the builder copies the PNG to `theme/assets/email/`).
  Use a **PNG at 2x** (email clients do not show SVG or WebP). A white badge sits on the brand-colour footer strip
  that both templates have.
- The site's own footer always carries the same badge (SVG is fine on the web): build.md > Agency badge.
- Check both emails on live: one test lead per form, then look at the client's copy (lead email) and the
  visitor's copy (auto-reply): same header, same footer, badge showing and linked.

## Spam: honeypot and reCAPTCHA v3

- The static honeypot field (`company` in the example) is checked at `wpcf7_spam` priority 1: a hit goes to the
  thank-you page with no email.
- **reCAPTCHA v3** through CF7's own integration (Contact > Integration, the developer pastes the keys). CF7's
  script only fills forms with its `wpcf7-form` class, which the static markup does not have, so the theme asks
  Google for a fresh token on submit (`assets/recaptcha.js`, the site key passed as data, no inline script) and
  fills `_wpcf7_recaptcha_response` itself.
- **A failed post is never silent:** CF7's response box stays, as `role="alert"`; after spam, an aborted post or a
  failed send it adds the Theme Settings phone (or fills `{phone}` where the Messages tab has it), so the visitor
  can still reach the business.
- Without JavaScript there is no reCAPTCHA token, so CF7 marks the post spam. That stays the default (reCAPTCHA
  strict). `KITWP_NOJS_LEADS` true keeps such a post when the honeypot is empty and a signed time stamp shows the
  form was open 3 seconds to 7 days; turn it on only for a site whose visitors post without JavaScript, and watch
  the spam.
- `KITWP_RECAPTCHA_LAZY` false (the default, proven on a live site): Google's script loads on every page.
  true: it loads on the first touch of a form or the chat, with a 10 second fallback. Faster on phones; retest
  every form on live before shipping it.
- Keys are domain-restricted: add the live domain and the local host in Google's console. Real submits on live are
  the only proof. The badge sits bottom right by default and can cover a chat button: decide its position (D4).

## The chat widget through CF7's REST endpoint

- The static widget is copied unchanged to `assets/chat-widget.js`; `kitwp_chat_widget()` prints its config
  (`window.__KITWP_CHAT`) and loads it after the load event.
- Only its save call changes: `assets/chat-save.js` has the pattern. It posts FormData to
  `/wp-json/contact-form-7/v1/contact-forms/<id>/feedback` with `_wpcf7`, `_wpcf7_version`, `_wpcf7_locale`,
  `_wpcf7_unit_tag` (`wpcf7-f<id>-o1`), `_wpcf7_container_post`, the fields, and the reCAPTCHA token.
- A JSON body gets 415; a missing unit tag gets 400; `mail_sent` is the only success.
- The Chat Lead form's Form tab is the field list; its Mail tab the email.

## Where the lead came from (form attribution)

The company attribution standard, on every lead form on every page and landing page by default, no plugin,
nothing to set up (`includes/forms-attribution.php`, `includes/forms-lead-source.php`, `assets/attribution.js`).
Every lead carries these eleven fields, with these labels, in this order, in the lead email, the CFDB7 columns, the
leads portal and the CRM mapping:

| # | Label | Posted name | Value |
|---|---|---|---|
| 1 | Lead Source | `lead_source` | The latest touch in words (below) |
| 2 | Google Ads Campaign ID | `google_ads_campaign_id` | `gad_campaignid`, else `utm_id`, else numeric `utm_campaign` |
| 3 | Google Click ID | `google_click_id` | `gclid` |
| 4 | Landing Page | `landing_page` | The latest touch's first page, with its query string |
| 5 | Referrer | `referrer` | The other site that sent the latest touch (host and path) |
| 6 | Lead Source Date | `lead_source_date` | The latest touch's date, YYYY-MM-DD in the site's time zone |
| 7 | Form Submitted From | `form_submitted_from` | The page the form was sent from |
| 8 | First Touch Source | `first_touch_source` | The first visit in words |
| 9 | First Visit Date | `first_visit_date` | YYYY-MM-DD in the site's time zone |
| 10 | First Touch Landing Page | `first_touch_landing_page` | With its query string |
| 11 | First Touch Referrer | `first_touch_referrer` | Host and path |

An empty value is "none", never a dropped row. The other captured values (utm_source, utm_medium, utm_campaign,
utm_term, utm_content, utm_id, gbraid, wbraid, fbclid, msclkid) follow as extra rows only when present; the first
visit's only when they differ from the latest touch's ("First Touch UTM Source"). In words: Google Ads (gclid,
gbraid, wbraid or gad_campaignid), Microsoft Ads (msclkid), else "utm_source / utm_medium", else "Facebook /
Instagram" (fbclid), else "Google search", "Bing search", "Yahoo search", "DuckDuckGo search" or "<site> (link)",
else "Direct". No page-script data at all: Lead Source "Not recorded".

- **Browser, first party only:** two visits: the **first visit** (kept `KITWP_ATTRIBUTION_DAYS`, 90; 0 = this visit
  only, for a site whose consent rules allow no stored data before consent) and the **latest campaign visit** (the
  last one that came with campaign tags, an ad click id or from another website; the latest touch, else the first
  visit). Each: the campaign tags, the click ids, `gad_campaignid`, its first page (with its query, without any
  parameter whose value holds an "@": an email address never goes in), the site that sent it, its time (UTC).
  Nothing leaves the browser until the visitor sends a form; nothing goes to a third party.
- **Consent:** with a consent banner, the first visit goes to localStorage only after the visitor accepts (ads or
  analytics, as the banner defines); until then, and after a decline, only this visit is kept (sessionStorage,
  gone with the visit), and a decline removes the stored visits. `KITWP_ATTRIBUTION_CONSENT` "auto" reads Google
  Consent Mode from the dataLayer; "banner" for a banner without Consent Mode, which calls
  `window.kitwpConsent(true | false)` when the visitor chooses and on each page with the stored choice; "none": no
  banner, stored as above.
- **Hidden fields on every CF7 form** (the chat's post too): the latest campaign visit as `utm_*`, the click ids,
  `gad_campaignid`, `landing_page`, `referrer`, `last_seen`; the first visit as `first_source` ... `first_content`,
  `first_id`, `first_gclid` ... `first_msclkid`, `first_gad_campaignid`, `first_landing_page`, `first_referrer`,
  `first_seen`. Times: "YYYY-MM-DD HH:MM" UTC.
- **Checked on the server** as CF7 reads the post (`wpcf7_posted_data`): only those names, scalar, cleaned, capped
  (1000 for landing pages, 500 for referrers, 16 for the times, 200 for the rest), http(s) addresses only; the rest
  is dropped. Then the server works out the eleven (a posted standard name is always replaced). Without JavaScript
  the form page's own address (the Referer) still gives its campaign tags and click ids. Reporting only: never
  used to decide anything about a lead.
- **Everywhere the lead goes:** the lead email's **Lead Attribution** table under the details (`[_kitk_source]`):
  a title row in the email's brand colour (`KITWP_BRAND_COLOUR`; its text black or white, whichever has the higher
  contrast; not a colour: #28292D with white), the eleven rows, then the extra rows; the plain-text form has the
  same "Label: value" lines. Contact Form CFDB7 stores the eleven as labelled columns in the same order, then the
  extra rows (`cfdb7_before_save_data`, values from the CF7 submission: CFDB7 keeps only the form's own tags by
  default, so hidden fields added by script never reach it alone; the raw browser fields stay out). A leads
  portal and a CRM connector get the posted names. The dataLayer gets `generate_lead` on /thank-you/, once per
  sent form, with `form_name` (the CF7 form's title), `lead_source` and `lead_medium`. A refresh pushes nothing.
- **The CRM or app:** on live, every lead form is mapped in the app the profile's connector plugin feeds
  (`extra_plugins` entry with `"lead_forms": true`: the live plugin checklist has the box) with the eleven posted
  names above; the TEST lead shows them there.
- **A WordPress site the kit did not build:** `python3 <kit>/scripts/launch/lead-source-plugin.py <out_dir>
  --brand '#rrggbb'` makes a must-use plugin from these same files (the loader and a `kitwp-lead-source/` folder):
  copy both into `wp-content/mu-plugins/`. It adds the table where the Mail tab has `<!-- kitwp-lead-source -->`,
  else before `</body>`, else at the end (a plain-text mail gets the rows as text), to the main email only; an error
  leaves the email as it was. `--consent banner` for a banner without Consent Mode. Never on a kit-built site.
- **Prove it:** open a form page with `?gad_campaignid=123&gclid=TEST&utm_source=google`, send a TEST lead: the
  email's Lead Attribution table and CFDB7 show the eleven labels in order with values (Lead Source "Google Ads",
  Campaign ID 123, Click ID TEST); a lead from a plain visit shows Lead Source "Direct" and "none" rows.

## Upgrading a kit site to the attribution standard

A live site built with an older kit (0.9.9 to 0.11.x) is brought up to the standard as its own task, one step:

1. Back up the theme, then copy from the kit over the theme's own copies (prefix swap only, as new-site.py does):
   `includes/forms-attribution.php`, `includes/forms-lead-source.php`, `includes/forms-mail.php` and
   `assets/attribution.js` (a site with the must-use plugin instead: run `lead-source-plugin.py` again and replace
   both). A site whose `forms-mail.php` was changed by hand: copy only its `_kitk_source` line.
2. PHPCS and `php -l` on the theme; then one TEST lead per form with the Prove-it address above: the email, CFDB7
   and the CRM show the eleven rows. Old CFDB7 rows keep their old columns.

## Form layout

Every lead form on every page and landing page looks the same and looks right:

- **The design has a form:** that form, 1:1 (the static markup and CSS; `site.json` `form_class` is its class).
- **No form in the design** (a landing page or section without one): the kit default. Set `site.json`
  `"form_class": "kitwp-form"`; `new-site.py` ships `assets/form-default.css` and the theme prints it inline once,
  before the first form on the page (`kitwp_form_default_style()`). Labels above their fields, two short fields
  per row from 640px (name and phone, email and service), the message and the button full width, inputs at least
  16px (no zoom on phones), a visible focus ring, a red border and note on a field with an error, the theme's own
  `.btn` for the button. `--kitwp-form-accent` and `--kitwp-form-error` take the theme's colours.
- **Prove it:** `node _plan/tools/report/form-layout.mjs <page url> [--form <selector>]` at 1280 and 390 wide:
  labels above, two per row on desktop and one on a phone, message full width, inputs 16px or more, a focus outline.

## The leads portal

**Optional, none by default.** Without a portal in the profile, leads go by email (with the Lead source table) and
Contact Form CFDB7 on live (rule 17): no Theme Settings group, no runbook item, no leads-check step, nothing blocks
the launch. The profile names a portal with `leads_portal.constant_prefix` (for example `ACME_LEADS`; also `admin`
and how a project is made); then every lead form also sends there, which catches the lead when the host's mail
fails. One site can still opt out in site.json: `"leads_portal": "none: <reason>"`. `kitwp_leads_send()` POSTs each lead form whether the email went out or failed (`wpcf7_mail_sent` and
`wpcf7_mail_failed`; CF7 fires one of them, spam neither; one send per submission): JSON with `form`, an
`idempotency_key`, the posted fields and `source_url`, `ip_address`, `gclid`, `fbp`, `fbc`; header `Authorization:
Bearer <key>`; 5 second timeout; 200 and 202 count as delivered; a failure is logged with the status only. The code and
the empty Theme Settings group (with a portal) are in from P3; only the values wait for live.

- The address (endpoint) and password (write key) live in **Theme Settings > Leads portal**: an ACF group of two
  fields (`leads_endpoint`, a URL; `leads_key`, a password field, masked) that `build_field_groups.py` writes when
  the profile names a portal, seeded empty. Administrators only: the group's location shows it to them alone, and a save by anyone else
  keeps the stored values (`kitwp_leads_settings_guard()`). The developer pastes both on live, logged in as an
  administrator. The key is never printed on the site or in an email; it is stored in the database, so it travels
  in Duplicator packages and database backups (keep those private, and rotate the key in the portal admin if one
  leaks).
- wp-config constants `<PREFIX>_ENDPOINT` and `<PREFIX>_KEY` (the profile's `constant_prefix`) win when defined,
  each on its own (`kitwp_leads_settings()` says which source it used).
- Off while `WP_ENVIRONMENT_TYPE` is local, development or staging. A local copy with the live key would
  otherwise send its test leads to the real portal, where they often cannot be deleted one by one.
- Only the form's own fields go, each capped in length (500 characters, 5000 for a message); the forwarded IP
  only when it is a valid public address, else REMOTE_ADDR.
- Files, consent and the honeypot never go; leave out health details, dates of birth and other sensitive fields
  with the `kitwp_leads_skip_fields` filter (per form).
- Prove the key without storing anything: `python3 _plan/tools/report/leads-check.py` (the developer runs it; the key
  from `KITWP_LEADS_KEY` or a hidden prompt, never printed) sends a GET, which the portal answers 200 for a good
  endpoint and key and stores nothing. On the site itself: `leads-check.py --site [<root>]` (WP-CLI; `--wp "wp @live"`
  for an alias) reads the values the site uses and sends the same GET from inside WordPress, so the key never leaves
  PHP; it says where the values came from (Theme Settings or wp-config). 401: wrong key or the project is off; 404:
  wrong project slug. Run it before launch with the live key, and on the go/no-go list. Never prove it with a POST from
  a script: that stores a real lead, and test leads often cannot be deleted one by one.
- Prove it on live: one TEST lead per form reaches the portal (its admin shows the count per form). The live plugin
  checklist (RUNBOOK section 4) has the item.
- A WordPress site the kit did not build: the same sender goes in as a small must-use plugin
  (`wp-content/mu-plugins/leads-portal.php`) made from `kitwp_leads_send()`, `kitwp_leads_tracking()` and their two
  hooks in the kit's `includes/forms-portal.php`, with the site's prefix and the constant prefix defined (such a
  site has no Theme Settings group: its endpoint and key go in the wp-config constants).

## Where leads are stored: CFDB7 only

Leads are stored only by Contact Form CFDB7, installed on live (the kit's plugin list). Never create a database
table, custom post type, option rows, files or an admin page of your own for enquiries or submissions; local mail
capture (_setup/mail) is local only. The email, CFDB7 and (when the profile names one) the leads portal are where a lead goes, and
none of them is the theme's own code. `self-check.py` reports any such storage in the theme or a must-use plugin as
`lead-storage` (a table created, a `$wpdb` write, or a post type or admin page named for enquiries, leads,
submissions, contacts, messages or form entries): remove it, CFDB7 on live keeps the leads.

## Local mail capture

While `WP_ENVIRONMENT_TYPE` is `local`, every email goes to the admin email only, the real recipients are kept in
an `X-<Prefix>-Original-To` header, and a copy is saved in `_setup/mail/` (a local mail catcher shows it too). When
PHP has no way to send mail here (XAMPP, MAMP, WampServer, serve-wp), the copy is the email: wp_mail() stops there
and reports success, so forms answer as on live (filter `<prefix>_mail_to_file`). A live wp-config left on `local`
sends every lead to the admin only: switch it at launch.

## Proving delivery

- Locally: each form once with JavaScript off and once on; the 303; the honeypot; the saved copy in `_setup/mail/`.
- On live: three test leads (inline form, pop-up, chat) named `TEST <developer> - please ignore (<form>)`, sent with
  the real submit button so reCAPTCHA runs. The developer confirms the emails arrived, and the host's delivery log
  (cPanel > Track Delivery) shows every recipient Accepted.
- Before launch: SPF includes the server (and any relay such as MailChannels) and a DMARC record exists (cPanel >
  Email Deliverability).
