<?php
/**
 * Lead forms: the leads portal. Each lead also goes server to server to the portal, on live only, also when the
 * email fails. The endpoint and write key live in Theme Settings > Leads portal (administrators only); wp-config
 * constants <KITWP_LEADS_PREFIX>_ENDPOINT and _KEY win when defined.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

/**
 * The portal's endpoint and write key: Theme Settings > Leads portal (always there; the developer pastes them on
 * live as an administrator), unless wp-config defines <KITWP_LEADS_PREFIX>_ENDPOINT or _KEY, which win. The key is
 * stored in the database: it travels in Duplicator packages and database backups. Never printed anywhere.
 *
 * @return array{endpoint: string, key: string, from: string} "from": where the values came from.
 */
function kitwp_leads_settings() {
	$p    = KITWP_LEADS_PREFIX;
	$from = [];
	$out  = [];
	foreach ( [ 'endpoint' => '_ENDPOINT', 'key' => '_KEY' ] as $name => $suffix ) {
		if ( '' !== $p && defined( $p . $suffix ) ) {
			$out[ $name ] = trim( (string) constant( $p . $suffix ) );
			$from[]       = 'wp-config';
		} else {
			$out[ $name ] = trim( (string) kitwp_setting( 'leads_' . $name ) );
			$from[]       = 'Theme Settings';
		}
	}
	$out['from'] = implode( ' and ', array_unique( $from ) );
	return $out;
}

/**
 * Theme Settings > Leads portal is for administrators only: its group shows to them alone (the group's location),
 * and a save by anyone else keeps the stored value, whatever the request posts. WP-CLI may set it.
 *
 * @param mixed $value   The value being saved.
 * @param mixed $post_id ACF post id ("options").
 * @param array $field   The field.
 * @return mixed
 */
function kitwp_leads_settings_guard( $value, $post_id, $field ) {
	if ( current_user_can( 'manage_options' ) || ( defined( 'WP_CLI' ) && WP_CLI ) ) {
		return $value;
	}
	return get_field( $field['key'], $post_id, false );
}
add_filter( 'acf/update_value/key=field_kitk_ts_leads_endpoint', 'kitwp_leads_settings_guard', 10, 3 );
add_filter( 'acf/update_value/key=field_kitk_ts_leads_key', 'kitwp_leads_settings_guard', 10, 3 );

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
 * Send each lead form to the leads portal (kitwp_leads_settings(): Theme Settings, or wp-config), server to server,
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
	if ( ! kitwp_is_lead_form( $form ) ) {
		return;
	}
	$settings = kitwp_leads_settings();
	$endpoint = $settings['endpoint'];
	$key      = $settings['key'];
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
