<?php
/**
 * Lead forms: the "Lead Attribution" table in the lead email ([_kitk_source]): the company attribution standard's
 * eleven rows in its order (Lead Source ... First Touch Referrer, "none" when empty), then the extra tags and click
 * ids that are present. It reads the values includes/forms-attribution.php worked out.
 *
 * @package kitwp
 */

defined( 'ABSPATH' ) || exit;

/**
 * The company attribution standard: the eleven fields every lead carries, as posted names and their labels, in
 * this order (the lead email's Lead Attribution table, the CFDB7 columns, the leads portal and a CRM mapping). The
 * server works them out from the checked browser values (kitwp_attribution_values()); an empty one is "none".
 *
 * @return array<string, string> Posted name => label.
 */
function kitwp_attribution_standard() {
	return [
		'lead_source'              => 'Lead Source',
		'google_ads_campaign_id'   => 'Google Ads Campaign ID',
		'google_click_id'          => 'Google Click ID',
		'landing_page'             => 'Landing Page',
		'referrer'                 => 'Referrer',
		'lead_source_date'         => 'Lead Source Date',
		'form_submitted_from'      => 'Form Submitted From',
		'first_touch_source'       => 'First Touch Source',
		'first_visit_date'         => 'First Visit Date',
		'first_touch_landing_page' => 'First Touch Landing Page',
		'first_touch_referrer'     => 'First Touch Referrer',
	];
}

/**
 * The other captured values, shown after the eleven only when present: the latest visit's under their own names,
 * the first visit's (first_*) only when they differ from the latest visit's.
 *
 * @return array<string, string> Campaign tag or click id => label.
 */
function kitwp_attribution_extras() {
	return [
		'utm_source'     => 'UTM Source',
		'utm_medium'     => 'UTM Medium',
		'utm_campaign'   => 'UTM Campaign',
		'utm_term'       => 'UTM Term',
		'utm_content'    => 'UTM Content',
		'utm_id'         => 'UTM ID',
		'gad_campaignid' => 'Google Ads Campaign ID',
		'gclid'          => 'Google Click ID',
		'gbraid'         => 'Google gbraid',
		'wbraid'         => 'Google wbraid',
		'fbclid'         => 'Facebook Click ID',
		'msclkid'        => 'Microsoft Click ID',
	];
}

/**
 * A visit's UTC time ("YYYY-MM-DD HH:MM") as a date in the site's time zone (Settings > General), "YYYY-MM-DD"; a
 * date alone stays as it is.
 *
 * @param string $stamp UTC time.
 * @return string '' when unknown.
 */
function kitwp_attribution_date( $stamp ) {
	$stamp = (string) $stamp;
	if ( preg_match( '/^\d{4}-\d{2}-\d{2}$/', $stamp ) ) {
		return $stamp;
	}
	$dt = preg_match( '/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/', $stamp ) ? DateTime::createFromFormat( 'Y-m-d H:i', $stamp, new DateTimeZone( 'UTC' ) ) : false;
	return $dt ? (string) wp_date( 'Y-m-d', $dt->getTimestamp(), wp_timezone() ) : '';
}

/**
 * The eleven standard values (kitwp_attribution_standard()) of a checked attribution. The latest touch is the
 * latest campaign visit, else the first visit (a visitor who only ever came direct). Google Ads Campaign ID:
 * gad_campaignid, else utm_id, else a numeric utm_campaign. An empty value is "none"; no page-script data at all:
 * Lead Source "Not recorded".
 *
 * @param array<string, string> $a    Clean attribution (kitwp_attribution_clean()).
 * @param string                $page The page the form was sent from.
 * @return array<string, string> Posted name => value, in the standard's order.
 */
function kitwp_attribution_values( $a, $page ) {
	$visits   = kitwp_attribution_visits( $a );
	$first    = $visits['first'];
	$last     = $visits['last'] ? $visits['last'] : $first;
	$campaign = $last['gad_campaignid'] ?? $last['utm_id'] ?? '';
	if ( '' === $campaign && preg_match( '/^\d+$/', $last['utm_campaign'] ?? '' ) ) {
		$campaign = $last['utm_campaign'];
	}
	$values = [
		'lead_source'              => $last ? kitwp_attribution_source( $last ) : 'Not recorded',
		'google_ads_campaign_id'   => $campaign,
		'google_click_id'          => $last['gclid'] ?? '',
		'landing_page'             => $last['landing'] ?? '',
		'referrer'                 => $last['referrer'] ?? '',
		'lead_source_date'         => kitwp_attribution_date( $last['time'] ?? '' ),
		'form_submitted_from'      => (string) $page,
		'first_touch_source'       => $first ? kitwp_attribution_source( $first ) : '',
		'first_visit_date'         => kitwp_attribution_date( $first['time'] ?? '' ),
		'first_touch_landing_page' => $first['landing'] ?? '',
		'first_touch_referrer'     => $first['referrer'] ?? '',
	];
	return array_map( static fn( $v ) => '' === trim( (string) $v ) ? 'none' : (string) $v, $values );
}

