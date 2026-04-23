#!/usr/bin/env python3
"""
Simple log reader to show OpenProject HTTPS errors
This doesn't require sudo - just reads what we can access
"""

import os
import glob

def check_readable_logs():
    """Check for readable OpenProject logs"""
    print("="*60)
    print("Searching for readable OpenProject logs...")
    print("="*60)
    
    possible_log_locations = [
        "/var/log/openproject/*.log",
        "/home/*/openproject/log/*.log",
        "/opt/openproject/log/*.log",
        "~/openproject/log/*.log",
    ]
    
    found_logs = []
    for pattern in possible_log_locations:
        expanded = os.path.expanduser(pattern)
        matches = glob.glob(expanded)
        for log_file in matches:
            if os.access(log_file, os.R_OK):
                found_logs.append(log_file)
    
    if found_logs:
        print(f"\nFound {len(found_logs)} readable log files:")
        for log in found_logs:
            print(f"  - {log}")
            print(f"    Size: {os.path.getsize(log)} bytes")
            print()
    else:
        print("\nNo readable OpenProject logs found in standard locations")
    
    return found_logs

def search_for_https_errors(log_file, num_lines=100):
    """Search for HTTPS-related errors in log file"""
    print(f"\nSearching {log_file} for HTTPS errors...")
    print("-"*60)
    
    try:
        with open(log_file, 'r', errors='ignore') as f:
            lines = f.readlines()
            
        # Get last N lines
        recent_lines = lines[-num_lines:]
        
        # Search for HTTPS-related content
        https_related = []
        for i, line in enumerate(recent_lines):
            if any(keyword in line.lower() for keyword in ['https', 'ssl', 'tls', 'certificate', 'mode']):
                https_related.append((i, line.strip()))
        
        if https_related:
            print(f"Found {len(https_related)} lines mentioning HTTPS/SSL/TLS:")
            for line_num, content in https_related[-20:]:  # Show last 20 matches
                print(f"  [{line_num}] {content}")
        else:
            print("No HTTPS-related entries found in last 100 lines")
            print("\nShowing last 10 lines of log:")
            for line in recent_lines[-10:]:
                print(f"  {line.strip()}")
                
    except Exception as e:
        print(f"Error reading {log_file}: {e}")

def main():
    print("\n" + "="*60)
    print("OpenProject HTTPS Error Diagnostic (No Sudo Required)")
    print("="*60 + "\n")
    
    # Check readable logs
    logs = check_readable_logs()
    
    # Search each log for HTTPS errors
    for log_file in logs:
        search_for_https_errors(log_file)
        print()
    
    print("\n" + "="*60)
    print("To apply the fix, you need to run as sudo:")
    print("  sudo openproject config:set OPENPROJECT_HTTPS=true")
    print("  sudo openproject restart web")
    print("="*60)

if __name__ == "__main__":
    main()
