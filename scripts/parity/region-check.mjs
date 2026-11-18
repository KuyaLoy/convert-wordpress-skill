// Pixel and text diff of single regions (header, footer, one section...) between the golden master and WordPress:
// the P1-06 check before the pages under them exist, and check-section.py's per-section check.
//   node region-check.mjs <ref> <wp> [route] [selectors] [widths] [hide]
//   node region-check.mjs http://site-ref.test http://site.test / header,footer 390,768,1440 main,#consent
//   node region-check.mjs http://site-ref.test http://site.test /about/ "section.hero" 390,1440 ""
// "hide" (default: main) is display:none on both sides: an empty WordPress <main> and the full static one would
// put the footer at different heights (fractional offsets shift text by 1 px), and fixed overlays (cookie bars,
// chat buttons) land on different parts of a region. Pass "" to hide nothing (a section inside main).
// Numbers first: one line per failing region (size, pixel share, text); images only for failures, in
// report/region/. Line 1: OK|FAIL region-check: n of m pass. Exit 1 when any region differs.
import { chromium } from 'playwright';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';
import fs from 'node:fs';
import path from 'node:path';
const [ref, wp, route = '/', sels = 'header,footer', ws = '390,1440', hide = 'main'] = process.argv.slice(2);
const OUT = path.resolve('report', 'region');
const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined });
let fail = 0, total = 0;
const lines = [];
const say = (l) => lines.push(l);
const slug = (s) => s.replace(/[^a-z0-9]+/gi, '_').replace(/^_|_$/g, '') || 'root';
for (const w of ws.split(',').map(Number)) {
  const shots = {}, texts = {};
  for (const [name, host] of [['ref', ref], ['wp', wp]]) {
    const page = await browser.newPage({ viewport: { width: w, height: 900 }, reducedMotion: 'reduce' });
    await page.route(/googletagmanager|google-analytics|recaptcha|doubleclick/, (r) => r.abort());
    await page.goto(host + route, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.addStyleTag({ content: `[data-aos]{opacity:1!important;transform:none!important}*{animation:none!important;transition:none!important}#wpadminbar{display:none!important}${hide ? hide + '{display:none!important}' : ''}` });
    for (const s of sels.split(',')) {
      const el = page.locator(s).first();
      if (!(await el.count()) || !(await el.isVisible())) { shots[name + s] = null; continue; }
      shots[name + s] = PNG.sync.read(await el.screenshot());
      texts[name + s] = (await el.innerText()).replace(/\s+/g, ' ').trim();
    }
    await page.close();
  }
  for (const s of sels.split(',')) {
    total++;
    const a = shots['ref' + s], b = shots['wp' + s];
    if (!a || !b) { fail++; say(`FAIL ${s} @${w} missing or hidden on ${!a ? 'ref' : ''}${!a && !b ? ' and ' : ''}${!b ? 'wp' : ''}`); continue; }
    const textSame = texts['ref' + s] === texts['wp' + s];
    let n = 0, pct = '-', size = a.width === b.width && a.height === b.height;
    if (size) { n = pixelmatch(a.data, b.data, null, a.width, a.height, { threshold: 0 }); pct = (100 * n / (a.width * a.height)).toFixed(3); }
    if (size && !n && textSame) { if (process.argv.includes('--all')) say(`PASS ${s} @${w} diff 0.000% (${a.width}x${a.height})`); continue; }
    fail++;
    say(`FAIL ${s} @${w}` + (size ? ` diff ${pct}%` : ` size ${a.width}x${a.height} vs ${b.width}x${b.height}`) + (textSame ? '' : ' text differs'));
    if (!textSame) say(`  ref: ${texts['ref' + s].slice(0, 160)}\n  wp:  ${texts['wp' + s].slice(0, 160)}`);
    fs.mkdirSync(OUT, { recursive: true });
    fs.writeFileSync(path.join(OUT, `${slug(route)}-${slug(s)}-${w}-ref.png`), PNG.sync.write(a));
    fs.writeFileSync(path.join(OUT, `${slug(route)}-${slug(s)}-${w}-wp.png`), PNG.sync.write(b));
  }
}
await browser.close();
console.log(`${fail ? 'FAIL' : 'OK'} region-check: ${total - fail} of ${total} pass` + (fail ? ` (images: ${OUT})` : ''));
if (lines.length) console.log(lines.slice(0, 40).join('\n'));
process.exit(fail ? 1 : 0);
