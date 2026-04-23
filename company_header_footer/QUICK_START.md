# Quick Start Guide - Company Header Footer Module

## ✅ Installation Complete!

The **Company Header Footer** module (v19.0.1.0.0) has been successfully installed in your Odoo 19 instance.

---

## 🚀 How to Use

### Step 1: Start Odoo Server

In PyCharm, configure the Python interpreter to use:
```
/home/sabry3/odoo_19_comunity/.venv/bin/python
```

Or start from terminal:
```bash
cd /home/sabry3/odoo_19_comunity
.venv/bin/python odoo19/odoo-bin -c odoo_conf/odoo.conf
```

### Step 2: Access Odoo

Open your browser and go to:
```
http://localhost:8029
```

### Step 3: Configure Header & Footer

1. **Navigate to Settings**
   - Click on **Settings** in the main menu
   - Or go to **Settings → Companies → Manage Companies**

2. **Select Your Company**
   - Click on your company name
   - The company form will open

3. **Go to Report Header & Footer Tab**
   - Look for the **"Report Header & Footer"** tab
   - Click on it

4. **Enable Custom Header/Footer**
   - Check ☑ **Use Custom Header**
   - Check ☑ **Use Custom Footer**

5. **Upload Images**
   - Click on the image upload area for header
   - Select your header image (JPG recommended, 1024x200 pixels)
   - Click on the image upload area for footer
   - Select your footer image (JPG recommended, 1024x150 pixels)

6. **Save**
   - Click the **Save** button

### Step 4: Test

Generate any PDF report to see your custom header and footer:
- Sales Order
- Invoice
- Purchase Order
- Delivery Order
- Any other report

---

## 📋 Image Specifications

### Header Image
- **Format**: JPG (recommended), PNG also works
- **Recommended Size**: 1024 x 200 pixels
- **Aspect Ratio**: Wide landscape
- **Maximum File Size**: < 500KB for best performance
- **Content**: Company logo, branding, contact info

### Footer Image
- **Format**: JPG (recommended), PNG also works
- **Recommended Size**: 1024 x 150 pixels
- **Aspect Ratio**: Wide landscape
- **Maximum File Size**: < 500KB for best performance
- **Content**: Address, legal info, website, page numbers

---

## 🎯 Features

✅ **Custom Header Image** - Replace Odoo's default header with your own  
✅ **Custom Footer Image** - Replace Odoo's default footer with your own  
✅ **Toggle Control** - Enable/disable independently  
✅ **Multi-Company** - Each company can have different images  
✅ **Automatic Fallback** - Uses Odoo default when custom disabled  
✅ **Works Everywhere** - All PDF reports use your custom layout

---

## 🔧 Troubleshooting

### Images Not Showing
1. Make sure **Use Custom Header/Footer** is checked
2. Verify images are uploaded (not just selected)
3. Click **Save** after uploading
4. Clear browser cache
5. Regenerate the PDF report

### Can't Find the Tab
1. Make sure you're in the **Company form** (not list view)
2. Look for tabs at the top of the form
3. Scroll through tabs if you have many

### Module Not Visible
1. Update Apps List: **Settings → Apps → Update Apps List**
2. Search for "Company Header Footer"
3. Should show as **Installed**

---

## 📚 Documentation

- **README.md** - Complete documentation
- **CHANGELOG.md** - Version history
- **ODOO19_COMPATIBILITY.md** - Technical details
- **INSTALLATION_LOG.md** - Installation details

---

## 💡 Tips

1. **Design Tips**
   - Keep important content away from edges
   - Use high-resolution images (300 DPI for print)
   - Test with actual reports before final deployment
   - Use consistent branding colors

2. **Performance Tips**
   - Compress images to reduce file size
   - Use JPG for photographs
   - Optimize images before uploading

3. **Multi-Company**
   - Each company can have unique header/footer
   - Switch between companies to configure each one
   - Images are company-specific

---

## ✅ Installation Summary

**What Was Installed:**
- ✅ Module: company_header_footer v19.0.1.0.0
- ✅ Database: coheader
- ✅ Status: Installed and ready
- ✅ Time: 0.35 seconds
- ✅ Errors: None

**Issue Resolved:**
- ❌ Initial: Compute method dependency issue
- ✅ Fixed: Removed @api.depends('id') decorators
- ✅ Result: Clean installation

---

## 📞 Support

**Author**: iTech Co.  
**Website**: http://www.iTech.com.eg  
**License**: LGPL-3

For issues or questions, refer to the documentation or contact iTech Co.

---

**Module is ready to use! Enjoy your custom report layouts! 🎉**
