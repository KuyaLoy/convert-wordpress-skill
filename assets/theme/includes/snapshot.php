<?php
/**
 * Parity snapshots, local copies only: any front-end URL with ?kitwp_snapshot=1 also saves its HTML to
 * _setup/snapshots/<path>.html ("home" for /, "/" in the path becomes "__"), where the DOM diff
 * (tools/parity/domdiff.py) and the cloud mirror (tools/parity/mkmirror.py) read it. Never deployed: _setup is
 * excluded from the Duplicator package.
 *
 * @package kitwp
 */

if ( 'local' !== wp_get_environment_type() ) {
	return;
}

/**
 * Start capturing the page when the snapshot flag is set.
 *
 * @return void
 */
function kitwp_snapshot_start() {
	if ( empty( $_GET['kitwp_snapshot'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended -- read-only, local copies only.
		return;
	}
	ob_start( 'kitwp_snapshot_write' );
}
add_action( 'template_redirect', 'kitwp_snapshot_start', 0 );

/**
 * Write the page HTML to the snapshot folder and pass it through unchanged.
 *
 * @param string $html Page HTML.
 * @return string
 */
function kitwp_snapshot_write( $html ) {
	$dir  = ABSPATH . '_setup/snapshots';
	$path = trim( (string) wp_parse_url( isset( $_SERVER['REQUEST_URI'] ) ? sanitize_text_field( wp_unslash( $_SERVER['REQUEST_URI'] ) ) : '/', PHP_URL_PATH ), '/' );
	$file = '' === $path ? 'home' : str_replace( '/', '__', $path );
	wp_mkdir_p( $dir );
	file_put_contents( $dir . '/' . sanitize_file_name( $file ) . '.html', $html ); // phpcs:ignore WordPress.WP.AlternativeFunctions.file_system_operations_file_put_contents -- local parity tool.
	return $html;
}
