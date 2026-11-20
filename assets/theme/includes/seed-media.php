<?php
/**
 * Seeder, media: the static site's images in the Media Library (media.json), with their alt text and sizes, SVG
 * allowed while seeding. Local copies only.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

if ( 'local' !== wp_get_environment_type() ) {
	return;
}

/**
 * Store the width and height attributes the static site prints for an image when they differ from the file
 * (media.json attrWidth/attrHeight, for example when the static code prints a fixed 600 x 600). Returns true when
 * the meta changed.
 *
 * @param int                  $id   Attachment ID.
 * @param array<string, mixed> $item media.json entry.
 * @return bool
 */
function kitwp_seed_media_attr_size( $id, $item ) {
	$want = isset( $item['attrWidth'], $item['attrHeight'] ) ? (int) $item['attrWidth'] . 'x' . (int) $item['attrHeight'] : '';
	if ( (string) get_post_meta( $id, '_kitk_attr_size', true ) === $want ) {
		return false;
	}
	if ( '' === $want ) {
		delete_post_meta( $id, '_kitk_attr_size' );
	} else {
		update_post_meta( $id, '_kitk_attr_size', $want );
	}
	return true;
}

/**
 * Import the images in media.json with the static build's WebP files as the kitk-<width> sizes.
 *
 * @return array<string, int>
 */
function kitwp_seed_media() {
	require_once ABSPATH . 'wp-admin/includes/file.php';
	require_once ABSPATH . 'wp-admin/includes/media.php';
	require_once ABSPATH . 'wp-admin/includes/image.php';

	$report = [
		'created' => 0,
		'updated' => 0,
		'skipped' => 0,
		'failed'  => 0,
	];
	$files  = trailingslashit( kitwp_seed_dir() ) . 'files';

	// The static WebP files are attached below, so WordPress makes no sizes of its own for seeded images.
	add_filter( 'intermediate_image_sizes_advanced', '__return_empty_array', 99 );
	add_filter( 'big_image_size_threshold', '__return_false', 99 );
	// SVG logos from the static build go into the Media Library too; SVG uploads stay closed outside the seeder.
	add_filter( 'upload_mimes', 'kitwp_seed_svg_mime' );
	add_filter( 'wp_check_filetype_and_ext', 'kitwp_seed_svg_filetype', 10, 3 );

	foreach ( kitwp_seed_json( 'media.json' ) as $item ) {
		$existing = kitwp_media_by_source( $item['src'] );
		if ( $existing ) {
			if ( kitwp_seed_media_attr_size( $existing, $item ) ) {
				++$report['updated'];
			} else {
				++$report['skipped'];
			}
			continue;
		}
		$original = $files . $item['src'];
		$tmp      = wp_tempnam( basename( $item['src'] ) );
		if ( ! is_readable( $original ) || ! copy( $original, $tmp ) ) {
			++$report['failed'];
			continue;
		}
		$id = media_handle_sideload(
			[
				'name'     => basename( $item['src'] ),
				'tmp_name' => $tmp,
			],
			0,
			'',
			[ 'post_title' => (string) $item['alt'] ]
		);
		if ( is_wp_error( $id ) ) {
			wp_delete_file( $tmp );
			++$report['failed'];
			continue;
		}
		update_post_meta( $id, '_kitk_source', $item['src'] );
		update_post_meta( $id, '_wp_attachment_image_alt', (string) $item['alt'] );
		foreach ( (array) ( $item['meta'] ?? [] ) as $kitwp_key => $kitwp_value ) {
			update_post_meta( $id, '_kitk_' . sanitize_key( (string) $kitwp_key ), $kitwp_value ); // Extra flags the theme reads, for example flush_right.
		}
		kitwp_seed_media_attr_size( $id, $item );

		// Copy the static WebP widths next to the original and register them as the kitk-* sizes.
		$meta = wp_get_attachment_metadata( $id );
		$dir  = dirname( (string) get_attached_file( $id ) );
		$name = pathinfo( (string) get_attached_file( $id ), PATHINFO_FILENAME );
		$meta = is_array( $meta ) ? $meta : [];
		if ( empty( $meta['sizes'] ) ) {
			$meta['sizes'] = [];
		}
		foreach ( (array) ( $item['variants'] ?? [] ) as $width => $variant ) { // None for an SVG.
			$from   = $files . $variant;
			$target = $name . '-kitk-' . $width . '.webp';
			if ( ! is_readable( $from ) || ! copy( $from, $dir . '/' . $target ) ) {
				continue;
			}
			$size = wp_getimagesize( $dir . '/' . $target );
			$meta['sizes'][ 'kitk-' . $width ] = [
				'file'      => $target,
				'width'     => $size ? (int) $size[0] : (int) $width,
				'height'    => $size ? (int) $size[1] : 0,
				'mime-type' => 'image/webp',
				'filesize'  => (int) filesize( $dir . '/' . $target ),
			];
		}
		wp_update_attachment_metadata( $id, $meta );
		++$report['created'];
	}

	remove_filter( 'intermediate_image_sizes_advanced', '__return_empty_array', 99 );
	remove_filter( 'big_image_size_threshold', '__return_false', 99 );
	remove_filter( 'upload_mimes', 'kitwp_seed_svg_mime' );
	remove_filter( 'wp_check_filetype_and_ext', 'kitwp_seed_svg_filetype', 10 );
	return $report;
}

/**
 * Allow SVG while the seeder imports media (only then).
 *
 * @param array<string, string> $mimes Allowed types.
 * @return array<string, string>
 */
function kitwp_seed_svg_mime( $mimes ) {
	$mimes['svg'] = 'image/svg+xml';
	return $mimes;
}

/**
 * WordPress cannot read an SVG's type from its content: trust the .svg extension while the seeder imports media.
 *
 * @param array<string, mixed> $data     Type check result.
 * @param string               $file     Full path.
 * @param string               $filename File name.
 * @return array<string, mixed>
 */
function kitwp_seed_svg_filetype( $data, $file, $filename ) {
	unset( $file );
	if ( 'svg' === strtolower( pathinfo( (string) $filename, PATHINFO_EXTENSION ) ) ) {
		$data['ext']  = 'svg';
		$data['type'] = 'image/svg+xml';
	}
	return $data;
}
