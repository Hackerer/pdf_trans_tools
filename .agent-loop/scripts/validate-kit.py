#!/usr/bin/env python3
"""Validate pdf_trans_tools - wrapper that runs pytest."""
import subprocess
import sys
import os

os.chdir("/Users/max/Documents/pdf_trans_tools")
os.environ["PYTHONPATH"] = "/Users/max/Documents/pdf_trans_tools/src"

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v"],
    capture_output=True,
    text=True
)
print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)
sys.exit(result.returncode)
