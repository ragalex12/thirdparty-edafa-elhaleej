#!/bin/bash
################################################################################
# OpenProject Workers Timesheet Payroll Project Creator
# Starts OpenProject service and creates the project with all work packages
################################################################################

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  OpenProject Workers Timesheet Payroll Project Creator"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
OPENPROJECT_PORT=8090
API_TIMEOUT=30
CREATE_SCRIPT="/opt/localaddons/openproject_scripts/create_workers_timesheet_payroll_project.py"

# ─── Function: Check if OpenProject is running ───────────────────────────────
check_openproject() {
    echo -n "Checking OpenProject service on port $OPENPROJECT_PORT... "
    if timeout 3 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/$OPENPROJECT_PORT" 2>/dev/null; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not running${NC}"
        return 1
    fi
}

# ─── Function: Start OpenProject ─────────────────────────────────────────────
start_openproject() {
    echo -e "${YELLOW}⚠${NC} Starting OpenProject Puma web service..."
    echo "  Command: openproject run web"
    
    # Try to start OpenProject
    if command -v openproject &> /dev/null; then
        nohup openproject run web > /tmp/openproject_web.log 2>&1 &
        OP_PID=$!
        echo -e "  PID: $OP_PID"
        
        # Wait for service to start
        echo -n "  Waiting for service to start (max 60 seconds)... "
        for i in {1..60}; do
            if check_openproject > /dev/null 2>&1; then
                echo -e "${GREEN}ready!${NC}"
                return 0
            fi
            sleep 1
            printf "."
        done
        echo -e "${RED}timeout${NC}"
        echo -e "${RED}✗${NC} OpenProject failed to start in time"
        echo "  Check logs: tail -f /tmp/openproject_web.log"
        return 1
    else
        echo -e "${RED}✗${NC} openproject command not found"
        echo "  Please install OpenProject or start it manually:"
        echo "    openproject run web"
        return 1
    fi
}

# ─── Function: Create project ────────────────────────────────────────────────
create_project() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}Creating OpenProject Project${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    if [ -f "$CREATE_SCRIPT" ]; then
        python3 "$CREATE_SCRIPT"
        RESULT=$?
        
        if [ $RESULT -eq 0 ]; then
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo -e "${GREEN}✓ Project created successfully!${NC}"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            echo -e "${GREEN}Access the project:${NC}"
            echo "  📍 Public URL: https://generated-complexity-ireland-fully.trycloudflare.com/projects/odoo19-workers-payroll-fix"
            echo "  🔗 Local URL:  http://127.0.0.1:$OPENPROJECT_PORT/projects/odoo19-workers-payroll-fix"
            echo ""
            echo -e "${YELLOW}Default credentials:${NC}"
            echo "  Username: admin"
            echo "  Password: admin"
            echo ""
            return 0
        else
            echo -e "${RED}✗${NC} Project creation failed (exit code: $RESULT)"
            return 1
        fi
    else
        echo -e "${RED}✗${NC} Script not found: $CREATE_SCRIPT"
        return 1
    fi
}

# ─── Main execution ──────────────────────────────────────────────────────────

# Check if OpenProject is running
if ! check_openproject; then
    # Try to start it
    if ! start_openproject; then
        exit 1
    fi
fi

# Give a moment for full service startup
sleep 2

# Create the project
if create_project; then
    exit 0
else
    exit 1
fi
