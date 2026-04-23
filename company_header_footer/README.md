# Company Header Footer

## Overview

This Odoo module allows you to use custom header and footer images (JPG format) for your company's PDF reports instead of the default Odoo header and footer layouts. Each company in a multi-company environment can have its own unique header and footer images.

## Features

- ✅ **Custom Header Image**: Upload a custom JPG image to be used as the header in all PDF reports
- ✅ **Custom Footer Image**: Upload a custom JPG image to be used as the footer in all PDF reports
- ✅ **Toggle Control**: Enable or disable custom header and footer independently
- ✅ **Multi-Company Support**: Each company can have different header/footer images
- ✅ **Fallback to Default**: Automatically falls back to Odoo's default layout when custom images are not enabled
- ✅ **Works with All Reports**: Compatible with all Odoo PDF reports
- ✅ **Multiple Layout Support**: Works with both Standard and Boxed external layouts

## Installation

1. Copy the `company_header_footer` module to your Odoo addons directory
2. Update the apps list in Odoo
3. Search for "Company Header Footer" in the Apps menu
4. Click Install

## Configuration

### Step 1: Access Company Settings

1. Navigate to **Settings** → **General Settings**
2. Scroll down to **Companies** section
3. Click on **Update Info** or go to **Settings** → **Users & Companies** → **Companies**
4. Select your company

### Step 2: Configure Header and Footer

1. In the company form, go to the **Report Header & Footer** tab
2. Check the boxes:
   - ☑ **Use Custom Header** - Enable custom header image
   - ☑ **Use Custom Footer** - Enable custom footer image

### Step 3: Upload Images

1. When **Use Custom Header** is enabled:
   - Upload your header image in JPG format
   - **Recommended size**: 1024 x 200 pixels
   - The image will be displayed at the top of all PDF reports

2. When **Use Custom Footer** is enabled:
   - Upload your footer image in JPG format
   - **Recommended size**: 1024 x 150 pixels
   - The image will be displayed at the bottom of all PDF reports

## Usage

Once configured, your custom header and footer images will automatically appear in all PDF reports, including:

- Sales Orders
- Purchase Orders
- Invoices
- Delivery Orders
- Any other reports using Odoo's external layout templates

### Switching Between Custom and Default

You can easily switch between custom images and Odoo's default layout:

- **To use custom images**: Check the "Use Custom Header" and/or "Use Custom Footer" boxes
- **To use default layout**: Uncheck the boxes to revert to Odoo's standard header/footer

## Technical Details

### Module Information

- **Technical Name**: `company_header_footer`
- **Version**: 19.0.1.0.0
- **Odoo Version**: 19.0 Community & Enterprise
- **Category**: Reporting
- **License**: LGPL-3
- **Author**: iTech Co.
- **Dependencies**: `base`, `web`
- **Python Version**: 3.10+

### Odoo 19 Compatibility

This module is fully compatible with Odoo 19 and follows all the latest conventions:

- ✅ Uses Python expression syntax for `invisible` attributes
- ✅ Includes required `license` field in manifest
- ✅ Uses `@api.depends()` decorators on compute methods
- ✅ Compatible with Odoo 19's QWeb rendering engine
- ✅ Bootstrap 5 compatible styling
- ✅ Modern Python 3.10+ syntax (f-strings, type hints ready)
- ✅ Follows Odoo 19 coding guidelines

### How It Works

The module extends the `res.company` model with the following fields:

- `report_header_image` (Binary): Stores the custom header image
- `report_footer_image` (Binary): Stores the custom footer image
- `use_custom_header` (Boolean): Controls whether to use custom header
- `use_custom_footer` (Boolean): Controls whether to use custom footer

The module inherits and modifies Odoo's standard external layout templates:

- `web.external_layout_standard`
- `web.external_layout_boxed`

When custom images are enabled, the module replaces the default header/footer divs with the uploaded images. When disabled, it falls back to Odoo's default behavior.

### Image Encoding

Images are stored as Binary fields and encoded to base64 format when displayed in PDF reports using the QWeb template syntax:

```xml
<img t-attf-src="data:image/jpeg;base64,{{ company.report_header_image }}" />
```

## File Structure

```
company_header_footer/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   └── res_company.py
├── views/
│   └── res_company_views.xml
├── report/
│   └── custom_external_layout.xml
├── security/
│   └── ir.model.access.csv
└── static/
    └── description/
        └── icon.png
```

## Best Practices

### Image Recommendations

1. **Format**: Use JPG format for smaller file sizes
2. **Resolution**: Use high-quality images (minimum 300 DPI for printing)
3. **Dimensions**:
   - Header: 1024 x 200 pixels (or similar aspect ratio)
   - Footer: 1024 x 150 pixels (or similar aspect ratio)
4. **File Size**: Keep images under 500KB for optimal performance
5. **Content**: Ensure important content is not too close to edges

### Design Tips

- **Header**: Include company logo, contact information, or branding elements
- **Footer**: Include company address, legal information, website, or page numbers
- **Consistency**: Use the same style and colors as your company branding
- **Contrast**: Ensure text in the report body is clearly distinguishable from header/footer

## Troubleshooting

### Images Not Showing

1. Verify that the checkboxes "Use Custom Header" and "Use Custom Footer" are enabled
2. Ensure images are uploaded in JPG format
3. Check that the images are not corrupted
4. Clear browser cache and regenerate the report

### Images Too Large or Small

- Adjust the image dimensions before uploading
- Use image editing software to resize images to recommended dimensions
- The module automatically scales images to fit the page width

### Multi-Company Issues

- Ensure you're logged in with a user that has access to the specific company
- Check that each company has its own header/footer configured
- Verify company context when viewing reports

## Support

For issues, questions, or contributions, please contact:

- **Author**: iTech Co.
- **Website**: http://www.iTech.com.eg

## Changelog

### Version 19.0.1.0.0 (2025-11-05)

**Added:**
- Initial release for Odoo 19
- Support for custom header and footer images (JPG format)
- Multi-company support - each company can have unique header/footer
- Toggle controls to enable/disable custom header and footer independently
- Compatible with Standard and Boxed external layouts
- Automatic fallback to Odoo default layout
- Comprehensive documentation and README

**Technical Improvements:**
- Uses Python expression syntax for `invisible` attributes (Odoo 19 standard)
- Added `@api.depends()` decorators on compute methods
- Proper `license` field in manifest (LGPL-3)
- Bootstrap 5 compatible styling
- Modern Python 3.10+ syntax with f-strings
- Optimized Binary field storage with `attachment=True`

For detailed changelog, see [CHANGELOG.md](CHANGELOG.md)

## License

LGPL-3 - See LICENSE file for details

