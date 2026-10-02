<?php
/**
 * Lead forms run by Contact Form 7, kept 1:1 with the static form and editable in CF7.
 *
 * Contact > Contact Forms holds the forms (seeded from _setup/seed/forms.json). Quote Form: the Form tab is the
 * form people see (labels, placeholders, options, button) and the Mail tab is the email (To, From, Subject, Bcc,
 * Reply-To and the HTML body with mail-tags). The theme prints CF7's text, email, tel, url, select, textarea and
 * hidden tags in the static markup and drops CF7's wrapper (kitwp_cf7_control, kitwp_cf7_clean). Per page it adds
 * the service options, the source, the pop-up's "qm-" id prefix and the compact form without email. As on the
 * static site the form posts normally (JavaScript on or off) and lands on KITWP_THANK_YOU with a 303. Chat Lead: the
 * chat widget posts FormData to CF7's REST endpoint; its Form tab is the field list and its Mail tab the email.
 *
 * Field names are the static form's: name, phone, email, postcode, service, when, whenDT, msg, source, and the
 * honeypot "company". Change kitwp_lead_data() and the mail-tags if the site's form differs.
 *
 * @package kitwp
 */

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
 * reCAPTCHA v3 for the lead forms and the chat. CF7's own script only fills forms with its "wpcf7-form" class,
 * which the static markup does not have, so on submit the theme asks Google for a fresh token, puts it in CF7's
 * hidden _wpcf7_recaptcha_response field and then submits (tokens last two minutes). window.kitwpRecaptcha() gives
 * the chat a token the same way. No key in Contact > Integration: nothing changes.
 *
 * KITWP_RECAPTCHA_LAZY false (default, proven on a live site): CF7 loads Google's script on every page.
 * KITWP_RECAPTCHA_LAZY true: CF7's script is dropped and Google's (about 400 KB) loads the first time someone
 * touches a lead form or the chat; after 10 seconds without Google the form still submits. Faster on phones, but
 * tested locally only: retest every form on live (keys only work on their domains).
 *
 * @return void
 */
function kitwp_recaptcha_submit_script() {
	$key = kitwp_recaptcha_sitekey();
	if ( '' === $key || ! wp_script_is( 'google-recaptcha', 'registered' ) ) {
		return;
	}
	$submit = 'document.addEventListener("submit",function(e){var f=e.target,i=f.querySelector&&f.querySelector("input[name=\'_wpcf7_recaptcha_response\']");'
		. 'if(!i||!f.classList.contains(C)||f.dataset.kitwpRc)return;e.preventDefault();var d=0,go=function(t){if(d++)return;if(t)i.value=t;f.dataset.kitwpRc="1";f.submit()};'
		. 'setTimeout(function(){go("")},10000);window.kitwpRecaptcha().then(go,function(){go("")})},true);';
	$head   = 'var K=' . wp_json_encode( $key ) . ',C=' . wp_json_encode( KITWP_FORM_CLASS ) . ';';
	if ( ! KITWP_RECAPTCHA_LAZY ) {
		wp_add_inline_script(
			'wpcf7-recaptcha',
			'(function(){' . $head
			. 'window.kitwpRecaptcha=function(){return new Promise(function(ok,no){if(typeof grecaptcha==="undefined"){no();return}grecaptcha.ready(function(){grecaptcha.execute(K,{action:"contactform"}).then(ok,no)})})};'
			. $submit . '})();'
		);
		return;
	}
	$api = wp_scripts()->registered['google-recaptcha']->src;
	wp_dequeue_script( 'wpcf7-recaptcha' );
	wp_register_script( 'kitwp-recaptcha', false, [], null, [ 'in_footer' => true ] ); // phpcs:ignore WordPress.WP.EnqueuedResourceParameters.MissingVersion -- inline only.
	wp_enqueue_script( 'kitwp-recaptcha' );
	wp_add_inline_script(
		'kitwp-recaptcha',
		'(function(){' . $head . 'var U=' . wp_json_encode( $api, JSON_UNESCAPED_SLASHES ) . ',W=' . wp_json_encode( 'form.' . KITWP_FORM_CLASS . ( '' !== KITWP_CHAT_SELECTOR ? ',' . KITWP_CHAT_SELECTOR : '' ) ) . ',p=null;'
		. 'function load(){if(!p){p=new Promise(function(ok,no){var s=document.createElement("script");s.src=U;s.async=true;s.onload=function(){grecaptcha.ready(ok)};s.onerror=function(){p=null;no()};document.head.appendChild(s)})}return p}'
		. 'window.kitwpRecaptcha=function(){return load().then(function(){return grecaptcha.execute(K,{action:"contactform"})})};'
		. 'var warm=function(e){var t=e.target;if(t&&t.closest&&t.closest(W))load()};'
		. '["focusin","pointerdown","touchstart"].forEach(function(n){document.addEventListener(n,warm,{capture:true,passive:true})});'
		. $submit . '})();'
	);
}
add_action( 'wp_enqueue_scripts', 'kitwp_recaptcha_submit_script', 30 );

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
	return kitwp_cf7_clean( $html, $ctx['prefix'] );
}

