/**
 * Form attribution: where each lead came from, on every Contact Form 7 form (includes/forms-attribution.php
 * enqueues this on every page; the server checks every value again). First party only: nothing leaves the browser
 * until the visitor sends a form.
 *
 * Settings (window.kitwpAttributionConfig): days (how long the first visit is kept, KITWP_ATTRIBUTION_DAYS; 0 =
 * this visit only) and thankYou (the thank-you page's address).
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
	var keep = local || session;
	var first = get(keep, 'kitwp_attr_first');
	if (!first || !first.t || (local && now - first.t > days * 864e5)) {
		first = {
			t: now,
			source: arrived.utm_source || '',
			medium: arrived.utm_medium || '',
			campaign: arrived.utm_campaign || '',
			landing: page(window.location.href),
			referrer: otherSite(document.referrer),
		};
		put(keep, 'kitwp_attr_first', first);
	}

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
