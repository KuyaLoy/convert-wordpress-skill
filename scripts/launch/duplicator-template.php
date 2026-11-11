<?php
/**
 * Creates or updates the Duplicator Pro template "launch" for package.py.
 *
 * Run by package.py:  wp eval-file duplicator-template.php <root> <paths file>
 * <root> is the WordPress root as package.py wrote the paths. <paths file> has one full path per line.
 * The installer password comes from the environment variable DUP_LAUNCH_INSTALLER_PASS.
 * Prints one line: template=<id> dirs=<count> files=<count>. It never prints the password.
 *
 * @package convert-to-wordpress
 */

if ( ! defined( 'WP_CLI' ) || ! WP_CLI ) {
	return;
}

foreach ( array( 'Duplicator\Models\TemplateEntity', 'Duplicator\Models\GlobalEntity', 'Duplicator\Package\Archive\PackageArchive' ) as $dup_class ) {
	if ( ! class_exists( $dup_class ) ) {
		WP_CLI::error( 'Duplicator Pro is not active (missing ' . $dup_class . ').', 2 );
	}
}

$dup_pass = (string) getenv( 'DUP_LAUNCH_INSTALLER_PASS' );
if ( strlen( $dup_pass ) < 12 ) {
	WP_CLI::error( 'No installer password in DUP_LAUNCH_INSTALLER_PASS.' );
}
if ( count( $args ) < 2 || ! is_readable( $args[1] ) ) {
	WP_CLI::error( 'Usage: wp eval-file duplicator-template.php <root> <paths file>' );
}

// The paths use the root as package.py saw it; Duplicator scans from ABSPATH, so rebase them onto it.
$dup_from  = rtrim( str_replace( '\\', '/', $args[0] ), '/' );
$dup_to    = rtrim( str_replace( '\\', '/', ABSPATH ), '/' );
$dup_paths = array();
foreach ( (array) file( $args[1], FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES ) as $dup_line ) {
	$dup_path = rtrim( str_replace( '\\', '/', trim( $dup_line ) ), ';/' );
	if ( '' === $dup_path ) {
		continue;
	}
	if ( 0 === strncasecmp( $dup_path, $dup_from . '/', strlen( $dup_from ) + 1 ) ) {
		$dup_path = $dup_to . substr( $dup_path, strlen( $dup_from ) );
	}
	$dup_paths[] = $dup_path;
}
$dup_joined = implode( ';', $dup_paths );

$dup_template = null;
$dup_all      = \Duplicator\Models\TemplateEntity::getAll();
foreach ( is_array( $dup_all ) ? $dup_all : array() as $dup_item ) {
	if ( ! $dup_item->is_manual && 'launch' === $dup_item->name ) {
		$dup_template = $dup_item;
		break;
	}
}
if ( null === $dup_template ) {
	$dup_default = \Duplicator\Models\TemplateEntity::getDefaultTemplate();
	if ( null === $dup_default ) {
		WP_CLI::error( 'Duplicator Pro has no default template to copy.', 3 );
	}
	$dup_template = new \Duplicator\Models\TemplateEntity();
	$dup_template->copyFromSourceId( $dup_default->getId() );
	$dup_template->name = 'launch';
}

$dup_template->archive_filter_on        = true;
$dup_template->archive_filter_dirs      = \Duplicator\Package\Archive\PackageArchive::parseDirectoryFilter( $dup_joined );
$dup_template->archive_filter_files     = \Duplicator\Package\Archive\PackageArchive::parseFileFilter( $dup_joined );
$dup_template->installer_opts_secure_on = 1;
$dup_template->installerPassowrd        = $dup_pass; // Duplicator's own spelling.
if ( ! $dup_template->save() ) {
	WP_CLI::error( 'Could not save the template "launch".', 3 );
}

$dup_global                      = \Duplicator\Models\GlobalEntity::getInstance();
$dup_global->installer_name_mode = \Duplicator\Models\GlobalEntity::INSTALLER_NAME_MODE_WITH_HASH;
if ( ! $dup_global->save() ) {
	WP_CLI::error( 'Could not save the Duplicator setting for the installer name.', 3 );
}

$dup_count = static function ( $list ) {
	return '' === (string) $list ? 0 : count( explode( ';', (string) $list ) );
};
WP_CLI::line(
	'template=' . (int) $dup_template->getId()
	. ' dirs=' . $dup_count( $dup_template->archive_filter_dirs )
	. ' files=' . $dup_count( $dup_template->archive_filter_files )
);
