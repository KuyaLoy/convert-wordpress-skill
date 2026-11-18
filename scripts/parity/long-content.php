<?php
/**
 * Long-content test page for design-check.mjs --long: a copy of one page with every text field filled long, to
 * prove the design holds after the client edits. CLI only, local sites only (WP_ENVIRONMENT_TYPE "local").
 *
 *   php long-content.php make /about/ [--factor=3]   a published copy at /kit-long-test-about/ (noindex)
 *   php long-content.php list                         the test pages this script made (IDs and paths)
 *   php long-content.php remove                       deletes exactly those IDs (each carries _kitwp_long_test)
 *
 * Long means: the title and every text, textarea and link title about three times as long (empty ones filled too),
 * every WYSIWYG and the page content repeated, repeater rows doubled (up to the field's maximum). Images, choices,
 * numbers and links stay as they are. The copy keeps the page template; a template chosen by slug (page-about.php)
 * does not apply to it. Remove the test pages before the launch package (P5).
 *
 * @package kitwp
 */

if ( 'cli' !== PHP_SAPI ) {
	http_response_code( 403 );
	exit;
}

/**
 * The host (and port) of a URL, before WordPress is loaded; "localhost" when there is none.
 *
 * @param string $url The URL.
 * @return string
 */
function kitwp_url_host( $url ) {
	$parts = parse_url( $url ); // phpcs:ignore WordPress.WP.AlternativeFunctions.parse_url_parse_url -- WordPress is not loaded yet.
	if ( empty( $parts['host'] ) || false !== strpos( $url, '{{' ) ) {
		return 'localhost';
	}
	return $parts['host'] . ( isset( $parts['port'] ) ? ':' . $parts['port'] : '' );
}

$kitwp_args = array_slice( $argv, 1 );
$kitwp_cmd  = $kitwp_args[0] ?? '';
$kitwp_dir  = __DIR__;
for ( $kitwp_i = 0; $kitwp_i < 8 && ! file_exists( $kitwp_dir . '/wp-load.php' ); $kitwp_i++ ) {
	$kitwp_dir = dirname( $kitwp_dir );
}
if ( ! file_exists( $kitwp_dir . '/wp-load.php' ) || ! in_array( $kitwp_cmd, array( 'make', 'list', 'remove' ), true ) ) {
	fwrite( STDERR, "usage: php long-content.php make /route/ [--factor=3] | list | remove (inside a WordPress theme's tests/parity)\n" );
	exit( 2 );
}
// The local address from parity.config.json next to this file (its "wp"), so permalinks come out right.
$kitwp_cfg              = json_decode( (string) file_get_contents( __DIR__ . '/parity.config.json' ), true );
$kitwp_host             = kitwp_url_host( is_array( $kitwp_cfg ) ? (string) ( $kitwp_cfg['wp'] ?? '' ) : '' );
$_SERVER['HTTP_HOST']   = $kitwp_host;
$_SERVER['REQUEST_URI'] = '/';
define( 'WP_USE_THEMES', false );
require $kitwp_dir . '/wp-load.php';

if ( 'local' !== wp_get_environment_type() ) {
	fwrite( STDERR, "FAIL long-content: refused: WP_ENVIRONMENT_TYPE is not local\n" );
	exit( 2 );
}

/**
 * A text about $factor times as long, made of its own words (empty: a plain filler sentence).
 *
 * @param mixed $text   The value.
 * @param int   $factor How much longer.
 * @return mixed
 */
function kitwp_long_text( $text, $factor ) {
	if ( ! is_string( $text ) ) {
		return $text;
	}
	$text = trim( $text );
	if ( '' === $text ) {
		$text = 'Long content test: a much longer text than the design shows';
	}
	$target = max( mb_strlen( $text ) * $factor, 40 );
	$out    = $text;
	while ( mb_strlen( $out ) < $target ) {
		$out .= ' ' . $text;
	}
	return $out;
}

/**
 * HTML repeated $factor times.
 *
 * @param mixed $html   The value.
 * @param int   $factor How many times.
 * @return mixed
 */
function kitwp_long_html( $html, $factor ) {
	if ( ! is_string( $html ) || '' === trim( $html ) ) {
		return is_string( $html ) ? '<p>' . kitwp_long_text( '', $factor ) . '</p>' : $html;
	}
	return implode( "\n", array_fill( 0, $factor, $html ) );
}

/**
 * One ACF value made long, by field type (raw values: rows keyed by sub field key).
 *
 * @param array $field  The ACF field.
 * @param mixed $value  Its raw value.
 * @param int   $factor How much longer.
 * @param int   $count  Fields changed (by reference).
 * @return mixed
 */
