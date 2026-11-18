/**
 * Design checks beyond the still page, numbers first (images only for failures):
 *
 *   node design-check.mjs --states  [--routes=/,/about/]   hover, focus-visible and the configured clicks (open menu,
 *                                                           tabs, sliders) against the source site in the same state
 *   node design-check.mjs --motion  [--routes=...]          transition and animation duration, delay and easing per
 *                                                           element against the source
 *   node design-check.mjs --long    [--routes=/kit-long-test-about/]   WordPress only: the long-content test page
 *                                                           (long-content.php) at 320 to 1920: page overflow, clipped text
 *   node design-check.mjs --states --motion --long          all three; --all prints passing rows too
 *
 * Hosts: parity.config.json (REF=..., WP=... override). Settings and pass marks: design-check.config.json.
 * Elements are matched between the two sites by their DOM path (tag and position from <body>), which the 1:1 DOM
 * diff already keeps equal. Output: report/design-check.json (rows: check, route, width, selector, state, prop,
 * ref, got, pass, image); line 1 OK|FAIL design-check: n of m pass, then the failing rows (at most 20).
 * Exit 1 when a row fails. The figma-to-wordpress skill writes the same row shape for its Figma checks.
 */
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const arg = (k, d) => (process.argv.find((a) => a.startsWith(`--${k}=`)) || '').split('=').slice(1).join('=') || d;
const flag = (k) => process.argv.includes(`--${k}`);
const here = (f) => new URL(f, import.meta.url);
const PCFG = JSON.parse(fs.readFileSync(here('./parity.config.json')));
const CFG = JSON.parse(fs.readFileSync(here('./design-check.config.json')));
const PM = CFG.passMarks;
const OUT = path.resolve(arg('out', 'report'));
const IMG = path.join(OUT, 'design-check');
const modes = ['states', 'motion', 'long'].filter(flag);
if (!modes.length) { console.log('FAIL design-check: give --states, --motion and/or --long'); process.exit(2); }

async function pickRef() {
  if (process.env.REF) return process.env.REF.replace(/\/$/, '');
  if (PCFG.ref && !PCFG.ref.includes('{{')) return PCFG.ref.replace(/\/$/, '');
  for (const u of PCFG.refCandidates || []) {
    try { const r = await fetch(u + '/', { signal: AbortSignal.timeout(3000) }); if (r.ok) return u.replace(/\/$/, ''); } catch {}
  }
  return '';
}
const WP = (process.env.WP || PCFG.wp).replace(/\/$/, '');
const REF = modes.some((m) => m !== 'long') ? await pickRef() : '';
if (modes.some((m) => m !== 'long') && !REF) { console.log('FAIL design-check: no reference host answers (parity.config.json "ref" or REF=...)'); process.exit(2); }
const allRoutes = JSON.parse(fs.readFileSync(here('./routes.json'))).filter((r) => !r.includes('missing'));
const routesArg = arg('routes', '');
const BLOCK = new RegExp((PCFG.block || []).join('|') || '^$');
const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined });
const rows = [];
const seenShared = new Set();
let imgCount = 0;

const SLIDERS = (CFG.longIgnore || []).join(',');
async function open(host, route, width, { still = true } = {}) {
  const ctx = await browser.newContext({ viewport: { width, height: 900 }, deviceScaleFactor: 1 });
  await ctx.route(BLOCK, (r) => r.abort());
  const page = await ctx.newPage();
  const res = await page.goto(host + route, { waitUntil: 'load', timeout: 60000 });
  await page.evaluate(() => document.fonts.ready);
  if (still) await page.addStyleTag({ content: '*,*::before,*::after{transition:none!important;animation:none!important}#wpadminbar{display:none!important}' });
  else await page.addStyleTag({ content: '#wpadminbar{display:none!important}' });
  return { ctx, page, status: res ? res.status() : 0 };
}

// In-page helpers: a DOM path per element, computed styles, interactive elements of the regions.
const PAGE_JS = `
window.__kitPath = (el) => { const p = []; for (let e = el; e && e !== document.body; e = e.parentElement) { let i = 1; for (let s = e.previousElementSibling; s; s = s.previousElementSibling) if (s.tagName === e.tagName) i++; p.unshift(e.tagName.toLowerCase() + ':' + i); } return p.join('>'); };
window.__kitFind = (path) => { let e = document.body; for (const part of path.split('>')) { if (!e) return null; const [t, i] = part.split(':'); e = [...e.children].filter((c) => c.tagName.toLowerCase() === t)[Number(i) - 1]; } return e || null; };
window.__kitStyle = (el, props) => { const cs = getComputedStyle(el); const r = el.getBoundingClientRect(); const o = {}; for (const p of props) o[p] = p === 'width' ? Math.round(r.width) + 'px' : p === 'height' ? Math.round(r.height) + 'px' : cs.getPropertyValue(p); o.visible = cs.display !== 'none' && cs.visibility !== 'hidden' && r.width > 0 && r.height > 0; return o; };
`;
const num = (v) => { const m = String(v).match(/^-?[\d.]+/); return m ? Number(m[0]) : null; };
const times = (v) => String(v).split(',').map((x) => { const t = x.trim(); return t.endsWith('ms') ? Number(t.slice(0, -2)) : Number(t.replace('s', '')) * 1000; });

