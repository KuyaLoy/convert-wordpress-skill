<?php
/**
 * Lead forms on a local copy (WP_ENVIRONMENT_TYPE "local"): every email goes to the site admin and to a file in
 * _setup/mail/, never to the real recipients.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

/**
 * Local only (WP_ENVIRONMENT_TYPE "local"): every email goes to the site admin email only, never to the client or
 * the Bcc list, so a local mail catcher shows it (Laragon's Mail Catcher, Mailpit in Local or DDEV) and nothing
 * reaches the real recipients even if a mail sender is ever set up. The real To and Bcc are kept in an
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
	file_put_contents( $dir . '/' . gmdate( 'Ymd-His' ) . '-' . substr( md5( (string) wp_rand() ), 0, 6 ) . '.html', '<!--' . "\n" . str_replace( '--', '- -', $meta ) . "\n-->\n" . $atts['message'] ); // phpcs:ignore WordPress.WP.AlternativeFunctions.file_system_operations_file_put_contents -- a local copy of the email; WP_Filesystem may ask for credentials.

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
 * Whether PHP's mail() can hand an email to anything on this machine: the program in sendmail_path (Laragon's Mail
 * Catcher, Mailpit) or, on Windows without one, an SMTP server at the php.ini address. XAMPP, MAMP, WampServer and
 * serve-wp.py usually have neither.
 *
 * @return bool
 */
function kitwp_local_mailer_ready() {
	$path = trim( (string) ini_get( 'sendmail_path' ) );
	if ( '' !== $path ) {
		$bin = '"' === $path[0] ? substr( $path, 1, max( 0, (int) strpos( $path, '"', 1 ) - 1 ) ) : (string) strtok( $path, ' ' );
		return is_file( $bin );
	}
	if ( 'WIN' !== strtoupper( substr( PHP_OS, 0, 3 ) ) ) {
		return false;
	}
	$smtp = @fsockopen( (string) ini_get( 'SMTP' ), (int) ini_get( 'smtp_port' ), $errno, $errstr, 1 ); // phpcs:ignore WordPress.PHP.NoSilencedErrors.Discouraged -- a refused connection is the answer here.
	if ( ! $smtp ) {
		return false;
	}
	fclose( $smtp ); // phpcs:ignore WordPress.WP.AlternativeFunctions.file_system_operations_fclose -- a socket, not a file.
	return true;
}

/**
 * Local only: when PHP cannot send mail on this machine, wp_mail() stops after the copy in _setup/mail/ and reports
 * success, so forms answer as they will on live (success message, thank-you redirect) instead of a send error. The
 * kitwp_mail_to_file filter forces it either way (true: file only; false: always try to send).
 *
 * @param null|bool            $result Short-circuit value from an earlier filter.
 * @param array<string, mixed> $atts   wp_mail() arguments.
 * @return null|bool
 */
function kitwp_local_mail_to_file( $result, $atts ) {
	if ( null !== $result || 'local' !== wp_get_environment_type() ) {
		return $result;
	}
	return apply_filters( 'kitwp_mail_to_file', ! kitwp_local_mailer_ready(), $atts ) ? true : null;
}
add_filter( 'pre_wp_mail', 'kitwp_local_mail_to_file', 10, 2 );
