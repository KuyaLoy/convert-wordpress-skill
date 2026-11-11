<?php
/**
 * Site values for the kit's includes. new-site.py fills the {{...}} values from site.json; after that, edit them
 * here. The other files in includes/ stay generic and read these constants.
 *
 * @package kitwp
 */

/** The schema.org type of the static site's JSON-LD org block (Organization, LocalBusiness, or a more specific type such as Dentist, LegalService, Restaurant, Store). */
const KITWP_SCHEMA_TYPE = '{{SCHEMA_TYPE}}';

/** Area served, as the static JSON-LD prints it (a City name). */
const KITWP_AREA_SERVED = '{{AREA_SERVED}}';

/** Country calling code for the JSON-LD phone ("44": 020 7946 0000 becomes +442079460000); empty when the number is already international. */
const KITWP_COUNTRY_CODE = '{{COUNTRY_CODE}}';

/** priceRange in the JSON-LD; empty leaves it out. */
const KITWP_PRICE_RANGE = '{{PRICE_RANGE}}';

/** Brand colour: the theme-color meta and the link colour in the lead email. */
const KITWP_BRAND_COLOUR = '{{BRAND_COLOUR}}';

/**
 * Agency badge in the footer of the lead email AND the auto-reply ([_kitk_badge]), from the profile's "branding":
 * a PNG in the theme (email clients do not show SVG or WebP), 2x size, shown at the width below; its link and alt.
 * Empty path: no badge. A white badge needs the dark footer strip of lead-email.html / autoreply-email.html.
 */
const KITWP_EMAIL_BADGE       = '{{EMAIL_BADGE}}';
const KITWP_EMAIL_BADGE_LINK  = '{{EMAIL_BADGE_LINK}}';
const KITWP_EMAIL_BADGE_ALT   = '{{EMAIL_BADGE_ALT}}';
const KITWP_EMAIL_BADGE_WIDTH = {{EMAIL_BADGE_WIDTH}};

/**
 * Agency badge in the SITE footer (kitwp_agency_badge(), placed in the footer's bottom bar): a theme file (SVG is
 * fine on the web), its link, alt and height. Theme Settings > Branding can replace the image and link, or hide it.
 */
const KITWP_SITE_BADGE        = '{{SITE_BADGE}}';
const KITWP_SITE_BADGE_LINK   = '{{EMAIL_BADGE_LINK}}';
const KITWP_SITE_BADGE_ALT    = '{{EMAIL_BADGE_ALT}}';
const KITWP_SITE_BADGE_HEIGHT = 40;

/**
 * Leads portal: every sent lead form is also POSTed (JSON, Bearer key) to <PREFIX>_ENDPOINT with <PREFIX>_KEY from
 * wp-config (the keys never live in the theme). Empty prefix: off. Never on local, development or staging.
 */
const KITWP_LEADS_PREFIX = '{{LEADS_PREFIX}}';

/** Client wp-admin (client-admin.php): hide Posts and Comments from the client. Set false when the site uses them. */
const KITWP_CLIENT_HIDE_POSTS = true;

/** Client wp-admin: the "Need help?" line on the client's dashboard (an email, a web address or a phone number); empty hides it. */
const KITWP_CLIENT_HELP = '{{CLIENT_HELP}}';

/** The <html> lang and dir exactly as the static site prints them (lang="en", lang="ar" dir="rtl"); empty: WordPress's own. */
const KITWP_HTML_ATTRIBUTES = '{{HTML_ATTRIBUTES}}';

/** Open Graph locale, as the static head (en_US, en_GB, en_AU...). */
const KITWP_OG_LOCALE = '{{OG_LOCALE}}';

/**
 * The live domain, without www (lead emails: the envelope sender and Message-ID are checked against it, so local
 * mail is built exactly as on live).
 */
const KITWP_DOMAIN = '{{DOMAIN}}';

