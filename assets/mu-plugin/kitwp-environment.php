<?php
/**
 * Plugin Name: {{SITE_NAME}} environment
 * Description: The environment by host when wp-config does not set it (a Duplicator import replaces wp-config): the
 * live host is production, a local address is local, any other host is staging. Staging is never indexed.
 * Version: 1.0.0
 *
 * Made by the convert-to-wordpress kit (new-site.py) into wp-content/mu-plugins/; it travels in the Duplicator
 * package, so a copy on a staging host knows it is staging even after the import wrote its own wp-config, .htaccess
 * and Reading setting. wp-config's own WP_ENVIRONMENT_TYPE always wins. The theme reads the environment as usual
 * (wp_get_environment_type()): staging sends no leads to the portal, and sections the theme shows only outside
 * production (the source preview's pending content) show there as in the preview. A new live domain: update the
 * two live hosts below (or define WP_ENVIRONMENT_TYPE 'production' in the live wp-config).
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

/**
 * The environment for this site's address (the home URL, never the request's Host header).
 *
 * @return string production, local or staging.
 */
function kitwp_environment_by_host() {
	$home = defined( 'WP_HOME' ) ? WP_HOME : get_option( 'home' );
	$host = strtolower( (string) wp_parse_url( (string) $home, PHP_URL_HOST ) );
	if ( in_array( $host, array( '{{LIVE_HOST}}', '{{OTHER_HOST}}' ), true ) ) {
		return 'production';
	}
	$local = strtolower( (string) preg_replace( '/:\d+$/', '', '{{LOCAL_HOST}}' ) );
	if ( $local === $host || in_array( $host, array( 'localhost', '127.0.0.1', '[::1]', '::1' ), true )
		|| preg_match( '/\.(test|localhost|local)$/', $host ) ) {
		return 'local';
	}
	return 'staging';
}

if ( ! defined( 'WP_ENVIRONMENT_TYPE' ) ) {
	define( 'WP_ENVIRONMENT_TYPE', kitwp_environment_by_host() );
}

// Staging is never indexed, whatever the imported Reading setting says: no robots, and the header for files too.
if ( 'staging' === WP_ENVIRONMENT_TYPE ) {
	add_filter( 'pre_option_blog_public', '__return_zero' );
	add_filter( 'wp_robots', 'wp_robots_no_robots' );
	add_action(
		'send_headers',
		static function () {
			header( 'X-Robots-Tag: noindex, nofollow', true );
		}
	);
}
