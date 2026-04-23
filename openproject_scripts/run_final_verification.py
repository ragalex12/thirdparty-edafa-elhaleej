#!/usr/bin/env python3
import subprocess
import sys

result = subprocess.run(
    [sys.executable, '/opt/localaddons/final_verification.py'],
    capture_output=True,
    text=True,
    timeout=15
)

output = result.stdout
if result.stderr:
    output += "\n\nSTDERR:\n" + result.stderr

print(output)

with open('/opt/localaddons/final_verification_result.txt', 'w') as f:
    f.write(output)

print("\nSaved to /opt/localaddons/final_verification_result.txt")
