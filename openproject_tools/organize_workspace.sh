#!/bin/bash
################################################################################
# Workspace Organization Script
# Organizes OpenProject and HR Security Fix related files into folders
################################################################################

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Workspace Organization Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Base directory
WORKSPACE="/opt/localaddons"
cd "$WORKSPACE" || exit 1

# Create organization folders
echo -e "${BLUE}Creating organization folders...${NC}"
mkdir -p openproject_scripts
mkdir -p openproject_docs
mkdir -p openproject_fixes
mkdir -p openproject_outputs
mkdir -p openproject_tools
mkdir -p archived_scripts

echo -e "${GREEN}✓${NC} Created directories:"
echo "  - openproject_scripts/ (Python scripts for OpenProject API)"
echo "  - openproject_docs/ (Documentation files)"
echo "  - openproject_fixes/ (Fix and diagnostic scripts)"
echo "  - openproject_outputs/ (Generated check results and status files)"
echo "  - openproject_tools/ (Root helper shell scripts and aliases)"
echo "  - archived_scripts/ (Old/temporary scripts)"
echo ""

# Move OpenProject Python scripts
echo -e "${BLUE}Organizing OpenProject Python scripts...${NC}"
for script in create_hr_security_project.py simple_create_openproject.py \
              run_openproject_setup.py close_completed_tasks.py \
              close_all_remaining.py verify_openproject_descriptions.py \
              show_task_descriptions.py check_all_workpackages.py \
              final_verification.py direct_project_check.py \
              check_openproject_logs.py convert_to_pdf.py \
              create_openproject.py test_openproject_connection.py \
              run_check_wps.py run_close_tasks.py run_direct_check.py \
              run_final_close.py run_final_verification.py \
              run_full_openproject_creation.py run_show_descriptions.py; do
    if [ -f "$script" ]; then
        mv "$script" openproject_scripts/
        echo -e "  ${GREEN}✓${NC} Moved $script"
    fi
done
echo ""

# Move documentation files
echo -e "${BLUE}Organizing documentation files...${NC}"
for doc in HR_SECURITY_PROJECT_DOCUMENTATION.md WORK_PACKAGES_REFERENCE.md \
           OPENPROJECT_SETUP_GUIDE.md WHATSAPP_MESSAGE_AR.txt \
           WHATSAPP_MESSAGE_SHORT_AR.txt WHATSAPP_MESSAGE_BRIEF_AR.txt; do
    if [ -f "$doc" ]; then
        mv "$doc" openproject_docs/
        echo -e "  ${GREEN}✓${NC} Moved $doc"
    fi
done
echo ""

# Move fix and diagnostic scripts
echo -e "${BLUE}Organizing fix scripts...${NC}"
for fix_script in fix_openproject_https.sh simple_https_fix.sh \
                  complete_https_fix.sh fix_and_verify_https.py \
                  https_fix_instructions.py restart_openproject_web.sh \
                  fix_https_config_files.sh fix_all.sh quick_fix.sh \
                  final_fix.sh get_tunnel_url.sh; do
    if [ -f "$fix_script" ]; then
        mv "$fix_script" openproject_fixes/
        echo -e "  ${GREEN}✓${NC} Moved $fix_script"
    fi
done
echo ""

# Move generated outputs and status files
echo -e "${BLUE}Organizing generated output files...${NC}"
for output_file in closing_tasks_result.txt direct_check_result.txt \
                   final_closing_result.txt final_verification_result.txt \
                   https_fix_output.txt openproject_created.txt \
                   openproject_final_result.txt openproject_setup_complete.txt \
                   task_descriptions_check.txt workpackages_status.txt; do
    if [ -f "$output_file" ]; then
        mv "$output_file" openproject_outputs/
        echo -e "  ${GREEN}✓${NC} Moved $output_file"
    fi
done
echo ""

# Keep main launcher in root
echo -e "${BLUE}Main launcher...${NC}"
if [ -f "open_openproject.sh" ]; then
    echo -e "  ${GREEN}✓${NC} Keeping open_openproject.sh in workspace root for easy access"
fi
echo ""

# Create README in each folder
echo -e "${BLUE}Creating README files...${NC}"

cat > openproject_scripts/README.md << 'EOF'
# OpenProject Python Scripts

This folder contains Python scripts for interacting with the OpenProject API.

## Key Scripts:

- **create_hr_security_project.py** - Main project creation script (783 lines)
- **close_completed_tasks.py** - First batch work package closure
- **close_all_remaining.py** - Second batch work package closure
- **verify_openproject_descriptions.py** - Description verification
- **check_all_workpackages.py** - Status checker
- **convert_to_pdf.py** - Markdown to PDF converter

## Usage:
```bash
python3 create_hr_security_project.py
```

## Configuration:
- API Token: f1336582f568...
- Port: 8090
- Host Header: generated-complexity-ireland-fully.trycloudflare.com
EOF

cat > openproject_docs/README.md << 'EOF'
# OpenProject Documentation

This folder contains all documentation related to the HR Security Fix project.

## Documents:

- **HR_SECURITY_PROJECT_DOCUMENTATION.md** - Complete 783-line technical documentation
- **WORK_PACKAGES_REFERENCE.md** - Reference document with all 32 work packages
- **OPENPROJECT_SETUP_GUIDE.md** - Setup instructions
- **WHATSAPP_MESSAGE_*.txt** - Arabic communication templates (3 variants)

## OpenProject Access:
- URL: https://generated-complexity-ireland-fully.trycloudflare.com
- Project: odoo19-hr-security-fix
- Login: admin / admin
EOF

cat > openproject_fixes/README.md << 'EOF'
# OpenProject Fixes & Diagnostics

This folder contains scripts used to diagnose and fix OpenProject configuration issues.

## HTTPS Configuration Fix:

The main issue resolved was HTTPS mode mismatch preventing PDF export.

**Solution applied:**
```bash
sed -i '/^OPENPROJECT_HTTPS/d' /etc/openproject/conf.d/server
echo 'OPENPROJECT_HTTPS=true' >> /etc/openproject/conf.d/server
```

## Scripts:
- Various diagnostic and fix scripts for HTTPS configuration
- Service restart scripts
- Log checking utilities
EOF

cat > openproject_outputs/README.md << 'EOF'
# OpenProject Outputs

This folder contains generated status files, verification outputs, and one-off run results.

## Typical Contents:

- Work package closure results
- Verification summaries
- HTTPS fix output logs
- OpenProject setup status files

These files are safe to archive or delete after review.
EOF

echo -e "  ${GREEN}✓${NC} Created README.md in openproject_scripts/"
echo -e "  ${GREEN}✓${NC} Created README.md in openproject_docs/"
echo -e "  ${GREEN}✓${NC} Created README.md in openproject_fixes/"
echo -e "  ${GREEN}✓${NC} Created README.md in openproject_outputs/"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Workspace organization complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Directory structure:"
echo "  /opt/localaddons/"
echo "  ├── open_openproject.sh          ← Quick launcher (run this!)"
echo "  ├── openproject_scripts/          ← Python API scripts"
echo "  ├── openproject_docs/             ← All documentation"
echo "  ├── openproject_fixes/            ← Fix & diagnostic scripts"
echo "  ├── openproject_outputs/          ← Generated outputs and status files"
echo "  ├── openproject_tools/            ← Root helper scripts and aliases"
echo "  └── archived_scripts/             ← Old scripts (if any)"
echo ""
echo "To open OpenProject quickly, run:"
echo -e "  ${YELLOW}bash open_openproject.sh${NC}"
echo ""
