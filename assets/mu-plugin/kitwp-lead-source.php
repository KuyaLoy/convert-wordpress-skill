<?php
/**
 * Plugin Name: Lead source
 * Description: Where each Contact Form 7 lead came from, as the company attribution standard's eleven fields (Lead Source ... First Touch Referrer; browser storage only, first party), checked on the server: a "Lead Attribution" table in each enquiry email, labelled columns in Contact Form CFDB7 and fields for a leads portal or CRM connector. For a WordPress site the convert-to-wordpress kit did not build.
 * Version: {{VERSION}}
 * Requires PHP: 7.4
 * License: GPL-2.0-or-later
 *
 * Made by the kit's scripts/launch/lead-source-plugin.py from the theme kit's own files (kitwp-lead-source/:
 * forms-attribution.php, forms-lead-source.php, attribution.js), so both stay the same code. Goes in
 * wp-content/mu-plugins/ with its folder. A theme built with the kit has all of this already: then this does nothing.
 * The table goes where the Mail tab has <!-- kitwp-lead-source -->, else before </body>, else at the end; a plain-text
 * mail gets the same rows as text. Any error leaves the email as it was: the enquiry always goes out.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

/**
 * Load the attribution once the theme is known (a kit theme defines the same functions: then skip).
 *
 * @return void
 */
function kitwp_lead_source_load() {
	if ( function_exists( 'kitwp_attribution_clean' ) ) {
		return;
	}
	defined( 'KITWP_BRAND_COLOUR' ) || define( 'KITWP_BRAND_COLOUR', '{{BRAND_COLOUR}}' );
	defined( 'KITWP_ATTRIBUTION_DAYS' ) || define( 'KITWP_ATTRIBUTION_DAYS', (int) '{{DAYS}}' );
	defined( 'KITWP_ATTRIBUTION_CONSENT' ) || define( 'KITWP_ATTRIBUTION_CONSENT', '{{CONSENT}}' );
	defined( 'KITWP_THANK_YOU' ) || define( 'KITWP_THANK_YOU', '{{THANK_YOU}}' );
	require_once __DIR__ . '/kitwp-lead-source/forms-attribution.php';
	require_once __DIR__ . '/kitwp-lead-source/forms-lead-source.php';
	add_action( 'wp_enqueue_scripts', 'kitwp_lead_source_script', 31 );
	add_filter( 'wpcf7_mail_components', 'kitwp_lead_source_mail', 10, 3 );
}
add_action( 'after_setup_theme', 'kitwp_lead_source_load', 0 );

/**
 * The capture script from this folder, on every page (a visitor may land on a page without a form).
 *
 * @return void
 */
function kitwp_lead_source_script() {
	$file = __DIR__ . '/kitwp-lead-source/attribution.js';
	if ( ! file_exists( $file ) ) {
		return;
	}
	wp_enqueue_script(
		'kitwp-attribution',
		content_url( 'mu-plugins/kitwp-lead-source/attribution.js' ),
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

/**
 * Add the "Lead Attribution" table to the main email of every CF7 form (not Mail (2), the copy to the visitor).
 *
 * @param array<string, mixed> $components Mail parts (subject, sender, body, recipient...).
 * @param object|null          $form       Contact form.
 * @param object|null          $mail       The mail being built.
 * @return array<string, mixed>
 */
function kitwp_lead_source_mail( $components, $form = null, $mail = null ) {
	try {
		if ( ! is_array( $components ) || ! isset( $components['body'] ) || ! is_object( $mail ) || ! method_exists( $mail, 'name' ) || 'mail' !== $mail->name() ) {
			return $components;
		}
		$sub = class_exists( 'WPCF7_Submission' ) ? WPCF7_Submission::get_instance() : null;
		if ( ! $sub ) {
			return $components;
		}
		$body  = (string) $components['body'];
		$props = is_object( $form ) && method_exists( $form, 'prop' ) ? (array) $form->prop( 'mail' ) : [];
		$html  = ! empty( $props['use_html'] ) || false !== stripos( $body, '</body>' ) || false !== stripos( $body, '</table>' );
		$block = kitwp_attribution_table( (array) $sub->get_posted_data(), (string) $sub->get_meta( 'url' ), $html );
		if ( ! $html ) {
			$components['body'] = rtrim( $body ) . "\n\n" . $block . "\n";
			return $components;
		}
		$marker = '<!-- kitwp-lead-source -->';
		$end    = stripos( $body, '</body>' );
		if ( false !== strpos( $body, $marker ) ) {
			$body = str_replace( $marker, $block, $body );
		} elseif ( false !== $end ) {
			$body = substr_replace( $body, $block, $end, 0 );
		} else {
			$body .= $block;
		}
		$components['body'] = $body;
	} catch ( \Throwable $e ) {
		unset( $e ); // Never stop an enquiry email.
	}
	return $components;
}
