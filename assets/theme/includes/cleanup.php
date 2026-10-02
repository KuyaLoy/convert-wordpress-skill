<?php
/**
 * Front-end clean-up for the 1:1 rule: only the static site's CSS may style a page, so WordPress and plugin
 * front-end styles that could change the look are switched off. The admin area is not affected.
 *
 * @package kitwp
 */

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
add_filter( 'show_admin_bar', '__return_false' );

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
