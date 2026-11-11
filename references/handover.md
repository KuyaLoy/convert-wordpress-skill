# The client pack

Read this when live QA (`references/qa-report.md`) passes. The client pack is what the client reads: two PDFs and
a message. The templates are in `_setup/handover/` (from `assets/handover/`):

| Template | Becomes | For |
|---|---|---|
| `website-sheet.html` | `Your-New-Website.pdf` (one A4 page) | The client: the address, the login steps, what changed, where enquiries go, what to do now |
| `editing-guide.html` | `How-to-Edit-Your-Website.pdf` | Whoever edits the site: pages, contact details, photos, forms, what to leave alone |
| `client-message.md` | A long and a short message | The project tracker comment and the client chat |

The client is not technical. Every sentence is plain English.

## Contents

- When
- Steps
- The plain-English check
- What goes to whom

## When

After live QA passes and the test leads arrived, before the report PDF: the report appends the editing guide.
The client's own login exists on live with the **Editor** role (the developer makes it; never Administrator for the
client unless the developer says so).

## Steps

1. **Fill the facts.** new-site.py already filled the `{{NAME}}` values. Replace every `[[...]]` with a fact checked
   on the live site, and delete what does not apply. "What changed" is 3 to 5 short points about what the client
   gains, not how it was built. The contact line for help is the developer's, as they want it shown.
2. **Check the words against the screen.** Menu names, tab names and button labels in the guide must match what
   the Editor login sees on live (for example Save or Update, and the menu that lists saved enquiries). Change the
   words to match. If the Editor cannot see the saved enquiries, say so in the guide ("ask us"); do not change the
   site to fix it unless the developer asks.
3. **Take the screenshots as the Editor.** In the browser pane, on the live site, signed in with an Editor login:
   the client's (before it is sent) or a spare one the developer removes afterwards. The developer signs in; the
   agent never types or sees the password. Window about 1280 x 800, only the part of the screen the step is about.
   Never show a password, another person's email address or a real enquiry (show only the TEST enquiry). Save
   each as a PNG in `_setup/handover/shots/` with the name in its box; if the browser tool cannot save files, the
   developer saves them. Then replace each `shot-box` line with `<img src="shots/<file>.png" alt="<alt text>">`,
   using the file and alt text written in that box (the comment at the top of the guide shows how).
4. **Make the PDFs** (from `_setup/handover/`):

   ```
   node ../../_plan/tools/report/pdf.mjs website-sheet.html Your-New-Website.pdf
   node ../../_plan/tools/report/pdf.mjs editing-guide.html How-to-Edit-Your-Website.pdf
   ```

   Open both. The website sheet must be one page; if not, shorten its points. Then the report PDF can append the
   guide (from `_setup/launch/`):
   `node ../../_plan/tools/report/pdf.mjs report.html Final-Live-Check.pdf ../handover/How-to-Edit-Your-Website.pdf`
5. **Write the message.** Fill `client-message.md` (both versions), then delete its rules block.
6. **Run the plain-English check** (below) on all three files, then hand everything to the developer.

## The plain-English check

Every file, before the PDFs are made and before the message is handed over:

```
grep -n "\[\[" website-sheet.html editing-guide.html client-message.md        # nothing left to fill
grep -n "{{" website-sheet.html editing-guide.html client-message.md          # no unfilled values
grep -n "$(printf '\342\200\224')" website-sheet.html editing-guide.html client-message.md  # no em dashes
grep -n -i -E "\bACF\b|\bSCF\b|\bCF7\b|contact form 7|\bDNS\b|cache|plugin|\bPHP\b|database|repeater|field group|_setup|_plan|\.html|password:" \
  website-sheet.html editing-guide.html client-message.md
```

The first three print nothing. Read every hit of the last one: a word stays only when the client sees it on screen
or it is explained in five words or fewer (the guide explains "Plugins (add-ons that run parts of the site)").
Then read each sentence once as the client would: short, one idea, no jargon, nothing internal.

## What goes to whom

- **The client** (through the developer): both PDFs and the long message, or the short message in a chat app. The
  login (username and password) goes separately, through a private channel the developer chooses, never in the
  tracker, the chat or a PDF.
- **The project tracker:** the long message, both PDFs and the final report PDF (`Final-Live-Check.pdf`, with the
  guide appended).
- **The developer:** everything above, to read and send. The agent never sends a message itself.
- The filled templates and the shots stay in `_setup/handover/`: private, like the rest of `_setup/` (blocked on
  the server and left out of the Duplicator package).
