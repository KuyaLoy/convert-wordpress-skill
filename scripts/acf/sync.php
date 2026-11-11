<?php
/**
 * Sync the theme's ACF JSON into the database, exactly as ACF's own "Sync" link does (same ACF functions, same
 * rule): every field group, options page, post type and taxonomy whose JSON is not in the database yet, or is
 * newer than its database copy. Afterwards ACF > Field Groups and ACF > Options Pages show nothing under
 * "Sync available". Run it after build_field_groups.py writes JSON (locally, and on live after an upload):
 *
 *     wp eval-file _plan/tools/acf/sync.php            sync every pending item
 *     wp eval-file _plan/tools/acf/sync.php dry-run    only list what would sync
 *
 * A second run syncs nothing. The JSON files are not rewritten while importing (ACF's own sync does the same).
 *
 * @package kitwp
 */

if ( ! defined( 'WP_CLI' ) || ! function_exists( 'acf_get_local_json_files' ) || ! function_exists( 'acf_import_internal_post_type' ) ) {
	echo "Run with WP-CLI (wp eval-file) on a site with ACF PRO 6.2+ or Secure Custom Fields active.\n";
	return;
}

$kitwp_dry   = in_array( 'dry-run', (array) ( $args ?? [] ), true );
$kitwp_count = 0;
acf_update_setting( 'json', false );

foreach ( [ 'acf-field-group', 'acf-ui-options-page', 'acf-post-type', 'acf-taxonomy' ] as $kitwp_type ) {
	if ( ! post_type_exists( $kitwp_type ) ) {
		continue;
	}
	$kitwp_files = acf_get_local_json_files( $kitwp_type );
	if ( ! $kitwp_files ) {
		continue;
	}
	foreach ( acf_get_internal_post_type_posts( $kitwp_type ) as $kitwp_post ) {
		if ( ! empty( $kitwp_post['private'] ) || 'json' !== acf_maybe_get( $kitwp_post, 'local' ) || empty( $kitwp_files[ $kitwp_post['key'] ] ) ) {
			continue;
		}
		$kitwp_modified = (int) acf_maybe_get( $kitwp_post, 'modified' );
		$kitwp_pending  = ! $kitwp_post['ID'] || ( $kitwp_modified && $kitwp_modified > (int) get_post_modified_time( 'U', true, $kitwp_post['ID'] ) );
		if ( ! $kitwp_pending ) {
			continue;
		}
		++$kitwp_count;
		$kitwp_label = $kitwp_type . ' ' . $kitwp_post['key'] . ' (' . acf_maybe_get( $kitwp_post, 'title', '' ) . ')';
		if ( $kitwp_dry ) {
			WP_CLI::log( 'would sync ' . $kitwp_label );
			continue;
		}
		$kitwp_local       = json_decode( (string) file_get_contents( $kitwp_files[ $kitwp_post['key'] ] ), true ); // phpcs:ignore WordPress.WP.AlternativeFunctions.file_get_contents_file_get_contents -- a theme file.
		$kitwp_local['ID'] = $kitwp_post['ID'];
		$kitwp_result      = acf_import_internal_post_type( $kitwp_local, $kitwp_type );
		WP_CLI::log( 'synced ' . $kitwp_label . ' -> ID ' . (int) ( $kitwp_result['ID'] ?? 0 ) );
	}
}

if ( $kitwp_dry ) {
	WP_CLI::success( $kitwp_count ? $kitwp_count . ' item(s) would sync.' : 'Nothing to sync: the database matches the JSON.' );
} else {
	WP_CLI::success( $kitwp_count ? $kitwp_count . ' item(s) synced.' : 'Nothing to sync: the database matches the JSON.' );
}
