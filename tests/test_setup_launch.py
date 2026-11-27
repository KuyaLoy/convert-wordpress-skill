"""Setup and launch get these right the first time: the live .htaccess per domain, the runbook per site, the
starter's unused files moved aside, plain ACF instructions, and the fresh install without CF7's sample form."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

from helpers import load, path, run


def read(p):
    with open(p, encoding='utf-8') as fh:
        return fh.read()


def write(p, text):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def make_site(root, **values):
    site = json.loads(read(path('assets', 'site.example.json')))
    site.update(site_name='Acme', legal_name='Acme Ltd', domain='acme.example.org', wp_root=root,
                local_host='acme.test', site_dir='acme', theme='acme', prefix='acme', key='ac')
    for k, v in values.items():
        if v is None:
            site.pop(k, None)
        else:
            site[k] = v
    sj = os.path.join(root, '_plan', 'site.json')
    write(sj, json.dumps(site))
    return sj


def render(profile=None, **values):
    """--plan-only into a new folder; returns (result, root)."""
    tmp = tempfile.mkdtemp()
    root = os.path.join(tmp, 'acme')
    prof = os.path.join(tmp, 'profile.local.json')
    write(prof, json.dumps(profile or {'leads_portal': {'constant_prefix': 'acme_leads'}}))
    r = run('scripts/new-site.py', make_site(root, **values), '--plan-only', '--profile', prof)
    return r, root


def launch(root, name):
    return read(os.path.join(root, '_setup', 'launch', name))


class HtaccessLive(unittest.TestCase):
    """F-042, F-043, F-063, F-100: the host rule is the site's own, private and developer files are closed."""

    def test_www_site(self):
        for values in ({'domain': 'www.acme.example.org', 'www': None}, {'domain': 'acme.example.org', 'www': True}):
            r, root = render(**values)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            ht = launch(root, 'htaccess-live.txt')
            self.assertNotIn('www\\.www', ht)
            self.assertIn('RewriteCond %{HTTP_HOST} ^acme\\.example\\.org$ [NC]\n'
                          '  RewriteRule ^ https://www.acme.example.org%{REQUEST_URI} [R=301,L]', ht)
            self.assertIn('RewriteCond %{HTTP_HOST} ^www\\.acme\\.example\\.org$ [NC]\n'
                          '  RewriteCond %{HTTPS} !=on', ht)
            self.assertIn('Live address https://www.acme.example.org,', launch(root, 'RUNBOOK.md'))

    def test_non_www_site_and_the_closed_files(self):
        r, root = render(www=False)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        ht = launch(root, 'htaccess-live.txt')
        self.assertIn('RewriteCond %{HTTP_HOST} ^www\\.acme\\.example\\.org$ [NC]\n'
                      '  RewriteRule ^ https://acme.example.org%{REQUEST_URI} [R=301,L]', ht)
        self.assertIn('RewriteCond %{HTTP_HOST} ^acme\\.example\\.org$ [NC]\n  RewriteCond %{HTTPS} !=on', ht)
        self.assertNotIn('https://www.', ht)
        self.assertIn('readme\\.html|license\\.txt|wp-config-sample\\.php|xmlrpc\\.php', ht)
        for rule in ('acf-json|node_modules|vendor|tests', 'composer\\.(json|lock)|package(-lock)?\\.json',
                     'phpcs\\.xml\\.dist', '.*\\.(md|log)$'):
            self.assertIn(rule, ht)
        self.assertIn('^/wp-content/themes/acme/', ht)
        self.assertNotIn('(?!theme/)', ht)  # Barebones: the theme folder itself is what WordPress loads
        for header in ('X-Content-Type-Options "nosniff"', 'Referrer-Policy "strict-origin-when-cross-origin"',
                       'X-Frame-Options "SAMEORIGIN"'):
            self.assertEqual(ht.count(header), 1, header)
        self.assertNotIn('<!--', ht)
        self.assertNotIn('{{', ht)
        r, root = render(starter='tw')
        self.assertIn('RedirectMatch 404 ^/wp-content/themes/acme/(?!theme/)', launch(root, 'htaccess-live.txt'))