function same(prop, a, b, tolerancePx) {
  if (a === b) return true;
  if (/^-?[\d.]+px$/.test(a) && /^-?[\d.]+px$/.test(b)) return Math.abs(num(a) - num(b)) <= tolerancePx;
  return false;
}

function add(row) { rows.push(row); }

async function shot(page, selectorPath, name) {
  if (imgCount >= 40) return null;
  fs.mkdirSync(IMG, { recursive: true });
  const file = path.join(IMG, `${name.replace(/[^a-z0-9]+/gi, '_')}.png`);
  try {
    const h = await page.evaluateHandle((p) => window.__kitFind(p), selectorPath);
    const el = h.asElement();
    if (el) await el.screenshot({ path: file }); else await page.screenshot({ path: file });
    imgCount++;
    return path.relative(OUT, file).replace(/\\/g, '/');
  } catch { return null; }
}

// --states: rest, hover and focus-visible of the interactive elements, and the configured clicks.
async function states(route, width) {
  const sides = {};
  for (const [name, host] of [['ref', REF], ['wp', WP]]) {
    sides[name] = await open(host, route, width);
    await sides[name].page.addScriptTag({ content: PAGE_JS });
  }
  if (sides.ref.status !== sides.wp.status) add({ check: 'state', route, width, selector: '-', state: 'load', prop: 'status', ref: sides.ref.status, got: sides.wp.status, pass: false, image: null });
  const found = await sides.ref.page.evaluate(({ regions, max }) => {
    const sel = 'a[href],button,[role=button],[role=tab],summary,input:not([type=hidden]),select,textarea';
    const out = [];
    for (const r of regions) for (const root of document.querySelectorAll(r)) for (const el of root.querySelectorAll(sel)) {
      const b = el.getBoundingClientRect(); const cs = getComputedStyle(el);
      if (b.width && b.height && cs.visibility !== 'hidden') out.push((el.closest('main') ? 'page|' : 'shared|') + window.__kitPath(el));
    }
    return [...new Set(out)].slice(0, max);
  }, { regions: CFG.regions, max: CFG.maxElements });
  // Header and footer repeat on every route: check them once per width.
  const paths = found.filter((x) => x.startsWith('page|') || !seenShared.has(width + x)).map((x) => { seenShared.add(width + x); return x.split('|')[1]; });
  for (const p of paths) {
    for (const state of ['hover', 'focus']) {
      const got = {};
      for (const side of ['ref', 'wp']) {
        const { page } = sides[side];
        const h = await page.evaluateHandle((x) => window.__kitFind(x), p);
        const el = h.asElement();
        if (!el) { got[side] = null; continue; }
        try {
          await page.mouse.move(0, 0);
          if (state === 'hover') { await el.scrollIntoViewIfNeeded(); await el.hover({ timeout: 2000, force: true }); }
          else { await page.keyboard.press('Shift'); await el.focus(); }
          await page.waitForTimeout(30);
          got[side] = await page.evaluate(({ x, props }) => window.__kitStyle(window.__kitFind(x), props), { x: p, props: CFG.styleProps });
          if (state === 'focus') await el.evaluate((e) => e.blur());
        } catch { got[side] = null; }
      }
      if (!got.ref || !got.wp) {
        add({ check: 'state', route, width, selector: p, state, prop: 'element', ref: !!got.ref, got: !!got.wp, pass: !got.ref && !got.wp, image: null });
        continue;
      }
      const bad = CFG.styleProps.filter((k) => !same(k, got.ref[k], got.wp[k], PM.px));
      if (!bad.length) { add({ check: 'state', route, width, selector: p, state, prop: '*', ref: 'same', got: 'same', pass: true, image: null }); continue; }
      // One row per element and state: the first property's values, every differing property named.
      add({ check: 'state', route, width, selector: p, state, prop: bad.join(','), ref: got.ref[bad[0]], got: got.wp[bad[0]], pass: false, image: null });
    }
  }
  for (const s of CFG.states.filter((x) => x.route === route && (!x.widths || x.widths.includes(width)))) {
    const snap = {};
    for (const side of ['ref', 'wp']) {  // a fresh page per entry: one toggle never leaks into the next
      await sides[side].ctx.close();
      sides[side] = await open(side === 'ref' ? REF : WP, route, width);
      await sides[side].page.addScriptTag({ content: PAGE_JS });
      const { page } = sides[side];
      try {
        await page.locator(s.click).first().click({ timeout: 3000 });
        await page.waitForTimeout(s.wait || 100);
        snap[side] = await page.evaluate(({ check, props }) => {
          const root = document.querySelector(check); if (!root) return null;
          return [root, ...root.querySelectorAll('*')].slice(0, 400).map((e) => [window.__kitPath(e), window.__kitStyle(e, props)]);
        }, { check: s.check, props: CFG.styleProps });
      } catch { snap[side] = null; }
    }
    if (!snap.ref || !snap.wp) { add({ check: 'state', route, width, selector: s.click, state: s.name, prop: 'click', ref: !!snap.ref, got: !!snap.wp, pass: false, image: null }); continue; }
    const W = Object.fromEntries(snap.wp);
    let fails = 0;
    for (const [p, st] of snap.ref) {
      const w = W[p];
      const diff = !w ? ['element'] : ['visible', ...CFG.styleProps].filter((k) => !(k === 'visible' ? st.visible === w.visible : same(k, st[k], w[k], PM.px)));
      for (const k of diff) {
        fails++;
        add({ check: 'state', route, width, selector: p, state: s.name, prop: k, ref: k === 'element' ? true : st[k], got: k === 'element' ? false : w[k], pass: false, image: fails === 1 ? await shot(sides.wp.page, p, `${route}-${s.name}-${width}-wp`) : null });
      }
    }
    if (!fails) add({ check: 'state', route, width, selector: s.check, state: s.name, prop: '*', ref: 'same', got: 'same', pass: true, image: null });
  }
  await sides.ref.ctx.close(); await sides.wp.ctx.close();
}

