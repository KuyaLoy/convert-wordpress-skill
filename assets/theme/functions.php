<?php
/**
 * {{SITE_NAME}} theme functions.
 *
 * Barebones' own files first (new-site.py moved its sample block, shortcodes, acf.php and functions.php to
 * _setup/starter-removed/), then the kit's files in this order: config first, seed.php before seed-pages.php. The
 * seed and snapshot files do nothing outside WP_ENVIRONMENT_TYPE "local". A _tw theme keeps its own functions.php:
 * new-site.py appends the kit's lines there instead.
 * After every PHP save: php -l, PHPCS, and the duplicate function check below (it must print nothing).
 *
 * @package kitwp
 */

// Duplicate function check (php -l cannot catch it; a duplicate took the reference build down twice):
// grep -h "^function" includes/*.php | sed 's/(.*//' | sort | uniq -d

$kitwp_inc = get_template_directory() . '/includes/';

// Barebones' files.
foreach ( [ 'setup', 'admin', 'menus', 'loaders', 'custom' ] as $kitwp_file ) {
	if ( file_exists( $kitwp_inc . $kitwp_file . '.php' ) ) {
		require_once $kitwp_inc . $kitwp_file . '.php';
	}
}

// The kit.
foreach ( [ 'config', 'cleanup', 'head', 'acf', 'helpers', 'media', 'forms', 'schema', 'seo', 'seed', 'seed-pages', 'snapshot' ] as $kitwp_file ) {
	require_once $kitwp_inc . $kitwp_file . '.php';
}