function kitwp_long_value( $field, $value, $factor, &$count ) {
	$type = $field['type'] ?? '';
	if ( in_array( $type, array( 'text', 'textarea' ), true ) ) {
		++$count;
		return kitwp_long_text( $value, $factor );
	}
	if ( 'wysiwyg' === $type ) {
		++$count;
		return kitwp_long_html( $value, $factor );
	}
	if ( 'link' === $type && is_array( $value ) && isset( $value['title'] ) ) {
		++$count;
		$value['title'] = kitwp_long_text( $value['title'], $factor );
		return $value;
	}
	if ( 'group' === $type && is_array( $value ) ) {
		foreach ( (array) ( $field['sub_fields'] ?? array() ) as $sub ) {
			$value[ $sub['key'] ] = kitwp_long_value( $sub, $value[ $sub['key'] ] ?? '', $factor, $count );
		}
		return $value;
	}
	if ( 'repeater' === $type && is_array( $value ) ) {
		foreach ( $value as $i => $row ) {
			foreach ( (array) ( $field['sub_fields'] ?? array() ) as $sub ) {
				$value[ $i ][ $sub['key'] ] = kitwp_long_value( $sub, $row[ $sub['key'] ] ?? '', $factor, $count );
			}
		}
		$rows = array_merge( array_values( $value ), array_values( $value ) );
		$max  = (int) ( $field['max'] ?? 0 );
		return $max > 0 ? array_slice( $rows, 0, max( $max, count( $value ) ) ) : $rows;
	}
	if ( 'flexible_content' === $type && is_array( $value ) ) {
		$layouts = array();
		foreach ( (array) ( $field['layouts'] ?? array() ) as $layout ) {
			$layouts[ $layout['name'] ] = $layout;
		}
		foreach ( $value as $i => $row ) {
			$name = $row['acf_fc_layout'] ?? '';
			foreach ( (array) ( $layouts[ $name ]['sub_fields'] ?? array() ) as $sub ) {
				$value[ $i ][ $sub['key'] ] = kitwp_long_value( $sub, $row[ $sub['key'] ] ?? '', $factor, $count );
			}
		}
		return $value;
	}
	return $value;
}

$kitwp_ids = array_map( 'intval', (array) get_option( 'kitwp_long_test_ids', array() ) );

if ( 'list' === $kitwp_cmd ) {
	echo 'OK long-content: ' . count( $kitwp_ids ) . " test page(s)\n";
	foreach ( $kitwp_ids as $kitwp_id ) {
		echo '- ' . $kitwp_id . ' ' . wp_make_link_relative( (string) get_permalink( $kitwp_id ) ) . ( get_post_meta( $kitwp_id, '_kitwp_long_test', true ) ? '' : ' (no marker: left alone)' ) . "\n";
	}
	exit( 0 );
}

if ( 'remove' === $kitwp_cmd ) {
	$kitwp_done = array();
	foreach ( $kitwp_ids as $kitwp_id ) {
		if ( get_post_meta( $kitwp_id, '_kitwp_long_test', true ) && wp_delete_post( $kitwp_id, true ) ) {
			$kitwp_done[] = $kitwp_id;
		}
	}
	update_option( 'kitwp_long_test_ids', array_values( array_diff( $kitwp_ids, $kitwp_done ) ), false );
	echo 'OK long-content: removed ' . count( $kitwp_done ) . ' test page(s)' . ( $kitwp_done ? ' (IDs ' . implode( ', ', $kitwp_done ) . ')' : '' ) . "\n";
	exit( 0 );
}

// make.
$kitwp_route = '';
foreach ( array_slice( $kitwp_args, 1 ) as $kitwp_a ) {
	if ( 0 !== strpos( $kitwp_a, '--' ) ) {
		$kitwp_route = trim( $kitwp_a, '/' );
		break;
	}
}
$kitwp_factor = 3;
foreach ( $kitwp_args as $kitwp_a ) {
	if ( 0 === strpos( $kitwp_a, '--factor=' ) ) {
		$kitwp_factor = max( 2, (int) substr( $kitwp_a, 9 ) );
	}
}
$kitwp_src = '' === $kitwp_route ? get_post( (int) get_option( 'page_on_front' ) ) : get_page_by_path( $kitwp_route );
if ( ! $kitwp_src ) {
	fwrite( STDERR, "FAIL long-content: no page at /{$kitwp_route}/\n" );
	exit( 1 );
}
$kitwp_slug = 'kit-long-test-' . ( $kitwp_src->post_name ? $kitwp_src->post_name : 'home' );
$kitwp_old  = get_page_by_path( $kitwp_slug );
if ( $kitwp_old && get_post_meta( $kitwp_old->ID, '_kitwp_long_test', true ) ) {
	echo 'OK long-content: /' . $kitwp_slug . '/ already there (ID ' . (int) $kitwp_old->ID . "): remove first to make it again\n";
	exit( 0 );
}
$kitwp_new = wp_insert_post(
	array(
		'post_type'    => 'page',
		'post_status'  => 'publish',
		'post_name'    => $kitwp_slug,
		'post_title'   => kitwp_long_text( $kitwp_src->post_title, $kitwp_factor ),
		'post_content' => '' === trim( $kitwp_src->post_content ) ? '' : kitwp_long_html( $kitwp_src->post_content, $kitwp_factor ),
		'meta_input'   => array(
			'_kitwp_long_test'                 => 1,
			'_wp_page_template'                => get_post_meta( $kitwp_src->ID, '_wp_page_template', true ),
			'_yoast_wpseo_meta-robots-noindex' => 1,
		),
	),
	true
);
if ( is_wp_error( $kitwp_new ) ) {
	fwrite( STDERR, 'FAIL long-content: ' . $kitwp_new->get_error_message() . "\n" );
	exit( 1 );
}
$kitwp_ids[] = (int) $kitwp_new;
update_option( 'kitwp_long_test_ids', array_values( array_unique( $kitwp_ids ) ), false );
$kitwp_count = 0;
if ( function_exists( 'get_field_objects' ) ) {
	foreach ( (array) get_field_objects( $kitwp_src->ID, false ) as $kitwp_field ) {
		update_field( $kitwp_field['key'], kitwp_long_value( $kitwp_field, $kitwp_field['value'], $kitwp_factor, $kitwp_count ), $kitwp_new );
	}
}
$kitwp_slug = get_post_field( 'post_name', $kitwp_new );
echo 'OK long-content: /' . $kitwp_slug . '/ (ID ' . (int) $kitwp_new . ') from /' . $kitwp_route . "/, {$kitwp_count} fields made long. Next: node design-check.mjs --long --routes=/{$kitwp_slug}/\n";
