<?php
/**
 * Seeder, pages: template pages (template-pages.json) and flexible pages and posts (pages.json). Local copies only.
 *
 * The exporters in _plan/tools/seed/ turn the static content into final field values, so this file only writes
 * them. A page is written only when its seed data changed since the last run (hash in _kitk_seed_hash), so a
 * second run changes nothing. Values the seeder resolves: "media:/static/path.jpg" (attachment by _kitk_source)
 * and "page:<slug>" (page ID). Site rules that build rows (for example a static Blocks component that picks a
 * layout by content shape) go in the "kitwp_seed_expand_row" filter, so this file stays generic.
 *
 * @package kitwp
 */

if ( 'local' !== wp_get_environment_type() ) {
	return;
}

/**
 * Resolve seed placeholders: "media:/photos/x.jpg" to an attachment ID, "page:<slug>" to a page ID, recursively.
 *
 * @param mixed $value Seed value.
 * @return mixed
 */
function kitwp_seed_placeholders( $value ) {
	if ( is_array( $value ) ) {
		return array_map( 'kitwp_seed_placeholders', $value );
	}
	if ( is_string( $value ) && 0 === strpos( $value, 'media:' ) ) {
		return kitwp_media_by_source( substr( $value, 6 ) );
	}
	if ( is_string( $value ) && 0 === strpos( $value, 'page:' ) ) {
		$page = get_page_by_path( substr( $value, 5 ) );
		return $page ? (int) $page->ID : 0;
	}
	return $value;
}

/**
 * Create a page or post by slug (or find it), with a template and order. Only changed values are written.
 *
 * @param string $slug     Slug (path for pages).
 * @param string $title    Title.
 * @param string $template Page template file, or 'default'.
 * @param int    $order    Menu order.
 * @param string $type     page or post.
 * @return int
 */
function kitwp_seed_upsert_page( $slug, $title, $template = 'default', $order = 0, $type = 'page' ) {
	$post = get_page_by_path( $slug, OBJECT, $type );
	$data = [
		'post_type'   => $type,
		'post_status' => 'publish',
		'post_title'  => $title,
		'post_name'   => basename( $slug ),
		'menu_order'  => (int) $order,
	];
	if ( $post ) {
		$id = (int) $post->ID;
		if ( $post->post_title !== $title || (int) $post->menu_order !== (int) $order || 'publish' !== $post->post_status ) {
			$data['ID'] = $id;
			wp_update_post( $data );
		}
	} else {
		$id = (int) wp_insert_post( $data );
	}
	if ( 'page' === $type && $template && get_post_meta( $id, '_wp_page_template', true ) !== $template ) {
		update_post_meta( $id, '_wp_page_template', $template );
	}
	return $id;
}

/**
 * Write ACF fields (by key: field_kitk_<group>_<name>) and post meta on a page, only when the payload changed.
 *
 * @param int                   $id     Page ID.
 * @param string                $group  Field key group, for example "service" or "ps".
 * @param array<string, mixed>  $fields Field name => value (already resolved).
 * @param array<string, string> $meta   Extra post meta (Yoast title, description, noindex).
 * @return bool True when written.
 */
function kitwp_seed_write_page( $id, $group, $fields, $meta = [] ) {
	$hash = md5( (string) wp_json_encode( [ $fields, $meta ] ) );
	if ( get_post_meta( $id, '_kitk_seed_hash', true ) === $hash ) {
		return false;
	}
	foreach ( $fields as $name => $value ) {
		update_field( 'field_kitk_' . $group . '_' . $name, $value, $id );
	}
	foreach ( $meta as $key => $value ) {
		update_post_meta( $id, $key, $value );
	}
	update_post_meta( $id, '_kitk_seed_hash', $hash );
	return true;
}

/**
 * Yoast meta for a seed entry's "seo" block.
 *
 * @param array<string, mixed> $seo title, description, noindex.
 * @return array<string, string>
 */
function kitwp_seed_seo_meta( $seo ) {
	return [
		'_yoast_wpseo_title'               => (string) ( $seo['title'] ?? '' ),
		'_yoast_wpseo_metadesc'            => (string) ( $seo['description'] ?? '' ),
		'_yoast_wpseo_meta-robots-noindex' => empty( $seo['noindex'] ) ? '0' : '1',
	];
}

