# Current Issue Contract

# Issue DOWNLOAD-REDIRECT-AUTH

Status: `completed`

## Identity

- Local Issue: `DOWNLOAD-REDIRECT-AUTH`
- Title: `Download redirects can forward the AtomGit bearer token to another origin`
- Type: `security`, `cli`, `compatibility`
- Priority: `P0`
- Branch: `codex/fix-download-redirect-auth` (local only)
- Base: `yuto`
- Delivery mode: implement and review locally, commit without the retired
  `czx:` prefix, merge into `yuto`, and push only `yuto`.

## Previous Issue (Closed)

- `DOWNLOAD-REPO-INFO-404` was delivered in `61a215c`: CLI downloads bypass
  the unsupported repo-info route, support nested non-ASCII filenames, and
  passed the recorded model/dataset readback. The stale `in_progress` state is
  closed by activation of this Issue.

## User Impact And Evidence

`_download_atomgit_file` adds the saved bearer token to a reusable header map.
Both urllib redirects and the raw UTF-8-path transport reuse that header map
after a redirect changes scheme, host, or port. An offline two-server probe
confirmed that a request redirected from `127.0.0.1` to `localhost` delivered
`Authorization: Bearer probe-secret` to the second origin.

A redirect controlled by a service response must not disclose an AtomGit token
to an unrelated origin. HTTPS downloads must also not silently downgrade to
plain HTTP.

## Scope

In scope:

- define a shared redirect-origin policy for CLI direct downloads;
- retain Authorization only for the original trusted origin;
- strip Authorization on cross-origin redirects;
- reject HTTPS-to-HTTP downgrade and unsupported schemes;
- cover urllib and raw UTF-8-path download branches with offline regressions.

Out of scope:

- destination path traversal, raw HTTP chunked framing, repository type
  selection, existing-file skip semantics, SDK downloads, and remote writes.

## Product Decisions

- Existing destination files remain skipped by default.
- `atomgit login --token` remains supported.
- Remote tests may use only the maintainer-provided
  `weixin_52273949/test_model` and `weixin_52273949/test_datasets` repositories.
- Commit subjects no longer use the `czx:` prefix.

## Acceptance Criteria

- Same-origin relative or absolute redirects retain the bearer token.
- A redirect changing scheme, hostname, or port does not forward the bearer
  token.
- HTTPS-to-HTTP downgrade fails before contacting the downgraded target.
- Redirect handling remains bounded and rejects unsupported URL schemes.
- Direct downloads without a redirect remain compatible.
- Focused download tests, the complete offline suite,
  `python -m compileall -q .`, and `git diff --check` pass in the
  `atomgit_cli` conda environment.

## Permissions

- Authorized: local source/test/documentation edits, local task branch and
  commits, local merge into `yuto`, and push of `yuto` only.
- Authorized remote testing: only the two maintainer-provided test repositories
  named above. This Issue requires no remote write.
- Not authorized: pushing the task branch, using other remote repositories,
  merging into `main`, release, or publication.

## Delivery Record

- Implementation: `_AtomGitRedirectHandler` now applies a shared origin policy
  to urllib downloads; the raw UTF-8-path transport applies the same policy at
  every redirect. Scheme, hostname, or port changes permanently remove the
  Authorization header. HTTPS-to-HTTP redirects, URL credentials, missing
  hosts, and unsupported schemes are rejected. Raw redirect lookup also uses
  the normalized lowercase `location` response-header key.
- Regression evidence: the new isolated two-server test failed before the fix
  because the second origin received `Bearer fake-download-token-never-print`;
  the raw branch also failed to recognize its lowercase location header.
- Focused offline tests: download redirect security, download contract, and
  download recovery scripts passed as 3 pytest cases.
- Complete offline suite: `python -m pytest` passed 37/37 in 31.70 seconds in
  the `atomgit_cli` conda environment.
- Required checks: `python -m compileall -q .` and `git diff --check` passed.
- Authorized read-only live check: downloaded `config.json` from
  `weixin_52273949/test_model`; result was successful, the temporary file
  existed, and its size was 77 bytes. No token was printed and no remote state
  changed.
- Independent review: first pass requested a P2 test-strengthening change for
  same-origin absolute redirects and cross-origin redirect chains. Both tests
  were added and passed. Fresh review found no open findings: `APPROVED`.
- Remaining risk: the live check proves compatibility with the current test
  repository path but cannot exercise every possible future CDN redirect
  topology. The offline matrix covers origin changes and downgrade rejection.
- Human acceptance: accepted; the maintainer authorized completion of the full
  development plan through tests, commits, local merges, and pushes of `yuto`.
- Commit/merge/push: authorized for this completed Issue.
