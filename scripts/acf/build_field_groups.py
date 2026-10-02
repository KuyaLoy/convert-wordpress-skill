#!/usr/bin/env python3
"""
Builds the ACF field group JSON for the theme: Theme Settings, component groups, template groups, Page Sections
and the menu item icon. Run from the WordPress root (or anywhere: paths are relative to this file):

    python3 _plan/tools/acf/build_field_groups.py            write acf-json/group_kitk_*.json
    python3 _plan/tools/acf/build_field_groups.py --check    only report what would change

Keys: group_kitk_<group>, field_kitk_<group>_<path>_<name>, layout_kitk_<group>_<layout>. They never change once
content is seeded (ACF stores values against the key). "modified" is bumped only for groups whose content changed,
so ACF > Field Groups lists exactly those under "Sync available": use each group's own Sync link (the bulk action
did nothing on the reference build). Defaults are the static site's copy, so a field nobody has saved still
renders 1:1 (read Theme Settings by field key: kitwp_setting()).

The library is at the top; replace the EXAMPLE SPEC with the site's content model (CONTENT-MODEL.md).
"""
import json
import os
import sys
import time

KEY = 'kitk'                     # ACF key prefix (new-site.py fills it)
THEME = '{{THEME}}'              # theme folder name
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
THEME_DIR = os.path.join(ROOT, 'wp-content', 'themes', THEME)
if os.path.exists(os.path.join(THEME_DIR, 'theme', 'functions.php')):  # _tw: WordPress loads <theme>/theme/
    THEME_DIR = os.path.join(THEME_DIR, 'theme')
OUT = os.path.join(THEME_DIR, 'acf-json')
NOW = int(time.time())
ICON_HELP = 'Material Symbols name, for example verified_user (fonts.google.com/icons).'
HIDE = ['the_content', 'excerpt', 'discussion', 'comments', 'author', 'format', 'featured_image', 'categories', 'tags', 'send-trackbacks']


# ---------------------------------------------------------------- library
def f(kind, key, name, label, **o):
    """One ACF field with every setting ACF writes for that type."""
    base = {'key': key, 'label': label, 'name': name, 'type': kind, 'instructions': o.pop('instructions', ''),
            'required': o.pop('required', 0), 'conditional_logic': 0,
            'wrapper': {'width': o.pop('width', ''), 'class': '', 'id': ''}}
    if kind in ('text', 'textarea', 'url', 'email', 'number'):
        base['default_value'] = o.pop('default', '')
        if kind in ('text', 'textarea', 'number'):
            base['placeholder'] = ''
        if kind == 'text':
            base.update({'maxlength': '', 'prepend': '', 'append': ''})
        if kind == 'textarea':
            base.update({'maxlength': '', 'rows': o.pop('rows', 3), 'new_lines': ''})
        if kind == 'number':
            base.update({'min': '', 'max': '', 'step': '', 'prepend': '', 'append': ''})
    elif kind == 'true_false':
        base.update({'message': o.pop('message', ''), 'default_value': o.pop('default', 0), 'ui': 1,
                     'ui_on_text': '', 'ui_off_text': ''})
    elif kind == 'color_picker':
        base.update({'default_value': o.pop('default', ''), 'enable_opacity': 0, 'return_format': 'string'})
    elif kind == 'image':
        base.update({'return_format': 'id', 'library': 'all', 'min_width': '', 'min_height': '', 'min_size': '',
                     'max_width': '', 'max_height': '', 'max_size': '', 'mime_types': '', 'preview_size': 'medium'})
    elif kind == 'link':
        base.update({'return_format': 'array'})
    elif kind == 'gallery':
        base.update({'return_format': 'id', 'library': 'all', 'min': o.pop('min', ''), 'max': o.pop('max', ''), 'min_width': '',
                     'min_height': '', 'min_size': '', 'max_width': '', 'max_height': '', 'max_size': '', 'mime_types': '',
                     'insert': 'append', 'preview_size': 'medium'})
    elif kind == 'wysiwyg':
        base.update({'default_value': o.pop('default', ''), 'tabs': 'all', 'toolbar': o.pop('toolbar', 'basic'), 'media_upload': 0, 'delay': 1})
    elif kind == 'post_object':
        base.update({'post_type': o.pop('post_type'), 'post_status': '', 'taxonomy': '', 'return_format': 'id',
                     'multiple': 0, 'allow_null': 1, 'bidirectional': 0, 'ui': 1, 'bidirectional_target': []})
    elif kind == 'select':
        base.update({'choices': o.pop('choices'), 'default_value': o.pop('default', ''), 'return_format': 'value',
                     'multiple': 0, 'allow_null': 0, 'ui': 0, 'ajax': 0, 'placeholder': ''})
    elif kind == 'relationship':
        base.update({'post_type': o.pop('post_type'), 'post_status': ['publish'], 'taxonomy': '', 'filters': ['search'],
                     'return_format': 'id', 'min': o.pop('min', ''), 'max': o.pop('max', ''), 'elements': '',
                     'bidirectional': 0, 'bidirectional_target': []})
    elif kind == 'tab':
        base.update({'placement': 'left', 'endpoint': 0, 'selected': 0})
        base['name'] = ''
    elif kind == 'group':
        base.update({'layout': 'block', 'sub_fields': o.pop('sub_fields')})
    elif kind == 'repeater':
        base.update({'layout': o.pop('layout', 'table'), 'pagination': 0, 'min': o.pop('min', 0), 'max': o.pop('max', 0),
                     'collapsed': '', 'button_label': o.pop('button', 'Add row'), 'rows_per_page': 20,
                     'sub_fields': o.pop('sub_fields')})
    elif kind == 'flexible_content':
        base.update({'layouts': {lay['key']: lay for lay in o.pop('layouts')}, 'min': '', 'max': '',
                     'button_label': o.pop('button', 'Add section')})
    assert not o, (key, o)
    return base


