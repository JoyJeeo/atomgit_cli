#!/usr/bin/env python3
"""Prevent false success for unsupported public repository creation."""
import sys
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
        public = api.create_repo("user/repo", repo_type="model", private=False)
        private = api.create_repo("user/repo", repo_type="dataset", private=True)
        ok = public is False and private is True and len(calls) == 1 and calls[0]["private"] is True
        print(f"[{'PASS' if ok else 'FAIL'}] public rejected; private forwarded")
        return 0 if ok else 1
    finally:
        api_mod.create_repo = original
        api_mod._atomgit_repo_exists = original_exists


if __name__ == "__main__":
    raise SystemExit(main())
