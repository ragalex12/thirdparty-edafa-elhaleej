#!/usr/bin/env python3
"""Test OpenProject API connectivity on different ports and configurations"""
import requests
from requests.auth import HTTPBasicAuth
import json

API_TOKEN = "f1336582f568d3dc0c27a938d711c10c5f3cb81366aed6ad27b663dc2a7034b3"
AUTH = HTTPBasicAuth("apikey", API_TOKEN)

# Test configurations
configs = [
    {
        "name": "Port 8088 with Host header",
        "url": "http://127.0.0.1:8088",
        "headers": {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Host": "localhost:8088",
        }
    },
    {
        "name": "Port 8090 with Host header",
        "url": "http://127.0.0.1:8090",
        "headers": {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Host": "localhost:8090",
        }
    },
    {
        "name": "Port 8090 without Host header",
        "url": "http://127.0.0.1:8090",
        "headers": {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    },
    {
        "name": "Port 8090 with Cloudflare Host",
        "url": "http://127.0.0.1:8090",
        "headers": {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Host": "generated-complexity-ireland-fully.trycloudflare.com",
        }
    },
]

print("Testing OpenProject API connectivity...\n")
print("=" * 70)

for config in configs:
    print(f"\nTest: {config['name']}")
    print(f"URL: {config['url']}/api/v3/projects")
    
    try:
        response = requests.get(
            f"{config['url']}/api/v3/projects",
            auth=AUTH,
            headers=config['headers'],
            timeout=5
        )
        
        if response.ok:
            data = response.json()
            project_count = len(data.get("_embedded", {}).get("elements", []))
            print(f"✓ SUCCESS - Status: {response.status_code}, Projects: {project_count}")
            
            # Save working config
            with open('/tmp/openproject_working_config.txt', 'w') as f:
                f.write(f"Working configuration:\n")
                f.write(f"URL: {config['url']}\n")
                f.write(f"Headers: {json.dumps(config['headers'], indent=2)}\n")
            print(f"  → Saved working config to /tmp/openproject_working_config.txt")
            break
        else:
            print(f"✗ FAILED - Status: {response.status_code}")
            print(f"  Error: {response.text[:200]}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"✗ CONNECTION REFUSED - {str(e)[:100]}")
    except requests.exceptions.Timeout:
        print(f"✗ TIMEOUT")
    except Exception as e:
        print(f"✗ ERROR - {str(e)[:100]}")

print("\n" + "=" * 70)
