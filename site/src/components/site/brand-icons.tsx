// Pixel brand icons for the social links, from HackerNoon's Pixel Icon Library
// (https://github.com/hackernoon/pixel-icon-library), copied here so the site does not install all 2,000 icons.
/*
 * MIT License
 *
 * Copyright (c) 2023 HackerNoon
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

const ICONS: Record<string, React.ReactNode> = {
  github: (
    <><polygon points="23 9 23 15 22 15 22 17 21 17 21 19 20 19 20 20 19 20 19 21 18 21 18 22 16 22 16 23 15 23 15 18 14 18 14 17 15 17 15 16 17 16 17 15 18 15 18 14 19 14 19 9 18 9 18 6 16 6 16 7 15 7 15 8 14 8 14 7 10 7 10 8 9 8 9 7 8 7 8 6 6 6 6 9 5 9 5 14 6 14 6 15 7 15 7 16 9 16 9 18 7 18 7 17 6 17 6 16 4 16 4 17 5 17 5 19 6 19 6 20 9 20 9 23 8 23 8 22 6 22 6 21 5 21 5 20 4 20 4 19 3 19 3 17 2 17 2 15 1 15 1 9 2 9 2 7 3 7 3 5 4 5 4 4 5 4 5 3 7 3 7 2 9 2 9 1 15 1 15 2 17 2 17 3 19 3 19 4 20 4 20 5 21 5 21 7 22 7 22 9 23 9"/></>
  ),
  linkedin: (
    <><path d="m22,2v-1H2v1h-1v20h1v1h20v-1h1V2h-1Zm-9,10v8h-3v-11h3v1h1v-1h4v1h1v10h-3v-8h-3Zm-9-4v-3h3v3h-3Zm3,1v11h-3v-11h3Z"/></>
  ),
  facebook: (
    <><polygon points="23 9 23 15 22 15 22 17 21 17 21 19 20 19 20 20 19 20 19 21 17 21 17 22 15 22 15 23 14 23 14 15 16 15 16 14 17 14 17 12 14 12 14 9 15 9 15 8 17 8 17 5 13 5 13 6 11 6 11 8 10 8 10 12 7 12 7 15 10 15 10 23 9 23 9 22 7 22 7 21 5 21 5 20 4 20 4 19 3 19 3 17 2 17 2 15 1 15 1 9 2 9 2 7 3 7 3 5 4 5 4 4 5 4 5 3 7 3 7 2 9 2 9 1 15 1 15 2 17 2 17 3 19 3 19 4 20 4 20 5 21 5 21 7 22 7 22 9 23 9"/></>
  ),
  instagram: (
    <><path d="m17,9v-1h-1v-1h-1v-1h-6v1h-1v1h-1v1h-1v6h1v1h1v1h1v1h6v-1h1v-1h1v-1h1v-6h-1Zm-1,5h-1v1h-1v1h-4v-1h-1v-1h-1v-4h1v-1h1v-1h4v1h1v1h1v4Z"/><path d="m22,5v-2h-1v-1h-2v-1H5v1h-2v1h-1v2h-1v14h1v2h1v1h2v1h14v-1h2v-1h1v-2h1V5h-1Zm-1,14h-1v1h-1v1H5v-1h-1v-1h-1V5h1v-1h1v-1h14v1h1v1h1v14Z"/><rect x="17" y="5" width="2" height="2"/></>
  ),
  threads: (
    <><path d="M21 7V5H20V4H19V3H18V2H16V1H8V2H6V3H5V4H4V5H3V8H2V16H3V19H4V20H5V21H6V22H8V23H16V22H18V21H19V20H20V19H21V12H20V11H19V10H16V8H15V7H14V6H10V7H9V8H8V9H11V8H13V9H14V10H10V11H9V12H8V16H9V17H10V18H14V17H15V16H16V12H18V13H19V18H18V19H17V20H15V21H9V20H7V19H6V18H5V15H4V9H5V6H6V5H7V4H9V3H15V4H17V5H18V6H19V8H22V7H21ZM13 15V16H11V15H10V13H11V12H13V13H14V15H13Z"/></>
  ),
  x: (
    <><path d="m15.5,10v-1h1v-1h1v-1h1v-1h1v-1h1v-1h1v-1h1v-1h-3v1h-1v1h-1v1h-1v1h-1v1h-1v1h-2v-1h-1v-1h-1v-2h-1v-1h-1v-1H1.5v1h1v1h1v1h1v2h1v1h1v2h1v1h1v2h1v1h-1v1h-1v1h-1v1h-1v1h-1v1h-1v1h-1v1h-1v1h3v-1h1v-1h1v-1h1v-1h1v-1h1v-1h2v1h1v1h1v2h1v1h1v1h7v-1h-1v-1h-1v-1h-1v-2h-1v-1h-1v-2h-1v-1h-1v-2h-1v-1h1Zm0,4v1h1v2h1v1h1v2h-3v-2h-1v-1h-1v-1h-1v-2h-1v-1h-1v-1h-1v-2h-1v-1h-1v-2h-1v-1h-1v-2h3v1h1v2h1v1h1v2h1v1h1v1h1v2h1Z"/></>
  ),
};

export function BrandIcon({ name, className = "size-6" }: { name: string; className?: string }) {
  const shape = ICONS[name];
  if (!shape) return null;
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false" className={className}>
      {shape}
    </svg>
  );
}
