# Current Issue Contract

# Issue DOWNLOAD-RAW-INTEGRITY

Status: `completed`

## Identity

- Local Issue: `DOWNLOAD-RAW-INTEGRITY`
- Title: `Raw UTF-8-path downloads can save HTTP framing as file content or accept truncated bodies`
- Type: `bug`, `security`, `cli`, `compatibility`
- Priority: `P1`
- Branch: `codex/fix-download-raw-integrity` (local only)
- Base: `yuto`
- Delivery mode: implement and review locally, commit, merge into `yuto`, and
  push only `yuto`.

## Previous Issue (Closed)

- `DOWNLOAD-PATH-TRAVERSAL` was delivered by `24a3baf` and merged into `yuto`
  by `e724c47`.

## User Impact And Evidence

The raw socket fallback copies response bytes until EOF without interpreting
HTTP body framing. An offline probe returned a valid chunked body containing
`data`; the CLI saved `4\r\ndata\r\n0\r\n\r\n` and reported success. A response
shorter than its Content-Length is likewise accepted. This path is used for
nested non-ASCII AtomGit filenames.

## Scope

In scope: decode chunked bodies, enforce Content-Length, reject ambiguous or
unsupported transfer framing, bound protocol line parsing, clean temporary
files after failure, preserve atomic replacement, and add strict offline
transport regressions.

Out of scope: destination paths, redirect credential policy, repository type,
and ordinary urllib response framing.

## Acceptance Criteria

- Valid chunked and fixed-length bodies produce only their decoded content.
- Truncated, malformed, conflicting, or unsupported framing fails without
  replacing an existing destination and removes the `.part` file.
- Close-delimited bodies remain supported.
- Existing nested non-ASCII AtomGit downloads remain compatible.
- Focused and full offline tests, compileall, and `git diff --check` pass.

## Permissions

- Authorized: local edits, commits, local merge into `yuto`, and push of
  `yuto`; the task branch remains local-only.
- Authorized remote tests: only `weixin_52273949/test_model` and
  `weixin_52273949/test_datasets`; no remote write is needed.

## Delivery Record

- Implementation: the raw transport now bounds status/header parsing, rejects
  malformed request/response headers, streams and decodes chunked bodies,
  enforces strict decimal Content-Length, rejects ambiguous or unsupported
  transfer framing, explicitly closes response streams and sockets, removes
  stale/failed `.part` files, and atomically replaces the destination only
  after a complete valid body.
- Regression evidence: before the fix only 2/7 initial assertions passed;
  chunk framing was saved as content and truncated, malformed, conflicting,
  and unsupported responses were all accepted.
- Focused offline tests: raw integrity, redirect security, and download
  contract passed as 3 pytest cases. Added valid fixed/chunked/close-delimited,
  malformed/truncated/conflicting framing, strict numeric syntax, chunk
  extensions, trailers, old-destination preservation, and cleanup coverage.
- Complete offline suite: `python -m pytest` passed 39/39 in 37.52 seconds.
- Required checks: compileall and `git diff --check` passed.
- Authorized read-only live check: nested `sub/中文样本.csv` downloaded from
  `weixin_52273949/test_model` and retained its 31-byte content.
- Independent review: first pass requested strict numeric syntax and explicit
  response-stream closure. Both findings were fixed and retested. Fresh review
  found no open findings: `APPROVED`.
- Human acceptance: standing acceptance granted for the approved full plan.
- Commit/merge/push: authorized.
