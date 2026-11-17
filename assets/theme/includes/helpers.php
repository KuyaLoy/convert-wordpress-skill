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
		if ( ! preg_match( '/(^|\.)google\.[a-z.]+$/', $host ) ) {
			return ''; // Short links (maps.app.goo.gl) and other sites.
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

/**
 * The site's own domain without "www.", for mail headers (Message-ID, envelope sender check).
 *
 * @return string
 */
function kitwp_site_domain() {
	$host = defined( 'KITWP_DOMAIN' ) && '' !== KITWP_DOMAIN ? KITWP_DOMAIN : (string) wp_parse_url( home_url(), PHP_URL_HOST );
	return (string) preg_replace( '/^www\./', '', strtolower( $host ) );
}

/**
 * The agency badge for the site footer's bottom bar (call it where the static footer has its credits). Theme
 * Settings > Branding: "Agency badge" (image) and "Agency badge link" replace the defaults, "Hide agency badge"
 * removes it; the defaults are KITWP_SITE_BADGE* (from the profile's branding). Prints nothing without an image
 * or a link.
 *
 * @return void
 */
function kitwp_agency_badge() {
	if ( kitwp_setting( 'agency_badge_hide' ) ) {
		return;
	}
	$id  = (int) kitwp_setting( 'agency_badge' );
	$src = $id ? (string) wp_get_attachment_url( $id ) : ( '' !== KITWP_SITE_BADGE ? kitwp_asset( KITWP_SITE_BADGE ) : '' );
	$url = (string) ( kitwp_setting( 'agency_link' ) ? kitwp_setting( 'agency_link' ) : KITWP_SITE_BADGE_LINK );
	$alt = $id ? trim( (string) get_post_meta( $id, '_wp_attachment_image_alt', true ) ) : '';
	$alt = '' !== $alt ? $alt : KITWP_SITE_BADGE_ALT;
	if ( '' === $src || '' === $url ) {
		return;
	}
	/* translators: %s: the badge's alt text. */
	$label = sprintf( __( '%s (opens in a new tab)', 'kitwp' ), $alt );
	printf(
		'<a href="%1$s" target="_blank" rel="noopener noreferrer" class="shrink-0" data-kitwp-badge="agency" aria-label="%2$s"><img src="%3$s" alt="%4$s" loading="lazy" decoding="async" style="display:block;height:%5$dpx;width:auto"></a>',
		esc_url( $url ),
		esc_attr( $label ),
		esc_url( $src ),
		esc_attr( $alt ),
		(int) KITWP_SITE_BADGE_HEIGHT
	);
}
