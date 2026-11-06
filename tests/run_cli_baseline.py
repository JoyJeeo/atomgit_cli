#!/usr/bin/env python3
"""Run the complete isolated offline matrix as the mandatory CLI baseline."""

import os
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def main():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=str(REPOSITORY_ROOT),
        check=False,
        env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
