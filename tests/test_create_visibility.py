#!/usr/bin/env python3
"""Create repositories only after their requested visibility is verified."""
import sys
import contextlib
import io
from atomgit.api import HuggingFaceAPI


def main():
    api_mod = sys.modules["atomgit.api"]
    cfg = sys.modules["atomgit.config"].config
    cfg.get_credentials = lambda: {"token": "fake-token-never-print"}
    original = api_mod.create_repo
    original_exists = api_mod._atomgit_repo_exists
    calls = []
    api_mod.create_repo = lambda **kw: calls.append(kw) or True
    api_mod._atomgit_repo_exists = lambda repo_id, token: False
    try:
        api = HuggingFaceAPI()
        visibility_calls = []
        api.set_repo_visibility = lambda repo_id, private: (
            visibility_calls.append((repo_id, private)) or True
        )
        public = api.create_repo("user/public", repo_type="model", private=False)
        private = api.create_repo("user/private", repo_type="dataset", private=True)
        private_existing = api.create_repo(
            "user/private-existing",
            repo_type="model",
            private=True,
            exist_ok=True,
        )
        ok = (
            public is True
            and private is True
            and private_existing is True
            and len(calls) == 3
            and all(call["private"] is True for call in calls)
            and calls[-1]["exist_ok"] is True
            and visibility_calls
            == [
                ("user/public", False),
                ("user/private", True),
                ("user/private-existing", True),
            ]
        )
        print(
            f"[{'PASS' if ok else 'FAIL'}] "
            "public and private visibility converged"
        )

        api.set_repo_visibility = lambda repo_id, private: False
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            failed_public = api.create_repo(
                "user/failed-public", repo_type="model", private=False
            )
        accurate_failure = (
            failed_public is False
            and calls[-1]["private"] is True
            and "可能" in captured.getvalue()
            and "repo visibility" in captured.getvalue()
        )
        print(f"[{'PASS' if accurate_failure else 'FAIL'}] failed transition is not success")

        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            failed_private_existing = api.create_repo(
                "user/failed-private-existing",
                repo_type="model",
                private=True,
                exist_ok=True,
            )
        accurate_private_failure = (
            failed_private_existing is False
            and calls[-1]["private"] is True
            and calls[-1]["exist_ok"] is True
            and "可能" in captured.getvalue()
            and "私有" in captured.getvalue()
        )
        print(
            f"[{'PASS' if accurate_private_failure else 'FAIL'}] "
            "failed private exist-ok is not success"
        )
        return 0 if ok and accurate_failure and accurate_private_failure else 1
    finally:
        api_mod.create_repo = original
        api_mod._atomgit_repo_exists = original_exists


if __name__ == "__main__":
    raise SystemExit(main())
