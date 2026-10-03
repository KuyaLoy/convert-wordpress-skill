/**
 * Capture a live site as a servable copy, when the developer has no source files (a site builder with no export,
 * or only the web address). The copy is the golden master: serve it unchanged with parity/serve.py.
 *
 *   node capture-site.mjs <url> <dest> [--max-pages 200] [--delay 300]
 *
 * Only for a site the developer owns or may rebuild. Pages come from /sitemap.xml when there is one, else from
 * following same-origin links. Each page is saved as the browser renders it (<path>/index.html, or the .html name
 * it has), after scrolling so lazy images load; every same-origin file it uses is saved at the same path (CSS, JS,
 * fonts, images, every srcset size, files named in CSS url() and @import). Same-origin absolute links become
 * root-relative, so the copy works on any local address. Writes routes.json; problems go to capture-log.txt.
 * Prints one line: OK|WARN capture-site: <pages> pages, <files> files -> <dest>
 * Limits: files with a query string are saved once under their path (?v=3 is dropped); other origins (CDNs,
 * fonts.googleapis.com) stay remote, as on the live site.
 */
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from './report/pw.mjs';

const args = process.argv.slice(2);
const opt = (name, dflt) => {
  const i = args.indexOf(name);
  if (i < 0) return dflt;
  const v = args[i + 1];
  args.splice(i, 2);
  return v;
};
const maxPages = Number(opt('--max-pages', 200));
const delay = Number(opt('--delay', 300));
const [start, dest] = args;
if (!start || !dest) {
  console.error('usage: node capture-site.mjs <url> <dest> [--max-pages 200] [--delay 300]');
  process.exit(2);
}
const startUrl = new URL(start);
const origin = startUrl.origin;
const hosts = new Set([startUrl.host, startUrl.host.replace(/^www\./, ''), 'www.' + startUrl.host.replace(/^www\./, '')]);
const log = [];
const saved = new Set();

const sameOrigin = (u) => {
  try {
    const x = new URL(u, origin);
    return (x.protocol === 'http:' || x.protocol === 'https:') && hosts.has(x.host) ? x : null;
  } catch {
    return null;
  }
};
const isPage = (pathname) => !/\.[a-z0-9]{1,11}$/i.test(pathname) || /\.(html?|php)$/i.test(pathname);
const pageFile = (pathname) => {
  const p = decodeURIComponent(pathname);
  if (/\.(html?)$/i.test(p)) return p;
  return p.replace(/\/?$/, '/') + 'index.html';
};
const fileOf = (pathname) => path.join(dest, ...decodeURIComponent(pathname).split('/').filter(Boolean));
// Same-origin absolute links (https://site, http://site, //site) become root-relative.
const relink = (text) => {
  let out = text;
  for (const h of hosts) {
    out = out.split(`https://${h}/`).join('/').split(`http://${h}/`).join('/').split(`//${h}/`).join('/');
    out = out.split(`"https://${h}"`).join('"/"').split(`"http://${h}"`).join('"/"');
  }
  return out;
};

function write(file, body) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, body);
}

async function routesFromSitemap(request) {
  const out = [];
  const read = async (u, depth) => {
    try {
      const r = await request.get(u, { timeout: 20000 });
      if (!r.ok()) return;
      const xml = await r.text();
      const locs = [...xml.matchAll(/<loc>\s*([^<\s]+)\s*<\/loc>/g)].map((m) => m[1]);
      if (/<sitemapindex/i.test(xml) && depth < 2) {
        for (const l of locs) await read(l, depth + 1);
      } else {
        for (const l of locs) {
          const x = sameOrigin(l);
          if (x) out.push(x.pathname);
        }
      }
    } catch {
      /* no sitemap: follow links instead */
    }
  };
  await read(origin + '/sitemap.xml', 0);
  return [...new Set(out)];
}

