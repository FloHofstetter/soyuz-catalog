"""The singleton metastore identity row.

Lives in its own module because it is structurally unique: no parent,
no children, one row ever. Bootstrapping happens lazily in
:func:`soyuz_catalog.services.metastore_service.get_metastore_summary`.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from soyuz_catalog.models._base import Base, _new_id, _now_ms


class Metastore(Base):
    """The singleton metastore identity row.

    The UC OpenAPI spec addresses every governed resource as living under
    *one* metastore, and ``GET /metastore_summary`` returns that
    metastore's identity. soyuz models the metastore as a
    single-row table rather than a hard-coded constant so that (a) the
    id survives process restarts on a real database, (b) two
    deployments report distinct ids, and (c) test fixtures get a fresh
    id per in-memory engine without extra plumbing. The row is created
    lazily on the first ``get_metastore_summary`` call — there is no
    ``CreateMetastore`` endpoint in soyuz and the UC spec does not
    expose one either, so the service layer bootstraps the row itself.

    No ``name`` / ``storage_root`` / ``region`` columns: the upstream
    ``GetMetastoreSummaryResponse`` defines only ``metastore_id``, and
    adding anything else would silently extend the spec — the UC OSS
    bug class this project refuses to tolerate.
    """

    __tablename__ = "metastore"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
