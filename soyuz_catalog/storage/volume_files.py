"""Local-filesystem backend for volume file IO.

Volumes persist only metadata in soyuz's database; the actual bytes
live under the ``storage_location`` URI the volume was created with.
This module implements the ``file://`` case so the "create a volume,
drop a CSV into it, query it as a Delta table" workflow works on any
single-node deployment without requiring S3 credentials.

Future cloud backends (s3, abfss, gs) can land here by implementing
the :class:`VolumeFileBackend` protocol and adding a ``get_backend``
case — the routes that call into this module do not need to know
which backend is in use.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit

from soyuz_catalog.exceptions import InvalidRequestError, NotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class VolumeFileEntry:
    """One browse-result row for a volume file.

    Attributes:
        path: Posix-style path relative to the volume's storage_location.
        size_bytes: Size of the file in bytes.
        is_dir: Whether this entry is a directory.
    """

    path: str
    size_bytes: int
    is_dir: bool


class VolumeFileBackend(Protocol):
    """Abstract backend for volume file operations.

    Only ``file://`` is implemented today; cloud backends land as new
    classes that satisfy this protocol.
    """

    def upload(self, relative_path: str, source: Iterator[bytes]) -> VolumeFileEntry:
        """Write bytes from *source* at *relative_path*.

        Args:
            relative_path: Volume-relative destination.
            source: Iterable of byte chunks.

        Returns:
            VolumeFileEntry: Metadata for the resulting file.
        """
        ...

    def download(self, relative_path: str) -> Path:
        """Return an absolute path the caller can stream out.

        Args:
            relative_path: Volume-relative source.

        Returns:
            Path: Absolute filesystem location for streaming.
        """
        ...

    def browse(self) -> list[VolumeFileEntry]:
        """Return every file (no dirs) under the volume, newest-first.

        Returns:
            list[VolumeFileEntry]: One entry per file below the root.
        """
        ...

    def delete(self, relative_path: str) -> bool:
        """Remove the file at *relative_path*.

        Args:
            relative_path: Volume-relative path to remove.

        Returns:
            bool: ``True`` iff a file was removed.
        """
        ...


class LocalVolumeFileBackend:
    """File-URI backend rooted at a volume's ``storage_location``.

    Accepts only ``file://`` URIs.  Every path argument is rejected if
    it resolves outside the volume root — no path-traversal bugs — and
    directories are materialised on demand.

    Args:
        storage_location: A ``file://`` URI describing the volume root.

    Raises:
        InvalidRequestError: If *storage_location* is not a ``file://``
            URI or is empty.
    """

    def __init__(self, storage_location: str) -> None:  # noqa: D107
        parsed = urlsplit(storage_location or "")
        if parsed.scheme != "file":
            raise InvalidRequestError(
                "volume file IO only supports file:// storage on this "
                f"deployment; got scheme {parsed.scheme!r}",
            )
        # ``file:///tmp/x`` parses with an empty netloc; ``parsed.path``
        # is the absolute filesystem path.  Windows file URIs never
        # hit this codepath because the single-node target is Linux.
        fs_path = parsed.path or ""
        if not fs_path:
            raise InvalidRequestError(
                "file:// storage_location must include an absolute path",
            )
        self._root = Path(fs_path).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        """The absolute root Path of this volume's local storage.

        Returns:
            Path: Resolved absolute root directory the backend
                rejects any file operation from escaping.
        """
        return self._root

    def _resolve_inside_root(self, relative_path: str) -> Path:
        """Resolve *relative_path* under the root, rejecting traversal.

        Args:
            relative_path: Client-supplied sub-path (may contain ``/``).

        Returns:
            Path: Absolute path beneath :attr:`root`.

        Raises:
            InvalidRequestError: On empty path or on paths that resolve
                outside the volume root.
        """
        rel = (relative_path or "").strip("/")
        if not rel or ".." in Path(rel).parts:
            raise InvalidRequestError(
                f"invalid volume-relative path: {relative_path!r}",
            )
        candidate = (self._root / rel).resolve()
        try:
            candidate.relative_to(self._root)
        except ValueError as exc:
            raise InvalidRequestError(
                f"path {relative_path!r} escapes the volume root",
            ) from exc
        return candidate

    def upload(self, relative_path: str, source: Iterator[bytes]) -> VolumeFileEntry:
        """Stream *source* into the file at *relative_path*.

        Args:
            relative_path: Destination sub-path within the volume.
            source: Iterable of byte chunks.

        Returns:
            VolumeFileEntry: Metadata for the resulting file.
        """
        target = self._resolve_inside_root(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        total = 0
        with target.open("wb") as fh:
            for chunk in source:
                if not chunk:
                    continue
                fh.write(chunk)
                total += len(chunk)
        rel_display = str(target.relative_to(self._root))
        return VolumeFileEntry(path=rel_display, size_bytes=total, is_dir=False)

    def download(self, relative_path: str) -> Path:
        """Return the absolute path for streaming *relative_path* out.

        Args:
            relative_path: Source sub-path within the volume.

        Returns:
            Path: Absolute filesystem path to the file.

        Raises:
            NotFoundError: When the file does not exist.
        """
        target = self._resolve_inside_root(relative_path)
        if not target.is_file():
            raise NotFoundError(f"volume file not found: {relative_path!r}")
        return target

    def browse(self) -> list[VolumeFileEntry]:
        """Return every file rooted at the volume, newest-first.

        Returns:
            list[VolumeFileEntry]: One entry per file below the root.
        """
        entries: list[VolumeFileEntry] = []
        if not self._root.is_dir():
            return entries
        for path in self._root.rglob("*"):
            if path.is_file():
                try:
                    size = path.stat().st_size
                except OSError:
                    size = 0
                rel = str(path.relative_to(self._root))
                entries.append(VolumeFileEntry(path=rel, size_bytes=size, is_dir=False))
        entries.sort(
            key=lambda e: (self._root / e.path).stat().st_mtime,
            reverse=True,
        )
        return entries

    def delete(self, relative_path: str) -> bool:
        """Remove the file at *relative_path*.

        Args:
            relative_path: Sub-path to delete.

        Returns:
            bool: ``True`` iff a file was deleted.
        """
        target = self._resolve_inside_root(relative_path)
        if not target.is_file():
            return False
        target.unlink()
        return True


def get_backend(storage_location: str) -> VolumeFileBackend:
    """Return a :class:`VolumeFileBackend` for *storage_location*.

    Only ``file://`` is supported; other schemes raise
    :class:`InvalidRequestError` at call time so the admin sees a
    clear error the first time a cloud volume is requested instead of
    a confusing ``NotImplementedError`` deep in the traceback.

    Args:
        storage_location: The volume's ``storage_location`` URI.

    Returns:
        VolumeFileBackend: An instance for the volume.

    Raises:
        InvalidRequestError: On unsupported URI schemes.
    """
    parsed = urlsplit(storage_location or "")
    if parsed.scheme == "file":
        return LocalVolumeFileBackend(storage_location)
    raise InvalidRequestError(
        "file IO for this volume's storage scheme is not yet implemented "
        f"on this deployment: {parsed.scheme!r}",
    )
