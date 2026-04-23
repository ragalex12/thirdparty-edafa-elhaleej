#!/usr/bin/env python3
"""
Simplified OpenProject Creator - Creates HR Security Enhancement Project
Uses direct API calls with minimal error handling to bypass issues
"""
import sys
import json
import requests
from requests.auth import HTTPBasicAuth

# Try both ports
for PORT in [8090, 8088]:
    OP_URL = f"http://127.0.0.1:{PORT}"
    API_TOKEN = "f1336582f568d3dc0c27a938d711c10c5f3cb81366aed6ad27b663dc2a7034b3"
    
    # Try different host headers
    for host_header in [None, f"localhost:{PORT}", "generated-complexity-ireland-fully.trycloudflare.com"]:
        print(f"\n{'='*70}")
        print(f"Testing: {OP_URL} with Host: {host_header}")
        print('='*70)
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if host_header:
            headers["Host"] = host_header
        
        try:
            # Test connection
            resp = requests.get(
                f"{OP_URL}/api/v3/projects",
                auth=HTTPBasicAuth("apikey", API_TOKEN),
                headers=headers,
                timeout=5
            )
            
            if resp.ok:
                print(f"✓ CONNECTION SUCCESS!")
                print(f"  Found {len(resp.json().get('_embedded', {}).get('elements', []))} projects")
                
                # Now create the project
                print(f"\n→ Creating 'Odoo 19 HR Security Enhancement' project...")
                
                project_data = {
                    "name": "Odoo 19 – HR Employee Security Enhancement",
                    "identifier": "odoo19-hr-security-fix",
                    "description": {
                        "format": "markdown",
                        "raw": "Complete debugging and security refactoring of hr_employee_enhance module"
                    },
                    "public": False,
                }
                
                create_resp = requests.post(
                    f"{OP_URL}/api/v3/projects",
                    auth=HTTPBasicAuth("apikey", API_TOKEN),
                    headers=headers,
                    data=json.dumps(project_data),
                    timeout=30,
                )
                
                if create_resp.ok:
                    project = create_resp.json()
                    project_id = project["id"]
                    print(f"✓ PROJECT CREATED! ID: {project_id}")
                    print(f"\nAccess it at:")
                    print(f"  https://generated-complexity-ireland-fully.trycloudflare.com/projects/odoo19-hr-security-fix")
                    
                    # Save success
                    with open('/opt/localaddons/openproject_created.txt', 'w') as f:
                        f.write(f"SUCCESS\n")
                        f.write(f"Project ID: {project_id}\n")
                        f.write(f"URL: https://generated-complexity-ireland-fully.trycloudflare.com/projects/odoo19-hr-security-fix\n")
                        f.write(f"Port: {PORT}\n")
                        f.write(f"Host header: {host_header}\n")
                    
                    print(f"\nNOTE: Project created successfully.")
                    print(f"Work packages must be created manually or via separate script.")
                    print(f"See /opt/localaddons/HR_SECURITY_PROJECT_DOCUMENTATION.md for all details.")
                    sys.exit(0)
                    
                elif "already been taken" in create_resp.text.lower():
                    print(f"✓ PROJECT ALREADY EXISTS")
                    print(f"\nAccess it at:")
                    print(f"  https://generated-complexity-ireland-fully.trycloudflare.com/projects/odoo19-hr-security-fix")
                    sys.exit(0)
                else:
                    print(f"✗ Project creation failed: {create_resp.status_code}")
                    print(f"  {create_resp.text[:300]}")
                    
            else:
                print(f"✗ Failed: {resp.status_code} - {resp.text[:100]}")
                
        except requests.exceptions.ConnectionError:
            print(f"✗ Connection refused")
        except Exception as e:
            print(f"✗ Error: {str(e)[:100]}")

print(f"\n{'='*70}")
print("FAILED: Could not connect to OpenProject on any configuration")
print("='*70")
sys.exit(1)
