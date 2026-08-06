#!/usr/bin/env python3
"""Create public repositories only after a verified V5 transition."""
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
        public = api.create_repo("user/repo", repo_type="model", private=False)
        private = api.create_repo("user/repo", repo_type="dataset", private=True)
        ok = (
            public is True
            and private is True
            and len(calls) == 2
            and all(call["private"] is True for call in calls)
            and visibility_calls == [("user/repo", False)]
        )
        print(f"[{'PASS' if ok else 'FAIL'}] public transitioned; private preserved")

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
        return 0 if ok and accurate_failure else 1
    finally:
        api_mod.create_repo = original
        api_mod._atomgit_repo_exists = original_exists


if __name__ == "__main__":
    raise SystemExit(main())
