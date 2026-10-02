// The hero picture: your site on the left, its WordPress copy on the right, the same 1:1.
// Original pixel art, drawn on a 63 x 31 grid.

type Px = { x: number; y: number; w?: number; h?: number; c: string; cls?: string };

const C = {
  frame: "#ffffff",
  fill: "#161616",
  bar: "#2b2b2b",
  light: "#bdbdbd",
  mid: "#5a5a5a",
  dim: "#3a3a3a",
  text: "#6a6a6a",
  card: "#262626",
  brand: "#f5412c",
  ink: "#0e0e0e",
};

function windowPixels(x0: number, editable: boolean): Px[] {
  const p: Px[] = [
    // frame with notched corners
    { x: x0 + 1, y: 0, w: 24, h: 1, c: C.frame },
    { x: x0 + 1, y: 29, w: 24, h: 1, c: C.frame },
    { x: x0, y: 1, w: 1, h: 28, c: C.frame },
    { x: x0 + 25, y: 1, w: 1, h: 28, c: C.frame },
    { x: x0 + 1, y: 1, w: 24, h: 28, c: C.fill },
    // title bar and its three lights
    { x: x0 + 1, y: 1, w: 24, h: 3, c: C.bar },
    { x: x0 + 3, y: 2, c: C.brand },
    { x: x0 + 5, y: 2, c: C.light },
    { x: x0 + 7, y: 2, c: C.mid },
    // header: logo and three links
    { x: x0 + 3, y: 6, w: 5, h: 2, c: C.light },
    { x: x0 + 12, y: 6, w: 3, h: 1, c: C.mid },
    { x: x0 + 16, y: 6, w: 3, h: 1, c: C.mid },
    { x: x0 + 20, y: 6, w: 3, h: 1, c: C.mid },
    // hero block with a headline and a button
    { x: x0 + 3, y: 10, w: 20, h: 7, c: C.brand },
    { x: x0 + 5, y: 12, w: 11, h: 1, c: C.frame },
    { x: x0 + 5, y: 14, w: 6, h: 2, c: C.ink },
    // body text
    { x: x0 + 3, y: 19, w: 20, h: 1, c: C.text },
    { x: x0 + 3, y: 21, w: 15, h: 1, c: C.text },
    // two cards
    { x: x0 + 3, y: 24, w: 9, h: 4, c: C.card },
    { x: x0 + 14, y: 24, w: 9, h: 4, c: C.card },
    { x: x0 + 4, y: 25, w: 5, h: 1, c: C.mid },
    { x: x0 + 15, y: 25, w: 5, h: 1, c: C.mid },
    { x: x0 + 4, y: 26, w: 3, h: 1, c: C.dim },
    { x: x0 + 15, y: 26, w: 3, h: 1, c: C.dim },
  ];
  if (editable) {
    // a text cursor in the headline: the words are editable now
    p.push({ x: x0 + 17, y: 11, w: 1, h: 3, c: C.frame, cls: "blink" });
    // dotted outlines: each card is an editable field
    for (const cx of [x0 + 2, x0 + 13]) {
      for (let i = 0; i <= 10; i += 2) {
        p.push({ x: cx + i, y: 23, c: C.frame });
        p.push({ x: cx + i, y: 28, c: C.frame });
      }
      for (let j = 25; j <= 27; j += 2) {
        p.push({ x: cx, y: j, c: C.frame });
        p.push({ x: cx + 10, y: j, c: C.frame });
      }
    }
  }
  return p;
}

// "1:1" in a 3 x 5 pixel font, and the copy arrow.
const ONE = [".X.", "XX.", ".X.", ".X.", "XXX"];
function glyph(rows: string[], x0: number, y0: number, c: string): Px[] {
  const out: Px[] = [];
  rows.forEach((row, y) => [...row].forEach((ch, x) => ch === "X" && out.push({ x: x0 + x, y: y0 + y, c })));
  return out;
}
const middle: Px[] = [
  ...glyph(ONE, 27, 5, C.frame),
  { x: 31, y: 6, c: C.frame },
  { x: 31, y: 8, c: C.frame },
  ...glyph(ONE, 33, 5, C.frame),
  { x: 27, y: 15, c: C.brand, cls: "march" },
  { x: 29, y: 15, c: C.brand, cls: "march march-2" },
  { x: 31, y: 15, c: C.brand, cls: "march march-3" },
  { x: 33, y: 13, w: 1, h: 5, c: C.brand },
  { x: 34, y: 14, w: 1, h: 3, c: C.brand },
  { x: 35, y: 15, c: C.brand },
];

const PIXELS: Px[] = [...windowPixels(0, false), ...middle, ...windowPixels(37, true)];

export function PixelScene({ labels }: { labels: string[] }) {
  return (
    <figure className="w-full">
      <svg
        viewBox="0 0 63 30"
        className="pixel-art h-auto w-full"
        role="img"
        aria-label="Your site and its WordPress copy side by side, the same layout, 1:1"
      >
        {PIXELS.map((p, i) => (
          <rect key={i} x={p.x} y={p.y} width={p.w ?? 1} height={p.h ?? 1} fill={p.c} className={p.cls} />
        ))}
      </svg>
      <figcaption className="mt-4 grid grid-cols-[26fr_11fr_26fr] text-center font-pixel text-base text-muted-foreground">
        <span>{labels[0]}</span>
        <span aria-hidden="true" />
        <span>{labels[1]}</span>
      </figcaption>
    </figure>
  );
}
