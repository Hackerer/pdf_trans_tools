#!/usr/bin/env python3
"""Validate pdf_trans_tools project."""
import subprocess
import sys
from pathlib import Path

def run_tests():
    """Run pytest on the project."""
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    tests_path = project_root / "tests"

    env = {**subprocess.os.environ, "PYTHONPATH": str(src_path)}

    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(tests_path), "-v"],
        env=env,
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    return result.returncode == 0

def main():
    success = run_tests()
    if success:
        print("\n[PASS] All validations passed")
        sys.exit(0)
    else:
        print("\n[FAIL] Validation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
