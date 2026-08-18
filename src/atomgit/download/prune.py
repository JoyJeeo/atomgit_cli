"""Race-safe POSIX and Windows managed-file pruning."""

import ntpath
import os
import stat
from pathlib import Path, PurePosixPath, PureWindowsPath


def _repository_filename_parts(filename: str) -> tuple:
    """Validate a repository filename and return its POSIX path parts."""
    if not isinstance(filename, str) or not filename:
        raise ValueError("仓库文件名为空或格式无效")
    if "\\" in filename:
        raise ValueError(f"仓库文件名包含不安全的反斜杠路径: {filename!r}")
    if any(ord(character) < 32 or ord(character) == 127 for character in filename):
        raise ValueError(f"仓库文件名包含控制字符: {filename!r}")

    raw_parts = filename.split("/")
    if any(part in ("", ".", "..") for part in raw_parts):
        raise ValueError(f"仓库文件名包含不安全的路径片段: {filename!r}")

    posix_path = PurePosixPath(filename)
    windows_path = PureWindowsPath(filename)
    if posix_path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
        raise ValueError(f"仓库文件名不能是绝对路径: {filename!r}")
    return tuple(raw_parts)


class _WindowsFileAPI:
    """Minimal Win32 handle API used for race-safe managed-file deletion."""

    FILE_ATTRIBUTE_DIRECTORY = 0x10
    FILE_ATTRIBUTE_REPARSE_POINT = 0x400
    _DELETE = 0x00010000
    _FILE_READ_ATTRIBUTES = 0x00000080
    _FILE_SHARE_READ_WRITE = 0x00000001 | 0x00000002
    _OPEN_EXISTING = 3
    _FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    _FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    _FILE_ATTRIBUTE_TAG_INFO_CLASS = 9
    _FILE_DISPOSITION_INFO_CLASS = 4

    def __init__(self):
        import ctypes
        from ctypes import wintypes

        if os.name != "nt":
            raise RuntimeError("Win32 file API is unavailable")

        class FileAttributeTagInfo(ctypes.Structure):
            _fields_ = [
                ("FileAttributes", wintypes.DWORD),
                ("ReparseTag", wintypes.DWORD),
            ]

        class FileDispositionInfo(ctypes.Structure):
            _fields_ = [("DeleteFile", wintypes.BOOLEAN)]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateFileW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        kernel32.CreateFileW.restype = wintypes.HANDLE
        kernel32.GetFinalPathNameByHandleW.argtypes = [
            wintypes.HANDLE,
            wintypes.LPWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
        ]
        kernel32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
        kernel32.GetFileInformationByHandleEx.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            wintypes.LPVOID,
            wintypes.DWORD,
        ]
        kernel32.GetFileInformationByHandleEx.restype = wintypes.BOOL
        kernel32.SetFileInformationByHandle.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            wintypes.LPVOID,
            wintypes.DWORD,
        ]
        kernel32.SetFileInformationByHandle.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        self._ctypes = ctypes
        self._kernel32 = kernel32
        self._attribute_info = FileAttributeTagInfo
        self._disposition_info = FileDispositionInfo
        self._invalid_handle = ctypes.c_void_p(-1).value

    def _error(self, error_code: int, path=None):
        message = self._ctypes.FormatError(error_code).strip()
        return OSError(error_code, message, path)

    def open_path(self, path, delete: bool = False):
        access = self._FILE_READ_ATTRIBUTES
        if delete:
            access |= self._DELETE
        handle = self._kernel32.CreateFileW(
            os.fspath(path),
            access,
            self._FILE_SHARE_READ_WRITE,
            None,
            self._OPEN_EXISTING,
            self._FILE_FLAG_BACKUP_SEMANTICS | self._FILE_FLAG_OPEN_REPARSE_POINT,
            None,
        )
        if handle == self._invalid_handle:
            error_code = self._ctypes.get_last_error()
            if error_code in (2, 3):
                raise FileNotFoundError(error_code, "path not found", path)
            raise self._error(error_code, path)
        return handle

    def final_path(self, handle) -> str:
        size = 32768
        buffer = self._ctypes.create_unicode_buffer(size)
        result = self._kernel32.GetFinalPathNameByHandleW(handle, buffer, size, 0)
        if result == 0:
            raise self._error(self._ctypes.get_last_error())
        if result >= size:
            size = result + 1
            buffer = self._ctypes.create_unicode_buffer(size)
            result = self._kernel32.GetFinalPathNameByHandleW(handle, buffer, size, 0)
            if result == 0 or result >= size:
                raise self._error(self._ctypes.get_last_error())
        return buffer.value

    def attributes(self, handle) -> int:
        information = self._attribute_info()
        if not self._kernel32.GetFileInformationByHandleEx(
            handle,
            self._FILE_ATTRIBUTE_TAG_INFO_CLASS,
            self._ctypes.byref(information),
            self._ctypes.sizeof(information),
        ):
            raise self._error(self._ctypes.get_last_error())
        return information.FileAttributes

    def mark_delete(self, handle) -> None:
        information = self._disposition_info(True)
        if not self._kernel32.SetFileInformationByHandle(
            handle,
            self._FILE_DISPOSITION_INFO_CLASS,
            self._ctypes.byref(information),
            self._ctypes.sizeof(information),
        ):
            raise self._error(self._ctypes.get_last_error())

    def close(self, handle) -> None:
        if not self._kernel32.CloseHandle(handle):
            raise self._error(self._ctypes.get_last_error())