class RunbookPerSite(unittest.TestCase):
    """F-082, F-083, F-084, F-090, F-103, F-048: only this site's forms, redirects, tracking and live addresses."""

    def test_forms_leads_tracking_and_local_hosts(self):
        r, root = render(forms=['the contact form', 'the quote pop-up'], gtm='GTM-AB12CD')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rb = launch(root, 'RUNBOOK.md')
        self.assertIn('One real test lead per form (the contact form, the quote pop-up)', rb)
        self.assertNotIn('chat', rb.split('## 5.')[1].split('## 6.')[0])
        self.assertIn('Where live leads go: each Contact Form 7 form\'s Mail tab "To" is the client\'s live address '
                      '(office@example.com', rb)
        self.assertIn('Client to-dos told to the client', rb)
        self.assertIn("wp search-replace '//acme.test' '//acme.example.org' --all-tables --dry-run", rb)
        self.assertIn("wp db search '[a-z0-9-]+\\.test|localhost' --all-tables --regex", rb)
        self.assertIn('Google Tag Manager ID GTM-AB12CD', rb)
        self.assertIn('live-qa.py https://acme.example.org --gtm GTM-AB12CD --local acme.test '
                      '--theme wp-content/themes/acme --wp "wp @live"`', rb)  # 0.12.0: --wp
        self.assertIn('track.mjs https://acme.example.org GTM-AB12CD', rb)
        self.assertNotIn('Redirection', rb.replace('no\n      Redirection plugin', '').replace(
            '(the Redirection plugin then joins the live plugins)', ''))
        self.assertIn('Old URLs: none to redirect', rb)
        self.assertIn('leads portal\'s form counts', rb)
        for kept in ('`ACME_LEADS_ENDPOINT`', '   - [ ] LiteSpeed Cache (the cache plugin)', '**Staging**'):
            self.assertIn(kept, rb)
        self.assertNotIn('<!--', rb)
        self.assertNotIn('{{', rb)

    def test_no_forms_no_tracking_no_portal_and_no_list(self):
        r, root = render({}, forms=[], gtm='', leads_portal='none: a brochure site without forms')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rb = launch(root, 'RUNBOOK.md')
        self.assertIn('No lead forms on this site', rb)
        self.assertNotIn('One real test lead', rb)
        self.assertIn('Tracking: none in this build', rb)
        self.assertNotIn('--gtm', rb)
        self.assertNotIn('track.mjs', rb)
        self.assertNotIn('Leads portal ready', rb)
        r, root = render(forms=None, chat=True, lead={'to': ''})
        rb = launch(root, 'RUNBOOK.md')
        self.assertIn('One real test lead per form (the contact form, the chat)', rb)
        self.assertIn('BLOCKER: site.json lead.to is empty', rb)
        self.assertIn('site.json has no "forms" list', r.stdout)

    def test_redirects_from_the_old_url_plan(self):
        r, root = render()
        self.assertNotIn('Tools > Redirection', launch(root, 'RUNBOOK.md'))
        plan_doc = os.path.join(root, '_plan', 'OLD-SITE-URLS.md')
        write(plan_doc, read(plan_doc) + '| /old-about/ | 301 | /about/ |\n')
        with open(os.path.join(root, '_setup', 'launch', 'RUNBOOK.md'), 'a', encoding='utf-8') as fh:
            fh.write('\nDeveloper note kept in the old copy.\n')
        r = run('scripts/new-site.py', os.path.join(root, '_plan', 'site.json'), '--launch-files', '--profile',
                os.path.join(os.path.dirname(root), 'profile.local.json'))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.startswith('OK new-site: launch files written'), r.stdout)
        rb = launch(root, 'RUNBOOK.md')
        self.assertIn('   - [ ] Redirection: Tools > Redirection, import `_setup/seed/redirects.json`', rb)
        self.assertIn('--redirects _setup/seed/redirects.json --wp "wp @live"`', rb)
        self.assertIn('Tools > Redirection > 404s weekly', rb)
        self.assertIn('Old-URL redirects live in Tools > Redirection', launch(root, 'htaccess-live.txt'))
        old = [d for d in os.listdir(os.path.join(root, '_setup', 'launch')) if d.startswith('before-')]
        self.assertEqual(len(old), 1)
        self.assertIn('Developer note kept', read(os.path.join(root, '_setup', 'launch', old[0], 'RUNBOOK.md')))


