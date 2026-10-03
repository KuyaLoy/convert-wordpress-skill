<?php
/**
 * Router for PHP's built-in web server (serve-wp.py): existing files are served as they are, every other address
 * goes to WordPress, so pretty permalinks work at the root of http://localhost:<port>. The private project files
 * answer 403, as the .htaccess block does on Apache.
 *
 * @package convert-to-wordpress
 */

$kitwp_uri  = rawurldecode( (string) parse_url( $_SERVER['REQUEST_URI'], PHP_URL_PATH ) );
$kitwp_root = rtrim( $_SERVER['DOCUMENT_ROOT'], '/\\' );

if ( preg_match( '#^/(_plan|_setup)(/|$)|(^|/)(BUILD-MAP|handoff|ai-handoff-summary|PLAN)\.md$|(^|/)debug\.log$|^/wp-config\.php$#i', $kitwp_uri ) ) {
	http_response_code( 403 );
	echo 'Forbidden';
	return true;
}

$kitwp_path = $kitwp_root . $kitwp_uri;
if ( '/' !== $kitwp_uri && is_file( $kitwp_path ) ) {
	return false; // The server sends the file, and runs it when it is a .php file.
}
if ( '/' !== $kitwp_uri && is_dir( $kitwp_path ) && is_file( rtrim( $kitwp_path, '/' ) . '/index.php' ) ) {
	$kitwp_index = rtrim( $kitwp_path, '/' ) . '/index.php'; // For example /wp-admin/.
} else {
	$kitwp_index = $kitwp_root . '/index.php';
}
$_SERVER['SCRIPT_FILENAME'] = $kitwp_index;
$_SERVER['SCRIPT_NAME']     = substr( $kitwp_index, strlen( $kitwp_root ) );
$_SERVER['PHP_SELF']        = $_SERVER['SCRIPT_NAME'];
chdir( dirname( $kitwp_index ) );
require $kitwp_index;