async function saveAsset(request, u, from) {
  const x = sameOrigin(u);
  if (!x || isPage(x.pathname)) return;
  const key = x.pathname;
  if (saved.has(key)) return;
  saved.add(key);
  try {
    const r = await request.get(x.href, { timeout: 30000 });
    if (!r.ok()) {
      log.push(`${r.status()} ${key} (used by ${from})`);
      return;
    }
    let body = await r.body();
    if (/\.css$/i.test(key)) {
      const css = relink(body.toString('utf8'));
      body = Buffer.from(css);
      const refs = [...css.matchAll(/url\(\s*['"]?([^'")]+)['"]?\s*\)/g), ...css.matchAll(/@import\s+['"]([^'"]+)['"]/g)]
        .map((m) => m[1]).filter((v) => !v.startsWith('data:'));
      write(fileOf(key), body);
      for (const ref of refs) await saveAsset(request, new URL(ref, x.href).href, key);
      return;
    }
    write(fileOf(key), body);
  } catch (e) {
    log.push(`failed ${key}: ${e.message.split('\n')[0]}`);
  }
}

const browser = await (await chromium()).launch({ executablePath: process.env.CHROME_PATH || undefined });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, userAgent: undefined });
const request = ctx.request;
const queue = await routesFromSitemap(request);
const fromSitemap = queue.length > 0;
if (!queue.includes(startUrl.pathname)) queue.unshift(startUrl.pathname);
const seen = new Set(queue);
const pages = [];

const page = await ctx.newPage();
const responses = new Set();
page.on('response', (r) => {
  const x = sameOrigin(r.url());
  if (x && r.request().resourceType() !== 'document') responses.add(x.href);
});

while (queue.length && pages.length < maxPages) {
  const route = queue.shift();
  try {
    const res = await page.goto(origin + route, { waitUntil: 'load', timeout: 60000 });
    if (!res || res.status() >= 400) {
      log.push(`${res ? res.status() : 'no answer'} page ${route}`);
      continue;
    }
    // scroll down and back so lazy images and scroll-triggered content load
    await page.evaluate(async () => {
      for (let y = 0; y < document.body.scrollHeight; y += 600) {
        window.scrollTo(0, y);
        await new Promise((r) => setTimeout(r, 80));
      }
      window.scrollTo(0, 0);
      await document.fonts.ready;
    });
    await page.waitForTimeout(500);
    const found = await page.evaluate(() => {
      const attr = (sel, a) => [...document.querySelectorAll(sel)].map((e) => e.getAttribute(a)).filter(Boolean);
      const srcset = [...document.querySelectorAll('[srcset]')].flatMap((e) =>
        e.getAttribute('srcset').split(',').map((c) => c.trim().split(/\s+/)[0]));
      return {
        html: '<!DOCTYPE html>\n' + document.documentElement.outerHTML,
        links: attr('a[href]', 'href'),
        assets: [...attr('img[src]', 'src'), ...srcset, ...attr('link[href]', 'href'), ...attr('script[src]', 'src'),
          ...attr('video[src],audio[src],source[src]', 'src'), ...attr('video[poster]', 'poster')],
      };
    });
    const final = sameOrigin(page.url());
    const savedRoute = final ? final.pathname : route;
    write(path.join(dest, pageFile(savedRoute)), relink(found.html));
    pages.push(savedRoute);
    for (const a of [...found.assets, ...responses]) await saveAsset(request, new URL(a, page.url()).href, savedRoute);
    responses.clear();
    if (!fromSitemap) {
      for (const l of found.links) {
        const x = sameOrigin(new URL(l, page.url()).href);
        if (x && isPage(x.pathname) && !seen.has(x.pathname)) {
          seen.add(x.pathname);
          queue.push(x.pathname);
        }
      }
    }
  } catch (e) {
    log.push(`failed page ${route}: ${e.message.split('\n')[0]}`);
  }
  if (delay) await page.waitForTimeout(delay);
}
await browser.close();

write(path.join(dest, 'routes.json'), JSON.stringify(pages, null, 2) + '\n');
if (log.length) write(path.join(dest, 'capture-log.txt'), log.join('\n') + '\n');
const files = saved.size;
const left = queue.length ? `, ${queue.length} more pages not taken (--max-pages)` : '';
console.log(`${pages.length && !log.length ? 'OK' : 'WARN'} capture-site: ${pages.length} pages, ${files} files -> ${dest}` +
  (log.length ? ` (${log.length} problems, see capture-log.txt)` : '') + left);
process.exit(pages.length ? 0 : 1);