TW_FUNCTIONS = """<?php
/**
 * Acme functions and definitions
 *
 * @package Acme
 */

if ( ! function_exists( 'acme_setup' ) ) :
	/**
	 * Sets up theme defaults.
	 */
	function acme_setup() {
		load_theme_textdomain( 'acme', get_template_directory() . '/languages' );

		// Add default posts and comments RSS feed links to head.
		add_theme_support( 'automatic-feed-links' );

		add_theme_support( 'title-tag' );

		/*
		 * Switch default core markup for search form, comment form, and comments
		 * to output valid HTML5.
		 */
		add_theme_support(
			'html5',
			array(
				'search-form',
				'comment-form',
				'comment-list',
				'gallery',
				'caption',
				'style',
				'script',
			)
		);

		// Add theme support for selective refresh for widgets.
		add_theme_support( 'customize-selective-refresh-widgets' );

		// Add support for editor styles.
		add_theme_support( 'editor-styles' );
	}
endif;
add_action( 'after_setup_theme', 'acme_setup' );

/**
 * Register widget area.
 *
 * @link https://developer.wordpress.org/themes/functionality/sidebars/#registering-a-sidebar
 */
function acme_widgets_init() {
	register_sidebar(
		array(
			'name' => __( 'Footer', 'acme' ),
			'id'   => 'sidebar-1',
		)
	);
}
add_action( 'widgets_init', 'acme_widgets_init' );

/**
 * Enqueue scripts and styles.
 */
function acme_scripts() {
	wp_enqueue_style( 'acme-style', get_stylesheet_uri(), array(), '0.1.0' );

	if ( is_singular() && comments_open() && get_option( 'thread_comments' ) ) {
		wp_enqueue_script( 'comment-reply' );
	}
}
add_action( 'wp_enqueue_scripts', 'acme_scripts' );

/**
 * Enqueue the block editor script.
 */
function acme_enqueue_block_editor_script() {
	wp_enqueue_script( 'acme-editor', get_template_directory_uri() . '/js/block-editor.min.js', array(), '0.1.0', true );
}
add_action( 'enqueue_block_assets', 'acme_enqueue_block_editor_script' );

/**
 * Limit the block editor to heading levels supported by Tailwind Typography.
 *
 * @param array  $args Array of arguments for registering a block type.
 * @param string $block_type Block type name including namespace.
 * @return array
 */
function acme_modify_heading_levels( $args, $block_type ) {
	if ( 'core/heading' !== $block_type ) {
		return $args;
	}
	$args['attributes']['levelOptions']['default'] = array( 2, 3, 4 );
	return $args;
}
add_filter( 'register_block_type_args', 'acme_modify_heading_levels', 10, 2 );

/**
 * Custom template tags for this theme.
 */
require get_template_directory() . '/inc/template-tags.php';

/**
 * Functions which enhance the theme by hooking into WordPress.
 */
require get_template_directory() . '/inc/template-functions.php';
"""

TW_PAGE = """<?php
get_header();
while ( have_posts() ) :
	the_post();
	get_template_part( 'template-parts/content/content', 'page' );

	// If comments are open, or we have at least one comment, load the comment template.
	if ( comments_open() || get_comments_number() ) {
		comments_template();
	}
endwhile;
get_footer();
"""

TW_CONTENT_PAGE = """<article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
	<?php acme_post_thumbnail(); ?>
	<div <?php acme_content_class( 'entry-content' ); ?>>
		<?php the_content(); ?>
	</div>
</article>
"""

TW_HEADER = """/*!
Theme Name: Acme
Theme URI: https://underscoretw.com/
Description: A custom theme based on _tw
Version: 0.1.0
Author: underscoretw.com
Author URI: https://underscoretw.com/
Text Domain: acme
Requires at least: 7.1
Requires PHP: 7.4
*/
"""


