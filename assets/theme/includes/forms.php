<?php
/**
 * Lead forms run by Contact Form 7, kept 1:1 with the static form and editable in CF7: the seeded form ids, the Quote
 * Form as the static markup, the posted values, the thank-you redirect and the chat widget's config.
 *
 * Contact > Contact Forms holds the forms (seeded from _setup/seed/forms.json). Quote Form: the Form tab is the
 * form people see (labels, placeholders, options, button) and the Mail tab is the email (To, From, Subject, Bcc,
 * Reply-To and the HTML body with mail-tags). The theme prints CF7's text, email, tel, url, select, textarea and
 * hidden tags in the static markup and drops CF7's wrapper (forms-controls.php). Per page it adds the service
 * options, the source, the pop-up's "qm-" id prefix and the compact form without email. As on the static site the
 * form posts normally (JavaScript on or off) and lands on KITWP_THANK_YOU with a 303. Chat Lead: the chat widget
 * posts FormData to CF7's REST endpoint; its Form tab is the field list and its Mail tab the email.
 *
 * One job per file: forms-controls.php (CF7's field tags in the static markup), forms-spam.php (honeypot and
 * reCAPTCHA), forms-mail.php (the branded lead email), forms-local-mail.php (mail on a local copy) and
 * forms-portal.php (the leads portal).
 *
 * Field names are the static form's: name, phone, email, postcode, service, when, whenDT, msg, source, and the
 * honeypot "company". Change kitwp_lead_fields(), kitwp_lead_data() and the mail-tags if the site's form differs.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

/**
 * The seeded CF7 form ID for "quote" or "chat" (0 when not seeded or CF7 is off).
 *
 * @param string $key Form key.
 * @return int
 */
function kitwp_cf7_form_id( $key ) {
	if ( ! function_exists( 'wpcf7_contact_form' ) ) {
		return 0;
	}
	$ids = (array) get_option( 'kitwp_cf7_forms', [] );
	$id  = (int) ( $ids[ $key ] ?? 0 );
	return $id && wpcf7_contact_form( $id ) ? $id : 0;
}

/**
 * Whether a CF7 form is one of the theme's lead forms.
 *
 * @param WPCF7_ContactForm|null $form Contact form.
 * @return bool
 */
function kitwp_is_lead_form( $form ) {
	if ( ! $form ) {
		return false;
	}
	return in_array( (int) $form->id(), array_map( 'intval', (array) get_option( 'kitwp_cf7_forms', [] ) ), true );
}

/**
 * The Quote Form as Contact Form 7 prints it from its Form tab, in the static markup.
 *
 * @param array<string, mixed> $args options, source, prefix ("qm-" in the pop-up), compact (no email field).
 * @return string Empty when CF7 or the seeded form is missing.
 */
function kitwp_quote_form_html( $args ) {
	$id = kitwp_cf7_form_id( 'quote' );
	if ( ! $id ) {
		return '';
	}
	$GLOBALS['kitwp_form_ctx'] = [
		'options' => array_values( array_map( 'strval', (array) ( $args['options'] ?? [] ) ) ),
		'source'  => (string) ( $args['source'] ?? '' ),
		'prefix'  => (string) ( $args['prefix'] ?? '' ),
		'compact' => ! empty( $args['compact'] ),
	];
	$html = (string) wpcf7_contact_form( $id )->form_html();
	$ctx  = $GLOBALS['kitwp_form_ctx'];
	unset( $GLOBALS['kitwp_form_ctx'] );
	// The failed-post note needs to know whether CF7 stopped this form's post (spam, aborted).
	$sub    = class_exists( 'WPCF7_Submission' ) ? WPCF7_Submission::get_instance() : null;
	$status = $sub && (int) $sub->get_contact_form()->id() === $id ? (string) $sub->get_status() : '';
	$html = kitwp_cf7_clean( $html, $ctx['prefix'], $status );
	// The form's name for the generate_lead event (assets/attribution.js); parity checks ignore data attributes.
	return (string) preg_replace( '/^<form /', '<form data-form-name="' . esc_attr( wpcf7_contact_form( $id )->title() ) . '" ', $html, 1 );
}

