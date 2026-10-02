/**
 * 1:1 parity check: the WordPress build against the static reference, page by page and width by width.
 *
 *   npm run quick                                all routes, quick widths
 *   npm run full                                 all routes, full widths (+ every CSS breakpoint and 1 px above)
 *   node parity.mjs --routes=/,/about/ --widths=390,1440
 *   node parity.mjs --self                       reference against itself: must be 0.000% everywhere
 *   node parity.mjs --keep=all                   keep every screenshot (default: only failing rows)
 *
 * Settings in parity.config.json (hosts, widths, blocked requests, hidden and masked elements, reveal class, clock).
 * Env: WP=..., REF=... override the hosts; CHROME_PATH for a browser outside Playwright's cache.
 * Output: report/index.html (side by side + diff images) and report/results.json. Never deploy this folder.
 *
 * Per route and width: full-page pixel diff (pixelmatch), visible text diff, SEO diff (title, description,
 * canonical, robots, lang, H1 to H6 order, JSON-LD types). Stable shots: tracking, maps and chat blocked or masked,
 * motion off, reveal forced on, clock frozen, lazy images made eager, the viewport grown to full height and every
 * image loaded and decoded before the shot (Chrome re-picks srcset on resize).
 */
import { chromium } from 'playwright';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';
import fs from 'node:fs';
import path from 'node:path';
import { breakpointWidths } from './breakpoints.mjs';

const arg = (k, d) => (process.argv.find((a) => a.startsWith(`--${k}=`)) || '').split('=').slice(1).join('=') || d;
const flag = (k) => process.argv.includes(`--${k}`);
const here = (f) => new URL(f, import.meta.url);
const CFG = JSON.parse(fs.readFileSync(here('./parity.config.json')));

let full = CFG.widths.full;
if (CFG.breakpointsFromCss && fs.existsSync(CFG.breakpointsFromCss)) {
  full = [...new Set([...full, ...breakpointWidths(fs.readFileSync(CFG.breakpointsFromCss, 'utf8'))])].sort((a, b) => a - b);
}
const WIDTHS = { quick: CFG.widths.quick, full };
const widthsArg = arg('widths', 'quick');
const widths = WIDTHS[widthsArg] || widthsArg.split(',').map(Number);
const allRoutes = JSON.parse(fs.readFileSync(here('./routes.json')));
const routes = arg('routes', '') ? arg('routes').split(',') : allRoutes;
const OUT = path.resolve(arg('out', 'report'));
const THRESHOLD = Number(arg('max-diff', String(CFG.maxDiff ?? 0.001)));
const KEEP = arg('keep', CFG.keepImages || 'fail');

async function pickRef() {
  if (process.env.REF) return process.env.REF.replace(/\/$/, '');
  if (CFG.ref) return CFG.ref.replace(/\/$/, '');
  for (const u of CFG.refCandidates || []) {
    try {
      const r = await fetch(u + '/', { signal: AbortSignal.timeout(3000) });
      if (r.ok) return u.replace(/\/$/, '');
    } catch {}
  }
  throw new Error('No reference host answers: set "ref" in parity.config.json or REF=...');
}

const BLOCK = new RegExp((CFG.block || []).join('|') || '^$');
const STABLE_CSS = `
  *,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}
  ${CFG.reveal ? `${CFG.reveal.selector}{opacity:1!important;transform:none!important}` : ''}
  ${(CFG.hide || []).length ? `${CFG.hide.join(',')}{display:none!important}` : ''}
  ${(CFG.mask || []).length ? `${CFG.mask.join(',')}{visibility:hidden!important}` : ''}
  html{scroll-behavior:auto!important}`;