def tw_site(**values):
    """A WordPress folder with a generated _tw theme (only the files new-site.py reads or moves)."""
    tmp = tempfile.mkdtemp()
    root = os.path.join(tmp, 'acme')
    tr = os.path.join(root, 'wp-content', 'themes', 'acme')
    th = os.path.join(tr, 'theme')
    write(os.path.join(root, 'wp-includes', 'version.php'), "<?php $wp_version = '7.1';\n")
    files = {
        'style.css': TW_HEADER, 'style-editor.css': TW_HEADER, 'functions.php': TW_FUNCTIONS, 'page.php': TW_PAGE,
        'index.php': "<?php\nget_header();\nacme_the_posts_navigation();\nget_footer();\n",
        '404.php': "<?php\nget_header();\n?>\n<div <?php acme_content_class( 'page-content' ); ?>></div>\n<?php\n"
                   'get_footer();\n',
        'archive.php': '<?php\n', 'search.php': '<?php\n', 'single.php': '<?php\n', 'comments.php': '<?php\n',
        'template-parts/content/content.php': '<?php\n', 'template-parts/content/content-none.php': '<?php\n',
        'template-parts/content/content-excerpt.php': '<?php\n', 'template-parts/content/content-single.php': '<?php\n',
        'template-parts/content/content-page.php': TW_CONTENT_PAGE,
        'inc/template-tags.php': "<?php\nfunction acme_post_thumbnail() {}\nfunction acme_the_posts_navigation() {}\n",
        'inc/template-functions.php': "<?php\nfunction acme_content_class( $c = '' ) {}\n",
        'js/script.min.js': '', 'js/readme.txt': 'x', 'js/block-editor.min.js': '', 'languages/readme.txt': 'x',
        'theme.json': json.dumps({'version': 3, 'settings': {'color': {'palette': [
            {'slug': 'background', 'color': '#ffffff', 'name': 'Background'},
            {'slug': 'foreground', 'color': '#404040', 'name': 'Foreground'},
            {'slug': 'primary', 'color': '#b91c1c', 'name': 'Primary'},
            {'slug': 'secondary', 'color': '#15803d', 'name': 'Secondary'},
            {'slug': 'tertiary', 'color': '#0369a1', 'name': 'Tertiary'}]},
            'layout': {'contentSize': '40rem', 'wideSize': '60rem'}}}),
    }
    for f, text in files.items():
        write(os.path.join(th, *f.split('/')), text)
    write(os.path.join(tr, 'tailwind', 'custom', 'file-header.css'), TW_HEADER)
    write(os.path.join(tr, 'javascript', 'block-editor.js'), '')
    write(os.path.join(tr, 'package.json'), json.dumps({'scripts': {
        'development:esbuild': 'npx esbuild ./javascript/script.js ./javascript/block-editor.js --bundle'}}))
    write(os.path.join(tr, 'tests', 'parity', 'swap', 'index.html'), 'swap test output')
    r = run('scripts/new-site.py', make_site(root, starter='tw', **values), '--profile', os.path.join(tmp, 'none.json'))
    return r, root, tr, th