/**
 * Turn CF7's form output into the static form: the bare form element (class KITWP_FORM_CLASS, posts to the page), no CF7
 * wrapper, screen-reader box or fieldset; CF7's hidden fields stay. A field marked for removal (compact form) goes
 * with its wrapper. After a failed post, CF7's message shows as a form note. Ids and label "for" get the prefix.
 *
 * @param string $html   CF7 form HTML.
 * @param string $prefix Id prefix.
 * @return string
 */
function kitwp_cf7_clean( $html, $prefix ) {
	$html = (string) preg_replace( '#^.*?<form\b[^>]*>#s', '<form class="' . esc_attr( KITWP_FORM_CLASS ) . '" action="" method="post">', $html, 1 );
	$html = (string) preg_replace( '#</form>.*$#s', '</form>', $html, 1 );
	$html = str_replace( [ '<fieldset class="hidden-fields-container">', '</fieldset>' ], '', $html );
	$html = (string) preg_replace( '/>\s+</', '><', $html );
	$html = (string) preg_replace( '#<div class="field">(?:(?!</div>).)*<!--kitk-drop-->(?:(?!</div>).)*</div>#s', '', $html );
	$html = (string) preg_replace_callback(
		'#<div class="wpcf7-response-output"[^>]*>(.*?)</div>#s',
		static function ( $m ) {
			$text = trim( wp_strip_all_tags( $m[1] ) );
			return '' === $text ? '' : '<p class="form-note" role="alert">' . esc_html( $text ) . '</p>';
		},
		$html
	);
	if ( '' !== $prefix ) {
		$html = (string) preg_replace( '/ (id|for)="(?!wpcf7)([A-Za-z][-A-Za-z0-9_]*)"/', ' $1="' . esc_attr( $prefix ) . '$2"', $html );
	}
	return $html;
}

/**
 * CF7 form-tag handler for text, email, tel, url, textarea, select and hidden. While the theme prints a lead form
 * the tag comes out in the static markup (attribute order as the static site, browser "required" kept, values
 * refilled after a failed post, CF7's error message under the field); any other CF7 form gets CF7's own markup.
 *
 * @param WPCF7_FormTag $tag Form tag.
 * @return string
 */
