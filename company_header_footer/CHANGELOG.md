# Changelog

All notable changes to the Company Header Footer module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [19.0.1.0.0] - 2025-11-05

### Added
- Initial release for Odoo 19
- Support for custom header and footer images (JPG format)
- Multi-company support - each company can have unique header/footer
- Toggle controls to enable/disable custom header and footer independently
- Compatible with Standard and Boxed external layouts
- Automatic fallback to Odoo default layout when custom images not enabled
- Binary field storage with attachment=True for optimal performance
- Computed fields for image filenames
- Comprehensive README documentation

### Changed
- Updated module version to 19.0.1.0.0 for Odoo 19 compatibility
- Added `license` field (LGPL-3) to manifest (required in Odoo 19)
- Updated `invisible` attribute syntax to use Python expressions (`field == False` instead of `not field`)
- Replaced `<p>` tags with `<div>` tags for better rendering in Odoo 19
- Added icon indicators in form view for better UX
- Removed `store=False` from computed fields (default behavior)
- Added `assets`, `post_init_hook`, and `uninstall_hook` keys to manifest
- Removed `@api.depends('id')` decorators (compute methods cannot depend on 'id' field in Odoo)

### Technical Details
- Python 3.10+ compatible
- Uses modern f-string formatting
- Follows Odoo 19 coding guidelines
- QWeb templates compatible with Odoo 19 rendering engine
- Bootstrap 5 compatible styling

### Security
- Proper access control via ir.model.access.csv
- Binary fields stored as attachments for security
- Only system administrators can modify header/footer settings

## [Future Releases]

### Planned Features
- Support for multiple image formats (PNG, SVG)
- Preview functionality before saving
- Image size validation
- Automatic image optimization
- Per-report layout customization
- Dynamic header/footer based on report type
- Template library for common layouts

