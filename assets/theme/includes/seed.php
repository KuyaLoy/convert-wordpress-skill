<?php
/**
 * Seeder: media, Theme Settings, pages, menus, CF7 forms, Yoast and redirects from the static site's content.
 * Local copies only (WP_ENVIRONMENT_TYPE "local"): on any other environment this file does nothing.
 *
 * Seed files live in _setup/seed/ at the WordPress root (written by the exporters in _plan/tools/seed/, private and
 * never deployed): media.json, settings.json, template-pages.json, pages.json, menus.json, forms.json (+ the form and
 * email files it names), seo.json, og-images.json, redirects.json. Tools > Seeder runs them. Every step is
 * idempotent: run it twice, and the second run must report "same" (or "kept") everywhere.
 *
 * @package kitwp
 */

if ( 'local' !== wp_get_environment_type() ) {
	return;
}

/**
 * Seed folder.
 *
 * @return string
 */
function kitwp_seed_dir() {
	return defined( 'KITWP_SEED_DIR' ) ? KITWP_SEED_DIR : ABSPATH . '_setup/seed';
}

/**
 * Read a seed JSON file.
 *
 * @param string $file File name.
 * @return array<mixed>
 */
function kitwp_seed_json( $file ) {
	$path = trailingslashit( kitwp_seed_dir() ) . $file;
	if ( ! is_readable( $path ) ) {
		return [];
	}
	$data = json_decode( (string) file_get_contents( $path ), true ); // phpcs:ignore WordPress.WP.AlternativeFunctions.file_get_contents_file_get_contents -- local seed file.
	return is_array( $data ) ? $data : [];
}

/**
 * Store the width and height attributes the static site prints for an image when they differ from the file
 * (media.json attrWidth/attrHeight, for example when the static code prints a fixed 600 x 600). Returns true when
 * the meta changed.
 *
 * @param int                  $id   Attachment ID.
 * @param array<string, mixed> $item media.json entry.
 * @return bool
 */
function kitwp_seed_media_attr_size( $id, $item ) {
	$want = isset( $item['attrWidth'], $item['attrHeight'] ) ? (int) $item['attrWidth'] . 'x' . (int) $item['attrHeight'] : '';
	if ( (string) get_post_meta( $id, '_kitk_attr_size', true ) === $want ) {
		return false;
	}
	if ( '' === $want ) {
		delete_post_meta( $id, '_kitk_attr_size' );
	} else {
		update_post_meta( $id, '_kitk_attr_size', $want );
	}
	return true;
}

/**
 * Import the images in media.json with the static build's WebP files as the kitk-<width> sizes.
 *
 * @return array<string, int>
 */
