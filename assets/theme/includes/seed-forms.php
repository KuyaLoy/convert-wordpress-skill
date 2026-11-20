<?php
/**
 * Seeder, forms: the CF7 lead forms and their branded emails (forms.json and the files it names). Local copies only.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

if ( 'local' !== wp_get_environment_type() ) {
	return;
}

/**
 * The Contact Form 7 forms from forms.json, for example:
 *   { "quote": { "title": "Quote Form", "form_file": "quote-form.txt", "body_file": "lead-email.html",
 *                "subject": "New Enquiry from [name] - [service]", "sender": "Site <no-reply@domain>",
 *                "recipient": "client@example.com", "bcc": "a@x, b@x", "reply_to": "[email]" },
 *     "chat":  { ... "form_file": "chat-form.txt", "subject": "New Chat Enquiry from [name] - [service]" } }
 * The Form tab comes from form_file and the Mail tab body from body_file (the full HTML email with mail-tags);
 * rows with blank mail-tags are left out ("Exclude lines with blank mail-tags").
 * Optional auto-reply (Mail (2)) to the visitor: "autoreply_file" (the same branded HTML shell as the lead email,
 * autoreply-email.html), "autoreply_subject", "autoreply_to" (default [email]), "autoreply_reply_to" (the client).
 *
 * @return array<string, array{title: string, form: string, mail: array<string, mixed>}>
 */
function kitwp_seed_form_defs() {
	$dir  = trailingslashit( kitwp_seed_dir() );
	$read = static function ( $file ) use ( $dir ) {
		$file = sanitize_file_name( (string) $file );
		return '' !== $file && is_readable( $dir . $file ) ? trim( (string) file_get_contents( $dir . $file ) ) : ''; // phpcs:ignore WordPress.WP.AlternativeFunctions.file_get_contents_file_get_contents -- local seed file.
	};
	$defs = [];
	foreach ( (array) kitwp_seed_json( 'forms.json' ) as $key => $def ) {
		$headers = [];
		if ( ! empty( $def['bcc'] ) ) {
			$headers[] = 'Bcc: ' . $def['bcc'];
		}
		if ( ! empty( $def['reply_to'] ) ) {
			$headers[] = 'Reply-To: ' . $def['reply_to'];
		}
		$defs[ sanitize_key( (string) $key ) ] = [
			'title' => (string) ( $def['title'] ?? $key ),
			'form'  => $read( $def['form_file'] ?? '' ),
			'mail'  => [
				'active'             => true,
				'subject'            => (string) ( $def['subject'] ?? '' ),
				'sender'             => (string) ( $def['sender'] ?? '' ),
				'recipient'          => (string) ( $def['recipient'] ?? '' ),
				'body'               => $read( $def['body_file'] ?? '' ),
				'additional_headers' => implode( "\n", $headers ),
				'attachments'        => '',
				'use_html'           => true,
				'exclude_blank'      => true,
			],
			'mail_2' => [
				'active'             => '' !== (string) ( $def['autoreply_file'] ?? '' ),
				'subject'            => (string) ( $def['autoreply_subject'] ?? '' ),
				'sender'             => (string) ( $def['sender'] ?? '' ),
				'recipient'          => (string) ( $def['autoreply_to'] ?? '[email]' ),
				'body'               => $read( $def['autoreply_file'] ?? '' ),
				'additional_headers' => ! empty( $def['autoreply_reply_to'] ) ? 'Reply-To: ' . $def['autoreply_reply_to'] : '',
				'attachments'        => '',
				'use_html'           => true,
				'exclude_blank'      => false,
			],
		];
	}
	return $defs;
}

/**
 * Why a form definition cannot be seeded ('' when it can): the form and the lead email are required, and every
 * email (the lead email and the auto-reply) must be the branded HTML template, a full HTML document, never plain text.
 *
 * @param string               $key Form key in forms.json.
 * @param array<string, mixed> $def Definition from kitwp_seed_form_defs().
 * @return string
 */
function kitwp_seed_form_problem( $key, $def ) {
	if ( '' === $def['form'] || '' === $def['mail']['body'] ) {
		return 'form or email file missing for "' . $key . '" (see forms.json)';
	}
	$emails = [ 'body_file' => $def['mail']['body'] ];
	if ( $def['mail_2']['active'] ) {
		$emails['autoreply_file'] = $def['mail_2']['body'];
	}
	foreach ( $emails as $file => $body ) {
		if ( ! preg_match( '/<html[\s>]/i', (string) $body ) ) {
			return $file . ' of "' . $key . '" is not the branded HTML email (a full HTML document)';
		}
	}
	return '';
}

/**
 * Hash of a CF7 form's seeded properties, as stored.
 *
 * @param WPCF7_ContactForm $form Contact form.
 * @return string
 */
function kitwp_seed_form_hash( $form ) {
	return md5( (string) wp_json_encode( [ $form->title(), $form->prop( 'form' ), $form->prop( 'mail' ) ] ) );
}

/**
 * Create the Quote Form and the Chat Lead in Contact Form 7. A form edited in the admin since it was seeded is
 * left as it is ("kept"); an untouched one is updated when the seed changes.
 *
 * @return array<string, int>
 */
function kitwp_seed_forms() {
	$report = [
		'created' => 0,
		'updated' => 0,
		'same'    => 0,
		'kept'    => 0,
	];
	if ( ! class_exists( 'WPCF7_ContactForm' ) ) {
		return [ 'contact form 7 not active' => 1 ];
	}
	$ids = (array) get_option( 'kitwp_cf7_forms', [] );
	foreach ( kitwp_seed_form_defs() as $key => $def ) {
		$problem = kitwp_seed_form_problem( $key, $def );
		if ( '' !== $problem ) {
			return [ $problem => 1 ];
		}
		if ( ! $def['mail_2']['active'] ) {
			$report[ 'no auto-reply for "' . $key . '" (add autoreply_file in forms.json)' ] = 1;
		}
		$seed = md5( (string) wp_json_encode( $def ) );
		$form = ! empty( $ids[ $key ] ) ? wpcf7_contact_form( (int) $ids[ $key ] ) : null;
		if ( $form ) {
			if ( kitwp_seed_form_hash( $form ) !== get_post_meta( $form->id(), '_kitk_seed_saved', true ) ) {
				++$report['kept'];
				continue;
			}
			if ( get_post_meta( $form->id(), '_kitk_seed_hash', true ) === $seed ) {
				++$report['same'];
				continue;
			}
			++$report['updated'];
		} else {
			$form = WPCF7_ContactForm::get_template(
				[
					'title'  => $def['title'],
					'locale' => get_locale(),
				]
			);
			++$report['created'];
		}
		$form->set_title( $def['title'] );
		$form->set_properties(
			[
				'form'   => $def['form'],
				'mail'   => $def['mail'],
				'mail_2' => $def['mail_2'],
			]
		);
		$id          = (int) $form->save();
		$ids[ $key ] = $id;
		update_post_meta( $id, '_kitk_seed_hash', $seed );
		update_post_meta( $id, '_kitk_seed_saved', kitwp_seed_form_hash( wpcf7_contact_form( $id ) ) );
	}
	update_option( 'kitwp_cf7_forms', $ids, false );
	return $report;
}
