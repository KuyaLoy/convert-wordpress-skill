<?php
/**
 * Lead forms: the leads portal. Each lead also goes server to server to the portal (KITWP_LEADS_PREFIX), on live
 * only, also when the email fails.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

/**
 * Tracking fields a leads portal usually asks for: the form's page, the visitor's IP, Google Ads and Meta click IDs,
 * and the form attribution (kitwp_attribution_fields(): utm_*, the ad click ids, landing page, referrer, first_*).
 *
 * @param WPCF7_Submission $sub Submission.
 * @return array<string, string>
 */
function kitwp_leads_tracking( $sub ) {
	$server = static fn( $k ) => isset( $_SERVER[ $k ] ) ? sanitize_text_field( wp_unslash( $_SERVER[ $k ] ) ) : '';
	$cookie = static fn( $k ) => isset( $_COOKIE[ $k ] ) ? sanitize_text_field( wp_unslash( $_COOKIE[ $k ] ) ) : '';
	// Anyone can send these proxy headers: one counts only when it holds a valid public IP, else the connection's own
	// address (validated too).
	$ip = '';
	foreach ( [ $server( 'HTTP_CF_CONNECTING_IP' ), trim( (string) explode( ',', $server( 'HTTP_X_FORWARDED_FOR' ) )[0] ) ] as $candidate ) {
		if ( filter_var( $candidate, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE ) ) {
			$ip = $candidate;
			break;
		}
	}
	if ( '' === $ip ) {
		$ip = (string) filter_var( $server( 'REMOTE_ADDR' ), FILTER_VALIDATE_IP );
	}
	$url = (string) $sub->get_meta( 'url' );
	if ( '' === $url ) {
		$url = (string) wp_get_referer();
	}
	$attribution = kitwp_attribution_clean( (array) $sub->get_posted_data() );
	$tracking    = [
		'source_url' => $url,
		'ip_address' => $ip,
		'gclid'      => isset( $_REQUEST['gclid'] ) ? sanitize_text_field( wp_unslash( $_REQUEST['gclid'] ) ) : $cookie( 'gclid' ), // phpcs:ignore WordPress.Security.NonceVerification.Recommended -- read only.
		'fbp'        => $cookie( '_fbp' ),
		'fbc'        => $cookie( '_fbc' ),
	];
	if ( isset( $attribution['gclid'] ) ) {
		$tracking['gclid'] = $attribution['gclid']; // the click the visit came with, kept by assets/attribution.js
	}
	return $tracking + $attribution;
}

/**
 * The fields that may go to the portal, with their length caps: the form's own fields (its Form tab) and the
 * lead fields (kitwp_lead_fields()). CF7 keeps every key a post sends, so anything else a bot adds stays out. A
 * textarea (and "msg") may be 5000 characters, as in the email; any other field 500.
 *
 * @param WPCF7_ContactForm $form Contact form.
 * @return array<string, int> Field name => maximum length.
 */
function kitwp_leads_allowed_fields( $form ) {
	$allowed = [];
	foreach ( kitwp_lead_fields() as $name ) {
		$allowed[ (string) $name ] = 'msg' === $name ? 5000 : 500;
	}
	foreach ( (array) $form->scan_form_tags() as $tag ) {
		if ( ! empty( $tag->name ) ) {
			$allowed[ (string) $tag->name ] = 'textarea' === $tag->basetype ? 5000 : 500;
		}
	}
	return $allowed;
}

/**
 * Send each lead form to the leads portal (KITWP_LEADS_PREFIX; endpoint and key from wp-config), server to server,
 * whether the email went out or failed: the portal is what still catches the lead when the host's mail is down. CF7
 * fires wpcf7_mail_sent or wpcf7_mail_failed for a submission (spam fires neither), and a request sends once. Off on
 * local, development and staging, so test submissions on a copy never reach the portal. Only the form's own fields
 * go, capped in length (kitwp_leads_allowed_fields()); files, consent, the honeypot and the fields in the
 * "kitwp_leads_skip_fields" filter (health details, dates of birth) stay out. A failure is logged with the status
 * only and never blocks the visitor.
 *
 * @param WPCF7_ContactForm $form Contact form.
 * @return void
 */
function kitwp_leads_send( $form ) {
	static $kitwp_sent = false;
	if ( $kitwp_sent ) {
		return;
	}
	$p = KITWP_LEADS_PREFIX;
	if ( '' === $p || ! kitwp_is_lead_form( $form ) || ! defined( $p . '_ENDPOINT' ) || ! defined( $p . '_KEY' ) ) {
		return;
	}
	$endpoint = (string) constant( $p . '_ENDPOINT' );
	$key      = (string) constant( $p . '_KEY' );
	if ( '' === $key || 0 !== strpos( $endpoint, 'https://' ) || in_array( wp_get_environment_type(), [ 'local', 'development', 'staging' ], true ) ) {
		return;
	}
	$sub = WPCF7_Submission::get_instance();
	if ( ! $sub ) {
		return;
	}
	$skip   = (array) apply_filters( 'kitwp_leads_skip_fields', [ 'consent', 'company' ], $form );
	$files  = array_keys( (array) $sub->uploaded_files() );
	$fields = [];
	foreach ( kitwp_leads_allowed_fields( $form ) as $name => $max ) {
		if ( in_array( $name, $skip, true ) || in_array( $name, $files, true ) || str_starts_with( (string) $name, '_' ) ) {
			continue;
		}
		$value = $sub->get_posted_data( $name );
		$value = trim( is_array( $value ) ? implode( ', ', array_filter( $value, 'is_scalar' ) ) : ( is_scalar( $value ) ? (string) $value : '' ) );
		if ( '' !== $value ) {
			$fields[ $name ] = mb_substr( $value, 0, $max, 'UTF-8' );
		}
	}
	$lead = [
		'form'            => $form->title(),
		'idempotency_key' => wp_generate_uuid4(),
	] + $fields + kitwp_leads_tracking( $sub );
	$kitwp_sent = true;
	$res        = wp_remote_post(
		$endpoint,
		[
			'timeout'     => 5,
			'redirection' => 0,
			'headers'     => [
				'Authorization' => 'Bearer ' . $key,
				'Content-Type'  => 'application/json',
			],
			'body'        => wp_json_encode( $lead ),
		]
	);
	$code = is_wp_error( $res ) ? 0 : (int) wp_remote_retrieve_response_code( $res );
	if ( 200 !== $code && 202 !== $code ) {
		// The status or transport error only: the response body may repeat what the visitor typed.
		error_log( '[leads] not delivered (' . $form->title() . '): ' . ( is_wp_error( $res ) ? $res->get_error_code() : 'HTTP ' . $code ) ); // phpcs:ignore WordPress.PHP.DevelopmentFunctions.error_log_error_log -- logs a lead the portal did not get.
	}
}
add_action( 'wpcf7_mail_sent', 'kitwp_leads_send' );
add_action( 'wpcf7_mail_failed', 'kitwp_leads_send' ); // the mail failed: the portal still gets the lead
