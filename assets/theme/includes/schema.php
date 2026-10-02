<?php
/**
 * JSON-LD as the static site prints it: the business on every page, then what the page shows: Service (pages on
 * the templates in the "kitwp_schema_service_templates" filter), an area business (the location template), the
 * Yoast page type (Schema tab: About page, Contact page) or Article (posts), one FAQPage for every FAQ printed on
 * the page, and the BreadcrumbList of the breadcrumb trail. Sections report what they print with
 * kitwp_schema_add(); the blocks are printed at the end of the page. Yoast's own graph is off, so search engines
 * see the same markup as on the static site. Compare every route's JSON-LD with the static build.
 *
 * @package kitwp
 */

add_filter( 'wpseo_json_ld_output', '__return_false' );

/**
 * Note something the page shows, for its JSON-LD. Call it from the partial that prints it.
 *
 * @param string $type  faq (rows with question, answer) or crumbs (rows with name, path).
 * @param array  $items Rows.
 * @return void
 */
function kitwp_schema_add( $type, $items ) {
	foreach ( (array) $items as $item ) {
		$GLOBALS['kitwp_schema'][ $type ][] = $item;
	}
}

/**
 * Absolute URL for a site path, on the site's own domain.
 *
 * @param string $path Path such as /about/.
 * @return string
 */
function kitwp_schema_url( $path ) {
	return untrailingslashit( home_url() ) . '/' . ltrim( (string) $path, '/' );
}

/**
 * Phone in international form for the JSON-LD: a leading 0 becomes +<country code>.
 *
 * @return string
 */
function kitwp_schema_tel() {
	$tel = kitwp_tel();
	return ( '' !== $tel && '0' === $tel[0] && '' !== KITWP_COUNTRY_CODE ) ? '+' . KITWP_COUNTRY_CODE . substr( $tel, 1 ) : $tel;
}

/**
 * The business block, as the static org schema. Image: Theme Settings "schema_image", else the site icon.
 *
 * @return array<string, mixed>
 */
function kitwp_schema_org() {
	$site    = untrailingslashit( home_url() );
	$address = (array) kitwp_opt( 'address', [] );
	$image   = (int) kitwp_opt( 'schema_image', 0 );
	$org     = [
		'@context'  => 'https://schema.org',
		'@type'     => KITWP_SCHEMA_TYPE,
		'@id'       => $site . '/#org',
		'name'      => (string) kitwp_opt( 'business_name', get_bloginfo( 'name' ) ),
		'legalName' => (string) kitwp_opt( 'legal_name' ),
		'url'       => $site,
		'telephone' => kitwp_schema_tel(),
		'email'     => (string) kitwp_opt( 'email' ),
		'image'     => $image ? (string) wp_get_attachment_url( $image ) : (string) get_site_icon_url(),
		'logo'      => get_theme_file_uri( 'assets/brand/logo.svg' ),
	];
	if ( '' !== KITWP_PRICE_RANGE ) {
		$org['priceRange'] = KITWP_PRICE_RANGE;
	}
	$org['address']                   = [
		'@type'           => 'PostalAddress',
		'addressLocality' => (string) ( $address['locality'] ?? '' ),
		'addressRegion'   => (string) ( $address['region'] ?? '' ),
		'postalCode'      => (string) ( $address['postcode'] ?? '' ),
		'addressCountry'  => (string) ( $address['country'] ?? '' ),
	];
	if ( '' !== KITWP_AREA_SERVED ) {
		$org['areaServed'] = [
			'@type' => 'City',
			'name'  => KITWP_AREA_SERVED,
		];
	}
	if ( KITWP_OPENING_HOURS ) {
		$org['openingHoursSpecification'] = array_map(
			static function ( $row ) {
				return [ '@type' => 'OpeningHoursSpecification' ] + $row;
			},
			KITWP_OPENING_HOURS
		);
	}
	return (array) apply_filters( 'kitwp_schema_org', kitwp_schema_clean( $org ) );
}

/**
 * Drop empty values from a JSON-LD block (a value nobody has filled is left out, not printed as ""), and an object
 * left with nothing but its @type.
 *
 * @param array<string, mixed> $block Block.
 * @return array<string, mixed>
 */
function kitwp_schema_clean( $block ) {
	foreach ( $block as $key => $value ) {
		if ( is_array( $value ) ) {
			$value = kitwp_schema_clean( $value );
			$keys  = array_diff( array_keys( $value ), [ '@type' ] );
			if ( ! $keys ) {
				unset( $block[ $key ] );
				continue;
			}
			$block[ $key ] = $value;
		} elseif ( '' === $value || null === $value ) {
			unset( $block[ $key ] );
		}
	}
	return $block;
}

/**
 * The JSON-LD blocks for the current page.
 *
 * @return array<int, array<string, mixed>>
 */
