<?php
/**
 * Lead forms: spam protection. The honeypot "company" field as the static handler, and reCAPTCHA v3 (CF7's
 * integration, Contact > Integration) for forms that post normally, with or without JavaScript.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

/**
 * The reCAPTCHA (v3) site key when CF7's reCAPTCHA integration is active (Contact > Integration), else empty.
 *
 * @return string
 */
function kitwp_recaptcha_sitekey() {
	if ( ! class_exists( 'WPCF7_RECAPTCHA' ) ) {
		return '';
	}
	$service = WPCF7_RECAPTCHA::get_instance();
	return $service->is_active() ? (string) $service->get_sitekey() : '';
}

/**
 * reCAPTCHA v3 for the lead forms and the chat (assets/recaptcha.js). CF7's own script only fills forms with its
 * "wpcf7-form" class, which the static markup does not have, so on submit the theme asks Google for a fresh token,
 * puts it in CF7's hidden _wpcf7_recaptcha_response field and then submits (tokens last two minutes).
 * window.kitwpRecaptcha() gives the chat a token the same way. No key in Contact > Integration: nothing loads.
 * The code is a theme file (cached, versioned by its file date); the site key and options go in as data.
 *
 * KITWP_RECAPTCHA_LAZY false (default, proven on a live site): CF7 loads Google's script on every page.
 * KITWP_RECAPTCHA_LAZY true: CF7's script is dropped and Google's (about 400 KB) loads the first time someone
 * touches a lead form or the chat; after 10 seconds without Google the form still submits. Faster on phones, but
 * tested locally only: retest every form on live (keys only work on their domains).
 *
 * @return void
 */
function kitwp_recaptcha_submit_script() {
	$key  = kitwp_recaptcha_sitekey();
	$file = get_stylesheet_directory() . '/assets/recaptcha.js';
	if ( '' === $key || ! wp_script_is( 'google-recaptcha', 'registered' ) || ! file_exists( $file ) ) {
		return;
	}
	$data = [
		'key'       => $key,
		'formClass' => KITWP_FORM_CLASS,
		'lazy'      => KITWP_RECAPTCHA_LAZY ? '1' : '',
		'api'       => '',
		'warm'      => '',
	];
	$deps = [ 'wpcf7-recaptcha' ];
	if ( KITWP_RECAPTCHA_LAZY ) {
		$data['api']  = (string) wp_scripts()->registered['google-recaptcha']->src;
		$data['warm'] = 'form.' . KITWP_FORM_CLASS . ( '' !== KITWP_CHAT_SELECTOR ? ',' . KITWP_CHAT_SELECTOR : '' );
		$deps         = [];
		wp_dequeue_script( 'wpcf7-recaptcha' );
	}
	wp_enqueue_script( 'kitwp-recaptcha', kitwp_asset( 'assets/recaptcha.js' ), $deps, (string) filemtime( $file ), [ 'in_footer' => true ] );
	wp_localize_script( 'kitwp-recaptcha', 'kitwpRecaptchaConfig', $data );
}
add_action( 'wp_enqueue_scripts', 'kitwp_recaptcha_submit_script', 30 );

/**
 * Honeypot, as the static handler: a filled "company" field is a bot. Marked as spam, nothing is sent, and the
 * visitor still lands on /thank-you/. Read array-safe: a bot posting company[] must not raise a PHP warning.
 *
 * @param bool              $spam       Spam so far.
 * @param WPCF7_Submission  $submission Submission.
 * @return bool
 */
function kitwp_lead_honeypot( $spam, $submission ) {
	if ( kitwp_is_lead_form( $submission->get_contact_form() ) && '' !== trim( (string) wpcf7_flat_join( $submission->get_posted_data( 'company' ) ) ) ) {
		$GLOBALS['kitwp_lead_honeypot'] = true;
		return true;
	}
	return $spam;
}
add_filter( 'wpcf7_spam', 'kitwp_lead_honeypot', 1, 2 );

/**
 * A signed time stamp for a lead form, so a post can prove the form was loaded a few seconds earlier.
 *
 * @param int|null $now Unix time; null for now.
 * @return string "time.signature".
 */