// --motion: every element of the regions with a transition or an animation on either side.
async function motion(route, width) {
  const read = async (host) => {
    const s = await open(host, route, width, { still: false });
    await s.page.addScriptTag({ content: PAGE_JS });
    const list = await s.page.evaluate((regions) => {
      const out = {};
      for (const r of regions) for (const root of document.querySelectorAll(r)) for (const el of [root, ...root.querySelectorAll('*')]) {
        const cs = getComputedStyle(el);
        const moving = (v) => v.split(',').some((t) => parseFloat(t) > 0);
        if (moving(cs.transitionDuration) || moving(cs.animationDuration)) {
          out[window.__kitPath(el)] = { 'transition-property': cs.transitionProperty, 'transition-duration': cs.transitionDuration,
            'transition-delay': cs.transitionDelay, 'transition-timing-function': cs.transitionTimingFunction,
            'animation-name': cs.animationName, 'animation-duration': cs.animationDuration, 'animation-delay': cs.animationDelay,
            'animation-timing-function': cs.animationTimingFunction, 'animation-iteration-count': cs.animationIterationCount };
        }
      }
      return out;
    }, CFG.regions);
    await s.ctx.close();
    return list;
  };
  const [R, Wl] = [await read(REF), await read(WP)];
  const paths = [...new Set([...Object.keys(R), ...Object.keys(Wl)])];
  let fails = 0;
  for (const p of paths) {
    const a = R[p], b = Wl[p];
    if (!a || !b) { fails++; add({ check: 'motion', route, width, selector: p, state: 'rest', prop: 'motion', ref: a ? 'moves' : 'still', got: b ? 'moves' : 'still', pass: false, image: null }); continue; }
    for (const k of Object.keys(a)) {
      const unhash = (v) => String(v).split(',').map((x) => x.trim().replace(/(__|_|-)[A-Za-z0-9]{5,}$/, '')).join(',');
      const ok = /duration|delay/.test(k)
        ? times(a[k]).length === times(b[k]).length && times(a[k]).every((t, i) => Math.abs(t - times(b[k])[i]) <= PM.ms)
        : k === 'animation-name' ? unhash(a[k]) === unhash(b[k]) : a[k] === b[k];
      if (!ok) { fails++; add({ check: 'motion', route, width, selector: p, state: 'rest', prop: k, ref: a[k], got: b[k], pass: false, image: null }); }
    }
  }
  if (!fails) add({ check: 'motion', route, width, selector: '*', state: 'rest', prop: 'elements', ref: Object.keys(R).length, got: Object.keys(Wl).length, pass: true, image: null });
}

