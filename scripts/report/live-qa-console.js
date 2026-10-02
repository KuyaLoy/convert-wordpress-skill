/*
 * live-qa-console.js: the live-qa.py page and redirect checks, run inside a real browser on the live site, for hosts
 * whose bot filter blocks scripted requests (Imunify360 "One moment, please" or 415).
 *
 * 1. Open https://<domain>/ in a normal browser tab (logged out).
 * 2. Set the inputs, then paste this file into DevTools > Console (or run it with your agent's browser JavaScript
 *    tool). It starts the checks in the background and returns at once.
 *      window.LIVE_QA = { gtm: 'GTM-XXXXXXX', local: 'example.test', redirects: [{ from: '/old/', to: '/new/' }] };
 * 3. A few seconds later read the result: window.__liveQa.summary (text) or window.__liveQa (all data).
 *
 * Same-origin fetch() only: GET requests, nothing is posted. The summary avoids "=", ";" and "?" because some
 * browser automation tools refuse output that looks like cookies or query strings. Host rules (http and www one
 * hop) cannot be tested from a page: check those with curl -I or the browser address bar.
 */
(() => {
  const cfg = Object.assign({ gtm: '', local: '.test', redirects: [], thankYou: '/thank-you/' }, window.LIVE_QA || {});
  const out = (window.__liveQa = { done: false, pages: 0, redirects: 0, fails: [], notes: [], summary: 'running' });
  const clean = (s) => String(s).replace(/[=;?]/g, ' ');
  const fetchText = async (url, opts = {}) => {
    const r = await fetch(url, Object.assign({ credentials: 'omit', cache: 'no-store' }, opts));
    return { status: r.status, url: r.url, redirected: r.redirected, text: await r.text() };
  };
  const run = async () => {
    const idx = await fetchText('/sitemap_index.xml');
    const maps = [...idx.text.matchAll(/<loc>([^<]+\.xml)<\/loc>/g)].map((m) => m[1]);
    let urls = [];
    for (const sm of maps) urls = urls.concat([...(await fetchText(sm)).text.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]));
    if (!urls.length) out.fails.push('sitemap lists no URLs');
    if (urls.some((u) => u.includes(cfg.thankYou.replace(/\/$/, '')))) out.fails.push('thank-you page is in the sitemap');
    urls.push(location.origin + cfg.thankYou);
    for (const u of urls) {
      const r = await fetchText(u);
      const [head, body = ''] = r.text.split('</head>');
      const p = [];
      if (r.status !== 200 || r.url.replace(/\/$/, '') !== u.replace(/\/$/, '')) p.push('status ' + r.status + ' final ' + new URL(r.url).pathname);
      if (cfg.gtm) {
        if (!head.includes(cfg.gtm) || !body.slice(0, 3000).includes('ns.html' + String.fromCharCode(63) + 'id' + String.fromCharCode(61) + cfg.gtm)) p.push('GTM head or noscript missing');
        if ((r.text.split(cfg.gtm).join('').match(/GTM-[A-Z0-9]{5,}/g) || []).length) p.push('another GTM id');
      }
      const h1 = (r.text.match(/<h1[\s>]/g) || []).length;
      if (h1 !== 1) p.push('h1 count ' + h1);
      if (cfg.local && r.text.includes(cfg.local)) p.push('local host string');
      if (!head.includes('name="description"')) p.push('no meta description');
      if (!head.includes('noindex') && !head.includes('rel="canonical"')) p.push('no canonical');
      if (p.length) out.fails.push(new URL(u).pathname + ': ' + p.join(', '));
      out.pages++;
    }
    for (const rule of cfg.redirects) {
      if (rule.regex || rule.from.startsWith('^')) { out.notes.push('regex rule, test by hand: ' + rule.from); continue; }
      const r = await fetchText(rule.from);
      const final = new URL(r.url).pathname;
      if (r.status !== 200 || final !== rule.to) out.fails.push('redirect ' + rule.from + ' landed on ' + final + ' (' + r.status + '), expected ' + rule.to);
      out.redirects++;
    }
    for (const n of [1, 2]) {
      const r = await fetchText('/live-qa-missing-page-404/');
      if (r.status !== 404) out.fails.push('missing URL answered ' + r.status + ' on request ' + n);
    }
    for (const pth of ['/installer.php', '/installer-backup.php', '/wp-content/debug.log', '/readme.html', '/_plan/', '/_setup/',
      '/handoff.md', '/ai-handoff-summary.md', '/BUILD-MAP.md', '/wp-config.php']) {
      const r = await fetch(pth, { credentials: 'omit', cache: 'no-store', redirect: 'manual' });
      if (r.status === 200 && (await r.text()).trim()) out.fails.push(pth + ' is public');
    }
    const users = await fetchText('/wp-json/wp/v2/users');
    if (users.status === 200 && users.text.trim().startsWith('[')) out.notes.push('REST user list is public: ' + JSON.parse(users.text).map((x) => x.slug).join(', '));
  };
  run()
    .catch((e) => out.fails.push('error: ' + e.message))
    .finally(() => {
      out.done = true;
      out.summary = clean(
        (out.fails.length ? out.fails.length + ' problem(s)' : 'ALL PASS') + ' | pages ' + out.pages + ' | redirects ' + out.redirects +
        (out.fails.length ? ' | ' + out.fails.join(' / ') : '') + (out.notes.length ? ' | notes: ' + out.notes.join(' / ') : '')
      );
    });
  return 'started: read window.__liveQa.summary in a few seconds';
})();
