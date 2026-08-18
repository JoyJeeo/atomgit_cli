#!/usr/bin/env python3
"""Prove supported fresh import orders and completion runtime lightness."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ENDPOINT = "https://hub.atomgit.com"
FORBIDDEN_COMPLETION_IMPORTS = (
    "atomgit.api",
    "atomgit.atomgit_hub",
    "atomgit_hub",
    "huggingface_hub",
    "datasets",
    "torch",
    "pyarrow",
    "pandas",
)
results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    suffix = f" -> {detail}" if detail and not condition else ""
    print(f"[{flag}] {name}{suffix}")


def run_probe(imports, home, completion=False):
    environment = os.environ.copy()
    for name in ("HF_ENDPOINT", "HF_HUB_DISABLE_XET", "HF_HOME"):
        environment.pop(name, None)
    environment["HOME"] = str(home)
    if completion:
        environment["_ATOMGIT_COMPLETE"] = "zsh_complete"
    else:
        environment.pop("_ATOMGIT_COMPLETE", None)
    script = (
        f"{imports}; "
        "import json, os, pathlib, sys; "
        "payload={'endpoint': os.environ.get('HF_ENDPOINT'), "
        "'xet': os.environ.get('HF_HUB_DISABLE_XET'), "
        "'home': os.environ.get('HF_HOME'), "
        "'cache_exists': pathlib.Path(os.environ['HF_HOME']).exists(), "
        f"'forbidden': [name for name in {FORBIDDEN_COMPLETION_IMPORTS!r} if name in sys.modules]}}; "
        "print(json.dumps(payload, sort_keys=True))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(REPOSITORY_ROOT),
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    try:
        payload = json.loads(completed.stdout) if completed.returncode == 0 else None
    except json.JSONDecodeError:
        payload = None
    return completed, payload


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        permutations = (
            "import atomgit; import atomgit.api; import atomgit.cli",
            "import atomgit.cli; import atomgit.api; import atomgit",
            "import atomgit.api; import atomgit_hub; import atomgit.cli",
            "import atomgit_hub; import atomgit; import atomgit.api",
        )
        for index, imports in enumerate(permutations, start=1):
            home = root / f"home-{index}"
            home.mkdir()
            completed, payload = run_probe(imports, home)
            expected_home = str(home / ".cache" / "atomgit")
            check(
                f"fresh supported import order {index} converges on runtime policy",
                completed.returncode == 0
                and payload is not None
                and payload["endpoint"] == EXPECTED_ENDPOINT
                and payload["xet"] == "1"
                and payload["home"] == expected_home
                and payload["cache_exists"] is False,
                completed.stdout.strip() or completed.stderr.strip(),
            )

        completion_home = root / "completion-home"
        completion_home.mkdir()
        completed, payload = run_probe(
            "import atomgit; import atomgit.cli",
            completion_home,
            completion=True,
        )
        check(
            "completion import applies policy without heavy business dependencies",
            completed.returncode == 0
            and payload is not None
            and payload["endpoint"] == EXPECTED_ENDPOINT
            and payload["forbidden"] == []
            and payload["cache_exists"] is False
            and not (completion_home / ".atomgit").exists(),
            completed.stdout.strip() or completed.stderr.strip(),
        )

    passed = sum(condition for _, condition, _ in results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