class G:
    """Builds fields for one group; keys are field_<KEY>_<prefix>_<path...>_<name>."""

    def __init__(self, prefix):
        self.p = prefix

    def k(self, *parts):
        return f'field_{KEY}_' + '_'.join((self.p,) + parts)

    def tab(self, label):
        return f('tab', self.k('tab', label.lower().replace(' & ', '_').replace(' ', '_')), '', label)

    def text(self, name, label, default='', *path, **o):
        return f('text', self.k(*path, name), name, label, default=default, **o)

    def area(self, name, label, default='', *path, **o):
        return f('textarea', self.k(*path, name), name, label, default=default, **o)

    def any(self, kind, name, label, *path, **o):
        return f(kind, self.k(*path, name), name, label, **o)

    def rep(self, name, label, subs, *path, **o):
        return f('repeater', self.k(*path, name), name, label, sub_fields=subs, **o)

    def group(self, name, label, subs, *path, **o):
        return f('group', self.k(*path, name), name, label, sub_fields=subs, **o)

    def layout(self, name, label, subs):
        return {'key': f'layout_{KEY}_{self.p}_{name}', 'name': name, 'label': label, 'display': 'block',
                'sub_fields': subs, 'min': '', 'max': ''}

    def flex(self, name, label, layouts, *path, **o):
        return f('flexible_content', self.k(*path, name), name, label, layouts=layouts, **o)


def field_group(key, title, fields, location, **o):
    return {'key': key, 'title': title, 'fields': fields, 'location': location, 'menu_order': o.get('menu_order', 0),
            'position': 'normal', 'style': o.get('style', 'default'), 'label_placement': 'top',
            'instruction_placement': 'label', 'hide_on_screen': o.get('hide', ''), 'active': o.get('active', True),
            'description': o.get('description', ''), 'show_in_rest': 0, 'display_title': '', 'modified': NOW}


groups = {}
INACTIVE_LOC = [[{'param': 'post_type', 'operator': '==', 'value': 'post'}]]

