"""Small request/result value objects used at all new boundaries."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generic, Optional, Tuple, TypeVar, Union


class Visibility(str, Enum):
    """Repository visibility understood by both CLI and native SDK."""

    PUBLIC = "public"
    PRIVATE = "private"


T = TypeVar("T")


@dataclass(frozen=True)
class OperationResult(Generic[T]):
    """A redacted, structured result shared by CLI and SDK orchestration.

    ``value`` is intentionally opaque to the core layer.  Adapters must never
    place credentials, signed URLs, response bodies, or secret-bearing causes
    in it or in ``metadata``.
    """

    operation: str
    ok: bool
    value: Optional[T] = None
    repo_id: Optional[str] = None
    revision: Optional[str] = None
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[BaseException] = None

    def unwrap(self) -> T:
        if not self.ok:
            if self.error is not None:
                raise self.error
            raise RuntimeError(f"{self.operation} failed")
        return self.value  # type: ignore[return-value]


@dataclass(frozen=True)
class RepositoryRequest:
    repo_id: str
    repo_type: str = "model"
    visibility: Optional[Visibility] = None
    revision: str = "main"
    token: Optional[Union[str, bool]] = None
    exist_ok: bool = False


@dataclass(frozen=True)
class UploadRequest:
    source: Union[str, Path]
    repo_id: str
    repo_type: str = "model"
    revision: str = "main"
    token: Optional[Union[str, bool]] = None
    path_in_repo: str = "./"
    ignore_patterns: Tuple[str, ...] = ()
    resumable: bool = False
    num_workers: int = 5
    batch_size: int = 20
    timeout: float = 300.0
    progress: bool = True
    checksum: bool = False
    auto_configure_lfs: bool = False


@dataclass(frozen=True)
class DownloadRequest:
    repo_id: str
    filename: Optional[str] = None
    repo_type: Optional[str] = None
    revision: str = "main"
    token: Optional[Union[str, bool]] = None
    local_dir: Optional[Union[str, Path]] = None
    force: bool = False
    checksum: bool = False
    resume: bool = False
    prune: bool = False
    allow_patterns: Optional[Tuple[str, ...]] = None
    ignore_patterns: Optional[Tuple[str, ...]] = None
