# 1:1 parity tools

Copy this folder to `wp-content/themes/<theme>/tests/parity/` (never deployed: Duplicator excludes `tests`).
Set the hosts and widths in `parity.config.json` and the routes in `routes.json` (every route of the static
sitemap, `/thank-you/`, and a missing URL for the 404).

| File | What it does |
|---|---|
| `parity.mjs` | Pixel diff (pixelmatch), visible text diff and SEO diff per route and width; HTML report in `report/` |
| `parity.config.json` | WordPress and reference hosts, quick and full widths, blocked requests, hidden and masked elements, reveal class, frozen clock |
| `breakpoints.mjs` | Full-run widths from the static CSS: every breakpoint and 1 px past it (`breakpointsFromCss` in the config) |
| `swaptest.py` | S1-05 swap test: the golden master with the theme's CSS swapped in (same origin), to run `parity.mjs` against |
| `region-check.mjs` | S1-07: pixel diff of single regions (header, footer, pop-up) before the pages under them exist |
| `domdiff.py` | DOM diff of regions (header, main, footer, pop-up) between a static page and a WordPress snapshot |
| `domdiff.config.json` | Optional: the site's regions and local hosts (see the defaults at the top of domdiff.py) |
| `mkmirror.py` | Builds a static mirror of the WordPress pages from `_setup/snapshots/` for cloud runs |
| `serve.py` | Serves the static build or the mirror on 127.0.0.1 with a real 404 |

## On Windows (reaches the .test sites)

```
npm install
npx playwright install chromium
npm run self        # reference against itself: must be 0.000%
npm run quick       # all routes, quick widths
npm run full        # sprint end: all routes, full widths
node parity.mjs --routes=/,/about/ --widths=390,1440
```

Screenshots are kept only for failing rows (`--keep=all` keeps every one). The reference build kept them all: 1.7 GB.

## The swap test (S1-05) and the global layout (S1-07)

```
python3 swaptest.py --ref http://<site>-ref.test --map swap.json   # see the top of swaptest.py for swap.json
python3 serve.py swap 8772 &
REF=http://<site>-ref.test WP=http://127.0.0.1:8772 node parity.mjs --widths=quick     # must be 0.000%
node region-check.mjs http://<site>-ref.test http://<site>.test / header,footer 390,768,1440 main,#consent
python3 domdiff.py golden/home.html snapshot/home.html header footer
```

## In the cloud (cannot reach .test)

1. Local: open every route with `?kitwp_snapshot=1` (logged out), so `_setup/snapshots/` has each page.
2. Stage the snapshots, the theme folder and `_setup/seed/media.json`; unzip the static build (golden master).
3. `python3 mkmirror.py --snapshots snaps --theme theme --theme-url /wp-content/themes/<theme> --local-host <site>.test --out mirror --static-build out --media media.json`
4. `python3 serve.py out 8771 &` and `python3 serve.py mirror 8773 &`
5. `REF=http://127.0.0.1:8771 WP=http://127.0.0.1:8773 node parity.mjs --widths=390,768,1440`

## Reading the results

- 0.000% with equal heights is the goal. A 0.1 to 0.3% band is usually an image caught mid srcset swap: check
  the image loaded before chasing it.
- One wild shot on Laragon (fallback fonts, 20%+) is web fonts loading late under load: re-run that shot.
- The DOM diff ignores `style` and `srcset`: compare those separately (all srcsets must match next/image's rule).
- SEO flags for canonical and robots are expected locally ("Discourage search engines" is on).
