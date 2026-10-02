# {{SITE_NAME}}: content model

Status: **Sprint 0 draft**. Written {{DATE}}. What gets built and where every piece of content lives.
Source: see `SOURCE-NOTES.md`. Design reference: the golden master (`ARCHITECTURE.md`).

## 1. Principles

1. **1:1 first.** Markup is copied from the golden master; fields replace content, never structure or classes.
2. **Pages, not custom post types**, so every URL stays at the root. A page template decides which fields show.
3. **Fixed templates where pages share a layout; one Flexible Content field ("Page Sections") where they don't.**
4. **Say it once.** Anything on two or more pages lives in Theme Settings, with tokens (`{phone}`, `{year}`...). A
   page field left empty uses the Theme Settings default.
5. **Navigation is WordPress menus**; menu item icons are an ACF field.
6. **Grids list the pages themselves** (by template, in menu order), so a new page shows up everywhere.
7. **Explicit, not automatic.** Layout choices the static code makes by rule become visible fields, seeded with
   exactly what the static site shows.
8. **Images live in the Media Library** with their alt text; artwork drawn by code stays in the theme.

| Kind | ACF field | Markup | Output |
|---|---|---|---|
| Headings, eyebrows, labels | Text | none | `esc_html()` |
| Short copy, list items, FAQ answers | Textarea | `b strong em a br` | `kitwp_inline()` |
| Paragraphs, legal text | WYSIWYG (basic) | links, bold, lists | `wp_kses_post()` |
| Links | Link | | `esc_url()`, `esc_html()` |
| Images | Image (ID) | | `kitwp_img()` (static attributes) |

Copy rules from the source (copy brief) go into the field instructions.

## 2. Page inventory

Every route of the static sitemap, plus /thank-you/ and the 404. One row each.

| # | URL | Title in wp-admin | Built with | H1 from | JSON-LD | Sprint |
|---|---|---|---|---|---|---|
| 1 | `/` | Home | Front page, Page Sections | Hero | Org | S4 |

Pages the static site lacks (a blog index, archives): listed here as new, in the site's design, flagged to SEO.

## 3. Theme Settings (options page `kitk-theme-settings`)

| Tab | Fields |
|---|---|
| Business | name, legal name, phone (shown, to dial), email, company number, licence or registration (if any), address, opening hours, image |
| Header / Footer | labels, column titles, social URLs (an icon shows only when its URL is filled), copyright |
| Forms | default service options, pop-up copy |
| Templates | default headings and copy for each template (with tokens) |
| 404 | heading, text, buttons |

## 4. Menus

| Location | Menu | Items |
|---|---|---|
| `primary` | Primary | (from the static header, in order) |

## 5. Template field groups

One subsection per template: the section order on the page, then the fields by tab (`[x]` = the static field name).

## 6. Page Sections (Flexible Content)

| Layout | Fields | Used on | Headings |
|---|---|---|---|
| `page_head` | eyebrow, H1, emphasis, sub | inner pages | H1 |

## 7. Forms

| Label | Name | Type | Notes |
|---|---|---|---|
| Your Name | `name` | text, required | never let a field named `name` reach WordPress unfiltered (kitwp_lead_query_vars) |

## 8. Media

| What | Count | Goes to |
|---|---|---|
| Photos | | Media Library |
| Logos, coded artwork | | Theme `assets/` |

## 9. Naming

Field group `group_kitk_<name>`, field `field_kitk_<group>_<field>`, layout `layout_kitk_<group>_<layout>`; field
names snake_case; partials `template-parts/sections/<layout-with-dashes>.php`. Keys never change once content is
seeded.
