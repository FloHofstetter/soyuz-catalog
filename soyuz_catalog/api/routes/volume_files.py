"""HTTP routes for volume file IO.

Attaches four file-level endpoints underneath the existing
``/volumes`` metadata surface:

- ``POST /volumes/{full_name}/files`` — streaming upload.
- ``GET  /volumes/{full_name}/files`` — browse (JSON list).
- ``GET  /volumes/{full_name}/files/{path:path}`` — stream download.
- ``DELETE /volumes/{full_name}/files/{path:path}`` — unlink a file.

Bytes live on whatever backend the volume's ``storage_location``
selects — today only ``file://`` is implemented, but
:func:`soyuz_catalog.storage.volume_files.get_backend` is the single
dispatch point for adding cloud backends later.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

from fastapi import APIRouter, Depends, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.services import volume_service
from soyuz_catalog.storage.volume_files import VolumeFileEntry, get_backend

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/volumes", tags=["volumes"])


def _entry_as_dict(entry: VolumeFileEntry) -> dict[str, object]:
    """Serialise a :class:`VolumeFileEntry` for JSON responses.

    Args:
        entry: The entry to serialise.

    Returns:
        dict[str, object]: JSON-friendly dict mirroring the dataclass
            fields.
    """
    return {
        "path": entry.path,
        "size_bytes": entry.size_bytes,
        "is_dir": entry.is_dir,
    }


def _resolve_backend(db: Session, full_name: str) -> object:
    """Load the volume metadata row and return its file backend.

    Args:
        db: Active database session.
        full_name: Dotted UC identifier.

    Returns:
        object: A :class:`soyuz_catalog.storage.volume_files.VolumeFileBackend`
            instance typed loosely to keep the ``fastapi`` dependency
            signature light.

    Raises:
        InvalidRequestError: When the volume has no
            ``storage_location`` to open a backend on.
    """  # noqa: DOC502 — raised inside the block below
    from soyuz_catalog.exceptions import InvalidRequestError

    volume = volume_service.get_volume(db, full_name)
    if not volume.storage_location:
        raise InvalidRequestError(
            f"volume {full_name!r} has no storage_location",
        )
    return get_backend(volume.storage_location)


@router.post(
    "/{full_name}/files",
    response_model=dict,
    summary="Upload file to volume",
)
async def upload_volume_file(
    full_name: str,
    path: str = Query(..., description="Volume-relative destination path."),
    upload: UploadFile = ...,  # type: ignore[assignment]
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Stream *upload* into the volume at *path*.

    Args:
        full_name: Dotted ``catalog.schema.volume`` identifier.
        path: Volume-relative destination path; enforced to stay
            inside the volume root.
        upload: The ``multipart/form-data`` body carrying the file.
        db: DB session dependency.

    Returns:
        dict[str, object]: Single ``file`` key with the resulting
            entry's JSON shape.
    """
    backend = _resolve_backend(db, full_name)

    def _chunks() -> Iterator[bytes]:
        while True:
            data = upload.file.read(64 * 1024)
            if not data:
                break
            yield data

    entry = backend.upload(path, _chunks())  # type: ignore[attr-defined]
    return {"file": _entry_as_dict(entry)}


@router.get("/{full_name}/files", summary="List files in volume")
def browse_volume_files(
    full_name: str,
    db: Session = Depends(get_db),
) -> dict[str, list[dict[str, object]]]:
    """List every file stored in the volume.

    Args:
        full_name: Dotted UC identifier.
        db: DB session dependency.

    Returns:
        dict[str, list[dict[str, object]]]: Dict with a ``files`` list;
            each item is the JSON form of :class:`VolumeFileEntry`.
    """
    backend = _resolve_backend(db, full_name)
    entries = backend.browse()  # type: ignore[attr-defined]
    return {"files": [_entry_as_dict(e) for e in entries]}


@router.get("/{full_name}/files/{path:path}", summary="Download file from volume")
def download_volume_file(
    full_name: str,
    path: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    """Stream a single file out of the volume.

    Args:
        full_name: Dotted UC identifier.
        path: Volume-relative source path.
        db: DB session dependency.

    Returns:
        FileResponse: :class:`fastapi.responses.FileResponse` streaming
            the file's bytes to the caller.
    """
    backend = _resolve_backend(db, full_name)
    absolute = backend.download(path)  # type: ignore[attr-defined]
    return FileResponse(path=str(absolute), filename=path.split("/")[-1])


@router.delete("/{full_name}/files/{path:path}", summary="Delete file from volume")
def delete_volume_file(
    full_name: str,
    path: str,
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    """Remove a file from the volume.

    Args:
        full_name: Dotted UC identifier.
        path: Volume-relative path to remove.
        db: DB session dependency.

    Returns:
        dict[str, bool]: Dict with a single ``deleted`` boolean flag.
    """
    backend = _resolve_backend(db, full_name)
    ok = backend.delete(path)  # type: ignore[attr-defined]
    return {"deleted": ok}