function kitwp_seed_media() {
	require_once ABSPATH . 'wp-admin/includes/file.php';
	require_once ABSPATH . 'wp-admin/includes/media.php';
	require_once ABSPATH . 'wp-admin/includes/image.php';

	$report = [
		'created' => 0,
		'updated' => 0,
		'skipped' => 0,
		'failed'  => 0,
	];
	$files  = trailingslashit( kitwp_seed_dir() ) . 'files';

	// The static WebP files are attached below, so WordPress makes no sizes of its own for seeded images.
	add_filter( 'intermediate_image_sizes_advanced', '__return_empty_array', 99 );
	add_filter( 'big_image_size_threshold', '__return_false', 99 );

	foreach ( kitwp_seed_json( 'media.json' ) as $item ) {
		$existing = kitwp_media_by_source( $item['src'] );
		if ( $existing ) {
			if ( kitwp_seed_media_attr_size( $existing, $item ) ) {
				++$report['updated'];
			} else {
				++$report['skipped'];
			}
			continue;
		}
		$original = $files . $item['src'];
		$tmp      = wp_tempnam( basename( $item['src'] ) );
		if ( ! is_readable( $original ) || ! copy( $original, $tmp ) ) {
			++$report['failed'];
			continue;
		}
		$id = media_handle_sideload(
			[
				'name'     => basename( $item['src'] ),
				'tmp_name' => $tmp,
			],
			0,
			'',
			[ 'post_title' => (string) $item['alt'] ]
		);
		if ( is_wp_error( $id ) ) {
			wp_delete_file( $tmp );
			++$report['failed'];
			continue;
		}
		update_post_meta( $id, '_kitk_source', $item['src'] );
		update_post_meta( $id, '_wp_attachment_image_alt', (string) $item['alt'] );
		foreach ( (array) ( $item['meta'] ?? [] ) as $kitwp_key => $kitwp_value ) {
			update_post_meta( $id, '_kitk_' . sanitize_key( (string) $kitwp_key ), $kitwp_value ); // Extra flags the theme reads, for example flush_right.
		}
		kitwp_seed_media_attr_size( $id, $item );

		// Copy the static WebP widths next to the original and register them as the kitk-* sizes.
		$meta = wp_get_attachment_metadata( $id );
		$dir  = dirname( (string) get_attached_file( $id ) );
		$name = pathinfo( (string) get_attached_file( $id ), PATHINFO_FILENAME );
		$meta = is_array( $meta ) ? $meta : [];
		if ( empty( $meta['sizes'] ) ) {
			$meta['sizes'] = [];
		}
		foreach ( (array) $item['variants'] as $width => $variant ) {
			$from   = $files . $variant;
			$target = $name . '-kitk-' . $width . '.webp';
			if ( ! is_readable( $from ) || ! copy( $from, $dir . '/' . $target ) ) {
				continue;
			}
			$size = wp_getimagesize( $dir . '/' . $target );
			$meta['sizes'][ 'kitk-' . $width ] = [
				'file'      => $target,
				'width'     => $size ? (int) $size[0] : (int) $width,
				'height'    => $size ? (int) $size[1] : 0,
				'mime-type' => 'image/webp',
				'filesize'  => (int) filesize( $dir . '/' . $target ),
			];
		}
		wp_update_attachment_metadata( $id, $meta );
		++$report['created'];
	}

	remove_filter( 'intermediate_image_sizes_advanced', '__return_empty_array', 99 );
	remove_filter( 'big_image_size_threshold', '__return_false', 99 );
	return $report;
}

/**
 * Top-level Theme Settings field keys by name, read from the field group JSON.
 *
 * @return array<string, array<string, mixed>>
 */
function kitwp_seed_settings_fields() {
	$json  = get_stylesheet_directory() . '/acf-json/group_kitk_theme_settings.json';
	$group = json_decode( (string) file_get_contents( $json ), true ); // phpcs:ignore WordPress.WP.AlternativeFunctions.file_get_contents_file_get_contents -- theme file.
	$out   = [];
	foreach ( (array) ( $group['fields'] ?? [] ) as $field ) {
		if ( ! empty( $field['name'] ) ) {
			$out[ $field['name'] ] = $field;
		}
	}
	return $out;
}

/**
 * Replace static image paths with attachment IDs in a seed value, using the field definition.
 *
 * @param mixed                $value Seed value.
 * @param array<string, mixed> $field ACF field.
 * @return mixed
 */
function kitwp_seed_resolve( $value, $field ) {
	if ( 'image' === $field['type'] ) {
		return is_string( $value ) && '' !== $value ? kitwp_media_by_source( $value ) : $value;
	}
	if ( 'true_false' === $field['type'] ) {
		return $value ? 1 : 0; // ACF stores false as nothing; 0 is stored.
	}
	if ( in_array( $field['type'], [ 'group', 'repeater' ], true ) && is_array( $value ) ) {
		$subs = [];
		foreach ( (array) $field['sub_fields'] as $sub ) {
			$subs[ $sub['name'] ] = $sub;
		}
		$fix = function ( $row ) use ( $subs ) {
			foreach ( $row as $k => $v ) {
				if ( isset( $subs[ $k ] ) ) {
					$row[ $k ] = kitwp_seed_resolve( $v, $subs[ $k ] );
				}
			}
			return $row;
		};
		return 'group' === $field['type'] ? $fix( $value ) : array_map( $fix, $value );
	}
	return $value;
}

/**
 * Write the Theme Settings values. Only fields whose stored value differs are written.
 *
 * @return array<string, int>
 */
