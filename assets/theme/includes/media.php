<?php
/**
 * Images: the same widths, format and markup as the static Next.js build (next/image).
 *
 * The static build serves WebP at KITWP_IMAGE_WIDTHS (quality 75) with width-descriptor srcsets. The same sizes
 * are registered here as kitk-<width>, so new uploads get them too, and the seeder attaches the static build's own
 * WebP files to the seeded images. WordPress 7.1's WebP output also saves a full-size .webp of each original:
 * harmless extra files.
 *
 * @package kitwp
 */

/**
 * The srcset widths of the static build.
 *
 * @return array<int, int>
 */
function kitwp_image_widths() {
	return KITWP_IMAGE_WIDTHS;
}

/**
 * Register one image size per static width (width only, never cropped).
 *
 * @return void
 */
function kitwp_image_sizes() {
	foreach ( kitwp_image_widths() as $kitwp_width ) {
		add_image_size( 'kitk-' . $kitwp_width, $kitwp_width, 0, false );
	}
}
add_action( 'after_setup_theme', 'kitwp_image_sizes' );

/**
 * Generate sub-sizes as WebP, like the static build.
 *
 * @param array<string, string> $formats Mime type map.
 * @return array<string, string>
 */
function kitwp_webp_output( $formats ) {
	$formats['image/jpeg'] = 'image/webp';
	$formats['image/png']  = 'image/webp';
	return $formats;
}
add_filter( 'image_editor_output_format', 'kitwp_webp_output' );

/**
 * WebP quality 75, as next/image.
 *
 * @param int    $quality   Quality.
 * @param string $mime_type Mime type.
 * @return int
 */
function kitwp_webp_quality( $quality, $mime_type = '' ) {
	return 'image/webp' === $mime_type ? 75 : $quality;
}
add_filter( 'wp_editor_set_quality', 'kitwp_webp_quality', 10, 2 );

/**
 * An <img> with the static build's attributes: alt, loading, width, height, decoding, style, sizes, srcset, src.
 *
 * @param int                  $id    Attachment ID.
 * @param string               $sizes The sizes attribute, copied from the static component.
 * @param array<string, mixed> $args  priority (bool, no lazy loading; also queue a preload), alt (overrides the
 *                                    media alt), width and height (the static component's fixed size), class,
 *                                    style, fill (bool, as next/image "fill": no size attributes, absolute).
 * @return string
 */
function kitwp_img( $id, $sizes, $args = [] ) {
	$id   = (int) $id;
	$meta = $id ? wp_get_attachment_metadata( $id ) : false;
	if ( ! $meta || empty( $meta['width'] ) ) {
		return '';
	}
	list( $srcset, $src ) = kitwp_img_srcset( $id, $meta );
	if ( ! array_key_exists( 'alt', $args ) ) {
		$args['alt'] = (string) get_post_meta( $id, '_wp_attachment_image_alt', true );
	}
	// Width and height attributes: the caller's, else what the static site prints for this image
	// (_kitk_attr_size, set by the seeder when it differs from the file), else the file's own size.
	$attr = explode( 'x', (string) get_post_meta( $id, '_kitk_attr_size', true ) );
	if ( ! isset( $args['width'] ) ) {
		$args['width'] = 2 === count( $attr ) ? (int) $attr[0] : (int) $meta['width'];
	}
	if ( ! isset( $args['height'] ) ) {
		$args['height'] = 2 === count( $attr ) ? (int) $attr[1] : (int) $meta['height'];
	}
	return kitwp_img_tag( $srcset, $src, $sizes, $args );
}

/**
 * An <img> for a theme image that has the static WebP widths beside it (assets/hero/sky.png-640.webp and so on).
 *
 * @param string               $base  Theme path without the width suffix, for example assets/hero/sky.png.
 * @param string               $sizes The sizes attribute.
 * @param array<string, mixed> $args  As kitwp_img(); alt defaults to "".
 * @return string
 */
function kitwp_asset_img( $base, $sizes, $args = [] ) {
	$srcset = [];
	$src    = '';
	foreach ( kitwp_image_widths() as $kitwp_width ) {
		$src      = kitwp_asset( $base . '-' . $kitwp_width . '.webp' );
		$srcset[] = $src . ' ' . $kitwp_width . 'w';
	}
	$args['alt'] = (string) ( $args['alt'] ?? '' );
	return kitwp_img_tag( $srcset, $src, $sizes, $args );
}

/**
 * Drop the srcset widths next/image leaves out: when sizes uses vw, it keeps only widths of at least the first
 * deviceSize times the smallest vw share. With deviceSize 640, "(max-width: 980px) 90vw, 520px" keeps 640 and up.
 *
 * @param string[] $srcset Entries like "https://.../x-kitk-256.webp 256w".
 * @param string   $sizes  Sizes attribute.
 * @return string[]
 */
function kitwp_srcset_for_sizes( $srcset, $sizes ) {
	if ( ! preg_match_all( '/(^|\s)(1?\d?\d)vw/', (string) $sizes, $m ) ) {
		return $srcset;
	}
	$min = KITWP_FIRST_DEVICE_SIZE * min( array_map( 'intval', $m[2] ) ) / 100;
	return array_values(
		array_filter(
			$srcset,
			static function ( $entry ) use ( $min ) {
				return (int) substr( (string) strrchr( $entry, ' ' ), 1 ) >= $min;
			}
		)
	);
}

