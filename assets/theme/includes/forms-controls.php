<?php
/**
 * Lead forms: CF7's field tags printed in the static form's markup (attribute order, required, values refilled and
 * CF7's error under a field after a failed post), and CF7's form output cut down to the static form element.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

/**
 * Turn CF7's form output into the static form: the bare form element (class KITWP_FORM_CLASS, posts to the page), no CF7
 * wrapper, screen-reader box or fieldset; CF7's hidden fields stay. A field marked for removal (compact form) goes
 * with its wrapper. After a failed post, CF7's message shows as a form note that screen readers announce (a spam,
 * reCAPTCHA or aborted result gets the phone number too, see kitwp_lead_failed_note()). Ids and label "for" get
 * the prefix.
 *
 * @param string $html   CF7 form HTML.
 * @param string $prefix Id prefix.
 * @param string $status Status of this form's submission on this request ('' when it was not posted).
 * @return string
 */
function kitwp_cf7_clean( $html, $prefix, $status = '' ) {
	$html = (string) preg_replace( '#^.*?<form\b[^>]*>#s', '<form class="' . esc_attr( KITWP_FORM_CLASS ) . '" action="" method="post">', $html, 1 );
	$html = (string) preg_replace( '#</form>.*$#s', '</form>', $html, 1 );
	$html = str_replace( [ '<fieldset class="hidden-fields-container">', '</fieldset>' ], '', $html );
	$html = (string) preg_replace( '/>\s+</', '><', $html );
	$html = (string) preg_replace( '#<div class="field">(?:(?!</div>).)*<!--kitk-drop-->(?:(?!</div>).)*</div>#s', '', $html );
	$html = (string) preg_replace_callback(
		'#<div class="wpcf7-response-output"[^>]*>(.*?)</div>#s',
		static function ( $m ) use ( $status ) {
			// CF7 escaped the text already: decoded first, so it is escaped once, not twice.
			return kitwp_lead_failed_note( html_entity_decode( wp_strip_all_tags( $m[1] ), ENT_QUOTES, 'UTF-8' ), $status );
		},
		$html
	);
	if ( '' !== $prefix ) {
		$html = (string) preg_replace( '/ (id|for)="(?!wpcf7)([A-Za-z][-A-Za-z0-9_]*)"/', ' $1="' . esc_attr( $prefix ) . '$2"', $html );
	}
	return $html;
}

/**
 * The form note after a failed post (role="alert", so screen readers announce it). When CF7 stopped the post (spam,
 * a reCAPTCHA fail, an aborted send) the visitor cannot fix it by editing a field, so the note also gives the
 * phone number from Theme Settings: "{phone}" in the CF7 message (Messages tab) becomes the tel: link, else
 * "Or call ..." is added. A spam result for the honeypot never shows: that post lands on /thank-you/.
 *
 * @param string $text   CF7's message, plain text.
 * @param string $status Submission status.
 * @return string
 */
function kitwp_lead_failed_note( $text, $status ) {
	$text    = trim( (string) $text );
	$stopped = in_array( $status, [ 'spam', 'aborted', 'mail_failed' ], true );
	if ( '' === $text && $stopped ) {
		$text = __( 'Sorry, your message could not be sent.', 'kitwp' );
	}
	if ( '' === $text ) {
		return '';
	}
	$phone = kitwp_phone();
	$tel   = kitwp_tel();
	$link  = '' !== $phone && '' !== $tel ? '<a href="' . esc_url( 'tel:' . $tel ) . '">' . esc_html( $phone ) . '</a>' : '';
	$parts = explode( '{phone}', $text, 2 );
	$body  = esc_html( $parts[0] );
	if ( isset( $parts[1] ) ) {
		$body .= ( '' !== $link ? $link : esc_html( $phone ) ) . esc_html( $parts[1] );
	} elseif ( $stopped && '' !== $link ) {
		/* translators: %s: the business phone number as a link. */
		$body .= ' ' . sprintf( esc_html__( 'Or call %s.', 'kitwp' ), $link );
	}
	return '<p class="form-note" role="alert">' . $body . '</p>';
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