function kitwp_seed_settings() {
	$report = [
		'updated' => 0,
		'same'    => 0,
		'unknown' => 0,
	];
	$fields = kitwp_seed_settings_fields();
	foreach ( kitwp_seed_json( 'settings.json' ) as $name => $value ) {
		if ( ! isset( $fields[ $name ] ) ) {
			++$report['unknown'];
			continue;
		}
		$field  = $fields[ $name ];
		$value  = kitwp_seed_resolve( $value, $field );
		$stored = kitwp_seed_named( get_field( $field['key'], 'option', false ), $field );
		if ( 'group' === $field['type'] && is_array( $value ) && is_array( $stored ) ) {
			$stored = array_intersect_key( $stored, $value ); // Compare only the sub fields the seed sets.
		}
		$saved = null !== get_option( 'options_' . $name, null );
		if ( $saved && kitwp_seed_same( $stored, $value, $field ) ) {
			++$report['same'];
			continue;
		}
		update_field( $field['key'], $value, 'option' );
		++$report['updated'];
		$GLOBALS['kitwp_seed_changed'][] = $name;
	}
	return $report;
}

/**
 * Compare a stored value (already keyed by field names) with a seed value.
 *
 * @param mixed                $stored Stored value.
 * @param mixed                $value  Seed value.
 * @param array<string, mixed> $field  ACF field.
 * @return bool
 */
function kitwp_seed_same( $stored, $value, $field ) {
	unset( $field );
	return wp_json_encode( kitwp_seed_norm( $stored ) ) === wp_json_encode( kitwp_seed_norm( $value ) );
}

/**
 * Turn an unformatted ACF value (sub fields keyed by field key) into the seed shape (keyed by name), recursively.
 *
 * @param mixed                $stored Unformatted value.
 * @param array<string, mixed> $field  ACF field.
 * @return mixed
 */
function kitwp_seed_named( $stored, $field ) {
	if ( ! in_array( $field['type'], [ 'group', 'repeater' ], true ) ) {
		return $stored;
	}
	$convert = function ( $row ) use ( $field ) {
		$named = [];
		foreach ( (array) $field['sub_fields'] as $sub ) {
			$named[ $sub['name'] ] = kitwp_seed_named( $row[ $sub['key'] ] ?? null, $sub );
		}
		return $named;
	};
	if ( 'group' === $field['type'] ) {
		return $convert( (array) $stored );
	}
	return array_values( array_map( $convert, (array) $stored ) );
}

/**
 * Normalise a value for comparison (strings, sorted keys, booleans as 0/1).
 *
 * @param mixed $v Value.
 * @return mixed
 */
function kitwp_seed_norm( $v ) {
	if ( is_array( $v ) ) {
		$out = [];
		foreach ( $v as $k => $x ) {
			$out[ $k ] = kitwp_seed_norm( $x );
		}
		if ( array_keys( $out ) !== range( 0, count( $out ) - 1 ) ) {
			ksort( $out );
		}
		return $out;
	}
	if ( is_bool( $v ) ) {
		return $v ? '1' : '0';
	}
	return null === $v ? '' : (string) $v;
}

/**
 * Build the five menus and assign their locations. A menu is rebuilt only when its items differ.
 *
 * @return array<string, int>
 */
function kitwp_seed_menus() {
	$report    = [
		'rebuilt' => 0,
		'same'    => 0,
	];
	$locations = get_theme_mod( 'nav_menu_locations', [] );
	foreach ( kitwp_seed_json( 'menus.json' ) as $location => $menu ) {
		$wanted = kitwp_seed_menu_rows( (array) $menu['items'] );
		$obj    = wp_get_nav_menu_object( $menu['name'] );
		$id     = $obj ? (int) $obj->term_id : (int) wp_create_nav_menu( $menu['name'] );
		$current = $obj ? kitwp_seed_menu_current( $id ) : [];
		if ( $obj && $current === $wanted ) {
			++$report['same'];
		} else {
			$diff = array_values( array_diff( $wanted, $current ) );
			$GLOBALS['kitwp_seed_menu_changed'][] = $location . ( $diff ? ' (' . $diff[0] . ' / ' . ( array_values( array_diff( $current, $wanted ) )[0] ?? '' ) . ')' : '' );
			foreach ( (array) wp_get_nav_menu_items( $id ) as $old ) {
				wp_delete_post( $old->ID, true );
			}
			kitwp_seed_menu_add( $id, (array) $menu['items'], 0 );
			++$report['rebuilt'];
		}
		$locations[ $location ] = $id;
	}
	set_theme_mod( 'nav_menu_locations', $locations );
	return $report;
}

