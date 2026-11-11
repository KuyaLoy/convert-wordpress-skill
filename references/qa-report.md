# Live QA and the report

Read this right after the move. The tools are in `_plan/tools/report/` (README there); the report template is
`_setup/launch/report.html`. Everything here only reads the live site, except the three test leads, which the
developer agrees to first.

## Contents

- The checks
- Test leads
- wp-admin on live
- Speed
- The report
- The task tracker and the stakeholder message
- The client pack
- Done means

## The checks

1. One command checks what we used to check by hand. It only reads the site (GET requests, 0.5 s apart):

   ```
   python3 _plan/tools/report/live-qa.py https://<canonical host> <GTM-ID> _setup/seed/redirects.json <local_host> \
     --leftovers <name>_archive.zip,<name>_installer.php --image /wp-content/uploads/<an image>.jpg --json live-qa.json
   ```

   Give the site on its canonical host (with www if the site uses www). Each check prints PASS or FAIL, and the run
   ends with ALL PASS or N FAIL. It checks:
   - Pages: every route answers 200. Routes come from the theme's `tests/parity/routes.json` (or `--routes`), plus
     every sitemap URL, `/` and the thank-you page. A made-up path answers 404, twice.
   - Old links: every rule in `redirects.json` answers one 301 to its target, also with `?utm_source=qa` kept.
   - Host rules: `http://`, `http://www.` and the other https host each answer one 301 to the canonical host.
   - Private files: planning, handoff, installer, Duplicator, log and config files answer 403 or 404. Add the
     Duplicator archive and installer names with `--leftovers`.
   - Certificate: it covers the domain and www and runs more than 14 days. The expiry date is printed.
   - Search engines: every page is index (the thank-you page noindex), with a canonical on the canonical host.
     robots.txt has a Sitemap line and the sitemap answers 200.
   - Local leftovers: no `.test` or `localhost` URL in any page.
   - Page content: one H1 and a meta description. With a GTM ID: the container and the noscript on every page.
   - WebP: with `--image`, a browser that accepts WebP gets `image/webp`.

   Before launch, add `--hidden`: then every page must be noindex and robots.txt must block everything. Exit 3
   means the host's bot filter blocked it: run `live-qa-console.js` in a real browser tab instead.
2. `node _plan/tools/report/track.mjs https://<domain> <GTM-ID> / /thank-you/`: the container loaded, the
   dataLayer events, the tag hosts; the ads conversion request only on `/thank-you/`.
3. Real phones (the developer): iOS Safari and Android Chrome: menu, pop-up, forms, call links.
4. A quick visual pass at 390 and 1440 on Home, one page per template, Contact and the thank-you page.

## Test leads

- Ask the developer first. Three leads: the inline form, the pop-up, the chat, each named
  `TEST <developer> - please ignore (<form>)`.
- Use the real submit button so reCAPTCHA runs. With a browser tool: scroll the button into view, take a screenshot,
  click by coordinate, then confirm the URL is `/thank-you/` (a click by element reference can fire before the
  scroll finishes).
- The developer confirms the emails arrived; the host's delivery log (cPanel > Track Delivery) shows every
  recipient Accepted. The developer's screenshots of the three emails go in the report.
- Some tracking tasks have an "email enquiry test received" box: the developer ticks it.

## wp-admin on live

The ACF menu is there and the licence is Active; every field group shows as saved (nothing to sync); Theme
Settings and a template page open without errors; Contact Form 7 lists the forms; `debug.log` has nothing new.

## Speed

Lighthouse mobile on the live site (command in the tools README), on Home, one template page and Contact. Report
the numbers as they are, with one plain sentence on what limits them (usually third-party scripts and icon fonts).

## The report

One PDF for the task tracker:

1. Screenshots: `node shots.mjs https://<domain> /:1440:home-desktop /thank-you/:1440:thankyou-desktop
   /<page>/:390:page-mobile /<page2>/:1440:page2-desktop`, plus the email screenshots.
2. Fill `report.html` with verified facts only: the summary, what was checked, the website task's requests one by
   one, the tracking task's requests, the test leads, the screenshots, next steps. `grep -n "\[\[" report.html`
   prints nothing when done.
3. `node pdf.mjs report.html Final-Live-Check.pdf ../handover/How-to-Edit-Your-Website.pdf` (the editing guide
   from the client pack appended; make it first: "The client pack" below).

Plain language for the client: no sprint or story numbers, no tool names, no internal notes.

## The task tracker and the stakeholder message

Draft both for the developer; they post them.

- **Task comment:** the live URL; what was checked (pages, old links and campaign URLs, GTM, the thank-you
  conversion, forms and emails, spam protection); the WordPress login (URL, username, `[PASTE PASSWORD HERE]`);
  where enquiry emails go ("let me know if this should change"); who does future edits; the PDF attached.
- **Stakeholder message** (the profile's role and channel, for example a chat message to the account manager):
  five to eight lines, the same facts, the login with the password placeholder, the same PDF.
- SEO tasks (Search Console, new copy) belong to whoever owns SEO: leave them out unless the developer asks.

## The client pack

After the checks pass, make the client pack: a one-page "Your new website" sheet, the "How to edit your website"
guide (screenshots taken as the client's Editor) and a plain-language message, from `_setup/handover/`. Make the
guide's PDF before the report's, so the report can append it. Steps, the plain-English check and who gets what:
`references/handover.md`.

## Done means

Every route 1:1 and editable; forms and emails proven on live; GTM and the conversion proven; old URLs redirect;
installer and planning files private; the ACF PRO licence active (none with SCF); the board, both handoff files and
the project's lessons current; the report PDF, the client pack, the task comment and the stakeholder message handed to
the developer.
