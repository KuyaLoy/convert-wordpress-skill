// Report HTML to an A4 PDF, optionally with other PDFs appended (one attachment for the task tracker).
//   node pdf.mjs report.html Final-Live-Check.pdf
//   node pdf.mjs report.html Final-Report.pdf Website-Editing-Guide.pdf
// Merging needs pdf-lib (npm i pdf-lib, or a global install); without it: qpdf --empty --pages a.pdf b.pdf -- out.pdf
import { chromium } from './pw.mjs';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const [src, out, ...extra] = process.argv.slice(2);
if (!out) { console.error('usage: node pdf.mjs <report.html> <out.pdf> [append.pdf ...]'); process.exit(2); }
const b = await (await chromium()).launch({ executablePath: process.env.CHROME_PATH || undefined });
const pg = await b.newPage();
await pg.goto(pathToFileURL(path.resolve(src)).href, { waitUntil: 'networkidle' });
const report = await pg.pdf({ format: 'A4', printBackground: true, margin: { top: '14mm', bottom: '14mm', left: '13mm', right: '13mm' } });
await b.close();

if (!extra.length) {
  fs.writeFileSync(out, report);
} else {
  let lib;
  try { lib = await import('pdf-lib'); } catch {
    const root = execSync('npm root -g', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim();
    lib = await import(pathToFileURL(path.join(root, 'pdf-lib', 'cjs', 'index.js')).href);
  }
  const { PDFDocument } = lib.default || lib;
  const doc = await PDFDocument.load(report);
  for (const f of extra) {
    const add = await PDFDocument.load(fs.readFileSync(f));
    for (const p of await doc.copyPages(add, add.getPageIndices())) doc.addPage(p);
  }
  fs.writeFileSync(out, await doc.save());
}
console.log(out);
