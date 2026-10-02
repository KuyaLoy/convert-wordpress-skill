#!/usr/bin/env python3
"""
Exports the static site's one-off pages (home, about, hubs, contact, thank you, legal, posts) into
_setup/seed/pages.json for the seeder. Text comes from the static build's HTML, so it is exact.

    python3 export-pages.py <static build dir> <out pages.json>

Each page is a list of Page Sections rows ({"acf_fc_layout": "<layout>", ...field values}) read from the top-level
sections of <main>. Values the seeder resolves: "media:/static/path.jpg" (attachment by _kitk_source) and
"page:<slug>" (page ID). Overrides equal to the Theme Settings default are left empty, so editing the default
reaches every page (see clean_defaults()). Needs BeautifulSoup and lxml (pip install beautifulsoup4 lxml).

The helpers are generic; write one function per page in the PAGES block.
"""
import json
import re
import sys

from bs4 import BeautifulSoup, Comment

if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(2)
BUILD, OUT = sys.argv[1], sys.argv[2]

# Site values that become tokens in copy (the theme fills them in when it renders). SITE MAPPING.
TOKENS = {
    # '020 7946 0000': '{phone}', 'tel:02079460000': 'tel:{tel}', 'hello@example.com': '{email}',
}


def load(path):
    """Top-level sections of <main>, plus the page's title, description and noindex."""
    s = open(f'{BUILD}/{path}', encoding='utf-8').read()
    soup = BeautifulSoup(s, 'lxml')
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()
    main = soup.find('main')
    secs = [c for c in main.find_all(recursive=False) if c.name != 'script']
    desc = soup.find('meta', attrs={'name': 'description'})
    robots = soup.find('meta', attrs={'name': 'robots'})
    return secs, {'title': soup.find('title').get_text(), 'description': desc['content'] if desc else '',
                  'noindex': bool(robots and 'noindex' in robots.get('content', ''))}


def T(el):
    """Visible text, whitespace collapsed."""
    return re.sub(r'\s+', ' ', el.get_text()).strip() if el else ''


def own(el, icon_class='material-icons'):
    """Text of the element without its icon span."""
    parts = []
    for c in el.children:
        if getattr(c, 'name', None) == 'span' and icon_class in (c.get('class') or []):
            continue
        parts.append(c.get_text() if hasattr(c, 'get_text') else str(c))
    return re.sub(r'\s+', ' ', ''.join(parts)).strip()


def inner(el):
    """Inner HTML (bold, links) for fields printed with kitwp_inline()."""
    return el.decode_contents(formatter='minimal').strip() if el else ''


def icon(el, icon_class='material-icons'):
    i = el.find('span', class_=icon_class) if el else None
    return i.get_text() if i else ''


def media(img, pattern=r'^/_img(/.+?)-\d+\.webp$'):
    """The static source path of an <img> (its srcset/src points at a WebP width), as a seeder placeholder."""
    m = re.match(pattern, img['src'])
    return 'media:' + (m.group(1) if m else img['src'])


def h_em(h):
    """Heading text and its <em> part (many static heroes print 'Heading <em>promise</em>')."""
    em = h.find('em')
    head = own(h) if not em else re.sub(r'\s+', ' ', ''.join(c.get_text() if hasattr(c, 'get_text') else str(c) for c in h.children if c is not em)).strip()
    return head, (em.get_text().strip() if em else '')


def tokens(html):
    for value, token in TOKENS.items():
        html = html.replace(value, token)
    return html


def faqs(wrap):
    return [{'question': own(d.find('summary')), 'answer': inner(d.find(class_='a') or d)} for d in wrap.find_all('details')]


def clean_defaults(rows, defaults):
    """Empty every override equal to the Theme Settings default. defaults: {layout: {field: default value}}."""
    for r in rows:
        for k, v in defaults.get(r['acf_fc_layout'], {}).items():
            if r.get(k) == v:
                r[k] = ''
    return rows


pages = []


def page(slug, path, title, build, kind='page', crumbs=None, **extra):
    secs, seo = load(path)
    pages.append({'slug': slug, 'title': title, 'kind': kind, 'seo': seo, 'crumbs': crumbs or {}, 'sections': build(secs), **extra})


# ---------------------------------------------------------------- PAGES (SITE MAPPING)
# Example: an About page with a page head and a final CTA.
# def about(s):
#     h1, em = h_em(s[0].find('h1'))
#     return [{'acf_fc_layout': 'page_head', 'eyebrow': T(s[0].find(class_='eyebrow')), 'h1': h1, 'em': em, 'sub': inner(s[0].find('p'))},
#             {'acf_fc_layout': 'final_cta', 'heading': T(s[-1].find('h2')), 'text': tokens(T(s[-1].find('p')))}]
# page('about', 'about/index.html', 'About', about)
# page('home', 'index.html', 'Home', home, front=True)

json.dump(pages, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('pages', len(pages), [p['slug'] for p in pages])