# ---------------------------------------------------------------- EXAMPLE SPEC (replace with the site's model)
# Theme Settings: the fields the kit's PHP reads (helpers.php, schema.php, forms.php) plus the 404 copy.
g = G('ts')
groups[f'group_{KEY}_theme_settings'] = field_group(f'group_{KEY}_theme_settings', 'Theme Settings', [
    g.tab('Business'),
    g.text('business_name', 'Business name', '{{SITE_NAME}}', width=50),
    g.text('legal_name', 'Legal name', '{{LEGAL_NAME}}', width=50),
    g.text('phone_display', 'Phone, as shown', '{{PHONE_DISPLAY}}', width=50, instructions='Used everywhere a phone number is shown.'),
    g.text('phone_tel', 'Phone, to dial', '{{PHONE_TEL}}', width=50, instructions='Digits only, used in tel: links.'),
    g.any('email', 'email', 'Email', default='{{EMAIL}}', width=50),
    g.text('company_number', 'Company number', '', width=25, instructions='As the static site shows it (ABN, EIN, company registration). Token {company_number}.'),
    g.text('registration', 'Licence or registration', '', width=25, instructions='Optional, as the static site shows it. Token {registration}.'),
    g.group('address', 'Address', [
        g.text('locality', 'Locality', '', 'address', width=25), g.text('region', 'Region', '', 'address', width=25),
        g.text('postcode', 'Postcode', '', 'address', width=25), g.text('country', 'Country', 'AU', 'address', width=25)]),
    g.any('image', 'schema_image', 'Business image (structured data)', width=35),
    g.tab('Quote form'),
    g.rep('qf_service_options', 'General service options', [g.text('label', 'Option', '', 'qf_service_options')], button='Add option',
          instructions='The service list on pages without their own list, and in the pop-up.'),
    g.tab('404'),
    g.text('e404_heading', 'Heading (H1)', '', width=75),
    g.area('e404_text', 'Text', '', rows=2),
], [[{'param': 'options_page', 'operator': '==', 'value': f'{KEY}-theme-settings'}]], style='seamless',
    description='Site-wide content (CONTENT-MODEL.md, Theme Settings).')

# Component group, inactive, for cloning or copying into layouts.
c = G('cmp')
groups[f'group_{KEY}_cmp_heading'] = field_group(f'group_{KEY}_cmp_heading', 'Component: Heading', [
    c.text('eyebrow', 'Eyebrow', '', 'heading', width=30), c.text('heading', 'Heading', '', 'heading', width=70),
    c.area('sub', 'Sub', '', 'heading', rows=2)], INACTIVE_LOC, active=False, description='Cloned by layouts.')

# A template group: fixed sections for pages that share a layout (here a Service page).
sv = G('service')
groups[f'group_{KEY}_tpl_service'] = field_group(f'group_{KEY}_tpl_service', 'Template: Service', [
    sv.tab('Hero'),
    sv.text('hero_h1', 'H1', '', width=50, required=1), sv.text('hero_em', 'H1 emphasis', '', width=50),
    sv.area('hero_sub', 'Sub', '', rows=2, instructions='Bold with <b>.'),
    sv.any('image', 'hero_image', 'Hero image', width=35),
    sv.tab('FAQs'),
    sv.rep('faqs', 'FAQs', [sv.text('question', 'Question', '', 'faqs'), sv.area('answer', 'Answer', '', 'faqs', rows=3)],
           layout='block', button='Add FAQ'),
], [[{'param': 'page_template', 'operator': '==', 'value': 'page-templates/service.php'}]],
    description='Service pages (CONTENT-MODEL.md).', hide=HIDE)