def _normalized_windows_handle_path(path: str) -> str:
    """Normalize one trusted final Win32 handle path for containment checks."""
    if (
        not isinstance(path, str)
        or not path
        or any(ord(character) < 32 for character in path)
    ):
        raise ValueError("Windows 文件句柄路径无效")
    return ntpath.normcase(ntpath.normpath(path))


def _prune_managed_download_file_windows(local_root, parts, windows_api=None) -> bool:
    """Delete one managed Windows file by verified handle, never by path."""
    if windows_api is None:
        windows_api = _WindowsFileAPI()
    root_handle = windows_api.open_path(local_root)
    directory_handles = [root_handle]
    target_handle = None
    try:
        root_attributes = windows_api.attributes(root_handle)
        if (
            not root_attributes & windows_api.FILE_ATTRIBUTE_DIRECTORY
            or root_attributes & windows_api.FILE_ATTRIBUTE_REPARSE_POINT
        ):
            raise ValueError("下载根目录不是安全的普通目录")

        root_final = _normalized_windows_handle_path(
            windows_api.final_path(root_handle)
        )
        current_path = os.fspath(local_root)
        for part in parts[:-1]:
            current_path = ntpath.join(current_path, part)
            try:
                directory_handle = windows_api.open_path(current_path)
            except FileNotFoundError:
                return False
            directory_handles.append(directory_handle)
            attributes = windows_api.attributes(directory_handle)
            if (
                not attributes & windows_api.FILE_ATTRIBUTE_DIRECTORY
                or attributes & windows_api.FILE_ATTRIBUTE_REPARSE_POINT
            ):
                raise ValueError("受管理路径包含不安全的父目录")
            directory_final = _normalized_windows_handle_path(
                windows_api.final_path(directory_handle)
            )
            try:
                inside_root = (
                    ntpath.commonpath((root_final, directory_final)) == root_final
                )
            except ValueError:
                inside_root = False
            if not inside_root:
                raise ValueError("受管理路径超出下载目录，已拒绝清理")

        target_path = ntpath.join(current_path, parts[-1])
        try:
            target_handle = windows_api.open_path(target_path, delete=True)
        except FileNotFoundError:
            return False

        target_attributes = windows_api.attributes(target_handle)
        if target_attributes & (
            windows_api.FILE_ATTRIBUTE_DIRECTORY
            | windows_api.FILE_ATTRIBUTE_REPARSE_POINT
        ):
            raise ValueError("受管理路径不再是普通文件，已拒绝清理")

        target_final = _normalized_windows_handle_path(
            windows_api.final_path(target_handle)
        )
        try:
            inside_root = (
                ntpath.commonpath((root_final, target_final)) == root_final
                and target_final != root_final
            )
        except ValueError:
            inside_root = False
        if not inside_root:
            raise ValueError("受管理路径超出下载目录，已拒绝清理")

        windows_api.mark_delete(target_handle)
        return True
    finally:
        try:
            if target_handle is not None:
                windows_api.close(target_handle)
        finally:
            close_error = None
            for directory_handle in reversed(directory_handles):
                try:
                    windows_api.close(directory_handle)
                except Exception as error:
                    if close_error is None:
                        close_error = error
            if close_error is not None:
                raise close_error


def _uses_windows_prune() -> bool:
    return os.name == "nt"


def _prune_managed_download_file(local_root: Path, filename: str) -> bool:
    """Delete one managed regular file without following directory symlinks."""
    parts = _repository_filename_parts(filename)
    if _uses_windows_prune():
        return _prune_managed_download_file_windows(Path(local_root).resolve(), parts)
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise RuntimeError("当前平台不支持安全的下载文件清理")
    directory_flags = os.O_RDONLY
    directory_flags |= os.O_DIRECTORY | os.O_NOFOLLOW

    descriptor = os.open(str(Path(local_root).resolve()), directory_flags)
    try:
        for part in parts[:-1]:
            try:
                next_descriptor = os.open(part, directory_flags, dir_fd=descriptor)
            except FileNotFoundError:
                return False
            os.close(descriptor)
            descriptor = next_descriptor
        try:
            file_status = os.stat(parts[-1], dir_fd=descriptor, follow_symlinks=False)
        except FileNotFoundError:
            return False
        if not stat.S_ISREG(file_status.st_mode):
            raise ValueError(f"受管理路径不再是普通文件，已拒绝清理: {filename!r}")
        os.unlink(parts[-1], dir_fd=descriptor)
        return True
    finally:
        os.close(descriptor)


def _prune_managed_download_files(local_root: Path, filenames) -> int:
    """Delete only previously managed regular files and leave directories."""
    removed = 0
    for filename in sorted(filenames):
        if _prune_managed_download_file(local_root, filename):
            removed += 1
    return removed
