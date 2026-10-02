// Screenshots of the live site for the final report.
//   node shots.mjs https://example.com / /services/:390 /thank-you/ /about/:1440:about-desktop
// "path:width[:name]". Width 390 or less gives a phone shot (height 844); the default is 1440 x 900.
// Files: <name>.png, by default shot-<slug>-<width>.png (report-template.html uses these names).
import { chromium } from './pw.mjs';
const [site, ...paths] = process.argv.slice(2);
if (!site) { console.error('usage: node shots.mjs <site> <path[:width[:name]]> ...'); process.exit(2); }
const b = await (await chromium()).launch({ executablePath: process.env.CHROME_PATH || undefined });
for (const arg of paths.length ? paths : ['/']) {
  const [p, w, n] = arg.split(':');
  const width = Number(w || 1440), height = width < 700 ? 844 : 900;
  const pg = await b.newPage({ viewport: { width, height } });
  await pg.goto(site.replace(/\/$/, '') + p, { waitUntil: 'load', timeout: 90000 });
  await pg.waitForTimeout(3500); // fixed wait: map iframes never reach network idle
  const name = (n || `shot-${p.replace(/^\/|\/$/g, '').replace(/\//g, '-') || 'home'}-${width}`) + '.png';
  await pg.screenshot({ path: name });
  console.log(name);
  await pg.close();
}
await b.close();
