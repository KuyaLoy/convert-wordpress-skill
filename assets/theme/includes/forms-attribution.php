<?php
/**
 * Lead forms: where each lead came from (form attribution), on every lead form by default, with no plugin.
 *
 * The browser script, assets/attribution.js, keeps the first visit and the latest campaign visit in the browser (first party only: nothing
 * is sent anywhere until the visitor sends a form) and fills hidden fields on every Contact Form 7 form. Here the
 * server checks them once, as CF7 reads the post (an allow-list of names, cleaned, capped in length; a referrer
 * without its query, a landing page with it but no email address) and adds the company standard's eleven fields.
 * The lead email ([_kitk_source]), Contact Form CFDB7 (the eleven as labelled columns), the leads portal and a CRM
 * connector then all get the same values. Reporting only: nothing here decides anything about a lead.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

/**
 * The attribution fields the browser posts and their length caps. The latest campaign visit (the last one that came
 * with campaign tags, an ad click id or from another website): utm_*, the click ids, landing_page, referrer,
 * last_seen. The first visit in KITWP_ATTRIBUTION_DAYS: the same, named first_* (without utm_: first_source,
 * first_id), and first_seen. Times are UTC, "YYYY-MM-DD HH:MM".
 *
 * @return array<string, int> Field name => maximum length.
 */
function kitwp_attribution_fields() {
	$fields = [];
	foreach ( kitwp_attribution_touch() as $name ) {
		$fields[ $name ] = 200;
	}
	$fields += [
		'landing_page' => 1000,
		'referrer'     => 500,
		'last_seen'    => 16,
	];
	foreach ( kitwp_attribution_touch() as $name ) {
		$fields[ 'first_' . str_replace( 'utm_', '', $name ) ] = 200;
	}
	return $fields + [
		'first_landing_page' => 1000,
		'first_referrer'     => 500,
		'first_seen'         => 16,
	];
}

/**
 * The campaign tags and ad click ids, as they arrive in a link (gad_campaignid: the Google Ads campaign of an
 * auto-tagged click).
 *
 * @return string[]
 */
function kitwp_attribution_touch() {
	return [ 'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'utm_id', 'gclid', 'gbraid', 'wbraid', 'fbclid', 'msclkid', 'gad_campaignid' ];
}

/**
 * An address as attribution keeps it: http or https, host and path; a landing page keeps its query string too
 * (the campaign tags in it), without any parameter whose value holds an "@" (an email address stays out). The
 * fragment always goes; a referrer (another site's address) keeps no query.
 *
 * @param string $url   Address.
 * @param bool   $query Keep the query string (landing pages and the form page).
 * @return string '' when it is not a web address.
 */
function kitwp_attribution_url( $url, $query = false ) {
	$parts = wp_parse_url( trim( (string) $url ) );
	if ( ! is_array( $parts ) || empty( $parts['host'] ) || ! in_array( strtolower( $parts['scheme'] ?? '' ), [ 'http', 'https' ], true ) ) {
		return '';
	}
	$port = isset( $parts['port'] ) ? ':' . (int) $parts['port'] : '';
	$keep = [];
	if ( $query && ! empty( $parts['query'] ) ) {
		foreach ( explode( '&', $parts['query'] ) as $pair ) {
			if ( '' !== $pair && ! str_contains( rawurldecode( str_replace( '+', ' ', $pair ) ), '@' ) ) {
				$keep[] = $pair;
			}
		}
	}
	return esc_url_raw( strtolower( $parts['scheme'] ) . '://' . strtolower( $parts['host'] ) . $port . ( $parts['path'] ?? '/' ) . ( $keep ? '?' . implode( '&', $keep ) : '' ) );
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
			$value = kitwp_attribution_url( $value, str_ends_with( $name, 'landing_page' ) );
		} elseif ( str_ends_with( $name, '_seen' ) ) {
			$value = preg_match( '/^\d{4}-\d{2}-\d{2}( \d{2}:\d{2})?$/', $value ) ? $value : ''; // UTC; a date alone (0.9.9) too.
		} else {
			$value = sanitize_text_field( $value );
		}
		$value = mb_substr( $value, 0, $max, 'UTF-8' );
		if ( '' !== $value ) {
			$clean[ $name ] = $value;
		}
	}
	$touch = kitwp_attribution_touch();
	if ( '' !== $referer && ! array_intersect_key( $clean, array_flip( $touch ) ) ) {
		parse_str( (string) wp_parse_url( $referer, PHP_URL_QUERY ), $query );
		foreach ( $touch as $name ) {
			$value = isset( $query[ $name ] ) && is_scalar( $query[ $name ] ) ? sanitize_text_field( (string) $query[ $name ] ) : '';
			if ( '' !== $value ) {
				$clean[ $name ] = mb_substr( $value, 0, 200, 'UTF-8' );
			}
		}
		if ( array_intersect_key( $clean, array_flip( $touch ) ) && ! isset( $clean['landing_page'] ) ) {
			$clean['landing_page'] = kitwp_attribution_url( $referer, true );
		}
	}
	return array_filter( $clean, 'strlen' );
}

