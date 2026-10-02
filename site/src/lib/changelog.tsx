import fs from "node:fs";
import path from "node:path";
import type { ReactNode } from "react";

// Patch notes come from the repository's CHANGELOG.md when the site is built, so they are never out of date.

export type Release = {
  version: string;
  date: string;
  sections: { title: string; items: string[] }[];
};

export function getReleases(limit = 3): Release[] {
  const file = path.join(process.cwd(), "..", "CHANGELOG.md");
  const text = fs.readFileSync(file, "utf8").replace(/\r\n/g, "\n");
  const releases: Release[] = [];

  for (const block of text.split(/^## /m).slice(1)) {
    const [head, ...lines] = block.split("\n");
    const m = head.match(/^\[([^\]]+)\]\s*-\s*(\d{4}-\d{2}-\d{2})/);
    if (!m) continue; // "Unreleased" and anything without a date stays off the site
    const release: Release = { version: m[1], date: m[2], sections: [] };
    let section: Release["sections"][number] | null = null;

    for (const line of lines) {
      const h = line.match(/^### (.+)/);
      if (h) {
        section = { title: h[1].trim(), items: [] };
        release.sections.push(section);
        continue;
      }
      if (line.startsWith("- ")) {
        if (!section) {
          section = { title: "Changes", items: [] };
          release.sections.push(section);
        }
        section.items.push(line.slice(2).trim());
      } else if (/^\s{2,}\S/.test(line) && section?.items.length) {
        section.items[section.items.length - 1] += " " + line.trim();
      }
    }
    releases.push(release);
    if (releases.length >= limit) break;
  }
  return releases;
}

export function formatDate(iso: string): string {
  const [y, mo, d] = iso.split("-").map(Number);
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${d} ${months[mo - 1]} ${y}`;
}

// Inline Markdown used in the changelog: `code`, **bold** and [links](url). Everything else is plain text.
export function Inline({ text }: { text: string }) {
  const out: ReactNode[] = [];
  const re = /`([^`]+)`|\*\*([^*]+)\*\*|\[([^\]]+)\]\(([^)]+)\)/g;
  let last = 0;
  let k = 0;
  for (let m = re.exec(text); m; m = re.exec(text)) {
    if (m.index > last) out.push(text.slice(last, m.index));
    if (m[1]) out.push(<code key={k++} className="text-[0.92em] text-foreground">{m[1]}</code>);
    else if (m[2]) out.push(<strong key={k++}>{m[2]}</strong>);
    else
      out.push(
        <a key={k++} href={m[4]} className="underline hover:text-brand">
          {m[3]}
        </a>,
      );
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push(text.slice(last));
  return <>{out}</>;
}