/**
 * The extra rows of a checked attribution (kitwp_attribution_extras()): the latest touch's tags and click ids that
 * are present (its gclid and Campaign ID are rows of the eleven already), then the first visit's that differ from
 * them, as "First Touch <label>". The latest touch is the one kitwp_attribution_values() uses. landing_page and
 * referrer are left out: in posted fields they hold the standard's values (the latest touch, else the first visit).
 *
 * @param array<string, string> $a Clean attribution.
 * @return array<string, string> Label => value.
 */
function kitwp_attribution_extra_rows( $a ) {
	$visits = kitwp_attribution_visits( array_diff_key( $a, array_flip( [ 'landing_page', 'referrer' ] ) ) );
	$last   = $visits['last'] ? $visits['last'] : $visits['first'];
	$rows   = [];
	$first  = [];
	foreach ( kitwp_attribution_extras() as $name => $label ) {
		if ( isset( $last[ $name ] ) && ! in_array( $name, [ 'gclid', 'gad_campaignid' ], true ) ) {
			$rows[ $label ] = $last[ $name ];
		}
		if ( isset( $visits['first'][ $name ] ) && ( $last[ $name ] ?? null ) !== $visits['first'][ $name ] ) {
			$first[ 'First Touch ' . $label ] = $visits['first'][ $name ];
		}
	}
	return $rows + $first;
}

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
 * Where one visit came from, in words: an ad click (Google Ads: gclid, gbraid, wbraid or gad_campaignid; Microsoft
 * Ads: msclkid); else the campaign's source / medium; else a Facebook or Instagram link (fbclid); else the search
 * engine or the site that linked; else "Direct".
 *
 * @param array<string, string> $visit A visit (kitwp_attribution_visits()).
 * @return string
 */
function kitwp_attribution_source( $visit ) {
	foreach ( [ 'gclid', 'gbraid', 'wbraid', 'gad_campaignid' ] as $name ) {
		if ( ! empty( $visit[ $name ] ) ) {
			return 'Google Ads';
		}
	}
	if ( ! empty( $visit['msclkid'] ) ) {
		return 'Microsoft Ads';
	}
	if ( ! empty( $visit['utm_source'] ) ) {
		return $visit['utm_source'] . ( ! empty( $visit['utm_medium'] ) ? ' / ' . $visit['utm_medium'] : '' );
	}
	if ( ! empty( $visit['fbclid'] ) ) {
		return 'Facebook / Instagram';
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
	return 'Direct';
}

/**
 * The Lead Attribution rows: the company standard's eleven, always, in its order (an empty value says "none"),
 * then the extra tags and click ids that are present (kitwp_attribution_extra_rows()).
 *
 * @param array<string, mixed> $posted The posted fields (with the standard's values from kitwp_attribution_posted()).
 * @param string               $page   The page the form was sent from, when the posted fields have no standard values.
 * @return array<int, array{0: string, 1: string}> [ label, value ].
 */
function kitwp_attribution_rows( $posted, $page = '' ) {
	$a      = kitwp_attribution_clean( $posted );
	$values = isset( $posted['lead_source'] ) ? $posted : kitwp_attribution_values( $a, $page );
	$rows   = [];
	foreach ( kitwp_attribution_standard() as $name => $label ) {
		$value  = is_scalar( $values[ $name ] ?? null ) ? trim( (string) $values[ $name ] ) : '';
		$rows[] = [ $label, '' !== $value ? $value : 'none' ];
	}
	foreach ( kitwp_attribution_extra_rows( $a ) as $label => $value ) {
		$rows[] = [ $label, $value ];
	}
	return $rows;
}

/**
 * The "Lead Attribution" table for the lead email ([_kitk_source]): a title row in the email's brand colour (its
 * text black or white, whichever reads better), label cells grey, as the email's details table. Plain text: the
 * same rows as "Label: value" lines.
 *
 * @param array<string, mixed> $posted The posted fields.
 * @param string               $page   The page the form was sent from (used only without the standard's values).
 * @param bool                 $html   HTML email.
 * @return string
 */
function kitwp_attribution_table( $posted, $page = '', $html = true ) {
	$rows = kitwp_attribution_rows( $posted, $page );
	if ( ! $html ) {
		$text = [ 'Lead Attribution' ];
		foreach ( $rows as $row ) {
			$text[] = $row[0] . ': ' . $row[1];
		}
		return implode( "\n", $text );
	}
	$e    = static fn( $t ) => htmlspecialchars( (string) $t, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8' );
	$cell = 'border:1px solid #dddddd;text-align:left;padding:8px 10px;vertical-align:top;';
	$out  = '';
	foreach ( $rows as $row ) {
		$out .= '<tr><td style="' . $cell . 'width:38%;background-color:#fafafa;font-weight:bold;">' . $e( $row[0] ) . '</td><td style="' . $cell . 'word-break:break-all;">' . $e( $row[1] ) . '</td></tr>';
	}
	[ $bg, $ink ] = kitwp_attribution_title_colours( (string) KITWP_BRAND_COLOUR );
	return '<table role="presentation" width="100%" style="font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:1.4;color:#333333;border-collapse:collapse;width:100%;margin-top:16px;"><tbody>'
		. '<tr><td style="' . $cell . 'background-color:' . $bg . ';border-color:' . $bg . ';color:' . $ink . ';" colspan="2"><b>Lead Attribution</b></td></tr>'
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
