<?php
/**
 * Front-end clean-up for the 1:1 rule: only the static site's CSS may style a page, so WordPress and plugin
 * front-end styles that could change the look are switched off. The admin area is not affected.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

/**
 * Dequeue WordPress front-end styles that the static site does not have.
 *
 * @return void
 */
function kitwp_dequeue_core_styles() {
	foreach ( [ 'wp-block-library', 'wp-block-library-theme', 'classic-theme-styles', 'global-styles', 'core-block-supports', 'wp-img-auto-sizes-contain' ] as $kitwp_handle ) {
		wp_dequeue_style( $kitwp_handle );
		wp_deregister_style( $kitwp_handle );
	}
}
add_action( 'wp_enqueue_scripts', 'kitwp_dequeue_core_styles', 100 );

// Global styles from theme.json (front end and the late footer copy).
remove_action( 'wp_enqueue_scripts', 'wp_enqueue_global_styles' );
remove_action( 'wp_footer', 'wp_enqueue_global_styles', 1 );
remove_action( 'wp_body_open', 'wp_global_styles_render_svg_filters' );

// Block CSS printed per block, and the "sizes=auto" image CSS (WordPress 6.7+).
add_filter( 'should_load_separate_core_block_assets', '__return_false' );
add_filter( 'wp_img_tag_add_auto_sizes', '__return_false' );

// Contact Form 7: no stylesheet (the forms are styled by the static CSS).
add_filter( 'wpcf7_load_css', '__return_false' );

// Head extras the static site does not print, and the emoji script.
remove_action( 'wp_head', 'rsd_link' );
remove_action( 'wp_head', 'wlwmanifest_link' );
remove_action( 'wp_head', 'wp_generator' );
remove_action( 'wp_head', 'wp_shortlink_wp_head', 10 );
remove_action( 'wp_head', 'rest_output_link_wp_head', 10 );
remove_action( 'wp_head', 'wp_oembed_add_discovery_links' );
remove_action( 'wp_head', 'print_emoji_detection_script', 7 );
remove_action( 'wp_print_styles', 'print_emoji_styles' );

/**
 * The WordPress toolbar (Dashboard, Edit Page...) shows for logged-in users, as in any theme. Visitors never get it,
 * so the public page stays 1:1 (parity runs logged out). While it shows, KITWP_ADMIN_BAR_CSS (config.php) moves a
 * sticky or fixed static header, and anything placed below it, down by the toolbar's height.
 *
 * @return void
 */
function kitwp_admin_bar_offset() {
	if ( '' === KITWP_ADMIN_BAR_CSS || ! is_admin_bar_showing() ) {
		return;
	}
	echo '<style id="kitwp-admin-bar">' . KITWP_ADMIN_BAR_CSS . "</style>\n"; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- a theme constant.
}
add_action( 'wp_head', 'kitwp_admin_bar_offset', 100 );

// Speculative loading (WordPress 6.8+) prints a speculation-rules script the static site does not have.
add_filter( 'wp_speculation_rules_configuration', '__return_null' );

/**
 * Hide the REST user list from visitors: WordPress shows usernames at /wp-json/wp/v2/users. Logged-in users keep
 * it. Return false from the "kitwp_hide_rest_users" filter if a plugin needs the public list.
 *
 * @param array<string, mixed> $endpoints REST routes.
 * @return array<string, mixed>
 */
function kitwp_rest_hide_users( $endpoints ) {
	if ( ! is_user_logged_in() && apply_filters( 'kitwp_hide_rest_users', true ) ) {
		unset( $endpoints['/wp/v2/users'], $endpoints['/wp/v2/users/(?P<id>[\d]+)'] );
	}
	return $endpoints;
}
add_filter( 'rest_endpoints', 'kitwp_rest_hide_users' );

/**
 * oEmbed answers (/wp-json/oembed/1.0/embed) without the author: WordPress puts the page author's display name and
 * author URL in them, which names a login account.
 *
 * @param array<string, mixed> $data oEmbed response data.
 * @return array<string, mixed>
 */
