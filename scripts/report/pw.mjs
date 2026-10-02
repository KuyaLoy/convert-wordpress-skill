// Load Playwright: the project's own install first (npm i -D playwright), else a global one (cloud workspaces).
import { execSync } from 'node:child_process';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

export async function chromium() {
  try { return (await import('playwright')).chromium; } catch {}
  const roots = [process.env.NODE_PATH, safe(() => execSync('npm root -g', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim()), '/opt/node22/lib/node_modules'];
  for (const root of roots.filter(Boolean)) {
    try { return (await import(pathToFileURL(path.join(root, 'playwright', 'index.mjs')).href)).chromium; } catch {}
  }
  throw new Error('Playwright not found: run "npm i -D playwright" here, then "npx playwright install chromium"');
}

function safe(fn) { try { return fn(); } catch { return ''; } }