/**
 * The page the form was sent from: the browser's Referer (the kit's forms and the chat post from the form's page;
 * the live .htaccess sends the full address within the site), else the address a native post went to.
 *
 * @return string With its query string, as kitwp_attribution_url() keeps it; '' when unknown.
 */
function kitwp_attribution_form_page() {
	// phpcs:disable WordPress.Security.ValidatedSanitizedInput.InputNotSanitized -- checked by kitwp_attribution_url().
	$referer = isset( $_SERVER['HTTP_REFERER'] ) ? (string) wp_unslash( $_SERVER['HTTP_REFERER'] ) : '';
	$uri     = isset( $_SERVER['REQUEST_URI'] ) ? (string) wp_unslash( $_SERVER['REQUEST_URI'] ) : '';
	// phpcs:enable
	$page = kitwp_attribution_url( $referer, true );
	if ( '' === $page && '' !== $uri && ! str_contains( $uri, '/wp-json/' ) ) {
		$page = kitwp_attribution_url( home_url( $uri ), true );
	}
	return $page;
}

/**
 * Clean the attribution fields as CF7 reads the post and add the eleven standard values, so the email, CFDB7, the
 * leads portal and a CRM connector see the same checked values (an oversized or tampered value is cut or dropped
 * before anything stores it; a posted standard name is always replaced by the server's own value).
 *
 * @param array<string, mixed> $posted Posted fields.
 * @return array<string, mixed>
 */
function kitwp_attribution_posted( $posted ) {
	if ( ! is_array( $posted ) ) {
		return $posted;
	}
	$page  = kitwp_attribution_form_page();
	$clean = kitwp_attribution_clean( $posted, $page );
	foreach ( array_merge( array_keys( kitwp_attribution_fields() ), array_keys( kitwp_attribution_standard() ) ) as $name ) {
		unset( $posted[ $name ] );
	}
	return $posted + kitwp_attribution_values( $clean, $page ) + $clean;
}
add_filter( 'wpcf7_posted_data', 'kitwp_attribution_posted' );

/**
 * Contact Form CFDB7 stores each lead with the standard's labels as its columns, in the standard's order, then the
 * extra rows. CFDB7 keeps only the form's own tags by default (cfdb7_strict_keys), so the values come from the CF7
 * submission, HTML-escaped as CFDB7 escapes its own (its admin prints them as they are). The form's own fields stay
 * first; raw browser fields never go in (the email and the portal keep them).
 *
 * @param array<string, mixed> $data What CFDB7 is about to store.
 * @return array<string, mixed>
 */
function kitwp_attribution_cfdb7( $data ) {
	$sub    = class_exists( 'WPCF7_Submission' ) ? WPCF7_Submission::get_instance() : null;
	$posted = $sub ? (array) $sub->get_posted_data() : [];
	if ( ! is_array( $data ) || ! isset( $posted['lead_source'] ) ) {
		return $data;
	}
	$out  = array_diff_key( $data, kitwp_attribution_fields() + kitwp_attribution_standard() );
	$rows = [];
	foreach ( kitwp_attribution_standard() as $name => $label ) {
		$rows[ $label ] = is_scalar( $posted[ $name ] ?? null ) ? (string) $posted[ $name ] : 'none';
	}
	return $out + array_map( 'esc_html', $rows + kitwp_attribution_extra_rows( kitwp_attribution_clean( $posted ) ) );
}
add_filter( 'cfdb7_before_save_data', 'kitwp_attribution_cfdb7' );

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
			'consent'  => (string) KITWP_ATTRIBUTION_CONSENT,
			'thankYou' => home_url( KITWP_THANK_YOU ),
		]
	);
}
add_action( 'wp_enqueue_scripts', 'kitwp_attribution_script', 30 );
