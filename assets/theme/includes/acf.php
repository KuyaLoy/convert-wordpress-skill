<?php
/**
 * ACF PRO (or the free Secure Custom Fields) set-up: local JSON in the theme and the Theme Settings options page.
 *
 * Field groups live as JSON in acf-json/ (built by tools/acf/build_field_groups.py, keys group_kitk_*,
 * field_kitk_*, layout_kitk_*, never renamed once content is seeded). Theme Settings is an ACF options page in the
 * same folder (ui_options_page_kitk_theme_settings.json), so it shows in ACF > Options Pages and syncs with the
 * field groups (tools/acf/sync.php). The ACF menu is never hidden: on live it holds the licence page, the options
 * pages and the field groups.
 *
 * @package kitwp
 */

/**
 * Save field groups into the theme's acf-json folder.
 *
 * @return string
 */
function kitwp_acf_json_save_path() {
	return get_stylesheet_directory() . '/acf-json';
}
add_filter( 'acf/settings/save_json', 'kitwp_acf_json_save_path' );

/**
 * Load field groups from the theme's acf-json folder only.
 *
 * @param array<int, string> $paths Default load paths.
 * @return array<int, string>
 */
function kitwp_acf_json_load_paths( $paths ) {
	unset( $paths[0] );
	$paths[] = get_stylesheet_directory() . '/acf-json';
	return $paths;
}
add_filter( 'acf/settings/load_json', 'kitwp_acf_json_load_paths' );

/**
 * Fallback for the Theme Settings options page: ACF registers it from its JSON (ACF > Options Pages) before this
 * runs; only when ACF has not (its options pages UI switched off, or a fields plugin without it) is it registered
 * here, with the same slug and settings, so the page always exists and never twice.
 *
 * @return void
 */
function kitwp_acf_options_pages() {
	if ( ! function_exists( 'acf_add_options_page' ) ) {
		return;
	}
	if ( function_exists( 'acf_get_options_page' ) && acf_get_options_page( 'kitk-theme-settings' ) ) {
		return;
	}
	acf_add_options_page(
		[
			'page_title'      => __( 'Theme Settings', 'kitwp' ),
			'menu_title'      => __( 'Theme Settings', 'kitwp' ),
			'menu_slug'       => 'kitk-theme-settings',
			'capability'      => 'edit_pages',
			'position'        => 59,
			'icon_url'        => 'dashicons-admin-customizer',
			'redirect'        => false,
			'autoload'        => true,
			'update_button'   => __( 'Save settings', 'kitwp' ),
			'updated_message' => __( 'Theme Settings saved.', 'kitwp' ),
		]
	);
}
add_action( 'acf/init', 'kitwp_acf_options_pages', 20 );

/**
 * Read a Theme Settings value by field name.
 *
 * Reads through the field key (field_kitk_ts_<name>), so ACF always knows the field: formatting and the default
 * value work even for a setting nobody has saved yet. Reading by name returns nothing for a never-saved field.
 *
 * @param string $name Field name.
 * @return mixed
 */
function kitwp_setting( $name ) {
	return function_exists( 'get_field' ) ? get_field( 'field_kitk_ts_' . $name, 'option' ) : null;
}
