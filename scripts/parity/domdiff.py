#!/usr/bin/env python3
"""DOM diff for 1:1 checks: compares element signatures of chosen regions in two HTML files.

    python3 domdiff.py static.html wordpress.html [region ...]
    python3 domdiff.py static.html static.html            self-test: every region SAME

Regions come from domdiff.config.json next to this file (tag, class or id, optionally the parent's class), for
example {"header": {"tag": "header"}, "main": {"tag": "main"}, "footer": {"tag": "footer"}}. Without a region
argument every region except "main" is compared. A signature is the tag, sorted classes, the attributes that
matter (ids, aria, sizes, alt, loading, fetchpriority, href path, image file name) and the element's own text.
Ignored on purpose: style and srcset (compare those separately), CF7's hidden inputs (_wpcf7*, _wpnonce) and the
empty captcha boxes WordPress adds. WordPress uploads named <name>-<key>-<width>.webp match the static
/_img/<path>-<width>.webp files by width. Exit code 1 when any region differs.
"""
import difflib
import json
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = {
    'regions': {'header': {'tag': 'header'}, 'main': {'tag': 'main'}, 'footer': {'tag': 'footer'}},
    'local_hosts': ['{{DOMAIN}}', 'www.{{DOMAIN}}', '{{LOCAL_HOST}}'],
    'size_key': 'kitk',
}
if os.path.exists(os.path.join(HERE, 'domdiff.config.json')):
    CFG.update(json.load(open(os.path.join(HERE, 'domdiff.config.json'), encoding='utf-8')))

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}
ATTRS = ['id', 'type', 'role', 'aria-label', 'aria-expanded', 'aria-controls', 'aria-hidden', 'aria-modal',
         'aria-labelledby', 'aria-current', 'aria-live', 'data-open', 'width', 'height', 'alt', 'rel', 'target',
         'hidden', 'for', 'name', 'placeholder', 'viewbox', 'd', 'loading', 'fetchpriority', 'decoding',
         'data-nimg', 'sizes', 'required', 'disabled', 'selected', 'tabindex', 'autocomplete', 'open']
SKIP_BOXES = ('cf-turnstile', 'wpcf7-recaptcha')


def wp_hidden(tag, a):
    return tag == 'input' and a.get('type') == 'hidden' and (a.get('name') or '').startswith(('_wpcf7', '_wpnonce'))


class Node:
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent, self.children, self.text = tag, dict(attrs), parent, [], ''


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node('#root', [], None)
        self.cur = self.root
        self.skip = 0
        self.drop_div = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if wp_hidden(tag, a):
            return
        if tag == 'div' and any(b in (a.get('class') or '').split() for b in SKIP_BOXES):
            self.drop_div += 1
            return
        if tag in ('script', 'style', 'template'):
            self.skip += 1
            return
        if self.skip:
            return
        n = Node(tag, attrs, self.cur)
        self.cur.children.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        if wp_hidden(tag, dict(attrs)) or self.skip:
            return
        self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        if tag == 'div' and self.drop_div:
            self.drop_div -= 1
            return
        if tag in ('script', 'style', 'template'):
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        if not self.skip:
            self.cur.text += data


def walk(n):
    yield n
    for c in n.children:
        yield from walk(c)


def cls(n):
    return (n.attrs.get('class') or '').split()


def sig(n):
    s = n.tag
    c = sorted(cls(n))
    if c:
        s += '.' + '.'.join(c)
    for a in ATTRS:
        if a in n.attrs:
            v = n.attrs[a] if n.attrs[a] is not None else ''
            s += f'[{a}:{v}]'
    if 'href' in n.attrs:
        href = n.attrs['href'] or ''
        u = urlparse(href)
        if u.scheme in ('tel', 'mailto'):
            s += '[href:' + href + ']'
        else:
            local = u.netloc in ('', *CFG['local_hosts'])
            s += '[href:' + ((u.path or '') if local else u.scheme + '://' + u.netloc + u.path)
            s += ('#' + u.fragment if u.fragment else '') + (('?' + u.query) if u.query and not local else '') + ']'
    if 'src' in n.attrs:
        f = (n.attrs['src'] or '').split('/')[-1].split('?')[0]
        f = re.sub(r'\.(?:jpe?g|png|webp)-(\d+)\.webp$', '-' + CFG['size_key'] + r'-\1.webp', f)  # static /_img name
        s += '[src:' + f + ']'
    t = re.sub(r'\s+', ' ', n.text).strip()
    if t:
        s += f'"{t}"'
    return s


def matcher(spec):
    def ok(n):
        if 'tag' in spec and n.tag != spec['tag']:
            return False
        if 'class' in spec and spec['class'] not in cls(n):
            return False
        if 'id' in spec and n.attrs.get('id') != spec['id']:
            return False
        if 'parent_class' in spec and (n.parent is None or spec['parent_class'] not in cls(n.parent)):
            return False
        return True
    return ok


def region(html, spec):
    p = P()
    p.feed(html)
    pred = matcher(spec)
    for n in walk(p.root):
        if n is not p.root and pred(n):
            return [sig(x) for x in walk(n)]
    return []


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    a = open(sys.argv[1], encoding='utf-8').read()
    b = open(sys.argv[2], encoding='utf-8').read()
    names = sys.argv[3:] or [k for k in CFG['regions'] if k != 'main']
    bad = 0
    for name in names:
        x, y = region(a, CFG['regions'][name]), region(b, CFG['regions'][name])
        if not x and not y:
            print(f'NONE  {name}: not found in either file')
            continue
        if x == y:
            print(f'SAME  {name}: {len(x)} elements')
            continue
        bad += 1
        print(f'DIFF  {name}: static {len(x)}, wordpress {len(y)}')
        for line in list(difflib.unified_diff(x, y, 'static', 'wordpress', n=0, lineterm=''))[2:40]:
            print('   ', line[:220])
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
