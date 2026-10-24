#!/usr/bin/env python3
"""Offline contracts for stable version identity and Release publication."""

import hashlib
import json
import os
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

from atomgit import __version__, release


ROOT = Path(__file__).resolve().parents[1]
RESULTS = []


def check(name, condition, detail=""):
    RESULTS.append((name, condition, detail))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" + (f" -> {detail}" if detail else ""))


def ci_gate_checks():
    import yaml

    ci_path = ROOT / ".github" / "workflows" / "ci.yml"
    if not ci_path.exists():
        check("push/PR/release share an offline CI gate", False)
        return
    ci = yaml.load(ci_path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    release_workflow = yaml.load(
        (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    check(
        "CI covers push, pull requests and reusable release verification",
        {"push", "pull_request", "workflow_call"} <= set(ci["on"]),
    )
    check("push CI targets main only", ci["on"]["push"]["branches"] == ["main"])
    prepare_runs = "\n".join(
        step.get("run", "") for step in release_workflow["jobs"]["prepare"]["steps"]
    )
    check(
        "release source must belong to main",
        "grep -E 'origin/main$'" in prepare_runs and "origin/yuto" not in prepare_runs,
    )
    from atomgit.infrastructure.completion import _ACTIVATION_WARNING

    raw_base = "https://raw.githubusercontent.com/JoyJeeo/atomgit_cli/main/"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    check(
        "installation and cleanup links use main",
        raw_base + "install.sh" in readme
        and raw_base + "uninstall.sh" in readme
        and raw_base + "uninstall.sh" in _ACTIVATION_WARNING,
    )
    job = ci["jobs"]["offline"]
    steps = job["steps"]
    runs = "\n".join(step.get("run", "") for step in steps)
    check(
        "CI runs the complete baseline in atomgit_cli",
        "python tests/run_cli_baseline.py" in runs
        and "python -m compileall -q ." in runs
        and any(
            step.get("with", {}).get("activate-environment") == "atomgit_cli"
            for step in steps
        ),
    )
    matrix = job["strategy"]["matrix"]["include"]
    check(
        "CI includes Linux, macOS, Windows and Python range endpoints",
        {row["os"] for row in matrix}
        >= {"ubuntu-latest", "macos-latest", "windows-latest"}
        and {row["python"] for row in matrix} >= {"3.9", "3.13"},
    )
    verify = release_workflow["jobs"].get("verify", {})
    check(
        "release verifies the exact source SHA before preparation",
        verify.get("uses") == "./.github/workflows/ci.yml"
        and verify.get("with", {}).get("source_sha") == "${{ inputs.source_sha }}"
        and release_workflow["jobs"]["prepare"].get("needs") == "verify",
    )
    check(
        "failed tests cannot be ignored by publishing",
        not any(step.get("continue-on-error") == "true" for step in steps)
        and "always()" not in str(release_workflow["jobs"]["prepare"])
        and release_workflow["jobs"]["publish"]["needs"] == "prepare",
    )


def main():
    ci_gate_checks()

    notes = ROOT / "RELEASE_NOTES.md"
    check("versioned release notes exist", notes.exists())
    if notes.exists():
        first_line = notes.read_text(encoding="utf-8").splitlines()[0]
        check(
            "release notes match the authoritative version",
            first_line == f"# AtomGit CLI {__version__}",
            first_line,
        )

    check("stable version accepts exact numeric SemVer", release.is_stable_version("1.2.3"))
    for invalid in ("v1.2.3", "1.2", "1.2.3-rc1", "1.2.3+local.1", "1.2.3.dev1", ""):
        check(f"stable version rejects {invalid or 'empty'}", not release.is_stable_version(invalid))

    releases = [
        {"tag_name": "v9.9.9", "draft": False, "prerelease": False},
        {"tag_name": "2.0.0", "draft": False, "prerelease": False},
        {"tag_name": "3.0.0", "draft": True, "prerelease": False},
        {"tag_name": "1.9.9", "draft": False, "prerelease": True},
        {"tag_name": "1.10.0", "draft": False, "prerelease": False},
    ]
    selected = release.select_release(releases)
    check("latest resolver ignores v, draft, and prerelease history", selected["tag_name"] == "2.0.0")
    check("explicit resolver rejects legacy tag", release.select_release(releases, "v9.9.9") is None)

    with tempfile.TemporaryDirectory(prefix="atomgit-release-contract-") as directory:
        wheel = Path(directory) / "atomgit-2.0.0-py3-none-any.whl"
        with zipfile.ZipFile(wheel, "w") as archive:
            archive.writestr("atomgit/__init__.py", "__version__ = '2.0.0'\n")
            archive.writestr(
                "atomgit-2.0.0.dist-info/METADATA",
                "Metadata-Version: 2.1\nName: atomgit\nVersion: 2.0.0\n",
            )
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
        checksum = f"{digest}  {wheel.name}\n"
        check("wheel metadata and checksum validate before pip", release.validate_release_assets(wheel, checksum, "2.0.0"))
        try:
            release.validate_checksum(checksum + checksum, wheel.name)
        except release.ReleaseValidationError:
            ambiguous = True
        else:
            ambiguous = False
        check("ambiguous checksum entries are rejected", ambiguous)

    deploy = (ROOT / "deploy.sh").read_text(encoding="utf-8")
    check("deploy script has no PyPI or twine publication path", "twine" not in deploy and "atomgitsdktoken" not in deploy)
    workflow = ROOT / ".github" / "workflows" / "release.yml"
    check("protected manual release workflow exists", workflow.exists())
    if workflow.exists():
        text = workflow.read_text(encoding="utf-8")
        check("release workflow is manual", "workflow_dispatch:" in text)
        check("release workflow creates annotated stable tags", "git tag -a" in text and "v${" not in text)
        check(
            "annotated tags use the repository-local Actions identity",
            'git config --local user.name "github-actions[bot]"' in text
            and 'git config --local user.email "41898282+github-actions[bot]@users.noreply.github.com"'
            in text
            and text.index('git config --local user.name "github-actions[bot]"')
            < text.index("git tag -a"),
        )
        check("release workflow has no PyPI or token write path", "twine" not in text and "atomgitsdktoken" not in text)
        check("release workflow pauses in a protected environment", "release-approval" in text and "contents: write" in text)
        check(
            "release checksums cover exact downloadable asset names",
            "sha256sum LICENSE atomgit-${{ inputs.version }}-py3-none-any.whl atomgit-${{ inputs.version }}.tar.gz"
            in text
            and "sha256sum *" not in text,
        )
        check(
            "release workflow publishes reviewed nonempty notes",
            text.index("Check out exact release notes")
            < text.index("Download reviewed assets")
            and "grep -Fx" in text
            and "--notes-file RELEASE_NOTES.md" in text
            and "--notes-file /dev/null" not in text,
        )
        check(
            "existing public Releases are rejected before asset mutation",
            "existing Release is not the expected unpublished draft" in text
            and text.index("existing Release is not the expected unpublished draft")
            < text.index("for asset in dist/*"),
        )
        check(
            "resumed drafts synchronize the reviewed release notes",
            'gh release edit "${{ inputs.version }}" --notes-file RELEASE_NOTES.md'
            in text,
        )
        check(
            "remote assets are exact and byte-verified before publication",
            "remote Release asset set differs from the exact expected set" in text
            and "remote asset bytes differ after upload" in text
            and "releases/tags/${{ inputs.version }}/assets" not in text
            and text.count('.assets[] | select(.name == \\"$name\\") | .digest') == 3
            and text.index("remote asset bytes differ after upload")
            < text.index('gh release edit "${{ inputs.version }}" --draft=false'),
        )
        check(
            "complete drafts preserve and validate their original assets",
            'gh release download "${{ inputs.version }}" --dir remote-dist' in text
            and "downloaded draft asset differs from its recorded digest" in text
            and "sha256sum --strict -c SHA256SUMS" in text
            and "cmp LICENSE remote-dist/LICENSE" in text
            and 'tarfile.open(sdist_path, "r:gz")' in text
            and 'expected_metadata = f"atomgit-{version}/PKG-INFO"' in text
            and "member.name == expected_metadata" in text
            and 'echo "ASSET_DIR=remote-dist" >> "$GITHUB_ENV"' in text
            and 'for asset in "$ASSET_DIR"/*' in text
            and "Production/Stable" in text
            and "--clobber" not in text,
        )
        check(
            "partial drafts reject unexpected assets and retain same-byte checks",
            "draft Release contains unexpected assets" in text
            and "existing asset bytes differ" in text
            and 'echo "ASSET_DIR=dist" >> "$GITHUB_ENV"' in text,
        )
        check("release workflow refuses mismatched existing assets", "existing asset bytes differ" in text and "--clobber" not in text)

    if any(not passed for _, passed, _ in RESULTS):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
