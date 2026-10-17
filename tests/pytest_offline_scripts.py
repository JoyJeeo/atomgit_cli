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

    # A missed fake must fail locally instead of sending fixture credentials.
    guard = tmp_path / "network_guard"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(
        "import socket\n"
        "_connect = socket.socket.connect\n"
        "_connect_ex = socket.socket.connect_ex\n"
        "def _check(sock, address):\n"
        "    if sock.family in (socket.AF_INET, socket.AF_INET6) and address[0] not in ('127.0.0.1', '::1', 'localhost'):\n"
        "        raise RuntimeError('offline test blocked external network')\n"
        "def connect(sock, address):\n"
        "    _check(sock, address)\n"
        "    return _connect(sock, address)\n"
        "def connect_ex(sock, address):\n"
        "    _check(sock, address)\n"
        "    return _connect_ex(sock, address)\n"
        "socket.socket.connect = connect\n"
        "socket.socket.connect_ex = connect_ex\n",
        encoding="utf-8",
    )
    environment["PYTHONPATH"] = (
        str(guard) + os.pathsep + environment.get("PYTHONPATH", "")
    )
    for secret_name in ("ATOMGIT_TEST_TOKEN", "ATOMGIT_TOKEN", "HF_TOKEN"):
        environment.pop(secret_name, None)

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
