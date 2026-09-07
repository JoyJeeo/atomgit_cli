"""Canonical AtomGit upload adapter and historical API method boundary."""

from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Optional

from huggingface_hub import close_session as close_hf_session
from huggingface_hub import constants as hf_constants
from huggingface_hub import upload_file as hf_upload_file
from huggingface_hub import upload_folder

from ...infrastructure.config import config
from ...infrastructure.filesystem import format_file_size
from ...infrastructure.validation import (
    is_supported_upload_revision,
    normalize_path_in_repo,
    validate_upload_path_no_symlinks,
)
from ..lfs.pointer import run_canonical_lfs_upload
from .contracts import _RESUMABLE_DEFAULT_REQUEST_TIMEOUT, DEFAULT_UPLOAD_BATCH_SIZE
from .errors import ResumableWorkerError, _classify_upload_error
from .ordinary import (
    _capture_progress_bar_state,
    _restore_progress_bar_state,
    _set_progress_bar,
    _upload_folder_with_workers,
)
from .projection import (
    _collect_resumable_upload_files,
    _prepare_resumable_upload_projection,
    _resumable_committed_file_count,
    _resumable_upload_progress,
)
from .resumable import (
    _execute_resumable_upload_process,
    _prefix_resumable_ignore_patterns,
    _print_upload_batch_plan,
    _print_upload_batch_summary,
    _validate_resumable_upload_target,
)

# Program-step 9 LFS policy slots are wired by atomgit.api.
_atomgit_repo_type = None
_RESUMABLE_LFS_PATTERN_MAX_COUNT = None
_configure_remote_lfs_attributes = None
_validated_lfs_patterns = None
_UPLOAD_TOKEN_OVERRIDE = ContextVar("atomgit_upload_token_override", default=None)


def _print_resumable_upload_progress(batch_number, batch_count, progress) -> None:
    message = (
        f"[批次 {batch_number}/{batch_count}] 断点状态: "
        f"已哈希 {progress['hashed_files']}/{progress['total_files']}"
        f"（{format_file_size(progress['hashed_bytes'])}/"
        f"{format_file_size(progress['total_bytes'])}），"
        f"LFS 已预上传 {progress['preuploaded_files']}/"
        f"{progress['lfs_files']}"
        f"（{format_file_size(progress['preuploaded_bytes'])}/"
        f"{format_file_size(progress['lfs_bytes'])}），"
        f"本地待确认 {progress['pending_files']}"
        f"（{format_file_size(progress['pending_bytes'])}）"
    )
    if progress["unknown_files"]:
        message += (
            f"，状态未知 {progress['unknown_files']}"
            f"（{format_file_size(progress['unknown_bytes'])}）"
        )
    print(message, flush=True)


@contextmanager
def scoped_upload_token(token):
    """Use an explicit SDK token without mutating saved user credentials."""
    marker = _UPLOAD_TOKEN_OVERRIDE.set(token)
    try:
        yield
    finally:
        _UPLOAD_TOKEN_OVERRIDE.reset(marker)


