<?php
/**
 * Seeder, menus: the static navigation as WordPress menus (menus.json). Local copies only.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

if ( 'local' !== wp_get_environment_type() ) {
	return;
}

/**
 * Build the five menus and assign their locations. A menu is rebuilt only when its items differ.
 *
 * @return array<string, int>
 */
function kitwp_seed_menus() {
	$report    = [
		'rebuilt' => 0,
		'same'    => 0,
	];
	$locations = get_theme_mod( 'nav_menu_locations', [] );
	foreach ( kitwp_seed_json( 'menus.json' ) as $location => $menu ) {
		$wanted = kitwp_seed_menu_rows( (array) $menu['items'] );
		$obj    = wp_get_nav_menu_object( $menu['name'] );
		$id     = $obj ? (int) $obj->term_id : (int) wp_create_nav_menu( $menu['name'] );
		$current = $obj ? kitwp_seed_menu_current( $id ) : [];
		if ( $obj && $current === $wanted ) {
			++$report['same'];
		} else {
			$diff = array_values( array_diff( $wanted, $current ) );
			$GLOBALS['kitwp_seed_menu_changed'][] = $location . ( $diff ? ' (' . $diff[0] . ' / ' . ( array_values( array_diff( $current, $wanted ) )[0] ?? '' ) . ')' : '' );
			foreach ( (array) wp_get_nav_menu_items( $id ) as $old ) {
				wp_delete_post( $old->ID, true );
			}
			kitwp_seed_menu_add( $id, (array) $menu['items'], 0 );
			++$report['rebuilt'];
		}
		$locations[ $location ] = $id;
	}
	set_theme_mod( 'nav_menu_locations', $locations );
	return $report;
}

/**
 * Where a menu row points: the page with that slug when it exists, otherwise a site-relative custom link.
 *
 * @param array<string, mixed> $row Seed row.
 * @return array<string, mixed>
 */
function kitwp_seed_menu_target( $row ) {
	if ( ! empty( $row['url'] ) ) {
		return [
			'type' => 'custom',
			'url'  => $row['url'],
		];
	}
	$page = get_page_by_path( (string) $row['slug'] );
	if ( $page ) {
		return [
			'type'      => 'post_type',
			'object'    => 'page',
			'object_id' => (int) $page->ID,
		];
	}
	return [
		'type' => 'custom',
		'url'  => home_url( '/' . trim( (string) $row['slug'], '/' ) . '/' ),
	];
}

/**
 * Flat, comparable list of the wanted rows.
 *
 * @param array<int, array<string, mixed>> $items Seed items.
 * @param int                              $depth Depth.
 * @return array<int, string>
 */
function kitwp_seed_menu_rows( $items, $depth = 0 ) {
	$rows = [];
	foreach ( $items as $row ) {
		$target = kitwp_seed_menu_target( $row );
		$rows[] = implode( '|', [ $depth, $row['title'], $target['url'] ?? 'page:' . $target['object_id'], $row['classes'] ?? '', $row['icon'] ?? '' ] );
		if ( ! empty( $row['children'] ) ) {
			$rows = array_merge( $rows, kitwp_seed_menu_rows( $row['children'], $depth + 1 ) );
		}
	}
	return $rows;
}

/**
 * The same flat list for a menu as it is stored now.
 *
 * @param int $menu_id Menu ID.
 * @return array<int, string>
 */
function kitwp_seed_menu_current( $menu_id ) {
	$rows  = [];
	$depth = [];
	foreach ( (array) wp_get_nav_menu_items( $menu_id ) as $item ) {
		$d                   = $item->menu_item_parent ? ( $depth[ (int) $item->menu_item_parent ] ?? 0 ) + 1 : 0;
		$depth[ $item->ID ]  = $d;
		$url                 = 'custom' === $item->type ? $item->url : 'page:' . (int) $item->object_id;
		$icon                = function_exists( 'get_field' ) ? (string) get_field( 'field_kitk_menu_item_icon', $item->ID ) : '';
		$rows[]              = implode( '|', [ $d, html_entity_decode( $item->title, ENT_QUOTES, 'UTF-8' ), $url, implode( ' ', array_filter( (array) $item->classes ) ), $icon ] );
	}
	return $rows;
}

/**
 * Add seed items to a menu.
 *
 * @param int                              $menu_id Menu ID.
 * @param array<int, array<string, mixed>> $items   Seed items.
 * @param int                              $parent  Parent menu item ID.
 * @return void
 */
function kitwp_seed_menu_add( $menu_id, $items, $parent ) {
	foreach ( $items as $row ) {
		$target = kitwp_seed_menu_target( $row );
		$args   = [
			'menu-item-title'     => $row['title'],
			'menu-item-status'    => 'publish',
			'menu-item-parent-id' => $parent,
			'menu-item-classes'   => $row['classes'] ?? '',
			'menu-item-type'      => $target['type'],
		];
		if ( 'custom' === $target['type'] ) {
			$args['menu-item-url'] = $target['url'];
		} else {
			$args['menu-item-object']    = $target['object'];
			$args['menu-item-object-id'] = $target['object_id'];
		}
		$item_id = wp_update_nav_menu_item( $menu_id, 0, $args );
		if ( is_wp_error( $item_id ) ) {
			continue;
		}
		if ( ! empty( $row['icon'] ) && function_exists( 'update_field' ) ) {
			update_field( 'field_kitk_menu_item_icon', $row['icon'], $item_id );
		}
		if ( ! empty( $row['children'] ) ) {
			kitwp_seed_menu_add( $menu_id, $row['children'], (int) $item_id );
		}
	}
}
