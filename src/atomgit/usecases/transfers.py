"""Transfer orchestration shared by the native SDK and CLI bridge."""

from typing import Any

from ..core.contracts import DownloadRequest, OperationResult, UploadRequest
from ..core.policies import resolve_token
from ..core.ports import ConfigPort, TransferPort
from ..domain.transfers import validate_download_request, validate_upload_request


class UploadUseCase:
    def __init__(self, transfer: TransferPort, config: ConfigPort):
        self.transfer = transfer
        self.config = config

    def file(self, request: UploadRequest) -> OperationResult[Any]:
        request = validate_upload_request(request)
        saved = _saved_token(self.config)
        token = resolve_token(request.token, saved, write=True)
        value = self.transfer.upload_file(
            source=request.source,
            repo_id=request.repo_id,
            repo_type=request.repo_type,
            revision=request.revision,
            token=token,
            path_in_repo=request.path_in_repo,
            ignore_patterns=list(request.ignore_patterns) or None,
            message=request.message,
            timeout=request.timeout,
            progress=request.progress,
            num_workers=request.num_workers,
        )
        return OperationResult(
            "upload_file",
            True,
            value=value,
            repo_id=request.repo_id,
            revision=request.revision,
        )

    def folder(self, request: UploadRequest) -> OperationResult[Any]:
        request = validate_upload_request(request)
        saved = _saved_token(self.config)
        token = resolve_token(request.token, saved, write=True)
        value = self.transfer.upload_folder(
            source=request.source,
            repo_id=request.repo_id,
            repo_type=request.repo_type,
            revision=request.revision,
            token=token,
            path_in_repo=request.path_in_repo,
            ignore_patterns=list(request.ignore_patterns) or None,
            message=request.message,
            timeout=request.timeout,
            progress=request.progress,
            resumable=request.resumable,
            num_workers=request.num_workers,
            batch_size=request.batch_size,
            auto_configure_lfs=request.auto_configure_lfs,
        )
        return OperationResult(
            "upload_folder",
            True,
            value=value,
            repo_id=request.repo_id,
            revision=request.revision,
            metadata={
                "resumable": request.resumable,
                "batch_size": request.batch_size,
                "auto_configure_lfs": request.auto_configure_lfs,
            },
        )


class DownloadUseCase:
    def __init__(self, transfer: TransferPort, config: ConfigPort):
        self.transfer = transfer
        self.config = config

    def snapshot(self, request: DownloadRequest) -> OperationResult[Any]:
        request = validate_download_request(request)
        token = resolve_token(request.token, _saved_token(self.config), write=False)
        value = self.transfer.download_snapshot(
            repo_id=request.repo_id,
            repo_type=request.repo_type,
            revision=request.revision,
            token=token,
            local_dir=request.local_dir,
            force=request.force,
            checksum=request.checksum,
            resume=request.resume,
            prune=request.prune,
            allow_patterns=(
                list(request.allow_patterns) if request.allow_patterns else None
            ),
            ignore_patterns=(
                list(request.ignore_patterns) if request.ignore_patterns else None
            ),
        )
        return OperationResult(
            "download_snapshot",
            True,
            value=value,
            repo_id=request.repo_id,
            revision=request.revision,
            metadata={
                "checksum": request.checksum,
                "resume": request.resume,
                "prune": request.prune,
            },
        )

    def file(self, request: DownloadRequest) -> OperationResult[Any]:
        request = validate_download_request(request)
        if not request.filename:
            raise ValueError("filename 不能为空")
        token = resolve_token(request.token, _saved_token(self.config), write=False)
        value = self.transfer.download_file(
            repo_id=request.repo_id,
            filename=request.filename,
            repo_type=request.repo_type,
            revision=request.revision,
            token=token,
            local_dir=request.local_dir,
            force=request.force,
            checksum=request.checksum,
            resume=request.resume,
        )
        return OperationResult(
            "download_file",
            True,
            value=value,
            repo_id=request.repo_id,
            revision=request.revision,
            metadata={"checksum": request.checksum, "resume": request.resume},
        )


def _saved_token(config: ConfigPort):
    credentials = config.get_credentials()
    return credentials.get("token") if credentials else None
