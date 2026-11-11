<?php
/**
 * A simple, safe wp-admin for the client. The client logs in with the Editor role (never an administrator). For
 * every user without manage_options:
 *
 * - The admin menu shows only Dashboard, Pages, Media, Theme Settings, Contact (CF7, without "Add Contact Form"),
 *   the CFDB7 enquiries when that plugin is active, and Profile. Posts and Comments show only when
 *   KITWP_CLIENT_HIDE_POSTS is false. The "kitwp_client_menu" filter changes the list.
 * - Menus only: no capability is removed, so a hidden screen still opens from its address. One is added at run time
 *   (nothing is saved): cfdb7_access for users who can edit pages, because CFDB7 gives it to administrators only.
 * - Update nags and plugin notices are hidden (ACF's own messages, such as "Theme Settings saved.", stay).
 * - The dashboard has one widget, "Your website", with plain-English links; the help line is KITWP_CLIENT_HELP.
 * - ACF's own menu (Field Groups, Tools) is hidden. Administrators keep it, as the kit's rule says.
 *
 * Administrators see the normal wp-admin.
 *
 * @package kitwp
 */

/**
 * Whether the current user is the client (logged in, without manage_options).
 *
 * @return bool
 */
function kitwp_client_is_client() {
	return is_user_logged_in() && ! current_user_can( 'manage_options' );
}

/**
 * Whether Contact Form CFDB7 (the enquiries list) is active.
 *
 * @return bool
 */
function kitwp_client_has_enquiries() {
	return function_exists( 'cfdb7_create_table' );
}

/**
 * Let users who can edit pages (the Editor role) open the CFDB7 enquiries. CFDB7 gives cfdb7_access to
 * administrators only. This adds it at run time and saves nothing in the database.
 *
 * @param array<string, bool> $allcaps The user's capabilities.
 * @return array<string, bool>
 */
function kitwp_client_enquiries_cap( $allcaps ) {
	if ( ! empty( $allcaps['edit_pages'] ) && empty( $allcaps['manage_options'] ) ) {
		$allcaps['cfdb7_access'] = true;
	}
	return $allcaps;
}
add_filter( 'user_has_cap', 'kitwp_client_enquiries_cap' );

/**
 * Keep only the client's menu items. Menus only: the capabilities stay.
 *
 * @return void
 */
function kitwp_client_menu() {
	if ( ! kitwp_client_is_client() ) {
		return;
	}
	$keep = [ 'index.php', 'edit.php?post_type=page', 'upload.php', 'kitk-theme-settings', 'wpcf7', 'wpcf7-dashboard', 'profile.php' ];
	if ( kitwp_client_has_enquiries() ) {
		$keep[] = 'cfdb7-list.php';
	}
	if ( ! KITWP_CLIENT_HIDE_POSTS ) {
		$keep[] = 'edit.php';
		$keep[] = 'edit-comments.php';
	}
	$keep = (array) apply_filters( 'kitwp_client_menu', $keep );

	foreach ( (array) ( $GLOBALS['menu'] ?? [] ) as $item ) {
		$slug = (string) ( $item[2] ?? '' );
		if ( '' !== $slug && ! in_array( $slug, $keep, true ) ) {
			remove_menu_page( $slug );
		}
	}

	// Contact Form 7: the client reads the forms and edits their messages, but adds none (its parent slug changed in 6.x).
	foreach ( [ 'wpcf7', 'wpcf7-dashboard' ] as $parent ) {
		remove_submenu_page( $parent, 'wpcf7-new' );
		remove_submenu_page( $parent, 'wpcf7-integration' );
	}
}
add_action( 'admin_menu', 'kitwp_client_menu', 9999 );

/**
 * Hide ACF's own menu (Field Groups, Post Types, Options Pages, Tools) from the client. Editing content and Theme
 * Settings keep working. Administrators keep the menu.
 *
 * @param bool $show Whether ACF shows its admin menu.
 * @return bool
 */
function kitwp_client_acf_admin( $show ) {
	return $show && current_user_can( 'manage_options' );
}
add_filter( 'acf/settings/show_admin', 'kitwp_client_acf_admin' );

/**
 * Hide update nags and plugin notices from the client, just before WordPress prints them. ACF's own notices (the
 * "saved" message of Theme Settings) and the pending email change notice stay. The "kitwp_client_notices" filter
 * adds more callbacks to keep (function names).
 *
 * @return void
 */
