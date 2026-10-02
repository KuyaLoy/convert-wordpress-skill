#!/usr/bin/env python3
"""Study the code the designer handed over before planning the conversion.

    python3 analyze-source.py <source folder> [--json report.json]

Read-only. Reports, with the evidence it found:
- the stack: plain HTML, server-rendered PHP, Next.js (static export or server), React with Vite or Create React App, Gatsby, Astro,
  Vue/Nuxt, Svelte/SvelteKit, Remix, or unknown; the package manager and the build scripts;
- the built output that is already there (out/, dist/, build/, .next/) and whether it holds rendered HTML;
- Tailwind (version, config, v4 @import) and so the starter theme: _tw for Tailwind, Barebones for plain CSS;
- routes (Next app/ and pages/ routers, .html files, React Router paths), dynamic routes to expand;
- content sources (content/ and data/ modules, Markdown/MDX, remote fetches), forms and their endpoints,
  tracking ids (GTM, GA4, Ads, Meta), fonts (Google Fonts links, next/font), icon sets, images (next/image),
  and redirect sources (redirect-map.csv, next.config redirects, vercel.json, _redirects, .htaccess).
Then the golden-master method for that stack (see references/source-types.md).

Options: --json <file> (everything found), --site-draft <file> (a first site.json: starter, GTM, html attributes,
fonts; never overwrites).
"""
import json
import os
import re
import sys

SKIP = {'node_modules', '.git', '.next', '.cache', '.vercel', '.turbo', 'coverage'}
CODE = ('.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.vue', '.svelte', '.astro', '.mdx', '.md', '.html', '.css', '.scss', '.php', '.json')


def walk(root, skip_built=False):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP and not (skip_built and x in ('out', 'dist', 'build'))]
        for f in files:
            yield os.path.join(d, f)


def read(p, limit=400_000):
    try:
        with open(p, encoding='utf-8', errors='replace') as fh:
            return fh.read(limit)
    except OSError:
        return ''


