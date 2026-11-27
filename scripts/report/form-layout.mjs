// Form layout check: a lead form laid out as the kit's standard asks (references/forms-email.md > Form layout).
//   node form-layout.mjs <page url or file> [--form <selector>] [--widths 1280,390]
// At each width: every label above its field, short fields two per row from 640px and one below, the message (a
// textarea) full width, every input, select and textarea at least 16px, a visible focus ring, and an error state
// (a field with a CF7 note gets a different border). Line 1: OK|FAIL form-layout; then the failures (at most 20).
import { chromium } from './pw.mjs';
import path from 'node:path';
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';

const args = process.argv.slice(2);
const opt = (name, def) => {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] ? args.splice(i, 2)[1] : def;
};
const formSel = opt('--form', 'form.kitwp-form, form');
const widths = opt('--widths', '1280,390').split(',').map((w) => parseInt(w, 10)).filter((w) => w > 0);
const target = args[0];
if (!target) {
  console.log('FAIL form-layout: usage: node form-layout.mjs <page url or file> [--form <selector>] [--widths 1280,390]');
  process.exit(2);
}
const url = /^https?:|^file:/.test(target) ? target : pathToFileURL(path.resolve(target)).href;
if (url.startsWith('file:') && !fs.existsSync(new URL(url))) {
  console.log(`FAIL form-layout: ${target} not found`);
  process.exit(2);
}

const browser = await (await chromium()).launch({ executablePath: process.env.CHROME_PATH || undefined });
const fails = [];
const seen = [];
try {
  for (const width of widths) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    await page.goto(url, { waitUntil: 'load' });
    const r = await page.evaluate((sel) => {
      const form = document.querySelector(sel);
      if (!form) return { missing: true };
      const box = (el) => el.getBoundingClientRect();
      const fields = [];
      form.querySelectorAll('input, select, textarea').forEach((c) => {
        const cs = getComputedStyle(c);
        if (c.type === 'hidden' || c.closest('.hp') || cs.display === 'none' || cs.visibility === 'hidden') return;
        const label = (c.id && form.querySelector(`label[for="${CSS.escape(c.id)}"]`)) || c.closest('label');
        const b = box(c);
        fields.push({
          name: c.name || c.id || c.tagName.toLowerCase(),
          area: c.tagName === 'TEXTAREA',
          top: Math.round(b.top), left: Math.round(b.left), width: Math.round(b.width),
          font: parseFloat(cs.fontSize),
          labelAbove: label && label !== c.closest('label') ? box(label).bottom <= b.top + 1 : !!label,
          hasLabel: !!label,
        });
      });
      return { width: Math.round(box(form).width), fields };
    }, formSel);
    if (r.missing) {
      fails.push(`${width}: no form matches "${formSel}"`);
      await page.close();
      continue;
    }
    if (!r.fields.length) fails.push(`${width}: the form has no visible fields`);
    for (const f of r.fields) {
      if (!f.hasLabel) fails.push(`${width}: ${f.name} has no label`);
      else if (!f.labelAbove) fails.push(`${width}: ${f.name}'s label is not above it`);
      if (f.font < 16) fails.push(`${width}: ${f.name} is ${f.font}px (16px or more)`);
      if (f.area && f.width < r.width * 0.95) fails.push(`${width}: ${f.name} is not full width (${f.width} of ${r.width}px)`);
    }
    const rows = {};
    r.fields.filter((f) => !f.area).forEach((f) => (rows[f.top] = (rows[f.top] || 0) + 1));
    const most = Math.max(0, ...Object.values(rows));
    const want = width >= 640 ? 2 : 1;
    const short = r.fields.filter((f) => !f.area).length;
    if (short >= 2 && most !== want) fails.push(`${width}: ${most} short field(s) per row (want ${want})`);
    // Focus ring and error state on the first field.
    const first = await page.$(`${formSel.split(',')[0]} input:not([type=hidden]):not([tabindex="-1"]), ${formSel.split(',')[0]} select`);
    if (first) {
      await first.focus();
      const ring = await first.evaluate((el) => {
        const cs = getComputedStyle(el);
        return (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0) || cs.boxShadow !== 'none';
      });
      if (!ring) fails.push(`${width}: no visible focus ring on ${await first.getAttribute('name')}`);
      const changed = await first.evaluate((el) => {
        el.blur();
        const before = getComputedStyle(el).borderColor;
        const note = document.createElement('span');
        note.className = 'form-note';
        note.setAttribute('role', 'alert');
        note.textContent = 'Please fill out this field.';
        el.after(note);
        const after = getComputedStyle(el).borderColor;
        note.remove();
        return before !== after;
      });
      if (!changed) fails.push(`${width}: no error state (a field with a .form-note keeps its border)`);
    }
    seen.push(`${width}px ${r.fields.length} fields, ${most} per row`);
    await page.close();
  }
} finally {
  await browser.close();
}
if (fails.length) {
  console.log(`FAIL form-layout: ${fails.length} problem(s) on ${target}`);
  fails.slice(0, 20).forEach((f) => console.log('  ' + f));
  process.exit(1);
}
console.log(`OK form-layout: ${target}: ${seen.join('; ')}; labels above, message full width, 16px+, focus and error states`);
