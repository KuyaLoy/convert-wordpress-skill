<?php
/**
 * Lead forms: the branded lead email and auto-reply. The lead as the static handler read it, the extra mail-tags
 * ([_kitk_...]), escaping, Reply-To and the envelope for mail from the site's own domain.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

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
 * The logo in the email header: Theme Settings > Branding "Email logo" (a PNG from the Media Library, seeded from
 * the static build), else the theme's assets/email/email-logo.png when that file exists. Neither: '' and the
 * emails show the logo's alt text instead of a broken image (kitwp_mail_no_empty_img()).
 *
 * @return string URL, or ''.
 */
function kitwp_email_logo_url() {
	$id  = (int) kitwp_setting( 'email_logo' );
	$url = $id ? (string) wp_get_attachment_url( $id ) : '';
	if ( '' !== $url ) {
		return $url;
	}
	return file_exists( get_theme_file_path( 'assets/email/email-logo.png' ) ) ? get_theme_file_uri( 'assets/email/email-logo.png' ) : '';
}

/**
 * An image whose src mail-tag came out empty (no email logo set) is replaced by its alt text in the same style, so
 * the lead email and the auto-reply never show a broken image.
 *
 * @param array<string, mixed> $components Mail parts.
 * @return array<string, mixed>
 */
function kitwp_mail_no_empty_img( $components ) {
	if ( empty( $components['body'] ) || ! is_string( $components['body'] ) ) {
		return $components;
	}
	$components['body'] = (string) preg_replace_callback(
		'#<img\b(?=[^>]*\ssrc\s*=\s*(["\'])\s*\1)[^>]*>#i',
		static function ( $m ) {
			$alt   = preg_match( '#\salt\s*=\s*"([^"]*)"#i', $m[0], $a ) ? $a[1] : '';
			$style = preg_match( '#\sstyle\s*=\s*"([^"]*)"#i', $m[0], $s ) ? $s[1] : '';
			return '' === $alt ? '' : '<span style="' . $style . '">' . $alt . '</span>';
		},
		$components['body']
	);
	return $components;
}
add_filter( 'wpcf7_mail_components', 'kitwp_mail_no_empty_img', 20 );

/**
 * The agency badge in the email footers: Theme Settings > Branding "Email badge" (a PNG at 2x from the Media
 * Library) and "Agency badge link", else the defaults in config.php (KITWP_EMAIL_BADGE*). "Hide agency badge"
 * hides it here too, only when the build recorded that the client asked (KITWP_BADGE_HIDE_NOTE).
 *
 * @return array{src: string, link: string, alt: string} Empty src or link: no badge.
 */
function kitwp_email_badge() {
	if ( kitwp_setting( 'agency_badge_hide' ) && '' !== KITWP_BADGE_HIDE_NOTE ) {
		return [
			'src'  => '',
			'link' => '',
			'alt'  => '',
		];
	}
	$id  = (int) kitwp_setting( 'email_badge' );
	$src = $id ? (string) wp_get_attachment_url( $id ) : '';
	$alt = $id ? trim( (string) get_post_meta( $id, '_wp_attachment_image_alt', true ) ) : '';
	return [
		'src'  => '' !== $src ? $src : ( '' !== KITWP_EMAIL_BADGE && file_exists( get_theme_file_path( KITWP_EMAIL_BADGE ) ) ? get_theme_file_uri( KITWP_EMAIL_BADGE ) : '' ),
		'link' => (string) ( kitwp_setting( 'agency_link' ) ? kitwp_setting( 'agency_link' ) : KITWP_EMAIL_BADGE_LINK ),
		'alt'  => '' !== $alt ? $alt : KITWP_EMAIL_BADGE_ALT,
	];
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
 * [_kitk_received] site time, [_kitk_logo] logo URL, [_kitk_site] site URL, [_kitk_year], [_kitk_name] the
 * sender's name (auto-reply greeting), [_kitk_badge] the agency badge for the footer of the lead email and the
 * auto-reply (KITWP_EMAIL_BADGE; empty when not set), [_kitk_source] the "Lead Attribution" table (the company
 * attribution standard's eleven rows, then the extra tags; kitwp_attribution_table()).
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
			return $h( kitwp_email_logo_url() );
		case '_kitk_site':
			return $h( untrailingslashit( home_url() ) );
		case '_kitk_source':
			return kitwp_attribution_table( (array) $submission->get_posted_data(), $lead['page'], $html );
		case '_kitk_year':
			return wp_date( 'Y' );
		case '_kitk_name':
			return $h( $lead['name'] );
		case '_kitk_badge':
			$badge = kitwp_email_badge();
			if ( ! $html || '' === $badge['src'] || '' === $badge['link'] ) {
				return '';
			}
			return '<a href="' . kitwp_mail_h( esc_url_raw( $badge['link'] ) ) . '" target="_blank" style="text-decoration:none;"><img src="' . kitwp_mail_h( $badge['src'] ) . '" width="' . (int) KITWP_EMAIL_BADGE_WIDTH . '" alt="' . kitwp_mail_h( $badge['alt'] ) . '" style="display:block;margin:0 auto;border:0;outline:none;width:' . (int) KITWP_EMAIL_BADGE_WIDTH . 'px;height:auto;color:#ffffff;font-size:12px;"></a>';
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
