#!/usr/bin/env python3
import subprocess
import sys

result = subprocess.run(
    [sys.executable, '/opt/localaddons/show_task_descriptions.py'],
    capture_output=True,
    text=True,
    timeout=10
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

with open('/opt/localaddons/task_descriptions_check.txt', 'w') as f:
    f.write(result.stdout)
    if result.stderr:
        f.write("\n\nSTDERR:\n" + result.stderr)

print("\nSaved to /opt/localaddons/task_descriptions_check.txt")