/**
 * Where a menu row points: the page with that slug when it exists, otherwise a site-relative custom link.
 *
 * @param array<string, mixed> $row Seed row.
 * @return array<string, mixed>
 */
function kitwp_seed_menu_target( $row ) {
	if ( ! empty( $row['url'] ) ) {
		return [
			'type' => 'custom',
			'url'  => $row['url'],
		];
	}
	$page = get_page_by_path( (string) $row['slug'] );
	if ( $page ) {
		return [
			'type'      => 'post_type',
			'object'    => 'page',
			'object_id' => (int) $page->ID,
		];
	}
	return [
		'type' => 'custom',
		'url'  => home_url( '/' . trim( (string) $row['slug'], '/' ) . '/' ),
	];
}

/**
 * Flat, comparable list of the wanted rows.
 *
 * @param array<int, array<string, mixed>> $items Seed items.
 * @param int                              $depth Depth.
 * @return array<int, string>
 */
function kitwp_seed_menu_rows( $items, $depth = 0 ) {
	$rows = [];
	foreach ( $items as $row ) {
		$target = kitwp_seed_menu_target( $row );
		$rows[] = implode( '|', [ $depth, $row['title'], $target['url'] ?? 'page:' . $target['object_id'], $row['classes'] ?? '', $row['icon'] ?? '' ] );
		if ( ! empty( $row['children'] ) ) {
			$rows = array_merge( $rows, kitwp_seed_menu_rows( $row['children'], $depth + 1 ) );
		}
	}
	return $rows;
}

/**
 * The same flat list for a menu as it is stored now.
 *
 * @param int $menu_id Menu ID.
 * @return array<int, string>
 */
function kitwp_seed_menu_current( $menu_id ) {
	$rows  = [];
	$depth = [];
	foreach ( (array) wp_get_nav_menu_items( $menu_id ) as $item ) {
		$d                   = $item->menu_item_parent ? ( $depth[ (int) $item->menu_item_parent ] ?? 0 ) + 1 : 0;
		$depth[ $item->ID ]  = $d;
		$url                 = 'custom' === $item->type ? $item->url : 'page:' . (int) $item->object_id;
		$icon                = function_exists( 'get_field' ) ? (string) get_field( 'field_kitk_menu_item_icon', $item->ID ) : '';
		$rows[]              = implode( '|', [ $d, html_entity_decode( $item->title, ENT_QUOTES, 'UTF-8' ), $url, implode( ' ', array_filter( (array) $item->classes ) ), $icon ] );
	}
	return $rows;
}

/**
 * Add seed items to a menu.
 *
 * @param int                              $menu_id Menu ID.
 * @param array<int, array<string, mixed>> $items   Seed items.
 * @param int                              $parent  Parent menu item ID.
 * @return void
 */
function kitwp_seed_menu_add( $menu_id, $items, $parent ) {
	foreach ( $items as $row ) {
		$target = kitwp_seed_menu_target( $row );
		$args   = [
			'menu-item-title'     => $row['title'],
			'menu-item-status'    => 'publish',
			'menu-item-parent-id' => $parent,
			'menu-item-classes'   => $row['classes'] ?? '',
			'menu-item-type'      => $target['type'],
		];
		if ( 'custom' === $target['type'] ) {
			$args['menu-item-url'] = $target['url'];
		} else {
			$args['menu-item-object']    = $target['object'];
			$args['menu-item-object-id'] = $target['object_id'];
		}
		$item_id = wp_update_nav_menu_item( $menu_id, 0, $args );
		if ( is_wp_error( $item_id ) ) {
			continue;
		}
		if ( ! empty( $row['icon'] ) && function_exists( 'update_field' ) ) {
			update_field( 'field_kitk_menu_item_icon', $row['icon'], $item_id );
		}
		if ( ! empty( $row['children'] ) ) {
			kitwp_seed_menu_add( $menu_id, $row['children'], (int) $item_id );
		}
	}
}

/**
 * Tools > Seeder.
 *
 * @return void
 */
