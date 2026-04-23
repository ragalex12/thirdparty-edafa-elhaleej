# Step-by-Step Testing Guide
## Company Header Footer Module v19.0.1.0.0

---

## Prerequisites ✅

- [x] Module installed successfully
- [x] Database initialized (coheader)
- [x] Virtual environment set up (.venv)
- [ ] Test images prepared (Header: 1024x200px, Footer: 1024x150px)

---

## Part 1: Prepare Test Images

### Option A: Use Sample Images (Quick Test)

You can create simple test images using online tools or existing images.

**Recommended Sizes:**
- Header: 1024 x 200 pixels
- Footer: 1024 x 150 pixels

### Option B: Create Test Images with Text

If you want to quickly test, you can use any existing JPG images temporarily.

---

## Part 2: Start Odoo Server

### Method 1: Using Terminal (Recommended for Testing)

```bash
# Navigate to project directory
cd /home/sabry3/odoo_19_comunity

# Start Odoo with virtual environment Python
.venv/bin/python odoo19/odoo-bin -c odoo_conf/odoo.conf
```

**Expected Output:**
```
INFO ? odoo: Odoo version 19.0
INFO ? odoo: Using configuration file at ...
INFO ? odoo.service.server: HTTP service (werkzeug) running on sabry3-Precision-5540:8029
```

**✅ Server is ready when you see**: `HTTP service (werkzeug) running on ...`

### Method 2: Using PyCharm

1. Open Run Configuration
2. Set Script path: `/home/sabry3/odoo_19_comunity/odoo19/odoo-bin`
3. Set Parameters: `-c /home/sabry3/odoo_19_comunity/odoo_conf/odoo.conf`
4. Set Python interpreter: `/home/sabry3/odoo_19_comunity/.venv/bin/python`
5. Click Run

---

## Part 3: Access Odoo Web Interface

### Step 1: Open Browser

Open your web browser and navigate to:
```
http://localhost:8029
```

### Step 2: Login or Setup

**If First Time:**
1. You'll see the database creation/selection page
2. Select database: `coheader`
3. Create admin account:
   - Email: admin@example.com (or your email)
   - Password: admin (or your password)
   - Language: English
   - Country: Your country

**If Already Setup:**
1. Enter your credentials
2. Click "Log in"

---

## Part 4: Verify Module Installation

### Step 1: Check Apps Menu

1. Click on the **Apps** icon in the main menu (grid icon)
2. Remove the "Apps" filter (clear the search)
3. Search for: `company_header_footer`

**✅ Expected Result:**
- Module should appear
- Status should show: **INSTALLED** (green checkmark)
- Version: 19.0.1.0.0

### Step 2: Alternative Check