class UploadServiceMixin:
    def upload_folder(
        self,
        file_path: Path,
        repo_id: str,
        remote_path: str = None,
        message: str = None,
        upload_timeout: Optional[float] = None,
        progress_bar: bool = True,
        path_in_repo: str = None,
        repo_type: str = None,
        revision: str = None,
        ignore_patterns=None,
        num_workers: int = 5,
    ) -> bool:
        """上传单个文件 - 使用Hugging Face Hub SDK

        优先使用 HF ``upload_file`` 直接以文件路径上传，避免旧实现中
        "先复制再上传"的额外本地拷贝开销；仅在 HF 版本过旧（无
        ``upload_file``）时回退到 ``upload_folder`` + 唯一系统临时目录。

        Args:
            path_in_repo: 仓库内目标目录前缀。为空/``./`` 时上传到仓库根目录；
                否则文件会被放到该前缀下（如 ``sub/`` → ``sub/<文件名>``）。
            repo_type: 仓库类型，``model`` 或 ``dataset``。为空时由 HF
                默认按 ``model`` 处理（保持既有行为）。
            revision: 上传目标 revision。AtomGit 当前仅支持空值或 ``main``；
                CLI 会在调用本方法前拒绝其他值。
            ignore_patterns: 单文件上传路径下该参数仅会匹配 ``file_path.name``，
                几乎不生效——主要对目录上传有意义。新实现（``upload_file``）
                不支持该参数，传入时若非空会回退到 ``upload_folder`` 旧路径
                以保留语义。
        """
        if not is_supported_upload_revision(revision):
            print("上传 revision 名称不合法，已拒绝上传")
            return False
        try:
            try:
                validate_upload_path_no_symlinks(file_path)
            except ValueError as error:
                print(str(error))
                return False
            if not file_path.exists():
                print(f"文件不存在: {file_path}")
                return False

            override_token = _UPLOAD_TOKEN_OVERRIDE.get()
            credentials = (
                {"token": override_token}
                if override_token
                else config.get_credentials()
            )
            if not credentials:
                print("未找到登录凭证")
                return False

            # 规范化 path_in_repo（remote_path 为旧别名，向后兼容）
            try:
                pipr = normalize_path_in_repo(
                    path_in_repo if path_in_repo is not None else remote_path
                )
            except ValueError as e:
                print(f"上传路径不合法: {e}")
                return False

            original_timeout = hf_constants.DEFAULT_REQUEST_TIMEOUT
            original_progress_state = _capture_progress_bar_state()
            _set_progress_bar(progress_bar)

            commit_message = message or "Upload folder using atomgit client"
            normalized_repo_id = self._normalize_repo_id(repo_id)
            # 使用 Monkey Patch 方式临时修改 huggingface_hub 的默认超时配置
            request_timeout = (
                upload_timeout
                if upload_timeout is not None
                else _RESUMABLE_DEFAULT_REQUEST_TIMEOUT
            )
            hf_constants.DEFAULT_REQUEST_TIMEOUT = request_timeout
            close_hf_session()

            try:
                # 路径2（推荐）：直接 upload_file，无本地拷贝
                if hf_upload_file is not None and not ignore_patterns:
                    # upload_file 需要完整的 path_in_repo（含文件名）
                    remote_file_path = (
                        f"{pipr}/{file_path.name}" if pipr else file_path.name
                    )
                    file_kwargs = dict(
                        path_or_fileobj=str(file_path),
                        path_in_repo=remote_file_path,
                        repo_id=normalized_repo_id,
                        token=credentials["token"],
                        commit_message=commit_message,
                    )
                    upload_repo_type = _atomgit_repo_type(repo_type)
                    if upload_repo_type is not None:
                        file_kwargs["repo_type"] = upload_repo_type
                    if revision is not None:
                        file_kwargs["revision"] = revision
                    run_canonical_lfs_upload(
                        lambda: hf_upload_file(**file_kwargs),
                        token=credentials["token"],
                        repo_id=normalized_repo_id,
                        timeout=request_timeout,
                    )
                    return True

                # 路径1（回退）：upload_folder + 临时目录拷贝（旧实现）
                # 触发条件：HF 版本过旧无 upload_file，或用户传了 ignore_patterns
                import tempfile

                with tempfile.TemporaryDirectory(prefix="atomgit-upload-") as temp_name:
                    temp_dir = Path(temp_name)
                    if pipr:
                        target_file = temp_dir / pipr / file_path.name
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        upload_path_in_repo = f"{pipr}/"
                    else:
                        target_file = temp_dir / file_path.name
                        upload_path_in_repo = "./"
                    import shutil

                    shutil.copy2(file_path, target_file)
                    upload_kwargs = dict(
                        repo_id=normalized_repo_id,
                        folder_path=str(temp_dir),
                        path_in_repo=upload_path_in_repo,
                        token=credentials["token"],
                        commit_message=commit_message,
                    )
                    upload_repo_type = _atomgit_repo_type(repo_type)
                    if upload_repo_type is not None:
                        upload_kwargs["repo_type"] = upload_repo_type
                    if revision is not None:
                        upload_kwargs["revision"] = revision
                    if ignore_patterns:
                        upload_kwargs["ignore_patterns"] = ignore_patterns
                    run_canonical_lfs_upload(
                        lambda: upload_folder(**upload_kwargs),
                        token=credentials["token"],
                        repo_id=normalized_repo_id,
                        timeout=request_timeout,
                    )
                    return True
            finally:
                hf_constants.DEFAULT_REQUEST_TIMEOUT = original_timeout
                close_hf_session()
                _restore_progress_bar_state(original_progress_state)
        except Exception as e:
            err_type, hint = _classify_upload_error(e, repo_id=repo_id)
            print(f"上传文件失败[{err_type}]")
            print(f"💡 建议: {hint}")
            return False

    def upload_directory(
        self,
        dir_path: Path,
        repo_id: str,
        message: str = None,
        progress_callback=None,
        upload_timeout: Optional[float] = None,
        progress_bar: bool = True,
        path_in_repo: str = None,
        repo_type: str = None,
        revision: str = None,
        ignore_patterns=None,
        resumable: bool = False,
        num_workers: int = 5,
        auto_configure_lfs: bool = False,
        batch_size: int = DEFAULT_UPLOAD_BATCH_SIZE,
    ) -> bool:
        """上传目录 - 使用Hugging Face Hub SDK

        Args:
            path_in_repo: 仓库内目标目录前缀。为空/``./`` 时上传到仓库根目录；
                否则目录内容会被放到该前缀下。
            repo_type: 仓库类型，``model`` 或 ``dataset``。为空时由 HF
                默认按 ``model`` 处理（保持既有行为）。
            revision: 上传目标 revision。AtomGit 当前仅支持空值或 ``main``；
                CLI 会在调用本方法前拒绝其他值。
            ignore_patterns: 忽略的文件模式列表（fnmatch/glob 风格，如
                ``*.tmp``、``logs/``、``**/.DS_Store``）。为 None 时不忽略。
            resumable: 是否启用可断点续传/分块上传模式。为 True 时改用 HF
                ``upload_large_folder``：进程级元数据写入目录下
                ``.cache/.huggingface/``，中断后再次执行可自动续传；适合
                大目录。CLI 使用按上传身份隔离的私有持久投影；
                ``path_in_repo`` 非空时将源目录内容放到对应远端前缀下，同时
                保留 HF 元数据。该模式不支持单一
                ``message`` / ``commit_message``（会产生多次提交），且 HF
                要求 ``repo_type`` 必填，为空时默认 ``model``。
            num_workers: 上传 worker 数，默认为 5；适用于断点续传和普通目录上传。
            batch_size: 外层目录批次的最大文件数，必须为 1..20 的整数。
            auto_configure_lfs: 仅用于 resumable。服务端将文件判定为 LFS 时，
                检查并补齐根目录 ``.gitattributes`` 的安全扩展名规则；同时保留
                超大 regular 文件的策略修复。规则作用于整个目标仓库。
        """
        if not is_supported_upload_revision(revision):
            print("上传 revision 名称不合法，已拒绝上传")
            return False
        if auto_configure_lfs and not resumable:
            print("--auto-configure-lfs 仅支持 resumable 目录上传")
            return False
        if (
            not isinstance(batch_size, int)
            or isinstance(batch_size, bool)
            or not 1 <= batch_size <= DEFAULT_UPLOAD_BATCH_SIZE
        ):
            print("上传批次大小必须是 1 到 20 之间的整数")
            return False
        try:
            try:
                validate_upload_path_no_symlinks(dir_path)
            except ValueError as error:
                print(str(error))
                return False
            if not dir_path.exists() or not dir_path.is_dir():
                print(f"目录不存在: {dir_path}")
                return False

            override_token = _UPLOAD_TOKEN_OVERRIDE.get()
            credentials = (
                {"token": override_token}
                if override_token
                else config.get_credentials()
            )
            if not credentials:
                print("未找到登录凭证")
                return False

            # 规范化 path_in_repo
            try:
                pipr = normalize_path_in_repo(path_in_repo)
            except ValueError as e:
                print(f"上传路径不合法: {e}")
                return False

            original_timeout = hf_constants.DEFAULT_REQUEST_TIMEOUT
            original_progress_state = _capture_progress_bar_state()
            _set_progress_bar(progress_bar)

            try:
                commit_message = message or "Upload folder using atomgit client"
                request_timeout = (
                    upload_timeout
                    if upload_timeout is not None
                    else _RESUMABLE_DEFAULT_REQUEST_TIMEOUT
                )
                hf_constants.DEFAULT_REQUEST_TIMEOUT = request_timeout
                close_hf_session()

                selected_files = _collect_resumable_upload_files(
                    dir_path, ignore_patterns
                )
                batches = [
                    selected_files[index : index + batch_size]
                    for index in range(0, len(selected_files), batch_size)
                ] or [[]]
                batch_count = len(batches)
                total_files = len(selected_files)
                submitted_files = 0
                skipped_files = 0
                completed_files = 0
                _print_upload_batch_plan(total_files, batch_count, batch_size)

                if resumable:
                    # 断点续传/分块上传：走 upload_large_folder
                    eff_repo_type = _atomgit_repo_type(repo_type) or "model"
                    normalized_repo_id = self._normalize_repo_id(repo_id)
                    _validate_resumable_upload_target(
                        token=credentials["token"],
                        repo_id=normalized_repo_id,
                        revision=revision,
                        request_timeout=request_timeout,
                    )
                    attempted_lfs_patterns = set()
                    for batch_index, batch in enumerate(batches):
                        batch_number = batch_index + 1
                        batch_file_count = len(batch)
                        print(
                            f"[批次 {batch_number}/{batch_count}] 开始: "
                            f"{batch_file_count} 个文件",
                            flush=True,
                        )
                        selected_paths = {item[0] for item in batch}
                        upload_root = None
                        batch_skipped = 0
                        try:
                            upload_root = _prepare_resumable_upload_projection(
                                dir_path,
                                normalized_repo_id,
                                eff_repo_type,
                                revision,
                                pipr,
                                ignore_patterns=None,
                                selected_paths=selected_paths,
                                batch_key=f"batch-{batch_size}-{batch_index}",
                            )
                            batch_skipped = _resumable_committed_file_count(
                                upload_root, selected_paths, pipr
                            )
                            if batch_skipped:
                                print(
                                    f"[批次 {batch_number}/{batch_count}] "
                                    f"续传跳过: {batch_skipped} 个已确认完成文件",
                                    flush=True,
                                )

                            lf_kwargs = dict(
                                repo_id=normalized_repo_id,
                                folder_path=str(upload_root),
                                repo_type=eff_repo_type,
                                num_workers=num_workers or 5,
                            )
                            if revision is not None:
                                lf_kwargs["revision"] = revision
                            if ignore_patterns:
                                lf_kwargs["ignore_patterns"] = (
                                    _prefix_resumable_ignore_patterns(
                                        pipr, ignore_patterns
                                    )
                                )
                            while True:
                                try:
                                    # Fully committed projections still enter HF
                                    # so authorization remains checked.
                                    _execute_resumable_upload_process(
                                        token=credentials["token"],
                                        upload_kwargs=lf_kwargs,
                                        request_timeout=request_timeout,
                                        batch_context=(batch_number, batch_count),
                                        auto_configure_lfs=auto_configure_lfs,
                                        configured_lfs_patterns=_validated_lfs_patterns(
                                            attempted_lfs_patterns
                                        ),
                                    )
                                    break
                                except ResumableWorkerError as error:
                                    if (
                                        error.category
                                        not in ("upload_mode", "lfs_attributes")
                                        or not auto_configure_lfs
                                    ):
                                        raise
                                    patterns = _validated_lfs_patterns(
                                        error.lfs_patterns
                                    )
                                    new_patterns = tuple(
                                        pattern
                                        for pattern in patterns
                                        if pattern not in attempted_lfs_patterns
                                    )
                                    if (
                                        len(attempted_lfs_patterns) + len(new_patterns)
                                        > _RESUMABLE_LFS_PATTERN_MAX_COUNT
                                    ):
                                        print(
                                            f"[批次 {batch_number}/{batch_count}] "
                                            "本次上传检测到的 LFS 扩展名超过自动配置上限；"
                                            "请手动配置 .gitattributes",
                                            flush=True,
                                        )
                                        raise
                                    if not new_patterns:
                                        if not patterns:
                                            print(
                                                f"[批次 {batch_number}/{batch_count}] "
                                                "无法从文件名推导安全的扩展名规则；"
                                                "请手动配置 .gitattributes",
                                                flush=True,
                                            )
                                        else:
                                            print(
                                                f"[批次 {batch_number}/{batch_count}] "
                                                "已尝试的 Git LFS 规则仍未生效；"
                                                "已停止自动修改以避免循环提交",
                                                flush=True,
                                            )
                                        raise
                                    attempted_lfs_patterns.update(new_patterns)
                                    if error.category == "lfs_attributes":
                                        print(
                                            f"[批次 {batch_number}/{batch_count}] "
                                            "检测到服务端判定为 LFS 的文件类型；"
                                            "正在检查远端 .gitattributes",
                                            flush=True,
                                        )
                                    else:
                                        print(
                                            f"[批次 {batch_number}/{batch_count}] "
                                            "检测到超大 regular 文件，需要配置 Git LFS",
                                            flush=True,
                                        )
                                    print(
                                        "将使用 --auto-configure-lfs 提交规则: "
                                        + ", ".join(new_patterns)
                                        + "（规则作用于整个仓库）",
                                        flush=True,
                                    )
                                    outcome = _configure_remote_lfs_attributes(
                                        token=credentials["token"],
                                        repo_id=normalized_repo_id,
                                        repo_type=eff_repo_type,
                                        revision=revision,
                                        patterns=new_patterns,
                                        request_timeout=request_timeout,
                                    )
                                    if outcome["changed"]:
                                        action = (
                                            "已创建" if outcome["created"] else "已更新"
                                        )
                                        continuation = (
                                            "正在刷新上传模式并重试当前批次"
                                            if error.category == "upload_mode"
                                            else "正在重试当前批次"
                                        )
                                        print(
                                            f"[批次 {batch_number}/{batch_count}] "
                                            f"{action}远端 .gitattributes；"
                                            f"{continuation}",
                                            flush=True,
                                        )
                                    else:
                                        continuation = (
                                            "正在刷新上传模式并重试当前批次"
                                            if error.category == "upload_mode"
                                            else "正在重试当前批次"
                                        )
                                        print(
                                            f"[批次 {batch_number}/{batch_count}] "
                                            "远端 .gitattributes 已包含所需规则；"
                                            f"{continuation}",
                                            flush=True,
                                        )
                        except Exception:
                            confirmed_in_batch = batch_skipped
                            batch_progress = None
                            if upload_root is not None:
                                batch_progress = _resumable_upload_progress(
                                    upload_root, batch, pipr
                                )
                                confirmed_in_batch = max(
                                    confirmed_in_batch,
                                    batch_progress["committed_files"],
                                )
                            skipped_files += batch_skipped
                            submitted_files += max(
                                0, confirmed_in_batch - batch_skipped
                            )
                            completed_files += confirmed_in_batch
                            remaining_files = total_files - completed_files
                            print(
                                f"[批次 {batch_number}/{batch_count}] 失败: "
                                f"累计确认完成 {completed_files}/{total_files}，"
                                f"剩余 {remaining_files}",
                                flush=True,
                            )
                            if batch_progress is not None:
                                _print_resumable_upload_progress(
                                    batch_number, batch_count, batch_progress
                                )
                            print(
                                "断点元数据已保留；修复问题后重新执行同一命令可继续上传",
                                flush=True,
                            )
                            _print_upload_batch_summary(
                                total_files,
                                submitted_files,
                                skipped_files,
                                completed_files,
                            )
                            raise

                        skipped_files += batch_skipped
                        newly_submitted = batch_file_count - batch_skipped
                        submitted_files += newly_submitted
                        completed_files += batch_file_count
                        print(
                            f"[批次 {batch_number}/{batch_count}] 成功: "
                            f"新增提交 {newly_submitted}，续传跳过 {batch_skipped}，"
                            f"累计完成 {completed_files}/{total_files}",
                            flush=True,
                        )
                else:
                    # 仓库内目标前缀：空 → "./"（根目录）
                    upload_path_in_repo = pipr + "/" if pipr else "./"
                    upload_kwargs = dict(
                        repo_id=self._normalize_repo_id(repo_id),
                        folder_path=str(dir_path),
                        path_in_repo=upload_path_in_repo,
                        token=credentials["token"],
                        commit_message=commit_message,
                    )
                    upload_repo_type = _atomgit_repo_type(repo_type)
                    if upload_repo_type is not None:
                        upload_kwargs["repo_type"] = upload_repo_type
                    if revision is not None:
                        upload_kwargs["revision"] = revision
                    for batch_index, batch in enumerate(batches):
                        batch_number = batch_index + 1
                        batch_file_count = len(batch)
                        print(
                            f"[批次 {batch_number}/{batch_count}] 开始: "
                            f"{batch_file_count} 个文件",
                            flush=True,
                        )
                        try:
                            if batch:
                                upload_kwargs["allow_patterns"] = [
                                    item[0].as_posix() for item in batch
                                ]
                            if ignore_patterns:
                                upload_kwargs["ignore_patterns"] = ignore_patterns
                            run_canonical_lfs_upload(
                                lambda: _upload_folder_with_workers(
                                    upload_kwargs, num_workers or 5
                                ),
                                token=credentials["token"],
                                repo_id=upload_kwargs["repo_id"],
                                timeout=request_timeout,
                            )
                        except Exception:
                            remaining_files = total_files - completed_files
                            print(
                                f"[批次 {batch_number}/{batch_count}] 失败: "
                                f"累计确认完成 {completed_files}/{total_files}，"
                                f"剩余 {remaining_files}",
                                flush=True,
                            )
                            _print_upload_batch_summary(
                                total_files,
                                submitted_files,
                                skipped_files,
                                completed_files,
                            )
                            raise
                        submitted_files += batch_file_count
                        completed_files += batch_file_count
                        print(
                            f"[批次 {batch_number}/{batch_count}] 成功: "
                            f"新增提交 {batch_file_count}，续传跳过 0，"
                            f"累计完成 {completed_files}/{total_files}",
                            flush=True,
                        )

                _print_upload_batch_summary(
                    total_files,
                    submitted_files,
                    skipped_files,
                    completed_files,
                )

                return True
            finally:
                hf_constants.DEFAULT_REQUEST_TIMEOUT = original_timeout
                close_hf_session()
                _restore_progress_bar_state(original_progress_state)

        except Exception as e:
            err_type, hint = _classify_upload_error(e, repo_id=repo_id)
            print(f"上传目录失败[{err_type}]")
            print(f"💡 建议: {hint}")
            return False