function kitwp_seed_menu_page() {
	add_management_page( __( 'Seeder', 'kitwp' ), __( 'Seeder', 'kitwp' ), 'manage_options', 'kitwp-seeder', 'kitwp_seed_page' );
}
add_action( 'admin_menu', 'kitwp_seed_menu_page' );

/**
 * Seeder screen and runner.
 *
 * @return void
 */
function kitwp_seed_page() {
	if ( ! current_user_can( 'manage_options' ) ) {
		return;
	}
	// The order matters: pages before menus (menus link pages only once they exist), forms before pages that print them.
	$steps  = (array) apply_filters(
		'kitwp_seed_steps',
		[
			'media'          => __( 'Media (media.json)', 'kitwp' ),
			'settings'       => __( 'Theme Settings (settings.json)', 'kitwp' ),
			'forms'          => __( 'Contact Form 7 forms (forms.json)', 'kitwp' ),
			'template_pages' => __( 'Template pages (template-pages.json)', 'kitwp' ),
			'flex_pages'     => __( 'Flexible pages and posts (pages.json)', 'kitwp' ),
			'menus'          => __( 'Menus (menus.json)', 'kitwp' ),
			'seo'            => __( 'Yoast SEO settings, social images, page types (seo.json, og-images.json)', 'kitwp' ),
			'redirects'      => __( 'Old URL redirects, Redirection plugin (redirects.json)', 'kitwp' ),
		]
	);
	$result = [];
	if ( ! function_exists( 'update_field' ) ) {
		echo '<div class="notice notice-error"><p>' . esc_html__( 'ACF PRO is not active: the seeder needs it.', 'kitwp' ) . '</p></div>';
		return;
	}
	if ( isset( $_POST['kitwp_seed'] ) && check_admin_referer( 'kitwp_seed' ) ) {
		$run = sanitize_key( wp_unslash( $_POST['kitwp_seed'] ) );
		foreach ( array_keys( $steps ) as $step ) {
			if ( ( 'all' === $run || $step === $run ) && function_exists( 'kitwp_seed_' . $step ) ) {
				$result[ $step ] = call_user_func( 'kitwp_seed_' . $step );
			}
		}
	}
	echo '<div class="wrap"><h1>' . esc_html__( 'Seeder', 'kitwp' ) . '</h1>';
	echo '<p>' . esc_html__( 'Seeds content from the static site. Safe to run again: anything already seeded is left as it is.', 'kitwp' ) . '</p>';
	echo '<p><code>' . esc_html( kitwp_seed_dir() ) . '</code> ' . ( is_dir( kitwp_seed_dir() ) ? esc_html__( 'found', 'kitwp' ) : '<strong>' . esc_html__( 'not found', 'kitwp' ) . '</strong>' ) . '</p>';
	foreach ( $result as $step => $counts ) {
		$parts = [];
		foreach ( $counts as $k => $n ) {
			$parts[] = $k . ' ' . (int) $n;
		}
		if ( 'menus' === $step && ! empty( $GLOBALS['kitwp_seed_menu_changed'] ) ) {
			$parts[] = 'changed: ' . implode( ', ', (array) $GLOBALS['kitwp_seed_menu_changed'] );
		}
		if ( in_array( $step, [ 'settings', 'seo' ], true ) && ! empty( $GLOBALS['kitwp_seed_changed'] ) ) {
			$parts[] = 'changed: ' . implode( ', ', (array) $GLOBALS['kitwp_seed_changed'] );
		}
		echo '<div class="notice notice-success"><p><strong>' . esc_html( $steps[ $step ] ) . ':</strong> ' . esc_html( implode( ', ', $parts ) ) . '</p></div>';
	}
	echo '<form method="post">';
	wp_nonce_field( 'kitwp_seed' );
	foreach ( $steps as $step => $label ) {
		echo '<p><button class="button" name="kitwp_seed" value="' . esc_attr( $step ) . '">' . esc_html( $label ) . '</button></p>';
	}
	echo '<p><button class="button button-primary" name="kitwp_seed" value="all">' . esc_html__( 'Run all', 'kitwp' ) . '</button></p></form></div>';
}

