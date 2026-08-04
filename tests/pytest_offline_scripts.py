"""Collect every legacy offline script in an isolated pytest subprocess."""

import os
import subprocess
import sys
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_CASES = sorted(
    path.relative_to(REPOSITORY_ROOT)
    for path in (REPOSITORY_ROOT / "tests").glob("test_*.py")
)


@pytest.mark.parametrize("script_path", SCRIPT_CASES, ids=str)
def test_offline_script(script_path, tmp_path):
    isolated_home = tmp_path / "home"
    isolated_home.mkdir()
    environment = os.environ.copy()
    environment.update(
        {
            "HOME": str(isolated_home),
            "GIT_CONFIG_GLOBAL": str(isolated_home / "gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
        }
    )

    result = subprocess.run(
        [sys.executable, str(REPOSITORY_ROOT / script_path)],
        cwd=str(REPOSITORY_ROOT),
        env=environment,
        capture_output=True,
        text=True,
        timeout=180 if script_path.name == "test_wheel_smoke.py" else 60,
    )

    assert result.returncode == 0, (
        f"{script_path} exited {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
