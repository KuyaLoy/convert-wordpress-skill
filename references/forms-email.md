# Forms and email: Contact Form 7, 1:1

Read this in Sprint 5. The code is the theme's `includes/forms.php`; the seed files are `_setup/seed/forms.json`,
`quote-form.txt`, `chat-form.txt` and `lead-email.html`.

## Contents

- The pattern: CF7 holds the form, the theme prints the static markup
- Posting, the thank-you redirect, errors
- Field names that break WordPress
- The email: one HTML part
- The auto-reply and the agency badge: one look for both emails
- Spam: honeypot and reCAPTCHA v3
- The chat widget through CF7's REST endpoint
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
- CF7's JS and CSS are off (`wpcf7_load_js`, the clean-up), autop off for lead forms. CF7's response box becomes
  the static form note.
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
  Google for a fresh token on submit and fills `_wpcf7_recaptcha_response` itself.
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

## The leads portal

When the profile names a leads portal (`leads_portal.constant_prefix`, for example `ACME_LEADS`),
`kitwp_leads_send()` POSTs every sent lead form there after the email went out: JSON with `form`, an
`idempotency_key`, the posted fields and `source_url`, `ip_address`, `gclid`, `fbp`, `fbc`; header
`Authorization: Bearer <key>`; 5 second timeout; a failure is logged with the status only.

- The endpoint and key live in wp-config only (`<PREFIX>_ENDPOINT`, `<PREFIX>_KEY`): the developer pastes them.
- Off while `WP_ENVIRONMENT_TYPE` is local, development or staging. A local copy with the live key would
  otherwise send its test leads to the real portal, where they often cannot be deleted one by one.
- Files, consent and the honeypot never go; leave out health details, dates of birth and other sensitive fields
  with the `kitwp_leads_skip_fields` filter (per form).
- Prove it on live: one TEST lead per form reaches the portal (its admin shows the count per form).

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