function kitwp_schema_blocks() {
	$site   = untrailingslashit( home_url() );
	$org    = [ '@id' => $site . '/#org' ];
	$blocks = [ kitwp_schema_org() ];
	$crumbs = (array) ( $GLOBALS['kitwp_schema']['crumbs'] ?? [] );
	$faqs   = (array) ( $GLOBALS['kitwp_schema']['faq'] ?? [] );
	$id     = is_singular() ? (int) get_queried_object_id() : 0;
	$label  = $crumbs ? (string) end( $crumbs )['name'] : ( $id ? kitwp_title( $id ) : '' );
	$url    = $id ? (string) get_permalink( $id ) : '';

	if ( $id && ! is_404() ) {
		$template = (string) get_page_template_slug( $id );
		if ( in_array( $template, (array) apply_filters( 'kitwp_schema_service_templates', [ 'page-templates/service.php' ] ), true ) ) {
			$blocks[] = [
				'@context'    => 'https://schema.org',
				'@type'       => 'Service',
				'name'        => $label,
				'description' => wp_strip_all_tags( (string) get_post_meta( $id, '_yoast_wpseo_metadesc', true ) ),
				'url'         => $url,
				'serviceType' => $label,
				'provider'    => $org,
				'areaServed'  => '' !== KITWP_AREA_SERVED ? [
					'@type' => 'City',
					'name'  => KITWP_AREA_SERVED,
				] : '',
			];
		} elseif ( apply_filters( 'kitwp_schema_location_template', 'page-templates/location.php' ) === $template ) {
			$blocks[] = [
				'@context'           => 'https://schema.org',
				'@type'              => KITWP_SCHEMA_TYPE,
				'name'               => (string) kitwp_opt( 'business_name', get_bloginfo( 'name' ) ) . ' ' . $label,
				'url'                => $url,
				'telephone'          => kitwp_schema_tel(),
				'parentOrganization' => $org,
				'areaServed'         => array_map(
					static function ( $row ) {
						return [
							'@type' => 'Place',
							'name'  => (string) ( $row['name'] ?? '' ) . (string) apply_filters( 'kitwp_schema_place_suffix', '' ),
						];
					},
					kitwp_rows( function_exists( 'get_field' ) ? get_field( (string) apply_filters( 'kitwp_schema_areas_field', 'areas' ), $id ) : [] )
				),
			];
		} elseif ( is_singular( 'post' ) ) {
			$blocks[] = [
				'@context'         => 'https://schema.org',
				'@type'            => 'Article',
				'headline'         => kitwp_title( $id ),
				'author'           => [
					'@type' => 'Organization',
					'name'  => (string) kitwp_opt( 'business_name', get_bloginfo( 'name' ) ),
				],
				'publisher'        => $org,
				'mainEntityOfPage' => $url,
				'dateModified'     => (string) get_the_modified_date( 'Y-m-d', $id ),
			];
		} else {
			$type = (string) get_post_meta( $id, '_yoast_wpseo_schema_page_type', true );
			if ( in_array( $type, [ 'AboutPage', 'ContactPage' ], true ) ) {
				$blocks[] = [
					'@context'   => 'https://schema.org',
					'@type'      => $type,
					'name'       => (string) get_post_meta( $id, '_kitk_schema_name', true ),
					'url'        => $url,
					'mainEntity' => $org,
				];
			}
		}
	}
	if ( $faqs ) {
		$blocks[] = [
			'@context'   => 'https://schema.org',
			'@type'      => 'FAQPage',
			'mainEntity' => array_map(
				static function ( $faq ) {
					return [
						'@type'          => 'Question',
						'name'           => (string) ( $faq['question'] ?? '' ),
						'acceptedAnswer' => [
							'@type' => 'Answer',
							'text'  => (string) ( $faq['answer'] ?? '' ),
						],
					];
				},
				array_values( $faqs )
			),
		];
	}
	if ( $crumbs ) {
		$blocks[] = [
			'@context'        => 'https://schema.org',
			'@type'           => 'BreadcrumbList',
			'itemListElement' => array_map(
				static function ( $item, $i ) {
					return [
						'@type'    => 'ListItem',
						'position' => $i + 1,
						'name'     => (string) $item['name'],
						'item'     => kitwp_schema_url( (string) $item['path'] ),
					];
				},
				array_values( $crumbs ),
				array_keys( array_values( $crumbs ) )
			),
		];
	}
	return (array) apply_filters( 'kitwp_schema_blocks', array_map( 'kitwp_schema_clean', $blocks ) );
}

/**
 * Print the JSON-LD blocks, one script each, as the static site.
 *
 * @return void
 */
function kitwp_schema_print() {
	foreach ( kitwp_schema_blocks() as $block ) {
		echo '<script type="application/ld+json">' . wp_json_encode( $block, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_HEX_TAG ) . '</script>'; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- JSON, tags hex-escaped.
	}
}
add_action( 'wp_footer', 'kitwp_schema_print', 5 );
