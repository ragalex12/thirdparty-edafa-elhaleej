#!/usr/bin/env python3
"""
Wrapper to run create_hr_security_project.py and capture all output
"""
import subprocess
import sys

print("Starting OpenProject creation...")
print("This may take 30-60 seconds as it creates all work packages...")
print("=" * 70)

result = subprocess.run(
    [sys.executable, '/opt/localaddons/create_hr_security_project.py'],
    capture_output=True,
    text=True
)

output = f"""
{'='*70}
OPENPROJECT CREATION - FINAL RESULTS
{'='*70}

Exit Code: {result.returncode}

STDOUT:
{result.stdout}

STDERR:
{result.stderr}

{'='*70}
"""

print(output)

# Write to file
with open('/opt/localaddons/openproject_final_result.txt', 'w') as f:
    f.write(output)

print("\nResults written to /opt/localaddons/openproject_final_result.txt")

if result.returncode == 0:
    print("\n✓ SUCCESS!")
    print("\nYour project is ready at:")
    print("https://generated-complexity-ireland-fully.trycloudflare.com/projects/odoo19-hr-security-fix")
else:
    print("\n✗ There were some errors. Check the output above.")

sys.exit(result.returncode)
