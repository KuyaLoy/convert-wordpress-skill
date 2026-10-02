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
