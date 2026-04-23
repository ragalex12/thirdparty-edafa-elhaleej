#!/usr/bin/env python3
import subprocess
import sys

result = subprocess.run(
    [sys.executable, '/opt/localaddons/direct_project_check.py'],
    capture_output=True,
    text=True,
    timeout=15
)

print(result.stdout)
if result.stderr:
    print("\nSTDERR:", result.stderr)

with open('/opt/localaddons/direct_check_result.txt', 'w') as f:
    f.write(result.stdout)
    if result.stderr:
        f.write("\n\nSTDERR:\n" + result.stderr)
