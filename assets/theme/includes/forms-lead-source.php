<?php
/**
 * Lead forms: the "Lead source" table in the lead email ([_kitk_source]), in the layout and words of an existing
 * company build: First visit, Latest campaign visit (only when it differs), Form sent from, each visit's source in
 * words. It reads the clean attribution from includes/forms-attribution.php.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

/**
 * The two visits of a clean attribution: [ 'first' => visit, 'last' => visit ], each with the keys the table reads
 * (utm_*, the click ids, referrer, landing, time); an empty array when that visit is not known.
 *
 * @param array<string, string> $a Clean attribution (kitwp_attribution_clean()).
 * @return array<string, array<string, string>>
 */
function kitwp_attribution_visits( $a ) {
	$visits = [
		'first' => [],
		'last'  => [],
	];
	foreach ( kitwp_attribution_touch() as $name ) {
		$short = str_replace( 'utm_', '', $name );
		if ( isset( $a[ $name ] ) ) {
			$visits['last'][ $name ] = $a[ $name ];
		}
		if ( isset( $a[ 'first_' . $short ] ) ) {
			$visits['first'][ $name ] = $a[ 'first_' . $short ];
		}
	}
	$map = [
		'referrer' => 'referrer',
		'landing'  => 'landing_page',
		'time'     => 'seen',
	];
	foreach ( $map as $key => $name ) {
		if ( isset( $a[ 'time' === $key ? 'last_seen' : $name ] ) ) {
			$visits['last'][ $key ] = $a[ 'time' === $key ? 'last_seen' : $name ];
		}
		if ( isset( $a[ 'first_' . $name ] ) ) {
			$visits['first'][ $key ] = $a[ 'first_' . $name ];
		}
	}
	return $visits;
}

/**
 * Where one visit came from, in words: the campaign's source / medium; else the ad click; else the search engine
 * or the site that linked; else "Direct (typed in, bookmark or no source)".
 *
 * @param array<string, string> $visit A visit (kitwp_attribution_visits()).
 * @return string
 */
function kitwp_attribution_source( $visit ) {
	if ( ! empty( $visit['utm_source'] ) ) {
		return $visit['utm_source'] . ( ! empty( $visit['utm_medium'] ) ? ' / ' . $visit['utm_medium'] : '' );
	}
	$map = [
		'gclid'   => 'Google Ads click',
		'gbraid'  => 'Google Ads click',
		'wbraid'  => 'Google Ads click',
		'fbclid'  => 'Facebook / Instagram click',
		'msclkid' => 'Microsoft Ads click',
	];
	foreach ( $map as $name => $label ) {
		if ( ! empty( $visit[ $name ] ) ) {
			return $label;
		}
	}
	if ( ! empty( $visit['referrer'] ) ) {
		$host = strtolower( (string) wp_parse_url( $visit['referrer'], PHP_URL_HOST ) );
		$map  = [
			'google.'     => 'Google search',
			'bing.'       => 'Bing search',
			'yahoo.'      => 'Yahoo search',
			'duckduckgo.' => 'DuckDuckGo search',
		];
		foreach ( $map as $needle => $label ) {
			if ( str_contains( $host, $needle ) ) {
				return $label;
			}
		}
		return ( '' !== $host ? (string) preg_replace( '/^www\./', '', $host ) : 'Another website' ) . ' (link)';
	}
	return 'Direct (typed in, bookmark or no source)';
}

/**
 * The "Lead source" rows: First visit, Latest campaign visit (only when it differs from the first), Form sent from.
 * Without the page script's data: "Not recorded".
 *
 * @param array<string, string> $a    Clean attribution.
 * @param string                $page The page the form was sent from.
 * @return array<int, array{0: string, 1: string[]}> Label => lines (the first line of a visit is its source).
 */
