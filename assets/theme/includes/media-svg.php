<?php
/**
 * SVG images from the Media Library: their size, printing one inline (a logo the static markup has as an inline
 * <svg>) and sanitising it first.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

/**
 * Width and height of an SVG attachment: what the static code prints (_kitk_attr_size), else the file's own
 * width and height attributes, else its viewBox.
 *
 * @param int $id Attachment ID.
 * @return array{0: int, 1: int}
 */
function kitwp_svg_size( $id ) {
	$attr = explode( 'x', (string) get_post_meta( (int) $id, '_kitk_attr_size', true ) );
	if ( 2 === count( $attr ) ) {
		return [ (int) $attr[0], (int) $attr[1] ];
	}
	$file = (string) get_attached_file( (int) $id );
	$head = is_readable( $file ) ? (string) file_get_contents( $file, false, null, 0, 4096 ) : ''; // phpcs:ignore WordPress.WP.AlternativeFunctions.file_get_contents_file_get_contents -- local media file.
	return kitwp_svg_size_of( $head );
}

/**
 * Width and height from SVG markup: its width and height attributes, else its viewBox; [0, 0] when neither.
 *
 * @param string $svg SVG markup (the start of the file is enough).
 * @return array{0: int, 1: int}
 */
function kitwp_svg_size_of( $svg ) {
	if ( ! preg_match( '/<svg\b[^>]*>/i', (string) $svg, $tag ) ) {
		return [ 0, 0 ];
	}
	$w = preg_match( '/\swidth\s*=\s*["\']([\d.]+)(?:px)?["\']/i', $tag[0], $mw ) ? (float) $mw[1] : 0;
	$h = preg_match( '/\sheight\s*=\s*["\']([\d.]+)(?:px)?["\']/i', $tag[0], $mh ) ? (float) $mh[1] : 0;
	if ( $w && $h ) {
		return [ (int) round( $w ), (int) round( $h ) ];
	}
	if ( preg_match( '/\sviewBox\s*=\s*["\']\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)\s*["\']/i', $tag[0], $vb ) ) {
		return [ (int) round( (float) $vb[1] ), (int) round( (float) $vb[2] ) ];
	}
	return [ 0, 0 ];
}

/**
 * An SVG from the Media Library printed inline, for a logo the static markup has as an inline <svg>: the markup
 * stays 1:1 and the client can still swap the logo in Theme Settings. The file is sanitised (kitwp_svg_clean()).
 * Not an SVG (the client uploaded a PNG): the <img> instead.
 *
 * @param int                  $id   Attachment ID (an image field's value).
 * @param array<string, mixed> $args For the <img> fallback: as kitwp_img(), plus sizes.
 * @return string
 */
function kitwp_inline_svg( $id, $args = [] ) {
	$id = (int) $id;
	if ( ! $id ) {
		return '';
	}
	if ( 'image/svg+xml' !== get_post_mime_type( $id ) ) {
		return kitwp_img( $id, (string) ( $args['sizes'] ?? '' ), $args );
	}
	$file = (string) get_attached_file( $id );
	$svg  = is_readable( $file ) ? (string) file_get_contents( $file ) : ''; // phpcs:ignore WordPress.WP.AlternativeFunctions.file_get_contents_file_get_contents -- local media file.
	return kitwp_svg_clean( $svg );
}

/**
 * Sanitise SVG markup for printing inline: from the first <svg> to the last </svg>, without comments, elements that
 * run or load code or other documents (<script>, <foreignObject>, <iframe>, <embed>, <object>, <handler>), on*
 * event attributes, href / xlink:href values other than "#..." or a raster data image, and animation values
 * (to, from, by, values) that set a javascript: or data: URL (an <animate> or <set> can turn a link into one).
 *
 * @param string $svg SVG markup.
 * @return string
 */
function kitwp_svg_clean( $svg ) {
	$svg   = (string) $svg;
	$start = stripos( $svg, '<svg' );
	$end   = strripos( $svg, '</svg>' );
	if ( false === $start || false === $end || $end < $start ) {
		return '';
	}
	$svg   = substr( $svg, $start, $end - $start + 6 );
	$svg   = (string) preg_replace( '#<!--.*?-->#s', '', $svg );
	$svg   = (string) preg_replace( '#<!\[CDATA\[.*?\]\]>#s', '', $svg );
	$block = 'script|foreignObject|iframe|embed|object|handler';
	$svg   = (string) preg_replace( '#<(' . $block . ')\b.*?</\1\s*>#is', '', $svg );
	$svg   = (string) preg_replace( '#</?(?:' . $block . ')\b[^>]*>#i', '', $svg );
	// An attribute may follow a "/" as well as a space (<svg/onload=...>).
	$svg = (string) preg_replace( '#[\s/]+on[a-z]+\s*=\s*("[^"]*"|\'[^\']*\'|[^\s>]+)#i', '', $svg );
	$svg = (string) preg_replace_callback(
		'#\s+((?:xlink:)?href|to|from|by|values)\s*=\s*("([^"]*)"|\'([^\']*)\'|([^\s>]+))#i',
		static function ( $m ) {
			$raw   = '' !== $m[3] ? $m[3] : ( '' !== ( $m[4] ?? '' ) ? $m[4] : ( $m[5] ?? '' ) );
			$value = trim( html_entity_decode( $raw, ENT_QUOTES | ENT_HTML5, 'UTF-8' ) );
			// Browsers ignore control characters and spaces inside a scheme ("java\tscript:").
			$bare = strtolower( (string) preg_replace( '/[\x00-\x20]+/', '', $value ) );
			if ( 'href' === strtolower( substr( $m[1], -4 ) ) ) {
				return ( '' === $value || '#' === $value[0] || preg_match( '#^data:image/(png|jpe?g|gif|webp);#i', $value ) ) ? $m[0] : '';
			}
			return preg_match( '#(^|[;\s])(javascript|vbscript|data):#', $bare ) ? '' : $m[0];
		},
		$svg
	);
	return trim( $svg );
}
