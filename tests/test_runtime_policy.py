#!/usr/bin/env python3
"""CLI, API, and SDK share one idempotent Hugging Face runtime policy."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from atomgit.runtime import (
    ATOMGIT_DISABLE_XET,
    ATOMGIT_HF_ENDPOINT,
    configure_hf_environment,
)


results = []


def check(name, condition, detail=""):
    results.append((name, condition, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"[{flag}] {name}" + (f" -> {detail}" if detail else ""))


def main():
    original = {
        name: os.environ.get(name)
        for name in ("HF_ENDPOINT", "HF_HUB_DISABLE_XET", "HF_HOME")
    }
    try:
        with tempfile.TemporaryDirectory() as home_dir:
            home = Path(home_dir)
            with patch("pathlib.Path.home", return_value=home):
                os.environ["HF_ENDPOINT"] = "https://wrong.invalid"
                os.environ["HF_HUB_DISABLE_XET"] = "0"
                os.environ["HF_HOME"] = "/wrong/cache"
                first = configure_hf_environment()
                second = configure_hf_environment()

            expected_cache = home / ".cache" / "atomgit"
            check("endpoint policy applied", os.environ["HF_ENDPOINT"] == ATOMGIT_HF_ENDPOINT)
            check("XET policy applied", os.environ["HF_HUB_DISABLE_XET"] == ATOMGIT_DISABLE_XET)
            check("cache policy applied", os.environ["HF_HOME"] == str(expected_cache))
            check("runtime setup does not create cache during import policy",
                  not expected_cache.exists())
            check("repeated setup is idempotent", first == second == expected_cache)

        import atomgit.api as package_api  # noqa: F401
        import atomgit.cli as package_cli  # noqa: F401
        import atomgit_hub as standalone_sdk  # noqa: F401

        check("API import keeps shared endpoint", os.environ["HF_ENDPOINT"] == ATOMGIT_HF_ENDPOINT)
        check("CLI import keeps shared endpoint", os.environ["HF_HOME"].endswith("/.cache/atomgit"))
        check("standalone SDK keeps shared XET policy", os.environ["HF_HUB_DISABLE_XET"] == "1")
    finally:
        for name, value in original.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    passed = sum(1 for _, condition, _ in results if condition)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
