/**
 * The test widths for a stylesheet: every px breakpoint in its @media queries, and 1 px past it.
 * max-width: N gives N and N + 1; min-width: N gives N - 1 and N.
 *
 *   node breakpoints.mjs path/to/static-built.css        prints the widths as JSON
 *
 * parity.mjs uses it when parity.config.json "breakpointsFromCss" points at the static build's CSS.
 */
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';

export function breakpointWidths(css) {
  const out = new Set();
  for (const m of css.matchAll(/@media[^{]*/g)) {
    for (const q of m[0].matchAll(/\((max|min)-width:\s*(\d+(?:\.\d+)?)px\)/g)) {
      const n = Math.floor(Number(q[2]));
      if (q[1] === 'max') { out.add(n); out.add(n + 1); } else { out.add(n - 1); out.add(n); }
    }
  }
  return [...out].filter((w) => w >= 280 && w <= 2560).sort((a, b) => a - b);
}

if (import.meta.url === pathToFileURL(process.argv[1] || '').href) {
  const file = process.argv[2];
  if (!file) { console.error('usage: node breakpoints.mjs <css file>'); process.exit(2); }
  console.log(JSON.stringify(breakpointWidths(fs.readFileSync(file, 'utf8'))));
}