class StarterTidy(unittest.TestCase):
    """F-003, F-069, F-078, F-097, F-105, F-114, F-117: what the site does not use goes aside, never deleted."""

    def test_tw_without_blog_or_chat(self):
        r, root, tr, th = tw_site()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('starter tidied for this site (no blog, no chat)', r.stdout)
        aside = os.path.join(root, '_setup', 'starter-removed')
        for f in ('archive.php', 'search.php', 'single.php', 'comments.php', 'index.php', 'js/readme.txt',
                  'js/block-editor.min.js', 'languages/readme.txt', 'inc/template-tags.php',
                  'inc/template-functions.php', 'template-parts/content/content-none.php'):
            self.assertFalse(os.path.exists(os.path.join(th, *f.split('/'))) and f != 'index.php', f)
            self.assertTrue(os.path.exists(os.path.join(aside, 'theme', *f.split('/'))), f)
        self.assertTrue(os.path.exists(os.path.join(aside, 'tests', 'parity', 'swap', 'index.html')))
        self.assertTrue(os.path.exists(os.path.join(aside, 'javascript', 'block-editor.js')))
        self.assertFalse(os.path.exists(os.path.join(th, 'assets', 'chat-save.js')))
        self.assertTrue(os.path.exists(os.path.join(th, 'template-parts', 'content', 'content-page.php')))
        fn = read(os.path.join(th, 'functions.php'))
        for gone in ('automatic-feed-links', "'search-form'", "'comment-form'", "'comment-list'",
                     'customize-selective-refresh-widgets', 'register_sidebar', 'comment-reply',
                     'acme_modify_heading_levels', 'block-editor.min.js', '/inc/template-tags.php',
                     '/inc/template-functions.php'):
            self.assertNotIn(gone, fn)
        for kept in ("'gallery'", 'editor-styles', 'acme_scripts', "'seed-pages'"):
            self.assertIn(kept, fn)
        self.assertIn("get_template_part( '404' );", read(os.path.join(th, 'index.php')))
        page = read(os.path.join(th, 'page.php'))
        self.assertNotIn('comments_template', page)
        cp = read(os.path.join(th, 'template-parts', 'content', 'content-page.php'))
        self.assertIn('<div class="entry-content">', cp)
        self.assertIn('the_post_thumbnail()', cp)
        self.assertIn('<div class="page-content">', read(os.path.join(th, '404.php')))
        for header in (os.path.join(th, 'style.css'), os.path.join(tr, 'tailwind', 'custom', 'file-header.css')):
            text = read(header)
            self.assertNotIn('underscoretw.com', text)
            self.assertIn('Requires PHP: 8.1', text)
            self.assertIn('Theme URI: https://acme.example.org/', text)
        self.assertNotIn('block-editor.js', read(os.path.join(tr, 'package.json')))
        colours = [c['color'] for c in json.loads(read(os.path.join(th, 'theme.json')))['settings']['color']['palette']]
        self.assertEqual(colours, ['#ffffff', '#404040'])
        acf_ht = read(os.path.join(th, 'acf-json', '.htaccess'))
        self.assertIn('Require all denied', acf_ht)
        self.assertIn('Deny from all', acf_ht)
        php = shutil.which('php')
        if php:
            for f in ('functions.php', 'index.php', 'page.php', '404.php'):
                lint = subprocess.run([php, '-l', os.path.join(th, f)], capture_output=True, text=True)
                self.assertEqual(lint.returncode, 0, f + lint.stdout)

    def test_tw_with_blog_chat_and_palette(self):
        palette = [{'slug': 'brand', 'color': '#123456', 'name': 'Brand'}]
        r, root, tr, th = tw_site(blog=True, chat=True, palette=palette, content_size='72rem')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for f in ('archive.php', 'single.php', 'comments.php', 'inc/template-tags.php', 'js/block-editor.min.js'):
            self.assertTrue(os.path.exists(os.path.join(th, *f.split('/'))), f)
        fn = read(os.path.join(th, 'functions.php'))
        self.assertIn('automatic-feed-links', fn)
        self.assertIn('/inc/template-tags.php', fn)
        self.assertNotIn('register_sidebar', fn)  # the widget area is never printed, blog or not
        self.assertTrue(os.path.exists(os.path.join(th, 'assets', 'chat-save.js')))
        tj = json.loads(read(os.path.join(th, 'theme.json')))['settings']
        self.assertEqual(tj['color']['palette'], palette)
        self.assertEqual(tj['layout']['contentSize'], '72rem')

    def test_run_again_keeps_the_tidy_theme(self):
        r, root, tr, th = tw_site()
        sj = os.path.join(root, '_plan', 'site.json')
        r = run('scripts/new-site.py', sj, '--profile', os.path.join(root, 'none.json'))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("get_template_part( '404' );", read(os.path.join(th, 'index.php')))


class AcfInstructions(unittest.TestCase):
    """F-009, F-088, F-099, F-116: every field explains itself in plain words."""

    def setUp(self):
        self.acf = load('scripts/acf/build_field_groups.py', 'build_field_groups_test')

    def test_the_kits_example_spec_passes(self):
        self.assertEqual(self.acf.instruction_problems(self.acf.groups), [])

    def test_missing_and_developer_words_are_refused(self):
        g = self.acf.G('demo')
        fields = [
            g.tab('Hero'),
            g.text('title', 'Title', ''),
            g.text('slug', 'Address', '', instructions='The page slug.'),
            g.text('number', 'Number', '', instructions='Token {company_number}.'),
            g.text('order', 'Order', '', instructions='One program_slug per line.'),
            g.rep('rows', 'Rows', [g.text('label', 'Label', '', 'rows', instructions='The words on the button.')],
                  instructions='A repeater of rows.'),
            g.text('ok', 'Number shown', '', instructions='Write {company_number} in any text to show it there.'),
        ]
        groups = {'group_kitk_demo': self.acf.field_group('group_kitk_demo', 'Demo', fields, [])}
        problems = '\n'.join(self.acf.instruction_problems(groups))
        self.assertIn('Demo > Title: no instructions', problems)
        self.assertIn('Demo > Address: developer words (slug)', problems)
        self.assertIn('Demo > Number: developer words (token; {company_number} not explained)', problems)
        self.assertIn('Demo > Order: developer words (program_slug)', problems)
        self.assertIn('Demo > Rows: developer words (repeater)', problems)
        self.assertNotIn('Hero', problems)
        self.assertNotIn('Number shown', problems)
        self.assertNotIn('Label', problems)