/** Where lead forms land (303) and the page kept out of the index. */
const KITWP_THANK_YOU = '/thank-you/';

/** Class of the static form element; the CF7 output is rewritten to <form class="..."> with it. */
const KITWP_FORM_CLASS = '{{FORM_CLASS}}';

/** CSS selector of the chat widget's launcher and panel, so reCAPTCHA can warm up on first touch (lazy mode). */
const KITWP_CHAT_SELECTOR = '{{CHAT_SELECTOR}}';

/**
 * reCAPTCHA mode. false: CF7's own script loads Google's on every page and the theme asks for a token on submit
 * (proven on a live site). true: Google's script loads on the first form or chat touch, with a 10 s
 * fallback (faster on phones; tested locally only, so retest every form on live before relying on it).
 */
const KITWP_RECAPTCHA_LAZY = false;

/**
 * The static build's image widths (the next/image sizes it serves) and its first deviceSize, which decides the
 * srcset when sizes uses vw. Read both from the static site's next.config (images.imageSizes, images.deviceSizes).
 */
const KITWP_IMAGE_WIDTHS       = [ 256, 384, 640, 828, 1080, 1200, 1920, 2048 ];
const KITWP_FIRST_DEVICE_SIZE  = 640;

/**
 * The static site's own stylesheets, byte for byte and in its order, as theme files (copied from its build, for
 * example [ 'assets/css/style.min.css', 'assets/css/responsive.min.css' ]). Empty: the starter's stylesheet
 * (Barebones' built CSS, _tw's style.css). Filled: the starter's stylesheet is left out. Proven by the swap test.
 */
const KITWP_STYLESHEETS = [];

/**
 * The static site's inline <style> in <head> (critical CSS), as theme files printed in order. "url(assets/" in
 * them becomes the theme's assets URL, so the theme keeps the static site's assets/ layout.
 */
const KITWP_INLINE_CSS = [];

/**
 * CSS printed only while the logged-in WordPress toolbar shows (visitors never get it). A sticky or fixed static
 * header needs it, or the toolbar covers the header: move the header, any panel that opens below it and anchor
 * offsets down by WordPress's own --wp-admin--admin-bar--height (32px; 46px at 782px and below). WordPress lets the
 * toolbar scroll away at 600px and below; keep it fixed there so a mobile menu's close button is never covered.
 * Example for a sticky header (check the static CSS for every use of the header height):
 * '@media screen and (max-width:600px){#wpadminbar{position:fixed}}header.site-header{top:var(--wp-admin--admin-bar--height,32px)}'
 * Empty: WordPress's default (fine for a header that scrolls with the page).
 */
const KITWP_ADMIN_BAR_CSS = '';

/** Google Fonts preconnects: only when the static head has them (sites with self-hosted fonts do not). */
const KITWP_PRECONNECT_FONTS = 'true' === '{{PRECONNECT_FONTS}}';

/** Font files preloaded on every page, as the static head (theme files, for example 'assets/fonts/Brand-Bold.woff2'). */
const KITWP_PRELOAD_FONTS = [];

/** Theme files preloaded on every page, as the static head (usually the logos). */
const KITWP_PRELOAD_ASSETS = [ 'assets/brand/logo.svg' ];

/**
 * robots.txt once the site is public: the static site's file, with {site} for the home URL. The Sitemap line
 * points to Yoast's index.
 */
const KITWP_ROBOTS_TXT = "User-Agent: *\nAllow: /\nDisallow: /thank-you/\n\nHost: {site}\nSitemap: {site}/sitemap_index.xml\n";

/**
 * Opening hours in the JSON-LD, as the static site prints them (schema.org OpeningHoursSpecification rows); empty:
 * none. Example: [ [ 'dayOfWeek' => [ 'Monday', 'Tuesday' ], 'opens' => '09:00', 'closes' => '17:00' ] ].
 */
const KITWP_OPENING_HOURS = [];