# Page Sections: one Flexible Content field for one-off pages (and posts).
ps = G('ps')
PS = ('page_sections',)
layouts = [
    ps.layout('page_head', 'Page head', [ps.text('eyebrow', 'Eyebrow', '', *PS, 'page_head', width=30),
                                        ps.text('h1', 'H1', '', *PS, 'page_head', width=35, required=1),
                                        ps.text('em', 'H1 emphasis', '', *PS, 'page_head', width=35),
                                        ps.area('sub', 'Sub', '', *PS, 'page_head', rows=2)]),
    ps.layout('faq', 'FAQ block', [ps.text('heading', 'Heading', '', *PS, 'faq'),
                                   ps.rep('faqs', 'FAQs', [ps.text('question', 'Question', '', *PS, 'faq', 'faqs'),
                                                           ps.area('answer', 'Answer', '', *PS, 'faq', 'faqs', rows=3)],
                                          *PS, 'faq', layout='block', button='Add FAQ')]),
    ps.layout('final_cta', 'Final CTA', [ps.text('heading', 'Heading', '', *PS, 'final_cta', width=50),
                                         ps.area('text', 'Text', '', *PS, 'final_cta', rows=2, instructions='{phone} is the phone number.')]),
]
groups[f'group_{KEY}_page_sections'] = field_group(f'group_{KEY}_page_sections', 'Page Sections', [
    ps.tab('Sections'),
    ps.flex('page_sections', 'Page sections', layouts, instructions='The page, section by section. The first row holds the H1.'),
    ps.tab('Breadcrumbs'),
    ps.any('true_false', 'crumbs_hide', 'Hide breadcrumbs', default=0, width=25),
    ps.text('crumbs_label', 'Label (empty: the page title)', '', width=25),
    ps.text('crumbs_parent_label', 'Parent label (optional)', '', width=25),
    ps.text('crumbs_parent_url', 'Parent link', '', width=25),
], [[{'param': 'page_template', 'operator': '==', 'value': 'default'}, {'param': 'post_type', 'operator': '==', 'value': 'page'}],
    [{'param': 'post_type', 'operator': '==', 'value': 'post'}]], description='Flexible pages and posts.', hide=HIDE)

# Menu item icon (read by the menu walker and written by the seeder: field_<KEY>_menu_item_icon).
m = G('menu_item')
groups[f'group_{KEY}_menu_item'] = field_group(f'group_{KEY}_menu_item', 'Menu item', [
    m.text('icon', 'Icon', '', instructions=ICON_HELP + ' Leave empty for none.')],
    [[{'param': 'nav_menu_item', 'operator': '==', 'value': 'all'}]], description='Icon shown before the menu label.')


# ---------------------------------------------------------------- checks and write
def check(groups):
    """Every key unique, every key on the naming rule, field names unique within their parent."""
    seen = set()

    def walk(fields, where):
        names = [x['name'] for x in fields if x.get('name')]
        dup = {n for n in names if names.count(n) > 1}
        assert not dup, f'duplicate field names {dup} in {where}'
        for x in fields:
            assert x['key'] not in seen, 'duplicate key ' + x['key']
            assert x['key'].startswith(f'field_{KEY}_'), 'key off the naming rule: ' + x['key']
            seen.add(x['key'])
            walk(x.get('sub_fields', []), x['key'])
            for lay in (x.get('layouts') or {}).values():
                assert lay['key'] not in seen, 'duplicate key ' + lay['key']
                assert lay['key'].startswith(f'layout_{KEY}_'), 'key off the naming rule: ' + lay['key']
                seen.add(lay['key'])
                walk(lay['sub_fields'], lay['key'])

    for key, grp in groups.items():
        assert key == grp['key'] and key.startswith(f'group_{KEY}_'), 'group key ' + key
        walk(grp['fields'], key)
    return len(seen)


def write(groups, only_check=False):
    os.makedirs(OUT, exist_ok=True)
    changed = []
    for key, grp in groups.items():
        path = os.path.join(OUT, key + '.json')
        old = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else None
        if old is not None:
            same = {k: v for k, v in old.items() if k != 'modified'} == {k: v for k, v in grp.items() if k != 'modified'}
            if same:
                continue
        changed.append(key)
        if not only_check:
            with open(path, 'w', encoding='utf-8') as fh:
                json.dump(grp, fh, indent=4, ensure_ascii=False)
                fh.write('\n')
    return changed


if __name__ == '__main__':
    n = check(groups)
    changed = write(groups, '--check' in sys.argv)
    verb = 'would change' if '--check' in sys.argv else 'written (modified ' + str(NOW) + ')'
    print(f'{len(groups)} groups, {n} keys; {len(changed)} {verb}: {", ".join(changed) or "none"}; folder {OUT}')