/**
 * The service list differs per page (it is set by the page, not the Form tab), so when a post is checked the
 * posted service is accepted as one of the options, as the static handler accepted any service.
 *
 * @param array<string, mixed> $tag Scanned form tag.
 * @return array<string, mixed>
 */
function kitwp_cf7_service_values( $tag ) {
	if ( 'service' !== ( $tag['name'] ?? '' ) || isset( $GLOBALS['kitwp_form_ctx'] ) || ! isset( $_POST['_wpcf7'], $_POST['service'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Missing -- CF7 checks the submission.
		return $tag;
	}
	$posted              = sanitize_text_field( wp_unslash( $_POST['service'] ) ); // phpcs:ignore WordPress.Security.NonceVerification.Missing -- CF7 checks the submission.
	$tag['values'][]     = $posted;
	$tag['raw_values'][] = $posted;
	$tag['labels'][]     = $posted;
	return $tag;
}
add_filter( 'wpcf7_form_tag', 'kitwp_cf7_service_values' );

/**
 * No automatic paragraphs in any CF7 form: the Form tab is the markup, so CF7 adds no stray <p> or <br> around
 * the fields (lead forms, the chat and any other form a template prints).
 */
add_filter( 'wpcf7_autop_or_not', '__return_false' );

/**
 * Empty paragraphs left in a form's markup (a blank line in the Form tab, an editor's paste) are removed.
 *
 * @param string $html Form elements.
 * @return string
 */
function kitwp_cf7_no_empty_p( $html ) {
	return (string) preg_replace( '#<p>(?:\s|&nbsp;|<br\s*/?>)*</p>#i', '', (string) $html );
}
add_filter( 'wpcf7_form_elements', 'kitwp_cf7_no_empty_p' );

/**
 * Print the pop-up's form, as the static QuoteModal: general options, field ids prefixed "qm-".
 *
 * @param string $context Where the form is printed.
 * @return void
 */
function kitwp_popup_form( $context ) {
	if ( 'popup' !== $context ) {
		return;
	}
	$path = isset( $_SERVER['REQUEST_URI'] ) ? (string) wp_parse_url( sanitize_text_field( wp_unslash( $_SERVER['REQUEST_URI'] ) ), PHP_URL_PATH ) : '/';
	get_template_part(
		'template-parts/sections/lead-form',
		null,
		[
			'options' => array_column( (array) kitwp_opt( 'qf_service_options', [] ), 'label' ),
			'source'  => 'popup:' . $path,
			'prefix'  => 'qm-',
		]
	);
}
add_action( 'kitwp_quote_form', 'kitwp_popup_form' );

// CF7's own front-end script and stylesheet are not used: the forms post normally, as on the static site.
add_filter( 'wpcf7_load_js', '__return_false' );

/**
 * The static form's "name" field is also a WordPress query var (a post slug), and WordPress reads query vars from
 * POST too, so a quote form post would look up a post called "Sarah M." and answer 404. For a CF7 post, "name" is
 * taken from the URL only.
 *
 * @param array<string, mixed> $query_vars Query vars.
 * @return array<string, mixed>
 */
function kitwp_lead_query_vars( $query_vars ) {
	if ( ! isset( $_POST['_wpcf7'], $_POST['name'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Missing -- read only to keep the page query right.
		return $query_vars;
	}
	parse_str( (string) ( $GLOBALS['wp']->matched_query ?? '' ), $matched );
	if ( isset( $matched['name'] ) && '' !== $matched['name'] ) {
		$query_vars['name'] = $matched['name'];
	} elseif ( isset( $_GET['name'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended -- read only to keep the page query right.
		$query_vars['name'] = sanitize_title( wp_unslash( $_GET['name'] ) ); // phpcs:ignore WordPress.Security.NonceVerification.Recommended -- read only to keep the page query right.
	} else {
		unset( $query_vars['name'] );
	}
	return $query_vars;
}
add_filter( 'request', 'kitwp_lead_query_vars' );

/**
 * After a normal (non-REST) post: sent, or caught by the honeypot, goes to /thank-you/ with a 303, as the static
 * handler did. A mail failure goes there too (the static handler did the same) and is logged.
 *
 * @return void
 */
function kitwp_lead_redirect() {
	if ( ! class_exists( 'WPCF7_Submission' ) || WPCF7_Submission::is_restful() ) {
		return;
	}
	$submission = WPCF7_Submission::get_instance();
	if ( ! $submission || ! kitwp_is_lead_form( $submission->get_contact_form() ) ) {
		return;
	}
	if ( in_array( $submission->get_status(), [ 'mail_sent', 'mail_failed' ], true ) || ! empty( $GLOBALS['kitwp_lead_honeypot'] ) ) {
		wp_safe_redirect( home_url( KITWP_THANK_YOU ), 303 );
		exit;
	}
}
add_action( 'template_redirect', 'kitwp_lead_redirect', 1 );

/**
 * Keep a trace when the email could not be handed off (as the static handler).
 *
 * @param WPCF7_ContactForm $form Contact form.
 * @return void
 */
function kitwp_lead_mail_failed( $form ) {
	$submission = WPCF7_Submission::get_instance();
	if ( $submission && kitwp_is_lead_form( $form ) ) {
		// The form only: field values can hold personal or health details and never go into a log.
		error_log( '[lead] mail failed: ' . $form->title() ); // phpcs:ignore WordPress.PHP.DevelopmentFunctions.error_log_error_log -- a lead whose email failed must leave a trace.
	}
}
add_action( 'wpcf7_mail_failed', 'kitwp_lead_mail_failed' );

/**
 * The static form's field names, across the lead forms and the chat (filter "kitwp_lead_fields" when the site's
 * forms differ). A mail-tag for one of them that a form does not post becomes empty.
 *
 * @return string[]
 */
function kitwp_lead_fields() {
	return (array) apply_filters( 'kitwp_lead_fields', [ 'name', 'phone', 'email', 'postcode', 'service', 'when', 'whenDT', 'msg', 'source' ] );
}

/**
 * The chat widget, when the static site has one (assets/chat-widget.js in the theme): its config, then the widget
 * script after the page has loaded (as Next's lazyOnload). WordPress adds the Chat Lead form's REST endpoint, CF7's
 * hidden fields and the reCAPTCHA site key; the widget's save() posts FormData to config.endpoint (pattern in
 * assets/chat-save.js). A JSON body answers 415 and a missing _wpcf7_unit_tag 400. Extra values the
 * static widget expects (its phone, images) go in through the "kitwp_chat_config" filter.
 *
 * @return void
 */
function kitwp_chat_widget() {
	$file = get_stylesheet_directory() . '/assets/chat-widget.js';
	if ( ! file_exists( $file ) || ! apply_filters( 'kitwp_chat_enabled', true ) ) {
		return;
	}
	$config = (array) apply_filters(
		'kitwp_chat_config',
		[
			'phone' => kitwp_phone(),
			'tel'   => kitwp_tel(),
		]
	);
	$id     = kitwp_cf7_form_id( 'chat' );
	if ( $id ) {
		$form                = wpcf7_contact_form( $id );
		$config['endpoint']  = rest_url( 'contact-form-7/v1/contact-forms/' . $id . '/feedback' );
		$config['recaptcha'] = kitwp_recaptcha_sitekey();
		$config['fields']    = [
			'_wpcf7'                => $id,
			'_wpcf7_version'        => WPCF7_VERSION,
			'_wpcf7_locale'         => $form->locale(),
			'_wpcf7_unit_tag'       => 'wpcf7-f' . $id . '-o1',
			'_wpcf7_container_post' => (int) get_queried_object_id(),
		];
	}
	$src = add_query_arg( 'ver', (string) filemtime( $file ), kitwp_asset( 'assets/chat-widget.js' ) );
	printf(
		'<script>window.__KITWP_CHAT=%1$s;addEventListener("load",function(){setTimeout(function(){var s=document.createElement("script");s.src=%2$s;document.body.appendChild(s)},1)})</script>',
		wp_json_encode( $config, JSON_UNESCAPED_SLASHES ),
		wp_json_encode( $src, JSON_UNESCAPED_SLASHES )
	);
}
add_action( 'wp_footer', 'kitwp_chat_widget', 20 );
