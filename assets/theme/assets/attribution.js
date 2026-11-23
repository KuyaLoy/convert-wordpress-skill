/**
 * Form attribution: where each lead came from, on every Contact Form 7 form (includes/forms-attribution.php
 * enqueues this on every page; the server checks every value again). First party only: nothing leaves the browser
 * until the visitor sends a form.
 *
 * Settings (window.kitwpAttributionConfig): days (how long the first visit is kept, KITWP_ATTRIBUTION_DAYS; 0 =
 * this visit only), consent (KITWP_ATTRIBUTION_CONSENT) and thankYou (the thank-you page's address).
 *
 * Consent: the first visit goes to localStorage only when the site has no consent banner, or once the visitor
 * accepted. "auto" reads Google Consent Mode from the dataLayer: a page that sets a consent default has a banner;
 * ad_storage or analytics_storage "granted" (default or update) is an accept, an update with neither granted a
 * decline. "banner": the site's banner (one without Consent Mode) calls window.kitwpConsent(true or false) when the
 * visitor chooses and on each page with the stored choice (or dispatches a "kitwp:consent" event with detail true or
 * false). "none": no banner. Until an accept, and after a decline, only this visit is kept (sessionStorage, gone
 * with the visit), and a decline removes a stored first visit. The form still gets this visit's values: the visitor
 * sends them with the form.
 *
 * Last touch, per visit (sessionStorage): the campaign tags (utm_source, utm_medium, utm_campaign, utm_term,
 * utm_content) and ad click ids (gclid, gbraid, wbraid, fbclid, msclkid) the visit came with, its first page and
 * the other site that sent it; a new campaign link within the visit replaces them. First touch (localStorage, kept
 * `days`): the first visit's source, medium, campaign, page, referrer and date. Addresses keep host and path only.
 * Each form gets them as hidden fields (utm_*, gclid..., landing_page, referrer, first_source, first_medium,
 * first_campaign, first_landing_page, first_referrer, first_seen). window.kitwpAttribution() returns them (the
 * chat widget adds them to its post). After a form is sent, the thank-you page pushes one generate_lead event to
 * the dataLayer with the form's name, source and medium (a refresh or a direct visit pushes nothing).
 */