/**
 * The Contact Form 7 forms from forms.json, for example:
 *   { "quote": { "title": "Quote Form", "form_file": "quote-form.txt", "body_file": "lead-email.html",
 *                "subject": "New Enquiry from [name] - [service]", "sender": "Site <no-reply@domain>",
 *                "recipient": "client@example.com", "bcc": "a@x, b@x", "reply_to": "[email]" },
 *     "chat":  { ... "form_file": "chat-form.txt", "subject": "New Chat Enquiry from [name] - [service]" } }
 * The Form tab comes from form_file and the Mail tab body from body_file (the full HTML email with mail-tags);
 * rows with blank mail-tags are left out ("Exclude lines with blank mail-tags").
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
		];
	}
	return $defs;
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
		if ( '' === $def['form'] || '' === $def['mail']['body'] ) {
			return [ 'form or email file missing for "' . $key . '" (see forms.json)' => 1 ];
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
				'form' => $def['form'],
				'mail' => $def['mail'],
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

/**
 * Yoast SEO, as the static site's head, from seo.json:
 *   { "logo_source": "/assets/logo-mark.png",            static path of the company logo and default share image
 *     "options": { "title-404-wpseo": "...", ... },       Yoast option overrides on top of the defaults below
 *     "page_meta": { "/about/": { "_yoast_wpseo_schema_page_type": "AboutPage", "_kitk_schema_name": "About X" } } }
 * plus og-images.json ({ "/path/": "/static/image.jpg" }) for each page's social image. Defaults: head clean-up on
 * (feeds, shortlinks, REST and oEmbed links, RSD, generator, emoji); campaign URL and permalink clean-up OFF
 * (campaign URLs and their tags must keep working); author, date, attachment and format archives off; categories
 * and tags noindex. Values are written only where they differ.
 *
 * @return array<string, int>
 */
function kitwp_seed_seo() {
	$report = [
		'changed' => 0,
		'same'    => 0,
	];
	if ( ! class_exists( 'WPSEO_Options' ) ) {
		return [ 'yoast seo not active' => 1 ];
	}
	$seo     = kitwp_seed_json( 'seo.json' );
	$logo    = ! empty( $seo['logo_source'] ) ? (int) kitwp_media_by_source( (string) $seo['logo_source'] ) : 0;
	$name    = (string) kitwp_opt( 'business_name', get_bloginfo( 'name' ) );
	$options = array_merge(
		[
			'remove_feed_global'            => true,
			'remove_feed_global_comments'   => true,
			'remove_feed_post_comments'     => true,
			'remove_feed_authors'           => true,
			'remove_feed_categories'        => true,
			'remove_feed_tags'              => true,
			'remove_feed_custom_taxonomies' => true,
			'remove_feed_post_types'        => true,
			'remove_feed_search'            => true,
			'remove_atom_rdf_feeds'         => true,
			'remove_shortlinks'             => true,
			'remove_rest_api_links'         => true,
			'remove_rsd_wlw_links'          => true,
			'remove_oembed_links'           => true,
			'remove_generator'              => true,
			'remove_emoji_scripts'          => true,
			'remove_powered_by_header'      => true,
			'remove_pingback_header'        => true,
			'clean_campaign_tracking_urls'  => false,
			'clean_permalinks'              => false,
			'enable_xml_sitemap'            => true,
			'disable-author'                => true,
			'disable-date'                  => true,
			'disable-attachment'            => true,
			'disable-post_format'           => true,
			'noindex-tax-category'          => true,
			'noindex-tax-post_tag'          => true,
			'noindex-tax-post_format'       => true,
			'breadcrumbs-enable'            => false,
			'company_or_person'             => 'company',
			'company_name'                  => $name,
			'website_name'                  => $name,
			'company_logo'                  => $logo ? (string) wp_get_attachment_url( $logo ) : '',
			'company_logo_id'               => $logo,
			'og_default_image'              => $logo ? (string) wp_get_attachment_url( $logo ) : '',
			'og_default_image_id'           => $logo,
			'opengraph'                     => true,
			'twitter'                       => true,
		],
		(array) ( $seo['options'] ?? [] )
	);
	foreach ( $options as $key => $value ) {
		if ( (string) WPSEO_Options::get( $key ) === (string) $value ) {
			++$report['same'];
			continue;
		}
		WPSEO_Options::set( $key, $value );
		++$report['changed'];
		$GLOBALS['kitwp_seed_changed'][] = $key;
	}
	$meta = [];
	foreach ( (array) kitwp_seed_json( 'og-images.json' ) as $path => $source ) {
		$image = (int) kitwp_media_by_source( (string) $source );
		if ( $image ) {
			$meta[ (string) $path ] = [
				'_yoast_wpseo_opengraph-image-id' => (string) $image,
				'_yoast_wpseo_opengraph-image'    => (string) wp_get_attachment_url( $image ),
			];
		}
	}
	foreach ( (array) ( $seo['page_meta'] ?? [] ) as $path => $fields ) {
		$meta[ (string) $path ] = array_merge( $meta[ (string) $path ] ?? [], (array) $fields );
	}
	foreach ( $meta as $path => $fields ) {
		$page = get_page_by_path( trim( $path, '/' ) );
		if ( ! $page ) {
			continue;
		}
		foreach ( $fields as $key => $value ) {
			if ( (string) get_post_meta( $page->ID, $key, true ) === (string) $value ) {
				++$report['same'];
				continue;
			}
			update_post_meta( $page->ID, $key, $value );
			++$report['changed'];
		}
	}
	return $report;
}

