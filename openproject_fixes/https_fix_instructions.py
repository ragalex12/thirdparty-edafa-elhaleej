#!/usr/bin/env python3
"""
Manual HTTPS Fix Instructions and Log Checker
Since we're experiencing terminal issues, this provides clear manual steps
"""

import os
import glob
from datetime import datetime

print("="*70)
print("OpenProject HTTPS Configuration Fix - Manual Instructions")
print("="*70)
print()

# Check if we can read any logs
print("### Checking for readable OpenProject logs ###")
print()

log_patterns = [
    "/var/log/openproject/*.log",
    "/home/*/openproject/log/*.log", 
    "/opt/openproject/log/*.log",
]

found_logs = []
for pattern in log_patterns:
    for log_file in glob.glob(pattern):
        if os.path.exists(log_file) and os.access(log_file, os.R_OK):
            found_logs.append(log_file)
            size = os.path.getsize(log_file)
            print(f"✓ Found: {log_file} ({size:,} bytes)")

if not found_logs:
    print("⚠️  No readable OpenProject logs found")
    print("   (This is normal if you don't have read permissions)")
print()

# Try to read recent log entries
if found_logs:
    print("### Checking for HTTPS-related errors in logs ###")
    print()
    for log_file in found_logs[:2]:  # Check first 2 logs only
        try:
            with open(log_file, 'r', errors='ignore') as f:
                lines = f.readlines()
                recent = lines[-100:] if len(lines) > 100 else lines
                
                https_errors = [line.strip() for line in recent 
                               if any(keyword in line.lower() 
                                     for keyword in ['https', 'mode', 'mismatch', 'ssl'])]
                
                if https_errors:
                    print(f"Found HTTPS-related entries in {os.path.basename(log_file)}:")
                    for error in https_errors[-10:]:  # Show last 10
                        print(f"  {error[:150]}")  # Truncate long lines
                    print()
        except Exception as e:
            print(f"Could not read {log_file}: {e}")
print()

print("="*70)
print("MANUAL FIX INSTRUCTIONS (run these commands in your terminal):")
print("="*70)
print()
print("1. Set HTTPS mode to true:")
print("   sudo openproject config:set OPENPROJECT_HTTPS=\"true\"")
print()
print("2. Update the configuration file:")
print("   echo 'OPENPROJECT_HTTPS=\"true\"' | sudo tee /etc/openproject/conf.d/https")
print()
print("3. Restart the web service:")
print("   sudo openproject restart web")
print()
print("4. Wait 15 seconds for restart:")
print("   sleep 15")
print()
print("5. Verify the fix:")
print("   sudo openproject config:get OPENPROJECT_HTTPS")
print("   (Should return: true)")
print()

print("="*70)
print("WHERE IS THE PDF EXPORT IN OPENPROJECT?")
print("="*70)
print()
print("After applying the fix above, access OpenProject and export PDFs:")
print()
print("📍 Your OpenProject URL:")
print("   https://generated-complexity-ireland-fully.trycloudflare.com")
print()
print("📍 Your Project URL:")
print("   https://generated-complexity-ireland-fully.trycloudflare.com/projects/odoo19-hr-security-fix")
print()
print("📋 Steps to export work packages as PDF:")
print()
print("   1. Open the project URL above in your browser")
print()
print("   2. Click 'Work packages' in the left sidebar menu")
print()
print("   3. IMPORTANT: By default, closed work packages are hidden!")
print("      → Click the filter/settings icon (funnel or gear icon)")
print("      → Find 'Status' filter")
print("      → Enable 'Show closed' or select 'All statuses'")
print("      → Click 'Apply' or 'Save'")
print()
print("   4. You should now see all 32 work packages:")
print("      • 5 Phases (Phase 1-5)")
print("      • 27 Tasks grouped under those phases")
print()
print("   5. To export as PDF:")
print("      → Option A: Export all work packages")
print("         • Click the '...' (three dots) or 'Settings' menu in top right")
print("         • Select 'Export' → 'PDF' or 'Export to PDF'")
print("         • Choose format options if prompted")
print("         • Click 'Download' or 'Export'")
print()
print("      → Option B: Export a single work package")
print("         • Click on any work package title to open it")
print("         • Look for 'Export', 'Print', or '...' menu")
print("         • Select 'PDF' or 'Print to PDF'")
print()
print("   6. The PDF will download to your browser's download folder")
print("      (Usually ~/Downloads or C:\\Users\\YourName\\Downloads)")
print()

print("="*70)
print("WHY YOU COULDN'T EXPORT BEFORE:")
print("="*70)
print()
print("The error was: 'HTTPS mode setup mismatch'")
print()
print("Root cause:")
print("  • Your Cloudflare tunnel uses HTTPS (https://...trycloudflare.com)")
print("  • But OpenProject was configured with OPENPROJECT_HTTPS=\"false\"")
print("  • This caused OpenProject to reject HTTPS requests")
print()
print("The fix:")
print("  • Set OPENPROJECT_HTTPS=\"true\"")
print("  • Restart the web service")
print("  • Now OpenProject accepts HTTPS requests from Cloudflare")
print()

print("="*70)
print("NEED MORE HELP?")
print("="*70)
print()
print("If you still can't see work packages or export PDF:")
print()
print("1. Verify HTTPS is set to true:")
print("   sudo openproject config:get OPENPROJECT_HTTPS")
print()
print("2. Check if web service is running:")
print("   ps aux | grep puma")
print()
print("3. Check production log for errors:")
print("   sudo tail -f /var/log/openproject/production.log")
print()
print("4. If work packages don't appear:")
print("   • Make sure you cleared the 'Status' filter in work packages view")
print("   • Try clicking 'Advanced filters' and removing all filters")
print("   • Refresh the page (F5 or Ctrl+R)")
print()

print("="*70)
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(f"Generated: {current_time}")
print("="*70)