async function capture(page, url) {
  const res = await page.goto(url, { waitUntil: 'load', timeout: 60000 });
  await page.addStyleTag({ content: STABLE_CSS });
  await page.evaluate(async (reveal) => {
    if (reveal) document.querySelectorAll(reveal.selector).forEach((e) => e.classList.add(reveal.addClass));
    document.querySelectorAll('img[loading="lazy"]').forEach((i) => { i.loading = 'eager'; });
    for (let y = 0; y < document.body.scrollHeight; y += 600) { window.scrollTo(0, y); await new Promise((r) => setTimeout(r, 40)); }
    window.scrollTo(0, 0);
    document.querySelectorAll('img[loading="lazy"]').forEach((i) => { i.loading = 'eager'; });
    await Promise.all([...document.images].filter((i) => !i.complete).map((i) => new Promise((r) => { i.onload = i.onerror = r; })));
    await Promise.all([...document.images].map((i) => (i.decode ? i.decode().catch(() => {}) : null)));
    await document.fonts.ready;
  }, CFG.reveal || null);
  // Grow the viewport to full height first: Chrome re-picks srcset candidates on resize, which can blank an image
  // mid-swap if the screenshot does the resize itself.
  const vw = page.viewportSize();
  const fullH = await page.evaluate(() => document.documentElement.scrollHeight);
  await page.setViewportSize({ width: vw.width, height: fullH });
  await page.evaluate(async () => {
    const pending = () => [...document.images].filter((i) => (i.currentSrc || i.getAttribute('src')) && (!i.complete || !i.naturalWidth));
    for (let n = 0; n < 20; n++) {
      await new Promise((r) => setTimeout(r, 150));
      const p = pending();
      if (!p.length && n >= 2) break;
      await Promise.all(p.map((i) => new Promise((r) => { i.onload = i.onerror = r; setTimeout(r, 3000); })));
    }
    await Promise.all([...document.images].map((i) => (i.decode ? i.decode().catch(() => {}) : null)));
  });
  await page.waitForTimeout(400);
  const shot = await page.screenshot({ fullPage: true });
  await page.setViewportSize(vw);
  const data = await page.evaluate((regions) => {
    const vis = (el) => (el ? el.innerText.replace(/\s+/g, ' ').trim() : '');
    const meta = (sel, at = 'content') => document.querySelector(sel)?.getAttribute(at) ?? null;
    const ld = [...document.querySelectorAll('script[type="application/ld+json"]')].flatMap((s) => {
      try { const j = JSON.parse(s.textContent); const items = Array.isArray(j) ? j : j['@graph'] || [j]; return items.map((x) => x['@type']).flat(); } catch { return ['(invalid JSON-LD)']; }
    });
    return {
      text: Object.fromEntries(Object.entries(regions).map(([k, sel]) => [k, vis(document.querySelector(sel))])),
      seo: {
        title: document.title,
        description: meta('meta[name="description"]'),
        canonical: meta('link[rel="canonical"]', 'href'),
        robots: meta('meta[name="robots"]'),
        lang: document.documentElement.lang,
        headings: [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map((h) => `${h.tagName.toLowerCase()}: ${h.innerText.replace(/\s+/g, ' ').trim()}`),
        jsonld: [...new Set(ld)].sort(),
      },
    };
  }, CFG.textRegions || { main: 'main' });
  return { status: res ? res.status() : 0, shot, ...data };
}

function pad(png, w, h) {
  if (png.width === w && png.height === h) return png;
  const out = new PNG({ width: w, height: h });
  out.data.fill(255);
  PNG.bitblt(png, out, 0, 0, Math.min(png.width, w), Math.min(png.height, h), 0, 0);
  return out;
}

function compareImages(a, b) {
  const A = PNG.sync.read(a), B = PNG.sync.read(b);
  const w = Math.max(A.width, B.width), h = Math.max(A.height, B.height);
  const diff = new PNG({ width: w, height: h });
  const n = pixelmatch(pad(A, w, h).data, pad(B, w, h).data, diff.data, w, h, { threshold: 0.1 });
  return { pixels: n, share: n / (w * h), refHeight: A.height, wpHeight: B.height, png: PNG.sync.write(diff) };
}

const diffList = (a, b) => {
  const out = [];
  for (let i = 0; i < Math.max(a.length, b.length); i++) if (a[i] !== b[i]) out.push({ i, ref: a[i] ?? null, wp: b[i] ?? null });
  return out;
};

const REF = await pickRef();
const WP = flag('self') ? REF : (process.env.WP || CFG.wp).replace(/\/$/, '');
fs.mkdirSync(path.join(OUT, 'img'), { recursive: true });
console.log(`REF ${REF}\nWP  ${WP}\n${routes.length} routes x ${widths.length} widths\n`);
const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined });
const results = [];
for (const route of routes) {
  for (const width of widths) {
    const make = async () => {
      const ctx = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce', deviceScaleFactor: 1 });
      await ctx.route(BLOCK, (r) => r.abort());
      const page = await ctx.newPage();
      if (CFG.clock) await page.clock.setFixedTime(new Date(CFG.clock));
      return { ctx, page };
    };
    const a = await make(), b = await make();
    const slug = (route.replace(/\//g, '_') || '_') + '-' + width;
    const row = { route, width, slug };
    try {
      const [ref, wp] = [await capture(a.page, REF + route), await capture(b.page, WP + route)];
      row.status = { ref: ref.status, wp: wp.status };
      const v = compareImages(ref.shot, wp.shot);
      row.visual = { pixels: v.pixels, share: v.share, refHeight: v.refHeight, wpHeight: v.wpHeight };
      row.text = Object.keys(ref.text).filter((k) => ref.text[k] !== wp.text[k]);
      row.seo = {};
      for (const k of Object.keys(ref.seo)) {
        const x = ref.seo[k], y = wp.seo[k];
        if (Array.isArray(x)) { const d = diffList(x, y); if (d.length) row.seo[k] = d; }
        else if (x !== y) row.seo[k] = { ref: x, wp: y };
      }
      row.textDetail = Object.fromEntries(row.text.map((k) => [k, { ref: ref.text[k].slice(0, 400), wp: wp.text[k].slice(0, 400) }]));
      row.pass = row.status.ref === row.status.wp && row.visual.share <= THRESHOLD && row.visual.refHeight === row.visual.wpHeight && !row.text.length && !Object.keys(row.seo).length;
      if (KEEP === 'all' || !row.pass) {
        fs.writeFileSync(path.join(OUT, 'img', `${slug}-ref.png`), ref.shot);
        fs.writeFileSync(path.join(OUT, 'img', `${slug}-wp.png`), wp.shot);
        fs.writeFileSync(path.join(OUT, 'img', `${slug}-diff.png`), v.png);
        row.images = true;
      }
    } catch (e) {
      row.error = String(e.message || e).slice(0, 300); row.pass = false;
    }
    results.push(row);
    console.log(`${row.pass ? 'PASS' : 'FAIL'} ${route} @${width}` + (row.visual ? ` diff ${(row.visual.share * 100).toFixed(3)}% h ${row.visual.refHeight}/${row.visual.wpHeight}` : '') + (row.text?.length ? ` text:${row.text}` : '') + (row.seo && Object.keys(row.seo).length ? ` seo:${Object.keys(row.seo)}` : '') + (row.error ? ` ERROR ${row.error}` : ''));
    await a.ctx.close(); await b.ctx.close();
  }
}
await browser.close();

fs.writeFileSync(path.join(OUT, 'results.json'), JSON.stringify({ ref: REF, wp: WP, ran: new Date().toISOString(), widths, results }, null, 2));
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[c]);
const pass = results.filter((r) => r.pass).length;
fs.writeFileSync(path.join(OUT, 'index.html'), `<!doctype html><meta charset="utf-8"><title>Parity report</title>
<style>body{font:14px system-ui;margin:20px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:6px;vertical-align:top}
.pass{background:#e8f5e9}.fail{background:#ffebee}img{width:31%;margin-right:1%;border:1px solid #ddd}pre{white-space:pre-wrap;font-size:12px;margin:0}</style>
<h1>Parity: ${pass} of ${results.length} pass</h1><p>REF ${esc(REF)} | WP ${esc(WP)} | ${new Date().toLocaleString()}</p>
<table><tr><th>Route</th><th>Width</th><th>Result</th><th>Details</th></tr>
${results.map((r) => `<tr class="${r.pass ? 'pass' : 'fail'}"><td>${esc(r.route)}</td><td>${r.width}</td><td>${r.pass ? 'PASS' : 'FAIL'}</td><td>
${r.error ? `<pre>${esc(r.error)}</pre>` : `<pre>status ${r.status.ref}/${r.status.wp} | pixels ${(r.visual.share * 100).toFixed(3)}% | height ${r.visual.refHeight}/${r.visual.wpHeight}
${r.text.length ? 'text differs: ' + r.text.join(', ') + '\n' + esc(JSON.stringify(r.textDetail, null, 1)) : ''}${Object.keys(r.seo).length ? '\nseo: ' + esc(JSON.stringify(r.seo, null, 1)) : ''}</pre>
${r.images ? `<details><summary>images (ref, wp, diff)</summary><img src="img/${r.slug}-ref.png"><img src="img/${r.slug}-wp.png"><img src="img/${r.slug}-diff.png"></details>` : ''}`}
</td></tr>`).join('\n')}</table>`);
console.log(`\n${pass} of ${results.length} pass. Report: ${path.join(OUT, 'index.html')}`);
process.exit(pass === results.length ? 0 : 1);
