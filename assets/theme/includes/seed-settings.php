<?php
/**
 * Seeder, Theme Settings: the business details, branding and other site-wide values (settings.json). Local copies
 * only.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

if ( 'local' !== wp_get_environment_type() ) {
	return;
}

/**
 * Top-level Theme Settings field keys by name, read from the field group JSON.
 *
 * @return array<string, array<string, mixed>>
 */
function kitwp_seed_settings_fields() {
	$json  = get_stylesheet_directory() . '/acf-json/group_kitk_theme_settings.json';
	$group = json_decode( (string) file_get_contents( $json ), true ); // phpcs:ignore WordPress.WP.AlternativeFunctions.file_get_contents_file_get_contents -- theme file.
	$out   = [];
	foreach ( (array) ( $group['fields'] ?? [] ) as $field ) {
		if ( ! empty( $field['name'] ) ) {
			$out[ $field['name'] ] = $field;
		}
	}
	return $out;
}

/**
 * Replace static image paths with attachment IDs in a seed value, using the field definition.
 *
 * @param mixed                $value Seed value.
 * @param array<string, mixed> $field ACF field.
 * @return mixed
 */
function kitwp_seed_resolve( $value, $field ) {
	if ( 'image' === $field['type'] ) {
		return is_string( $value ) && '' !== $value ? kitwp_media_by_source( $value ) : $value;
	}
	if ( 'true_false' === $field['type'] ) {
		return $value ? 1 : 0; // ACF stores false as nothing; 0 is stored.
	}
	if ( in_array( $field['type'], [ 'group', 'repeater' ], true ) && is_array( $value ) ) {
		$subs = [];
		foreach ( (array) $field['sub_fields'] as $sub ) {
			$subs[ $sub['name'] ] = $sub;
		}
		$fix = function ( $row ) use ( $subs ) {
			foreach ( $row as $k => $v ) {
				if ( isset( $subs[ $k ] ) ) {
					$row[ $k ] = kitwp_seed_resolve( $v, $subs[ $k ] );
				}
			}
			return $row;
		};
		return 'group' === $field['type'] ? $fix( $value ) : array_map( $fix, $value );
	}
	return $value;
}

/**
 * Write the Theme Settings values. Only fields whose stored value differs are written.
 *
 * @return array<string, int>
 */
function kitwp_seed_settings() {
	$report = [
		'updated' => 0,
		'same'    => 0,
		'unknown' => 0,
	];
	$fields = kitwp_seed_settings_fields();
	foreach ( kitwp_seed_json( 'settings.json' ) as $name => $value ) {
		if ( 'site_icon' === $name ) {
			// WordPress's Site Icon (Settings > General), from a seeded square image of at least 512 px.
			$icon = is_string( $value ) && '' !== $value ? kitwp_media_by_source( $value ) : 0;
			if ( ! $icon ) {
				++$report['unknown'];
			} elseif ( (int) get_option( 'site_icon' ) === $icon ) {
				++$report['same'];
			} else {
				update_option( 'site_icon', $icon );
				++$report['updated'];
			}
			continue;
		}
		if ( ! isset( $fields[ $name ] ) ) {
			++$report['unknown'];
			continue;
		}
		$field  = $fields[ $name ];
		$value  = kitwp_seed_resolve( $value, $field );
		$stored = kitwp_seed_named( get_field( $field['key'], 'option', false ), $field );
		if ( 'group' === $field['type'] && is_array( $value ) && is_array( $stored ) ) {
			$stored = array_intersect_key( $stored, $value ); // Compare only the sub fields the seed sets.
		}
		$saved = null !== get_option( 'options_' . $name, null );
		if ( $saved && kitwp_seed_same( $stored, $value, $field ) ) {
			++$report['same'];
			continue;
		}
		update_field( $field['key'], $value, 'option' );
		++$report['updated'];
		$GLOBALS['kitwp_seed_changed'][] = $name;
	}
	return kitwp_seed_agency_badge( $report );
}

/**
 * Theme Settings > Branding pre-filled with the profile's agency badge: the theme's default files (KITWP_SITE_BADGE,
 * KITWP_EMAIL_BADGE) go into the Media Library once and fill "Agency badge" and "Email badge", the default link
 * fills "Agency badge link". Only empty fields are filled: a value set in wp-admin is kept.
 *
 * @param array<string, int> $report The settings report so far.
 * @return array<string, int>
 */