function kitwp_cf7_control( $tag ) {
	$ctx = $GLOBALS['kitwp_form_ctx'] ?? null;
	if ( null === $ctx ) {
		$cf7 = [
			'select'   => 'wpcf7_select_form_tag_handler',
			'textarea' => 'wpcf7_textarea_form_tag_handler',
			'hidden'   => 'wpcf7_hidden_form_tag_handler',
		];
		$fn  = $cf7[ $tag->basetype ] ?? 'wpcf7_text_form_tag_handler';
		return function_exists( $fn ) ? (string) call_user_func( $fn, $tag ) : '';
	}
	if ( empty( $tag->name ) ) {
		return '';
	}
	$base = $tag->basetype;
	if ( 'email' === $base && $ctx['compact'] ) {
		return '<!--kitk-drop-->';
	}
	$name     = $tag->name;
	$id       = (string) $tag->get_option( 'id', 'id', true );
	$id_attr  = '' !== $id ? ' id="' . esc_attr( $id ) . '"' : '';
	$hangover = wpcf7_get_hangover( $name );
	$value    = is_scalar( $hangover ) ? (string) $hangover : '';
	$error    = trim( wp_strip_all_tags( (string) wpcf7_get_validation_error( $name ) ) );
	$tip      = '' !== $error ? '<span class="form-note" role="alert">' . esc_html( $error ) . '</span>' : '';
	$holder   = $tag->has_option( 'placeholder' ) && isset( $tag->values[0] ) ? (string) $tag->values[0] : '';
	$required = $tag->is_required() ? ' required' : '';

	if ( 'hidden' === $base ) {
		$hidden = 'source' === $name ? $ctx['source'] : (string) ( $tag->values[0] ?? '' );
		return '<input type="hidden" name="' . esc_attr( $name ) . '" value="' . esc_attr( $hidden ) . '">';
	}
	if ( 'select' === $base ) {
		$items = array_map( 'strval', (array) $tag->labels );
		$first = $tag->has_option( 'first_as_label' ) ? (string) array_shift( $items ) : '';
		if ( 'service' === $name ) {
			$items = $ctx['options'];
		}
		$out = '<select' . $id_attr . ' name="' . esc_attr( $name ) . '"' . $required . '>';
		if ( '' !== $first ) {
			$out .= '<option value="" disabled' . ( '' === $value ? ' selected' : '' ) . '>' . esc_html( $first ) . '</option>';
		}
		foreach ( $items as $item ) {
			$out .= '<option' . ( '' !== $value && $value === $item ? ' selected' : '' ) . '>' . esc_html( $item ) . '</option>';
		}
		return $out . '</select>' . $tip;
	}
	if ( 'textarea' === $base ) {
		return '<textarea' . $id_attr . ' name="' . esc_attr( $name ) . '"' . ( '' !== $holder ? ' placeholder="' . esc_attr( $holder ) . '"' : '' ) . $required . '>' . esc_textarea( $value ) . '</textarea>' . $tip;
	}
	$tabindex = $tag->get_option( 'tabindex', 'signed_int', true );
	$auto     = $tag->get_autocomplete_option();
	return '<input' . $id_attr . ' type="' . esc_attr( 'text' === $base ? 'text' : $base ) . '"'
		. ( false !== $tabindex && '' !== (string) $tabindex ? ' tabindex="' . esc_attr( (string) $tabindex ) . '"' : '' )
		. ( '' !== $holder ? ' placeholder="' . esc_attr( $holder ) . '"' : '' )
		. $required
		. ( $auto ? ' autocomplete="' . esc_attr( $auto ) . '"' : '' )
		. ' name="' . esc_attr( $name ) . '"'
		. ( '' !== $value ? ' value="' . esc_attr( $value ) . '"' : '' )
		. '>' . $tip;
}

/**
 * Use kitwp_cf7_control() for CF7's field tags: CF7's own are removed first (add() never replaces a type).
 *
 * @return void
 */
function kitwp_cf7_register_controls() {
	foreach ( [ 'text', 'text*', 'email', 'email*', 'url', 'url*', 'tel', 'tel*', 'textarea', 'textarea*', 'select', 'select*', 'hidden' ] as $type ) {
		wpcf7_remove_form_tag( $type );
	}
	wpcf7_add_form_tag( [ 'text', 'text*', 'email', 'email*', 'url', 'url*', 'tel', 'tel*', 'textarea', 'textarea*' ], 'kitwp_cf7_control', [ 'name-attr' => true ] );
	wpcf7_add_form_tag(
		[ 'select', 'select*' ],
		'kitwp_cf7_control',
		[
			'name-attr'         => true,
			'selectable-values' => true,
		]
	);
	wpcf7_add_form_tag(
		'hidden',
		'kitwp_cf7_control',
		[
			'name-attr'      => true,
			'display-hidden' => true,
		]
	);
}
add_action( 'wpcf7_init', 'kitwp_cf7_register_controls', 20, 0 );

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
	$posted              = sanitize_text_field( wp_unslash( $_POST['service'] ) ); // phpcs:ignore WordPress.Security.NonceVerification.Missing
	$tag['values'][]     = $posted;
	$tag['raw_values'][] = $posted;
	$tag['labels'][]     = $posted;
	return $tag;
}
add_filter( 'wpcf7_form_tag', 'kitwp_cf7_service_values' );

/**
 * No automatic paragraphs in the lead forms (the Form tab is the static markup).
 *
 * @param bool $autop CF7 setting.
 * @return bool
 */
