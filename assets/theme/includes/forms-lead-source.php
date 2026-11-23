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
	foreach ( [ 'referrer' => 'referrer', 'landing' => 'landing_page', 'time' => 'seen' ] as $key => $name ) {
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
	foreach ( [ 'gclid' => 'Google Ads click', 'gbraid' => 'Google Ads click', 'wbraid' => 'Google Ads click', 'fbclid' => 'Facebook / Instagram click', 'msclkid' => 'Microsoft Ads click' ] as $name => $label ) {
		if ( ! empty( $visit[ $name ] ) ) {
			return $label;
		}
	}
	if ( ! empty( $visit['referrer'] ) ) {
		$host = strtolower( (string) wp_parse_url( $visit['referrer'], PHP_URL_HOST ) );
		foreach ( [ 'google.' => 'Google search', 'bing.' => 'Bing search', 'yahoo.' => 'Yahoo search', 'duckduckgo.' => 'DuckDuckGo search' ] as $needle => $label ) {
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
		foreach ( [ 'utm_campaign' => 'Campaign', 'utm_term' => 'Keyword', 'utm_content' => 'Ad', 'gclid' => 'gclid', 'gbraid' => 'gbraid', 'wbraid' => 'wbraid', 'fbclid' => 'fbclid', 'msclkid' => 'msclkid', 'referrer' => 'From', 'landing' => 'Landing page' ] as $key => $name ) {
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
 * The "Lead source" table for the lead email ([_kitk_source]): a title row in the email's brand colour, label cells
 * grey, as the email's details table. Plain text: the same rows as lines.
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
	$dark = $e( KITWP_BRAND_COLOUR );
	return '<table role="presentation" width="100%" style="font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:1.4;color:#333333;border-collapse:collapse;width:100%;margin-top:16px;"><tbody>'
		. '<tr><td style="' . $cell . 'background-color:' . $dark . ';border-color:' . $dark . ';color:#ffffff;" colspan="2"><b>Lead source</b></td></tr>'
		. $out . '</tbody></table>';
}
