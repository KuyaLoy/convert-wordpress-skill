<?php
/**
 * Output helpers shared by the header, footer and sections. Site-specific components (icons, buttons, badges)
 * go next to these, each printing the same markup as the static component of the same name.
 *
 * @package kitwp
 */

/**
 * Theme Settings value with a fallback when the field is empty.
 *
 * @param string $name     Field name.
 * @param mixed  $fallback Value when empty.
 * @return mixed
 */
function kitwp_opt( $name, $fallback = '' ) {
	$value = kitwp_setting( $name );
	return ( null === $value || '' === $value || false === $value ) ? $fallback : $value;
}

/**
 * Phone number as shown (Theme Settings > Business > phone_display).
 *
 * @return string
 */
function kitwp_phone() {
	return (string) kitwp_opt( 'phone_display' );
}

/**
 * Phone number for tel: links, digits and + only (Theme Settings > Business > phone_tel).
 *
 * @return string
 */
function kitwp_tel() {
	return (string) preg_replace( '/[^0-9+]/', '', (string) kitwp_opt( 'phone_tel' ) );
}

/**
 * Replace the site-wide placeholders in a Theme Settings or page string.
 *
 * Built in: {phone} {tel} {email} {year} {legal_name} {company_number} {registration} (the last two as typed in
 * Theme Settings, empty when not filled). Add site tokens with the "kitwp_tokens" filter, or per call with $extra
 * (for example name and short for template pages).
 *
 * @param string                $text  Text with placeholders.
 * @param array<string, string> $extra Extra placeholder => value pairs, without braces.
 * @return string
 */
function kitwp_tokens( $text, $extra = [] ) {
	$map = [
		'{phone}'          => kitwp_phone(),
		'{tel}'            => kitwp_tel(),
		'{email}'          => (string) kitwp_opt( 'email' ),
		'{year}'           => wp_date( 'Y' ),
		'{legal_name}'     => (string) kitwp_opt( 'legal_name' ),
		'{company_number}' => (string) kitwp_opt( 'company_number' ),
		'{registration}'   => (string) kitwp_opt( 'registration' ),
	];
	foreach ( (array) apply_filters( 'kitwp_tokens', [] ) as $key => $value ) {
		$map[ '{' . $key . '}' ] = (string) $value;
	}
	foreach ( $extra as $key => $value ) {
		$map[ '{' . $key . '}' ] = (string) $value;
	}
	return strtr( (string) $text, $map );
}

/**
 * Inline HTML allowed in short copy fields (bold, emphasis, links, line breaks).
 *
 * @param string $html Field value.
 * @return string
 */
function kitwp_inline( $html ) {
	return wp_kses(
		(string) $html,
		[
			'b'      => [],
			'strong' => [],
			'em'     => [],
			'i'      => [],
			'br'     => [],
			'a'      => [
				'href'   => true,
				'target' => true,
				'rel'    => true,
			],
		]
	);
}

/**
 * Inline HTML from a field inside a tag, as a static Html component (<p>, <span>, <li>, <div>).
 *
 * @param string $tag   Tag name.
 * @param string $html  Field value.
 * @param string $class Class.
 * @return string
 */
function kitwp_html( $tag, $html, $class = '' ) {
	$tag = in_array( $tag, [ 'p', 'span', 'li', 'div' ], true ) ? $tag : 'p';
	return '<' . $tag . ( '' !== $class ? ' class="' . esc_attr( $class ) . '"' : '' ) . '>' . kitwp_inline( $html ) . '</' . $tag . '>';
}

/**
 * Material Symbols icon span (many static sites use the icon font). Always aria-hidden.
 *
 * @param string $name  Icon name.
 * @param string $class Extra class.
 * @return string
 */
function kitwp_icon( $name, $class = '' ) {
	return '<span class="' . esc_attr( trim( 'material-icons ' . $class ) ) . '" aria-hidden="true">' . esc_html( $name ) . '</span>';
}

/**
 * URL of a file in the theme.
 *
 * @param string $path Path relative to the theme root.
 * @return string
 */
function kitwp_asset( $path ) {
	return get_stylesheet_directory_uri() . '/' . ltrim( $path, '/' );
}

/**
 * Site-relative URL for links to this site ("/about/"), as on the static site. Other URLs are unchanged.
 *
 * @param string $url URL.
 * @return string
 */
function kitwp_rel_url( $url ) {
	$home = wp_parse_url( home_url( '/' ) );
	$link = wp_parse_url( (string) $url );
	if ( ! empty( $link['host'] ) && ! empty( $home['host'] ) && strtolower( $link['host'] ) === strtolower( $home['host'] ) ) {
		return wp_make_link_relative( $url );
	}
	return (string) $url;
}

/**
 * Start capturing markup that must have no whitespace between tags, like React output (whitespace between
 * inline-block elements adds gaps).
 *
 * @return void
 */
function kitwp_tight_start() {
	ob_start();
}

/**
 * Print the captured markup with line breaks and indentation between tags removed, tab-only gaps too (PHP's ?>
 * eats the newline and leaves the tabs), and whitespace at the start and end of the buffer. Spaces inside a line,
 * such as between an icon and its label, are kept.
 *
 * @return void
 */
function kitwp_tight_end() {
	echo preg_replace( [ '/>[ \t]*\R[ \t]*</', '/>\t+</', '/^\s+</', '/>\s+$/' ], [ '><', '><', '<', '>' ], (string) ob_get_clean() ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- markup was escaped when it was built.
}

/**
 * Rows of an ACF repeater or flexible field: ACF returns false or null when there are none, and (array) false
 * would give one empty row.
 *
 * @param mixed $value Field value.
 * @return array<int, mixed>
 */
function kitwp_rows( $value ) {
	return is_array( $value ) ? array_values( array_filter( $value, 'is_array' ) ) : [];
}

/**
 * A post's title as typed, without wptexturize (which turns "&" into "&#038;" and straight quotes into curly
 * ones), so escaped output matches the static site. Use it for menu labels too.
 *
 * @param int|WP_Post|null $post Post, default the current one.
 * @return string
 */
function kitwp_title( $post = null ) {
	return (string) get_post_field( 'post_title', $post ? $post : get_the_ID(), 'raw' );
}

/**
 * Published pages that use a page template, in menu order (the static content order). Grids and hubs loop over
 * these, so a new page shows up everywhere without editing a list.
 *
 * @param string $template Template file, for example page-templates/service.php.
 * @return array<int, int> Page IDs.
 */
function kitwp_template_pages( $template ) {
	return array_map(
		'intval',
		get_posts(
			[
				'post_type'      => 'page',
				'post_status'    => 'publish',
				'posts_per_page' => -1,
				'fields'         => 'ids',
				'orderby'        => 'menu_order',
				'order'          => 'ASC',
				'meta_key'       => '_wp_page_template', // phpcs:ignore WordPress.DB.SlowDBQuery.slow_db_query_meta_key -- a handful of pages.
				'meta_value'     => $template, // phpcs:ignore WordPress.DB.SlowDBQuery.slow_db_query_meta_value
			]
		)
	);
}

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
 * The site's own domain without "www.", for mail headers (Message-ID, envelope sender check).
 *
 * @return string
 */
function kitwp_site_domain() {
	$host = defined( 'KITWP_DOMAIN' ) && '' !== KITWP_DOMAIN ? KITWP_DOMAIN : (string) wp_parse_url( home_url(), PHP_URL_HOST );
	return (string) preg_replace( '/^www\./', '', strtolower( $host ) );
}