(function () {
	'use strict';

	var c = window.kitwpAttributionConfig || {};
	var days = parseInt(c.days, 10);
	days = isNaN(days) || days < 0 ? 90 : days;
	var TAGS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'];
	var CLICKS = ['gclid', 'gbraid', 'wbraid', 'fbclid', 'msclkid'];
	var now = Date.now();

	function storage(kind) {
		try {
			var s = window[kind];
			s.setItem('kitwp_t', '1');
			s.removeItem('kitwp_t');
			return s;
		} catch (e) {
			return null; // blocked (private mode, strict settings): the form still gets this page's values
		}
	}
	function get(s, key) {
		try {
			return s ? JSON.parse(s.getItem(key) || 'null') : null;
		} catch (e) {
			return null;
		}
	}
	function put(s, key, value) {
		try {
			if (s) {
				s.setItem(key, JSON.stringify(value));
			}
		} catch (e) {
			// full or blocked: nothing to keep
		}
	}
	// Host and path only: a query can carry an email address or a name.
	function page(url) {
		try {
			var u = new URL(url, window.location.href);
			return /^https?:$/.test(u.protocol) ? u.origin + u.pathname : '';
		} catch (e) {
			return '';
		}
	}
	function otherSite(ref) {
		try {
			return ref && new URL(ref).host !== window.location.host ? page(ref) : '';
		} catch (e) {
			return '';
		}
	}

	var query = new URLSearchParams(window.location.search);
	var arrived = {};
	TAGS.concat(CLICKS).forEach(function (k) {
		var v = query.get(k);
		if (v) {
			arrived[k] = v.slice(0, 200);
		}
	});
	var campaign = Object.keys(arrived).length > 0;
	var session = storage('sessionStorage');
	var local = days > 0 ? storage('localStorage') : null;

	var last = get(session, 'kitwp_attr_last');
	if (!last || campaign) {
		last = arrived;
		last.landing_page = page(window.location.href);
		last.referrer = otherSite(document.referrer);
		put(session, 'kitwp_attr_last', last);
	}
	var mode = c.consent === 'banner' || c.consent === 'none' ? c.consent : 'auto';
	var choice = null; // the banner's answer through window.kitwpConsent(): true or false
	// Google Consent Mode in the dataLayer: null when the page sets none, else 'yes', 'no' or 'pending'.
	function consentMode() {
		var dl = window.dataLayer || [];
		var seen = false;
		var updated = false;
		var granted = false;
		for (var i = 0; i < dl.length; i++) {
			var e = dl[i];
			if (e && e[0] === 'consent' && (e[1] === 'default' || e[1] === 'update') && e[2]) {
				seen = true;
				updated = updated || e[1] === 'update';
				if (e[2].ad_storage || e[2].analytics_storage) {
					granted = e[2].ad_storage === 'granted' || e[2].analytics_storage === 'granted';
				}
			}
		}
		if (!seen) {
			return null;
		}
		return granted ? 'yes' : updated ? 'no' : 'pending';
	}
	// 'free' (no banner), 'yes' (accepted), 'no' (declined) or 'pending'.
	function consent() {
		if (mode === 'none') {
			return 'free';
		}
		if (choice !== null) {
			return choice ? 'yes' : 'no';
		}
		var cm = consentMode();
		return cm || (mode === 'banner' ? 'pending' : 'free');
	}
	function mayKeep() {
		var s = consent();
		return !!local && (s === 'free' || s === 'yes');
	}

	var first = (mayKeep() && get(local, 'kitwp_attr_first')) || get(session, 'kitwp_attr_first');
	if (!first || !first.t || (days > 0 && now - first.t > days * 864e5)) {
		first = {
			t: now,
			source: arrived.utm_source || '',
			medium: arrived.utm_medium || '',
			campaign: arrived.utm_campaign || '',
			landing: page(window.location.href),
			referrer: otherSite(document.referrer),
		};
	}
	put(session, 'kitwp_attr_first', first);
	// Apply the visitor's current choice: keep the first visit after an accept, drop it after a decline.
	function sync() {
		if (mayKeep()) {
			put(local, 'kitwp_attr_first', first);
		} else if (local && consent() === 'no') {
			try {
				local.removeItem('kitwp_attr_first');
			} catch (e) {
				// blocked: nothing was stored
			}
		}
	}
	sync();
	window.kitwpConsent = function (accepted) {
		choice = accepted === true || accepted === 'granted';
		sync();
	};
	document.addEventListener('kitwp:consent', function (e) {
		window.kitwpConsent(e && e.detail);
	});

	function fields() {
		var f = {};
		TAGS.concat(CLICKS, ['landing_page', 'referrer']).forEach(function (k) {
			if (last[k]) {
				f[k] = last[k];
			}
		});
		[
			['first_source', first.source],
			['first_medium', first.medium],
			['first_campaign', first.campaign],
			['first_landing_page', first.landing],
			['first_referrer', first.referrer],
		].forEach(function (p) {
			if (p[1]) {
				f[p[0]] = p[1];
			}
		});
		f.first_seen = new Date(first.t).toISOString().slice(0, 10);
		return f;
	}
	window.kitwpAttribution = fields;

	function isCf7(form) {
		return !!(form && form.querySelector && form.querySelector('input[name="_wpcf7"]'));
	}
	// Hidden fields are updated in place (a page restored from the back button keeps its inputs: never twice).
	function fill(form) {
		if (!isCf7(form)) {
			return;
		}
		sync(); // a Consent Mode update since the page loaded counts from here
		var f = fields();
		Object.keys(f).forEach(function (k) {
			var input = form.querySelector('input[type="hidden"][name="' + k + '"]');
			if (!input) {
				input = document.createElement('input');
				input.type = 'hidden';
				input.name = k;
				form.appendChild(input);
			}
			input.value = f[k];
		});
	}
	function fillAll() {
		Array.prototype.forEach.call(document.forms, fill);
	}
	// A form added later (a pop-up) is filled when it is first used.
	document.addEventListener(
		'focusin',
		function (e) {
			fill(e.target && e.target.form);
		},
		true
	);
	document.addEventListener(
		'submit',
		function (e) {
			var form = e.target;
			if (!isCf7(form)) {
				return;
			}
			fill(form);
			var f = fields();
			put(session, 'kitwp_lead', {
				form: form.getAttribute('data-form-name') || '',
				source: f.utm_source || (f.referrer ? 'referral' : f.gclid ? 'google' : 'direct'),
				medium: f.utm_medium || (f.gclid ? 'cpc' : ''),
				at: Date.now(),
			});
		},
		true
	);
	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', fillAll);
	} else {
		fillAll();
	}

	// generate_lead once per sent form, on the thank-you page only, within 30 minutes of the submit.
	var lead = c.thankYou && page(window.location.href) === page(c.thankYou) ? get(session, 'kitwp_lead') : null;
	if (lead && now - lead.at < 30 * 60 * 1000) {
		try {
			session.removeItem('kitwp_lead');
		} catch (e) {
			// blocked: the event may repeat on a refresh
		}
		window.dataLayer = window.dataLayer || [];
		window.dataLayer.push({
			event: 'generate_lead',
			form_name: lead.form,
			lead_source: lead.source,
			lead_medium: lead.medium,
		});
	}
})();