/**
 * Template pages from template-pages.json:
 *   [{ "slug": "example-service", "title": "Example Service", "template": "page-templates/service.php", "order": 1,
 *      "group": "service", "fields": { "hero_h1": "...", "hero_image": "media:/assets/x.png", "related": ["page:a"] },
 *      "seo": { "title": "...", "description": "..." } }]
 * Every page is created first, then the fields are written, so "page:" links to pages later in the file resolve
 * in the same run.
 *
 * @return array<string, int>
 */
function kitwp_seed_template_pages() {
	$report = [
		'written' => 0,
		'same'    => 0,
	];
	$pages  = (array) kitwp_seed_json( 'template-pages.json' );
	$ids    = [];
	foreach ( $pages as $p ) {
		$ids[ $p['slug'] ] = kitwp_seed_upsert_page( (string) $p['slug'], (string) $p['title'], (string) ( $p['template'] ?? 'default' ), (int) ( $p['order'] ?? 0 ) );
	}
	foreach ( $pages as $p ) {
		$fields = (array) kitwp_seed_placeholders( (array) ( $p['fields'] ?? [] ) );
		if ( kitwp_seed_write_page( $ids[ $p['slug'] ], (string) $p['group'], $fields, kitwp_seed_seo_meta( (array) ( $p['seo'] ?? [] ) ) ) ) {
			++$report['written'];
		} else {
			++$report['same'];
		}
	}
	return $report;
}

/**
 * Flexible pages and posts from pages.json:
 *   [{ "slug": "about", "title": "About", "kind": "page", "front": false, "posts_page": false,
 *      "seo": { "title": "...", "description": "...", "noindex": false },
 *      "crumbs": { "hide": 0, "label": "", "parent_label": "", "parent_url": "" },
 *      "card": { "photo": "media:/photos/x.jpg", "summary": "" },
 *      "sections": [ { "acf_fc_layout": "page_head", "h1": "...", ... } ] }]
 * Rows go into the Page Sections field (field_kitk_ps_page_sections); "front" makes the page the front page and
 * "posts_page" the posts page (a /blog/ the static site did not have).
 *
 * @return array<string, int>
 */
function kitwp_seed_flex_pages() {
	$report = [
		'written' => 0,
		'same'    => 0,
	];
	$pages  = (array) kitwp_seed_json( 'pages.json' );
	$ids    = [];
	foreach ( $pages as $p ) {
		$type              = 'post' === ( $p['kind'] ?? 'page' ) ? 'post' : 'page';
		$ids[ $p['slug'] ] = kitwp_seed_upsert_page( (string) $p['slug'], (string) $p['title'], 'page' === $type ? 'default' : '', 0, $type );
	}
	foreach ( $pages as $p ) {
		$id   = $ids[ $p['slug'] ];
		$rows = [];
		foreach ( (array) ( $p['sections'] ?? [] ) as $row ) {
			$expanded = apply_filters( 'kitwp_seed_expand_row', null, $row, $p );
			$rows     = array_merge( $rows, is_array( $expanded ) ? $expanded : [ $row ] );
		}
		$crumbs = (array) ( $p['crumbs'] ?? [] );
		$fields = [
			'page_sections'       => kitwp_seed_placeholders( $rows ),
			'crumbs_hide'         => empty( $crumbs['hide'] ) ? 0 : 1,
			'crumbs_label'        => (string) ( $crumbs['label'] ?? '' ),
			'crumbs_parent_label' => (string) ( $crumbs['parent_label'] ?? '' ),
			'crumbs_parent_url'   => (string) ( $crumbs['parent_url'] ?? '' ),
		];
		if ( isset( $p['card'] ) ) {
			$fields['card_photo']   = kitwp_seed_placeholders( (string) ( $p['card']['photo'] ?? '' ) );
			$fields['card_summary'] = (string) ( $p['card']['summary'] ?? '' );
		}
		if ( kitwp_seed_write_page( $id, 'ps', $fields, kitwp_seed_seo_meta( (array) ( $p['seo'] ?? [] ) ) ) ) {
			++$report['written'];
		} else {
			++$report['same'];
		}
		if ( ! empty( $p['front'] ) && ( 'page' !== get_option( 'show_on_front' ) || (int) get_option( 'page_on_front' ) !== $id ) ) {
			update_option( 'show_on_front', 'page' );
			update_option( 'page_on_front', $id );
		}
		if ( ! empty( $p['posts_page'] ) && (int) get_option( 'page_for_posts' ) !== $id ) {
			update_option( 'page_for_posts', $id );
		}
	}
	return $report;
}