/**
 * Build the <img> tag in the attribute order next/image prints.
 *
 * @param string[]             $srcset Srcset entries.
 * @param string               $src    Largest file.
 * @param string               $sizes  Sizes attribute.
 * @param array<string, mixed> $args   alt, priority, width, height, class, style, fill.
 * @return string
 */
function kitwp_img_tag( $srcset, $src, $sizes, $args ) {
	$fill = ! empty( $args['fill'] );
	$html = '<img alt="' . esc_attr( (string) ( $args['alt'] ?? '' ) ) . '"';
	if ( empty( $args['priority'] ) ) {
		$html .= ' loading="lazy"'; // Priority images load eagerly with no fetchpriority (as the Next 15 build); the template queues a preload.
	}
	if ( ! $fill ) {
		$html .= ' width="' . (int) ( $args['width'] ?? 0 ) . '" height="' . (int) ( $args['height'] ?? 0 ) . '"';
	}
	$html .= ' decoding="async" data-nimg="' . ( $fill ? 'fill' : '1' ) . '"';
	if ( ! empty( $args['class'] ) ) {
		$html .= ' class="' . esc_attr( $args['class'] ) . '"';
	}
	$extra = empty( $args['style'] ) ? '' : (string) $args['style'];
	if ( $fill ) {
		$style = 'position:absolute;height:100%;width:100%;left:0;top:0;right:0;bottom:0;' . ( '' === $extra ? '' : $extra . ';' ) . 'color:transparent';
	} else {
		$style = 'color:transparent' . ( '' === $extra ? '' : ';' . $extra );
	}
	$html  .= ' style="' . esc_attr( $style ) . '"';
	$srcset = kitwp_srcset_for_sizes( $srcset, $sizes );
	if ( $srcset ) {
		$html .= ' sizes="' . esc_attr( $sizes ) . '" srcset="' . esc_attr( implode( ', ', $srcset ) ) . '"';
	}
	return $html . ' src="' . esc_url( $src ) . '">';
}

/**
 * The srcset entries (static widths, as next/image) and the largest file for an attachment.
 *
 * @param int                       $id   Attachment ID.
 * @param array<string, mixed>|null $meta Attachment metadata, when the caller already has it.
 * @return array{0: string[], 1: string} Srcset entries and src.
 */
function kitwp_img_srcset( $id, $meta = null ) {
	$meta   = is_array( $meta ) ? $meta : wp_get_attachment_metadata( (int) $id );
	$src    = (string) wp_get_attachment_url( (int) $id );
	$base   = trailingslashit( dirname( $src ) );
	$srcset = [];
	$widths = kitwp_image_widths();
	foreach ( $widths as $kitwp_width ) {
		if ( empty( $meta['sizes'][ 'kitk-' . $kitwp_width ]['file'] ) ) {
			continue;
		}
		$url      = $base . $meta['sizes'][ 'kitk-' . $kitwp_width ]['file'];
		$srcset[] = $url . ' ' . $kitwp_width . 'w';
		$src      = $url;
	}
	// An upload narrower than the largest width has no size of that width: its original is the largest candidate.
	if ( empty( $meta['sizes'][ 'kitk-' . end( $widths ) ] ) && ! empty( $meta['width'] ) ) {
		$src      = (string) wp_get_attachment_url( (int) $id );
		$srcset[] = $src . ' ' . (int) $meta['width'] . 'w';
	}
	return [ $srcset, $src ];
}

/**
 * Queue a priority image for a preload link in <head>, as next/image "priority" does. Call before get_header().
 *
 * @param int    $id    Attachment ID.
 * @param string $sizes The same sizes value the <img> uses.
 * @return void
 */
function kitwp_preload_image( $id, $sizes ) {
	if ( (int) $id ) {
		$GLOBALS['kitwp_preloads'][] = [
			'id'    => (int) $id,
			'sizes' => (string) $sizes,
		];
	}
}

/**
 * Queue a theme image for a preload link: a single file (an SVG), or a base path with the static WebP widths.
 *
 * @param string $path  Theme path, for example assets/hero/wordmark.svg or assets/hero/sky.png.
 * @param string $sizes Sizes for a WebP set; empty for a single file.
 * @return void
 */
function kitwp_preload_asset( $path, $sizes = '' ) {
	$GLOBALS['kitwp_preloads'][] = [
		'asset' => (string) $path,
		'sizes' => (string) $sizes,
	];
}

/**
 * Attachment ID for a seeded static path, for example /photos/team/crew.jpg (stored in _kitk_source).
 *
 * @param string $source Static path.
 * @return int
 */
function kitwp_media_by_source( $source ) {
	$ids = get_posts(
		[
			'post_type'      => 'attachment',
			'post_status'    => 'inherit',
			'posts_per_page' => 1,
			'fields'         => 'ids',
			'meta_key'       => '_kitk_source', // phpcs:ignore WordPress.DB.SlowDBQuery.slow_db_query_meta_key -- seeding and lookups only.
			'meta_value'     => $source, // phpcs:ignore WordPress.DB.SlowDBQuery.slow_db_query_meta_value
		]
	);
	return $ids ? (int) $ids[0] : 0;
}
