/**
 * Chat lead save: the pattern for a static site's chat widget in WordPress. Not loaded on its own.
 *
 * The static widget (copied unchanged to assets/chat-widget.js) keeps its questions, state and markup; only the call
 * where it sent the lead changes: call window.kitwpChatSave(values) instead (paste this file's function at the top
 * of chat-widget.js). includes/forms.php prints window.__KITWP_CHAT before the widget loads:
 *   endpoint   the Chat Lead form's CF7 REST URL: /wp-json/contact-form-7/v1/contact-forms/<id>/feedback
 *   fields     CF7's hidden fields: _wpcf7, _wpcf7_version, _wpcf7_locale, _wpcf7_unit_tag, _wpcf7_container_post
 *   recaptcha  the reCAPTCHA v3 site key ('' when off); window.kitwpRecaptcha() returns a token
 *   phone, tel and anything added through the "kitwp_chat_config" filter
 *
 * Rules that bite: send FormData (a JSON body gets 415); always send _wpcf7_unit_tag (400 without it); the value
 * names match the Chat Lead form tab ([text* name] ...); "mail_sent" is the only success; "source" starting with
 * "chat:" labels the lead email "Chat widget".
 *
 * Example: kitwpChatSave({ name, phone, postcode, service, when, msg }).then(showThanks, showError)
 */
(function () {
	'use strict';

	function token(siteKey) {
		if (!siteKey || typeof window.kitwpRecaptcha !== 'function') {
			return Promise.resolve('');
		}
		// Google can be slow or blocked: after 10 seconds send without a token (CF7 then decides).
		return Promise.race([
			window.kitwpRecaptcha().catch(function () {
				return '';
			}),
			new Promise(function (done) {
				setTimeout(function () {
					done('');
				}, 10000);
			}),
		]);
	}

	window.kitwpChatSave = function (values) {
		var c = window.__KITWP_CHAT || {};
		if (!c.endpoint) {
			return Promise.reject(new Error('The Chat Lead form is not seeded yet.'));
		}
		var body = new FormData();
		Object.keys(c.fields || {}).forEach(function (k) {
			body.append(k, c.fields[k]);
		});
		Object.keys(values || {}).forEach(function (k) {
			body.append(k, values[k] == null ? '' : String(values[k]));
		});
		if (!body.has('source')) {
			body.append('source', 'chat:' + window.location.pathname);
		}
		return token(c.recaptcha)
			.then(function (t) {
				if (t) {
					body.append('_wpcf7_recaptcha_response', t);
				}
				return fetch(c.endpoint, { method: 'POST', body: body });
			})
			.then(function (r) {
				return r.json().catch(function () {
					throw new Error('HTTP ' + r.status);
				});
			})
			.then(function (res) {
				if (res.status !== 'mail_sent') {
					var e = new Error(res.message || res.status || 'not sent');
					e.result = res; // res.invalid_fields: [{ field, message }] for validation_failed
					throw e;
				}
				return res;
			});
	};
})();
