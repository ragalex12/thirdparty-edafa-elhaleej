#!/bin/bash
################################################################################
# Temporary Files Cleanup Script
# Removes temporary log files and outputs from /tmp
################################################################################

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Temporary Files Cleanup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# List of temporary files to clean up
TEMP_FILES=(
    "/tmp/simple_create_output.txt"
    "/tmp/full_creation_output.txt"
    "/tmp/https_fix_output.txt"
    "/tmp/pdf_conversion.log"
    "/tmp/work_packages.html"
    "/tmp/openproject_web.log"
    "/tmp/openproject_web_final.log"
    "/tmp/HTTPS_FIX_GUIDE.txt"
    "/tmp/cloudflared.log"
)

echo "Checking for temporary files to remove..."
echo ""

REMOVED_COUNT=0
TOTAL_SIZE=0

for file in "${TEMP_FILES[@]}"; do
    if [ -f "$file" ]; then
        SIZE=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
        TOTAL_SIZE=$((TOTAL_SIZE + SIZE))
        rm -f "$file"
        echo -e "  ${GREEN}✓${NC} Removed: $file ($(numfmt --to=iec-i --suffix=B $SIZE 2>/dev/null || echo ${SIZE}B))"
        REMOVED_COUNT=$((REMOVED_COUNT + 1))
    fi
done

if [ $REMOVED_COUNT -eq 0 ]; then
    echo -e "  ${YELLOW}ℹ${NC} No temporary files found to remove"
else
    echo ""
    echo -e "${GREEN}✓${NC} Removed $REMOVED_COUNT file(s)"
    if command -v numfmt &> /dev/null; then
        echo -e "${GREEN}✓${NC} Freed space: $(numfmt --to=iec-i --suffix=B $TOTAL_SIZE)"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Cleanup complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
