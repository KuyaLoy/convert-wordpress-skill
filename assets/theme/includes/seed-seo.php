<?php
/**
 * Seeder, SEO: Yoast titles, descriptions and images (seo.json, og-images.json) and the old site's redirects
 * (redirects.json, in the Redirection plugin). Local copies only.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

if ( 'local' !== wp_get_environment_type() ) {
	return;
}

/**
 * Yoast SEO, as the static site's head, from seo.json:
 *   { "logo_source": "/assets/logo-mark.png",            static path of the company logo and default share image
 *     "options": { "title-404-wpseo": "...", ... },       Yoast option overrides on top of the defaults below
 *     "page_meta": { "/about/": { "_yoast_wpseo_schema_page_type": "AboutPage", "_kitk_schema_name": "About X" } } }
 * plus og-images.json ({ "/path/": "/static/image.jpg" }) for each page's social image. Defaults: head clean-up on
 * (feeds, shortlinks, REST and oEmbed links, RSD, generator, emoji); campaign URL and permalink clean-up OFF
 * (campaign URLs and their tags must keep working); author, date, attachment and format archives off; categories
 * and tags noindex. Values are written only where they differ.
 *
 * @return array<string, int>
 */
function kitwp_seed_seo() {
	$report = [
		'changed' => 0,
		'same'    => 0,
	];
	if ( ! class_exists( 'WPSEO_Options' ) ) {
		return [ 'yoast seo not active' => 1 ];
	}
	$seo     = kitwp_seed_json( 'seo.json' );
	$logo    = ! empty( $seo['logo_source'] ) ? (int) kitwp_media_by_source( (string) $seo['logo_source'] ) : 0;
	$name    = (string) kitwp_opt( 'business_name', get_bloginfo( 'name' ) );
	$options = array_merge(
		[
			'remove_feed_global'            => true,
			'remove_feed_global_comments'   => true,
			'remove_feed_post_comments'     => true,
			'remove_feed_authors'           => true,
			'remove_feed_categories'        => true,
			'remove_feed_tags'              => true,
			'remove_feed_custom_taxonomies' => true,
			'remove_feed_post_types'        => true,
			'remove_feed_search'            => true,
			'remove_atom_rdf_feeds'         => true,
			'remove_shortlinks'             => true,
			'remove_rest_api_links'         => true,
			'remove_rsd_wlw_links'          => true,
			'remove_oembed_links'           => true,
			'remove_generator'              => true,
			'remove_emoji_scripts'          => true,
			'remove_powered_by_header'      => true,
			'remove_pingback_header'        => true,
			'clean_campaign_tracking_urls'  => false,
			'clean_permalinks'              => false,
			'enable_xml_sitemap'            => true,
			'disable-author'                => true,
			'disable-date'                  => true,
			'disable-attachment'            => true,
			'disable-post_format'           => true,
			'noindex-tax-category'          => true,
			'noindex-tax-post_tag'          => true,
			'noindex-tax-post_format'       => true,
			'breadcrumbs-enable'            => false,
			'company_or_person'             => 'company',
			'company_name'                  => $name,
			'website_name'                  => $name,
			'company_logo'                  => $logo ? (string) wp_get_attachment_url( $logo ) : '',
			'company_logo_id'               => $logo,
			'og_default_image'              => $logo ? (string) wp_get_attachment_url( $logo ) : '',
			'og_default_image_id'           => $logo,
			'opengraph'                     => true,
			'twitter'                       => true,
		],
		(array) ( $seo['options'] ?? [] )
	);
	foreach ( $options as $key => $value ) {
		if ( (string) WPSEO_Options::get( $key ) === (string) $value ) {
			++$report['same'];
			continue;
		}
		WPSEO_Options::set( $key, $value );
		++$report['changed'];
		$GLOBALS['kitwp_seed_changed'][] = $key;
	}
	$meta = [];
	foreach ( (array) kitwp_seed_json( 'og-images.json' ) as $path => $source ) {
		$image = (int) kitwp_media_by_source( (string) $source );
		if ( $image ) {
			$meta[ (string) $path ] = [
				'_yoast_wpseo_opengraph-image-id' => (string) $image,
				'_yoast_wpseo_opengraph-image'    => (string) wp_get_attachment_url( $image ),
			];
		}
	}
	foreach ( (array) ( $seo['page_meta'] ?? [] ) as $path => $fields ) {
		$meta[ (string) $path ] = array_merge( $meta[ (string) $path ] ?? [], (array) $fields );
	}
	foreach ( $meta as $path => $fields ) {
		$page = get_page_by_path( trim( $path, '/' ) );
		if ( ! $page ) {
			continue;
		}
		foreach ( $fields as $key => $value ) {
			if ( (string) get_post_meta( $page->ID, $key, true ) === (string) $value ) {
				++$report['same'];
				continue;
			}
			update_post_meta( $page->ID, $key, $value );
			++$report['changed'];
		}
	}
	return $report;
}