1. Go to **Settings** menu
2. Scroll down to find **Activate the developer mode**
3. Click on it (you'll see a bug icon in the top menu)
4. Go back to Apps
5. You should see technical information

---

## Part 5: Configure Header and Footer

### Step 1: Navigate to Company Settings

**Option A: Through Settings**
1. Click **Settings** in the main menu
2. Scroll to **Companies** section
3. Click **Update Info** button

**Option B: Direct Navigation**
1. Click **Settings**
2. Go to **Users & Companies** → **Companies**
3. Click on your company name (usually the first one)

### Step 2: Find Report Header & Footer Tab

1. You should now be in the Company form view
2. Look at the tabs at the top (General Information, Contact Information, etc.)
3. Find and click on: **"Report Header & Footer"** tab

**✅ Expected View:**
```
Report Header & Footer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
☐ Use Custom Header
☐ Use Custom Footer
```

### Step 3: Enable Custom Header

1. Check the box: ☑ **Use Custom Header**
2. A new section will appear: **"Report Header Image"**
3. You'll see an image upload widget

### Step 4: Upload Header Image

1. Click on the image placeholder area
2. Click **"Upload an image"** or drag and drop
3. Select your header image file (JPG, 1024x200px recommended)
4. Wait for upload to complete
5. You should see a preview of your image

### Step 5: Enable Custom Footer

1. Check the box: ☑ **Use Custom Footer**
2. A new section will appear: **"Report Footer Image"**

### Step 6: Upload Footer Image

1. Click on the image placeholder area
2. Click **"Upload an image"** or drag and drop
3. Select your footer image file (JPG, 1024x150px recommended)
4. Wait for upload to complete
5. You should see a preview of your image

### Step 7: Save Changes

1. Click the **Save** button at the top of the form
2. Wait for confirmation message

**✅ Expected Result:**
- Both images should be visible in preview
- Both checkboxes should be checked
- Save should complete without errors

---

## Part 6: Test with PDF Reports

Now let's test if the custom header and footer appear in PDF reports.

### Test 1: Create a Sales Quotation (If Sales App Available)

**Step 1: Create a Quotation**
1. Go to **Sales** app (if installed)
2. Click **Create** button
3. Fill in:
   - Customer: Select or create a customer
   - Add a product line (any product)
4. Click **Save**

**Step 2: Generate PDF**
1. Click **Print** button (or three dots menu)
2. Select **Quotation / Order**
3. PDF should download or open

**✅ Expected Result:**
- PDF opens in new tab or downloads
- **Custom header image** appears at the top
- **Custom footer image** appears at the bottom
- Report content is between header and footer

### Test 2: Create a Invoice (If Accounting App Available)

**Step 1: Create an Invoice**
1. Go to **Accounting** app (if installed)
2. Go to **Customers** → **Invoices**
3. Click **Create**
4. Fill in:
   - Customer: Select a customer
   - Add an invoice line
5. Click **Save**

**Step 2: Generate PDF**
1. Click **Print Invoice** or **Print** button
2. PDF should generate

**✅ Expected Result:**
- Custom header at top
- Custom footer at bottom
- Invoice content in between

### Test 3: Use Any Available Report

Any report that uses Odoo's standard layout should work:
- Purchase Orders
- Delivery Orders
- Manufacturing Orders
- HR Documents
- Project Reports

---

## Part 7: Test Toggle Functionality

### Test: Disable Custom Header/Footer

**Step 1: Go Back to Company Settings**
1. Navigate to **Settings** → **Companies**
2. Select your company
3. Go to **Report Header & Footer** tab

**Step 2: Disable Custom Header**
1. Uncheck: ☐ **Use Custom Header**
2. Click **Save**

**Step 3: Generate Report Again**
1. Generate the same report as before
2. Check the PDF

**✅ Expected Result:**
- Header should now show **Odoo's default header** (company logo, address)
- Footer should still show your **custom footer image**

**Step 4: Disable Custom Footer**
1. Go back to company settings
2. Uncheck: ☐ **Use Custom Footer**
3. Click **Save**

**Step 5: Generate Report Again**
1. Generate a report
2. Check the PDF

**✅ Expected Result:**
- Both header and footer should show **Odoo's default layout**

---

## Part 8: Test Multi-Company (Optional)

If you have multiple companies configured:

### Step 1: Switch to Another Company

1. Click on company name in top right corner
2. Select another company

### Step 2: Configure Different Images

1. Go to **Settings** → **Companies**
2. Select the second company
3. Upload **different** header and footer images
4. Save

### Step 3: Test

1. Generate a report while logged in as the second company
2. Verify that the **second company's images** appear

**✅ Expected Result:**
- Each company shows its own custom images
- Images don't mix between companies

---

## Part 9: Visual Verification Checklist

When viewing a PDF report with custom header/footer enabled:

### Header Area ✅
- [ ] Custom header image is visible
- [ ] Image is full width
- [ ] Image is not cut off or distorted
- [ ] Image is clear and readable
- [ ] No Odoo default logo appears

### Footer Area ✅
- [ ] Custom footer image is visible
- [ ] Image is full width
- [ ] Image is not cut off or distorted
- [ ] Image is clear and readable
- [ ] Page numbers appear (if included in your footer image)

### Content Area ✅
- [ ] Report content is visible between header and footer
- [ ] No overlap between header and content
- [ ] No overlap between footer and content
- [ ] Content is properly formatted

---

## Part 10: Troubleshooting Common Issues

### Issue 1: Tab Not Visible

**Symptoms:**
- Can't find "Report Header & Footer" tab

**Solutions:**
1. Make sure you're in **Form view** (not list view)
2. Scroll through tabs (might be at the end)
3. Check if module is really installed (Apps menu)
4. Restart Odoo and refresh browser

### Issue 2: Images Not Appearing in PDF

**Symptoms:**
- PDF shows default Odoo header/footer
- Custom images don't appear

**Solutions:**
1. Verify checkboxes are checked (Use Custom Header/Footer)
2. Make sure you clicked **Save** after uploading
3. Clear browser cache (Ctrl+Shift+Del)
4. Regenerate the report (don't use cached version)
5. Check image format (JPG recommended)
6. Try smaller image file size

### Issue 3: Images Distorted or Cut Off

**Symptoms:**
- Images appear stretched or compressed
- Parts of image are missing

**Solutions:**
1. Use recommended dimensions:
   - Header: 1024 x 200 pixels
   - Footer: 1024 x 150 pixels
2. Maintain aspect ratio when resizing
3. Leave margins around important content
4. Test with different image editing

### Issue 4: Cannot Upload Images

**Symptoms:**
- Upload button doesn't work
- Error when uploading

**Solutions:**
1. Check file size (keep under 2MB)
2. Check file format (JPG, PNG should work)
3. Check file permissions
4. Try different browser
5. Check Odoo logs for errors

### Issue 5: Changes Not Reflected

**Symptoms:**
- Old images still appear
- Changes don't take effect

**Solutions:**
1. Hard refresh browser (Ctrl+F5)
2. Clear browser cache completely
3. Check if you saved the changes
4. Make sure you're viewing the right company
5. Restart Odoo server

---

## Part 11: Advanced Testing

### Test Different Report Types

Test with various report templates to ensure compatibility:

1. **Standard Layout**: Sales Orders, Invoices
2. **Boxed Layout**: Some reports use boxed layout
3. **Custom Reports**: If you have custom reports

### Test Different Paper Sizes

1. Change paper format in report settings
2. Test with A4 and Letter sizes
3. Verify images scale properly

### Test Print Quality

1. Actually print a report (physical printer)
2. Check if images print clearly
3. Verify colors and contrast

---

## Part 12: Performance Testing

### Test with Large Images

1. Upload large images (close to 2MB)
2. Generate report
3. Check generation time
4. Verify PDF file size

**✅ Acceptable Performance:**
- Report generation: < 5 seconds
- PDF file size: < 5MB

### Test with Multiple Reports

1. Generate 10+ reports quickly
2. Verify all show correct header/footer
3. Check for memory issues

---

## Success Criteria ✅

Your testing is successful if:

- [ ] Module appears as installed in Apps
- [ ] "Report Header & Footer" tab is visible in Company form
- [ ] Images upload successfully
- [ ] Preview shows uploaded images
- [ ] PDF reports show custom header when enabled
- [ ] PDF reports show custom footer when enabled
- [ ] Toggle switches work (enable/disable)
- [ ] Default layout appears when custom disabled
- [ ] Multiple companies can have different images (if applicable)
- [ ] No errors in Odoo logs
- [ ] Reports generate within reasonable time
- [ ] Images are clear and not distorted

---

## Test Report Template

Use this template to document your testing:

```
TESTING REPORT - Company Header Footer Module
=============================================

Date: ___________
Tester: ___________
Odoo Version: 19.0
Module Version: 19.0.1.0.0

Installation:
[ ] Module installed successfully
[ ] No errors during installation

Configuration:
[ ] Tab visible in company form
[ ] Header image uploaded
[ ] Footer image uploaded
[ ] Changes saved

PDF Generation:
[ ] Sales Order tested
[ ] Invoice tested
[ ] Other reports tested: ___________

Visual Quality:
[ ] Header appears correctly
[ ] Footer appears correctly
[ ] Images are clear
[ ] No distortion

Toggle Testing:
[ ] Disable header works
[ ] Disable footer works
[ ] Re-enable works

Issues Found:
1. ___________
2. ___________

Overall Result: [ ] PASS  [ ] FAIL

Notes:
___________________________________________
___________________________________________
```

---

## Need Help?

**Check Logs:**
```bash
# View Odoo logs
tail -f /var/log/odoo/odoo.log

# Or check terminal output where Odoo is running
```

**Enable Debug Mode:**
1. Settings → Activate developer mode
2. Helps see more detailed errors

**Documentation:**
- See README.md for detailed information
- See TROUBLESHOOTING section in README.md
- See INSTALLATION_LOG.md for installation details

---

**Happy Testing! 🧪✅**