def rel(root, p):
    return os.path.relpath(p, root).replace('\\', '/')


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    root = os.path.abspath(sys.argv[1])
    r = {'root': root, 'stack': 'unknown', 'evidence': [], 'notes': []}

    # Package files (the app may sit in a subfolder, as website/site/).
    pkgs = [p for p in walk(root) if os.path.basename(p) == 'package.json']
    app = None
    deps = {}
    for p in sorted(pkgs, key=len):
        data = json.loads(read(p) or '{}')
        d = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
        if any(k in d for k in ('next', 'react', 'vue', 'nuxt', 'astro', 'gatsby', 'svelte', '@sveltejs/kit', '@remix-run/react', 'vite')):
            app, deps = os.path.dirname(p), d
            r['package_json'] = rel(root, p)
            r['scripts'] = data.get('scripts', {})
            break
    if app is None and pkgs:
        # No framework (a plain PHP or HTML site with a CSS build): keep the root package's scripts and dependencies.
        p = sorted(pkgs, key=len)[0]
        data = json.loads(read(p) or '{}')
        deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
        r['package_json'] = rel(root, p)
        r['scripts'] = data.get('scripts', {})
        app = os.path.dirname(p)
    base = app or root
    for lock, pm in (('pnpm-lock.yaml', 'pnpm'), ('yarn.lock', 'yarn'), ('package-lock.json', 'npm'), ('bun.lockb', 'bun')):
        if os.path.exists(os.path.join(base, lock)):
            r['package_manager'] = pm
            break

    def has(name):
        return name in deps

    if has('next'):
        r['stack'] = 'nextjs'
        cfg = ''
        for n in ('next.config.mjs', 'next.config.js', 'next.config.ts'):
            if os.path.exists(os.path.join(base, n)):
                cfg = read(os.path.join(base, n))
                r['next_config'] = n
                break
        nums = lambda m: [int(x) for x in re.findall(r'\d+', m[0])] if m else []
        dev = nums(re.findall(r'deviceSizes\s*:\s*\[([^\]]*)\]', cfg)) or [640, 750, 828, 1080, 1200, 1920, 2048, 3840]
        img = nums(re.findall(r'imageSizes\s*:\s*\[([^\]]*)\]', cfg)) or [16, 32, 48, 64, 96, 128, 256, 384]
        scripts = ' '.join(f'{k}={v}' for k, v in json.loads(read(os.path.join(base, 'package.json')) or '{}').get('scripts', {}).items())
        r['next'] = {
            'version': deps.get('next'),
            'static_export': bool(re.search(r"output\s*[:=]\s*['\"]export['\"]", cfg)),
            'conditional_export': bool(re.search(r'process\.env\.\w+[^\n]*\n?[^\n]*output\s*[:=]', cfg)) or 'build:static' in scripts or 'next export' in scripts,
            'trailing_slash': bool(re.search(r'trailingSlash\s*:\s*true', cfg)),
            'image_loader': bool(re.search(r'loader(File)?\s*:', cfg)),
            'images_unoptimized': bool(re.search(r'unoptimized\s*:\s*true', cfg)),
            'device_sizes': dev,
            'image_sizes': img,
            'srcset_widths': sorted(set(dev + img)),
            'first_device_size': dev[0],
            'redirects_in_config': 'redirects' in cfg,
        }
    elif has('gatsby'):
        r['stack'] = 'gatsby'
    elif has('astro'):
        r['stack'] = 'astro'
    elif has('nuxt'):
        r['stack'] = 'nuxt'
    elif has('@sveltejs/kit'):
        r['stack'] = 'sveltekit'
    elif has('@remix-run/react'):
        r['stack'] = 'remix'
    elif has('vue'):
        r['stack'] = 'vue'
    elif has('react') and has('react-scripts'):
        r['stack'] = 'react-cra'
    elif has('react'):
        r['stack'] = 'react-vite' if has('vite') else 'react'
    elif os.path.exists(os.path.join(base, 'index.php')):
        r['stack'] = 'php'
    elif any(p.endswith('.html') for p in walk(root, skip_built=True)):
        r['stack'] = 'static-html'

    # Built output already present.
    built = {}
    for d in ('out', 'dist', 'build', '.next', 'public'):
        p = os.path.join(base, d)
        if os.path.isdir(p):
            htmls = [x for x in walk(p) if x.endswith('.html')]
            rendered = 0
            for h in htmls[:20]:
                t = read(h, 200_000)
                body = t.split('<body', 1)[-1]
                if len(re.sub(r'<script[\s\S]*?</script>|<[^>]+>|\s+', '', body)) > 200:
                    rendered += 1
            built[d] = {'html_files': len(htmls), 'sampled_with_text': rendered, 'sampled': min(20, len(htmls))}
    r['built_output'] = built
    # The <html> attributes (lang, dir) of the first rendered page: WordPress must print the same.
    first = None
    if built or r['stack'] == 'static-html':
        for d in ('out', 'dist', 'build', 'public', ''):
            hs = [x for x in walk(os.path.join(base, d) if d else base) if x.endswith('.html')]
            if hs:  # the home page first: index.html nearest the top
                first = sorted(hs, key=lambda x: (os.path.basename(x) != 'index.html', x.count(os.sep), x))[0]
                break
    if not first and r['stack'] == 'php':
        cands = [x for x in walk(base, skip_built=True) if x.endswith('.php') and re.search(r'<html\b[^>]*\blang=', read(x, 600_000))]
        first = sorted(cands, key=lambda x: (0 if re.search(r'header|index|layout|head', os.path.basename(x)) else 1, len(x)))[0] if cands else None
    if first:
        m = re.search(r'<html\b([^>]*\blang=[^>]*)>', read(first, 600_000), re.I) or re.search(r'<html\b([^>]*)>', read(first, 50_000), re.I)
        attrs = ' '.join(re.findall(r'\b(?:lang|dir)=["\'][^"\']*["\']', m.group(1))) if m else ''
        r['html_attributes'] = attrs
        if re.search(r'dir=["\']rtl', attrs):
            r['notes'].append('Right-to-left site: keep dir="rtl" (site.json html_attributes) and check every layout in RTL.')
    for z in (x for x in os.listdir(root) if x.lower().endswith('.zip')):
        r.setdefault('zips', []).append(z)

    # Tailwind.
    tw = {'dependency': deps.get('tailwindcss') or deps.get('@tailwindcss/postcss') or deps.get('@tailwindcss/vite')}
    tw['config'] = [rel(root, p) for p in walk(base) if re.search(r'tailwind\.config\.(js|cjs|mjs|ts)$', p)]
    css_hits = []
    for p in walk(base, skip_built=True):
        if p.endswith(('.css', '.scss')):
            t = read(p, 100_000)
            if re.search(r'@tailwind\s+(base|components|utilities)|@import\s+["\']tailwindcss', t):
                css_hits.append(rel(root, p))
    tw['css_entry'] = css_hits
    r['tailwind'] = tw if (tw['dependency'] or tw['config'] or css_hits) else None
    r['starter_theme'] = '_tw (Tailwind)' if r['tailwind'] else 'Barebones (plain CSS)'

    # Routes.
    routes = set()
    for p in walk(base, skip_built=True):
        rp = rel(base, p)
        m = re.match(r'(?:src/)?app/(.*?)/?page\.(tsx|jsx|ts|js|mdx)$', rp)
        if m:
            seg = '/'.join(s for s in m.group(1).split('/') if not (s.startswith('(') and s.endswith(')')))
            routes.add('/' + (seg + '/' if seg else ''))
        m = re.match(r'(?:src/)?pages/(.*)\.(tsx|jsx|ts|js|mdx)$', rp)
        if m and not re.search(r'(^|/)(_app|_document|_error|api/)', m.group(1)):
            seg = re.sub(r'(^|/)index$', '', m.group(1))
            routes.add('/' + (seg + '/' if seg else ''))
        if r['stack'] == 'php' and rp.endswith('.php') and '/' not in rp:
            ht = read(os.path.join(base, '.htaccess'), 100_000)
            slash = '' if re.search(r'\$1\.php', ht) else '/'
            routes.add('/' + ('' if rp == 'index.php' else rp[:-4] + slash))
        if r['stack'] == 'static-html' and rp.endswith('.html'):
            routes.add('/' + re.sub(r'(^|/)index\.html$', r'\1', rp))
        # File-based routers: Astro, Gatsby (src/pages), Nuxt (pages/*.vue), SvelteKit (src/routes/**/+page.svelte).
        m = (re.match(r'src/pages/(.*)\.(astro|md|mdx|html)$', rp) if r['stack'] in ('astro', 'gatsby') else None) \
            or (re.match(r'(?:src/)?pages/(.*)\.vue$', rp) if r['stack'] in ('nuxt', 'vue') else None)
        if m and not re.search(r'(^|/)_', m.group(1)):
            seg = re.sub(r'(^|/)index$', '', m.group(1))
            routes.add('/' + (seg + '/' if seg else ''))
        m = re.match(r'src/routes/(.*?)/?\+page\.svelte$', rp) if r['stack'] == 'sveltekit' else None
        if m:
            seg = '/'.join(x for x in m.group(1).split('/') if x and not (x.startswith('(') and x.endswith(')')))
            routes.add('/' + (seg + '/' if seg else ''))
        if p.endswith(CODE[:6]):
            for m2 in re.finditer(r'<Route[^>]*\bpath=["\']([^"\']+)|\bpath:\s*["\'](/[^"\']*)["\']', read(p, 200_000)):
                routes.add(m2.group(1) or m2.group(2))
    r['routes'] = sorted(routes)
    r['dynamic_routes'] = [x for x in r['routes'] if '[' in x or ':' in x]

    # Content, forms, tracking, fonts, icons, images, redirects.
    content, forms, tracking, fonts, icons, redirects, mailers, libs = set(), set(), set(), set(), set(), set(), set(), set()
    private = sorted(rel(root, p) for p in walk(base, skip_built=True)
                     if not p.endswith(('.example', '.sample', '.dist')) and re.search(r'(^|[\\/])(\.env(\..*)?|env\.php|secrets?\.\w+|wp-config\.php|leads?\.(json|csv)|'
                                  r'submissions?\.(json|csv))$', p, re.I))
    next_image = 0
    for p in walk(base, skip_built=True):
        rp = rel(root, p)
        if re.search(r'(^|/)(content|data)/', rp) and p.endswith(('.ts', '.js', '.json', '.md', '.mdx', '.yml', '.yaml', '.php')):
            content.add(rp.split('/content/')[0] + '/content/' if '/content/' in '/' + rp else os.path.dirname(rp) + '/')
        base_name = os.path.basename(p).lower()
        if base_name in ('redirect-map.csv', 'vercel.json', '_redirects', '.htaccess', 'netlify.toml'):
            redirects.add(rp)
        if not p.endswith(CODE):
            continue
        t = read(p, 300_000)
        for m in re.finditer(r'<form[^>]*action=["\']([^"\']+)', t):
            forms.add(('PHP endpoint ' if '<?' in m.group(1) else '') + m.group(1))
        if p.endswith('.php') and not re.search(r'(^|/)(lib|vendor|libs|third[-_]party)/', rp) \
                and re.search(r'PHPMailer|\bmail\s*\(|wp_mail\s*\(', t):
            mailers.add(rp)
        for m in re.finditer(r'fetch\(\s*[`"\'](/api/[^`"\']+|https?://[^`"\']+)', t):
            forms.add('fetch ' + m.group(1)[:80])
        if '/api/' in rp and p.endswith('.php'):
            forms.add('PHP handler ' + rp)
        tracking.update(x for x in re.findall(r'\b(GTM-[A-Z0-9]{5,9}|G-[A-Z0-9]{8,12}|AW-\d{8,12})\b', t)
                        if not re.fullmatch(r'(GTM|G)-X+', x))
        if re.search(r"fbq\(\s*['\"]init", t):
            tracking.add('Meta pixel')
        fonts.update(re.findall(r'https://fonts\.googleapis\.com/css2\?[^"\'\s)]+', t)[:5])
        if p.endswith(('.css', '.scss')) and '/min/' not in rp and 'vendor' not in rp:
            for fam in re.findall(r"@font-face\s*\{[^}]*font-family:\s*['\"]?([^;'\"]+)", t):
                fonts.add('self-hosted: ' + fam.strip() + ' (copy the font files and @font-face CSS into the theme)')
        for lib, rx in (('Swiper', r'swiper'), ('GSAP', r'\bgsap\b'), ('AOS', r'\baos\.(js|css)|data-aos='),
                        ('Alpine.js', r'x-data=|alpinejs'), ('jQuery', r'jquery(\.min)?\.js'), ('Lottie', r'lottie')):
            if re.search(rx, t, re.I):
                libs.add(lib)
        if re.search(r"from\s+['\"]next/font/(google|local)['\"]", t):
            fonts.add('next/font (self-hosted at build time: copy the built font files and @font-face CSS)')
        for lib, rx in (('Material Symbols/Icons', r'Material\+Symbols|material-icons|material-symbols'), ('Font Awesome', r'fontawesome|font-awesome'),
                        ('lucide-react', r"from ['\"]lucide-react"), ('react-icons', r"from ['\"]react-icons"), ('heroicons', r'heroicons')):
            if re.search(rx, t, re.I):
                icons.add(lib)
        next_image += len(re.findall(r"from ['\"]next/image['\"]", t))
    r['content_sources'] = sorted(content)[:20]
    r['forms'] = sorted(forms)[:20]
    r['tracking'] = sorted(tracking)
    r['fonts'] = sorted(fonts)
    r['icons'] = sorted(icons)
    r['next_image_imports'] = next_image
    r['redirect_sources'] = sorted(redirects)
    r['mail_handlers'] = sorted(mailers)
    r['libraries'] = sorted(libs)
    if libs:
        r['notes'].append('Front-end libraries (' + ', '.join(sorted(libs)) + '): ship the same versions in the theme and '
                          'keep their markup and classes; their behaviour is part of the parity check.')
    r['private_files'] = private
    if mailers:
        r['notes'].append('The source sends its own mail (' + ', '.join(sorted(mailers)[:3]) + '): Contact Form 7 replaces it. '
                          'Copy the email layout and recipients, not the mailer code.')
    if private:
        r['notes'].append('Secrets or personal data (' + ', '.join(private[:5]) + '): never read them aloud, copy them into '
                          'the theme, the seed or the repo, or open lead files; ask the developer for what is needed.')

    # Golden master method.
    s = r['stack']
    if s == 'static-html':
        gm = 'The HTML files are the golden master: serve the folder as <site>-ref and copy markup and CSS as they are.'
    elif s == 'nextjs' and (r['next']['static_export'] or r['next']['conditional_export']):
        gm = ('Build the static export (out/) with the live settings (indexable; the build script may need an env such as '
              'STATIC_EXPORT=1 or SITE_INDEXABLE=1) and serve it as <site>-ref. Never upload the repo zip.')
    elif s == 'nextjs':
        gm = ('No static export: either add one (output "export", force-static robots/sitemap, an image loader) on a copy, '
              'or run "next build && next start" and capture every route with _plan/tools/snapshot-routes.mjs.')
    elif s == 'php':
        gm = ('Server-rendered PHP: serve the source unchanged as its own local site (<site>-ref.test), then capture each '
              'route\'s rendered HTML with _plan/tools/snapshot-routes.mjs; that capture is the markup to copy. The CSS is the '
              'compiled file the pages load (run the build only in a copy if it is missing). Check .htaccess for the real URLs.')
    elif s in ('gatsby', 'astro') or (s == 'sveltekit'):
        gm = 'Build (static output in public/ or dist/) and serve it as <site>-ref; check the HTML holds the rendered text.'
    else:
        gm = ('Client-rendered app: build and preview it, then capture each route\'s rendered HTML with '
              '_plan/tools/snapshot-routes.mjs; that capture is the markup to copy. CSS comes from the build.')
    r['golden_master'] = gm
    if r.get('dynamic_routes'):
        r['notes'].append('Dynamic routes: list their real paths from the content or the built output.')
    if r['tailwind']:
        r['notes'].append('Tailwind: keep the same Tailwind version and config in the _tw theme; prove the CSS with the swap test.')
        major = re.search(r'(\d+)', str((r['tailwind'] or {}).get('dependency') or ''))
        if (major and major.group(1) == '3') or (r['tailwind'] or {}).get('config'):
            r['notes'].append('Tailwind v3 (a tailwind.config file): _tw builds with v4, whose defaults differ. Upgrade a copy of the '
                              'source (npx @tailwindcss/upgrade) and prove 0 diff, or ship the compiled CSS verbatim; record the '
                              'choice (references/source-types.md).')
    if s == 'nextjs' and next_image:
        r['notes'].append('next/image: copy its srcset widths and rule (references/build.md, media).')

    if '--site-draft' in sys.argv:
        # A first site.json from what the source shows; the intake fills the rest (references/setup.md).
        kit = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ex = os.path.join(kit, 'assets', 'site.example.json')
        if not os.path.exists(ex):
            ex = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'site.example.json')
        draft = json.load(open(ex, encoding='utf-8'))
        draft['starter'] = 'tw' if r['tailwind'] else 'barebones'
        gtm = [x for x in r['tracking'] if x.startswith('GTM-')]
        draft['gtm'] = gtm[0] if gtm else ''
        if r.get('html_attributes'):
            draft['html_attributes'] = r['html_attributes']
        links = [f'<link href="{u}" rel="stylesheet">' for u in r['fonts'] if u.startswith('https://')]
        draft['font_links'] = links
        draft['_from_source'] = ('starter, gtm, html_attributes and font_links come from analyze-source.py; '
                                 'every other value is the example and must come from the intake')
        out = sys.argv[sys.argv.index('--site-draft') + 1]
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        if os.path.exists(out):
            print(f'site draft: {out} exists, not overwritten')
        else:
            json.dump(draft, open(out, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
            print(f'site draft: {out} written (fill the rest from the intake)')
    if '--json' in sys.argv:
        out = sys.argv[sys.argv.index('--json') + 1]
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        json.dump(r, open(out, 'w', encoding='utf-8'), indent=2)
    print(f"stack: {s}" + (f" (Next {r['next']['version']}, static export {r['next']['static_export']}, conditional export {r['next']['conditional_export']})" if s == 'nextjs' else ''))
    if s == 'nextjs':
        n = r['next']
        print(f"next/image: srcset widths {n['srcset_widths']}, first deviceSize {n['first_device_size']}, custom loader {n['image_loader']}, trailingSlash {n['trailing_slash']}")
    print(f"package: {r.get('package_json', '-')} ({r.get('package_manager', '-')}); build scripts: {', '.join(k for k in r.get('scripts', {}) if 'build' in k or 'export' in k) or '-'}")
    print(f"built output: {json.dumps(built) if built else 'none'}" + (f"; zips: {', '.join(r['zips'])}" if r.get('zips') else ''))
    print(f"tailwind: {'yes ' + json.dumps(r['tailwind']) if r['tailwind'] else 'no'} -> starter theme {r['starter_theme']}")
    if r.get('html_attributes') is not None:
        print(f"html attributes: {r['html_attributes'] or '(none)'} -> site.json html_attributes")
    print(f"routes ({len(r['routes'])}): {' '.join(r['routes'][:60])}")
    for k in ('dynamic_routes', 'content_sources', 'forms', 'mail_handlers', 'tracking', 'fonts', 'icons', 'libraries',
              'redirect_sources',
              'private_files'):
        if r.get(k):
            print(f"{k}: {' | '.join(map(str, r[k]))}")
    print(f"next/image imports: {next_image}")
    print(f"golden master: {gm}")
    for n in r['notes']:
        print('note:', n)


if __name__ == '__main__':
    main()
