"""Staging tables and Delta unbackfilled commits.

Two intentionally schema-light tables: experimental allocation
metadata (:class:`StagingTable`) and the passthrough Delta commit
coordinator's state (:class:`DeltaUnbackfilledCommit`, ADR-0011). Both
store ``table_id`` (or ``schema_id`` / ``catalog_id``) as opaque ids
without ON DELETE CASCADE — same service-owns-cascade pattern as the
rest of the catalog.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from soyuz_catalog.models._base import Base, _new_id, _now_ms

if TYPE_CHECKING:
    from soyuz_catalog.models.catalog import Schema


class StagingTable(Base):
    """A Unity Catalog staging-table allocation.

    Staging tables are the experimental allocation-only half of the UC
    managed-table creation protocol: a client POSTs the intended
    ``(catalog, schema, name)`` triple, the server returns an opaque
    ``id`` plus a ``staging_location`` URL the client can write data
    to, and a later *promote* step (not modelled in soyuz) turns the
    allocation into a real :class:`soyuz_catalog.models.Table`. The
    upstream spec flags this as ``WARNING: experimental``, so the shape
    is intentionally thinner than :class:`soyuz_catalog.models.Table`:
    no columns, no properties, no ``updated_at`` (there is no PATCH
    endpoint), and no uniqueness constraint on ``(schema_id, name)``
    because two concurrent allocation requests for the same name are
    legal and must both succeed with distinct ids.

    The ``staging_location`` is derived at create time from the parent
    schema's ``storage_location`` (falling back to the catalog's
    ``storage_root``), with a UUID-hex path segment so two allocations
    under the same name never collide on disk. The derivation keys on
    a fresh UUID rather than the staging-table ``id`` so that the URL
    is independently random — a convenience for any future cleanup job
    that wants to walk ``__staging__/`` without a DB join.

    The foreign key to ``schemas.id`` is declared without
    ``ondelete="CASCADE"`` — same service-owns-cascade policy as every
    other child resource in this module. There is intentionally no
    explicit delete path: the spec defines no delete endpoint for
    staging tables and the rows are expected to be short-lived. A
    future cascade wiring through ``delete_schema`` would slot in
    alongside the existing children without breaking this contract.
    """

    __tablename__ = "staging_tables"

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
    staging_location: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)

    schema: Mapped[Schema] = relationship("Schema")


class DeltaUnbackfilledCommit(Base):
    """One unbackfilled Delta commit tracked by the coordinator.

    Persists state for the passthrough Delta commit coordinator
    (ADR-0011). Each row represents a staged commit file
    the Delta Kernel client has written to ``_delta_log/.tmp/<uuid>.json``
    and registered via ``POST /delta/preview/commits`` but has not yet
    published to ``_delta_log/NNNNN.json``. The client self-publishes
    after receiving a 200 response and signals the completed publish on
    a subsequent ``POST`` carrying ``latest_backfilled_version``, at
    which point the service prunes rows at earlier versions and marks
    the boundary row with :attr:`is_backfilled_latest_commit` so
    ``GET`` can still report an accurate ``latest_table_version``
    after cleanup (the exact upstream pattern from
    ``DeltaCommitRepository.java`` lines 236-414).

    The composite unique constraint on ``(table_id, commit_version)`` is
    the **entire** optimistic-concurrency story: two writers racing at
    the same version serialise through the database, one wins, and the
    other's :class:`sqlalchemy.exc.IntegrityError` translates to a 409
    in :func:`soyuz_catalog.services.delta_commits_service.commit`.
    There is no lock manager and no background backfill watchdog —
    Delta Kernel readers apply unbackfilled rows in-memory, so a crash
    between the ``commit`` call and the client-side publish is a
    read-path concern that heals itself on the next snapshot.

    ``table_id`` references :class:`soyuz_catalog.models.Table.id` by
    convention but has **no foreign key**, matching the
    :class:`soyuz_catalog.models.Tag` /
    :class:`soyuz_catalog.models.LineageEdge` /
    :class:`soyuz_catalog.models.Permission` pattern: a ``DROP TABLE``
    leaves commit rows behind as unreachable orphans (the opaque id is
    unique per creation, so a new table with the same name cannot
    inherit them). ADR-0011 Consequences documents this explicitly.
    """

    __tablename__ = "delta_unbackfilled_commits"
    __table_args__ = (
        UniqueConstraint(
            "table_id",
            "commit_version",
            name="uq_delta_unbackfilled_commits_table_id_version",
        ),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    table_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    commit_version: Mapped[int] = mapped_column(BigInteger, nullable=False)
    commit_timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_modification_timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_backfilled_latest_commit: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
