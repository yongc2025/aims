"""AIMS pipeline acceptance runner."""

import subprocess
import sys


CHECKS = [
    [sys.executable, "-m", "backend.utils.health_check"],
    [sys.executable, "scripts/verify_database.py"],
]


if __name__ == "__main__":
    print("AIMS Pipeline Acceptance")
    print("=" * 30)

    failed = False

    for command in CHECKS:
        print("Running:", " ".join(command))
        result = subprocess.run(command)
        if result.returncode != 0:
            failed = True

    if failed:
        print("FAILED")
        raise SystemExit(1)

    print("READY")
