<?php
/**
 * Seeder: media, Theme Settings, pages, menus, CF7 forms, Yoast and redirects from the static site's content.
 * Local copies only (WP_ENVIRONMENT_TYPE "local"): on any other environment this file does nothing.
 *
 * Seed files live in _setup/seed/ at the WordPress root (written by the exporters in _plan/tools/seed/, private and
 * never deployed): media.json, settings.json, template-pages.json, pages.json, menus.json, forms.json (+ the form and
 * email files it names), seo.json, og-images.json, redirects.json. Tools > Seeder runs them. Every step is
 * idempotent: run it twice, and the second run must report "same" (or "kept") everywhere. This file holds the
 * runner; each step has its own file: seed-media.php, seed-settings.php, seed-pages.php, seed-menus.php,
 * seed-forms.php, seed-seo.php.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

if ( 'local' !== wp_get_environment_type() ) {
	return;
}

/**
 * Seed folder.
 *
 * @return string
 */
function kitwp_seed_dir() {
	return defined( 'KITWP_SEED_DIR' ) ? KITWP_SEED_DIR : ABSPATH . '_setup/seed';
}

/**
 * Read a seed JSON file.
 *
 * @param string $file File name.
 * @return array<mixed>
 */
function kitwp_seed_json( $file ) {
	$path = trailingslashit( kitwp_seed_dir() ) . $file;
	if ( ! is_readable( $path ) ) {
		return [];
	}
	$data = json_decode( (string) file_get_contents( $path ), true ); // phpcs:ignore WordPress.WP.AlternativeFunctions.file_get_contents_file_get_contents -- local seed file.
	return is_array( $data ) ? $data : [];
}

/**
 * Tools > Seeder.
 *
 * @return void
 */
function kitwp_seed_menu_page() {
	add_management_page( __( 'Seeder', 'kitwp' ), __( 'Seeder', 'kitwp' ), 'manage_options', 'kitwp-seeder', 'kitwp_seed_page' );
}
add_action( 'admin_menu', 'kitwp_seed_menu_page' );

/**
 * Seeder screen and runner.
 *
 * @return void
 */
function kitwp_seed_page() {
	if ( ! current_user_can( 'manage_options' ) ) {
		return;
	}
	// The order matters: pages before menus (menus link pages only once they exist), forms before pages that print them.
	$steps  = (array) apply_filters(
		'kitwp_seed_steps',
		[
			'media'          => __( 'Media (media.json)', 'kitwp' ),
			'settings'       => __( 'Theme Settings (settings.json)', 'kitwp' ),
			'forms'          => __( 'Contact Form 7 forms (forms.json)', 'kitwp' ),
			'template_pages' => __( 'Template pages (template-pages.json)', 'kitwp' ),
			'flex_pages'     => __( 'Flexible pages and posts (pages.json)', 'kitwp' ),
			'menus'          => __( 'Menus (menus.json)', 'kitwp' ),
			'seo'            => __( 'Yoast SEO settings, social images, page types (seo.json, og-images.json)', 'kitwp' ),
			'redirects'      => __( 'Old URL redirects, Redirection plugin (redirects.json)', 'kitwp' ),
		]
	);
	$result = [];
	if ( ! function_exists( 'update_field' ) ) {
		echo '<div class="notice notice-error"><p>' . esc_html__( 'ACF PRO or Secure Custom Fields is not active: the seeder needs one of them.', 'kitwp' ) . '</p></div>';
		return;
	}
	if ( isset( $_POST['kitwp_seed'] ) && check_admin_referer( 'kitwp_seed' ) ) {
		$run = sanitize_key( wp_unslash( $_POST['kitwp_seed'] ) );
		foreach ( array_keys( $steps ) as $step ) {
			if ( ( 'all' === $run || $step === $run ) && function_exists( 'kitwp_seed_' . $step ) ) {
				$result[ $step ] = call_user_func( 'kitwp_seed_' . $step );
			}
		}
	}
	echo '<div class="wrap"><h1>' . esc_html__( 'Seeder', 'kitwp' ) . '</h1>';
	echo '<p>' . esc_html__( 'Seeds content from the static site. Safe to run again: anything already seeded is left as it is.', 'kitwp' ) . '</p>';
	echo '<p><code>' . esc_html( kitwp_seed_dir() ) . '</code> ' . ( is_dir( kitwp_seed_dir() ) ? esc_html__( 'found', 'kitwp' ) : '<strong>' . esc_html__( 'not found', 'kitwp' ) . '</strong>' ) . '</p>';
	foreach ( $result as $step => $counts ) {
		$parts = [];
		foreach ( $counts as $k => $n ) {
			$parts[] = $k . ' ' . (int) $n;
		}
		if ( 'menus' === $step && ! empty( $GLOBALS['kitwp_seed_menu_changed'] ) ) {
			$parts[] = 'changed: ' . implode( ', ', (array) $GLOBALS['kitwp_seed_menu_changed'] );
		}
		if ( in_array( $step, [ 'settings', 'seo' ], true ) && ! empty( $GLOBALS['kitwp_seed_changed'] ) ) {
			$parts[] = 'changed: ' . implode( ', ', (array) $GLOBALS['kitwp_seed_changed'] );
		}
		echo '<div class="notice notice-success"><p><strong>' . esc_html( $steps[ $step ] ) . ':</strong> ' . esc_html( implode( ', ', $parts ) ) . '</p></div>';
	}
	echo '<form method="post">';
	wp_nonce_field( 'kitwp_seed' );
	foreach ( $steps as $step => $label ) {
		echo '<p><button class="button" name="kitwp_seed" value="' . esc_attr( $step ) . '">' . esc_html( $label ) . '</button></p>';
	}
	echo '<p><button class="button button-primary" name="kitwp_seed" value="all">' . esc_html__( 'Run all', 'kitwp' ) . '</button></p></form></div>';
}
