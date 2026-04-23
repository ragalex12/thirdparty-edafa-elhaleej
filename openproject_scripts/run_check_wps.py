#!/usr/bin/env python3
import subprocess
import sys

result = subprocess.run(
    [sys.executable, '/opt/localaddons/check_all_workpackages.py'],
    capture_output=True,
    text=True,
    timeout=10
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

with open('/opt/localaddons/workpackages_status.txt', 'w') as f:
    f.write(result.stdout)
