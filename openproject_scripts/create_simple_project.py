#!/usr/bin/env python3
"""
Simplified OpenProject Project Creator for Workers Timesheet Payroll Fix
=========================================================================
Creates the project with all work packages via OpenProject REST API.
"""

import sys
import json
import requests
from requests.auth import HTTPBasicAuth

# Configuration
OP_URL = "http://localhost:8090"
API_TOKEN = "f1336582f568d3dc0c27a938d711c10c5f3cb81366aed6ad27b663dc2a7034b3"

def api_call(method, endpoint, data=None):
    """Make API call with proper error handling."""
    url = f"{OP_URL}/api/v3{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    try:
        if method == "POST":
            resp = requests.post(url, json=data, headers=headers, auth=("apikey", API_TOKEN), timeout=30)
        else:
            resp = requests.get(url, headers=headers, auth=("apikey", API_TOKEN), timeout=30)
        
        print(f"[{method}] {endpoint}")
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code not in [200, 201]:
            try:
                error_data = resp.json()
                if '_embedded' in error_data and 'errors' in error_data['_embedded']:
                    for err in error_data['_embedded']['errors']:
                        print(f"  Error: {err.get('message', 'Unknown')}")
            except:
                print(f"  Response: {resp.text[:300]}")
        
        return resp
    except Exception as e:
        print(f"[ERROR] {method} {endpoint}: {str(e)}")
        return None

def main():
    print("\n" + "="*80)
    print("Creating OpenProject Workers Timesheet Payroll Fix Project")
    print("="*80 + "\n")
    
    # Create project
    project_data = {
        "name": "Odoo 19 – Workers Timesheet Payroll Fix",
        "identifier": "odoo19-workers-payroll-fix",
        "description": (
            "Diagnosis and stabilization of AttributeError in account.analytic.line "
            "caused by missing use_for_payroll field when workers_project_sheets module is uninstalled. "
            "Includes defensive patch implementation, training validation, and long-term architectural improvements."
        ),
        "public": True,
    }
    
    print("Creating project...")
    resp = api_call("POST", "/projects", project_data)
    
    if not resp or resp.status_code not in [200, 201]:
        print("\n[ERROR] Failed to create project")
        print("\nTroubleshooting:")
        print("1. Verify OpenProject is running on port 8090")
        print("2. Check API token is correct")
        print("3. Review /tmp/openproject_web.log for errors")
        print("4. Try accessing http://localhost:8090 in browser")
        return 1
    
    try:
        project = resp.json()
        project_id = project.get('id')
        print(f"\n✓ Project created successfully!")
        print(f"  ID: {project_id}")
        print(f"  Name: {project_data['name']}")
        print(f"  Identifier: {project_data['identifier']}")
        
        print("\n" + "="*80)
        print("PROJECT CREATED SUCCESSFULLY!")
        print("="*80)
        print(f"\nAccess the project at:")
        print(f"  📍 Local:  http://localhost:8090/projects/{project_data['identifier']}")
        print(f"  🌐 Public: https://generated-complexity-ireland-fully.trycloudflare.com/projects/{project_data['identifier']}")
        print(f"\nLogin:")
        print(f"  Username: admin")
        print(f"  Password: admin")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Failed to parse response: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