function kitwp_client_notices() {
	if ( ! kitwp_client_is_client() ) {
		return;
	}
	$keep = (array) apply_filters( 'kitwp_client_notices', [ 'acf_render_admin_notices', 'new_user_email_admin_notice' ] );
	foreach ( [ 'admin_notices', 'all_admin_notices', 'user_admin_notices', 'network_admin_notices' ] as $hook ) {
		if ( empty( $GLOBALS['wp_filter'][ $hook ] ) ) {
			continue;
		}
		foreach ( $GLOBALS['wp_filter'][ $hook ]->callbacks as $priority => $callbacks ) {
			foreach ( $callbacks as $callback ) {
				if ( is_string( $callback['function'] ) && in_array( $callback['function'], $keep, true ) ) {
					continue;
				}
				remove_action( $hook, $callback['function'], $priority );
			}
		}
	}
}
add_action( 'in_admin_header', 'kitwp_client_notices', 9999 );

/**
 * The client's toolbar: no WordPress logo menu (links to wordpress.org), and no Comments or New Post when posts are
 * hidden.
 *
 * @param WP_Admin_Bar $bar The toolbar.
 * @return void
 */
function kitwp_client_toolbar( $bar ) {
	if ( ! kitwp_client_is_client() ) {
		return;
	}
	$bar->remove_node( 'wp-logo' );
	if ( KITWP_CLIENT_HIDE_POSTS ) {
		$bar->remove_node( 'comments' );
		$bar->remove_node( 'new-post' );
	}
}
add_action( 'admin_bar_menu', 'kitwp_client_toolbar', 999 );

/**
 * A clean dashboard for the client: every widget (WordPress's and plugins') is removed and "Your website" is added.
 *
 * @return void
 */
function kitwp_client_dashboard() {
	if ( ! kitwp_client_is_client() ) {
		return;
	}
	remove_action( 'welcome_panel', 'wp_welcome_panel' );
	foreach ( (array) ( $GLOBALS['wp_meta_boxes']['dashboard'] ?? [] ) as $context => $priorities ) {
		foreach ( (array) $priorities as $boxes ) {
			foreach ( array_keys( (array) $boxes ) as $id ) {
				remove_meta_box( (string) $id, 'dashboard', (string) $context );
			}
		}
	}
	wp_add_dashboard_widget( 'kitwp_client_widget', __( 'Your website', 'kitwp' ), 'kitwp_client_widget' );
}
add_action( 'wp_dashboard_setup', 'kitwp_client_dashboard', 9999 );

/**
 * The "Your website" widget: plain-English links to what the client changes most.
 *
 * @return void
 */
function kitwp_client_widget() {
	$links = [
		[ admin_url( 'edit.php?post_type=page' ), __( 'Edit a page', 'kitwp' ), __( 'Change the words and pictures on any page.', 'kitwp' ) ],
	];
	if ( function_exists( 'get_field' ) ) {
		$links[] = [ admin_url( 'admin.php?page=kitk-theme-settings' ), __( 'Change the phone, email or address', 'kitwp' ), __( 'Theme Settings: details that show on every page.', 'kitwp' ) ];
	}
	if ( kitwp_client_has_enquiries() && current_user_can( 'cfdb7_access' ) ) {
		$links[] = [ admin_url( 'admin.php?page=cfdb7-list.php' ), __( 'See enquiries', 'kitwp' ), __( 'Messages people sent through the forms on the website.', 'kitwp' ) ];
	}

	echo '<ul>';
	foreach ( $links as $link ) {
		printf(
			'<li><a href="%1$s"><strong>%2$s</strong></a><br>%3$s</li>',
			esc_url( $link[0] ),
			esc_html( $link[1] ),
			esc_html( $link[2] )
		);
	}
	echo '</ul>';

	$help = trim( (string) KITWP_CLIENT_HELP );
	if ( '' === $help || str_contains( $help, '{{' ) ) {
		return;
	}
	if ( is_email( $help ) ) {
		$help_html = '<a href="' . esc_url( 'mailto:' . $help ) . '">' . esc_html( $help ) . '</a>';
	} elseif ( str_starts_with( $help, 'https://' ) || str_starts_with( $help, 'http://' ) ) {
		$help_html = '<a href="' . esc_url( $help ) . '">' . esc_html( $help ) . '</a>';
	} else {
		$help_html = esc_html( $help );
	}
	echo '<p><strong>' . esc_html__( 'Need help?', 'kitwp' ) . '</strong> ' . $help_html . '</p>'; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- escaped above.
}