function kitwp_cf7_autop( $autop ) {
	return isset( $GLOBALS['kitwp_form_ctx'] ) ? false : $autop;
}
add_filter( 'wpcf7_autop_or_not', 'kitwp_cf7_autop' );

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
	} elseif ( isset( $_GET['name'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended
		$query_vars['name'] = sanitize_title( wp_unslash( $_GET['name'] ) ); // phpcs:ignore WordPress.Security.NonceVerification.Recommended
	} else {
		unset( $query_vars['name'] );
	}
	return $query_vars;
}
add_filter( 'request', 'kitwp_lead_query_vars' );

/**
 * Honeypot, as the static handler: a filled "company" field is a bot. Marked as spam, nothing is sent, and the
 * visitor still lands on /thank-you/.
 *
 * @param bool              $spam       Spam so far.
 * @param WPCF7_Submission  $submission Submission.
 * @return bool
 */
function kitwp_lead_honeypot( $spam, $submission ) {
	if ( kitwp_is_lead_form( $submission->get_contact_form() ) && '' !== trim( (string) $submission->get_posted_data( 'company' ) ) ) {
		$GLOBALS['kitwp_lead_honeypot'] = true;
		return true;
	}
	return $spam;
}
add_filter( 'wpcf7_spam', 'kitwp_lead_honeypot', 1, 2 );

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
		error_log( '[lead] mail failed: ' . wp_json_encode( kitwp_lead_data( $submission ) ) ); // phpcs:ignore WordPress.PHP.DevelopmentFunctions.error_log_error_log
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
 * The lead, as the static handler reads it.
 *
 * @param WPCF7_Submission $submission Submission.
 * @return array<string, string>
 */
function kitwp_lead_data( $submission ) {
	$field = static function ( $key, $max = 500 ) use ( $submission ) {
		$value = $submission->get_posted_data( $key );
		$value = is_array( $value ) ? (string) wpcf7_flat_join( $value ) : ( is_scalar( $value ) ? (string) $value : '' );
		$value = trim( $value );
		return mb_substr( $value, 0, $max, 'UTF-8' );
	};
	$lead           = [];
	foreach ( [ 'name', 'phone', 'email', 'postcode', 'service', 'when', 'whenDT', 'source' ] as $key ) {
		$lead[ $key ] = $field( $key );
	}
	$lead['msg']    = $field( 'msg', 5000 );
	$lead['source'] = '' !== $lead['source'] ? $lead['source'] : 'website';
	$lead['page']   = mb_substr( (string) $submission->get_meta( 'url' ), 0, 500, 'UTF-8' );
	return $lead;
}

/**
 * HTML-escape for the email, exactly as the static handler.
 *
 * @param string $text Text.
 * @return string
 */
function kitwp_mail_h( $text ) {
	return htmlspecialchars( (string) $text, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8' );
}

/**
 * Values the lead email needs beyond the fields, worked out as the static handler did.
 *
 * @param array<string, string> $lead From kitwp_lead_data().
 * @return array<string, string> Plain text values.
 */
function kitwp_lead_extras( $lead ) {
	$oneline = static function ( $text ) {
		return trim( (string) preg_replace( '/\s*[\r\n]+\s*/', ' ', $text ) );
	};
	$tz      = wp_timezone();
	// Dates in the site's own format and language (Settings > General), so the email reads right in any country.
	$format = (string) apply_filters( 'kitwp_lead_date_format', get_option( 'date_format' ) . ', ' . get_option( 'time_format' ) );
	$labels = (array) apply_filters(
		'kitwp_lead_via_labels',
		[
			'chat'  => 'Chat widget',
			'popup' => 'Pop-up form',
			'form'  => 'Website form',
		]
	);
	$when   = $lead['when'];
	if ( '' !== $lead['whenDT'] ) {
		$dt     = DateTime::createFromFormat( 'Y-m-d\TH:i', $lead['whenDT'], $tz );
		$picked = $dt ? wp_date( $format, $dt->getTimestamp(), $tz ) : $lead['whenDT'];
		$when   = ( '' === $when || preg_match( '/pick a date/i', $when ) ) ? $picked : $when . ' (' . $picked . ')';
	}
	$src = $lead['source'];
	return [
		'when'      => $when,
		'via'       => (string) ( str_starts_with( $src, 'chat:' ) ? $labels['chat'] : ( str_starts_with( $src, 'popup:' ) ? $labels['popup'] : $labels['form'] ) ),
		'tel'       => (string) preg_replace( '/[^0-9+]/', '', $lead['phone'] ),
		'received'  => wp_date( $format, null, $tz ),
		'preheader' => $oneline( 'New enquiry from ' . $lead['name'] . ( '' !== $lead['service'] ? ', ' . $lead['service'] : '' ) . ( '' !== $lead['postcode'] ? ', ' . $lead['postcode'] : '' ) ),
	];
}

/**
 * Mail-tags for the lead email (Mail tab), on top of the field tags:
 * [_kitk_subject] the Subject line, [_kitk_preheader], [_kitk_tel] phone digits, [_kitk_email] email link,
 * [_kitk_when] When Needed with the picked date, [_kitk_via] Submitted Via, [_kitk_page] page link,
 * [_kitk_received] site time, [_kitk_logo] logo URL, [_kitk_site] site URL, [_kitk_year].
 * With "Exclude lines with blank mail-tags" on, a row whose tags are all empty is left out, as the static email.
 *
 * @param string|null    $output   Replacement so far.
 * @param string         $name     Tag name.
 * @param bool           $html     HTML body.
 * @param WPCF7_MailTag  $mail_tag Mail tag.
 * @return string|null
 */
function kitwp_lead_special_tags( $output, $name, $html, $mail_tag = null ) {
	unset( $mail_tag );
	$submission = class_exists( 'WPCF7_Submission' ) ? WPCF7_Submission::get_instance() : null;
	// A lead field this form does not have (the quote form has no postcode): empty, so "Exclude lines with blank
	// mail-tags" drops its row instead of printing "[postcode]".
	if ( $submission && null === $output && in_array( (string) $name, kitwp_lead_fields(), true ) && null === $submission->get_posted_data( (string) $name ) ) {
		return '';
	}
	if ( ! str_starts_with( (string) $name, '_kitk_' ) || ! $submission ) {
		return $output;
	}
	$lead  = kitwp_lead_data( $submission );
	$extra = kitwp_lead_extras( $lead );
	$h     = $html ? 'kitwp_mail_h' : 'strval';
	$link  = 'color:' . KITWP_BRAND_COLOUR . ';';
	switch ( $name ) {
		case '_kitk_subject':
			$mail = WPCF7_Mail::get_current();
			return $mail ? $h( $mail->get( 'subject', true ) ) : '';
		case '_kitk_preheader':
			return $h( $extra['preheader'] );
		case '_kitk_tel':
			return $h( $extra['tel'] );
		case '_kitk_email':
			if ( '' === $lead['email'] ) {
				return '';
			}
			return $html && is_email( $lead['email'] ) ? '<a href="mailto:' . kitwp_mail_h( $lead['email'] ) . '" style="' . $link . '">' . kitwp_mail_h( $lead['email'] ) . '</a>' : $h( $lead['email'] );
		case '_kitk_when':
			return $h( $extra['when'] );
		case '_kitk_via':
			return $h( $extra['via'] );
		case '_kitk_page':
			if ( '' === $lead['page'] ) {
				return '';
			}
			return $html && preg_match( '#^https?://#i', $lead['page'] ) ? '<a href="' . kitwp_mail_h( $lead['page'] ) . '" style="' . $link . '">' . kitwp_mail_h( $lead['page'] ) . '</a>' : $h( $lead['page'] );
		case '_kitk_received':
			return $h( $extra['received'] );
		case '_kitk_logo':
			return $h( get_theme_file_uri( 'assets/email/email-logo.png' ) );
		case '_kitk_site':
			return $h( untrailingslashit( home_url() ) );
		case '_kitk_year':
			return wp_date( 'Y' );
	}
	return $output;
}
add_filter( 'wpcf7_special_mail_tags', 'kitwp_lead_special_tags', 10, 4 );

/**
 * Field mail-tags in the lead emails' HTML body are escaped as the static handler did (no curly quotes), and the
 * message keeps its line breaks.
 *
 * @param string|null   $replaced  Replacement so far.
 * @param mixed         $submitted Posted value.
 * @param bool          $html      HTML body.
 * @param WPCF7_MailTag $mail_tag  Mail tag.
 * @return string|null
 */
function kitwp_lead_mail_tag( $replaced, $submitted, $html, $mail_tag ) {
	if ( ! $html || null === $submitted || ! kitwp_is_lead_form( wpcf7_get_current_contact_form() ) ) {
		return $replaced;
	}
	$text = kitwp_mail_h( trim( (string) wpcf7_flat_join( $submitted ) ) );
	return 'msg' === $mail_tag->field_name() ? nl2br( $text ) : $text;
}
add_filter( 'wpcf7_mail_tag_replaced', 'kitwp_lead_mail_tag', 20, 4 );

/**
 * Reply-To from the Mail tab is kept only when the visitor gave a valid email (the static handler's rule).
 *
 * @param array<string, mixed> $components Mail parts.
 * @param WPCF7_ContactForm    $form       Contact form.
 * @param WPCF7_Mail           $mail       Mail template.
 * @return array<string, mixed>
 */
function kitwp_lead_mail( $components, $form, $mail ) {
	$submission = class_exists( 'WPCF7_Submission' ) ? WPCF7_Submission::get_instance() : null;
	if ( ! $submission || ! kitwp_is_lead_form( $form ) || 'mail' !== $mail->name() ) {
		return $components;
	}
	$email   = trim( (string) $submission->get_posted_data( 'email' ) );
	$headers = [];
	foreach ( explode( "\n", str_replace( "\r\n", "\n", (string) $components['additional_headers'] ) ) as $line ) {
		$line = trim( $line );
		if ( '' === $line || ( 0 === stripos( $line, 'reply-to:' ) && ! is_email( $email ) ) ) {
			continue;
		}
		$headers[] = $line;
	}
	$components['additional_headers'] = implode( "\n", $headers );
	return $components;
}
add_filter( 'wpcf7_mail_components', 'kitwp_lead_mail', 10, 3 );

/**
 * For emails from the site's own domain: envelope sender = From, a Message-ID on the domain and one HTML part
 * (CF7's msgHTML() adds a plain-text part; the static handler sent one part, which the host's MailChannels filter
 * accepts). Runs after CF7's own phpmailer_init (priority 10).
 *
 * @param PHPMailer\PHPMailer\PHPMailer $phpmailer Mailer.
 * @return void
 */
function kitwp_mail_envelope( $phpmailer ) {
	// phpcs:disable WordPress.NamingConventions.ValidVariableName.UsedPropertyNotSnakeCase -- PHPMailer properties.
	if ( str_ends_with( strtolower( (string) $phpmailer->From ), '@' . kitwp_site_domain() ) ) {
		if ( '' === (string) $phpmailer->Sender ) {
			$phpmailer->Sender = $phpmailer->From;
		}
		$phpmailer->MessageID = '<' . bin2hex( random_bytes( 12 ) ) . '@' . kitwp_site_domain() . '>';
		$phpmailer->AltBody   = '';
	}
	// phpcs:enable
}
add_action( 'phpmailer_init', 'kitwp_mail_envelope', 20 );

/**
 * Local only (WP_ENVIRONMENT_TYPE "local"): every email goes to the site admin email only, never to the client or
 * the Bcc list, so Laragon's Mail Catcher shows it (click the notification to open it) and nothing reaches the
 * real recipients even if Laragon's Mail Sender is ever set up. The real To and Bcc are kept in an
 * X-Kitwp-Original-To header, and a copy with the real headers is saved to _setup/mail/ as an .html file.
 *
 * @param array<string, mixed> $atts wp_mail() arguments.
 * @return array<string, mixed>
 */
function kitwp_local_mail_capture( $atts ) {
	if ( 'local' !== wp_get_environment_type() ) {
		return $atts;
	}
	$headers = is_array( $atts['headers'] ) ? $atts['headers'] : explode( "\n", str_replace( "\r\n", "\n", (string) $atts['headers'] ) );
	$to      = is_array( $atts['to'] ) ? $atts['to'] : explode( ',', (string) $atts['to'] );
	$meta    = 'To: ' . implode( ', ', $to ) . "\nSubject: " . $atts['subject'] . "\n" . implode( "\n", $headers );
	$dir     = ABSPATH . '_setup/mail';
	wp_mkdir_p( $dir );
	file_put_contents( $dir . '/' . gmdate( 'Ymd-His' ) . '-' . substr( md5( (string) wp_rand() ), 0, 6 ) . '.html', '<!--' . "\n" . str_replace( '--', '- -', $meta ) . "\n-->\n" . $atts['message'] ); // phpcs:ignore WordPress.WP.AlternativeFunctions.file_system_operations_file_put_contents

	$original = array_map( 'trim', $to );
	$kept     = [];
	foreach ( $headers as $line ) {
		$line = trim( (string) $line );
		if ( preg_match( '/^(bcc|cc):\s*(.+)$/i', $line, $match ) ) {
			$original[] = strtolower( $match[1] ) . ' ' . $match[2];
			continue;
		}
		if ( '' !== $line ) {
			$kept[] = $line;
		}
	}
	$kept[]          = 'X-Kitwp-Original-To: ' . implode( '; ', $original );
	$atts['to']      = (string) get_option( 'admin_email' );
	$atts['headers'] = $kept;
	return $atts;
}
add_filter( 'wp_mail', 'kitwp_local_mail_capture', 999 );

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
