#!/usr/bin/env python3
import subprocess
import sys

result = subprocess.run(
    [sys.executable, '/opt/localaddons/close_all_remaining.py'],
    capture_output=True,
    text=True,
    timeout=60
)

print(result.stdout)
if result.stderr:
    print("\nSTDERR:", result.stderr)

with open('/opt/localaddons/final_closing_result.txt', 'w') as f:
    f.write(result.stdout)
    if result.stderr:
        f.write("\n\nSTDERR:\n" + result.stderr)

print("\nResults saved to /opt/localaddons/final_closing_result.txt")