class FreshInstallSamples(unittest.TestCase):
    """F-080, F-095: CF7's sample form goes on a fresh install; the privacy setting points at the site's page."""

    def php_run(self, setup):
        php = shutil.which('php')
        if not php:
            self.skipTest('php is not on the PATH')
        src = read(path('scripts', 'setup', 'install-wp.py'))
        block = re.search(r'// kit:samples-start\n(.*?)// kit:samples-end', src, re.S).group(1)
        # Just enough of WordPress for the block: posts in memory, options in an array.
        stub = r"""<?php
$posts = %s;
$options = array( 'wp_page_for_privacy_policy' => 3 );
function get_posts( $q ) {
	global $posts;
	$out = array();
	foreach ( $posts as $p ) {
		$status = empty( $q['post_status'] ) || 'any' === $q['post_status'] || $p->post_status === $q['post_status'];
		if ( $p->post_type === $q['post_type'] && $status && ( empty( $q['name'] ) || $p->post_name === $q['name'] ) ) {
			$out[] = $p;
		}
	}
	return $out;
}
function get_post( $id ) {
	global $posts;
	foreach ( $posts as $p ) {
		if ( $p->ID === (int) $id ) {
			return $p;
		}
	}
	return null;
}
function wp_delete_post( $id, $force ) {
	global $posts;
	$posts = array_values( array_filter( $posts, fn( $p ) => $p->ID !== $id ) );
	return true;
}
function get_option( $k ) {
	global $options;
	return isset( $options[ $k ] ) ? $options[ $k ] : false;
}
function update_option( $k, $v ) {
	global $options;
	$options[ $k ] = $v;
}
$kit_out = array();
""" % setup
        tail = ("\necho json_encode( array( 'out' => $kit_out, 'posts' => array_map( fn( $p ) => $p->ID, $posts ), "
                "'privacy' => $options['wp_page_for_privacy_policy'] ) );\n")
        tmp = tempfile.mkdtemp()
        f = os.path.join(tmp, 't.php')
        write(f, stub + block + tail)
        r = subprocess.run([php, f], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return json.loads(r.stdout)

    def post(self, i, kind, title, status='publish', name=''):
        return (f"(object) array( 'ID' => {i}, 'post_type' => '{kind}', 'post_title' => '{title}', "
                f"'post_status' => '{status}', 'post_name' => '{name}' )")

    def test_fresh_install(self):
        posts = 'array( %s )' % ', '.join([self.post(3, 'page', 'Privacy Policy', 'draft', 'privacy-policy'),
                                           self.post(4, 'wpcf7_contact_form', 'Contact form 1')])
        res = self.php_run(posts + ";\n$kit_fresh = true")
        self.assertEqual(res['posts'], [])
        self.assertEqual(res['privacy'], 0)
        self.assertIn('Contact Form 7 sample form', res['out']['removed'])

    def test_the_sites_privacy_page_and_real_forms_stay(self):
        posts = 'array( %s )' % ', '.join([self.post(3, 'page', 'Privacy Policy', 'draft', 'privacy-policy'),
                                           self.post(4, 'wpcf7_contact_form', 'Contact form 1'),
                                           self.post(9, 'wpcf7_contact_form', 'Quote'),
                                           self.post(12, 'page', 'Privacy', 'publish', 'privacy')])
        res = self.php_run(posts + ";\n$kit_fresh = false")
        self.assertEqual(res['posts'], [3, 4, 9, 12])  # not a fresh install: nothing deleted
        self.assertEqual(res['privacy'], 12)


if __name__ == '__main__':
    unittest.main()
