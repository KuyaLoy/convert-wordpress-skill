// Pixel diff of single regions (header, footer...) between the golden master and WordPress: the S1-07 check,
// before the pages under them exist.
//   node region-check.mjs <ref> <wp> [route] [selectors] [widths] [hide]
//   node region-check.mjs http://site-ref.test http://site.test / header,footer 390,768,1440 main,#consent
// "hide" (default: main) is display:none on both sides: an empty WordPress <main> and the full static one would
// put the footer at different heights (fractional offsets shift text by 1 px), and fixed overlays (cookie bars,
// chat buttons) land on different parts of a region. Exit 1 when any region differs.
import { chromium } from 'playwright';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';
const [ref, wp, route = '/', sels = 'header,footer', ws = '390,1440', hide = 'main'] = process.argv.slice(2);
const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined });
let fail = 0;
for (const w of ws.split(',').map(Number)) {
  const shots = {};
  for (const [name, host] of [['ref', ref], ['wp', wp]]) {
    const page = await browser.newPage({ viewport: { width: w, height: 900 }, reducedMotion: 'reduce' });
    await page.route(/googletagmanager|google-analytics|recaptcha|doubleclick/, (r) => r.abort());
    await page.goto(host + route, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.addStyleTag({ content: `[data-aos]{opacity:1!important;transform:none!important}*{animation:none!important;transition:none!important}${hide ? hide + '{display:none!important}' : ''}` });
    for (const s of sels.split(',')) {
      const el = page.locator(s).first();
      shots[name + s] = PNG.sync.read(await el.screenshot());
    }
    await page.close();
  }
  for (const s of sels.split(',')) {
    const a = shots['ref' + s], b = shots['wp' + s];
    if (a.width !== b.width || a.height !== b.height) { fail++; console.log(`FAIL ${s} @${w} size ${a.width}x${a.height} vs ${b.width}x${b.height}`); continue; }
    const n = pixelmatch(a.data, b.data, null, a.width, a.height, { threshold: 0 });
    const pct = (100 * n / (a.width * a.height)).toFixed(3);
    if (n) fail++;
    console.log(`${n ? 'FAIL' : 'PASS'} ${s} @${w} diff ${pct}% (${a.width}x${a.height})`);
  }
}
await browser.close();
process.exit(fail ? 1 : 0);