function kitwp_oembed_hide_author( $data ) {
	unset( $data['author_name'], $data['author_url'] );
	return $data;
}
add_filter( 'oembed_response_data', 'kitwp_oembed_hide_author' );

/**
 * A site without search (KITWP_SITE_SEARCH false): "?s=" in the query string is ignored, as a static host ignores
 * query strings, so /?s=x shows the home page. A search path (/search/x) stays a search and kitwp_static_routes()
 * answers it with a 404.
 *
 * @param array<string, mixed> $vars Query vars.
 * @return array<string, mixed>
 */
function kitwp_no_search( $vars ) {
	if ( KITWP_SITE_SEARCH || is_admin() || ! isset( $vars['s'] ) ) {
		return $vars;
	}
	parse_str( (string) ( $GLOBALS['wp']->matched_query ?? '' ), $matched );
	if ( ! isset( $matched['s'] ) ) {
		unset( $vars['s'] );
	}
	return $vars;
}
add_filter( 'request', 'kitwp_no_search' );

/**
 * Whether a route WordPress answers is one the static site does not have: category, tag, taxonomy, date and author
 * archives, paged listings (/page/2/), feeds and search when the site has no blog (KITWP_KEEP_BLOG false);
 * attachment pages, and a page asked for by another path than its own (/home for the front page, /About for
 * /about/), always. Post type archives a build registers on purpose stay.
 *
 * @param string $path The requested path.
 * @return bool
 */
function kitwp_is_starter_route( $path ) {
	if ( is_attachment() || ( is_search() && ! KITWP_SITE_SEARCH ) ) {
		return true;
	}
	if ( ! KITWP_KEEP_BLOG && ( is_category() || is_tag() || is_tax() || is_date() || is_author() || is_paged() || is_feed() ) ) {
		return true;
	}
	if ( ! is_singular() || ( '' === (string) get_query_var( 'pagename' ) && '' === (string) get_query_var( 'name' ) ) ) {
		return false;
	}
	$own = (string) wp_parse_url( (string) get_permalink(), PHP_URL_PATH );
	return untrailingslashit( rawurldecode( $path ) ) !== untrailingslashit( rawurldecode( $own ) );
}

/**
 * Starter routes answer a real 404, as the static site does (kitwp_is_starter_route()). The "kitwp_static_404"
 * filter can keep one (return false). WordPress would otherwise answer some of them with a 301 (to the home page,
 * the file or the right case), so the canonical redirect is off for them.
 *
 * @return void
 */
function kitwp_static_routes() {
	if ( is_admin() || is_404() ) {
		return;
	}
	$path = (string) wp_parse_url( esc_url_raw( wp_unslash( $_SERVER['REQUEST_URI'] ?? '/' ) ), PHP_URL_PATH ); // phpcs:ignore WordPress.Security.ValidatedSanitizedInput.InputNotSanitized -- esc_url_raw() cleans it; only compared.
	if ( ! apply_filters( 'kitwp_static_404', kitwp_is_starter_route( $path ), $path ) ) {
		return;
	}
	global $wp_query;
	$wp_query->set_404();
	$wp_query->is_feed = false; // set_404() keeps it, and the feed (or Yoast's feed redirect) would still answer.
	status_header( 404 );
	nocache_headers();
	remove_action( 'template_redirect', 'redirect_canonical' );
}
// On "wp", before Yoast SEO's feed redirect (priority -10000), which would send /feed/ to the home page with a 301.
add_action( 'wp', 'kitwp_static_routes', -10001 );

// No guessing on a 404 (WordPress sends /serv to /services/ with a 301; a static host answers 404).
add_filter( 'do_redirect_guess_404_permalink', '__return_false' );

// Without a blog the head has no feed links (the static head has none).
if ( ! KITWP_KEEP_BLOG ) {
	remove_action( 'wp_head', 'feed_links', 2 );
	remove_action( 'wp_head', 'feed_links_extra', 3 );
}

// No "optimized with Yoast SEO" comments around the head: the static head has none.
add_filter( 'wpseo_debug_markers', '__return_false' );
