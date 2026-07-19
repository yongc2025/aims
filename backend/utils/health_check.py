"""AIMS environment health check utility."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


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
    try:
        db_path.mkdir(parents=True, exist_ok=True)
        test_file = db_path / ".healthcheck"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        return True, str(db_path)
    except OSError as exc:
        return False, str(exc)


def main():
    checks = [
        ("python", check_python()),
        ("environment", check_environment()),
        ("database_path", check_database()),
    ]

    failed = False
    print("AIMS Health Check")
    print("=" * 30)

    for name, (ok, detail) in checks:
        symbol = "OK" if ok else "FAIL"
        print(f"{symbol} {name}: {detail}")
        if not ok:
            failed = True

    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
