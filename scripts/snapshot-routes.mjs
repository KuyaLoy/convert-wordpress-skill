/**
 * Capture the rendered HTML of every route, for sources whose built files do not hold the page (client-rendered
 * React or Vue apps, Next.js without a static export, any SSR app). The capture is the markup to copy into the
 * theme partials, and the input for the DOM diff.
 *
 *   node snapshot-routes.mjs http://localhost:3000 golden/ /,/about/,/contact/
 *   node snapshot-routes.mjs http://localhost:4173 golden/ sitemap        (routes from /sitemap.xml)
 *   node snapshot-routes.mjs http://localhost:4173 golden/ routes.json    (a JSON list)
 *
 * Files: home.html for /, about.html for /about/, a__b.html for /a/b/ (the same names as the WordPress snapshots).
 * Waits for the load event, a fixed 1.5 s, fonts and images; scroll-reveal content is forced visible only in the
 * screenshot tools, not here, so the HTML is exactly what the app renders.
 */
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from './report/pw.mjs';

const [base, outDir, list = '/'] = process.argv.slice(2);
if (!outDir) { console.error('usage: node snapshot-routes.mjs <base url> <out dir> <routes | sitemap | routes.json>'); process.exit(2); }
const site = base.replace(/\/$/, '');
let routes;
if (list === 'sitemap') {
  const xml = await (await fetch(site + '/sitemap.xml')).text();
  routes = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => new URL(m[1]).pathname);
} else if (list.endsWith('.json')) {
  routes = JSON.parse(fs.readFileSync(list, 'utf8'));
} else {
  routes = list.split(',');
}
fs.mkdirSync(outDir, { recursive: true });
const b = await (await chromium()).launch({ executablePath: process.env.CHROME_PATH || undefined });
for (const route of routes) {
  const pg = await b.newPage({ viewport: { width: 1440, height: 900 } });
  const res = await pg.goto(site + route, { waitUntil: 'load', timeout: 60000 });
  await pg.waitForTimeout(1500);
  await pg.evaluate(async () => { await document.fonts.ready; });
  const html = '<!DOCTYPE html>\n' + (await pg.evaluate(() => document.documentElement.outerHTML));
  const p = route.replace(/^\/|\/$/g, '');
  const name = (p === '' ? 'home' : p.replace(/\//g, '__')) + '.html';
  fs.writeFileSync(path.join(outDir, name), html);
  console.log(`${res ? res.status() : '-'} ${route} -> ${name} (${html.length} bytes)`);
  await pg.close();
}
await b.close();
