<?php
/**
 * Lead forms: where each lead came from (form attribution), on every lead form by default, with no plugin.
 *
 * assets/attribution.js keeps the visit's campaign tags and ad click ids in the browser (first party only: nothing
 * is sent anywhere until the visitor sends a form) and fills hidden fields on every Contact Form 7 form. Here the
 * server checks them once, as CF7 reads the post: an allow-list of names, cleaned, capped in length, addresses
 * without their query. The lead email ([_kitk_source]), Contact Form CFDB7 (it stores the posted fields) and the
 * leads portal then all get the same clean values. Reporting only: nothing here decides anything about a lead.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

/**
 * The attribution fields and their length caps: the last touch (this visit: the campaign tags and ad click ids it
 * came with, its first page, the site that sent it), then the first touch (the first visit in KITWP_ATTRIBUTION_DAYS).
 *
 * @return array<string, int> Field name => maximum length.
 */
function kitwp_attribution_fields() {
	$fields = [];
	foreach ( [ 'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'gclid', 'gbraid', 'wbraid', 'fbclid', 'msclkid' ] as $name ) {
		$fields[ $name ] = 200;
	}
	return $fields + [
		'landing_page'       => 500,
		'referrer'           => 500,
		'first_source'       => 200,
		'first_medium'       => 200,
		'first_campaign'     => 200,
		'first_landing_page' => 500,
		'first_referrer'     => 500,
		'first_seen'         => 10,
	];
}

/**
 * An address as attribution keeps it: http or https, host and path only. The query and fragment go, because a
 * query can carry an email address or a name.
 *
 * @param string $url Address.
 * @return string '' when it is not a web address.
 */
function kitwp_attribution_url( $url ) {
	$parts = wp_parse_url( trim( (string) $url ) );
	if ( ! is_array( $parts ) || empty( $parts['host'] ) || ! in_array( strtolower( $parts['scheme'] ?? '' ), [ 'http', 'https' ], true ) ) {
		return '';
	}
	$port = isset( $parts['port'] ) ? ':' . (int) $parts['port'] : '';
	return esc_url_raw( strtolower( $parts['scheme'] ) . '://' . strtolower( $parts['host'] ) . $port . ( $parts['path'] ?? '/' ) );
}

/**
 * The attribution of a post, checked: only the allow-listed names, scalar values, cleaned and capped; anything
 * else is dropped. Without JavaScript nothing is posted, so the form page's own address (the browser's Referer)
 * still gives the campaign tags and click ids the page was opened with.
 *
 * @param array<string, mixed> $posted  Posted fields.
 * @param string               $referer The form page's address ('' when unknown).
 * @return array<string, string> Only the non-empty values.
 */
function kitwp_attribution_clean( $posted, $referer = '' ) {
	$clean = [];
	foreach ( kitwp_attribution_fields() as $name => $max ) {
		$value = $posted[ $name ] ?? '';
		$value = is_scalar( $value ) ? trim( (string) $value ) : '';
		if ( '' === $value ) {
			continue;
		}
		if ( str_ends_with( $name, 'landing_page' ) || str_ends_with( $name, 'referrer' ) ) {
			$value = kitwp_attribution_url( $value );
		} elseif ( 'first_seen' === $name ) {
			$value = preg_match( '/^\d{4}-\d{2}-\d{2}$/', $value ) ? $value : '';
		} else {
			$value = sanitize_text_field( $value );
		}
		$value = mb_substr( $value, 0, $max, 'UTF-8' );
		if ( '' !== $value ) {
			$clean[ $name ] = $value;
		}
	}
	$touch = array_slice( array_keys( kitwp_attribution_fields() ), 0, 10 ); // the campaign tags and click ids
	if ( '' !== $referer && ! array_intersect_key( $clean, array_flip( $touch ) ) ) {
		parse_str( (string) wp_parse_url( $referer, PHP_URL_QUERY ), $query );
		foreach ( $touch as $name ) {
			$value = isset( $query[ $name ] ) && is_scalar( $query[ $name ] ) ? sanitize_text_field( (string) $query[ $name ] ) : '';
			if ( '' !== $value ) {
				$clean[ $name ] = mb_substr( $value, 0, 200, 'UTF-8' );
			}
		}
		if ( array_intersect_key( $clean, array_flip( $touch ) ) && ! isset( $clean['landing_page'] ) ) {
			$clean['landing_page'] = kitwp_attribution_url( $referer );
		}
	}
	return array_filter( $clean, 'strlen' );
}

/**
 * Clean the attribution fields as CF7 reads the post, so the email, CFDB7 and the portal see the same checked
 * values (an oversized or tampered value is cut or dropped before anything stores it).
 *
 * @param array<string, mixed> $posted Posted fields.
 * @return array<string, mixed>
 */
function kitwp_attribution_posted( $posted ) {
	if ( ! is_array( $posted ) ) {
		return $posted;
	}
	$referer = isset( $_SERVER['HTTP_REFERER'] ) ? esc_url_raw( wp_unslash( $_SERVER['HTTP_REFERER'] ) ) : '';
	$clean   = kitwp_attribution_clean( $posted, $referer );
	foreach ( array_keys( kitwp_attribution_fields() ) as $name ) {
		unset( $posted[ $name ] );
	}
	return $posted + $clean;
}
add_filter( 'wpcf7_posted_data', 'kitwp_attribution_posted' );

/**
 * Where the lead came from, as lines for the lead email ("Direct" first when no campaign, ad click or other site
 * sent the visitor).
 *
 * @param array<string, string> $a Clean attribution (kitwp_attribution_clean()).
 * @return string[]
 */
function kitwp_attribution_lines( $a ) {
	$pair   = static fn( $x, $y ) => trim( $x . ( '' !== $y ? ' / ' . $y : '' ), ' /' );
	$lines  = [];
	$source = $pair( $a['utm_source'] ?? '', $a['utm_medium'] ?? '' );
	$clicks = [];
	foreach ( [ 'gclid' => 'Google Ads', 'gbraid' => 'Google Ads (app)', 'wbraid' => 'Google Ads (web to app)', 'fbclid' => 'Meta', 'msclkid' => 'Microsoft Ads' ] as $name => $label ) {
		if ( isset( $a[ $name ] ) ) {
			$clicks[] = $label . ' (' . $name . ')';
		}
	}
	if ( '' === $source && ! $clicks && ! isset( $a['referrer'] ) ) {
		$lines[] = 'Direct (no campaign, ad click or other site)';
	}
	foreach ( [
		'Source / medium' => $source,
		'Campaign'        => $a['utm_campaign'] ?? '',
		'Keyword'         => $a['utm_term'] ?? '',
		'Ad content'      => $a['utm_content'] ?? '',
		'Ad click'        => implode( ', ', $clicks ),
		'Referrer'        => $a['referrer'] ?? '',
		'Landing page'    => $a['landing_page'] ?? '',
	] as $label => $value ) {
		if ( '' !== $value ) {
			$lines[] = $label . ': ' . $value;
		}
	}
	if ( isset( $a['first_seen'] ) ) {
		$first   = $pair( $a['first_source'] ?? '', $a['first_medium'] ?? '' );
		$first   = '' !== $first ? $first : ( isset( $a['first_referrer'] ) ? 'from ' . $a['first_referrer'] : 'direct' );
		$lines[] = 'First visit: ' . implode( ', ', array_filter( [ $a['first_seen'], $first, $a['first_campaign'] ?? '', $a['first_landing_page'] ?? '' ] ) );
	}
	return $lines;
}

/**
 * The browser side: assets/attribution.js on every page (deferred, versioned by its file date), so the landing page
 * of any visit is recorded. Its settings go in as data.
 *
 * @return void
 */
function kitwp_attribution_script() {
	$file = get_stylesheet_directory() . '/assets/attribution.js';
	if ( ! file_exists( $file ) ) {
		return;
	}
	wp_enqueue_script(
		'kitwp-attribution',
		kitwp_asset( 'assets/attribution.js' ),
		[],
		(string) filemtime( $file ),
		[
			'in_footer' => true,
			'strategy'  => 'defer',
		]
	);
	wp_localize_script(
		'kitwp-attribution',
		'kitwpAttributionConfig',
		[
			'days'     => (string) (int) KITWP_ATTRIBUTION_DAYS,
			'thankYou' => home_url( KITWP_THANK_YOU ),
		]
	);
}
add_action( 'wp_enqueue_scripts', 'kitwp_attribution_script', 30 );
