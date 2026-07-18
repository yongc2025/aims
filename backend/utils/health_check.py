"""AIMS environment health check utility."""

import os
import sys
from pathlib import Path


def check_python():
    version = sys.version_info
    ok = version.major == 3 and version.minor >= 11
    return ok, f"Python {version.major}.{version.minor}.{version.micro}"


def check_environment():
    required = [
        "OPENCODE_API_KEY",
        "OPENCODE_MODEL",
    ]
    missing = [key for key in required if not os.getenv(key)]
    return len(missing) == 0, missing


def check_database():
    db_path = Path("storage")
    try