function kitwp_form_stamp( $now = null ) {
	$time = (string) ( null === $now ? time() : (int) $now );
	return $time . '.' . substr( wp_hash( 'kitwp_form_stamp|' . $time ), 0, 20 );
}

/**
 * Whether a posted time stamp is ours and its form was loaded at least 3 seconds and at most 7 days before the post
 * (bots post at once; a cached page can be days old).
 *
 * @param string   $stamp Posted value.
 * @param int|null $now   Unix time; null for now.
 * @return bool
 */
function kitwp_form_stamp_ok( $stamp, $now = null ) {
	$parts = explode( '.', (string) $stamp );
	if ( 2 !== count( $parts ) || ! ctype_digit( $parts[0] ) || ! hash_equals( kitwp_form_stamp( (int) $parts[0] ), (string) $stamp ) ) {
		return false;
	}
	$age = ( null === $now ? time() : (int) $now ) - (int) $parts[0];
	return $age >= 3 && $age <= 7 * DAY_IN_SECONDS;
}

/**
 * With KITWP_NOJS_LEADS and reCAPTCHA on, lead forms get the time stamp in CF7's hidden fields (the parity checks
 * ignore "_wpcf7" names).
 *
 * @param array<string, string> $fields Hidden fields.
 * @return array<string, string>
 */
function kitwp_form_stamp_field( $fields ) {
	if ( KITWP_NOJS_LEADS && '' !== kitwp_recaptcha_sitekey() && kitwp_is_lead_form( wpcf7_get_current_contact_form() ) ) {
		$fields['_wpcf7_kitwp_ts'] = kitwp_form_stamp();
	}
	return $fields;
}
add_filter( 'wpcf7_form_hidden_fields', 'kitwp_form_stamp_field' );

/**
 * A lead form posted without JavaScript (or while Google's script was blocked) has no reCAPTCHA token, and CF7 calls
 * that spam: the lead would be lost. Such a post is let through only when reCAPTCHA's empty token was the one
 * reason (no other check failed, a token that scored low stays spam), the honeypot is empty, it is a normal post
 * (the chat posts over REST and always runs JavaScript) and its time stamp shows a person had the form open for a
 * few seconds. CF7's later checks (disallowed words, Akismet) still run, because this runs at reCAPTCHA's priority.
 * Opt-in (KITWP_NOJS_LEADS): off, reCAPTCHA stays strict and the visitor sees the failure note with the phone.
 *
 * @param bool             $spam       Spam so far.
 * @param WPCF7_Submission $submission Submission.
 * @return bool
 */
function kitwp_recaptcha_no_js( $spam, $submission ) {
	if ( ! KITWP_NOJS_LEADS || ! $spam || ! empty( $GLOBALS['kitwp_lead_honeypot'] ) || WPCF7_Submission::is_restful() || ! kitwp_is_lead_form( $submission->get_contact_form() ) ) {
		return $spam;
	}
	// phpcs:disable WordPress.Security.NonceVerification.Missing -- CF7 checks the submission; read only.
	$token = isset( $_POST['_wpcf7_recaptcha_response'] ) ? sanitize_text_field( wp_unslash( $_POST['_wpcf7_recaptcha_response'] ) ) : '';
	$stamp = isset( $_POST['_wpcf7_kitwp_ts'] ) ? sanitize_text_field( wp_unslash( $_POST['_wpcf7_kitwp_ts'] ) ) : '';
	// phpcs:enable
	$log = (array) $submission->get_spam_log();
	if ( '' !== $token || ! $log || '' !== trim( (string) wpcf7_flat_join( $submission->get_posted_data( 'company' ) ) ) ) {
		return $spam;
	}
	foreach ( $log as $entry ) {
		if ( 'recaptcha' !== ( $entry['agent'] ?? '' ) ) {
			return $spam;
		}
	}
	return kitwp_form_stamp_ok( $stamp ) ? false : $spam;
}
add_filter( 'wpcf7_spam', 'kitwp_recaptcha_no_js', 9, 2 );
