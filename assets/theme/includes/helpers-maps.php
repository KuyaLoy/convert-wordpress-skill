<?php
/**
 * Google Maps from one Theme Settings or page field: the embed URL (kitwp_map_src()) and the iframe for a page the
 * static site does not have (kitwp_map_iframe()).
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

/**
 * A Google Maps embed src for an iframe attribute. esc_url() would turn "&" into "&#038;" and the URL would no
 * longer match the static one, so the value is cleaned with esc_url_raw() and escaped for the attribute.
 *
 * @param string $src Embed URL.
 * @return string Attribute-safe value.
 */
function kitwp_iframe_src( $src ) {
	return esc_attr( esc_url_raw( (string) $src ) );
}

/**
 * The live Google Maps embed URL for one field that takes whatever the client has: a Google Maps link (from the
 * address bar), the embed code (Share > Embed a map) or a plain address. An embed URL is kept as it is; a place,
 * search or coordinates link and an address become a keyless embed (maps.google.com/maps?q=...&output=embed).
 * Empty or not usable (a short maps.app.goo.gl link cannot be read without a network call): the default, which is
 * the city until the address is confirmed (KITWP_MAP_DEFAULT, site.json "map_default").
 *
 * @param string|null $value   The field value; null reads Theme Settings > Business "Map".
 * @param string|null $default What to show when the value is empty or not usable; null = KITWP_MAP_DEFAULT.
 * @return string Embed URL (raw: print it with kitwp_iframe_src()), or '' when there is nothing to show.
 */
function kitwp_map_src( $value = null, $default = null ) {
	$value   = trim( (string) ( null === $value ? kitwp_setting( 'map' ) : $value ) );
	$default = trim( (string) ( null === $default ? KITWP_MAP_DEFAULT : $default ) );
	$src     = kitwp_map_embed_url( $value );
	if ( '' === $src && '' !== $default && $default !== $value ) {
		$src = kitwp_map_embed_url( $default );
	}
	return $src;
}

/**
 * One value (embed code, Google Maps link or address) as an embed URL; '' when it cannot be used.
 *
 * @param string $value Field value.
 * @return string
 */
function kitwp_map_embed_url( $value ) {
	$value = trim( (string) $value );
	if ( preg_match( '/<iframe\b[^>]*?\ssrc\s*=\s*(["\'])(.*?)\1/is', $value, $m ) ) {
		$value = trim( html_entity_decode( $m[2], ENT_QUOTES ) );
	}
	if ( '' === $value ) {
		return '';
	}
	$query = '';
	if ( preg_match( '#^(https?:)?//#i', $value ) ) {
		$parts = wp_parse_url( $value );
		$host  = strtolower( (string) ( $parts['host'] ?? '' ) );
		$path  = (string) ( $parts['path'] ?? '' );
		// Google itself only: google.com or a country domain (google.de, google.co.uk, google.com.au), or a subdomain of
		// one. Short links (maps.app.goo.gl) and other sites, google.evil.example too, are not usable.
		if ( ! preg_match( '/(^|\.)google\.(com|[a-z]{2}|com?\.[a-z]{2})$/', $host ) ) {
			return '';
		}
		if ( str_starts_with( $path, '/maps/embed' ) ) {
			return 'https:' === substr( $value, 0, 6 ) ? $value : 'https:' . preg_replace( '#^(https?:)?#i', '', $value );
		}
		parse_str( (string) ( $parts['query'] ?? '' ), $args );
		if ( ! empty( $args['q'] ) && is_string( $args['q'] ) ) {
			$query = $args['q'];
		} elseif ( ! empty( $args['query'] ) && is_string( $args['query'] ) ) {
			$query = $args['query'];
		} elseif ( preg_match( '#/maps/(?:place|search)/([^/@]+)#', $path, $p ) ) {
			$query = urldecode( str_replace( '+', ' ', $p[1] ) );
		} elseif ( preg_match( '#/@(-?[\d.]+),(-?[\d.]+)#', $path, $c ) ) {
			$query = $c[1] . ',' . $c[2];
		}
	} else {
		$query = (string) preg_replace( '/\s+/', ' ', wp_strip_all_tags( $value ) );
	}
	$query = trim( $query );
	return '' === $query ? '' : 'https://maps.google.com/maps?q=' . rawurlencode( $query ) . '&output=embed';
}

/**
 * A live Google Maps iframe for a page or section the static site does not have (copied sections keep their own
 * iframe markup and only take kitwp_map_src() as the src). Lazy, no referrer, a title for screen readers.
 *
 * @param string|null           $value As kitwp_map_src().
 * @param array<string, string> $attrs title, class, width, height, style.
 * @return string
 */
function kitwp_map_iframe( $value = null, $attrs = [] ) {
	$src = kitwp_map_src( $value );
	if ( '' === $src ) {
		return '';
	}
	$attrs = array_merge(
		[
			'title'  => 'Map: ' . kitwp_opt( 'business_name', get_bloginfo( 'name' ) ),
			'class'  => '',
			'width'  => '600',
			'height' => '450',
			'style'  => 'border:0',
		],
		$attrs
	);
	$html = '<iframe src="' . kitwp_iframe_src( $src ) . '"';
	foreach ( [ 'title', 'class', 'width', 'height', 'style' ] as $name ) {
		if ( '' !== (string) $attrs[ $name ] ) {
			$html .= ' ' . $name . '="' . esc_attr( (string) $attrs[ $name ] ) . '"';
		}
	}
	return $html . ' loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>';
}