/**
 * Old URLs into the Redirection plugin (Tools > Redirection), from _setup/seed/redirects.json
 * ([{ "from": "/old/", "to": "/new/", "group": "Old site pages" }, { "from": "^/x(/.*)?$", "to": "/", "regex": true }]):
 * the old pages the static .htaccess redirected plus the old archive URLs (_plan/OLD-SITE-URLS.md). All 301, query
 * strings passed on (campaign tags reach the new page), trailing slash and case ignored. A source that already has a
 * redirect is left as it is, so edits made in Redirection are kept.
 *
 * @return array<string, int>
 */
function kitwp_seed_redirects() {
	global $wpdb;
	$report = [
		'created' => 0,
		'kept'    => 0,
	];
	if ( ! class_exists( 'Red_Item' ) || ! class_exists( 'Red_Group' ) || ! function_exists( 'red_set_options' ) ) {
		return [ 'redirection plugin not active' => 1 ];
	}
	// Redirection creates its tables in its own setup screen, not on activation.
	$kitwp_table = $wpdb->prefix . 'redirection_items';
	if ( $wpdb->get_var( $wpdb->prepare( 'SHOW TABLES LIKE %s', $kitwp_table ) ) !== $kitwp_table ) { // phpcs:ignore WordPress.DB.DirectDatabaseQuery
		return [ 'redirection not set up yet: finish its setup in Tools > Redirection (or wp redirection database install), then run this step again' => 1 ];
	}
	red_set_options(
		[
			'flag_query'    => 'pass',
			'flag_case'     => true,
			'flag_trailing' => true,
		]
	);
	$groups = [];
	foreach ( (array) Red_Group::get_all() as $group ) {
		$groups[ (string) $group['name'] ] = (int) $group['id'];
	}
	foreach ( (array) kitwp_seed_json( 'redirects.json' ) as $row ) {
		$name = (string) ( $row['group'] ?? 'Old site pages' );
		if ( empty( $groups[ $name ] ) ) {
			$created         = Red_Group::create( $name, 1 );
			$groups[ $name ] = $created ? (int) $created->get_id() : 0;
		}
		$regex = ! empty( $row['regex'] );
		$found = $wpdb->get_var( $wpdb->prepare( "SELECT id FROM {$wpdb->prefix}redirection_items WHERE url = %s OR url = %s LIMIT 1", (string) $row['from'], untrailingslashit( (string) $row['from'] ) ) ); // phpcs:ignore WordPress.DB.DirectDatabaseQuery -- seeder lookup in the plugin's table.
		if ( $found ) {
			++$report['kept'];
			continue;
		}
		$item = Red_Item::create(
			[
				'url'         => (string) $row['from'],
				'regex'       => $regex,
				'match_type'  => 'url',
				'action_type' => 'url',
				'action_code' => 301,
				'action_data' => [ 'url' => (string) $row['to'] ],
				'group_id'    => $groups[ $name ],
				'title'       => '',
			]
		);
		if ( ! is_wp_error( $item ) ) {
			++$report['created'];
		}
	}
	return $report;
}
