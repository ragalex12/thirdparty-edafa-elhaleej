#!/usr/bin/env python3
import subprocess
import sys

result = subprocess.run(
    [sys.executable, '/opt/localaddons/close_completed_tasks.py'],
    capture_output=True,
    text=True,
    timeout=60
)

output = result.stdout
if result.stderr:
    output += "\n\nSTDERR:\n" + result.stderr

print(output)

# Save to file
with open('/opt/localaddons/closing_tasks_result.txt', 'w') as f:
    f.write(output)
    f.write(f"\n\nExit code: {result.returncode}")

print("\n" + "="*80)
if result.returncode == 0:
    print("✓ SUCCESS: All tasks closed!")
else:
    print(f"⚠ Completed with exit code: {result.returncode}")
print("Results saved to /opt/localaddons/closing_tasks_result.txt")
print("="*80)
