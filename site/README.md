# The convert-to-wordpress website

The landing page at https://kuyaloy.github.io/convert-wordpress-skill/. It is not part of the skill: agents that
run the skill never need this folder.

- Next.js static export (`output: "export"`, base path `/convert-wordpress-skill`), Tailwind CSS 4, shadcn/ui with
  8bitcn/ui components (MIT), Pixelarticons (MIT), self-hosted fonts from Fontsource (OFL).
- Every visible word is in `src/content/site.ts`. The patch notes come from `../CHANGELOG.md` when the site builds.
- `.github/workflows/pages.yml` builds and publishes it on every push to `main` that touches `site/` or the
  changelog.

```
npm install
npm run dev      # http://localhost:3000/convert-wordpress-skill/
npm run build    # static files in out/
```

To host it somewhere else, build with the address and the folder it will live in, then upload `out/`:

```
SITE_URL=https://convert.example.com/ SITE_BASE_PATH= npm run build                          # a subdomain
SITE_URL=https://example.com/convert-to-wordpress/ SITE_BASE_PATH=/convert-to-wordpress npm run build   # a subfolder
```

Rules: plain words, no em or en dashes, the plain label first and the game tag second, motion off when the visitor
asks for reduced motion, both themes checked (Auto, Light, Dark). The author's contact details and social links in
`src/content/site.ts` are there on purpose (the "Need a developer?" section and the footer).
