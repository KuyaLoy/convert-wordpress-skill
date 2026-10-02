<?php
/**
 * The lead form. Contact Form 7 prints it from the Quote Form's Form tab, in the static markup
 * (kitwp_quote_form_html() in includes/forms.php). The markup below is only the fallback for when CF7 is off or the
 * form is not seeded yet: paste the static form's HTML here (same tags, classes and order), with the field ids
 * prefixed by $kitwp_p. It looks the same but sends nothing.
 *
 * @package kitwp
 * @var array{options: array<int, string>, source: string, prefix?: string, compact?: bool} $args
 */

$kitwp_cf7 = kitwp_quote_form_html( $args );
if ( '' !== $kitwp_cf7 ) {
	echo $kitwp_cf7; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- built by CF7 and kitwp_cf7_control().
	return;
}
$kitwp_p = (string) ( $args['prefix'] ?? '' );
?>
<form class="<?php echo esc_attr( KITWP_FORM_CLASS ); ?>" action="" method="post">
	<input type="hidden" name="source" value="<?php echo esc_attr( $args['source'] ); ?>">
	<label class="hp" aria-hidden="true">Leave this empty<input type="text" tabindex="-1" autocomplete="off" name="company"></label>
	<div class="field"><label for="<?php echo esc_attr( $kitwp_p ); ?>name">Your Name</label><input id="<?php echo esc_attr( $kitwp_p ); ?>name" type="text" required autocomplete="name" name="name"></div>
	<div class="field"><label for="<?php echo esc_attr( $kitwp_p ); ?>phone">Phone</label><input id="<?php echo esc_attr( $kitwp_p ); ?>phone" type="tel" required autocomplete="tel" name="phone"></div>
	<?php if ( empty( $args['compact'] ) ) : ?>
		<div class="field"><label for="<?php echo esc_attr( $kitwp_p ); ?>email">Email</label><input id="<?php echo esc_attr( $kitwp_p ); ?>email" type="email" autocomplete="email" name="email"></div>
	<?php endif; ?>
	<div class="field"><label for="<?php echo esc_attr( $kitwp_p ); ?>service">Service</label><select id="<?php echo esc_attr( $kitwp_p ); ?>service" name="service" required><option value="" disabled selected>Select a service</option><?php foreach ( (array) $args['options'] as $kitwp_option ) : ?><option><?php echo esc_html( $kitwp_option ); ?></option><?php endforeach; ?></select></div>
	<div class="field"><label for="<?php echo esc_attr( $kitwp_p ); ?>msg">Message</label><textarea id="<?php echo esc_attr( $kitwp_p ); ?>msg" name="msg"></textarea></div>
	<button type="submit">Send</button>
</form>
