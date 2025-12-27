"""
Auto-run upload with 1000 records for testing
"""

import subprocess
import sys

# Run the upload with automatic inputs
process = subprocess.Popen(
    [sys.executable, "upload_structured_data.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# Send inputs
process.stdin.write("1\n")  # Select option 1 (1000 records)
process.stdin.flush()

# Wait a bit for it to load
import time
time.sleep(10)

process.stdin.write("y\n")  # Confirm upload
process.stdin.flush()

# Stream output
for line in process.stdout:
    print(line, end='')

process.wait()
