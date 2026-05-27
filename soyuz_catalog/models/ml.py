"""Registered models and their versions.

ML asset sub-tree of the UC namespace
(``catalog.schema.registered_model.version_int``). The shape is
deliberately thinner than the tabular hierarchy because the spec
defines fewer fields for ML resources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from soyuz_catalog.models._base import Base, _new_id, _now_ms

if TYPE_CHECKING:
    from soyuz_catalog.models.catalog import Schema


class RegisteredModel(Base):
    """A Unity Catalog registered model (third-level namespace, ML assets).

    A registered model is the metadata container for a series of
    :class:`ModelVersion` rows. It lives at the same level of the UC
    namespace as tables, volumes, and functions
    (``catalog.schema.model``) and is addressed by ``full_name`` in
    every REST endpoint the same way.

    The shape is deliberately thinner than
    :class:`soyuz_catalog.models.Table` because the UC
    ``RegisteredModelInfo`` schema defines only the bookkeeping fields
    plus an optional ``storage_location``. soyuz does not derive a
    managed location for registered models on create (unlike
    catalogs/schemas/tables) because ``CreateRegisteredModel`` takes
    no ``storage_root`` and the upstream spec leaves
    ``storage_location`` as a free-form server field — we accept
    ``None`` and never populate it until a real consumer asks. The
    divergence is documented.

    Like every other parent resource in this project, the foreign key
    to ``schemas.id`` is declared without ``ondelete="CASCADE"``. Child
    :class:`ModelVersion` rows are cascaded explicitly at the service
    layer when a ``DELETE /models/{full_name}?force=true`` request
    arrives; without ``force`` the delete is rejected with 409 if any
    versions still exist. Same policy as catalogs → schemas and
    schemas → tables.
    """

    __tablename__ = "registered_models"
    __table_args__ = (
        UniqueConstraint("schema_id", "name", name="uq_registered_models_schema_id_name"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    schema_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("schemas.id"),
        nullable=False,
        index=True,
    )
    catalog_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("catalogs.id"),
        nullable=False,
        index=True,
    )
    storage_location: Mapped[str | None] = mapped_column(String, nullable=True)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    schema: Mapped[Schema] = relationship("Schema")
    versions: Mapped[list[ModelVersion]] = relationship(
        "ModelVersion",
        back_populates="registered_model",
        cascade="all, delete-orphan",
        order_by="ModelVersion.version",
    )


class ModelVersion(Base):
    """A single version of a :class:`RegisteredModel`.

    Model versions are a sub-resource of a registered model: they are
    addressed as ``(catalog.schema.model_name, version_int)`` rather
    than by a free-form name, and the primary key on the wire is the
    monotonic ``version`` integer. Internally the PK is an opaque
    UUID hex so the row survives a rename of the parent model without
    the version numbers getting renumbered; the user-facing
    ``version`` column is unique **within a registered model** via
    ``UniqueConstraint("registered_model_id", "version")``.

    ``status`` is a spec enum with four values (``UNKNOWN``,
    ``PENDING_REGISTRATION``, ``FAILED_REGISTRATION``, ``READY``) but
    soyuz only ever stores ``READY``: there is no async registration
    pipeline, so the other three states cannot arise from our own
    writes. The column stays because the spec requires it on the
    response and because future migration-in of real UC data could
    carry non-READY rows. See ``DIVERGENCES.md``.

    ``source`` is the URI of the source artifacts for the model and
    is required on create; it is *not* scheme-validated via
    :func:`soyuz_catalog.storage.parse_storage_uri` because the UC
    spec allows arbitrary locators (``mlflow://...``, ``runs:/...``,
    HTTP URLs, etc.) that the storage-URI parser deliberately
    rejects. ``storage_location`` is a separate optional field for
    the cloud path where the uploaded artifacts actually live.
    """

    __tablename__ = "model_versions"
    __table_args__ = (
        UniqueConstraint(
            "registered_model_id",
            "version",
            name="uq_model_versions_registered_model_id_version",
        ),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    registered_model_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("registered_models.id"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    run_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="READY")
    storage_location: Mapped[str | None] = mapped_column(String, nullable=True)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    registered_model: Mapped[RegisteredModel] = relationship(
        "RegisteredModel",
        back_populates="versions",
    )
