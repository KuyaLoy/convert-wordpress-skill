/**
 * reCAPTCHA v3 for the lead forms and the chat, enqueued by includes/forms-spam.php only when CF7's reCAPTCHA
 * integration has keys. The settings come in as window.kitwpRecaptchaConfig:
 *   key        the site key
 *   formClass  the static form's class (KITWP_FORM_CLASS)
 *   lazy       "1": Google's script loads on the first touch of a lead form or the chat (KITWP_RECAPTCHA_LAZY)
 *   api        lazy only: Google's script URL as CF7 registered it
 *   warm       lazy only: the selector whose first touch starts loading Google's script
 *
 * CF7's own script only fills forms with its "wpcf7-form" class, which the static markup does not have, so on
 * submit this asks Google for a fresh token (tokens last two minutes), puts it in CF7's hidden
 * _wpcf7_recaptcha_response field and submits. After 10 seconds without Google the form submits without a token
 * (the server then decides). window.kitwpRecaptcha() gives the chat widget a token the same way.
 */
(function () {
	'use strict';

	var c = window.kitwpRecaptchaConfig || {};
	if (!c.key) {
		return;
	}
	var loading = null;

	function ready() {
		if (c.lazy !== '1') {
			return new Promise(function (ok, no) {
				if (typeof window.grecaptcha === 'undefined') {
					no();
					return;
				}
				window.grecaptcha.ready(ok);
			});
		}
		if (!loading) {
			loading = new Promise(function (ok, no) {
				var s = document.createElement('script');
				s.src = c.api;
				s.async = true;
				s.onload = function () {
					window.grecaptcha.ready(ok);
				};
				s.onerror = function () {
					loading = null;
					no();
				};
				document.head.appendChild(s);
			});
		}
		return loading;
	}

	window.kitwpRecaptcha = function () {
		return ready().then(function () {
			return window.grecaptcha.execute(c.key, { action: 'contactform' });
		});
	};

	if (c.lazy === '1' && c.warm) {
		var warm = function (e) {
			var t = e.target;
			if (t && t.closest && t.closest(c.warm)) {
				ready().catch(function () {});
			}
		};
		['focusin', 'pointerdown', 'touchstart'].forEach(function (name) {
			document.addEventListener(name, warm, { capture: true, passive: true });
		});
	}

	document.addEventListener(
		'submit',
		function (e) {
			var form = e.target;
			var field = form.querySelector && form.querySelector("input[name='_wpcf7_recaptcha_response']");
			if (!field || !form.classList.contains(c.formClass) || form.dataset.kitwpRc) {
				return;
			}
			e.preventDefault();
			var sent = false;
			var go = function (token) {
				if (sent) {
					return;
				}
				sent = true;
				if (token) {
					field.value = token;
				}
				form.dataset.kitwpRc = '1';
				form.submit();
			};
			setTimeout(function () {
				go('');
			}, 10000);
			window.kitwpRecaptcha().then(go, function () {
				go('');
			});
		},
		true
	);
})();