function kitwp_seed_agency_badge( $report ) {
	require_once ABSPATH . 'wp-admin/includes/file.php';
	require_once ABSPATH . 'wp-admin/includes/media.php';
	require_once ABSPATH . 'wp-admin/includes/image.php';
	add_filter( 'upload_mimes', 'kitwp_seed_svg_mime' );
	add_filter( 'wp_check_filetype_and_ext', 'kitwp_seed_svg_filetype', 10, 3 );
	$images = [
		'agency_badge' => [ KITWP_SITE_BADGE, KITWP_SITE_BADGE_ALT ],
		'email_badge'  => [ KITWP_EMAIL_BADGE, KITWP_EMAIL_BADGE_ALT ],
	];
	foreach ( $images as $name => [ $rel, $alt ] ) {
		$file = get_stylesheet_directory() . '/' . $rel;
		if ( '' === $rel || kitwp_setting( $name ) || ! is_readable( $file ) ) {
			continue;
		}
		$id = kitwp_media_by_source( 'theme:' . $rel );
		if ( ! $id ) {
			$tmp = wp_tempnam( basename( $rel ) );
			$id  = copy( $file, $tmp ) ? media_handle_sideload(
				[
					'name'     => basename( $rel ),
					'tmp_name' => $tmp,
				],
				0,
				'',
				[ 'post_title' => $alt ]
			) : 0;
			if ( ! $id || is_wp_error( $id ) ) {
				wp_delete_file( $tmp );
				++$report['unknown'];
				continue;
			}
			update_post_meta( $id, '_kitk_source', 'theme:' . $rel );
			update_post_meta( $id, '_wp_attachment_image_alt', $alt );
		}
		update_field( 'field_kitk_ts_' . $name, (int) $id, 'option' );
		++$report['updated'];
	}
	if ( '' !== KITWP_SITE_BADGE_LINK && ! kitwp_setting( 'agency_link' ) ) {
		update_field( 'field_kitk_ts_agency_link', KITWP_SITE_BADGE_LINK, 'option' );
		++$report['updated'];
	}
	remove_filter( 'upload_mimes', 'kitwp_seed_svg_mime' );
	remove_filter( 'wp_check_filetype_and_ext', 'kitwp_seed_svg_filetype', 10 );
	return $report;
}

/**
 * Compare a stored value (already keyed by field names) with a seed value.
 *
 * @param mixed                $stored Stored value.
 * @param mixed                $value  Seed value.
 * @param array<string, mixed> $field  ACF field.
 * @return bool
 */
function kitwp_seed_same( $stored, $value, $field ) {
	unset( $field );
	return wp_json_encode( kitwp_seed_norm( $stored ) ) === wp_json_encode( kitwp_seed_norm( $value ) );
}

/**
 * Turn an unformatted ACF value (sub fields keyed by field key) into the seed shape (keyed by name), recursively.
 *
 * @param mixed                $stored Unformatted value.
 * @param array<string, mixed> $field  ACF field.
 * @return mixed
 */
function kitwp_seed_named( $stored, $field ) {
	if ( ! in_array( $field['type'], [ 'group', 'repeater' ], true ) ) {
		return $stored;
	}
	$convert = function ( $row ) use ( $field ) {
		$named = [];
		foreach ( (array) $field['sub_fields'] as $sub ) {
			$named[ $sub['name'] ] = kitwp_seed_named( $row[ $sub['key'] ] ?? null, $sub );
		}
		return $named;
	};
	if ( 'group' === $field['type'] ) {
		return $convert( (array) $stored );
	}
	return array_values( array_map( $convert, (array) $stored ) );
}

/**
 * Normalise a value for comparison (strings, sorted keys, booleans as 0/1).
 *
 * @param mixed $v Value.
 * @return mixed
 */
function kitwp_seed_norm( $v ) {
	if ( is_array( $v ) ) {
		$out = [];
		foreach ( $v as $k => $x ) {
			$out[ $k ] = kitwp_seed_norm( $x );
		}
		if ( array_keys( $out ) !== range( 0, count( $out ) - 1 ) ) {
			ksort( $out );
		}
		return $out;
	}
	if ( is_bool( $v ) ) {
		return $v ? '1' : '0';
	}
	return null === $v ? '' : (string) $v;
}
