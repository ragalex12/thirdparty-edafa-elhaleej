#!/usr/bin/env python3
"""
OpenProject HTTPS Configuration Fix and Verification
This script checks and fixes the HTTPS mode mismatch issue
"""

import subprocess
import os
from datetime import datetime

LOG_FILE = "/tmp/openproject_https_diagnostic.txt"

def log(message):
    """Write message to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    with open(LOG_FILE, 'a') as f:
        f.write(full_message + "\n")

def run_command(cmd, description):
    """Run a command and log the results"""
    log(f"\n{'='*60}")
    log(f"RUNNING: {description}")
    log(f"COMMAND: {cmd}")
    log(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        log(f"Exit Code: {result.returncode}")
        
        if result.stdout:
            log(f"STDOUT:\n{result.stdout}")
        
        if result.stderr:
            log(f"STDERR:\n{result.stderr}")
        
        return result
    except subprocess.TimeoutExpired:
        log("ERROR: Command timed out after 60 seconds")
        return None
    except Exception as e:
        log(f"ERROR: {str(e)}")
        return None

def main():
    # Clear previous log
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    
    log("OpenProject HTTPS Configuration Diagnostic Tool")
    log("="*60)
    
    # Step 1: Check current HTTPS configuration
    log("\n### STEP 1: Check Current HTTPS Configuration ###")
    result = run_command(
        "sudo openproject config:get OPENPROJECT_HTTPS",
        "Get current OPENPROJECT_HTTPS setting"
    )
    
    current_https_value = None
    if result and result.returncode == 0:
        current_https_value = result.stdout.strip()
        log(f"Current OPENPROJECT_HTTPS value: '{current_https_value}'")
    
    # Step 2: Check configuration file
    log("\n### STEP 2: Check Configuration File ###")
    run_command(
        "cat /etc/openproject/conf.d/https 2>&1 || echo 'File does not exist yet'",
        "Read HTTPS configuration file"
    )
    
    # Step 3: Check for recent errors in logs
    log("\n### STEP 3: Check Recent OpenProject Logs ###")
    run_command(
        "sudo tail -n 50 /var/log/openproject/production.log 2>&1 || echo 'Log file not found'",
        "Read last 50 lines of production log"
    )
    
    # Step 4: Apply fix if needed
    if current_https_value != "true":
        log("\n### STEP 4: Applying HTTPS Configuration Fix ###")
        log("HTTPS is not set to 'true', applying fix...")
        
        # Set via config command
        run_command(
            "sudo openproject config:set OPENPROJECT_HTTPS=true",
            "Set OPENPROJECT_HTTPS to true"
        )
        
        # Create/update the conf file
        run_command(
            "echo 'OPENPROJECT_HTTPS=true' | sudo tee /etc/openproject/conf.d/https",
            "Create/update HTTPS configuration file"
        )
        
        # Restart web service
        log("\nRestarting OpenProject web service...")
        run_command(
            "sudo openproject restart web",
            "Restart OpenProject web service"
        )
        
        log("\nWaiting 15 seconds for service to restart...")
        import time
        time.sleep(15)
        
        # Verify the fix
        log("\n### STEP 5: Verify Configuration After Fix ###")
        result = run_command(
            "sudo openproject config:get OPENPROJECT_HTTPS",
            "Verify OPENPROJECT_HTTPS is now true"
        )
        
        if result and result.returncode == 0:
            new_value = result.stdout.strip()
            if new_value == "true":
                log("\n✅ SUCCESS! HTTPS configuration is now set to 'true'")
            else:
                log(f"\n⚠️ WARNING: Expected 'true' but got '{new_value}'")
    else:
        log("\n✅ HTTPS is already set to 'true' - no fix needed")
    
    # Step 6: Check service status
    log("\n### STEP 6: Check OpenProject Service Status ###")
    run_command(
        "sudo systemctl status openproject-web-1 2>&1 | head -n 20 || echo 'Service status unavailable'",
        "Check OpenProject web service status"
    )
    
    log("\n" + "="*60)
    log("DIAGNOSTIC COMPLETE")
    log(f"Full log saved to: {LOG_FILE}")
    log("="*60)
    
    print(f"\n\nFull diagnostic log saved to: {LOG_FILE}")
    print("You can view it with: cat /tmp/openproject_https_diagnostic.txt")

if __name__ == "__main__":
    main()
