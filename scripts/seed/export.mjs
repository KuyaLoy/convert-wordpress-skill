/**
 * Exports the static site's content into the seed files the WordPress seeder reads (_setup/seed/).
 *
 *   node export.mjs <content.mjs> <static out dir> <static public dir> <seed dir>
 *
 * content.mjs is the static site's content modules bundled into one file Node can import, for example:
 *   npx esbuild website/content/index.ts --bundle --format=esm --platform=node --outfile=content.mjs
 * (the reference build used rolldown the same way). Bundle from a copy of the static source, never in place.
 *
 * Writes media.json (and copies every image plus its static WebP widths into <seed dir>/files/), settings.json,
 * menus.json and content.json. Template pages: write template-pages.json here too when the field values come
 * straight from the content modules (see the TEMPLATE PAGES block). Flexible pages come from the built HTML
 * instead (export-pages.py), so their text is exact.
 *
 * Fill the SITE MAPPING blocks; everything else is generic.
 */
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const [contentFile, outDir, publicDir, seedDir] = process.argv.slice(2);
if (!seedDir) {
  console.error('usage: node export.mjs <content.mjs> <static out dir> <static public dir> <seed dir>');
  process.exit(2);
}
const c = await import(pathToFileURL(path.resolve(contentFile)).href);

// The static build's image widths and the path pattern of its WebP files (a static export with a custom loader
// writes them itself; the reference build used /_img<src>-<width>.webp). Must match KITWP_IMAGE_WIDTHS.
const WIDTHS = [256, 384, 640, 828, 1080, 1200, 1920, 2048];
const variantPath = (src, w) => `/_img${src}-${w}.webp`;

fs.mkdirSync(path.join(seedDir, 'files'), { recursive: true });

/* ---------- media ---------- */
const media = [];
/**
 * Add an image the site uses. alt: the static alt text (never a person's name). extra: width, height,
 * attrWidth/attrHeight (when the static <img> prints a size that differs from the file), meta (flags the theme reads).
 */
const addMedia = (src, alt, extra = {}) => {
  if (!media.some((m) => m.src === src)) media.push({ src, alt, ...extra });
};

/* SITE MAPPING: media. Example: every photo in the content's photo list.
for (const p of Object.values(c.photos)) addMedia(p.src, p.alt, { width: p.width, height: p.height });
*/

let copied = 0;
const missing = [];
for (const m of media) {
  const files = [[path.join(publicDir, m.src), path.join(seedDir, 'files', m.src)]];
  m.variants = {};
  for (const w of WIDTHS) {
    const v = variantPath(m.src, w);
    files.push([path.join(outDir, v), path.join(seedDir, 'files', v)]);
    m.variants[w] = v;
  }
  for (const [from, to] of files) {
    if (!fs.existsSync(from)) { missing.push(from); continue; }
    fs.mkdirSync(path.dirname(to), { recursive: true });
    fs.copyFileSync(from, to);
    fs.chmodSync(to, 0o644); // files copied from a Windows mount keep 0700 otherwise
    copied++;
  }
}

/* ---------- Theme Settings: field name => value; images by static path (the seeder resolves them) ---------- */
/* SITE MAPPING: settings. Names must match the Theme Settings field names (build_field_groups.py). */
const settings = {
  // business_name: c.site.name, legal_name: c.site.legalName, phone_display: c.site.phone, phone_tel: c.site.tel,
  // email: c.site.email, company_number: c.site.companyNumber, address: c.site.address, qf_service_options: c.services.map((s) => ({ label: s.name })),
};

/* ---------- menus: { location: { name, items: [{ title, slug | url, icon, classes, children }] } } ---------- */
/* SITE MAPPING: menus, in the static header and footer order. Items point at page slugs. */
const menus = {
  // primary: { name: 'Primary', items: [{ title: 'Services', slug: 'services', children: c.services.map((s) => ({ title: s.name, slug: s.slug })) }] },
};

/* ---------- template pages: [{ slug, title, template, order, group, fields, seo }] ---------- */
/* SITE MAPPING: template pages. Values are final field values: "media:<static path>" for images and
   "page:<slug>" for links to other pages. Overrides equal to the Theme Settings default stay empty. */
const templatePages = [
  // ...c.services.map((s, i) => ({ slug: s.slug, title: s.name, template: 'page-templates/service.php', order: i, group: 'service',
  //   fields: { hero_h1: s.hero.h1, hero_em: s.hero.em, hero_sub: s.hero.sub, hero_image: 'media:' + s.heroImage,
  //             faqs: s.faqs.map((q) => ({ question: q.q, answer: q.a })) },
  //   seo: { title: s.meta.title, description: s.meta.description } })),
];

const write = (f, d) => fs.writeFileSync(path.join(seedDir, f), JSON.stringify(d, null, 2) + '\n');
write('media.json', media);
write('settings.json', settings);
write('menus.json', menus);
write('template-pages.json', templatePages);
write('content.json', Object.fromEntries(Object.entries(c).filter(([, v]) => typeof v !== 'function')));
console.log(`media ${media.length}, files copied ${copied}, missing ${missing.length}; settings ${Object.keys(settings).length}; menus ${Object.keys(menus).length}; template pages ${templatePages.length}`);
if (missing.length) console.log(missing.slice(0, 10).join('\n'));
