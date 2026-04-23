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