/**
 * Old URLs into the Redirection plugin (Tools > Redirection), from _setup/seed/redirects.json
 * ([{ "from": "/old/", "to": "/new/", "group": "Old site pages" }, { "from": "^/x(/.*)?$", "to": "/", "regex": true }]):
 * the old pages the static .htaccess redirected plus the old archive URLs (_plan/OLD-SITE-URLS.md). All 301, query
 * strings passed on (campaign tags reach the new page), trailing slash and case ignored. A source that already has a
 * redirect is left as it is, so edits made in Redirection are kept.
 *
 * @return array<string, int>
 */
function kitwp_seed_redirects() {
	global $wpdb;
	$report = [
		'created' => 0,
		'kept'    => 0,
	];
	if ( ! class_exists( 'Red_Item' ) || ! class_exists( 'Red_Group' ) || ! function_exists( 'red_set_options' ) ) {
		return [ 'redirection plugin not active' => 1 ];
	}
	// Redirection creates its tables in its own setup screen, not on activation.
	$kitwp_table = $wpdb->prefix . 'redirection_items';
	if ( $wpdb->get_var( $wpdb->prepare( 'SHOW TABLES LIKE %s', $kitwp_table ) ) !== $kitwp_table ) { // phpcs:ignore WordPress.DB.DirectDatabaseQuery -- checks that the plugin's table exists; no API for it.
		return [ 'redirection not set up yet: finish its setup in Tools > Redirection (or wp redirection database install), then run this step again' => 1 ];
	}
	red_set_options(
		[
			'flag_query'    => 'pass',
			'flag_case'     => true,
			'flag_trailing' => true,
		]
	);
	$groups = [];
	foreach ( (array) Red_Group::get_all() as $group ) {
		$groups[ (string) $group['name'] ] = (int) $group['id'];
	}
	foreach ( (array) kitwp_seed_json( 'redirects.json' ) as $row ) {
		$name = (string) ( $row['group'] ?? 'Old site pages' );
		if ( empty( $groups[ $name ] ) ) {
			$created         = Red_Group::create( $name, 1 );
			$groups[ $name ] = $created ? (int) $created->get_id() : 0;
		}
		$regex = ! empty( $row['regex'] );
		$found = $wpdb->get_var( $wpdb->prepare( "SELECT id FROM {$wpdb->prefix}redirection_items WHERE url = %s OR url = %s LIMIT 1", (string) $row['from'], untrailingslashit( (string) $row['from'] ) ) ); // phpcs:ignore WordPress.DB.DirectDatabaseQuery -- seeder lookup in the plugin's table.
		if ( $found ) {
			++$report['kept'];
			continue;
		}
		$item = Red_Item::create(
			[
				'url'         => (string) $row['from'],
				'regex'       => $regex,
				'match_type'  => 'url',
				'action_type' => 'url',
				'action_code' => 301,
				'action_data' => [ 'url' => (string) $row['to'] ],
				'group_id'    => $groups[ $name ],
				'title'       => '',
			]
		);
		if ( ! is_wp_error( $item ) ) {
			++$report['created'];
		}
	}
	return $report;
}
