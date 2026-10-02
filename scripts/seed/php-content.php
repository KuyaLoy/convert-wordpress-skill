<?php
/**
 * Dumps a PHP source's content variables (the site-wide arrays and strings its partials print) as an ES module,
 * so export.mjs can read them like a JavaScript site's content modules.
 *
 *   php php-content.php <source copy> <file.php> [<file.php> ...] > content.mjs
 *   php php-content.php source config/config.php data/global-content.php > content.mjs
 *
 * Run it on a copy of the source whose env loader is a stub with blank values (references/source-types.md):
 * the real .env never leaves the developer's machine. Every variable the files define is written; objects and
 * resources are left out, and so is any variable whose name looks like a secret (key, token, password, SMTP...)
 * or a lead recipient (bcc, cc, admin email): recipients come from the intake into site.json, never from code. Then: node export.mjs content.mjs <golden master> <public dir> <seed dir>.
 *
 * @package kitwp
 */

if ( $argc < 3 ) {
	fwrite( STDERR, "usage: php php-content.php <source copy> <file.php> [...] > content.mjs\n" );
	exit( 2 );
}
$kitwp_root = rtrim( $argv[1], '/' );
if ( ! is_dir( $kitwp_root ) ) {
	fwrite( STDERR, "not a folder: {$kitwp_root}\n" );
	exit( 2 );
}
$_SERVER += [ 'HTTP_HOST' => 'localhost', 'REQUEST_URI' => '/', 'SERVER_NAME' => 'localhost', 'HTTPS' => '' ];
chdir( $kitwp_root );
$kitwp_before = array_keys( get_defined_vars() );
ob_start();
foreach ( array_slice( $argv, 2 ) as $kitwp_file ) {
	require_once $kitwp_root . '/' . ltrim( $kitwp_file, '/' );
}
ob_end_clean();
$kitwp_out = [];
foreach ( get_defined_vars() as $kitwp_name => $kitwp_value ) {
	// Our own variables, and anything that could hold a secret or a lead recipient, are never written.
	if ( in_array( $kitwp_name, $kitwp_before, true ) || 0 === strpos( $kitwp_name, 'kitwp_' )
		|| preg_match( '/secret|pass|token|key|smtp|recaptcha|salt|auth|bcc|cc_|recipient|admin_email|debug/i', $kitwp_name ) ) {
		continue;
	}
	if ( is_scalar( $kitwp_value ) || is_array( $kitwp_value ) || null === $kitwp_value ) {
		$kitwp_out[ $kitwp_name ] = $kitwp_value;
	}
}
echo '// Written by php-content.php from ' . implode( ', ', array_slice( $argv, 2 ) ) . "\n";
echo 'export default ' . json_encode( $kitwp_out, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE ) . ";\n";