function kitwp_attribution_rows( $a, $page ) {
	$visits = kitwp_attribution_visits( $a );
	$rows   = [];
	$visit  = static function ( $label, $v ) {
		$lines = [ kitwp_attribution_source( $v ) ];
		$map   = [
			'utm_campaign' => 'Campaign',
			'utm_term'     => 'Keyword',
			'utm_content'  => 'Ad',
			'gclid'        => 'gclid',
			'gbraid'       => 'gbraid',
			'wbraid'       => 'wbraid',
			'fbclid'       => 'fbclid',
			'msclkid'      => 'msclkid',
			'referrer'     => 'From',
			'landing'      => 'Landing page',
		];
		foreach ( $map as $key => $name ) {
			if ( ! empty( $v[ $key ] ) ) {
				$lines[] = $name . ': ' . $v[ $key ];
			}
		}
		if ( ! empty( $v['time'] ) ) {
			$lines[] = 'When: ' . $v['time'] . ( strlen( $v['time'] ) > 10 ? ' UTC' : '' );
		}
		return [ $label, $lines ];
	};
	if ( $visits['first'] ) {
		$rows[] = $visit( 'First visit', $visits['first'] );
	}
	$same = static fn( $v ) => array_diff_key( $v, [ 'time' => 1 ] );
	if ( $visits['last'] && $same( $visits['last'] ) !== $same( $visits['first'] ) ) {
		$rows[] = $visit( 'Latest campaign visit', $visits['last'] );
	}
	if ( ! $rows ) {
		$rows[] = [ '', [ "Not recorded (the visitor's browser did not run the page script)." ] ];
	}
	if ( '' !== trim( (string) $page ) ) {
		$rows[] = [ 'Form sent from', [ (string) $page ] ];
	}
	return $rows;
}

/**
 * The "Lead source" table for the lead email ([_kitk_source]): a title row in the email's brand colour (its text
 * black or white, whichever reads better), label cells grey, as the email's details table. Plain text: the same rows as lines.
 *
 * @param array<string, string> $a    Clean attribution.
 * @param string                $page The page the form was sent from.
 * @param bool                  $html HTML email.
 * @return string
 */
function kitwp_attribution_table( $a, $page, $html = true ) {
	$rows = kitwp_attribution_rows( $a, $page );
	if ( ! $html ) {
		$text = [ 'Lead source' ];
		foreach ( $rows as $row ) {
			$text[] = ( '' !== $row[0] ? $row[0] . ': ' : '' ) . implode( "\n  ", $row[1] );
		}
		return implode( "\n", $text );
	}
	$e    = static fn( $t ) => htmlspecialchars( (string) $t, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8' );
	$cell = 'border:1px solid #dddddd;text-align:left;padding:8px 10px;vertical-align:top;';
	$out  = '';
	foreach ( $rows as $row ) {
		$lines = array_map( $e, $row[1] );
		if ( 'First visit' === $row[0] || 'Latest campaign visit' === $row[0] ) {
			$lines[0] = '<b>' . $lines[0] . '</b>';
		}
		$out .= '' === $row[0]
			? '<tr><td style="' . $cell . '" colspan="2">' . $lines[0] . '</td></tr>'
			: '<tr><td style="' . $cell . 'width:38%;background-color:#fafafa;font-weight:bold;">' . $e( $row[0] ) . '</td><td style="' . $cell . '">' . implode( '<br>', $lines ) . '</td></tr>';
	}
	[ $bg, $ink ] = kitwp_attribution_title_colours( (string) KITWP_BRAND_COLOUR );
	return '<table role="presentation" width="100%" style="font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:1.4;color:#333333;border-collapse:collapse;width:100%;margin-top:16px;"><tbody>'
		. '<tr><td style="' . $cell . 'background-color:' . $bg . ';border-color:' . $bg . ';color:' . $ink . ';" colspan="2"><b>Lead source</b></td></tr>'
		. $out . '</tbody></table>';
}

/**
 * The title row's colours: the email's brand colour, and #1a1a1a or #ffffff on it, whichever has the higher
 * contrast (WCAG relative luminance; a yellow brand gets dark text, a dark one white). Not a #rgb or #rrggbb colour:
 * #28292D with white.
 *
 * @param string $brand The brand colour.
 * @return string[] [ background, text ]
 */
function kitwp_attribution_title_colours( $brand ) {
	$hex = ltrim( trim( $brand ), '#' );
	if ( 3 === strlen( $hex ) ) {
		$hex = $hex[0] . $hex[0] . $hex[1] . $hex[1] . $hex[2] . $hex[2];
	}
	if ( ! preg_match( '/^[0-9a-f]{6}$/i', $hex ) ) {
		return [ '#28292D', '#ffffff' ];
	}
	$lum = 0.0;
	foreach ( [ 0.2126, 0.7152, 0.0722 ] as $i => $weight ) {
		$c    = hexdec( substr( $hex, $i * 2, 2 ) ) / 255;
		$lum += $weight * ( $c <= 0.03928 ? $c / 12.92 : ( ( $c + 0.055 ) / 1.055 ) ** 2.4 );
	}
	$dark  = ( $lum + 0.05 ) / ( 0.0103 + 0.05 ); // #1a1a1a's luminance is 0.0103
	$light = 1.05 / ( $lum + 0.05 );
	return [ '#' . strtolower( $hex ), $dark >= $light ? '#1a1a1a' : '#ffffff' ];
}
