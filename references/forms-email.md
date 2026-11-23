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
- The leads portal
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
- **Agency badge in both footers:** when the profile's `branding` names a badge, the lead email and the
  auto-reply end with it, linked (`[_<key>_badge]`, set in config.php `<PREFIX>_EMAIL_BADGE*`; the builder copies
  the PNG to `theme/assets/email/`). Use a **PNG at 2x** (email clients do not show SVG or WebP). A white badge
  sits on the brand-colour footer strip that both templates have.
- The site's own footer can carry the same badge (SVG is fine on the web) when the profile asks for it.
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

On every lead form by default, no plugin, nothing to set up (`includes/forms-attribution.php`,
`assets/attribution.js`):

- **Browser, first party only:** two visits, as an existing company build keeps them: the **first visit** (kept
  `KITWP_ATTRIBUTION_DAYS`, 90; 0 = this visit only, for a site whose consent rules allow no stored data before
  consent) and the **latest campaign visit** (the last one that came with campaign tags, an ad click id or from
  another website). Each: the campaign tags (utm_source, utm_medium, utm_campaign, utm_term, utm_content), ad click
  ids (gclid, gbraid, wbraid, fbclid, msclkid), its first page, the site that sent it, its time (UTC). Addresses
  keep host and path, never the query. Nothing leaves the browser until the visitor sends a form; nothing goes to
  a third party.
- **Consent:** with a consent banner, the first visit goes to localStorage only after the visitor accepts (ads or
  analytics, as the banner defines); until then, and after a decline, only this visit is kept (sessionStorage,
  gone with the visit), and a decline removes the stored visits. `KITWP_ATTRIBUTION_CONSENT` "auto" reads Google
  Consent Mode from the dataLayer; "banner" for a banner without Consent Mode, which calls
  `window.kitwpConsent(true | false)` when the visitor chooses and on each page with the stored choice; "none": no
  banner, stored as above.
- **Hidden fields on every CF7 form** (the chat's post too). The latest campaign visit: `utm_source`,
  `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`, `gclid`, `gbraid`, `wbraid`, `fbclid`, `msclkid`,
  `landing_page`, `referrer`, `last_seen`. The first visit: `first_source`, `first_medium`, `first_campaign`,
  `first_term`, `first_content`, `first_gclid`, `first_gbraid`, `first_wbraid`, `first_fbclid`, `first_msclkid`,
  `first_landing_page`, `first_referrer`, `first_seen`. Times: "YYYY-MM-DD HH:MM" UTC.
- **Checked on the server** as CF7 reads the post (`wpcf7_posted_data`): only those names, scalar, cleaned, capped
  (500 for the addresses, 16 for the times, 200 for the rest), http(s) addresses only; the rest is dropped. Without
  JavaScript the form page's own address (the Referer) still gives its campaign tags and click ids. Reporting only:
  never used to decide anything about a lead.
- **Everywhere the lead goes:** the lead email's **Lead source** table under the details (`[_kitk_source]`,
  `includes/forms-lead-source.php`): a title row in the email's brand colour, then "First visit", "Latest campaign
  visit" (only when it differs from the first) and "Form sent from" (the page). Each visit starts with its source in
  words (bold): utm_source / utm_medium; else "Google Ads click", "Facebook / Instagram click", "Microsoft Ads
  click"; else "Google search", "Bing search", "Yahoo search", "DuckDuckGo search" or "<site> (link)"; else "Direct
  (typed in, bookmark or no source)"; then Campaign, Keyword, Ad, the click ids, From, Landing page, "When: ... UTC".
  No page-script data: "Not recorded (the visitor's browser did not run the page script)." The plain-text form has
  the same rows. Contact Form CFDB7 stores the posted fields; the leads portal gets the same names as fields
  (`gclid` from the visit); the dataLayer gets `generate_lead` on /thank-you/, once per sent form, with
  `form_name` (the CF7 form's title), `lead_source` and `lead_medium`. A refresh pushes nothing.
- **Prove it:** open a form page with `?utm_source=qa&utm_medium=test&utm_campaign=launch&gclid=TEST`, send a TEST
  lead: the email's Lead source table and the portal show them; a lead from a plain visit shows "Direct (typed in,
  bookmark or no source)".

## The leads portal

**Mandatory on live** for every site with a lead form: the host's mail sometimes fails, and the portal still
catches the lead. The profile names it (`leads_portal.constant_prefix`, for example `ACME_LEADS`); an empty one is
a go-live blocker. A site without a lead form says so in site.json: `"leads_portal": "none: <reason>"`.
`kitwp_leads_send()` POSTs each lead form whether the email went out or failed (`wpcf7_mail_sent` and
`wpcf7_mail_failed`; CF7 fires one of them, spam neither; one send per submission): JSON with `form`, an
`idempotency_key`, the posted fields and `source_url`, `ip_address`, `gclid`, `fbp`, `fbc`; header
`Authorization: Bearer <key>`; 5 second timeout; 200 and 202 count as delivered; a failure is logged with the
status only. The code is in from P3; only the keys wait for live.

- The endpoint and key live in wp-config only (`<PREFIX>_ENDPOINT`, `<PREFIX>_KEY`): the developer pastes them.
- Off while `WP_ENVIRONMENT_TYPE` is local, development or staging. A local copy with the live key would
  otherwise send its test leads to the real portal, where they often cannot be deleted one by one.
- Only the form's own fields go, each capped in length (500 characters, 5000 for a message); the forwarded IP
  only when it is a valid public address, else REMOTE_ADDR.
- Files, consent and the honeypot never go; leave out health details, dates of birth and other sensitive fields
  with the `kitwp_leads_skip_fields` filter (per form).
- Prove the key without storing anything: `python3 _plan/tools/report/leads-check.py` (the developer runs it; the
  key from `KITWP_LEADS_KEY` or a hidden prompt, never printed) sends a GET, which the portal answers 200 for a good
  endpoint and key and stores nothing. 401: wrong key or the project is off; 404: wrong project slug. Run it before
  launch with the live key, and on the go/no-go list. Never prove it with a POST from a script: that stores a real
  lead, and test leads often cannot be deleted one by one.
- Prove it on live: one TEST lead per form reaches the portal (its admin shows the count per form). The live plugin
  checklist (RUNBOOK section 4) has the item.
- A WordPress site the kit did not build: the same sender goes in as a small must-use plugin
  (`wp-content/mu-plugins/leads-portal.php`) made from `kitwp_leads_send()`, `kitwp_leads_tracking()` and their two
  hooks in the kit's `includes/forms-portal.php`, with the site's prefix and the constant prefix defined.

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
