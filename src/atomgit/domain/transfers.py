"""Upload/download validation and final-state invariants."""

from pathlib import Path

from ..core.contracts import DownloadRequest, UploadRequest
from ..core.policies import normalize_repo_id, normalize_repo_type, normalize_revision


def validate_upload_request(request: UploadRequest) -> UploadRequest:
    source = Path(request.source)
    if not source.exists():
        raise FileNotFoundError(f"路径不存在: {source}")
    if not isinstance(request.num_workers, int) or request.num_workers < 1:
        raise ValueError("num_workers 必须是正整数")
    if not isinstance(request.batch_size, int) or not 1 <= request.batch_size <= 20:
        raise ValueError("batch_size 必须是 1 到 20 之间的整数")
    if request.timeout <= 0:
        raise ValueError("timeout 必须大于 0")
    return UploadRequest(
        source=source,
        repo_id=normalize_repo_id(request.repo_id),
        repo_type=normalize_repo_type(request.repo_type),
        revision=normalize_revision(request.revision),
        token=request.token,
        path_in_repo=request.path_in_repo or "./",
        ignore_patterns=tuple(request.ignore_patterns or ()),
        message=request.message,
        resumable=bool(request.resumable),
        num_workers=request.num_workers,
        batch_size=request.batch_size,
        timeout=float(request.timeout),
        progress=bool(request.progress),
        checksum=bool(request.checksum),
        auto_configure_lfs=bool(request.auto_configure_lfs),
    )


def validate_download_request(request: DownloadRequest) -> DownloadRequest:
    return DownloadRequest(
        repo_id=normalize_repo_id(request.repo_id),
        filename=request.filename,
        repo_type=(
            None
            if request.repo_type in (None, "")
            else normalize_repo_type(request.repo_type)
        ),
        revision=normalize_revision(request.revision),
        token=request.token,
        local_dir=request.local_dir,
        force=bool(request.force),
        checksum=bool(request.checksum),
        resume=bool(request.resume),
        prune=bool(request.prune),
        allow_patterns=(
            None if request.allow_patterns is None else tuple(request.allow_patterns)
        ),
        ignore_patterns=(
            None if request.ignore_patterns is None else tuple(request.ignore_patterns)
        ),
    )
