// Proves tracking in a real browser: the GTM container loaded, the dataLayer events, and which tag hosts fire.
//   node track.mjs https://example.com GTM-XXXXXXX [/ /thank-you/]
// Look for the Google Ads conversion (googleadservices.com/pagead/conversion) on /thank-you/ only.
import { chromium } from './pw.mjs';
const [site, gtm, ...paths] = process.argv.slice(2);
if (!gtm) { console.error('usage: node track.mjs <site> <GTM-ID> [paths...]'); process.exit(2); }
const TAGS = /(^|\.)(googletagmanager\.com|googleadservices\.com|google-analytics\.com|analytics\.google\.com|doubleclick\.net|trkcall\.com|facebook\.(com|net)|bat\.bing\.com|clarity\.ms)$/;
const b = await (await chromium()).launch({ executablePath: process.env.CHROME_PATH || undefined });
for (const p of paths.length ? paths : ['/', '/thank-you/']) {
  const pg = await b.newPage();
  const hits = new Set();
  pg.on('request', (r) => {
    const u = new URL(r.url());
    if (TAGS.test(u.hostname)) hits.add(u.hostname + u.pathname.replace(/\/\d{6,}.*$/, '/...').slice(0, 60));
  });
  await pg.goto(site.replace(/\/$/, '') + p, { waitUntil: 'load', timeout: 90000 });
  await pg.waitForTimeout(6000);
  const st = await pg.evaluate((id) => ({
    gtm: !!(window.google_tag_manager && window.google_tag_manager[id]),
    dataLayer: (window.dataLayer || []).map((e) => e.event).filter(Boolean),
  }), gtm);
  console.log(p, JSON.stringify(st));
  console.log('   ' + [...hits].join('\n   '));
  await pg.close();
}
await b.close();
