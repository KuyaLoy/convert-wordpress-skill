# Final live check kit

Used by the convert-to-wordpress skill after go-live. new-site.py copies this folder to `_plan/tools/report/` and the
report template to `_setup/launch/report.html`. Nothing here sends anything: every check only reads the live site.

| File | What it does | Run |
|---|---|---|
| `live-qa.py` | Every sitemap URL plus /thank-you/: 200, GTM in the head and the noscript, one H1, a description, a canonical, no local host name; every old URL lands on its target in one hop; installer, Duplicator and planning files not public; a missing URL answers 404 twice; http and www reach https in one hop; the REST user list; robots.txt. Exit 3 when the host's bot filter blocks it | `python3 live-qa.py https://example.com GTM-XXXXXXX _setup/seed/redirects.json example.test` (`-` instead of the GTM ID skips the GTM checks) |
| `live-qa-console.js` | The same checks inside a browser tab on the live site, for hosts whose bot filter blocks scripts. Set `window.LIVE_QA` first (see the file), paste, then read `window.__liveQa.summary` | browser console or a browser tool |
| `track.mjs` | Real-browser proof: the GTM container loaded, the dataLayer events, the tag hosts per page (the ads conversion only on /thank-you/) | `node track.mjs https://example.com GTM-XXXXXXX / /thank-you/` |
| `shots.mjs` | Live screenshots for the report: `path:width:name` (390 or less = phone) | `node shots.mjs https://example.com /:1440:home-desktop /thank-you/:1440:thankyou-desktop /a-page/:390:page-mobile` |
| `pdf.mjs` | The report HTML to an A4 PDF, with other PDFs (the editing guide) appended | `node pdf.mjs report.html Final-Live-Check.pdf Editing-Guide.pdf` |
| `pw.mjs` | Finds Playwright: the local install first, then a global one | (used by the scripts above) |

Report: fill `_setup/launch/report.html` with verified facts only (`grep -n "\[\[" report.html` prints nothing when
done), put the screenshots next to it, then make the PDF. Plain language for the client: no sprint numbers, no tool
names.

Playwright: `npm i -D playwright` here, then `npx playwright install chromium` (or use a global install; pw.mjs finds
both). Merging PDFs needs `pdf-lib` (`npm i pdf-lib`); without it: `qpdf --empty --pages a.pdf b.pdf -- out.pdf`.

Lighthouse (mobile, on the live site; the shared PageSpeed API key often runs out):

```
npx -y lighthouse@12 https://example.com --quiet --chrome-flags="--headless=new" \
  --only-categories=performance,accessibility,best-practices,seo --output=json --output-path=lh.json
```

Set `CHROME_PATH` when Chrome is not found (for example a Playwright Chromium). In a container add `--no-sandbox` to
the Chrome flags.

Blocked by the host: Imunify360 or a similar bot filter can answer scripted requests with "One moment, please" or 415.
Run `live-qa-console.js` in a real browser tab instead. Some browser tools refuse output that looks like cookies or
query strings: the console script prints without `=`, `;` and `?`.
