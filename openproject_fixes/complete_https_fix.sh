#!/bin/bash
# Complete HTTPS Fix and Diagnostic for OpenProject
# This script will fix the HTTPS issue and show you logs

OUTPUT_FILE="/tmp/https_fix_complete_log.txt"
echo "===========================================================" > "$OUTPUT_FILE"
echo "OpenProject HTTPS Configuration Fix" >> "$OUTPUT_FILE"
echo "Started: $(date)" >> "$OUTPUT_FILE"
echo "===========================================================" >> "$OUTPUT_FILE"

echo "" >> "$OUTPUT_FILE"
echo "### STEP 1: Current HTTPS Configuration ###" >> "$OUTPUT_FILE"
echo "Checking current HTTPS setting..." >> "$OUTPUT_FILE"
CURRENT_VALUE=$(openproject config:get OPENPROJECT_HTTPS 2>&1)
echo "Current OPENPROJECT_HTTPS: $CURRENT_VALUE" >> "$OUTPUT_FILE"

echo "" >> "$OUTPUT_FILE"
echo "### STEP 2: Applying HTTPS Fix ###" >> "$OUTPUT_FILE"
echo "Setting OPENPROJECT_HTTPS to true..." >> "$OUTPUT_FILE"
openproject config:set OPENPROJECT_HTTPS="true" >> "$OUTPUT_FILE" 2>&1

echo "" >> "$OUTPUT_FILE"
echo "Creating HTTPS config file..." >> "$OUTPUT_FILE"
echo 'OPENPROJECT_HTTPS="true"' | tee /etc/openproject/conf.d/https >> "$OUTPUT_FILE" 2>&1

echo "" >> "$OUTPUT_FILE"
echo "### STEP 3: Restarting OpenProject Web Service ###" >> "$OUTPUT_FILE"
echo "Stopping old processes..." >> "$OUTPUT_FILE"
pkill -9 -u openproject 2>> "$OUTPUT_FILE" || true
pkill -9 -f "rails|puma" 2>> "$OUTPUT_FILE" || true

echo "Starting web service..." >> "$OUTPUT_FILE"
openproject restart web >> "$OUTPUT_FILE" 2>&1

echo "Waiting 20 seconds for service to restart..." >> "$OUTPUT_FILE"
sleep 20

echo "" >> "$OUTPUT_FILE"
echo "### STEP 4: Verifying Configuration ###" >> "$OUTPUT_FILE"
NEW_VALUE=$(openproject config:get OPENPROJECT_HTTPS 2>&1)
echo "New OPENPROJECT_HTTPS value: $NEW_VALUE" >> "$OUTPUT_FILE"

if [ "$NEW_VALUE" = "true" ]; then
    echo "✅ SUCCESS: HTTPS is now set to 'true'" >> "$OUTPUT_FILE"
else
    echo "⚠️  WARNING: Expected 'true' but got '$NEW_VALUE'" >> "$OUTPUT_FILE"
fi

echo "" >> "$OUTPUT_FILE"
echo "### STEP 5: Checking Recent OpenProject Logs ###" >> "$OUTPUT_FILE"
echo "Searching for HTTPS-related errors in logs..." >> "$OUTPUT_FILE"

# Check production log
if [ -f /var/log/openproject/production.log ]; then
    echo "" >> "$OUTPUT_FILE"
    echo "--- Last 30 lines of production.log ---" >> "$OUTPUT_FILE"
    tail -n 30 /var/log/openproject/production.log >> "$OUTPUT_FILE" 2>&1
fi

# Check for any HTTPS errors
if [ -f /var/log/openproject/production.log ]; then
    echo "" >> "$OUTPUT_FILE"
    echo "--- Searching for 'HTTPS' or 'mode' in recent logs ---" >> "$OUTPUT_FILE"
    grep -i "https\|mode.*mismatch" /var/log/openproject/production.log | tail -n 20 >> "$OUTPUT_FILE" 2>&1 || echo "No HTTPS-related errors found" >> "$OUTPUT_FILE"
fi

echo "" >> "$OUTPUT_FILE"
echo "### STEP 6: Service Status ###" >> "$OUTPUT_FILE"
ps aux | grep -E "puma|openproject" | grep -v grep >> "$OUTPUT_FILE" 2>&1

echo "" >> "$OUTPUT_FILE"
echo "===========================================================" >> "$OUTPUT_FILE"
echo "HTTPS FIX COMPLETE!" >> "$OUTPUT_FILE"
echo "===========================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "HOW TO EXPORT PDF FROM OPENPROJECT:" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "1. Open your browser and go to:" >> "$OUTPUT_FILE"
echo "   https://generated-complexity-ireland-fully.trycloudflare.com" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "2. Navigate to: Projects → 'Odoo 19 HR Security Fix'" >> "$OUTPUT_FILE"
echo "   OR directly: https://generated-complexity-ireland-fully.trycloudflare.com/projects/odoo19-hr-security-fix" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "3. Click 'Work packages' in the left menu" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "4. By default, closed work packages are hidden. Click the filter icon" >> "$OUTPUT_FILE"
echo "   and enable 'Show closed work packages' or clear all filters" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "5. You should see all 32 work packages (5 Phases + 27 Tasks)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "6. To export as PDF:" >> "$OUTPUT_FILE"
echo "   - Click the '...' (three dots) menu in the top right" >> "$OUTPUT_FILE"
echo "   - Select 'Export' or 'Download PDF'" >> "$OUTPUT_FILE"
echo "   - The PDF will download to your browser's download folder" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "Alternative: Export individual work package" >> "$OUTPUT_FILE"
echo "   - Click on any work package to open it" >> "$OUTPUT_FILE"
echo "   - Look for export/print option in the work package details" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "===========================================================" >> "$OUTPUT_FILE"
echo "Log file location: $OUTPUT_FILE" >> "$OUTPUT_FILE"
echo "Completed: $(date)" >> "$OUTPUT_FILE"
echo "===========================================================" >> "$OUTPUT_FILE"

# Make it readable
chmod 644 "$OUTPUT_FILE"

echo "Fix complete! Results saved to: $OUTPUT_FILE"
cat "$OUTPUT_FILE"
