<?php
/**
 * Yoast SEO output matched to the static site's head: Open Graph type "website" and the static locale, robots
 * "index, follow" (or noindex) without Yoast's max-* directives, and the static robots.txt. Titles, descriptions,
 * social images, noindex and page types are per page in Yoast's fields (seeded by Tools > Seeder > SEO). Note:
 * WordPress core still adds max-image-preview:large through wp_robots; remove that core filter only if the static
 * head must match byte for byte.
 *
 * @package kitwp
 */

add_filter(
	'wpseo_opengraph_type',
	static function () {
		return 'website';
	}
);

add_filter(
	'wpseo_og_locale',
	static function () {
		return KITWP_OG_LOCALE;
	}
);

/**
 * Robots meta as the static site: index or noindex, follow or nofollow, nothing else.
 *
 * @param array<string, string> $robots Yoast's robots values.
 * @return array<string, string>
 */
function kitwp_seo_robots( $robots ) {
	return array_intersect_key( (array) $robots, array_flip( [ 'index', 'follow' ] ) );
}
add_filter( 'wpseo_robots_array', 'kitwp_seo_robots' );

/**
 * robots.txt as the static site (KITWP_ROBOTS_TXT), pointing to Yoast's sitemap. While "Discourage search
 * engines" is on (local, staging), WordPress's own blocking file is kept.
 *
 * @param string $output    robots.txt so far.
 * @param bool   $is_public Whether the site is public.
 * @return string
 */
function kitwp_seo_robots_txt( $output, $is_public ) {
	if ( ! $is_public ) {
		return $output;
	}
	return str_replace( '{site}', untrailingslashit( home_url() ), KITWP_ROBOTS_TXT );
}
add_filter( 'robots_txt', 'kitwp_seo_robots_txt', 999999, 2 );
