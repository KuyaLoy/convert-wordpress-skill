# {{SITE_NAME}}: old site URL check

Checked {{DATE}} on the old site (live, a local copy, or a backup).

## How

1. The old site's full sitemap (every sub-sitemap) and, for WordPress, the REST counts of pages and posts.
2. The designer's redirect map, if there is one (KEEP, MERGE, REMOVE).
3. Archive and theme-part URLs the map misses (categories, tags, authors, listings, header/footer post types).
4. Campaign URLs from the tracking task: they never change.

## Result

| Old URL | Action | Target |
|---|---|---|
| | KEEP / 301 | |

Every 301 goes into `_setup/seed/redirects.json`; check each one locally and again on live (live-qa.py).
No 301 row here (and site.json "redirects" not true): the site has no redirects, so the runbook has no Redirection
plugin or step. Rows added later: `new-site.py _plan/site.json --launch-files` writes the runbook again with them.