// --long: WordPress only, the long-content test page at every width.
async function long(route) {
  for (const width of CFG.longWidths) {
    const s = await open(WP, route, width);
    if (s.status !== 200) {
      add({ check: 'long', route, width, selector: '-', state: 'long', prop: 'status', ref: 200, got: s.status, pass: false, image: null });
      await s.ctx.close();
      break;
    }
    await s.page.addScriptTag({ content: PAGE_JS });
    const r = await s.page.evaluate((sliders) => {
      const over = document.documentElement.scrollWidth - window.innerWidth;
      const clipped = [];
      for (const el of document.body.querySelectorAll('*')) {
        const cs = getComputedStyle(el);
        if (!/(hidden|clip)/.test(cs.overflowX + cs.overflowY) || cs.webkitLineClamp !== 'none' && cs.webkitLineClamp) continue;
        if (cs.textOverflow === 'ellipsis' || el.offsetWidth <= 2 || el.offsetHeight <= 2) continue; // intended, or screen-reader text
        if (!el.innerText || !el.innerText.trim() || (sliders && el.closest(sliders))) continue; // sliders scroll on purpose
        if (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1) clipped.push(window.__kitPath(el));
      }
      const wide = [...document.body.querySelectorAll('*')].filter((e) => e.getBoundingClientRect().right > window.innerWidth + 1 && getComputedStyle(e).position !== 'fixed').slice(0, 5).map((e) => window.__kitPath(e));
      return { over, clipped: clipped.slice(0, 10), clippedCount: clipped.length, wide };
    }, SLIDERS);
    const okOver = r.over <= PM.overflowPx, okClip = r.clippedCount <= PM.clippedText;
    add({ check: 'long', route, width, selector: okOver ? 'html' : (r.wide[0] || 'html'), state: 'long', prop: 'overflow-x', ref: `<= ${PM.overflowPx}px`, got: `${r.over}px`, pass: okOver,
      image: okOver ? null : await shot(s.page, '', `${route}-long-${width}-page`) });
    add({ check: 'long', route, width, selector: r.clipped[0] || '*', state: 'long', prop: 'clipped-text', ref: PM.clippedText, got: r.clippedCount, pass: okClip,
      image: okClip ? null : await shot(s.page, r.clipped[0], `${route}-long-${width}-clipped`) });
    await s.ctx.close();
  }
}

for (const mode of modes) {
  const routes = routesArg ? routesArg.split(',') : mode === 'long' ? CFG.longRoutes : mode === 'states' ? [...new Set([...allRoutes, ...CFG.states.map((s) => s.route)])] : allRoutes;
  if (mode === 'long' && !routes.length) { add({ check: 'long', route: '-', width: 0, selector: '-', state: 'long', prop: 'test page', ref: 'a route', got: 'none', pass: false, image: null }); continue; }
  for (const route of routes) {
    try {
      if (mode === 'states') for (const w of CFG.stateWidths) await states(route, w);
      if (mode === 'motion') await motion(route, CFG.motionWidth);
      if (mode === 'long') await long(route);
    } catch (e) {
      add({ check: mode === 'states' ? 'state' : mode, route, width: 0, selector: '-', state: '-', prop: 'error', ref: '', got: String(e.message || e).slice(0, 200), pass: false, image: null });
    }
  }
}
await browser.close();

const pass = rows.filter((r) => r.pass).length, fail = rows.length - pass;
fs.mkdirSync(OUT, { recursive: true });
fs.writeFileSync(path.join(OUT, 'design-check.json'), JSON.stringify({ tool: 'design-check', version: 1, ran: new Date().toISOString(),
  ref: REF, wp: WP, modes, passMarks: PM, rows, summary: { pass, fail } }, null, 2));
const listed = rows.filter((r) => flag('all') || !r.pass);
console.log(`${fail ? 'FAIL' : 'OK'} design-check: ${pass} of ${rows.length} pass (${modes.join(', ')}). Rows: ${path.join(OUT, 'design-check.json')}`);
for (const r of listed.slice(0, flag('all') ? listed.length : 20)) {
  console.log(`${r.pass ? 'PASS' : 'FAIL'} ${r.check} ${r.route} @${r.width} ${r.state} ${r.selector} ${r.prop}: ref ${r.ref} | wp ${r.got}${r.image ? ' | ' + r.image : ''}`);
}
if (!flag('all') && listed.length > 20) console.log(`... ${listed.length - 20} more failures in design-check.json`);
process.exit(fail ? 1 : 0);
