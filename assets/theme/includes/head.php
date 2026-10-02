<?php
/**
 * Head tags shared by every page, matching the static site's <head>. The viewport meta is in header.php.
 * Page-specific tags (title, description, canonical, Open Graph) come from Yoast. Image preloads: the files in
 * KITWP_PRELOAD_ASSETS on every page, then the priority images each template queues (as next/image "priority").
 *
 * @package kitwp
 */

/**
 * Print the preconnects, theme colour, favicon and font links. The font links are copied from the static <head>
 * exactly (same order, same URLs, & written as &amp;). If a Site Icon is set in Settings > General, WordPress
 * prints that instead of the theme favicon.
 *
 * @return void
 */
function kitwp_head_tags() {
	if ( KITWP_PRECONNECT_FONTS ) {
		echo '<link rel="preconnect" href="https://fonts.googleapis.com">' . "\n";
		echo '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">' . "\n";
	}
	echo '<meta name="theme-color" content="' . esc_attr( KITWP_BRAND_COLOUR ) . '">' . "\n";
	if ( ! has_site_icon() ) {
		// The static favicon set, from the theme's assets/brand/ (a file that is not there yet is left out).
		$kitwp_icons = [
			'favicon.svg'          => '<link rel="icon" href="%s" type="image/svg+xml">',
			'favicon-32.png'       => '<link rel="icon" href="%s" sizes="32x32" type="image/png">',
			'apple-touch-icon.png' => '<link rel="apple-touch-icon" href="%s">',
		];
		foreach ( $kitwp_icons as $kitwp_icon => $kitwp_tag ) {
			if ( file_exists( get_stylesheet_directory() . '/assets/brand/' . $kitwp_icon ) ) {
				printf( $kitwp_tag . "\n", esc_url( kitwp_asset( 'assets/brand/' . $kitwp_icon ) ) ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- fixed markup, the URL is escaped.
			}
		}
	}
	?>
{{FONT_LINKS}}
<?php
}
add_action( 'wp_head', 'kitwp_head_tags', 2 );

/**
 * The <html> attributes on the front end exactly as the static site (KITWP_HTML_ATTRIBUTES), whatever the Site
 * Language says; wp-admin keeps WordPress's own. Empty: WordPress's own everywhere.
 *
 * @param string $output Attributes WordPress built.
 * @return string
 */
function kitwp_html_attributes( $output ) {
	return ( '' !== KITWP_HTML_ATTRIBUTES && ! is_admin() ) ? KITWP_HTML_ATTRIBUTES : $output;
}
add_filter( 'language_attributes', 'kitwp_html_attributes' );

/**
 * Print the image preloads first in <head>, as the static site: the fixed theme files, then any priority image
 * queued with kitwp_preload_image() or kitwp_preload_asset(), in the order they were queued.
 *
 * @return void
 */
function kitwp_head_preloads() {
	foreach ( KITWP_PRELOAD_FONTS as $kitwp_file ) {
		if ( file_exists( get_stylesheet_directory() . '/' . ltrim( $kitwp_file, '/' ) ) ) {
			echo '<link rel="preload" href="' . esc_url( kitwp_asset( $kitwp_file ) ) . '" as="font" type="font/' . esc_attr( pathinfo( $kitwp_file, PATHINFO_EXTENSION ) ) . "\" crossorigin>\n";
		}
	}
	foreach ( KITWP_PRELOAD_ASSETS as $kitwp_file ) {
		if ( file_exists( get_stylesheet_directory() . '/' . ltrim( $kitwp_file, '/' ) ) ) {
			echo '<link rel="preload" as="image" href="' . esc_url( kitwp_asset( $kitwp_file ) ) . "\">\n";
		}
	}
	foreach ( (array) ( $GLOBALS['kitwp_preloads'] ?? [] ) as $kitwp_item ) {
		if ( isset( $kitwp_item['asset'] ) && '' === $kitwp_item['sizes'] ) {
			echo '<link rel="preload" as="image" href="' . esc_url( kitwp_asset( $kitwp_item['asset'] ) ) . "\">\n";
			continue;
		}
		if ( isset( $kitwp_item['asset'] ) ) {
			$kitwp_srcset = [];
			foreach ( KITWP_IMAGE_WIDTHS as $kitwp_width ) {
				$kitwp_srcset[] = kitwp_asset( $kitwp_item['asset'] . '-' . $kitwp_width . '.webp' ) . ' ' . $kitwp_width . 'w';
			}
		} else {
			list( $kitwp_srcset ) = kitwp_img_srcset( (int) $kitwp_item['id'] );
		}
		$kitwp_srcset = kitwp_srcset_for_sizes( $kitwp_srcset, $kitwp_item['sizes'] );
		if ( $kitwp_srcset ) {
			echo '<link rel="preload" as="image" imagesrcset="' . esc_attr( implode( ', ', $kitwp_srcset ) ) . '" imagesizes="' . esc_attr( $kitwp_item['sizes'] ) . "\">\n";
		}
	}
}
add_action( 'wp_head', 'kitwp_head_preloads', 0 );

/**
 * The static site's stylesheets (KITWP_STYLESHEETS) in its order, in place of the starter's own stylesheet.
 *
 * @return void
 */
function kitwp_static_styles() {
	if ( ! KITWP_STYLESHEETS ) {
		return;
	}
	$kitwp_theme_uri = get_template_directory_uri();
	foreach ( wp_styles()->queue as $kitwp_handle ) {
		$kitwp_src = (string) ( wp_styles()->registered[ $kitwp_handle ]->src ?? '' );
		if ( 0 === strpos( $kitwp_src, $kitwp_theme_uri ) || 0 === strpos( $kitwp_src, get_stylesheet_directory_uri() ) ) {
			wp_dequeue_style( $kitwp_handle );
		}
	}
	foreach ( KITWP_STYLESHEETS as $kitwp_i => $kitwp_file ) {
		$kitwp_path = get_stylesheet_directory() . '/' . ltrim( $kitwp_file, '/' );
		if ( file_exists( $kitwp_path ) ) {
			wp_enqueue_style( 'kitwp-static-' . $kitwp_i, kitwp_asset( $kitwp_file ), [], (string) filemtime( $kitwp_path ) );
		}
	}
}
add_action( 'wp_enqueue_scripts', 'kitwp_static_styles', 20 );

/**
 * The static site's inline <style> (KITWP_INLINE_CSS), before the stylesheets, as on the static page.
 *
 * @return void
 */
function kitwp_inline_styles() {
	$kitwp_css = '';
	foreach ( KITWP_INLINE_CSS as $kitwp_file ) {
		$kitwp_path = get_stylesheet_directory() . '/' . ltrim( $kitwp_file, '/' );
		if ( file_exists( $kitwp_path ) ) {
			$kitwp_css .= (string) file_get_contents( $kitwp_path ); // phpcs:ignore WordPress.WP.AlternativeFunctions.file_get_contents_file_get_contents -- a theme file.
		}
	}
	if ( '' !== $kitwp_css ) {
		$kitwp_css = str_replace( [ 'url(assets/', "url('assets/", 'url("assets/' ], [ 'url(' . kitwp_asset( 'assets/' ), "url('" . kitwp_asset( 'assets/' ), 'url("' . kitwp_asset( 'assets/' ) ], $kitwp_css );
		echo '<style>' . wp_strip_all_tags( $kitwp_css ) . "</style>\n"; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- the theme's own CSS, tags stripped.
	}
}
add_action( 'wp_head', 'kitwp_inline_styles', 7 );
